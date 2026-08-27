from enum import Enum
import logging
from src.storage.core.provider import IStorageProvider
from src.storage.engines.json.provider import JsonStorageProvider
from src.storage.engines.sqlite.provider import SqliteStorageProvider
from src.storage.core.archive_interface import ILibraryStorage, ITaskStorage, IMediaStorage

logger = logging.getLogger(__name__)

class StorageEngine(str, Enum):
    JSON = "json"
    SQLITE = "sqlite"

class StorageFactory:
    def __init__(self, config):
        self.config = config
        self._provider = self._create_provider()

    def _create_provider(self) -> IStorageProvider:
        engine = self.config.engine
        data_dir = self.config.data_dir
        
        if engine == StorageEngine.JSON:
            provider = JsonStorageProvider(data_dir=data_dir)
            logger.info(f"Storage Provider Initialized: {StorageEngine.JSON.value}")
            return provider
        elif engine == StorageEngine.SQLITE:
            provider = SqliteStorageProvider(data_dir=data_dir)
            logger.info(f"Storage Provider Initialized: {StorageEngine.SQLITE.value}")
            return provider
        else:
            raise ValueError(f"Unsupported storage engine: {engine}")

    def get_library_storage(self) -> ILibraryStorage:
        return self._provider.get_library_storage()

    def get_task_storage(self) -> ITaskStorage:
        return self._provider.get_task_storage()

    def get_media_storage(self) -> IMediaStorage:
        return self._provider.get_media_storage()
