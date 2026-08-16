from fastapi import APIRouter, HTTPException, Query
from typing import List
from src.application.comic_manager import ComicManager
from src.domain.models import Comic, Chapter, PageImage

comic_router = APIRouter(prefix="/api/v1/comics", tags=["Comics"])

@comic_router.get("/{provider_id}/search", response_model=List[Comic])
def search_comics(
    provider_id: str, 
    keyword: str = Query(..., description="Keyword to search"), 
    page: int = Query(1, ge=1), 
    page_size: int = Query(30, ge=1, le=100)
):
    """Search comics by keyword."""
    try:
        manager = ComicManager()
        manager.use(provider_id)
        return manager.search_comics(keyword, page, page_size)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

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

@comic_router.get("/{provider_id}/{comic_id}/chapters/{chapter_id}/images", response_model=List[PageImage])
def get_chapter_images(provider_id: str, comic_id: str, chapter_id: str):
    """Get all images for a specific chapter."""
    try:
        manager = ComicManager()
        manager.use(provider_id)
        return manager.fetch_chapter_images(comic_id, chapter_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
