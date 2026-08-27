from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from .comic import ComicDetail, Chapter, ComicInfo

class LocalComicItem(ComicInfo):
    """Lightweight projection for library listings."""
    completed_chapters_count: int = 0

class LocalChapterItem(Chapter):
    """Chapter info in local library."""
    page_count: int = 0

class LocalComic(ComicDetail):
    """Represents a comic that has been tracked/downloaded into the local library."""
    local_path: str = ""
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class LocalChapterImages(BaseModel):
    """Complete image URLs for a specific chapter."""
    provider_id: str
    comic_id: str
    chapter_id: str
    title: str
    images: List[str]
