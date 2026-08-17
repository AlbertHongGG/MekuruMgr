from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Dict
from enum import Enum
from datetime import datetime

class PageImage(BaseModel):
    url: str
    width: int = 0
    height: int = 0
    order: int = 0

class Chapter(BaseModel):
    id: str
    title: str
    order: float = 0.0
    cover_url: str = ""
    is_vip: bool = False
    publish_time: str = ""

class Comic(BaseModel):
    id: str
    title: str
    cover_url: str
    author: str = ""
    description: str = ""
    tags: List[str] = Field(default_factory=list)
    update_status: str = ""
    model_config = ConfigDict(extra="ignore")

class DownloadStatus(str, Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"

class ArchivedChapter(BaseModel):
    chapter_id: str
    title: str
    page_count: int = 0
    local_path: str = ""
    status: DownloadStatus = DownloadStatus.PENDING

class ArchivedComic(BaseModel):
    provider_id: str
    comic_id: str
    title: str
    tags: List[str]
    description: str
    cover_url: str
    local_path: str
    chapters: Dict[str, ArchivedChapter] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

# --- Library (Read-Only) Models ---

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
