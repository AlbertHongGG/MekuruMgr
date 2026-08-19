import logging
from typing import List, Optional
from datetime import datetime

from src.storage.core.user_interface import IUserStorage
from src.domain.user_models import UserComicInteraction, ReadingProgress
from src.domain.exceptions import AppBaseError

logger = logging.getLogger(__name__)

class UserService:
    def __init__(self, user_storage: IUserStorage):
        self.storage = user_storage

    def get_interaction(self, provider_id: str, comic_id: str) -> UserComicInteraction:
        """Get or create an interaction for a comic."""
        interaction = self.storage.get_interaction(provider_id, comic_id)
        if not interaction:
            interaction = UserComicInteraction(provider_id=provider_id, comic_id=comic_id)
        return interaction

    def toggle_favorite(self, provider_id: str, comic_id: str, title: str = "") -> bool:
        """Toggle favorite status. Returns the new status."""
        interaction = self.get_interaction(provider_id, comic_id)
        if title and title != interaction.title:
            interaction.title = title
            
        interaction.is_favorite = not interaction.is_favorite
        interaction.updated_at = datetime.now()
        self.storage.save_interaction(interaction)
        logger.info(f"Toggled favorite for {comic_id} on {provider_id} to {interaction.is_favorite}")
        return interaction.is_favorite

    def update_reading_progress(self, provider_id: str, comic_id: str, chapter_id: str, page_index: int, title: str = "") -> None:
        """Update the reading progress for a specific chapter."""
        interaction = self.get_interaction(provider_id, comic_id)
        if title and title != interaction.title:
            interaction.title = title
        
        if chapter_id not in interaction.reading_history:
            interaction.reading_history[chapter_id] = ReadingProgress(chapter_id=chapter_id, page_index=page_index)
        else:
            interaction.reading_history[chapter_id].page_index = page_index
            interaction.reading_history[chapter_id].updated_at = datetime.now()
            
        interaction.last_read_chapter_id = chapter_id
        interaction.updated_at = datetime.now()
        self.storage.save_interaction(interaction)
        logger.debug(f"Updated reading progress for {comic_id} / {chapter_id} to page {page_index}")

    def get_all_favorites(self) -> List[UserComicInteraction]:
        """Get all favorite interactions directly without any metadata composition."""
        return [i for i in self.storage.get_all_interactions() if i.is_favorite]
