from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse
from typing import List
import urllib.parse

from src.core.interfaces import ILibraryService
from src.domain.models import LocalComicItem, LocalComicDetail, LocalChapterImages, LocalChapterItem, LibraryComic
from src.domain.exceptions import AppBaseError
from src.server.dependencies import get_library_service, get_container, resolve_provider

library_router = APIRouter(prefix="/api/v1/library", tags=["Library"])

def _format_cover(request: Request, cover_url: str) -> str:
    if not cover_url or cover_url.startswith("http"):
        return cover_url
    parts = cover_url.split('/')
    encoded_parts = [urllib.parse.quote(p) for p in parts]
    return f"{request.base_url}api/v1/library/media/" + "/".join(encoded_parts)

@library_router.get("/", response_model=List[LocalComicItem])
async def explore_library(
    request: Request,
    library_service: ILibraryService = Depends(get_library_service)
):
    comics = await library_service.list_comics()
    for c in comics:
        c.cover_url = _format_cover(request, c.cover_url)
    return comics

@library_router.get("/media/{path:path}")
async def get_archived_media(path: str, container = Depends(get_container)):
    try:
        stream_gen, content_type = await container.media_storage.get_image_stream(path)
        return StreamingResponse(stream_gen, media_type=content_type)
    except AppBaseError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@library_router.get("/search", response_model=List[LocalComicItem])
async def search_library_comics(
    request: Request,
    keyword: str,
    library_service: ILibraryService = Depends(get_library_service)
):
    try:
        comics = await library_service.search_comics(keyword)
        for c in comics:
            c.cover_url = _format_cover(request, c.cover_url)
        return comics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@library_router.get("/explore", response_model=List[LocalComicItem])
async def explore_library_comics(
    request: Request,
    library_service: ILibraryService = Depends(get_library_service)
):
    try:
        comics = await library_service.list_comics()
        for c in comics:
            c.cover_url = _format_cover(request, c.cover_url)
        return comics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@library_router.get("/{provider_id}/{comic_id}", response_model=LocalComicDetail)
async def get_library_comic_detail(
    request: Request,
    comic_id: str, 
    provider_id: str = Depends(resolve_provider),
    library_service: ILibraryService = Depends(get_library_service)
):
    try:
        detail = await library_service.get_comic_detail(provider_id, comic_id)
        detail.cover_url = _format_cover(request, detail.cover_url)
        return detail
    except AppBaseError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@library_router.get("/{provider_id}/{comic_id}/chapters", response_model=List[LocalChapterItem])
async def get_library_comic_chapters(
    comic_id: str, 
    provider_id: str = Depends(resolve_provider),
    library_service: ILibraryService = Depends(get_library_service)
):
    try:
        return await library_service.get_comic_chapters(provider_id, comic_id)
    except AppBaseError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@library_router.get("/{provider_id}/{comic_id}/chapters/{chapter_id}", response_model=LocalChapterImages)
async def get_library_chapter_images(
    request: Request,
    comic_id: str, 
    chapter_id: str, 
    provider_id: str = Depends(resolve_provider),
    library_service: ILibraryService = Depends(get_library_service)
):
    try:
        chapter_data = await library_service.get_chapter_images(provider_id, comic_id, chapter_id)
        
        base_url = f"{request.base_url}api/v1/library/media/"
        formatted_images = []
        for img in chapter_data.images:
            parts = img.split('/')
            encoded_parts = [urllib.parse.quote(p) for p in parts]
            formatted_images.append(base_url + "/".join(encoded_parts))
            
        chapter_data.images = formatted_images
        return chapter_data
    except AppBaseError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
