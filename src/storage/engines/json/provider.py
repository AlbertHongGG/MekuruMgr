import logging
from src.storage.core.provider import IStorageProvider
from src.storage.core.archive_interface import IArchiveStorage
from src.storage.engines.json.archive_repo import LocalJsonStorage

logger = logging.getLogger(__name__)

class JsonStorageProvider(IStorageProvider):
    """
    Provides JSON-based implementations for all storage repositories.
    Manages singletons to ensure only one instance of each repository exists.
    """
    def __init__(self):
        self._archive_repo = None

    def get_archive_storage(self) -> IArchiveStorage:
        if self._archive_repo is None:
            self._archive_repo = LocalJsonStorage()
            logger.info("JSON Archive Storage Initialized")
        return self._archive_repo
