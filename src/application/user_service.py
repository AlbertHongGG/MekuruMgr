import logging
from typing import List, Optional
from datetime import datetime

from src.storage.core.user_interface import IUserStorage
from src.application.library_service import LibraryService
from src.domain.user_models import UserComicInteraction, ReadingProgress, UserLibraryItem
from src.domain.exceptions import AppBaseError

logger = logging.getLogger(__name__)

class UserService:
    def __init__(self, user_storage: IUserStorage, library_service: LibraryService):
        self.storage = user_storage
        self.library_service = library_service

    def get_interaction(self, provider_id: str, comic_id: str) -> UserComicInteraction:
        """Get or create an interaction for a comic."""
        interaction = self.storage.get_interaction(provider_id, comic_id)
        if not interaction:
            interaction = UserComicInteraction(provider_id=provider_id, comic_id=comic_id)
        return interaction

    def toggle_favorite(self, provider_id: str, comic_id: str) -> bool:
        """Toggle favorite status. Returns the new status."""
        interaction = self.get_interaction(provider_id, comic_id)
        interaction.is_favorite = not interaction.is_favorite
        interaction.updated_at = datetime.now()
        self.storage.save_interaction(interaction)
        logger.info(f"Toggled favorite for {comic_id} on {provider_id} to {interaction.is_favorite}")
        return interaction.is_favorite

    def update_reading_progress(self, provider_id: str, comic_id: str, chapter_id: str, page_index: int) -> None:
        """Update the reading progress for a specific chapter."""
        interaction = self.get_interaction(provider_id, comic_id)
        
        if chapter_id not in interaction.reading_history:
            interaction.reading_history[chapter_id] = ReadingProgress(chapter_id=chapter_id, page_index=page_index)
        else:
            interaction.reading_history[chapter_id].page_index = page_index
            interaction.reading_history[chapter_id].updated_at = datetime.now()
            
        interaction.last_read_chapter_id = chapter_id
        interaction.updated_at = datetime.now()
        self.storage.save_interaction(interaction)
        logger.debug(f"Updated reading progress for {comic_id} / {chapter_id} to page {page_index}")

    def get_composed_favorites(self) -> List[UserLibraryItem]:
        """Get all favorites, combined with library metadata."""
        favorites = [i for i in self.storage.get_all_interactions() if i.is_favorite]
        
        result = []
        for fav in favorites:
            try:
                # Use library_service to get comic details
                detail = self.library_service.get_comic_detail(fav.provider_id, fav.comic_id)
                item = UserLibraryItem(
                    provider_id=fav.provider_id,
                    comic_id=fav.comic_id,
                    title=detail.title,
                    cover_url=detail.cover_url,
                    completed_chapters_count=len(self.library_service.get_comic_chapters(fav.provider_id, fav.comic_id)),
                    is_favorite=True,
                    last_read_chapter_id=fav.last_read_chapter_id
                )
                result.append(item)
            except AppBaseError:
                # Comic might be marked as favorite but deleted from local library
                pass
                
        return result
