import asyncio
import httpx
import shutil
import mimetypes
from pathlib import Path
import structlog
import aiofiles
from datetime import datetime

from src.application.comic_manager import ComicManager
from src.storage.factory import StorageFactory, StorageEngine
from src.domain.models import ArchivedComic, ArchivedChapter, DownloadStatus
from src.domain.exceptions import AppBaseError

logger = structlog.get_logger(__name__)

class ArchiverEngine:
    """
    Orchestrates the tracking and syncing of comics to local storage.
    Uses an Incremental Sync architecture to avoid re-downloading existing chapters.
    """
    def __init__(self, manager: ComicManager, max_concurrent_downloads: int = 5):
        self.manager = manager
        self.storage = StorageFactory.get_storage(StorageEngine.JSON)
        self.semaphore = asyncio.Semaphore(max_concurrent_downloads)

    async def _download_image(self, client: httpx.AsyncClient, url: str, dest_path: Path):
        async with self.semaphore:
            try:
                response = await client.get(url, timeout=30.0)
                response.raise_for_status()
                
                content_type = response.headers.get('content-type', '')
                ext = mimetypes.guess_extension(content_type) or '.jpg'
                
                if not dest_path.suffix:
                    dest_path = dest_path.with_suffix(ext)
                    
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                async with aiofiles.open(dest_path, 'wb') as f:
                    await f.write(response.content)
                return dest_path.name
            except Exception as e:
                logger.error("image_download_failed", url=url, error=str(e))
                raise

    async def track_comic(self, provider_id: str, comic_id: str) -> ArchivedComic:
        """
        Add a comic to the local tracking library. 
        Only fetches metadata and cover. Does NOT download chapters.
        """
        self.manager.use(provider_id)
        
        # Check if already tracked
        existing = self.storage.get_comic(provider_id, comic_id)
        if existing:
            return existing
            
        logger.info("archiver_tracking_comic", comic_id=comic_id)
        comic_detail = self.manager.fetch_comic_detail(comic_id)
        
        comic_dir = self.storage.data_dir / provider_id / comic_id
        comic_dir.mkdir(parents=True, exist_ok=True)
        
        cover_path = comic_dir / "cover"
        async with httpx.AsyncClient() as client:
            filename = await self._download_image(client, comic_detail.cover_url, cover_path)
            
        archived_comic = ArchivedComic(
            provider_id=provider_id,
            comic_id=comic_id,
            title=comic_detail.title,
            tags=comic_detail.tags,
            description=comic_detail.description,
            cover_url=f"{provider_id}/{comic_id}/{filename}",
            local_path=f"{provider_id}/{comic_id}",
        )
        
        self.storage.save_comic(archived_comic)
        logger.info("archiver_comic_tracked", comic_id=comic_id, title=comic_detail.title)
        return archived_comic

    async def sync_comic(self, provider_id: str, comic_id: str):
        """
        Perform an incremental sync. 
        Downloads only the chapters that are missing or FAILED.
        """
        self.manager.use(provider_id)
        
        archived_comic = self.storage.get_comic(provider_id, comic_id)
        if not archived_comic:
            # Auto-track if not exist
            archived_comic = await self.track_comic(provider_id, comic_id)
            
        logger.info("archiver_syncing_comic", comic_id=comic_id)
        remote_chapters = self.manager.fetch_all_chapters(comic_id)
        comic_dir = self.storage.data_dir / provider_id / comic_id
        
        # Determine Delta (Incremental Sync logic)
        delta_chapters = []
        for remote_ch in remote_chapters:
            local_ch = archived_comic.chapters.get(remote_ch.id)
            if not local_ch or local_ch.status != DownloadStatus.COMPLETED:
                delta_chapters.append(remote_ch)
                
        if not delta_chapters:
            logger.info("archiver_sync_up_to_date", comic_id=comic_id)
            return archived_comic
            
        logger.info("archiver_delta_found", comic_id=comic_id, delta_count=len(delta_chapters))
        
        async with httpx.AsyncClient() as client:
            for chapter in delta_chapters:
                logger.info("archiver_downloading_chapter", chapter_id=chapter.id, title=chapter.title)
                
                # Mark as downloading
                archived_comic.chapters[chapter.id] = ArchivedChapter(
                    chapter_id=chapter.id,
                    title=chapter.title,
                    status=DownloadStatus.DOWNLOADING
                )
                self.storage.save_comic(archived_comic)
                
                try:
                    images = self.manager.fetch_chapter_images(comic_id, chapter.id)
                    chapter_dir = comic_dir / chapter.id
                    chapter_dir.mkdir(parents=True, exist_ok=True)
                    
                    tasks = []
                    for index, image in enumerate(images):
                        dest_path = chapter_dir / f"{index:03d}" 
                        tasks.append(self._download_image(client, image.url, dest_path))
                    
                    await asyncio.gather(*tasks)
                    
                    # Mark as completed
                    archived_comic.chapters[chapter.id].status = DownloadStatus.COMPLETED
                    archived_comic.chapters[chapter.id].page_count = len(images)
                    archived_comic.chapters[chapter.id].local_path = f"{provider_id}/{comic_id}/{chapter.id}"
                    
                except Exception as e:
                    logger.error("archiver_chapter_failed", chapter_id=chapter.id, error=str(e))
                    archived_comic.chapters[chapter.id].status = DownloadStatus.FAILED
                
                archived_comic.updated_at = datetime.now()
                self.storage.save_comic(archived_comic)
                
        logger.info("archiver_sync_completed", comic_id=comic_id)
        return archived_comic

    def delete_archived_comic(self, provider_id: str, comic_id: str):
        archived = self.storage.get_comic(provider_id, comic_id)
        if not archived:
            raise AppBaseError(f"Comic {comic_id} from {provider_id} is not found in local library.")
            
        # 1. Remove from JSON
        self.storage.delete_comic(provider_id, comic_id)
        
        # 2. Delete physical files
        target_dir = self.storage.data_dir / provider_id / comic_id
        if target_dir.exists():
            shutil.rmtree(target_dir)
            logger.info("archiver_deleted_files", path=str(target_dir))
