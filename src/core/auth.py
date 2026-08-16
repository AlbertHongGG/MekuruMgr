import time
import hashlib
import urllib.parse
from typing import Generator
import httpx

class ComicWifiAuth(httpx.Auth):
    """
    HTTPx Auth interceptor for Comic API.
    Automatically injects requestTime and sign into the request body.
    """
    SALT = "#X2u%rXE^dk%FUpdRH8BvjmZnPDDXLhZ"

    def auth_flow(self, request: httpx.Request) -> Generator[httpx.Request, httpx.Response, None]:
        # Only process POST requests with form-urlencoded body
        if request.method == "POST" and request.headers.get("Content-Type", "").startswith("application/x-www-form-urlencoded"):
            # Parse existing body
            body_bytes = request.read()
            body_str = body_bytes.decode("utf-8")
            params = dict(urllib.parse.parse_qsl(body_str, keep_blank_values=True))

            # Inject requestTime
            request_time = str(int(time.time() * 1000))
            params["requestTime"] = request_time

            # Generate sign
            sign = self._generate_sign(params)
            params["sign"] = sign

            # Re-encode body
            new_body = urllib.parse.urlencode(params)
            new_body_bytes = new_body.encode("utf-8")
            
            # Create a new headers dict and let httpx calculate Content-Length
            new_headers = request.headers.copy()
            if "Content-Length" in new_headers:
                del new_headers["Content-Length"]
            if "content-length" in new_headers:
                del new_headers["content-length"]
            
            yield httpx.Request(
                method=request.method,
                url=request.url,
                headers=new_headers,
                content=new_body_bytes
            )
        else:
            yield request

    def _generate_sign(self, params: dict[str, str]) -> str:
        """
        1. Sort keys alphabetically A-Z
        2. Concat Salt + values
        3. Return MD5 lower hex
        """
        sorted_keys = sorted(params.keys())
        concat_str = self.SALT + "".join([params[k] for k in sorted_keys])
        return hashlib.md5(concat_str.encode("utf-8")).hexdigest()
