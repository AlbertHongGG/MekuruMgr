from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List

from src.core.container import AppContainer
from src.domain.models.archive import LibraryComic, DownloadTask, TaskStatus
from src.application.archive_engine import ArchiveEngine
from src.server.dependencies import resolve_provider


archive_router = APIRouter(prefix="/api/v1/archive", tags=["Archive"])

def get_archive_engine(request: Request) -> ArchiveEngine:
    return request.app.state.container.archive_engine

@archive_router.get("/", response_model=List[LibraryComic])
async def list_archived_comics(archive_engine: ArchiveEngine = Depends(get_archive_engine)):
    """List all locally tracked comics."""
    
    return await archive_engine.library_storage.list_comics()

@archive_router.get("/queue", response_model=List[DownloadTask])
async def get_active_queue(archive_engine: ArchiveEngine = Depends(get_archive_engine)):
    """Get a list of all active download tasks."""
    tasks = await archive_engine.task_storage.list_tasks()
    return tasks

@archive_router.get("/{provider_id}/{comic_id}", response_model=LibraryComic)
async def get_archived_comic(
    comic_id: str, 
    provider_id: str = Depends(resolve_provider),
    archive_engine: ArchiveEngine = Depends(get_archive_engine)
):
    """Get metadata for a specific tracked comic."""
    
    comic = await archive_engine.library_storage.get_comic(provider_id, comic_id)
    if not comic:
        raise HTTPException(status_code=404, detail="Tracked comic not found")
    return comic

@archive_router.post("/{provider_id}/{comic_id}/track")
async def track_comic(
    comic_id: str, 
    provider_id: str = Depends(resolve_provider),
    archive_engine: ArchiveEngine = Depends(get_archive_engine)
):
    """Add a comic to the tracking library without downloading chapters."""
    try:
        archived = await archive_engine.track_comic(provider_id, comic_id)
        return {"message": f"Successfully tracked comic {comic_id}", "data": archived}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@archive_router.post("/{provider_id}/{comic_id}/sync", response_model=DownloadTask)
async def sync_comic(
    comic_id: str, 
    provider_id: str = Depends(resolve_provider),
    archive_engine: ArchiveEngine = Depends(get_archive_engine)
):
    """Perform an incremental sync in the background by submitting to queue."""
    try:
        task = await archive_engine.submit_sync(provider_id, comic_id)
        return task
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@archive_router.post("/{provider_id}/{comic_id}/pause")
async def pause_comic(
    comic_id: str, 
    provider_id: str = Depends(resolve_provider),
    archive_engine: ArchiveEngine = Depends(get_archive_engine)
):
    """Pause an active sync task."""
    task_id = f"{provider_id}::{comic_id}"
    success = await archive_engine.pause_task_async(task_id)
    if success:
        return {"message": f"Sync task paused for {comic_id}", "status": "paused"}
    raise HTTPException(status_code=404, detail="Active task not found or cannot be paused")

@archive_router.post("/{provider_id}/{comic_id}/resume")
async def resume_comic(
    comic_id: str, 
    provider_id: str = Depends(resolve_provider),
    archive_engine: ArchiveEngine = Depends(get_archive_engine)
):
    """Resume a paused sync task."""
    task_id = f"{provider_id}::{comic_id}"
    success = await archive_engine.resume_task_async(task_id)
    if success:
        return {"message": f"Sync task resumed for {comic_id}", "status": "queued"}
    raise HTTPException(status_code=404, detail="Task not found or not in pausable state")

@archive_router.delete("/{provider_id}/{comic_id}/cancel")
async def cancel_sync_comic(
    comic_id: str, 
    provider_id: str = Depends(resolve_provider),
    archive_engine: ArchiveEngine = Depends(get_archive_engine)
):
    """Cancel a sync task."""
    task_id = f"{provider_id}::{comic_id}"
    success = await archive_engine.cancel_task_async(task_id)
    if success:
        return {"message": f"Sync task cancelled for {comic_id}", "status": "cancelled"}
    raise HTTPException(status_code=404, detail="Task not found")

@archive_router.delete("/{provider_id}/{comic_id}")
async def delete_archived_comic(
    comic_id: str,
    provider_id: str = Depends(resolve_provider), 
    archive_engine: ArchiveEngine = Depends(get_archive_engine)
):
    """Delete an archived comic and all its local files."""
    try:
        await archive_engine.library_storage.delete_comic(provider_id, comic_id)
        await archive_engine.media_storage.delete_media(provider_id, comic_id)
        
        task_id = f"{provider_id}::{comic_id}"
        await archive_engine.cancel_task_async(task_id)
        await archive_engine.task_storage.delete_task(task_id)
        
        return {"message": f"Comic {comic_id} deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@archive_router.get("/{provider_id}/{comic_id}/progress")
async def get_sync_progress(
    comic_id: str,
    provider_id: str = Depends(resolve_provider), 
    archive_engine: ArchiveEngine = Depends(get_archive_engine)
):
    """Get real-time detailed sync progress for a comic."""
    task = await archive_engine.get_progress(provider_id, comic_id)
    if not task:
        raise HTTPException(status_code=404, detail="No progress found for comic")
    return task
