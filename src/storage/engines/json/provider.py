import logging
from src.storage.core.provider import IStorageProvider
from src.storage.core.archive_interface import ILibraryStorage, ITaskStorage, IMediaStorage
from src.storage.engines.json.archive_repo import JsonLibraryStorage, JsonTaskStorage, LocalMediaStorage

logger = logging.getLogger(__name__)

class JsonStorageProvider(IStorageProvider):
    """
    Provides JSON-based implementations for all storage repositories.
    Manages singletons to ensure only one instance of each repository exists.
    """
    def __init__(self):
        self._library_repo = None
        self._task_repo = None
        self._media_repo = None

    def get_library_storage(self) -> ILibraryStorage:
        if self._library_repo is None:
            self._library_repo = JsonLibraryStorage()
            logger.info("JSON Library Storage Initialized")
        return self._library_repo
        
    def get_task_storage(self) -> ITaskStorage:
        if self._task_repo is None:
            self._task_repo = JsonTaskStorage()
            logger.info("JSON Task Storage Initialized")
        return self._task_repo
        
    def get_media_storage(self) -> IMediaStorage:
        if self._media_repo is None:
            self._media_repo = LocalMediaStorage()
            logger.info("Local Media Storage Initialized")
        return self._media_repo
