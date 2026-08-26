from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class AppConfig(BaseSettings):
    """
    Global Application Configuration.
    Reads from .env using the APP_ prefix.
    """
    model_config = SettingsConfigDict(env_prefix="APP_", env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # The default provider to use if none is specified
    default_provider: str = Field(default="comicwifi")
    
    # The default comic ID to use for testing/default CLI commands
    default_comic_id: str = Field(default="7e68b404b74ffff98a9b77d4f24abefe")
    
    # Server settings
    host: str = Field(default="127.0.0.1")
    port: int = Field(default=8000)
    
    # Environment
    debug: bool = Field(default=False)
    
    # Storage
    storage_engine: str = Field(default="json")

app_settings = AppConfig()
