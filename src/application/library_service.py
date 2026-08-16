import urllib.parse
from typing import List, Optional

from src.storage.factory import StorageFactory, StorageEngine
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
    def __init__(self, base_media_url: str = "/media/"):
        self.storage = StorageFactory.get_storage(StorageEngine.JSON)
        # base_media_url could be a full URL "http://127.0.0.1:8000/media/" 
        # or relative "/media/". We default to relative for flexibility.
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

    def get_comic_detail(self, provider_id: str, comic_id: str) -> LocalComicDetail:
        """Get comic details including only COMPLETED chapters."""
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

        return LocalComicDetail(
            provider_id=c.provider_id,
            comic_id=c.comic_id,
            title=c.title,
            tags=c.tags,
            description=c.description,
            cover_url=self._build_url(c.cover_url),
            chapters=completed_chapters
        )

    def get_chapter_images(self, provider_id: str, comic_id: str, chapter_id: str) -> LocalChapterImages:
        """Get a list of full CDN image URLs for a specific chapter."""
        c = self.storage.get_comic(provider_id, comic_id)
        if not c:
            raise AppBaseError(f"Comic {comic_id} from {provider_id} not found in library.")
            
        ch = c.chapters.get(chapter_id)
        if not ch or ch.status != DownloadStatus.COMPLETED:
            raise AppBaseError(f"Chapter {chapter_id} is not fully downloaded or doesn't exist.")

        # Reconstruct the image paths based on storage format: provider/comic/chapter/000.ext
        # To get the exact filenames, we look at the actual directory.
        target_dir = self.storage.data_dir / provider_id / comic_id / chapter_id
        if not target_dir.exists():
            raise AppBaseError(f"Physical directory for chapter {chapter_id} not found.")

        # Get all image files sorted alphabetically (e.g. 000.jpg, 001.jpg)
        image_files = sorted([f.name for f in target_dir.iterdir() if f.is_file()])
        
        image_urls = []
        for img in image_files:
            relative_path = f"{provider_id}/{comic_id}/{chapter_id}/{img}"
            image_urls.append(self._build_url(relative_path))

        return LocalChapterImages(
            provider_id=provider_id,
            comic_id=comic_id,
            chapter_id=chapter_id,
            title=ch.title,
            images=image_urls
        )
