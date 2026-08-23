from typing import Optional
from .http_client import CopymangaHttpClient
from .models import (
    CopymangaResponse,
    ExploreResult,
    SearchResult,
    DetailResult,
    ChapterListResult,
    ChapterImageResult
)

class CopymangaApiClient:
    def __init__(self):
        self.http_client = CopymangaHttpClient()

    def get_explore_comics(self, limit: int = 18, offset: int = 0) -> CopymangaResponse[ExploreResult]:
        params = {
            "limit": limit,
            "offset": offset,
            "free_type": 1,
            "ordering": "-datetime_updated",
            "theme": "",
            "top": "",
            "platform": 3
        }
        res_json = self.http_client.get("/comics", params=params)
        return CopymangaResponse[ExploreResult].model_validate(res_json)

    def get_comic_detail(self, path_word: str) -> CopymangaResponse[DetailResult]:
        params = {
            "platform": 3
        }
        # The user's curl used /comic2/ for detail
        endpoint = f"/comic2/{path_word}"
        res_json = self.http_client.get(endpoint, params=params)
        return CopymangaResponse[DetailResult].model_validate(res_json)

    def get_chapter_list(self, path_word: str, limit: int = 100, offset: int = 0) -> CopymangaResponse[ChapterListResult]:
        params = {
            "limit": limit,
            "offset": offset,
            "platform": 3
        }
        endpoint = f"/comic/{path_word}/group/default/chapters"
        res_json = self.http_client.get(endpoint, params=params)
        return CopymangaResponse[ChapterListResult].model_validate(res_json)

    def get_chapter_images(self, path_word: str, chapter_uuid: str) -> CopymangaResponse[ChapterImageResult]:
        params = {
            "platform": 3
        }
        endpoint = f"/comic/{path_word}/chapter2/{chapter_uuid}"
        res_json = self.http_client.get(endpoint, params=params)
        return CopymangaResponse[ChapterImageResult].model_validate(res_json)

    def search_comics(self, keyword: str, limit: int = 18, offset: int = 0) -> CopymangaResponse[SearchResult]:
        params = {
            "limit": limit,
            "offset": offset,
            "q_type": "",
            "q": keyword,
            "platform": 3
        }
        res_json = self.http_client.get("/search/comic", params=params)
        return CopymangaResponse[SearchResult].model_validate(res_json)
