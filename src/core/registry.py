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
    Uses the Singleton pattern to keep a single active registry of CLASSES.
    """
    def __init__(self):
        self._provider_classes: Dict[str, Type[BaseComicProvider]] = {}
        self._aliases: Dict[str, str] = {}

    def register(self, provider_id: str, provider_class: Type[BaseComicProvider], aliases: list[str] = None):
        """Register a provider class with the system."""
        aliases = aliases or []
        
        if provider_id in self._provider_classes:
            raise AppBaseError(f"Provider ID collision: '{provider_id}' is already registered.")
            
        self._provider_classes[provider_id] = provider_class
        
        # Register aliases
        for alias in aliases:
            if alias in self._provider_classes:
                raise AppBaseError(f"Provider alias collision: '{alias}' conflicts with an existing provider ID.")
            if alias in self._aliases:
                raise AppBaseError(f"Provider alias collision: '{alias}' is already registered by '{self._aliases[alias]}'.")
            self._aliases[alias] = provider_id
            
        logger.info(f"Provider Registered: {provider_id} (Aliases: {aliases})")

    def resolve_id(self, provider_id: str) -> str:
        """Resolve a given provider ID or alias to the primary provider ID."""
        if provider_id in self._provider_classes:
            return provider_id
        if provider_id in self._aliases:
            return self._aliases[provider_id]
        raise AppBaseError(f"Provider '{provider_id}' is not registered.")

    def get_provider_class(self, provider_id: str) -> Type[BaseComicProvider]:
        """Retrieve a provider class by its ID or alias."""
        primary_id = self.resolve_id(provider_id)
        return self._provider_classes[primary_id]

    def get_all_classes(self) -> Dict[str, Type[BaseComicProvider]]:
        return self._provider_classes.copy()

    def load_all_providers(self):
        """
        Dynamically discover and import all providers in the src.providers package.
        """
        providers_dir = Path(__file__).parent.parent / "providers"
        
        if not providers_dir.exists() or not providers_dir.is_dir():
            return
            
        for provider_path in providers_dir.iterdir():
            if provider_path.is_dir() and not provider_path.name.startswith("_"):
                module_name = f"src.providers.{provider_path.name}.provider"
                try:
                    importlib.import_module(module_name)
                    logger.debug(f"Successfully loaded provider module: {module_name}")
                except Exception as e:
                    logger.error(f"Failed to load provider module {module_name}: {e}")

registry = ProviderRegistry()
