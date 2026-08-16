import logging
import importlib
from pathlib import Path
from typing import Dict, Type
from src.core.provider import BaseComicProvider
from src.domain.exceptions import AppBaseError

logger = logging.getLogger(__name__)

class ProviderRegistry:
    """
    Central registry for all comic providers.
    Uses the Singleton pattern to keep a single active registry.
    """
    def __init__(self):
        self._providers: Dict[str, BaseComicProvider] = {}

    def register(self, provider_class: Type[BaseComicProvider]):
        """Register a provider class with the system."""
        provider = provider_class()
        self._providers[provider.provider_id] = provider
        logger.info(f"Provider Registered: {provider.provider_name} (ID: {provider.provider_id})")

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
                module_name = f"src.providers.{provider_path.name}.provider"
                try:
                    importlib.import_module(module_name)
                    logger.debug(f"Successfully loaded provider module: {module_name}")
                except Exception as e:
                    logger.error(f"Failed to load provider module {module_name}: {e}")

registry = ProviderRegistry()
