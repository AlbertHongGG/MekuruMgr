from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class AppConfig(BaseSettings):
    """
    Application Configuration
    Uses environment variables or .env file for easy overrides.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    base_url: str = Field(default="https://api.comicwifi.com", description="Comic API Base URL")
    
    # Device Fingerprinting Headers
    # Defaults taken from the intercepted packet to avoid blocking
    user_agent: str = Field(default="ktor-client")
    device_id: str = Field(default="2c9b9cb61659a16b")
    app_version: str = Field(default="1.1.1")
    app_version_code: str = Field(default="111")
    channel_no: str = Field(default="3")
    app_channel: str = Field(default="3")
    app_id: str = Field(default="6")
    os_version: str = Field(default="13")
    device_model: str = Field(default="SM-A326BR")
    device_brand: str = Field(default="samsung")
    device_make: str = Field(default="samsung")
    screen_width: str = Field(default="720")
    screen_height: str = Field(default="1445")
    os_type: str = Field(default="1")
    network_type: str = Field(default="0")
    language: str = Field(default="zh")
    device_language: str = Field(default="zh")
    time_zone: str = Field(default="GMT+08:00")
    lower_flow: str = Field(default="No")
    imei: str = Field(default="")
    mac: str = Field(default="")
    oaid: str = Field(default="")
    userid: str = Field(default="-1")
    token: str = Field(default="")
    isvpn: str = Field(default="")
    languagecode: str = Field(default="")

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

settings = AppConfig()
