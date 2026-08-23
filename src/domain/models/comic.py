from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional

class PageImage(BaseModel):
    url: str
    width: int = 0
    height: int = 0
    index: int = 0

class Chapter(BaseModel):
    id: str
    title: str
    cover_url: str = ""
    publish_time: str = ""

class ComicSearchResult(BaseModel):
    id: str
    provider_id: str
    title: str = ""
    cover_url: str = ""

class ComicExploreResult(BaseModel):
    id: str
    provider_id: str
    title: str
    cover_url: str
    tags: List[str] = Field(default_factory=list)

class ComicDetail(BaseModel):
    id: str
    provider_id: str
    title: str
    cover_url: str
    author: Optional[str] = None
    description: str
    tags: List[str] = Field(default_factory=list)
    update_status: str = ""
    model_config = ConfigDict(extra="ignore")

