from pydantic import BaseModel
from typing import List

class LocalComicItem(BaseModel):
    """Basic comic info for library listing."""
    provider_id: str
    comic_id: str
    title: str
    cover_url: str
    completed_chapters_count: int

class LocalChapterItem(BaseModel):
    """Basic chapter info within a comic detail."""
    chapter_id: str
    title: str
    page_count: int

class LocalComicDetail(BaseModel):
    """Detailed comic info without chapter list."""
    provider_id: str
    comic_id: str
    title: str
    tags: List[str]
    description: str
    cover_url: str

class LocalChapterImages(BaseModel):
    """Complete image URLs for a specific chapter."""
    provider_id: str
    comic_id: str
    chapter_id: str
    title: str
    images: List[str]

