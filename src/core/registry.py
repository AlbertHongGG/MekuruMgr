import structlog
import importlib
from pathlib import Path
from typing import Dict
from src.core.provider import BaseComicProvider
from src.core.exceptions import AppBaseError

logger = structlog.get_logger(__name__)

class ProviderRegistry:
    """
    Central registry for all comic providers.
    Uses the Singleton pattern to keep a single active registry.
    """
    def __init__(self):
        self._providers: Dict[str, BaseComicProvider] = {}

    def register(self, provider_class: type[BaseComicProvider]):
        """Register a provider class with the system."""
        provider = provider_class()
        self._providers[provider.provider_id] = provider
        logger.info("provider_registered", name=provider.provider_name, provider_id=provider.provider_id)

    def get_provider(self, provider_id: str) -> BaseComicProvider:
        """Retrieve an instantiated provider by its ID."""
        if provider_id not in self._providers:
            raise AppBaseError(f"Provider '{provider_id}' is not registered.")
        return self._providers[provider_id]

    def get_all(self) -> Dict[str, BaseComicProvider]:
        return self._providers.copy()

    def load_all_providers(self):
        """
        Dynamically discover and import all providers in the src.providers package.
        This removes the need for manual imports in main entrypoints.
        """
        # Get the path to src/providers
        providers_dir = Path(__file__).parent.parent / "providers"
        
        if not providers_dir.exists() or not providers_dir.is_dir():
            return
            
        # Iterate over all directories in src/providers
        for provider_path in providers_dir.iterdir():
            if provider_path.is_dir() and not provider_path.name.startswith("_"):
                # Try to import the 'provider.py' module inside the directory
                provider_module = f"src.providers.{provider_path.name}.provider"
                try:
                    importlib.import_module(provider_module)
                    logger.debug("dynamic_import_success", module=provider_module)
                except ImportError as e:
                    logger.error("dynamic_import_failed", module=provider_module, error=str(e))

registry = ProviderRegistry()
