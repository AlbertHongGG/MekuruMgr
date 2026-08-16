from abc import ABC, abstractmethod
from typing import List, Optional
from src.domain.models import ArchivedComic

class IStorage(ABC):
    """
    Abstract Base Class defining the contract for Comic Storage.
    Any concrete storage implementation (JSON, SQLite, PostgreSQL) must satisfy this interface.
    """
    
    @property
    @abstractmethod
    def data_dir(self):
        """Get the base data directory path for media storage."""
        pass

    @abstractmethod
    def get_comic(self, provider_id: str, comic_id: str) -> Optional[ArchivedComic]:
        """Retrieve a tracked comic by its ID."""
        pass

    @abstractmethod
    def save_comic(self, comic: ArchivedComic) -> None:
        """Save or update a tracked comic."""
        pass

    @abstractmethod
    def delete_comic(self, provider_id: str, comic_id: str) -> None:
        """Delete a tracked comic from the storage."""
        pass
        
    @abstractmethod
    def list_comics(self) -> List[ArchivedComic]:
        """List all tracked comics."""
        pass
