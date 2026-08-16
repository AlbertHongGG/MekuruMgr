import asyncio
import httpx
import shutil
import mimetypes
from pathlib import Path
import logging
import aiofiles
from datetime import datetime
from rich.progress import Progress, TaskID, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn

from src.application.comic_manager import ComicManager
from src.storage.factory import StorageFactory, StorageEngine
from src.domain.models import ArchivedComic, ArchivedChapter, DownloadStatus
from src.domain.exceptions import AppBaseError

logger = logging.getLogger(__name__)

class ArchiverEngine:
    """
    Orchestrates the tracking and syncing of comics to local storage.
    Uses an Incremental Sync architecture to avoid re-downloading existing chapters.
    """
    def __init__(self, manager: ComicManager, max_concurrent_downloads: int = 5):
        self.manager = manager
        self.storage = StorageFactory.get_storage(StorageEngine.JSON)
        self.semaphore = asyncio.Semaphore(max_concurrent_downloads)

    async def _download_image(self, client: httpx.AsyncClient, url: str, dest_path: Path, progress: Progress = None, task_id: TaskID = None):
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
                    
                if progress and task_id is not None:
                    progress.advance(task_id)
                    
                return dest_path.name
            except Exception as e:
                logger.error(f"Failed to download image [red]{url}[/]: {e}")
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
            
        logger.info(f"Tracking new comic: [green]{comic_id}[/]")
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
        logger.info(f"Successfully tracked: [cyan]{comic_detail.title}[/]")
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
            
        logger.info(f"Syncing comic: [cyan]{archived_comic.title}[/]")
        remote_chapters = self.manager.fetch_all_chapters(comic_id)
        comic_dir = self.storage.data_dir / provider_id / comic_id
        
        # Determine Delta (Incremental Sync logic)
        delta_chapters = []
        for remote_ch in remote_chapters:
            local_ch = archived_comic.chapters.get(remote_ch.id)
            if not local_ch or local_ch.status != DownloadStatus.COMPLETED:
                delta_chapters.append(remote_ch)
                
        if not delta_chapters:
            logger.info(f"Sync up-to-date. No new chapters for [cyan]{archived_comic.title}[/].")
            return archived_comic
            
        logger.info(f"Found [yellow]{len(delta_chapters)}[/] missing/failed chapters to download.")
        
        async with httpx.AsyncClient() as client:
            with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeRemainingColumn(),
            ) as progress:
                sync_task = progress.add_task(f"[bold green]Total Sync Progress", total=len(delta_chapters))
                
                for chapter in delta_chapters:
                    chapter_task = progress.add_task(f"[cyan]Downloading {chapter.title}", total=1) # Will be updated when images are fetched
                    
                    # Mark as downloading
                    archived_comic.chapters[chapter.id] = ArchivedChapter(
                        chapter_id=chapter.id,
                        title=chapter.title,
                        status=DownloadStatus.DOWNLOADING
                    )
                    self.storage.save_comic(archived_comic)
                    
                    try:
                        images = self.manager.fetch_chapter_images(comic_id, chapter.id)
                        progress.update(chapter_task, total=len(images))
                        
                        chapter_dir = comic_dir / chapter.id
                        chapter_dir.mkdir(parents=True, exist_ok=True)
                        
                        tasks = []
                        for index, image in enumerate(images):
                            dest_path = chapter_dir / f"{index:03d}" 
                            tasks.append(self._download_image(client, image.url, dest_path, progress, chapter_task))
                        
                        await asyncio.gather(*tasks)
                        
                        # Mark as completed
                        archived_comic.chapters[chapter.id].status = DownloadStatus.COMPLETED
                        archived_comic.chapters[chapter.id].page_count = len(images)
                        archived_comic.chapters[chapter.id].local_path = f"{provider_id}/{comic_id}/{chapter.id}"
                        
                    except Exception as e:
                        logger.error(f"Failed to download chapter [red]{chapter.title}[/]: {e}")
                        archived_comic.chapters[chapter.id].status = DownloadStatus.FAILED
                    
                    archived_comic.updated_at = datetime.now()
                    self.storage.save_comic(archived_comic)
                    
                    progress.advance(sync_task)
                    progress.remove_task(chapter_task)
                
        logger.info(f"Sync complete for [cyan]{archived_comic.title}[/]")
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
            logger.info(f"Deleted physical files at [yellow]{target_dir}[/]")
