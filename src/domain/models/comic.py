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

class ComicInfo(BaseModel):
    """Unified base model for all comic representations."""
    id: str
    provider_id: str
    title: str
    cover_url: str

class ComicSearchResult(ComicInfo):
    pass

class ComicExploreResult(ComicInfo):
    tags: List[str] = Field(default_factory=list)

class ComicDetail(ComicInfo):
    author: Optional[str] = None
    description: str = ""
    tags: List[str] = Field(default_factory=list)
    update_status: str = ""
    
    model_config = ConfigDict(extra="ignore")
