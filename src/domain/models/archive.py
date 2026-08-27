from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from enum import Enum
from datetime import datetime

class TaskStatus(str, Enum):
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ChapterTask(BaseModel):
    chapter_id: str
    title: str
    status: TaskStatus = TaskStatus.QUEUED
    total_pages: int = 0
    downloaded_pages: int = 0
    error_message: Optional[str] = None

class DownloadTask(BaseModel):
    task_id: str  # Format: "provider_id::comic_id"
    provider_id: str
    comic_id: str
    comic_title: str = ""
    cover_url: str = ""
    status: TaskStatus = TaskStatus.QUEUED
    chapters: Dict[str, ChapterTask] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    error_message: Optional[str] = None
    
    @property
    def total_chapters(self) -> int:
        return len(self.chapters)
        
    @property
    def completed_chapters(self) -> int:
        return sum(1 for ch in self.chapters.values() if ch.status == TaskStatus.COMPLETED)

class LibraryComic(BaseModel):
    provider_id: str
    comic_id: str
    title: str
    author: Optional[str] = None
    tags: List[str]
    description: str
    cover_url: str
    local_path: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
