from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Request
from typing import List
from functools import lru_cache

from src.application.comic_manager import ComicManager
from src.application.archiver_engine import ArchiverEngine
from src.storage.factory import StorageFactory, StorageEngine
from src.domain.models import ArchivedComic

archive_router = APIRouter(prefix="/api/v1/archive", tags=["Archive"])

@lru_cache()
def get_archiver():
    manager = ComicManager()
    provider = StorageFactory.get_provider(StorageEngine.JSON)
    return ArchiverEngine(manager, provider.get_archive_storage())

@archive_router.get("/", response_model=List[ArchivedComic])
def list_archived_comics():
    """List all locally archived comics."""
    provider = StorageFactory.get_provider(StorageEngine.JSON)
    return provider.get_archive_storage().list_comics()

@archive_router.get("/{provider_id}/{comic_id}", response_model=ArchivedComic)
def get_archived_comic(provider_id: str, comic_id: str):
    """Get metadata for a specific archived comic."""
    provider = StorageFactory.get_provider(StorageEngine.JSON)
    comic = provider.get_archive_storage().get_comic(provider_id, comic_id)
    if not comic:
        raise HTTPException(status_code=404, detail="Archived comic not found")
    return comic

@archive_router.post("/{provider_id}/{comic_id}/track")
async def track_comic(
    provider_id: str, 
    comic_id: str, 
    archiver: ArchiverEngine = Depends(get_archiver)
):
    """Add a comic to the tracking library without downloading chapters."""
    archived = await archiver.track_comic(provider_id, comic_id)
    return {"message": f"Successfully tracked comic {comic_id}", "data": archived}

@archive_router.get("/sync/active")
async def get_active_sync_tasks(request: Request):
    """Get a list of all currently active sync tasks."""
    active_tasks = request.app.state.task_manager.get_active_tasks()
    
    result = []
    for task_id in active_tasks:
        if task_id.startswith("sync::"):
            parts = task_id.split("::")
            if len(parts) == 3:
                _, provider, comic = parts
                result.append({
                    "task_id": task_id,
                    "provider_id": provider,
                    "comic_id": comic
                })
    
    return {"active_tasks": result, "total": len(result)}

@archive_router.post("/{provider_id}/{comic_id}/sync")
async def sync_comic(
    provider_id: str, 
    comic_id: str, 
    request: Request,
    archiver: ArchiverEngine = Depends(get_archiver)
):
    """Perform an incremental sync in the background."""
    task_id = f"sync::{provider_id}::{comic_id}"
    submitted = request.app.state.task_manager.submit(task_id, archiver.sync_comic(provider_id, comic_id))
    
    if not submitted:
        return {"message": f"Sync is already running for {comic_id} on {provider_id}.", "status": "running"}
        
    return {"message": f"Incremental sync started for {comic_id} on {provider_id} in the background.", "status": "started"}

@archive_router.delete("/{provider_id}/{comic_id}")
def delete_archived_comic(
    provider_id: str, 
    comic_id: str,
    archiver: ArchiverEngine = Depends(get_archiver)
):
    """Delete an archived comic and all its local files."""
    try:
        archiver.delete_archived_comic(provider_id, comic_id)
        return {"message": f"Comic {comic_id} deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@archive_router.get("/{provider_id}/{comic_id}/progress")
def get_sync_progress(
    provider_id: str, 
    comic_id: str,
    archiver: ArchiverEngine = Depends(get_archiver)
):
    """Get real-time detailed sync progress for a comic."""
    try:
        return archiver.get_sync_progress(provider_id, comic_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
