from pydantic import BaseModel, Field
from typing import Dict, List
from datetime import datetime
from enum import Enum

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
