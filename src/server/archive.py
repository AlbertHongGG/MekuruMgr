from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List

from src.storage.factory import StorageFactory
from src.domain.models.archive import LibraryComic, DownloadTask, TaskStatus
from src.application.queue_service import DownloadQueueService
from src.server.deps import resolve_provider_id

archive_router = APIRouter(prefix="/api/v1/archive", tags=["Archive"])

def get_queue_service(request: Request) -> DownloadQueueService:
    return request.app.state.queue_service

@archive_router.get("/", response_model=List[LibraryComic])
def list_archived_comics():
    """List all locally tracked comics."""
    provider = StorageFactory.get_provider()
    return provider.get_library_storage().list_comics()

@archive_router.get("/queue", response_model=List[DownloadTask])
def get_active_queue(queue_service: DownloadQueueService = Depends(get_queue_service)):
    """Get a list of all active download tasks."""
    tasks = queue_service.task_storage.list_tasks()
    return tasks

@archive_router.get("/{provider_id}/{comic_id}", response_model=LibraryComic)
def get_archived_comic(comic_id: str, provider_id: str = Depends(resolve_provider_id)):
    """Get metadata for a specific tracked comic."""
    provider = StorageFactory.get_provider()
    comic = provider.get_library_storage().get_comic(provider_id, comic_id)
    if not comic:
        raise HTTPException(status_code=404, detail="Tracked comic not found")
    return comic

@archive_router.post("/{provider_id}/{comic_id}/track")
async def track_comic(
    comic_id: str, 
    provider_id: str = Depends(resolve_provider_id),
    queue_service: DownloadQueueService = Depends(get_queue_service)
):
    """Add a comic to the tracking library without downloading chapters."""
    try:
        archived = await queue_service.track_comic(provider_id, comic_id)
        return {"message": f"Successfully tracked comic {comic_id}", "data": archived}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@archive_router.post("/{provider_id}/{comic_id}/sync", response_model=DownloadTask)
async def sync_comic(
    comic_id: str, 
    provider_id: str = Depends(resolve_provider_id),
    queue_service: DownloadQueueService = Depends(get_queue_service)
):
    """Perform an incremental sync in the background by submitting to queue."""
    try:
        task = await queue_service.submit_sync(provider_id, comic_id)
        return task
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@archive_router.post("/{provider_id}/{comic_id}/pause")
async def pause_comic(
    comic_id: str, 
    provider_id: str = Depends(resolve_provider_id),
    queue_service: DownloadQueueService = Depends(get_queue_service)
):
    """Pause an active sync task."""
    task_id = f"{provider_id}::{comic_id}"
    success = queue_service.pause_task(task_id)
    if success:
        return {"message": f"Sync task paused for {comic_id}", "status": "paused"}
    raise HTTPException(status_code=404, detail="Active task not found or cannot be paused")

@archive_router.post("/{provider_id}/{comic_id}/resume")
async def resume_comic(
    comic_id: str, 
    provider_id: str = Depends(resolve_provider_id),
    queue_service: DownloadQueueService = Depends(get_queue_service)
):
    """Resume a paused sync task."""
    task_id = f"{provider_id}::{comic_id}"
    success = queue_service.resume_task(task_id)
    if success:
        return {"message": f"Sync task resumed for {comic_id}", "status": "queued"}
    raise HTTPException(status_code=404, detail="Task not found or not in pausable state")

@archive_router.delete("/{provider_id}/{comic_id}/cancel")
async def cancel_sync_comic(
    comic_id: str, 
    provider_id: str = Depends(resolve_provider_id),
    queue_service: DownloadQueueService = Depends(get_queue_service)
):
    """Cancel a sync task."""
    task_id = f"{provider_id}::{comic_id}"
    success = queue_service.cancel_task(task_id)
    if success:
        return {"message": f"Sync task cancelled for {comic_id}", "status": "cancelled"}
    raise HTTPException(status_code=404, detail="Task not found")

@archive_router.delete("/{provider_id}/{comic_id}")
def delete_archived_comic(
    comic_id: str,
    provider_id: str = Depends(resolve_provider_id), 
    queue_service: DownloadQueueService = Depends(get_queue_service)
):
    """Delete an archived comic and all its local files."""
    try:
        queue_service.library_storage.delete_comic(provider_id, comic_id)
        queue_service.media_storage.delete_media(provider_id, comic_id)
        
        task_id = f"{provider_id}::{comic_id}"
        queue_service.cancel_task(task_id)
        queue_service.task_storage.delete_task(task_id)
        
        return {"message": f"Comic {comic_id} deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@archive_router.get("/{provider_id}/{comic_id}/progress")
def get_sync_progress(
    comic_id: str,
    provider_id: str = Depends(resolve_provider_id), 
    queue_service: DownloadQueueService = Depends(get_queue_service)
):
    """Get real-time detailed sync progress for a comic."""
    task = queue_service.get_progress(provider_id, comic_id)
    if not task:
        raise HTTPException(status_code=404, detail="No progress found for comic")
    return task
