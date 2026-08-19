import urllib.parse
from typing import List

from src.storage.core.archive_interface import IArchiveStorage
from src.domain.models import (
    LocalComicItem, 
    LocalComicDetail, 
    LocalChapterItem, 
    LocalChapterImages,
    DownloadStatus
)
from src.domain.exceptions import AppBaseError

class LibraryService:
    """
    Read-only service for providing clean, consumable comic data.
    Filters out incomplete chapters and transforms internal paths to CDN URLs.
    """
    def __init__(self, storage: IArchiveStorage, base_media_url: str = "/media/"):
        self.storage = storage
        self.base_media_url = base_media_url.rstrip("/") + "/"

    def _build_url(self, path: str) -> str:
        if not path:
            return ""
        # Ensure proper URL encoding for paths (but keep slashes intact)
        parts = path.split('/')
        encoded_parts = [urllib.parse.quote(p) for p in parts]
        return self.base_media_url + "/".join(encoded_parts)

    def list_comics(self) -> List[LocalComicItem]:
        """Get a clean list of all locally tracked comics."""
        archived_comics = self.storage.list_comics()
        items = []
        for c in archived_comics:
            completed_count = sum(1 for ch in c.chapters.values() if ch.status == DownloadStatus.COMPLETED)
            items.append(LocalComicItem(
                provider_id=c.provider_id,
                comic_id=c.comic_id,
                title=c.title,
                cover_url=self._build_url(c.cover_url),
                completed_chapters_count=completed_count
            ))
        return items

    def search_comics(self, keyword: str) -> List[LocalComicItem]:
        """Search local library by keyword."""
        if not keyword or not keyword.strip():
            return []
            
        archived_comics = self.storage.search_comics(keyword.strip())
        items = []
        for c in archived_comics:
            completed_count = sum(1 for ch in c.chapters.values() if ch.status == DownloadStatus.COMPLETED)
            items.append(LocalComicItem(
                provider_id=c.provider_id,
                comic_id=c.comic_id,
                title=c.title,
                cover_url=self._build_url(c.cover_url),
                completed_chapters_count=completed_count
            ))
        return items

    def get_comic_detail(self, provider_id: str, comic_id: str) -> LocalComicDetail:
        """Get comic details without chapter array."""
        c = self.storage.get_comic(provider_id, comic_id)
        if not c:
            raise AppBaseError(f"Comic {comic_id} from {provider_id} not found in library.")

        return LocalComicDetail(
            provider_id=c.provider_id,
            comic_id=c.comic_id,
            title=c.title,
            author=c.author,
            tags=c.tags,
            description=c.description,
            cover_url=self._build_url(c.cover_url)
        )

    def get_comic_chapters(self, provider_id: str, comic_id: str) -> List[LocalChapterItem]:
        """Get only the COMPLETED chapters for a comic."""
        c = self.storage.get_comic(provider_id, comic_id)
        if not c:
            raise AppBaseError(f"Comic {comic_id} from {provider_id} not found in library.")

        completed_chapters = []
        for ch in c.chapters.values():
            if ch.status == DownloadStatus.COMPLETED:
                completed_chapters.append(LocalChapterItem(
                    chapter_id=ch.chapter_id,
                    title=ch.title,
                    page_count=ch.page_count
                ))
        return completed_chapters

    def get_chapter_images(self, provider_id: str, comic_id: str, chapter_id: str) -> LocalChapterImages:
        """Get a list of full CDN image URLs for a specific chapter."""
        c = self.storage.get_comic(provider_id, comic_id)
        if not c:
            raise AppBaseError(f"Comic {comic_id} from {provider_id} not found in library.")
            
        ch = c.chapters.get(chapter_id)
        if not ch or ch.status != DownloadStatus.COMPLETED:
            raise AppBaseError(f"Chapter {chapter_id} is not fully downloaded or doesn't exist.")

        # Ask media storage for the relative paths
        relative_paths = self.storage.get_chapter_images(provider_id, comic_id, chapter_id)
        if not relative_paths:
            raise AppBaseError(f"Physical images for chapter {chapter_id} not found.")

        image_urls = [self._build_url(p) for p in relative_paths]

        return LocalChapterImages(
            provider_id=provider_id,
            comic_id=comic_id,
            chapter_id=chapter_id,
            title=ch.title,
            images=image_urls
        )
