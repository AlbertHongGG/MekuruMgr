from pydantic import BaseModel, Field
from typing import List, Optional, Any

# Explore & Search Models
class ManwaListItem(BaseModel):
    id: int
    name: str
    pic: str = ""
    picx: str = ""
    author: str = "Unknown"

class ManwaListResponse(BaseModel):
    list: List[ManwaListItem]

# Detail Models
class ManwaTag(BaseModel):
    name: str

class ManwaChapterItem(BaseModel):
    id: int
    name: str
    sort: int = 0
    addtime: str = ""
    # other fields are present but we only need these

class ManwaDetailData(BaseModel):
    id: Any
    name: str
    picx: str = ""
    author: List[str] = []
    text: str = ""
    state: str = ""
    tags: List[ManwaTag] = []
    chapter_list: List[ManwaChapterItem] = []

# Image List Models
class ManwaPicItem(BaseModel):
    pic: str

class ManwaPicListData(BaseModel):
    piclist: List[ManwaPicItem]
