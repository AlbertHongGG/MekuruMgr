import hmac
import hashlib
import time
from typing import Dict
import httpx
from email.utils import parsedate_to_datetime

class CopymangaSigner:
    """
    Generates dynamic authentication headers for Copymanga API.
    Based on the HMAC-SHA256 algorithm with a fixed internal key.
    """
    def __init__(self):
        # Fixed key extracted from the App
        self.fixed_tap_string = b"3af08590311032efe0660550a0563a53"
        self._clock_offset: int = None

    def _sync_clock_offset(self) -> None:
        """Fetch the server's time and calculate the offset to our local clock."""
        try:
            # Make a lightweight request to grab the server's Date header
            with httpx.Client(verify=False, timeout=5.0) as client:
                res = client.head("https://api.copy202601.com/api/v3/comics", headers={"user-agent": "COPY/3.0.9"})
                if "Date" in res.headers:
                    server_dt = parsedate_to_datetime(res.headers["Date"])
                    server_ts = int(server_dt.timestamp())
                    local_ts = int(time.time())
                    self._clock_offset = server_ts - local_ts
                else:
                    self._clock_offset = -3  # fallback to -3 seconds if Date header is missing
        except Exception:
            self._clock_offset = -3  # fallback safely

    def get_auth_headers(self) -> Dict[str, str]:
        if self._clock_offset is None:
            self._sync_clock_offset()
            
        # 1. Get current timestamp (seconds), synchronized with server's clock
        current_timestamp_str = str(int(time.time()) + self._clock_offset)
        current_timestamp_bytes = current_timestamp_str.encode('utf-8')
        
        # 2. HMAC-SHA256(Key=tapString, Msg=Timestamp)
        signature = hmac.new(
            key=self.fixed_tap_string, 
            msg=current_timestamp_bytes, 
            digestmod=hashlib.sha256
        ).hexdigest()
        
        return {
            "x-auth-timestamp": current_timestamp_str,
            "x-auth-signature": signature
        }
