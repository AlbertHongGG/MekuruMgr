from enum import Enum
from src.storage.interface import IStorage
from src.storage.local_json import LocalJsonStorage
import structlog

logger = structlog.get_logger(__name__)

class StorageEngine(str, Enum):
    JSON = "json"

class StorageFactory:
    """
    Factory for creating Storage instances.
    Enables swapping out storage backends (e.g. JSON, SQLite) without touching application code.
    """
    _instance: IStorage = None

    @classmethod
    def get_storage(cls, engine: StorageEngine = StorageEngine.JSON) -> IStorage:
        if cls._instance is not None:
            return cls._instance
            
        if engine == StorageEngine.JSON:
            cls._instance = LocalJsonStorage()
            logger.info("storage_initialized", engine=engine.value)
        else:
            raise ValueError(f"Unknown storage engine: {engine}")
            
        return cls._instance
