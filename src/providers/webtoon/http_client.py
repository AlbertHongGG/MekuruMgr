import httpx
import logging
from typing import Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.domain.exceptions import NetworkError, ApiLogicError
from .config import BASE_URL
from .signer import WebtoonUrlSigner

logger = logging.getLogger(__name__)

class WebtoonHttpClient:
    """
    HTTP Client wrapper for Webtoon.
    Handles session management, automatic URL signing, and error catching.
    """
    def __init__(self):
        self.base_url = BASE_URL
        self.signer = WebtoonUrlSigner()
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
        Sends a signed GET request.
        """
        if params is None:
            params = {}

        # Construct the raw URL with params using httpx Request builder
        request = self.client.build_request("GET", endpoint, params=params)
        raw_url = str(request.url)
        
        # Sign the URL
        signed_url = self.signer.sign_url(raw_url)
        
        logger.debug(f"webtoon_http_get url={signed_url}")

        try:
            # We send the request using the raw signed URL
            response = self.client.get(signed_url)
            response.raise_for_status()
        except httpx.HTTPError as e:
            logger.error(f"http_request_failed url={signed_url} error={str(e)}")
            raise NetworkError(f"Network error on Webtoon API: {e}") from e

        try:
            response.encoding = 'utf-8'
            res_json = response.json()
        except ValueError as e:
            logger.error(f"invalid_json_response url={signed_url} text={response.text}")
            raise NetworkError("Failed to parse JSON response") from e

        return res_json
