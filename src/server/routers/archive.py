from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import List
import structlog

from src.storage.local_storage import storage
from src.storage.models import ArchivedComic
from src.archiver.service import ArchiverService
from src.manager.comic_manager import ComicManager

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/v1/archive", tags=["Archive"])

def get_archiver():
    manager = ComicManager()
    return ArchiverService(manager)

@router.get("/", response_model=List[ArchivedComic])
def list_archived_comics():
    """List all locally archived comics."""
    return storage.list_comics()

@router.get("/{provider_id}/{comic_id}", response_model=ArchivedComic)
def get_archived_comic(provider_id: str, comic_id: str):
    """Get metadata for a specific archived comic."""
    comic = storage.get_comic(provider_id, comic_id)
    if not comic:
        raise HTTPException(status_code=404, detail="Archived comic not found")
    return comic

@router.post("/{provider_id}/{comic_id}/track")
async def track_comic(
    provider_id: str, 
    comic_id: str, 
    archiver: ArchiverService = Depends(get_archiver)
):
    """
    Add a comic to the tracking library without downloading chapters.
    """
    archived = await archiver.track_comic(provider_id, comic_id)
    return {"message": f"Successfully tracked comic {comic_id}", "data": archived}

@router.post("/{provider_id}/{comic_id}/sync")
async def sync_comic(
    provider_id: str, 
    comic_id: str, 
    background_tasks: BackgroundTasks,
    archiver: ArchiverService = Depends(get_archiver)
):
    """
    Perform an incremental sync in the background.
    Downloads only missing or failed chapters.
    """
    background_tasks.add_task(archiver.sync_comic, provider_id, comic_id)
    return {"message": f"Incremental sync started for {comic_id} on {provider_id} in the background."}

@router.delete("/{provider_id}/{comic_id}")
def delete_archived_comic(
    provider_id: str, 
    comic_id: str,
    archiver: ArchiverService = Depends(get_archiver)
):
    """Delete an archived comic and all its local files."""
    try:
        archiver.delete_archived_comic(provider_id, comic_id)
        return {"message": f"Comic {comic_id} deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
