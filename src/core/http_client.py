import httpx
import structlog
from typing import Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.core.exceptions import NetworkError, ApiLogicError
from src.core.auth import Signer

logger = structlog.get_logger(__name__)

class BaseHttpClient:
    def __init__(self, base_url: str, signer: Signer):
        self.base_url = base_url
        self.signer = signer
        
        # Define common headers (Device fingerprinting, etc.)
        self.headers = {
            "accept": "application/json",
            "accept-charset": "UTF-8",
            "user-agent": "ktor-client",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            # Dummy device identifiers
            "deviceid": "dummy_device_id",
            "appid": "6",
            "appversion": "1.1.1",
            "osv": "13",
            "model": "GenericDevice",
            "os": "1"
        }
        
        self.client = httpx.Client(
            base_url=self.base_url,
            headers=self.headers,
            timeout=httpx.Timeout(10.0)
        )

    def close(self):
        self.client.close()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(NetworkError),
        reraise=True
    )
    def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sends a POST request with automatically injected requestTime and sign.
        """
        # Inject signature
        req_time, sign = self.signer.generate_signature(endpoint, data)
        payload = data.copy()
        payload["requestTime"] = str(req_time)
        payload["sign"] = sign

        logger.debug("sending_request", endpoint=endpoint, payload=payload)

        try:
            response = self.client.post(endpoint, data=payload)
            response.raise_for_status()
        except httpx.HTTPError as e:
            logger.error("http_request_failed", endpoint=endpoint, error=str(e))
            raise NetworkError(f"Network error on {endpoint}: {e}") from e

        try:
            res_json = response.json()
        except ValueError as e:
            logger.error("invalid_json_response", endpoint=endpoint, text=response.text)
            raise NetworkError("Failed to parse JSON response") from e

        # Handle API level logic errors
        code = res_json.get("code", -1)
        if code != 200:
            msg = res_json.get("message", "Unknown error")
            logger.warning("api_logic_error", endpoint=endpoint, code=code, message=msg)
            raise ApiLogicError(msg, code)

        return res_json.get("data", {})
