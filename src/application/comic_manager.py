import logging
from typing import List, Optional, Union

from src.core.provider import BaseComicProvider
from src.domain.models import ComicSearchResult, ComicDetail, Chapter, PageImage, ComicExploreResult
from src.core.registry import registry
from src.core.constants import BuiltinProvider

logger = logging.getLogger(__name__)

class ComicManager:
    """
    High-level business logic orchestrator for the Comic platform.
    Now entirely decoupled from specific comic sources using Dependency Injection.
    """
    def __init__(self, default_provider_id: Optional[Union[str, BuiltinProvider]] = None):
        self._active_provider: Optional[BaseComicProvider] = None
        if default_provider_id:
            self.use(default_provider_id)
    def resolve_id(self, provider_id: str) -> str:
        return registry.resolve_id(provider_id)

    def use(self, provider_id: str):
        resolved_id = self.resolve_id(provider_id)
        if hasattr(self, '_providers') and resolved_id in self._providers:
            self._active_provider = self._providers[resolved_id]
        else:
            # Fallback for tests not using DI
            p_class = registry.get_provider_class(resolved_id)
            self._active_provider = p_class()


    @property
    def provider(self) -> BaseComicProvider:
        """Get the currently active provider. Raises an error if none is selected."""
        if not self._active_provider:
            raise RuntimeError("No provider selected. Call use('provider_id') first.")
        return self._active_provider

    def fetch_comic_detail(self, comic_id: str) -> ComicDetail:
        """Fetch the details of a specific comic using the active provider."""
        logger.info(f"Fetching comic detail: [green]{comic_id}[/] from [magenta]{self.provider.provider_id}[/]")
        return self.provider.get_comic_detail(comic_id)

    def fetch_all_chapters(self, comic_id: str) -> List[Chapter]:
        """Fetch all chapters for a specific comic using the active provider."""
        logger.info(f"Fetching chapters for: [green]{comic_id}[/] from [magenta]{self.provider.provider_id}[/]")
        return self.provider.get_chapter_list(comic_id)

    def fetch_chapter_images(self, comic_id: str, chapter_id: str) -> List[PageImage]:
        """Fetch all images for a specific chapter using the active provider."""
        # Removing spammy log here since progress bar will handle it
        return self.provider.get_chapter_images(comic_id, chapter_id)
    def get_available_providers(self) -> List[str]:
        if hasattr(self, '_providers'):
            return list(self._providers.keys())
        return list(registry.get_all_classes().keys())


    def search_comics(self, keyword: str, page: int = 1, page_size: int = 30) -> List[ComicSearchResult]:
        """Search for comics using the active provider."""
        logger.info(f"Searching comics with keyword: [green]{keyword}[/] from [magenta]{self.provider.provider_id}[/]")
        return self.provider.search_comics(keyword, page, page_size)

    def explore_comics(self, page: int = 1, page_size: int = 30) -> List[ComicExploreResult]:
        """Explore/discover comics using the active provider."""
        logger.info(f"Exploring comics from [magenta]{self.provider.provider_id}[/]")
        return self.provider.explore_comics(page, page_size)
