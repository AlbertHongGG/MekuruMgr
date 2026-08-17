from typing import List
from pydantic import TypeAdapter

from src.providers.comicwifi.http_client import BaseHttpClient
from src.providers.comicwifi.models.requests import ComicDetailRequest, ChapterListRequest, ChapterImagesRequest, ComicSearchRequest, ComicExploreRequest
from src.providers.comicwifi.models.responses import ComicDetail, ChapterList, ChapterReadData, SearchResultItem

class ComicApiClient:
    """
    Strongly-typed API client for the Comic API.
    Transforms business domain requests into HTTP calls and validates responses using Pydantic.
    """
    def __init__(self, http_client: BaseHttpClient):
        self._http = http_client

    def get_comic_detail(self, req: ComicDetailRequest) -> ComicDetail:
        raw_data = self._http.post("/api/comic/detail_page", data=req.model_dump(by_alias=True))
        return ComicDetail.model_validate(raw_data)

    def get_chapter_list(self, req: ChapterListRequest) -> ChapterList:
        raw_data = self._http.post("/api/comic/chapter_list", data=req.model_dump(by_alias=True))
        return ChapterList.model_validate(raw_data)

    def get_chapter_images(self, req: ChapterImagesRequest) -> ChapterReadData:
        # Based on the intercepted event, reading a chapter is usually /api/comic/read
        raw_data = self._http.post("/api/comic/read", data=req.model_dump(by_alias=True))
        return ChapterReadData.model_validate(raw_data)

    def search_comics(self, req: ComicSearchRequest) -> List[SearchResultItem]:
        raw_data = self._http.post("/api/comic/search", data=req.model_dump(by_alias=True))
        ta = TypeAdapter(List[SearchResultItem])
        return ta.validate_python(raw_data)

    def explore_comics(self, req: ComicExploreRequest) -> List[SearchResultItem]:
        raw_data = self._http.post("/api/comic/classify_list", data=req.model_dump(by_alias=True))
        ta = TypeAdapter(List[SearchResultItem])
        return ta.validate_python(raw_data)
