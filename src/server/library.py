from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse
from typing import List

from src.application.library_service import LibraryService
from src.domain.models import LocalComicItem, LocalComicDetail, LocalChapterImages, LocalChapterItem
from src.domain.exceptions import AppBaseError
from src.storage.factory import StorageFactory
from src.server.deps import resolve_provider_id

library_router = APIRouter(prefix="/api/v1/library", tags=["Library"])

def get_service(request: Request) -> LibraryService:
    provider = StorageFactory.get_provider()
    # The new absolute API URL for the media proxy
    base_media_url = str(request.base_url) + "api/v1/library/media/"
    return LibraryService(
        library_storage=provider.get_library_storage(),
        task_storage=provider.get_task_storage(),
        media_storage=provider.get_media_storage(),
        base_media_url=base_media_url
    )

@library_router.get("/media/{path:path}")
async def get_archived_media(path: str):
    """Serve an archived media file using the storage engine."""
    try:
        provider = StorageFactory.get_provider()
        stream_gen, content_type = await provider.get_media_storage().get_image_stream(path)
        return StreamingResponse(stream_gen, media_type=content_type)
    except AppBaseError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@library_router.get("/search", response_model=List[LocalComicItem])
async def search_library_comics(keyword: str, request: Request):
    """Search locally available comics by keyword."""
    try:
        service = get_service(request)
        return await service.search_comics(keyword)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@library_router.get("/explore", response_model=List[LocalComicItem])
async def explore_library_comics(request: Request):
    """Explore all locally available comics (Alias for list)."""
    try:
        service = get_service(request)
        return await service.list_comics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@library_router.get("/{provider_id}/{comic_id}", response_model=LocalComicDetail)
async def get_library_comic_detail(comic_id: str, request: Request, provider_id: str = Depends(resolve_provider_id)):
    """Get comic details and only the COMPLETED chapters."""
    try:
        service = get_service(request)
        return await service.get_comic_detail(provider_id, comic_id)
    except AppBaseError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@library_router.get("/{provider_id}/{comic_id}/chapters", response_model=List[LocalChapterItem])
async def get_library_comic_chapters(comic_id: str, request: Request, provider_id: str = Depends(resolve_provider_id)):
    """Get only the COMPLETED chapters for a comic."""
    try:
        service = get_service(request)
        return await service.get_comic_chapters(provider_id, comic_id)
    except AppBaseError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@library_router.get("/{provider_id}/{comic_id}/chapters/{chapter_id}", response_model=LocalChapterImages)
async def get_library_chapter_images(comic_id: str, chapter_id: str, request: Request, provider_id: str = Depends(resolve_provider_id)):
    """Get the full image URLs for a fully downloaded chapter."""
    try:
        service = get_service(request)
        return await service.get_chapter_images(provider_id, comic_id, chapter_id)
    except AppBaseError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
