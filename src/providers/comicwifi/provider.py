from typing import List, Any
import logging

from src.core.provider import BaseComicProvider
from src.domain.models import ComicSearchResult, ComicDetail, Chapter, PageImage, ComicExploreResult
from src.core.registry import registry
from src.core.constants import BuiltinProvider

from src.providers.comicwifi.http_client import ComicWifiHttpClient
from src.providers.comicwifi.api import ComicApiClient
from src.providers.comicwifi.models.requests import ComicDetailRequest, ChapterListRequest, ChapterImagesRequest, ComicSearchRequest, ComicExploreRequest

logger = logging.getLogger(__name__)

class ComicWifiProvider(BaseComicProvider):
    """
    Adapter for ComicWifi. 
    Translates standard interface calls to ComicWifi specific API calls,
    and maps the specific JSON responses back to standardized models.
    """
    
    def __init__(self, http_client=None):
        self._http = http_client or ComicWifiHttpClient()
        self._api = ComicApiClient(self._http)

    def add_api_hook(self, hook: Any) -> None:
        self._http.add_hook(hook)

    @property
    def provider_id(self) -> str:
        return BuiltinProvider.COMICWIFI

    @property
    def provider_name(self) -> str:
        return "ComicWifi Official"

    def get_comic_detail(self, comic_id: str) -> ComicDetail:
        raw_detail = self._api.get_comic_detail(ComicDetailRequest(comicId=comic_id))
        
        # Mapping to Standard Domain Model
        return ComicDetail(
            id=str(raw_detail.id),
            provider_id=self.provider_id,
            title=raw_detail.name or "Unknown Title",
            cover_url=raw_detail.cover or "",
            description=raw_detail.desc or "",
            tags=raw_detail.tags or [],
            update_status=raw_detail.trace or ""
        )

    def get_chapter_list(self, comic_id: str) -> List[Chapter]:
        raw_list = self._api.get_chapter_list(ChapterListRequest(comicId=comic_id))
        
        # Mapping
        chapters = []
        for idx, ch in enumerate(raw_list.chapters):
            chapters.append(Chapter(
                id=str(ch.chapter_id),
                title=ch.chapter_name or f"Chapter {idx+1}",
                cover_url=ch.chapter_cover or "",
                publish_time=ch.create_time or ""
            ))
        return chapters

    def get_chapter_images(self, comic_id: str, chapter_id: str) -> List[PageImage]:
        raw_images = self._api.get_chapter_images(ChapterImagesRequest(comicId=comic_id, chapterId=chapter_id))
        
        # Mapping
        pages = []
        for idx, img in enumerate(raw_images.imgs):
            pages.append(PageImage(
                url=img.url,
                width=img.width,
                height=img.height,
                index=idx
            ))
        return pages

    def search_comics(self, keyword: str, page: int = 1, page_size: int = 30) -> List[ComicSearchResult]:
        try:
            req = ComicSearchRequest(key=keyword, page=page, pageSize=page_size)
            items = self._api.search_comics(req)
            return [
                ComicSearchResult(
                    id=item.module_item.id,
                    provider_id=self.provider_id,
                    title=item.module_item.name,
                    cover_url=item.module_item.cover
                )
                for item in items
            ]
        except Exception as e:
            from src.domain.exceptions import ApiLogicError
            raise ApiLogicError(f"Failed to search comics: {str(e)}")

    def explore_comics(self, page: int = 1, page_size: int = 30) -> List[ComicExploreResult]:
        try:
            from src.providers.comicwifi.models.requests import ComicExploreRequest
            from src.domain.exceptions import ApiLogicError
            req = ComicExploreRequest(page=page, pageSize=page_size)
            items = self._api.explore_comics(req)
            return [
                ComicExploreResult(
                    id=item.module_item.id,
                    provider_id=self.provider_id,
                    title=item.module_item.name,
                    cover_url=item.module_item.cover,
                    tags=item.module_item.tags or []
                )
                for item in items
            ]
        except Exception as e:
            raise ApiLogicError(f"Failed to explore comics: {str(e)}")

# Register this provider automatically when the module is imported
registry.register(ComicWifiProvider)
