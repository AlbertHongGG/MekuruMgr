import urllib.parse
from typing import List

from src.storage.core.archive_interface import ILibraryStorage, ITaskStorage, IMediaStorage
from src.domain.models import (
    LocalComicItem, 
    LocalComicDetail, 
    LocalChapterItem, 
    LocalChapterImages,
    TaskStatus
)
from src.domain.exceptions import AppBaseError

class LibraryService:
    """
    Read-only service for providing clean, consumable comic data.
    Filters out incomplete chapters and transforms internal paths to CDN URLs.
    """
    def __init__(self, library_storage: ILibraryStorage, task_storage: ITaskStorage, media_storage: IMediaStorage):
        self.library_storage = library_storage
        self.task_storage = task_storage
        self.media_storage = media_storage


    async def _get_completed_chapters_count(self, provider_id: str, comic_id: str) -> int:
        task = await self.task_storage.get_task(f"{provider_id}::{comic_id}")
        if task:
            return task.completed_chapters
        return 0

    async def list_comics(self) -> List[LocalComicItem]:
        """Get a clean list of all locally tracked comics."""
        archived_comics = await self.library_storage.list_comics()
        items = []
        for c in archived_comics:
            completed_count = await self._get_completed_chapters_count(c.provider_id, c.comic_id)
            items.append(LocalComicItem(
                provider_id=c.provider_id,
                comic_id=c.comic_id,
                title=c.title,
                cover_url=c.cover_url,
                completed_chapters_count=completed_count
            ))
        return items

    async def search_comics(self, keyword: str) -> List[LocalComicItem]:
        """Search local library by keyword."""
        if not keyword or not keyword.strip():
            return []
            
        archived_comics = await self.library_storage.search_comics(keyword.strip())
        items = []
        for c in archived_comics:
            completed_count = await self._get_completed_chapters_count(c.provider_id, c.comic_id)
            items.append(LocalComicItem(
                provider_id=c.provider_id,
                comic_id=c.comic_id,
                title=c.title,
                cover_url=c.cover_url,
                completed_chapters_count=completed_count
            ))
        return items

    async def get_comic_detail(self, provider_id: str, comic_id: str) -> LocalComicDetail:
        """Get comic details without chapter array."""
        c = await self.library_storage.get_comic(provider_id, comic_id)
        if not c:
            raise AppBaseError(f"Comic {comic_id} from {provider_id} not found in library.")

        return LocalComicDetail(
            provider_id=c.provider_id,
            comic_id=c.comic_id,
            title=c.title,
            author=c.author,
            tags=c.tags,
            description=c.description,
            cover_url=c.cover_url
        )

    async def get_comic_chapters(self, provider_id: str, comic_id: str) -> List[LocalChapterItem]:
        """Get only the COMPLETED chapters for a comic."""
        c = await self.library_storage.get_comic(provider_id, comic_id)
        if not c:
            raise AppBaseError(f"Comic {comic_id} from {provider_id} not found in library.")

        task = await self.task_storage.get_task(f"{provider_id}::{comic_id}")
        completed_chapters = []
        
        if task:
            for ch in task.chapters.values():
                if ch.status == TaskStatus.COMPLETED:
                    completed_chapters.append(LocalChapterItem(
                        chapter_id=ch.chapter_id,
                        title=ch.title,
                        page_count=ch.total_pages
                    ))
        return completed_chapters

    async def get_chapter_images(self, provider_id: str, comic_id: str, chapter_id: str) -> LocalChapterImages:
        """Get a list of full CDN image URLs for a specific chapter."""
        c = await self.library_storage.get_comic(provider_id, comic_id)
        if not c:
            raise AppBaseError(f"Comic {comic_id} from {provider_id} not found in library.")
            
        task = await self.task_storage.get_task(f"{provider_id}::{comic_id}")
        if not task:
            raise AppBaseError(f"No task found for comic {comic_id}.")
            
        ch = task.chapters.get(chapter_id)
        if not ch or ch.status != TaskStatus.COMPLETED:
            raise AppBaseError(f"Chapter {chapter_id} is not fully downloaded or doesn't exist.")

        # Ask media storage for the relative paths
        relative_paths = await self.media_storage.get_chapter_images(provider_id, comic_id, chapter_id)
        if not relative_paths:
            raise AppBaseError(f"Physical images for chapter {chapter_id} not found.")

        image_urls = [p for p in relative_paths]

        return LocalChapterImages(
            provider_id=provider_id,
            comic_id=comic_id,
            chapter_id=chapter_id,
            title=ch.title,
            images=image_urls
        )
