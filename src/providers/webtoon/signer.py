import time
import hmac
import hashlib
import base64
import urllib.parse
from .config import SECRET_KEY

class WebtoonUrlSigner:
    """
    負責 Webtoon API 的 HMAC-SHA1 URL 簽名 (msgpad & md)
    """
    def __init__(self, secret_key: bytes = SECRET_KEY):
        self.secret_key = secret_key

    def sign_url(self, url: str, msgpad: str = None) -> str:
        """
        依照指定步驟計算 HMAC-SHA1 並附加簽名至 URL。
        """
        # 決定 timestamp，如果沒有給定則使用當下時間 (毫秒)
        if msgpad is None:
            msgpad = str(int(time.time() * 1000))
        
        # 擷取 URL 並強制擷取前 255 個字元
        truncated_url = url[:255]
        
        # 在截斷後的字串尾部，直接無縫拼接上 msgpad 的數值
        payload_str = truncated_url + msgpad
        payload_bytes = payload_str.encode('utf-8')
        
        # Hash 運算：帶入 HMAC-SHA1 演算法，得出 Byte 陣列
        mac = hmac.new(self.secret_key, payload_bytes, hashlib.sha1)
        digest = mac.digest()
        
        # Base64 編碼：轉換成可讀字串
        b64_str = base64.b64encode(digest).decode('utf-8')
        
        # URL 編碼：UTF-8 的 URL Encode
        md = urllib.parse.quote(b64_str, safe='')
        
        # 組合最終網址
        separator = "&" if "?" in url else "?"
        if url.endswith("&") or url.endswith("?"):
            separator = ""
            
        final_url = f"{url}{separator}msgpad={msgpad}&md={md}"
        
        return final_url
