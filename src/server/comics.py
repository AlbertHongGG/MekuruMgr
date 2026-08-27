from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List
from src.server.dependencies import resolve_provider, get_comic_manager
from src.application.comic_manager import ComicManager
from src.domain.models import ComicSearchResult, ComicDetail, Chapter, PageImage


comic_router = APIRouter(prefix="/api/v1/comics", tags=["Comics"])

@comic_router.get("/{provider_id}/search", response_model=List[ComicSearchResult])
def search_comics(keyword: str = Query(..., description="Keyword to search"), provider_id: str = Depends(resolve_provider), page: int = Query(1, ge=1), page_size: int = Query(30, ge=1, le=100), manager: ComicManager = Depends(get_comic_manager)):
    """Search comics by keyword."""
    try:
        manager.use(provider_id)
        return manager.search_comics(keyword, page, page_size)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@comic_router.get("/{provider_id}/explore", response_model=List[ComicSearchResult])
def explore_comics(provider_id: str = Depends(resolve_provider), page: int = Query(1, ge=1), page_size: int = Query(30, ge=1, le=100), manager: ComicManager = Depends(get_comic_manager)):
    """Explore/discover comics from a specific provider."""
    try:
        manager.use(provider_id)
        return manager.explore_comics(page, page_size)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@comic_router.get("/{provider_id}/{comic_id}", response_model=ComicDetail)
def get_comic(comic_id: str, provider_id: str = Depends(resolve_provider), manager: ComicManager = Depends(get_comic_manager)):
    """Get comic details from a specific provider."""
    try:
        manager.use(provider_id)
        return manager.fetch_comic_detail(comic_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@comic_router.get("/{provider_id}/{comic_id}/chapters", response_model=List[Chapter])
def get_comic_chapters(comic_id: str, provider_id: str = Depends(resolve_provider), manager: ComicManager = Depends(get_comic_manager)):
    """Get all chapters for a comic."""
    try:
        manager.use(provider_id)
        return manager.fetch_all_chapters(comic_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@comic_router.get("/{provider_id}/{comic_id}/chapters/{chapter_id}/images", response_model=List[PageImage])
def get_chapter_images(comic_id: str, chapter_id: str, provider_id: str = Depends(resolve_provider), manager: ComicManager = Depends(get_comic_manager)):
    """Get all images for a specific chapter."""
    try:
        manager.use(provider_id)
        return manager.fetch_chapter_images(comic_id, chapter_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
