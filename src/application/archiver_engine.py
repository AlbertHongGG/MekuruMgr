import asyncio
import httpx
import logging
from datetime import datetime
from rich.progress import Progress, TaskID, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn

from src.application.comic_manager import ComicManager
from src.storage.interface import IArchiveStorage
from src.domain.models import ArchivedComic, ArchivedChapter, DownloadStatus
from src.domain.exceptions import AppBaseError

logger = logging.getLogger(__name__)

class ArchiverEngine:
    """
    Orchestrates the tracking and syncing of comics to storage.
    Pure business logic. No pathlib, no glob, no hardcoded storage engines.
    """
    def __init__(self, manager: ComicManager, storage: IArchiveStorage, max_concurrent_downloads: int = 5):
        self.manager = manager
        self.storage = storage
        self.semaphore = asyncio.Semaphore(max_concurrent_downloads)

    async def _download_image(self, client: httpx.AsyncClient, provider_id: str, comic_id: str, chapter_id: str, index: int, url: str, progress: Progress = None, task_id: TaskID = None):
        async with self.semaphore:
            try:
                response = await client.get(url, timeout=30.0)
                response.raise_for_status()
                content_type = response.headers.get('content-type', '')
                
                await self.storage.save_image(provider_id, comic_id, chapter_id, index, response.content, content_type)
                    
                if progress and task_id is not None:
                    progress.advance(task_id)
            except Exception as e:
                logger.error(f"Failed to download image [red]{url}[/]: {e}")
                raise

    async def track_comic(self, provider_id: str, comic_id: str) -> ArchivedComic:
        self.manager.use(provider_id)
        
        existing = self.storage.get_comic(provider_id, comic_id)
        if existing:
            return existing
            
        logger.info(f"Tracking new comic: [green]{comic_id}[/]")
        comic_detail = self.manager.fetch_comic_detail(comic_id)
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(comic_detail.cover_url, timeout=30.0)
                response.raise_for_status()
                content_type = response.headers.get('content-type', '')
                filename = await self.storage.save_image(provider_id, comic_id, 'cover', 0, response.content, content_type)
            except Exception as e:
                logger.error(f"Failed to download cover image: {e}")
                filename = "cover.jpg"
            
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
        self.manager.use(provider_id)
        
        archived_comic = self.storage.get_comic(provider_id, comic_id)
        if not archived_comic:
            archived_comic = await self.track_comic(provider_id, comic_id)
            
        logger.info(f"Syncing comic: [cyan]{archived_comic.title}[/]")
        remote_chapters = self.manager.fetch_all_chapters(comic_id)
        
        # Determine Delta
        delta_chapters = []
        for remote_ch in remote_chapters:
            local_ch = archived_comic.chapters.get(remote_ch.id)
            
            if not local_ch or local_ch.status != DownloadStatus.COMPLETED:
                delta_chapters.append(remote_ch)
            else:
                if self.storage.is_chapter_missing(provider_id, comic_id, remote_ch.id):
                    logger.warning(f"Chapter [yellow]{remote_ch.title}[/] folder is missing. Re-queuing.")
                    delta_chapters.append(remote_ch)
                elif local_ch.page_count is not None:
                    actual_files = self.storage.count_downloaded_images(provider_id, comic_id, remote_ch.id)
                    if actual_files < local_ch.page_count:
                        logger.warning(f"Chapter [yellow]{remote_ch.title}[/] is missing files ({actual_files}/{local_ch.page_count}). Re-queuing.")
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
                    chapter_task = progress.add_task(f"[cyan]Downloading {chapter.title}", total=1)
                    
                    archived_comic.chapters[chapter.id] = ArchivedChapter(
                        chapter_id=chapter.id,
                        title=chapter.title,
                        status=DownloadStatus.DOWNLOADING
                    )
                    self.storage.save_comic(archived_comic)
                    
                    try:
                        images = self.manager.fetch_chapter_images(comic_id, chapter.id)
                        progress.update(chapter_task, total=len(images))
                        
                        tasks = []
                        for index, image in enumerate(images):
                            if self.storage.check_image_exists(provider_id, comic_id, chapter.id, index):
                                if progress and chapter_task is not None:
                                    progress.advance(chapter_task)
                                continue
                            
                            tasks.append(self._download_image(client, provider_id, comic_id, chapter.id, index, image.url, progress, chapter_task))
                        
                        if tasks:
                            await asyncio.gather(*tasks)
                        
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
            
        self.storage.delete_comic(provider_id, comic_id)
