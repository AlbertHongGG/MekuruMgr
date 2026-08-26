from abc import ABC, abstractmethod
from src.storage.core.archive_interface import ILibraryStorage, ITaskStorage, IMediaStorage

class IStorageProvider(ABC):
    """
    Abstract factory for storage engines.
    Each engine (e.g., JSON, SQLite) must implement this provider
    to return its specific repositories.
    """
    @abstractmethod
    def get_library_storage(self) -> ILibraryStorage:
        pass

    @abstractmethod
    def get_task_storage(self) -> ITaskStorage:
        pass
        
    @abstractmethod
    def get_media_storage(self) -> IMediaStorage:
        pass
