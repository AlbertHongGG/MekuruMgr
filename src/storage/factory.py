from enum import Enum
import logging
from src.storage.core.provider import IStorageProvider
from src.storage.engines.json.provider import JsonStorageProvider

logger = logging.getLogger(__name__)

class StorageEngine(str, Enum):
    JSON = "json"

class StorageFactory:
    _providers = {}

    @classmethod
    def get_provider(cls, engine: StorageEngine = StorageEngine.JSON) -> IStorageProvider:
        if engine not in cls._providers:
            if engine == StorageEngine.JSON:
                cls._providers[engine] = JsonStorageProvider()
                logger.info(f"Storage Provider Initialized: {engine.value}")
            else:
                raise ValueError(f"Unknown storage engine: {engine}")
        return cls._providers[engine]
