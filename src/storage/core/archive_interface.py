from abc import ABC, abstractmethod
from typing import List, Optional, Any, Tuple

from src.domain.models import LocalComic, DownloadTask

class ILibraryStorage(ABC):
    @abstractmethod
    async def get_comic(self, provider_id: str, comic_id: str) -> Optional[LocalComic]:
        pass

    @abstractmethod
    async def save_comic(self, comic: LocalComic) -> None:
        pass

    @abstractmethod
    async def delete_comic(self, provider_id: str, comic_id: str) -> None:
        pass
        
    @abstractmethod
    async def list_comics(self) -> List[LocalComic]:
        pass

    @abstractmethod
    async def search_comics(self, keyword: str) -> List[LocalComic]:
        pass


class ITaskStorage(ABC):
    @abstractmethod
    async def get_task(self, task_id: str) -> Optional[DownloadTask]:
        pass

    @abstractmethod
    async def save_task(self, task: DownloadTask) -> None:
        pass
        
    @abstractmethod
    async def delete_task(self, task_id: str) -> None:
        pass
        
    @abstractmethod
    async def list_tasks(self) -> List[DownloadTask]:
        pass


class IMediaStorage(ABC):
    @abstractmethod
    async def save_image(self, provider_id: str, comic_id: str, chapter_id: str, index: int, content: bytes, content_type: str) -> str:
        pass

    @abstractmethod
    async def get_chapter_images(self, provider_id: str, comic_id: str, chapter_id: str) -> List[str]:
        pass

    @abstractmethod
    async def count_downloaded_images(self, provider_id: str, comic_id: str, chapter_id: str) -> int:
        pass

    @abstractmethod
    async def get_image_stream(self, relative_path: str) -> Tuple[Any, str]:
        pass
        
    @abstractmethod
    async def check_image_exists(self, provider_id: str, comic_id: str, chapter_id: str, index: int) -> bool:
        pass

    @abstractmethod
    async def is_chapter_missing(self, provider_id: str, comic_id: str, chapter_id: str) -> bool:
        pass
        
    @abstractmethod
    async def delete_media(self, provider_id: str, comic_id: str) -> None:
        pass
