from typing import Dict, Type
import structlog
from src.core.provider import BaseComicProvider

logger = structlog.get_logger(__name__)

class ProviderRegistry:
    """
    A central registry to manage and instantiate different comic providers.
    Follows the Factory pattern.
    """
    def __init__(self):
        self._providers: Dict[str, Type[BaseComicProvider]] = {}
        self._instances: Dict[str, BaseComicProvider] = {}

    def register(self, provider_class: Type[BaseComicProvider]) -> None:
        """Register a new provider class."""
        # Instantiate temporarily to get the ID, or require an ID attribute on the class.
        # We can just instantiate it lazily or aggressively.
        # For simplicity, we assume the class can be instantiated without args.
        try:
            temp_instance = provider_class()
            pid = temp_instance.provider_id
            self._providers[pid] = provider_class
            logger.info("provider_registered", provider_id=pid, name=temp_instance.provider_name)
        except Exception as e:
            logger.error("provider_registration_failed", error=str(e), cls=provider_class.__name__)

    def get_provider(self, provider_id: str) -> BaseComicProvider:
        """Get or create an instance of a provider."""
        if provider_id not in self._providers:
            raise ValueError(f"Provider '{provider_id}' is not registered.")
        
        if provider_id not in self._instances:
            provider_class = self._providers[provider_id]
            self._instances[provider_id] = provider_class()
            
        return self._instances[provider_id]

    def list_providers(self) -> list[str]:
        """List all registered provider IDs."""
        return list(self._providers.keys())

# Global registry instance
registry = ProviderRegistry()
