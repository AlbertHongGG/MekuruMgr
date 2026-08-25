import hashlib
import time
import json
import base64
from typing import Tuple, Dict, Any
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

class ManwaCrypto:
    """
    Handles payload decryption and header signature generation for Manwa provider.
    """
    TOKEN_SALT = "jsdaghuiaonfyudsfnkgjdfkdd"
    KEY_SALT = ",noiusdfy73osadjap012njdsfn"

    @classmethod
    def generate_headers(cls) -> Tuple[Dict[str, str], str, str]:
        """
        Generates required headers including dynamic signature and timestamp.
        Returns:
            headers, x_token, devid
        """
        devid = str(int(time.time() * 1000))
        token_raw = f"{devid},{cls.TOKEN_SALT}"
        x_token = hashlib.md5(token_raw.encode('utf-8')).hexdigest()
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-A315G) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36 mwa-1.1.26+1',
            'Accept': 'application/json, text/plain, */*',
            'devid': devid,
            'x-token': x_token,
            'Origin': 'http://mseeowpm1.xyz',
            'Referer': 'http://mseeowpm1.xyz',
            'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'Content-Type': 'application/json; charset=utf-8'
        }
        return headers, x_token, devid

    @classmethod
    def try_aes_decrypt(cls, cipher_bytes: bytes, seed: str) -> str:
        """
        Attempts AES-256-ECB decryption using the derived key from the given seed.
        """
        key_str = hashlib.md5(f"{seed}{cls.KEY_SALT}".encode('utf-8')).hexdigest()
        key_bytes = key_str.encode('utf-8')
        
        cipher = AES.new(key_bytes, AES.MODE_ECB)
        decrypted = cipher.decrypt(cipher_bytes)
        return unpad(decrypted, AES.block_size).decode('utf-8')

    @classmethod
    def decrypt_data(cls, raw_response_text: str, x_token: str, devid: str) -> Dict[str, Any]:
        """
        Cleans the response and decrypts the Base64 AES payload into a JSON dict.
        """
        cleaned_str = raw_response_text.strip()
        if cleaned_str.startswith('"') and cleaned_str.endswith('"'):
            cleaned_str = cleaned_str[1:-1]
        cleaned_str = cleaned_str.replace(r'\/', '/').replace('\\', '')
        
        cipher_bytes = base64.b64decode(cleaned_str)

        for seed in [x_token, devid]:
            try:
                plain_text = cls.try_aes_decrypt(cipher_bytes, seed)
                return json.loads(plain_text)
            except Exception:
                continue
                
        raise ValueError("Decryption failed: Could not match key seed for payload.")

    @classmethod
    def decrypt_image(cls, encrypted_bytes: bytes) -> bytes:
        """
        Decrypts downloaded comic image binary data using AES-128-CBC.
        """
        key = b"my2ecret782ecret"
        iv = b"my2ecret782ecret"
        
        cipher = AES.new(key, AES.MODE_CBC, iv)
        return unpad(cipher.decrypt(encrypted_bytes), AES.block_size)
