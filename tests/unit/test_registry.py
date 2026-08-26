import pytest
from src.core.registry import ProviderRegistry
from src.core.provider import BaseComicProvider
from src.domain.exceptions import AppBaseError

class DummyProvider1(BaseComicProvider):
    @property
    def provider_id(self) -> str:
        return "dummy1"

    @property
    def aliases(self) -> list[str]:
        return ["d1", "dummy_one"]

    @property
    def provider_name(self) -> str:
        return "Dummy 1"

    def get_comic_detail(self, comic_id: str): pass
    def get_chapter_list(self, comic_id: str): pass
    def get_chapter_images(self, comic_id: str, chapter_id: str): pass
    def search_comics(self, keyword: str, page: int = 1, page_size: int = 30): pass
    def explore_comics(self, page: int = 1, page_size: int = 30): pass

class DummyProvider2(BaseComicProvider):
    @property
    def provider_id(self) -> str:
        return "dummy2"

    @property
    def aliases(self) -> list[str]:
        return ["d2", "dummy_two"]

    @property
    def provider_name(self) -> str:
        return "Dummy 2"

    def get_comic_detail(self, comic_id: str): pass
    def get_chapter_list(self, comic_id: str): pass
    def get_chapter_images(self, comic_id: str, chapter_id: str): pass
    def search_comics(self, keyword: str, page: int = 1, page_size: int = 30): pass
    def explore_comics(self, page: int = 1, page_size: int = 30): pass

class ConflictProvider(BaseComicProvider):
    @property
    def provider_id(self) -> str:
        return "dummy3"

    @property
    def aliases(self) -> list[str]:
        return ["d1"] # Conflicts with dummy1

    @property
    def provider_name(self) -> str:
        return "Conflict Provider"

    def get_comic_detail(self, comic_id: str): pass
    def get_chapter_list(self, comic_id: str): pass
    def get_chapter_images(self, comic_id: str, chapter_id: str): pass
    def search_comics(self, keyword: str, page: int = 1, page_size: int = 30): pass
    def explore_comics(self, page: int = 1, page_size: int = 30): pass

def test_registry_register_and_get():
    registry = ProviderRegistry()
    registry.register(DummyProvider1)
    
    # Check primary ID
    p1 = registry.get_provider("dummy1")
    assert p1.provider_id == "dummy1"
    
    # Check aliases
    p1_alias1 = registry.get_provider("d1")
    assert p1_alias1 is p1
    
    p1_alias2 = registry.get_provider("dummy_one")
    assert p1_alias2 is p1

def test_registry_not_found():
    registry = ProviderRegistry()
    with pytest.raises(AppBaseError):
        registry.get_provider("unknown")

def test_registry_conflict():
    registry = ProviderRegistry()
    registry.register(DummyProvider1)
    
    with pytest.raises(AppBaseError) as exc_info:
        registry.register(ConflictProvider)
        
    assert "Provider alias collision" in str(exc_info.value)
