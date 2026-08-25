import logging
from typing import Dict, Any, Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.domain.exceptions import NetworkError, ApiLogicError
from src.core.http_client import BaseHttpClient
from .config import BASE_URL, TOKEN, IDENTIFIER
from .crypto import GuaziCrypto

logger = logging.getLogger(__name__)

class GuaziHttpClient(BaseHttpClient):
    """
    HTTP Client wrapper for Guazi.
    Handles field-level AES decryption of specific JSON fields and hook notifications.
    """
    def __init__(self):
        super().__init__(
            provider_id="guazi",
            base_url=BASE_URL,
            verify=False
        )
        # Default Headers
        self.client.headers.update({
            "devicetype": "android",
            "token": TOKEN,
            "user-agent": "okhttp/4.7.2",
            "accept-encoding": "gzip",
        })

    def _decrypt_dict(self, data: Any) -> Any:
        """
        Recursively traverse the JSON structure and decrypt 'name' and 'img' fields.
        """
        if isinstance(data, dict):
            for k, v in data.items():
                if k in ["name", "img"] and isinstance(v, str) and v:
                    try:
                        decrypted = GuaziCrypto.decrypt(v)
                        if decrypted:
                            data[k] = decrypted
                    except Exception as e:
                        logger.warning(f"Guazi decryption failed for field '{k}': {e}")
                else:
                    data[k] = self._decrypt_dict(v)
            return data
        elif isinstance(data, list):
            return [self._decrypt_dict(item) for item in data]
        else:
            return data

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(NetworkError),
        reraise=True
    )
    def request(self, method: str, endpoint: str, params: Optional[Dict[str, Any]] = None, data: Optional[Dict[str, Any]] = None) -> Any:
        # Automatically append required identifier and versionCode
        from .config import VERSION_CODE, IDENTIFIER
        
        if method.upper() == "GET":
            if params is None:
                params = {}
            params["identifier"] = IDENTIFIER
            params["versionCode"] = VERSION_CODE
        else:
            if data is None:
                data = {}
            data["identifier"] = IDENTIFIER
            data["versionCode"] = VERSION_CODE

        try:
            if method.upper() == "GET":
                response = self.client.get(endpoint, params=params)
            else:
                headers = {"content-type": "application/x-www-form-urlencoded"} if data else None
                response = self.client.post(endpoint, data=data, headers=headers)
                
            response.raise_for_status()
        except httpx.HTTPError as e:
            logger.error(f"http_request_failed endpoint={endpoint} error={str(e)}")
            raise NetworkError(f"Network error on Guazi API: {e}") from e

        try:
            res_json = response.json()
        except ValueError as e:
            logger.error(f"invalid_json_response endpoint={endpoint} text={response.text}")
            raise NetworkError("Failed to parse JSON response") from e

        # Validate logic error
        error_code = res_json.get("error_code", -1)
        if error_code != 0:
            msg = res_json.get("msg", "Unknown error")
            logger.warning(f"guazi_api_error code={error_code} msg={msg}")
            raise ApiLogicError(msg, error_code)

        # Decrypt specific fields
        res_json = self._decrypt_dict(res_json)
        
        # Trigger hooks with decrypted data
        self.notify_hooks(endpoint, res_json)

        return res_json.get("data")
