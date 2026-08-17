from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from typing import List

from src.application.library_service import LibraryService
from src.domain.models import LocalComicItem, LocalComicDetail, LocalChapterImages
from src.domain.exceptions import AppBaseError
from src.storage.factory import StorageFactory, StorageEngine

library_router = APIRouter(prefix="/api/v1/library", tags=["Library"])

def get_service(request: Request) -> LibraryService:
    storage = StorageFactory.get_storage(StorageEngine.JSON)
    # The new absolute API URL for the media proxy
    base_media_url = str(request.base_url) + "api/v1/library/media/"
    return LibraryService(storage=storage, base_media_url=base_media_url)

@library_router.get("/media/{path:path}")
def get_archived_media(path: str):
    """Serve an archived media file using the storage engine."""
    try:
        storage = StorageFactory.get_storage(StorageEngine.JSON)
        stream_gen, content_type = storage.get_image_stream(path)
        return StreamingResponse(stream_gen, media_type=content_type)
    except AppBaseError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@library_router.get("/search", response_model=List[LocalComicItem])
def search_library_comics(keyword: str, request: Request):
    """Search locally available comics by keyword."""
    try:
        service = get_service(request)
        return service.search_comics(keyword)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@library_router.get("/explore", response_model=List[LocalComicItem])
def explore_library_comics(request: Request):
    """Explore all locally available comics (Alias for list)."""
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

@library_router.get("/{provider_id}/{comic_id}/chapters", response_model=List[LocalChapterItem])
def get_library_comic_chapters(provider_id: str, comic_id: str, request: Request):
    """Get only the COMPLETED chapters for a comic."""
    try:
        service = get_service(request)
        return service.get_comic_chapters(provider_id, comic_id)
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
