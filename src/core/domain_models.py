from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional

class PageImage(BaseModel):
    """Standardized representation of a single page/image in a chapter."""
    url: str
    width: int = 0
    height: int = 0
    order: int = 0  # To ensure images are displayed in correct order

class Chapter(BaseModel):
    """Standardized representation of a comic chapter."""
    id: str
    title: str
    order: float = 0.0  # Float to allow chapters like 1.5
    cover_url: str = ""
    is_vip: bool = False
    publish_time: str = ""

class Comic(BaseModel):
    """Standardized representation of a comic's details."""
    id: str
    title: str
    cover_url: str
    author: str = ""
    description: str = ""
    tags: List[str] = Field(default_factory=list)
    update_status: str = ""
    
    model_config = ConfigDict(extra="ignore")
