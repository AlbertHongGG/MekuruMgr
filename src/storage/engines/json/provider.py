import logging
import os
from src.storage.core.provider import IStorageProvider
from src.storage.core.archive_interface import ILibraryStorage, ITaskStorage, IMediaStorage
from src.storage.engines.json.archive_repo import JsonLibraryStorage, JsonTaskStorage, LocalMediaStorage

logger = logging.getLogger(__name__)

class JsonStorageProvider(IStorageProvider):
    """
    Provides JSON-based implementations for all storage repositories.
    Manages singletons to ensure only one instance of each repository exists.
    """
    def __init__(self, data_dir: str):
        self._library_repo = None
        self._task_repo = None
        self._media_repo = None
        self.data_dir = data_dir

    def get_library_storage(self) -> ILibraryStorage:
        if self._library_repo is None:
            db_path = os.path.join(self.data_dir, "library.json")
            self._library_repo = JsonLibraryStorage(db_path=db_path)
            logger.info(f"JSON Library Storage Initialized at {db_path}")
        return self._library_repo
        
    def get_task_storage(self) -> ITaskStorage:
        if self._task_repo is None:
            db_path = os.path.join(self.data_dir, "tasks.json")
            self._task_repo = JsonTaskStorage(db_path=db_path)
            logger.info(f"JSON Task Storage Initialized at {db_path}")
        return self._task_repo
        
    def get_media_storage(self) -> IMediaStorage:
        if self._media_repo is None:
            self._media_repo = LocalMediaStorage(data_dir=self.data_dir)
            logger.info(f"Local Media Storage Initialized at {self.data_dir}")
        return self._media_repo
