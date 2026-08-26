from abc import ABC, abstractmethod
from typing import List, Optional, Any

from src.domain.models.archive import LibraryComic, DownloadTask

class ILibraryStorage(ABC):
    @abstractmethod
    def get_comic(self, provider_id: str, comic_id: str) -> Optional[LibraryComic]:
        pass

    @abstractmethod
    def save_comic(self, comic: LibraryComic) -> None:
        pass

    @abstractmethod
    def delete_comic(self, provider_id: str, comic_id: str) -> None:
        pass
        
    @abstractmethod
    def list_comics(self) -> List[LibraryComic]:
        pass

    @abstractmethod
    def search_comics(self, keyword: str) -> List[LibraryComic]:
        pass


class ITaskStorage(ABC):
    @abstractmethod
    def get_task(self, task_id: str) -> Optional[DownloadTask]:
        pass

    @abstractmethod
    def save_task(self, task: DownloadTask) -> None:
        pass
        
    @abstractmethod
    def delete_task(self, task_id: str) -> None:
        pass
        
    @abstractmethod
    def list_tasks(self) -> List[DownloadTask]:
        pass


class IMediaStorage(ABC):
    @abstractmethod
    async def save_image(self, provider_id: str, comic_id: str, chapter_id: str, index: int, content: bytes, content_type: str) -> str:
        pass

    @abstractmethod
    def get_chapter_images(self, provider_id: str, comic_id: str, chapter_id: str) -> List[str]:
        pass

    @abstractmethod
    def count_downloaded_images(self, provider_id: str, comic_id: str, chapter_id: str) -> int:
        pass

    @abstractmethod
    def get_image_stream(self, relative_path: str) -> tuple[Any, str]:
        pass
        
    @abstractmethod
    def check_image_exists(self, provider_id: str, comic_id: str, chapter_id: str, index: int) -> bool:
        pass

    @abstractmethod
    def is_chapter_missing(self, provider_id: str, comic_id: str, chapter_id: str) -> bool:
        pass
        
    @abstractmethod
    def delete_media(self, provider_id: str, comic_id: str) -> None:
        pass
