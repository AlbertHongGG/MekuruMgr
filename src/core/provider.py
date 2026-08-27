from abc import ABC, abstractmethod
from typing import List, Dict, Any, TypeVar

from src.domain.models import ComicSearchResult, ComicDetail, Chapter, PageImage, ComicExploreResult

class BaseComicProvider(ABC):
    """
    The standard contract that ALL comic providers must implement.
    """
    
    @property
    @abstractmethod
    def provider_id(self) -> str:
        """A unique identifier for this provider (e.g., 'comicwifi')."""
        pass

    @property
    def aliases(self) -> List[str]:
        """Alternative identifiers for this provider (e.g., ['comicwf']). Defaults to empty list."""
        return []

    @classmethod
    def get_config_class(cls) -> Any:
        """
        Optional: Return the pydantic settings class for this provider's configuration.
        This allows dynamic generation of environment variables and DI.
        """
        return None

    def add_api_hook(self, hook: Any) -> None:
        """
        Add an interceptor hook to the underlying HTTP clients.
        Providers should override this if they have internal HTTP clients.
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """A human-readable name for this provider (e.g., 'ComicWifi Official')."""
        pass

    @abstractmethod
    def get_comic_detail(self, comic_id: str) -> ComicDetail:
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
    def search_comics(self, keyword: str, page: int = 1, page_size: int = 30) -> List[ComicSearchResult]:
        """Search for comics matching a keyword."""
        pass

    @abstractmethod
    def explore_comics(self, page: int = 1, page_size: int = 30) -> List[ComicExploreResult]:
        """Explore/discover comics from the provider."""
        pass

    async def download_image(self, client: Any, url: str) -> tuple[bytes, str]:
        """
        Download an image using the provider's specific mechanism.
        Returns a tuple of (content bytes, content_type string).
        """
        response = await client.get(url, timeout=30.0)
        response.raise_for_status()
        content_type = response.headers.get('content-type', '')
        return response.content, content_type
