from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class ComicWifiConfig(BaseSettings):
    """
    Configuration strictly bound to the 'COMICWIFI_' namespace in the .env file.
    No hardcoded values are allowed here. Everything is loaded dynamically.
    """
    model_config = SettingsConfigDict(env_prefix="COMICWIFI_", env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # API Base URL
    base_url: str = Field(default="https://api.comicwifi.com")

    # Device Fingerprinting Headers
    user_agent: str
    device_id: str
    app_version: str
    app_version_code: str
    channel_no: str
    app_channel: str
    app_id: str
    os_version: str
    device_model: str
    device_brand: str
    device_make: str
    screen_width: str
    screen_height: str
    os_type: str
    network_type: str
    language: str
    device_language: str
    time_zone: str
    lower_flow: str
    imei: str
    mac: str
    oaid: str
    userid: str
    token: str
    isvpn: str
    languagecode: str

    @property
    def http_headers(self) -> dict[str, str]:
        """Returns standard headers required by the server."""
        return {
            "accept": "application/json",
            "accept-charset": "UTF-8",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "user-agent": self.user_agent,
            "deviceid": self.device_id,
            "language": self.language,
            "device_language": self.device_language,
            "time-zone": self.time_zone,
            "lower-flow": self.lower_flow,
            "appversion": self.app_version,
            "appversioncode": self.app_version_code,
            "channelno": self.channel_no,
            "appchannel": self.app_channel,
            "appid": self.app_id,
            "imei": self.imei,
            "osv": self.os_version,
            "model": self.device_model,
            "brand": self.device_brand,
            "make": self.device_make,
            "mac": self.mac,
            "sw": self.screen_width,
            "sh": self.screen_height,
            "os": self.os_type,
            "net-work": self.network_type,
            "oaid": self.oaid,
            "userid": self.userid,
            "token": self.token,
            "isvpn": self.isvpn,
            "languagecode": self.languagecode,
            "accept-encoding": "gzip",
        }

settings = ComicWifiConfig()
