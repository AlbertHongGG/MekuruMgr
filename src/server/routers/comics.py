from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional

from src.core.domain_models import Comic, Chapter, PageImage
from src.core.constants import BuiltinProvider
from src.core.config import app_settings
from src.core.exceptions import AppBaseError
from src.manager.comic_manager import ComicManager

router = APIRouter(prefix="/api/v1/comics", tags=["Comics"])

def get_manager(provider: Optional[str] = None) -> ComicManager:
    try:
        # Fallback to default provider from .env if none provided
        target_provider = provider or app_settings.default_provider
        # Try to resolve built-in provider enum if applicable, otherwise use string
        try:
            target_provider = BuiltinProvider(target_provider)
        except ValueError:
            pass # It's a string ID for a 3rd party plugin, which is fine
        
        return ComicManager(target_provider)
    except AppBaseError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{comic_id}", response_model=Comic)
def get_comic(comic_id: str, provider: Optional[str] = Query(None, description="Plugin ID to use")):
    """Get basic details of a comic."""
    manager = get_manager(provider)
    try:
        return manager.fetch_comic_detail(comic_id)
    except AppBaseError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{comic_id}/chapters", response_model=List[Chapter])
def get_chapters(comic_id: str, provider: Optional[str] = Query(None)):
    """List all chapters of a comic."""
    manager = get_manager(provider)
    try:
        return manager.fetch_all_chapters(comic_id)
    except AppBaseError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{comic_id}/chapters/{chapter_id}/images", response_model=List[PageImage])
def get_chapter_images(comic_id: str, chapter_id: str, provider: Optional[str] = Query(None)):
    """Get all image pages for a specific chapter."""
    manager = get_manager(provider)
    try:
        return manager.fetch_chapter_images(comic_id, chapter_id)
    except AppBaseError as e:
        raise HTTPException(status_code=404, detail=str(e))
