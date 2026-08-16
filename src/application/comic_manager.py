import logging
from typing import List, Optional, Union

from src.core.provider import BaseComicProvider
from src.domain.models import Comic, Chapter, PageImage
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

    def use(self, provider_id: Union[str, BuiltinProvider]) -> "ComicManager":
        """Switch the active provider dynamically by its ID."""
        # Enum values in Python are instance of the Enum class. Since BuiltinProvider inherits from str, 
        # it can be passed directly, but we call str() to ensure the registry gets the pure string key.
        provider_key = str(provider_id.value if isinstance(provider_id, BuiltinProvider) else provider_id)
        self._active_provider = registry.get_provider(provider_key)
        logger.info(f"Switched Provider: [cyan]{self._active_provider.provider_name}[/] (ID: [magenta]{provider_key}[/])")
        return self

    @property
    def provider(self) -> BaseComicProvider:
        """Get the currently active provider. Raises an error if none is selected."""
        if not self._active_provider:
            raise RuntimeError("No provider selected. Call use('provider_id') first.")
        return self._active_provider

    def fetch_comic_detail(self, comic_id: str) -> Comic:
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
        """List all available providers."""
        return registry.list_providers()

    def search_comics(self, keyword: str, page: int = 1, page_size: int = 30) -> List[Comic]:
        """Search for comics using the active provider."""
        logger.info(f"Searching comics with keyword: [green]{keyword}[/] from [magenta]{self.provider.provider_id}[/]")
        return self.provider.search_comics(keyword, page, page_size)
