from typing import Dict, Any, List
import logging

from src.domain.exceptions import ApiLogicError
from .http_client import WebtoonHttpClient
from .config import DEFAULT_PARAMS
from .models.responses import (
    WebtoonSearchResult,
    WebtoonTitleHomeResult,
    WebtoonEpisodeListResult,
    WebtoonEpisodeInfoResult
)

logger = logging.getLogger(__name__)

class WebtoonApiClient:
    def __init__(self):
        self.http = WebtoonHttpClient()

    def _extract_result(self, raw_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract the 'result' object from Webtoon's standard response format.
        """
        message = raw_json.get("message", {})
        code = message.get("code")
        
        # Webtoon API puts error codes directly in the message dict sometimes
        if code and code not in (200, 0):
            err_msg = message.get("message", "Unknown Webtoon API Error")
            raise ApiLogicError(f"Webtoon API Error: {err_msg}", code)
            
        result = message.get("result")
        if result is None:
            # Fallback for APIs that might return directly
            return message
        return result

    def search_all_v2(self, query: str, start_index: int = 1, page_size: int = 30) -> WebtoonSearchResult:
        params = DEFAULT_PARAMS.copy()
        params.update({
            "query": query,
            "startIndex": start_index,
            "pageSize": page_size,
            "v": "1"
        })
        res = self.http.get("/lineWebtoon/webtoon/searchAllV2", params)
        result_data = self._extract_result(res)
        return WebtoonSearchResult(**result_data)

    def title_home_main_v3(self, title_no: int) -> WebtoonTitleHomeResult:
        params = DEFAULT_PARAMS.copy()
        params.update({
            "titleNo": title_no,
            "v": "1"
        })
        res = self.http.get("/lineWebtoon/webtoon/titleHomeMainV3", params)
        result_data = self._extract_result(res)
        return WebtoonTitleHomeResult(**result_data)

    def title_home_episode_list_v3(self, title_no: int, offset: int = 0, page_size: int = 30) -> WebtoonEpisodeListResult:
        params = DEFAULT_PARAMS.copy()
        params.update({
            "titleNo": title_no,
            "offset": offset,
            "pageSize": page_size,
            "ordering": "OLDEST",
            "v": "1"
        })
        res = self.http.get("/lineWebtoon/webtoon/titleHomeEpisodeListV3", params)
        result_data = self._extract_result(res)
        return WebtoonEpisodeListResult(**result_data)

    def episode_info_with_login(self, title_no: int, episode_no: int) -> WebtoonEpisodeInfoResult:
        params = DEFAULT_PARAMS.copy()
        params.update({
            "titleNo": title_no,
            "episodeNo": episode_no,
            "priorityViewingType": "IMAGE",
            "v": "4"
        })
        res = self.http.get("/lineWebtoon/webtoon/episodeInfoWithLogin.json", params)
        result_data = self._extract_result(res)
        return WebtoonEpisodeInfoResult(**result_data)
