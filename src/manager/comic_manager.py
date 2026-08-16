import structlog
from typing import List, Optional

from src.core.provider import BaseComicProvider
from src.core.domain_models import Comic, Chapter, PageImage
from src.core.registry import registry

logger = structlog.get_logger(__name__)

class ComicManager:
    """
    High-level business logic orchestrator for the Comic platform.
    Now entirely decoupled from specific comic sources using Dependency Injection.
    """
    def __init__(self, default_provider_id: Optional[str] = None):
        self._active_provider: Optional[BaseComicProvider] = None
        if default_provider_id:
            self.use(default_provider_id)

    def use(self, provider_id: str) -> "ComicManager":
        """Switch the active provider dynamically by its ID."""
        self._active_provider = registry.get_provider(provider_id)
        logger.info("manager_switched_provider", provider_id=provider_id, name=self._active_provider.provider_name)
        return self

    @property
    def provider(self) -> BaseComicProvider:
        """Get the currently active provider. Raises an error if none is selected."""
        if not self._active_provider:
            raise RuntimeError("No provider selected. Call use('provider_id') first.")
        return self._active_provider

    def fetch_comic_detail(self, comic_id: str) -> Comic:
        """Fetch the details of a specific comic using the active provider."""
        logger.info("fetch_comic_detail", comic_id=comic_id, provider=self.provider.provider_id)
        return self.provider.get_comic_detail(comic_id)

    def fetch_all_chapters(self, comic_id: str) -> List[Chapter]:
        """Fetch all chapters for a specific comic using the active provider."""
        logger.info("fetch_all_chapters", comic_id=comic_id, provider=self.provider.provider_id)
        return self.provider.get_chapter_list(comic_id)

    def fetch_chapter_images(self, comic_id: str, chapter_id: str) -> List[PageImage]:
        """Fetch all images for a specific chapter using the active provider."""
        logger.info("fetch_chapter_images", comic_id=comic_id, chapter_id=chapter_id, provider=self.provider.provider_id)
        return self.provider.get_chapter_images(comic_id, chapter_id)

    def get_available_providers(self) -> List[str]:
        """List all available providers."""
        return registry.list_providers()
