from fastapi import APIRouter, HTTPException
from typing import List
from src.application.comic_manager import ComicManager
from src.domain.models import Comic, Chapter

comic_router = APIRouter(prefix="/api/v1/comics", tags=["Comics"])

@comic_router.get("/{provider_id}/{comic_id}", response_model=Comic)
def get_comic(provider_id: str, comic_id: str):
    """Get comic details from a specific provider."""
    try:
        manager = ComicManager()
        manager.use(provider_id)
        return manager.fetch_comic_detail(comic_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@comic_router.get("/{provider_id}/{comic_id}/chapters", response_model=List[Chapter])
def get_comic_chapters(provider_id: str, comic_id: str):
    """Get all chapters for a comic."""
    try:
        manager = ComicManager()
        manager.use(provider_id)
        return manager.fetch_all_chapters(comic_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
