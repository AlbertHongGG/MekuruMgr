import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, BaseModel

class ServerConfig(BaseModel):
    host: str = Field(default="127.0.0.1", description="API Server IP")
    port: int = Field(default=8000, description="API Server Port")

class StorageConfig(BaseModel):
    engine: str = Field(default="sqlite", description="Storage engine (sqlite or json)")
    data_dir: str = Field(default="./data", description="Storage directory")

class EngineConfig(BaseModel):
    worker_count: int = Field(default=5, description="Download worker count")
    max_concurrent_tasks: int = Field(default=5, description="Max concurrent downloads")

class AppConfig(BaseSettings):
    """
    Root configuration for the application.
    """
    model_config = SettingsConfigDict(
        env_prefix="APP_", 
        env_file=os.environ.get("ENV_FILE", ".env"), 
        env_file_encoding="utf-8", 
        extra="ignore",
        env_nested_delimiter="__"
    )

    debug: bool = Field(default=False, description="Enable debug mode")
    default_provider: str = Field(default="comicwifi", description="Default provider")

    server: ServerConfig = Field(default_factory=ServerConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    engine: EngineConfig = Field(default_factory=EngineConfig)
