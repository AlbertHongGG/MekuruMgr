import httpx
import structlog
from typing import Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.core.exceptions import NetworkError, ApiLogicError
from src.providers.comicwifi.auth import ComicWifiAuth
from src.providers.comicwifi.config import settings

logger = structlog.get_logger(__name__)

class BaseHttpClient:
    """
    Core HTTP Client wrapper.
    Handles session management, auth injection, and error catching.
    """
    def __init__(self):
        self.base_url = settings.base_url
        self.auth = ComicWifiAuth()
        self.client = httpx.Client(
            base_url=self.base_url,
            headers=settings.http_headers,
            auth=self.auth,
            timeout=httpx.Timeout(15.0)
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
        Sends a POST request. The auth interceptor automatically injects requestTime and sign.
        """
        logger.debug("http_post_request", endpoint=endpoint)

        try:
            response = self.client.post(endpoint, data=data)
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
