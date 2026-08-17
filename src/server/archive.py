from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Request
from typing import List
from src.application.comic_manager import ComicManager
from src.application.archiver_engine import ArchiverEngine
from src.storage.factory import StorageFactory, StorageEngine
from src.domain.models import ArchivedComic

archive_router = APIRouter(prefix="/api/v1/archive", tags=["Archive"])

def get_archiver():
    manager = ComicManager()
    storage = StorageFactory.get_storage(StorageEngine.JSON)
    return ArchiverEngine(manager, storage)

@archive_router.get("/", response_model=List[ArchivedComic])
def list_archived_comics():
    """List all locally archived comics."""
    storage = StorageFactory.get_storage(StorageEngine.JSON)
    return storage.list_comics()

@archive_router.get("/{provider_id}/{comic_id}", response_model=ArchivedComic)
def get_archived_comic(provider_id: str, comic_id: str):
    """Get metadata for a specific archived comic."""
    storage = StorageFactory.get_storage(StorageEngine.JSON)
    comic = storage.get_comic(provider_id, comic_id)
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

@archive_router.post("/{provider_id}/{comic_id}/sync")
async def sync_comic(
    provider_id: str, 
    comic_id: str, 
    request: Request,
    archiver: ArchiverEngine = Depends(get_archiver)
):
    """Perform an incremental sync in the background."""
    request.app.state.task_manager.submit(archiver.sync_comic(provider_id, comic_id))
    return {"message": f"Incremental sync started for {comic_id} on {provider_id} in the background."}

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
