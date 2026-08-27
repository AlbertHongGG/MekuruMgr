from typing import List, Any
import logging
from datetime import datetime

from src.core.provider import BaseComicProvider
from src.domain.models import ComicSearchResult, ComicDetail, Chapter, PageImage, ComicExploreResult
from src.core.registry import registry

from .http_client import GuaziHttpClient
from .crypto import GuaziCrypto
from .models.api_models import GuaziComicList, GuaziComicDetail, GuaziChapterItem, GuaziImageList

logger = logging.getLogger(__name__)

class GuaziProvider(BaseComicProvider):
    def __init__(self, http_client=None):
        self.client = http_client or GuaziHttpClient()

    def add_api_hook(self, hook: Any) -> None:
        self.client.add_hook(hook)

    @property
    def provider_id(self) -> str:
        return "guazi"

    @property
    def provider_name(self) -> str:
        return "Guazi"

    def _convert_timestamp(self, ts: str) -> str:
        try:
            return datetime.fromtimestamp(int(ts)).strftime('%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            return ts

    def get_comic_detail(self, comic_id: str) -> ComicDetail:
        params = {"id": comic_id}
        data = self.client.request("GET", "index.php/api/v2/mcomic/detail", params=params)
        
        parsed = GuaziComicDetail.model_validate(data)
        
        return ComicDetail(
            id=str(parsed.id),
            provider_id=self.provider_id,
            title=parsed.name,
            cover_url=parsed.pic,
            author=parsed.author,
            description=parsed.content,
            update_status=parsed.serialize,
            tags=[parsed.category_name] if parsed.category_name else []
        )

    def get_chapter_list(self, comic_id: str) -> List[Chapter]:
        data_payload = {"id": comic_id, "sort": "asc"}
        data = self.client.request("POST", "index.php/api/v2/mcomic/chapter", data=data_payload)
        
        chapters = []
        if isinstance(data, list):
            for ch in data:
                parsed = GuaziChapterItem.model_validate(ch)
                chapters.append(Chapter(
                    id=str(parsed.id),
                    provider_id=self.provider_id,
                    comic_id=comic_id,
                    title=parsed.name,
                    order=parsed.xid,
                    publish_time=self._convert_timestamp(parsed.addtime)
                ))
        return chapters

    def get_chapter_images(self, comic_id: str, chapter_id: str) -> List[PageImage]:
        params = {"chapter_id": chapter_id}
        data = self.client.request("GET", "index.php/api/v2/mcomic/pics", params=params)
        
        parsed = GuaziImageList.model_validate(data)
        
        images = []
        for idx, img in enumerate(parsed.images):
            if img.img:
                images.append(PageImage(
                    url=img.img,
                    index=idx
                ))
        return images

    def search_comics(self, keyword: str, page: int = 1, page_size: int = 30) -> List[ComicSearchResult]:
        # Encrypt the keyword as Base64 for the API request
        enc_keyword = GuaziCrypto.encrypt(keyword)
        
        data_payload = {"keyword": enc_keyword, "page": page}
        data = self.client.request("POST", "index.php/api/v2/mcomic/search", data=data_payload)
        
        parsed = GuaziComicList.model_validate(data)
        comics = []
        for item in parsed.list:
            comics.append(ComicSearchResult(
                id=str(item.id),
                provider_id=self.provider_id,
                title=item.name,
                cover_url=item.pic or item.pic_thumb
            ))
        return comics

    def explore_comics(self, page: int = 1, page_size: int = 20) -> List[ComicExploreResult]:
        params = {
            "page": page,
            "page_size": page_size,
            "sort": 2
        }
        data = self.client.request("GET", "index.php/api/v2/mcomic/index", params=params)
        
        parsed = GuaziComicList.model_validate(data)
        comics = []
        for item in parsed.list:
            comics.append(ComicExploreResult(
                id=str(item.id),
                provider_id=self.provider_id,
                title=item.name,
                cover_url=item.pic or item.pic_thumb,
                tags=[]
            ))
        return comics

    async def download_image(self, client: Any, url: str) -> tuple[bytes, str]:
        headers = {
            "User-Agent": "okhttp/4.7.2",
            "Referer": "https://api.guaziapp.com"
        }
        response = await client.get(url, headers=headers, timeout=30.0)
        response.raise_for_status()
        content_type = response.headers.get('content-type', '')
        return response.content, content_type


# Legacy compatibility for registry
_temp_instance = GuaziProvider()
_provider_id = _temp_instance.provider_id
_provider_id = str(_provider_id.value) if hasattr(_provider_id, 'value') else str(_provider_id)
registry.register(
    provider_id=_provider_id,
    provider_class=GuaziProvider,
    aliases=_temp_instance.aliases
)

