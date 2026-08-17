from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Any

class BaseResponse(BaseModel):
    model_config = ConfigDict(extra="ignore", coerce_numbers_to_str=True)

class ComicDetail(BaseResponse):
    id: Any
    name: Optional[str] = ""
    cover: Optional[str] = ""
    aspectRatio: Optional[float] = 0.0
    comicUpdateTime: Optional[str] = ""
    tags: List[str] = Field(default_factory=list)
    desc: Optional[str] = ""
    trace: Optional[str] = ""
    collect_status: Optional[int] = 0
    progress_id: Optional[int] = 0
    chapter_subscribe_status: Optional[int] = 0
    eighteen_pop_status: Optional[int] = 0

class ChapterInfo(BaseResponse):
    chapter_id: Any
    chapter_name: Optional[str] = ""
    chapter_cover: Optional[str] = ""
    create_time: Optional[str] = ""
    is_checked: Optional[int] = 0
    is_new_chapter: Optional[int] = 0
    showVipIcon: Optional[bool] = False

class ChapterList(BaseResponse):
    chapters: List[ChapterInfo] = Field(default_factory=list)

class ChapterImage(BaseResponse):
    url: str
    height: int = 0
    width: int = 0
    action: Optional[str] = None

class ChapterReadData(BaseResponse):
    imgs: List[ChapterImage] = Field(default_factory=list)

class SearchModuleItem(BaseResponse):
    id: str
    name: str
    cover: str
    tags: List[str] = Field(default_factory=list)
    desc: str = ""

class SearchResultItem(BaseResponse):
    module_item: SearchModuleItem
