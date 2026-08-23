from src.core.registry import registry
from .provider import CopymangaProvider

# Register the provider
registry.register(CopymangaProvider)

__all__ = ["CopymangaProvider"]
