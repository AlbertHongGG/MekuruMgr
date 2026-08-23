from typing import Any, Generic, TypeVar, Optional, List, Dict
from pydantic import BaseModel

T = TypeVar('T')

class CopymangaResponse(BaseModel, Generic[T]):
    code: int
    message: str
    results: Optional[T] = None

class Author(BaseModel):
    name: str
    alias: Optional[str] = None
    path_word: str

class Theme(BaseModel):
    name: str
    path_word: str

class ComicItem(BaseModel):
    name: str
    alias: Optional[str] = None
    path_word: str
    cover: str
    ban: Optional[int] = 0
    author: List[Author] = []
    popular: Optional[int] = 0

class ExploreResult(BaseModel):
    list: List[ComicItem] = []
    total: int = 0
    limit: int = 0
    offset: int = 0

class SearchResult(ExploreResult):
    pass

class ComicDetailItem(BaseModel):
    name: str
    alias: Optional[str] = None
    path_word: str
    cover: str
    author: List[Author] = []
    theme: List[Theme] = []
    brief: Optional[str] = None
    datetime_updated: Optional[str] = None
    status: Optional[Any] = None

class DetailResult(BaseModel):
    comic: ComicDetailItem

class ChapterItem(BaseModel):
    uuid: str
    name: str
    size: Optional[int] = None
    datetime_created: Optional[str] = None

class ChapterListResult(BaseModel):
    list: List[ChapterItem] = []
    total: int = 0

class ImageItem(BaseModel):
    url: str

class ChapterImageInner(BaseModel):
    contents: List[ImageItem] = []
    words: List[int] = []

class ChapterImageResult(BaseModel):
    chapter: Optional[ChapterImageInner] = None
