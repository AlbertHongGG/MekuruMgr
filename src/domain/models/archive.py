from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from enum import Enum
from datetime import datetime

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
    author: Optional[str] = None
    tags: List[str]
    description: str
    cover_url: str
    local_path: str
    chapters: Dict[str, ArchivedChapter] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class ChapterSyncProgress(BaseModel):
    chapter_id: str
    title: str
    total_pages: int
    downloaded_pages: int
    status: DownloadStatus

class ComicSyncProgress(BaseModel):
    provider_id: str
    comic_id: str
    total_chapters: int
    completed_chapters: int
    failed_chapters: int
    pending_chapters: int
    downloading_chapters: int
    active_chapters: List[ChapterSyncProgress] = Field(default_factory=list)

