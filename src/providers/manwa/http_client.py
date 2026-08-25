import httpx
import logging
from typing import Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.domain.exceptions import NetworkError, ApiLogicError
from .config import BASE_URL
from .crypto import ManwaCrypto

logger = logging.getLogger(__name__)

class ManwaHttpClient:
    """
    HTTP Client wrapper for Manwa.
    Handles dynamic headers, AES decryption, and retries.
    """
    def __init__(self):
        self.base_url = BASE_URL
        self.client = httpx.Client(
            base_url=self.base_url,
            timeout=httpx.Timeout(15.0),
            verify=False
        )

    def close(self):
        self.client.close()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(NetworkError),
        reraise=True
    )
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        if params is None:
            params = {}

        headers, x_token, devid = ManwaCrypto.generate_headers()
        
        logger.debug(f"manwa_http_get endpoint={endpoint} params={params}")

        try:
            response = self.client.get(endpoint, params=params, headers=headers)
            response.raise_for_status()
        except httpx.HTTPError as e:
            logger.error(f"http_request_failed endpoint={endpoint} error={str(e)}")
            raise NetworkError(f"Network error on Manwa API: {e}") from e

        # Decrypt response
        try:
            res_json = ManwaCrypto.decrypt_data(response.text, x_token, devid)
        except Exception as e:
            logger.error(f"decryption_failed endpoint={endpoint} error={str(e)}")
            raise NetworkError("Failed to decrypt API response") from e

        code = res_json.get("code", 1)
        if code != 1:
            msg = res_json.get("message", "Unknown API Error")
            logger.error(f"manwa_api_error code={code} msg={msg}")
            raise ApiLogicError(msg, code)
            
        return res_json.get("data", {})
