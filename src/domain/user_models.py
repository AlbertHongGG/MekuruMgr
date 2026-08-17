from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime

class ReadingProgress(BaseModel):
    chapter_id: str
    page_index: int = 0
    updated_at: datetime = Field(default_factory=datetime.now)

class UserComicInteraction(BaseModel):
    provider_id: str
    comic_id: str
    is_favorite: bool = False
    reading_history: Dict[str, ReadingProgress] = Field(default_factory=dict) # chapter_id -> progress
    last_read_chapter_id: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.now)

class UserProfile(BaseModel):
    # Key format: "{provider_id}::{comic_id}"
    interactions: Dict[str, UserComicInteraction] = Field(default_factory=dict)

# --- Read Models (Projection) ---
class UserLibraryItem(BaseModel):
    """Composed read-model containing both User State and Archive Metadata"""
    provider_id: str
    comic_id: str
    title: str
    cover_url: str
    completed_chapters_count: int
    is_favorite: bool
    last_read_chapter_id: Optional[str] = None
