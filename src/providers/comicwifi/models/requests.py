from pydantic import BaseModel, ConfigDict
from typing import Optional

class BaseRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

class ComicDetailRequest(BaseRequest):
    comicId: str

class ChapterListRequest(BaseRequest):
    comicId: str
    order: str = "asc"
    page: int = 1
    pageSize: int = 999999

class ChapterImagesRequest(BaseRequest):
    comicId: str
    chapterId: str

class ComicSearchRequest(BaseRequest):
    key: str
    page: int = 1
    pageSize: int = 30

class ComicExploreRequest(BaseRequest):
    page: int = 1
    pageSize: int = 30
    labelName: str = "全部,人氣"
    orderType: str = ""
    label: str = ""
