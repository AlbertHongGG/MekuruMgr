from fastapi import APIRouter, HTTPException, Request, Depends
from typing import List
from pydantic import BaseModel

from src.application.user_service import UserService
from src.application.library_service import LibraryService
from src.storage.factory import StorageFactory, StorageEngine
from src.domain.user_models import UserComicInteraction

user_router = APIRouter(prefix="/api/v1/user", tags=["User Profile"])

def get_user_service(request: Request) -> UserService:
    provider = StorageFactory.get_provider(StorageEngine.JSON)
    base_media_url = str(request.base_url) + "api/v1/library/media/"
    library_service = LibraryService(storage=provider.get_archive_storage(), base_media_url=base_media_url)
    return UserService(user_storage=provider.get_user_storage(), library_service=library_service)

class ReadProgressRequest(BaseModel):
    chapter_id: str
    page_index: int

@user_router.get("/favorites", response_model=List[UserComicInteraction])
def get_user_favorites(service: UserService = Depends(get_user_service)):
    """Get all favorite interactions directly."""
    return service.get_all_favorites()

@user_router.get("/interactions/{provider_id}/{comic_id}", response_model=UserComicInteraction)
def get_interaction(provider_id: str, comic_id: str, service: UserService = Depends(get_user_service)):
    """Get full interaction details for a specific comic."""
    return service.get_interaction(provider_id, comic_id)

@user_router.post("/interactions/{provider_id}/{comic_id}/favorite")
def toggle_favorite(provider_id: str, comic_id: str, service: UserService = Depends(get_user_service)):
    """Toggle the favorite status of a comic."""
    new_status = service.toggle_favorite(provider_id, comic_id)
    return {"message": "Favorite status updated", "is_favorite": new_status}

@user_router.post("/interactions/{provider_id}/{comic_id}/read")
def update_read_progress(provider_id: str, comic_id: str, payload: ReadProgressRequest, service: UserService = Depends(get_user_service)):
    """Update reading progress for a chapter."""
    service.update_reading_progress(provider_id, comic_id, payload.chapter_id, payload.page_index)
    return {"message": "Reading progress updated"}
