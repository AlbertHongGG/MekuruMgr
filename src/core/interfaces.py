from abc import ABC, abstractmethod
from typing import List, Optional, Any

from src.domain.models import ComicDetail, Chapter, PageImage, ComicSearchResult, ComicExploreResult
from src.domain.models import LocalComicItem, LocalComicDetail, LocalChapterItem, LocalChapterImages
from src.domain.models.archive import DownloadTask

class IComicManager(ABC):
    @property
    @abstractmethod
    def active_provider(self) -> Any:
        pass
        
    @abstractmethod
    def use(self, provider_id: str) -> None:
        pass

    @abstractmethod
    def resolve_id(self, provider_id: str) -> str:
        pass
        
    @abstractmethod
    def get_available_providers(self) -> List[dict]:
        pass
        
    @abstractmethod
    async def fetch_comic_detail(self, provider_id: str, comic_id: str) -> ComicDetail:
        pass

    @abstractmethod
    async def fetch_all_chapters(self, provider_id: str, comic_id: str) -> List[Chapter]:
        pass

    @abstractmethod
    async def fetch_chapter_images(self, provider_id: str, comic_id: str, chapter_id: str) -> List[PageImage]:
        pass

    @abstractmethod
    async def search_comics(self, provider_id: str, keyword: str, page: int = 1) -> List[ComicSearchResult]:
        pass

    @abstractmethod
    async def explore_comics(self, provider_id: str, page: int = 1) -> List[ComicExploreResult]:
        pass

class ILibraryService(ABC):
    @abstractmethod
    async def list_comics(self) -> List[LocalComicItem]:
        pass

    @abstractmethod
    async def search_comics(self, keyword: str) -> List[LocalComicItem]:
        pass

    @abstractmethod
    async def get_comic_detail(self, provider_id: str, comic_id: str) -> LocalComicDetail:
        pass

    @abstractmethod
    async def get_comic_chapters(self, provider_id: str, comic_id: str) -> List[LocalChapterItem]:
        pass

    @abstractmethod
    async def get_chapter_images(self, provider_id: str, comic_id: str, chapter_id: str) -> LocalChapterImages:
        pass

class IArchiveEngine(ABC):
    @abstractmethod
    async def start(self) -> None:
        pass
        
    @abstractmethod
    async def stop(self) -> None:
        pass

    @abstractmethod
    async def track_comic(self, provider_id: str, comic_id: str) -> None:
        pass

    @abstractmethod
    async def submit_sync(self, provider_id: str, comic_id: str) -> None:
        pass

    @abstractmethod
    async def pause_task_async(self, provider_id: str, comic_id: str) -> None:
        pass

    @abstractmethod
    async def resume_task_async(self, provider_id: str, comic_id: str) -> None:
        pass

    @abstractmethod
    async def cancel_task_async(self, provider_id: str, comic_id: str) -> None:
        pass

    @abstractmethod
    def get_progress(self, provider_id: str, comic_id: str) -> Optional[DownloadTask]:
        pass
