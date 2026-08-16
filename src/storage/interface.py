from abc import ABC, abstractmethod
from typing import List, Optional

from src.domain.models import ArchivedComic

class IArchiveStorage(ABC):
    """
    Facade interface for complete comic storage operations (both metadata and physical media).
    Any engine using this interface knows nothing about how the underlying data is stored.
    """
    
    # --- Metadata Operations ---
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
        """Delete a tracked comic and all its media from the storage."""
        pass
        
    @abstractmethod
    def list_comics(self) -> List[ArchivedComic]:
        """List all tracked comics."""
        pass

    # --- Media Operations ---
    @abstractmethod
    async def save_image(self, provider_id: str, comic_id: str, chapter_id: str, index: int, content: bytes, content_type: str) -> str:
        """
        Saves a binary image (atomic) and returns its relative filename/identifier.
        If chapter_id is 'cover', saves as cover.
        """
        pass

    @abstractmethod
    def get_chapter_images(self, provider_id: str, comic_id: str, chapter_id: str) -> List[str]:
        """
        Returns a sorted list of relative paths/URLs to the actual image files.
        """
        pass

    @abstractmethod
    def count_downloaded_images(self, provider_id: str, comic_id: str, chapter_id: str) -> int:
        """
        Counts physical/valid files in the chapter storage to verify completion.
        """
        pass
        
    @abstractmethod
    def check_image_exists(self, provider_id: str, comic_id: str, chapter_id: str, index: int) -> bool:
        """
        For image-level resuming: checks if a specific index was already downloaded and is valid.
        """
        pass

    @abstractmethod
    def is_chapter_missing(self, provider_id: str, comic_id: str, chapter_id: str) -> bool:
        """
        Checks if the chapter storage completely doesn't exist.
        """
        pass
