from enum import Enum
import logging
from src.storage.interface import IArchiveStorage
from src.storage.local_storage import LocalJsonStorage

logger = logging.getLogger(__name__)

class StorageEngine(str, Enum):
    JSON = "json"

class StorageFactory:
    _instances = {}

    @classmethod
    def get_storage(cls, engine: StorageEngine = StorageEngine.JSON) -> IArchiveStorage:
        if engine not in cls._instances:
            if engine == StorageEngine.JSON:
                cls._instances[engine] = LocalJsonStorage()
                logger.info(f"Archive Storage Initialized: {engine.value}")
            else:
                raise ValueError(f"Unknown storage engine: {engine}")
        return cls._instances[engine]
