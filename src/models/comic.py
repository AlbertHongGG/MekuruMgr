from pydantic import BaseModel, Field
from typing import List, Optional, Any

class BaseResponse(BaseModel):
    code: int
    message: str
    data: Any = None

# --- Detail Page Models ---
class ComicDetailRequest(BaseModel):
    comicId: str

class ComicDetail(BaseModel):
    name: str
    cover: str
    comicUpdateTime: Optional[str] = None
    # Add other fields as necessary based on the real API

class ComicDetailResponse(BaseResponse):
    data: Optional[ComicDetail] = None

# --- Chapter List Models ---
class ChapterListRequest(BaseModel):
    comicId: str
    order: str = "asc"
    page: int = 1
    pageSize: int = 999999

class Chapter(BaseModel):
    chapter_id: int
    chapter_name: str
    chapter_cover: Optional[str] = None
    create_time: Optional[str] = None

class ChapterListData(BaseModel):
    chapters: List[Chapter]

class ChapterListResponse(BaseResponse):
    data: Optional[ChapterListData] = None

# --- Read Comic Models ---
class ReadRequest(BaseModel):
    comicId: str
    chapterId: int

class ComicImage(BaseModel):
    url: str
    height: int
    width: int

class ReadData(BaseModel):
    imgs: List[ComicImage]

class ReadResponse(BaseResponse):
    data: Optional[ReadData] = None
