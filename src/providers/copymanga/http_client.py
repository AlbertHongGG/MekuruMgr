import httpx
import logging
import datetime
from typing import Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.domain.exceptions import NetworkError
from .config import BASE_URL, DEFAULT_HEADERS
from .signer import CopymangaSigner

logger = logging.getLogger(__name__)

class CopymangaHttpClient:
    """
    HTTP Client wrapper for Copymanga.
    Handles headers, error catching, and retries.
    """
    def __init__(self):
        self.base_url = BASE_URL
        self.signer = CopymangaSigner()
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
        """
        Sends a GET request with Copymanga specific headers.
        """
        if params is None:
            params = {}

        # Merge headers
        headers = dict(DEFAULT_HEADERS)
        
        # Override dt with today's date in YYYY.MM.DD format
        headers["dt"] = datetime.datetime.now().strftime("%Y.%m.%d")
        
        # Override with dynamic signature headers
        auth_headers = self.signer.get_auth_headers()
        headers.update(auth_headers)

        logger.debug(f"copymanga_http_get endpoint={endpoint} params={params}")

        try:
            response = self.client.get(endpoint, params=params, headers=headers)
            response.raise_for_status()
        except httpx.HTTPError as e:
            logger.error(f"http_request_failed endpoint={endpoint} error={str(e)}")
            raise NetworkError(f"Network error on Copymanga API: {e}") from e

        try:
            response.encoding = 'utf-8'
            res_json = response.json()
        except ValueError as e:
            logger.error(f"invalid_json_response endpoint={endpoint} text={response.text}")
            raise NetworkError("Failed to parse JSON response") from e

        # Also log if backend returns specific errors
        if isinstance(res_json, dict) and res_json.get("code") != 200:
            error_msg = res_json.get("message", "Unknown error")
            logger.error(f"copymanga_api_error code={res_json.get('code')} msg={error_msg}")
            raise NetworkError(f"Backend returned error: {error_msg}")
             
        return res_json
