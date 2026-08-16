from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional

class BaseResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

class ComicDetail(BaseResponse):
    id: str
    name: str
    cover: str
    aspectRatio: float = 0.0
    comicUpdateTime: str = ""
    tags: List[str] = Field(default_factory=list)
    desc: str = ""
    trace: str = ""
    collect_status: int = 0
    progress_id: int = 0
    chapter_subscribe_status: int = 0
    eighteen_pop_status: int = 0

class ChapterInfo(BaseResponse):
    chapter_id: int
    chapter_name: str
    chapter_cover: str = ""
    create_time: str = ""
    is_checked: int = 0
    is_new_chapter: int = 0
    showVipIcon: bool = False

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
