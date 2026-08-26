import asyncio
import logging
from typing import Dict, Optional, List
from datetime import datetime
import httpx

from src.application.comic_manager import ComicManager
from src.application.interfaces import IProgressObserver
from src.storage.core.archive_interface import ILibraryStorage, ITaskStorage, IMediaStorage
from src.domain.models.archive import DownloadTask, ChapterTask, TaskStatus, LibraryComic
from src.domain.exceptions import AppBaseError

logger = logging.getLogger(__name__)

class DownloadQueueService:
    def __init__(
        self, 
        manager: ComicManager,
        library_storage: ILibraryStorage,
        task_storage: ITaskStorage,
        media_storage: IMediaStorage,
        max_concurrent_tasks: int = 2,
        max_concurrent_pages: int = 5
    ):
        self.manager = manager
        self.library_storage = library_storage
        self.task_storage = task_storage
        self.media_storage = media_storage
        
        self.max_concurrent_tasks = max_concurrent_tasks
        self.max_concurrent_pages = max_concurrent_pages
        
        self._running = False
        self._main_loop_task: Optional[asyncio.Task] = None
        self._active_workers: Dict[str, asyncio.Task] = {}
        self._cancellation_events: Dict[str, asyncio.Event] = {}
        self._page_semaphore = asyncio.Semaphore(self.max_concurrent_pages)

    def start(self):
        if self._running:
            return
        self._running = True
        
        # Recover interrupted tasks
        tasks = self.task_storage.list_tasks()
        for task in tasks:
            if task.status == TaskStatus.DOWNLOADING:
                task.status = TaskStatus.PAUSED
                self.task_storage.save_task(task)
                
        self._main_loop_task = asyncio.create_task(self._queue_loop())
        logger.info("Download Queue Service started.")

    async def stop(self):
        self._running = False
        if self._main_loop_task:
            self._main_loop_task.cancel()
            
        for event in self._cancellation_events.values():
            event.set()
            
        if self._active_workers:
            await asyncio.gather(*self._active_workers.values(), return_exceptions=True)
            
        logger.info("Download Queue Service stopped.")

    async def _queue_loop(self):
        while self._running:
            try:
                if len(self._active_workers) < self.max_concurrent_tasks:
                    tasks = self.task_storage.list_tasks()
                    queued_tasks = [t for t in tasks if t.status == TaskStatus.QUEUED]
                    
                    # Sort by created_at ascending
                    queued_tasks.sort(key=lambda t: t.created_at)
                    
                    for task in queued_tasks:
                        if len(self._active_workers) >= self.max_concurrent_tasks:
                            break
                            
                        if task.task_id not in self._active_workers:
                            self._start_task(task.task_id)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Queue loop error: {e}")
                
            await asyncio.sleep(2.0)

    async def submit_sync(self, provider_id: str, comic_id: str) -> DownloadTask:
        task_id = f"{provider_id}::{comic_id}"
        
        # Ensure library metadata exists
        library_comic = self.library_storage.get_comic(provider_id, comic_id)
        if not library_comic:
            await self.track_comic(provider_id, comic_id)

        task = self.task_storage.get_task(task_id)
        if task:
            if task.status in [TaskStatus.QUEUED, TaskStatus.DOWNLOADING]:
                return task
            task.status = TaskStatus.QUEUED
            task.error_message = None
            task.updated_at = datetime.now()
        else:
            task = DownloadTask(
                task_id=task_id,
                provider_id=provider_id,
                comic_id=comic_id,
                status=TaskStatus.QUEUED
            )
            
        self.task_storage.save_task(task)
        logger.info(f"Task submitted: {task_id}")
        return task

    def pause_task(self, task_id: str) -> bool:
        task = self.task_storage.get_task(task_id)
        if not task:
            return False
            
        if task.status in [TaskStatus.QUEUED, TaskStatus.DOWNLOADING]:
            if task.status == TaskStatus.DOWNLOADING and task_id in self._cancellation_events:
                self._cancellation_events[task_id].set()
            task.status = TaskStatus.PAUSED
            self.task_storage.save_task(task)
            return True
            
        return False

    def resume_task(self, task_id: str) -> bool:
        task = self.task_storage.get_task(task_id)
        if not task or task.status not in [TaskStatus.PAUSED, TaskStatus.FAILED]:
            return False
            
        task.status = TaskStatus.QUEUED
        task.error_message = None
        task.updated_at = datetime.now()
        self.task_storage.save_task(task)
        return True

    def cancel_task(self, task_id: str) -> bool:
        task = self.task_storage.get_task(task_id)
        if not task:
            return False
            
        if task.status == TaskStatus.DOWNLOADING:
            if task_id in self._cancellation_events:
                self._cancellation_events[task_id].set()
            
        task.status = TaskStatus.CANCELLED
        self.task_storage.save_task(task)
        return True

    def get_progress(self, provider_id: str, comic_id: str) -> Optional[DownloadTask]:
        task_id = f"{provider_id}::{comic_id}"
        return self.task_storage.get_task(task_id)

    def _start_task(self, task_id: str):
        task = self.task_storage.get_task(task_id)
        if not task:
            return
            
        task.status = TaskStatus.DOWNLOADING
        task.updated_at = datetime.now()
        self.task_storage.save_task(task)
        
        cancel_event = asyncio.Event()
        self._cancellation_events[task_id] = cancel_event
        
        worker = asyncio.create_task(self._task_worker(task_id, cancel_event))
        self._active_workers[task_id] = worker
        
        worker.add_done_callback(lambda t: self._cleanup_worker(task_id))

    def _cleanup_worker(self, task_id: str):
        self._active_workers.pop(task_id, None)
        self._cancellation_events.pop(task_id, None)

    async def _task_worker(self, task_id: str, cancel_event: asyncio.Event):
        task = self.task_storage.get_task(task_id)
        if not task:
            return
            
        self.manager.use(task.provider_id)
        
        try:
            # 1. Fetch remote chapters
            remote_chapters = await asyncio.to_thread(self.manager.fetch_all_chapters, task.comic_id)
            
            # 2. Update task chapters state
            t_update = self.task_storage.get_task(task_id)
            if not t_update:
                return
                
            new_chapters_added = False
            for r_ch in remote_chapters:
                if r_ch.id not in t_update.chapters:
                    t_update.chapters[r_ch.id] = ChapterTask(
                        chapter_id=r_ch.id,
                        title=r_ch.title
                    )
                    new_chapters_added = True
                    
            if new_chapters_added:
                self.task_storage.save_task(t_update)
            
            # 3. Process chapters
            async with httpx.AsyncClient() as client:
                for ch_id in list(t_update.chapters.keys()):
                    if cancel_event.is_set():
                        break
                        
                    t_update = self.task_storage.get_task(task_id)
                    if not t_update or ch_id not in t_update.chapters:
                        continue
                    
                    chapter_task = t_update.chapters[ch_id]
                        
                    if chapter_task.status == TaskStatus.COMPLETED:
                        # Verify files
                        actual_files = self.media_storage.count_downloaded_images(task.provider_id, task.comic_id, ch_id)
                        if actual_files >= chapter_task.total_pages and chapter_task.total_pages > 0:
                            continue
                        else:
                            chapter_task.status = TaskStatus.QUEUED
                            
                    chapter_task.status = TaskStatus.DOWNLOADING
                    self.task_storage.save_task(t_update)
                    
                    try:
                        images = await asyncio.to_thread(self.manager.fetch_chapter_images, task.comic_id, ch_id)
                        
                        t_update = self.task_storage.get_task(task_id)
                        if not t_update or ch_id not in t_update.chapters:
                            continue
                            
                        t_update.chapters[ch_id].total_pages = len(images)
                        
                        # Recount downloaded
                        downloaded = self.media_storage.count_downloaded_images(task.provider_id, task.comic_id, ch_id)
                        t_update.chapters[ch_id].downloaded_pages = downloaded
                        self.task_storage.save_task(t_update)
                        
                        for index, image in enumerate(images):
                            if cancel_event.is_set():
                                break
                                
                            if self.media_storage.check_image_exists(task.provider_id, task.comic_id, ch_id, index):
                                continue
                                
                            await self._download_page(client, task.provider_id, task.comic_id, ch_id, index, image.url)
                            
                            # Update progress in DB safely
                            t_update = self.task_storage.get_task(task_id)
                            if t_update and ch_id in t_update.chapters:
                                t_update.chapters[ch_id].downloaded_pages += 1
                                self.task_storage.save_task(t_update)
                                
                        if not cancel_event.is_set():
                            t_update = self.task_storage.get_task(task_id)
                            if t_update and ch_id in t_update.chapters:
                                t_update.chapters[ch_id].status = TaskStatus.COMPLETED
                                self.task_storage.save_task(t_update)
                                
                    except Exception as e:
                        logger.error(f"Error downloading chapter {ch_id}: {e}")
                        t_update = self.task_storage.get_task(task_id)
                        if t_update and ch_id in t_update.chapters:
                            t_update.chapters[ch_id].status = TaskStatus.FAILED
                            t_update.chapters[ch_id].error_message = str(e)
                            self.task_storage.save_task(t_update)
                            
            # Final task status update
            t_final = self.task_storage.get_task(task_id)
            if t_final:
                if cancel_event.is_set():
                    if t_final.status == TaskStatus.DOWNLOADING:
                        t_final.status = TaskStatus.PAUSED
                else:
                    all_completed = all(c.status == TaskStatus.COMPLETED for c in t_final.chapters.values())
                    any_failed = any(c.status == TaskStatus.FAILED for c in t_final.chapters.values())
                    
                    if all_completed and len(t_final.chapters) > 0:
                        t_final.status = TaskStatus.COMPLETED
                    elif any_failed:
                        t_final.status = TaskStatus.FAILED
                    else:
                        t_final.status = TaskStatus.COMPLETED # Fallback
                        
                t_final.updated_at = datetime.now()
                self.task_storage.save_task(t_final)
                
        except Exception as e:
            logger.error(f"Task worker error {task_id}: {e}")
            t_fail = self.task_storage.get_task(task_id)
            if t_fail:
                t_fail.status = TaskStatus.FAILED
                t_fail.error_message = str(e)
                self.task_storage.save_task(t_fail)

    async def _download_page(self, client: httpx.AsyncClient, provider_id: str, comic_id: str, chapter_id: str, index: int, url: str):
        async with self._page_semaphore:
            content, content_type = await self.manager.provider.download_image(client, url)
            await self.media_storage.save_image(provider_id, comic_id, chapter_id, index, content, content_type)

    async def track_comic(self, provider_id: str, comic_id: str) -> LibraryComic:
        self.manager.use(provider_id)
        comic_detail = await asyncio.to_thread(self.manager.fetch_comic_detail, comic_id)
        
        # Cover download is synchronous here for simplicity in this method, 
        # or we could make it async. Since this is called from submit_sync (sync), 
        # let's run it in a new event loop or using existing asyncio loop if running.
        
        # Simplified: we just save the comic detail and leave cover downloading for a background task if needed,
        # but to keep it simple, we do it inline if possible, or just skip cover for now and save metadata.
        library_comic = LibraryComic(
            provider_id=provider_id,
            comic_id=comic_id,
            title=comic_detail.title,
            author=comic_detail.author,
            tags=comic_detail.tags,
            description=comic_detail.description,
            cover_url=comic_detail.cover_url,
            local_path=f"{provider_id}/{comic_id}"
        )
        self.library_storage.save_comic(library_comic)
        
        # We can spawn a separate task for cover to avoid blocking
        asyncio.create_task(self._download_cover(provider_id, comic_id, comic_detail.cover_url))
        
        return library_comic

    async def _download_cover(self, provider_id: str, comic_id: str, url: str):
        try:
            async with httpx.AsyncClient() as client:
                self.manager.use(provider_id)
                content, content_type = await self.manager.provider.download_image(client, url)
                filename = await self.media_storage.save_image(provider_id, comic_id, 'cover', 0, content, content_type)
                
                # Update library cover URL to local
                library_comic = self.library_storage.get_comic(provider_id, comic_id)
                if library_comic:
                    library_comic.cover_url = f"{provider_id}/{comic_id}/{filename}"
                    self.library_storage.save_comic(library_comic)
        except Exception as e:
            logger.error(f"Failed to download cover for {comic_id}: {e}")
