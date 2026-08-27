import asyncio
import logging
from typing import Dict, Optional
from datetime import datetime
import httpx

from src.application.comic_manager import ComicManager
from src.storage.core.archive_interface import ILibraryStorage, ITaskStorage, IMediaStorage
from src.domain.models.archive import DownloadTask, ChapterTask, TaskStatus, LocalComic

logger = logging.getLogger(__name__)

class PageDownloadJob:
    def __init__(self, task_id: str, provider_id: str, comic_id: str, chapter_id: str, page_index: int, url: str):
        self.task_id = task_id
        self.provider_id = provider_id
        self.comic_id = comic_id
        self.chapter_id = chapter_id
        self.page_index = page_index
        self.url = url

class ProgressTracker:
    def __init__(self, task_storage: ITaskStorage):
        self.task_storage = task_storage
        self.tasks: Dict[str, DownloadTask] = {}
        self.dirty_tasks: set = set()
        self._lock = asyncio.Lock()

    async def load_task(self, task_id: str) -> Optional[DownloadTask]:
        async with self._lock:
            if task_id not in self.tasks:
                task = await self.task_storage.get_task(task_id)
                if task:
                    self.tasks[task_id] = task
            return self.tasks.get(task_id)

    async def update_page_progress(self, task_id: str, chapter_id: str, increment: int = 1):
        async with self._lock:
            task = self.tasks.get(task_id)
            if task and chapter_id in task.chapters:
                task.chapters[chapter_id].downloaded_pages += increment
                task.updated_at = datetime.now()
                self.dirty_tasks.add(task_id)

    async def update_chapter_status(self, task_id: str, chapter_id: str, status: TaskStatus, error: str = None, total_pages: int = None):
        async with self._lock:
            task = self.tasks.get(task_id)
            if task and chapter_id in task.chapters:
                task.chapters[chapter_id].status = status
                if error:
                    task.chapters[chapter_id].error_message = error
                if total_pages is not None:
                    task.chapters[chapter_id].total_pages = total_pages
                task.updated_at = datetime.now()
                self.dirty_tasks.add(task_id)

    async def update_task_status(self, task_id: str, status: TaskStatus, error: str = None):
        async with self._lock:
            task = self.tasks.get(task_id)
            if task:
                task.status = status
                if error:
                    task.error_message = error
                task.updated_at = datetime.now()
                self.dirty_tasks.add(task_id)

    async def mark_dirty(self, task_id: str):
        async with self._lock:
            self.dirty_tasks.add(task_id)

    async def flush_dirty(self):
        to_flush = []
        async with self._lock:
            for tid in list(self.dirty_tasks):
                if tid in self.tasks:
                    to_flush.append(self.tasks[tid].model_copy(deep=True))
            self.dirty_tasks.clear()
        
        for task in to_flush:
            try:
                await self.task_storage.save_task(task)
            except Exception as e:
                logger.error(f"Error flushing task {task.task_id}: {e}")

class ArchiveEngine:
    def __init__(
        self, 
        manager: ComicManager, 
        library_storage: ILibraryStorage, 
        task_storage: ITaskStorage, 
        media_storage: IMediaStorage, 
        worker_count: int = 5,
        max_concurrent_tasks: int = 2
    ):
        self.manager = manager
        self.library_storage = library_storage
        self.task_storage = task_storage
        self.media_storage = media_storage
        self.worker_count = worker_count
        self.max_concurrent_tasks = max_concurrent_tasks
        
        self.tracker = ProgressTracker(self.task_storage)
        self.queue: asyncio.Queue[PageDownloadJob] = asyncio.Queue()
        self._running = False
        self._main_task = None
        self._flusher_task = None
        self._workers = []
        
        self._active_coordinators: Dict[str, asyncio.Task] = {}
        self._cancellation_events: Dict[str, asyncio.Event] = {}

    async def start(self):
        if self._running: return
        self._running = True
        
        # Recover paused tasks
        tasks = await self.task_storage.list_tasks()
        for t in tasks:
            if t.status == TaskStatus.DOWNLOADING:
                t.status = TaskStatus.PAUSED
                await self.task_storage.save_task(t)

        self._flusher_task = asyncio.create_task(self._flush_loop())
        for _ in range(self.worker_count):
            w = asyncio.create_task(self._page_worker())
            self._workers.append(w)
            
        self._main_task = asyncio.create_task(self._coordinator_loop())
        logger.info(f"Archive Engine started with {self.worker_count} workers.")

    async def stop(self):
        self._running = False
        if self._main_task:
            self._main_task.cancel()
            
        for event in self._cancellation_events.values():
            event.set()
            
        for _ in range(len(self._workers)):
            await self.queue.put(None)
            
        await asyncio.gather(*self._workers, return_exceptions=True)
        
        if self._flusher_task:
            self._flusher_task.cancel()
            
        await self.tracker.flush_dirty()
        logger.info("Archive Engine stopped.")

    async def submit_sync(self, provider_id: str, comic_id: str) -> DownloadTask:
        task_id = f"{provider_id}::{comic_id}"
        library_comic = await self.library_storage.get_comic(provider_id, comic_id)
        if not library_comic:
            library_comic = await self.track_comic(provider_id, comic_id)

        task = await self.task_storage.get_task(task_id)
        if task:
            if task.status in [TaskStatus.QUEUED, TaskStatus.DOWNLOADING]:
                return task
            task.status = TaskStatus.QUEUED
            task.error_message = None
            task.updated_at = datetime.now()
            task.comic_title = library_comic.title
            task.cover_url = library_comic.cover_url
        else:
            task = DownloadTask(
                task_id=task_id,
                provider_id=provider_id,
                comic_id=comic_id,
                comic_title=library_comic.title,
                cover_url=library_comic.cover_url,
                status=TaskStatus.QUEUED
            )
            
        await self.task_storage.save_task(task)
        logger.info(f"Task submitted: {task_id}")
        return task

    async def track_comic(self, provider_id: str, comic_id: str) -> LocalComic:
        self.manager.use(provider_id)
        comic_detail = await asyncio.to_thread(self.manager.fetch_comic_detail, comic_id)
        
        library_comic = LocalComic(
            provider_id=provider_id,
            id=comic_id,
            title=comic_detail.title,
            author=comic_detail.author,
            tags=comic_detail.tags,
            description=comic_detail.description,
            cover_url=comic_detail.cover_url,
            local_path=f"{provider_id}/{comic_id}"
        )
        await self.library_storage.save_comic(library_comic)
        
        # Async cover download
        asyncio.create_task(self._download_cover(provider_id, comic_id, comic_detail.cover_url))
        
        return library_comic

    async def _download_cover(self, provider_id: str, comic_id: str, url: str):
        try:
            async with httpx.AsyncClient() as client:
                self.manager.use(provider_id)
                content, content_type = await self.manager.provider.download_image(client, url)
                filename = await self.media_storage.save_image(provider_id, comic_id, 'cover', 0, content, content_type)
                
                library_comic = await self.library_storage.get_comic(provider_id, comic_id)
                if library_comic:
                    library_comic.cover_url = f"{provider_id}/{comic_id}/{filename}"
                    await self.library_storage.save_comic(library_comic)
        except Exception as e:
            logger.error(f"Failed to download cover for {comic_id}: {e}")

    def pause_task(self, task_id: str) -> bool:
        task = asyncio.run_coroutine_threadsafe(self.task_storage.get_task(task_id), asyncio.get_event_loop()).result()
        if not task: return False
        
        if task.status in [TaskStatus.QUEUED, TaskStatus.DOWNLOADING]:
            if task_id in self._cancellation_events:
                self._cancellation_events[task_id].set()
            task.status = TaskStatus.PAUSED
            if task_id in self.tracker.tasks:
                self.tracker.tasks[task_id].status = TaskStatus.PAUSED
            asyncio.run_coroutine_threadsafe(self.task_storage.save_task(task), asyncio.get_event_loop())
            return True
        return False
        
    async def pause_task_async(self, task_id: str) -> bool:
        task = await self.task_storage.get_task(task_id)
        if not task: return False
        
        if task.status in [TaskStatus.QUEUED, TaskStatus.DOWNLOADING]:
            if task_id in self._cancellation_events:
                self._cancellation_events[task_id].set()
            task.status = TaskStatus.PAUSED
            if task_id in self.tracker.tasks:
                self.tracker.tasks[task_id].status = TaskStatus.PAUSED
            await self.task_storage.save_task(task)
            return True
        return False

    async def resume_task_async(self, task_id: str) -> bool:
        task = await self.task_storage.get_task(task_id)
        if not task or task.status not in [TaskStatus.PAUSED, TaskStatus.FAILED]:
            return False
            
        task.status = TaskStatus.QUEUED
        task.error_message = None
        task.updated_at = datetime.now()
        if task_id in self.tracker.tasks:
            self.tracker.tasks[task_id].status = TaskStatus.QUEUED
            self.tracker.tasks[task_id].error_message = None
        await self.task_storage.save_task(task)
        return True

    async def cancel_task_async(self, task_id: str) -> bool:
        task = await self.task_storage.get_task(task_id)
        if not task: return False
            
        if task.status == TaskStatus.DOWNLOADING:
            if task_id in self._cancellation_events:
                self._cancellation_events[task_id].set()
            
        task.status = TaskStatus.CANCELLED
        await self.task_storage.save_task(task)
        return True

    async def get_progress(self, provider_id: str, comic_id: str) -> Optional[DownloadTask]:
        task_id = f"{provider_id}::{comic_id}"
        # Read from memory if active, else from storage
        mem_task = await self.tracker.load_task(task_id)
        if mem_task:
            return mem_task
        return await self.task_storage.get_task(task_id)

    async def _flush_loop(self):
        while self._running:
            try:
                await asyncio.sleep(1.5)
                await self.tracker.flush_dirty()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Flusher error: {e}")

    async def _page_worker(self):
        async with httpx.AsyncClient(timeout=15.0) as client:
            while self._running:
                try:
                    job = await self.queue.get()
                    if job is None:
                        self.queue.task_done()
                        break
                        
                    cancel_event = self._cancellation_events.get(job.task_id)
                    if cancel_event and cancel_event.is_set():
                        self.queue.task_done()
                        continue

                    try:
                        self.manager.use(job.provider_id)
                        content, content_type = await self.manager.provider.download_image(client, job.url)
                        await self.media_storage.save_image(
                            job.provider_id, job.comic_id, job.chapter_id, job.page_index, content, content_type
                        )
                        await self.tracker.update_page_progress(job.task_id, job.chapter_id, 1)
                    except Exception as e:
                        logger.error(f"Failed to download page {job.page_index} for {job.chapter_id}: {e}")
                        
                    self.queue.task_done()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Worker error: {e}")

    async def _coordinator_loop(self):
        while self._running:
            try:
                if len(self._active_coordinators) < self.max_concurrent_tasks:
                    tasks = await self.task_storage.list_tasks()
                    queued_tasks = [t for t in tasks if t.status == TaskStatus.QUEUED]
                    queued_tasks.sort(key=lambda t: t.created_at)
                    
                    for task in queued_tasks:
                        if len(self._active_coordinators) >= self.max_concurrent_tasks:
                            break
                        if task.task_id not in self._active_coordinators:
                            self._start_task(task)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Coordinator loop error: {e}")
                
            await asyncio.sleep(2.0)

    def _start_task(self, task: DownloadTask):
        cancel_event = asyncio.Event()
        self._cancellation_events[task.task_id] = cancel_event
        t = asyncio.create_task(self._process_task(task.task_id, cancel_event))
        self._active_coordinators[task.task_id] = t
        t.add_done_callback(lambda x: self._cleanup_task(task.task_id))

    def _cleanup_task(self, task_id: str):
        self._active_coordinators.pop(task_id, None)
        self._cancellation_events.pop(task_id, None)

    async def _process_task(self, task_id: str, cancel_event: asyncio.Event):
        task = await self.tracker.load_task(task_id)
        if not task: return
        
        await self.tracker.update_task_status(task_id, TaskStatus.DOWNLOADING)
        
        try:
            self.manager.use(task.provider_id)
            
            # 1. Fetch remote chapters
            remote_chapters = await asyncio.to_thread(self.manager.fetch_all_chapters, task.comic_id)
            
            # 2. Sync chapters
            new_chapters_added = False
            for r_ch in remote_chapters:
                if r_ch.id not in task.chapters:
                    task.chapters[r_ch.id] = ChapterTask(chapter_id=r_ch.id, title=r_ch.title)
                    new_chapters_added = True
            
            if new_chapters_added:
                await self.tracker.mark_dirty(task_id)
                await self.tracker.flush_dirty() 

            # 3. Process each chapter
            for ch_id, ch_task in task.chapters.items():
                if cancel_event.is_set(): break
                if ch_task.status == TaskStatus.COMPLETED:
                    actual_dl = await self.media_storage.count_downloaded_images(task.provider_id, task.comic_id, ch_id)
                    if ch_task.total_pages > 0 and actual_dl >= ch_task.total_pages:
                        continue
                        
                await self.tracker.update_chapter_status(task_id, ch_id, TaskStatus.DOWNLOADING)
                
                try:
                    images = await asyncio.to_thread(self.manager.fetch_chapter_images, task.comic_id, ch_id)
                    await self.tracker.update_chapter_status(task_id, ch_id, TaskStatus.DOWNLOADING, total_pages=len(images))
                    
                    downloaded = await self.media_storage.count_downloaded_images(task.provider_id, task.comic_id, ch_id)
                    
                    # Concurrently check existing images
                    async def _check(idx, img):
                        exists = await self.media_storage.check_image_exists(task.provider_id, task.comic_id, ch_id, idx)
                        return None if exists else (idx, img)
                        
                    checks = await asyncio.gather(*[_check(idx, img) for idx, img in enumerate(images)])
                    missing_images = [c for c in checks if c is not None]

                    # Reset downloaded count in memory for accurate tracking via worker increments
                    task.chapters[ch_id].downloaded_pages = downloaded
                    await self.tracker.mark_dirty(task_id)

                    for idx, img in missing_images:
                        if cancel_event.is_set(): break
                        job = PageDownloadJob(task_id, task.provider_id, task.comic_id, ch_id, idx, img.url)
                        await self.queue.put(job)
                        
                    if not cancel_event.is_set():
                        await self.queue.join() 
                        
                        actual_dl = await self.media_storage.count_downloaded_images(task.provider_id, task.comic_id, ch_id)
                        if actual_dl >= len(images):
                            await self.tracker.update_chapter_status(task_id, ch_id, TaskStatus.COMPLETED)
                        else:
                            await self.tracker.update_chapter_status(task_id, ch_id, TaskStatus.FAILED, error="Not all pages downloaded.")

                except Exception as e:
                    logger.error(f"Error chapter {ch_id}: {e}")
                    await self.tracker.update_chapter_status(task_id, ch_id, TaskStatus.FAILED, error=str(e))
                    
            if cancel_event.is_set():
                await self.tracker.update_task_status(task_id, TaskStatus.PAUSED)
            else:
                task = await self.tracker.load_task(task_id)
                all_done = all(c.status == TaskStatus.COMPLETED for c in task.chapters.values())
                any_failed = any(c.status == TaskStatus.FAILED for c in task.chapters.values())
                
                if all_done and len(task.chapters) > 0:
                    await self.tracker.update_task_status(task_id, TaskStatus.COMPLETED)
                elif any_failed:
                    await self.tracker.update_task_status(task_id, TaskStatus.FAILED)
                else:
                    await self.tracker.update_task_status(task_id, TaskStatus.COMPLETED)
                    
        except Exception as e:
            logger.error(f"Task process error {task_id}: {e}")
            await self.tracker.update_task_status(task_id, TaskStatus.FAILED, error=str(e))
