from abc import ABC, abstractmethod
from typing import List, Dict, Any, TypeVar

from src.domain.models import Comic, Chapter, PageImage

class BaseComicProvider(ABC):
    """
    The standard contract that ALL comic providers must implement.
    Whether it's ComicWifi, a friend's server, or a local file source,
    it MUST implement these methods and return standardized domain models.
    """
    
    @property
    @abstractmethod
    def provider_id(self) -> str:
        """A unique identifier for this provider (e.g., 'comicwifi')."""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """A human-readable name for this provider (e.g., 'ComicWifi Official')."""
        pass

    @abstractmethod
    def get_comic_detail(self, comic_id: str) -> Comic:
        """Fetch basic details and metadata for a specific comic."""
        pass

    @abstractmethod
    def get_chapter_list(self, comic_id: str) -> List[Chapter]:
        """Fetch the list of all available chapters for a comic."""
        pass

    @abstractmethod
    def get_chapter_images(self, comic_id: str, chapter_id: str) -> List[PageImage]:
        """Fetch the actual image pages for a specific chapter."""
        pass

    @abstractmethod
    def search_comics(self, keyword: str, page: int = 1, page_size: int = 30) -> List[Comic]:
        """Search for comics matching a keyword."""
        pass

    @abstractmethod
    def explore_comics(self, page: int = 1, page_size: int = 30) -> List[Comic]:
        """Explore/discover comics from the provider."""
        pass
