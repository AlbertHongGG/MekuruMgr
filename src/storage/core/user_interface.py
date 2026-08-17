from abc import ABC, abstractmethod
from typing import List, Optional
from src.domain.user_models import UserComicInteraction

class IUserStorage(ABC):
    @abstractmethod
    def get_interaction(self, provider_id: str, comic_id: str) -> Optional[UserComicInteraction]:
        """Get the user interaction state for a specific comic."""
        pass
        
    @abstractmethod
    def save_interaction(self, interaction: UserComicInteraction) -> None:
        """Save or update the user interaction state."""
        pass
        
    @abstractmethod
    def get_all_interactions(self) -> List[UserComicInteraction]:
        """Get all user interactions (useful for finding all favorites)."""
        pass
