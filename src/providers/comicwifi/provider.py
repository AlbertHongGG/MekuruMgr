from typing import List
import logging

from src.core.provider import BaseComicProvider
from src.domain.models import Comic, Chapter, PageImage
from src.core.registry import registry
from src.core.constants import BuiltinProvider

from src.providers.comicwifi.http_client import BaseHttpClient
from src.providers.comicwifi.api import ComicApiClient
from src.providers.comicwifi.models.requests import ComicDetailRequest, ChapterListRequest, ChapterImagesRequest, ComicSearchRequest

logger = logging.getLogger(__name__)

class ComicWifiProvider(BaseComicProvider):
    """
    Adapter for ComicWifi. 
    Translates standard interface calls to ComicWifi specific API calls,
    and maps the specific JSON responses back to standardized models.
    """
    
    def __init__(self):
        self._http = BaseHttpClient()
        self._api = ComicApiClient(self._http)

    @property
    def provider_id(self) -> str:
        return BuiltinProvider.COMICWIFI

    @property
    def provider_name(self) -> str:
        return "ComicWifi Official"

    def get_comic_detail(self, comic_id: str) -> Comic:
        # Spammy log removed
        raw_detail = self._api.get_comic_detail(ComicDetailRequest(comicId=comic_id))
        
        # Mapping to Standard Domain Model
        return Comic(
            id=raw_detail.id,
            title=raw_detail.name,
            cover_url=raw_detail.cover,
            description=raw_detail.desc,
            tags=raw_detail.tags,
            update_status=raw_detail.trace
        )

    def get_chapter_list(self, comic_id: str) -> List[Chapter]:
        # Spammy log removed
        raw_list = self._api.get_chapter_list(ChapterListRequest(comicId=comic_id))
        
        # Mapping
        chapters = []
        for idx, ch in enumerate(raw_list.chapters):
            # The API returns chapters in some order, but might not have explicit floats.
            # We use enumerate as a fallback order or try to extract from name if needed.
            # Here we just use the index as order for simplicity, assuming they are ordered.
            chapters.append(Chapter(
                id=str(ch.chapter_id),
                title=ch.chapter_name,
                order=float(idx),
                cover_url=ch.chapter_cover,
                is_vip=ch.showVipIcon,
                publish_time=ch.create_time
            ))
        return chapters

    def get_chapter_images(self, comic_id: str, chapter_id: str) -> List[PageImage]:
        # Spammy log removed
        raw_images = self._api.get_chapter_images(ChapterImagesRequest(comicId=comic_id, chapterId=chapter_id))
        
        # Mapping
        pages = []
        for idx, img in enumerate(raw_images.imgs):
            pages.append(PageImage(
                url=img.url,
                width=img.width,
                height=img.height,
                order=idx
            ))
        return pages

    def search_comics(self, keyword: str, page: int = 1, page_size: int = 30) -> List[Comic]:
        req = ComicSearchRequest(key=keyword, page=page, pageSize=page_size)
        raw_results = self._api.search_comics(req)
        
        # Mapping
        comics = []
        for item in raw_results:
            mod = item.module_item
            comics.append(Comic(
                id=mod.id,
                title=mod.name,
                cover_url=mod.cover,
                description=mod.desc,
                tags=mod.tags
            ))
        return comics

# Register this provider automatically when the module is imported
registry.register(ComicWifiProvider)
