import base64
import hashlib
from datetime import datetime
from typing import Optional
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

class GuaziCrypto:
    """
    AES-CBC encryption/decryption utilities for Guazi.
    """

    @staticmethod
    def _md5(text: str) -> str:
        return hashlib.md5(text.encode("utf-8")).hexdigest().lower()

    @classmethod
    def get_key_and_iv(cls, date_str: Optional[str] = None) -> tuple[str, str]:
        """
        Derives Key and IV based on date string.
        """
        if not date_str:
            date_str = datetime.now().strftime("%Y%m%d")

        raw_str = f"guazi{date_str}"
        full_md5 = cls._md5(raw_str)

        key = full_md5  # 32 chars -> AES-256 Key
        iv = full_md5[8:24]  # Middle 16 chars -> 16 Bytes IV
        return key, iv

    @classmethod
    def decrypt(cls, ciphertext_b64: str, date_str: Optional[str] = None) -> str:
        """
        Decrypts a Base64 AES-CBC encrypted string.
        """
        if not ciphertext_b64:
            return ""

        key, iv = cls.get_key_and_iv(date_str)
        key_bytes = key.encode("utf-8")
        iv_bytes = iv.encode("utf-8")
        
        try:
            encrypted_data = base64.b64decode(ciphertext_b64)
            cipher = AES.new(key_bytes, AES.MODE_CBC, iv_bytes)
            decrypted_bytes = unpad(cipher.decrypt(encrypted_data), AES.block_size)
            return decrypted_bytes.decode("utf-8")
        except Exception:
            # Fallback for old cache or wrong date, though it's rare
            return ""

    @classmethod
    def encrypt(cls, plaintext: str, date_str: Optional[str] = None) -> str:
        """
        Encrypts a string and returns a Base64 string.
        Used for encrypting search keywords.
        """
        if not plaintext:
            return ""

        key, iv = cls.get_key_and_iv(date_str)
        key_bytes = key.encode("utf-8")
        iv_bytes = iv.encode("utf-8")

        cipher = AES.new(key_bytes, AES.MODE_CBC, iv_bytes)
        padded_data = pad(plaintext.encode("utf-8"), AES.block_size)
        encrypted_bytes = cipher.encrypt(padded_data)
        return base64.b64encode(encrypted_bytes).decode("utf-8")
