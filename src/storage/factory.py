from enum import Enum
import logging
from src.storage.core.provider import IStorageProvider
from src.storage.engines.json.provider import JsonStorageProvider

from typing import Optional
from src.core.config import app_settings

logger = logging.getLogger(__name__)

class StorageEngine(str, Enum):
    JSON = "json"
    SQLITE = "sqlite"

class StorageFactory:
    _providers = {}

    @classmethod
    def get_provider(cls, engine: Optional[StorageEngine] = None) -> IStorageProvider:
        if engine is None:
            # Fallback to json if setting is somehow invalid
            engine_str = app_settings.storage_engine.lower()
            engine = StorageEngine(engine_str) if engine_str in [e.value for e in StorageEngine] else StorageEngine.JSON
            
        if engine not in cls._providers:
            if engine == StorageEngine.JSON:
                cls._providers[engine] = JsonStorageProvider()
                logger.info(f"Storage Provider Initialized: {engine.value}")
            elif engine == StorageEngine.SQLITE:
                from src.storage.engines.sqlite.provider import SqliteStorageProvider
                cls._providers[engine] = SqliteStorageProvider()
                logger.info(f"Storage Provider Initialized: {engine.value}")
            else:
                raise ValueError(f"Unknown storage engine: {engine}")
        return cls._providers[engine]
