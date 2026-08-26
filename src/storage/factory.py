from enum import Enum
import logging
from src.storage.core.provider import IStorageProvider
from src.storage.engines.json.provider import JsonStorageProvider

from typing import Optional
from src.core.config import app_settings

logger = logging.getLogger(__name__)

class StorageEngine(str, Enum):
    JSON = "json"

class StorageFactory:
    _providers = {}

    @classmethod
    def get_provider(cls, engine: Optional[StorageEngine] = None) -> IStorageProvider:
        if engine is None:
            engine = StorageEngine(app_settings.storage_engine.lower())
            
        if engine not in cls._providers:
            if engine == StorageEngine.JSON:
                cls._providers[engine] = JsonStorageProvider()
                logger.info(f"Storage Provider Initialized: {engine.value}")
            else:
                raise ValueError(f"Unknown storage engine: {engine}")
        return cls._providers[engine]
