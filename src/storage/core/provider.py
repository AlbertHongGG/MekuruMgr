from abc import ABC, abstractmethod
from src.storage.core.archive_interface import IArchiveStorage
from src.storage.core.user_interface import IUserStorage

class IStorageProvider(ABC):
    """
    Abstract factory for storage engines.
    Each engine (e.g., JSON, SQLite) must implement this provider
    to return its specific repositories.
    """
    @abstractmethod
    def get_archive_storage(self) -> IArchiveStorage:
        pass
        
    @abstractmethod
    def get_user_storage(self) -> IUserStorage:
        pass
