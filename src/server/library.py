from fastapi import APIRouter, HTTPException, Request
from typing import List

from src.application.library_service import LibraryService
from src.domain.models import LocalComicItem, LocalComicDetail, LocalChapterImages
from src.domain.exceptions import AppBaseError

library_router = APIRouter(prefix="/api/v1/library", tags=["Library"])

def get_service(request: Request) -> LibraryService:
    # Use FastAPI's Request to get the exact base URL of the server
    # This allows absolute URLs (e.g. http://127.0.0.1:8000/media/)
    base_media_url = str(request.base_url) + "media/"
    return LibraryService(base_media_url=base_media_url)

@library_router.get("/", response_model=List[LocalComicItem])
def list_library_comics(request: Request):
    """List all locally available comics (Read-Only)."""
    try:
        service = get_service(request)
        return service.list_comics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@library_router.get("/{provider_id}/{comic_id}", response_model=LocalComicDetail)
def get_library_comic_detail(provider_id: str, comic_id: str, request: Request):
    """Get comic details and only the COMPLETED chapters."""
    try:
        service = get_service(request)
        return service.get_comic_detail(provider_id, comic_id)
    except AppBaseError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@library_router.get("/{provider_id}/{comic_id}/chapters/{chapter_id}", response_model=LocalChapterImages)
def get_library_chapter_images(provider_id: str, comic_id: str, chapter_id: str, request: Request):
    """Get the full image URLs for a fully downloaded chapter."""
    try:
        service = get_service(request)
        return service.get_chapter_images(provider_id, comic_id, chapter_id)
    except AppBaseError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
