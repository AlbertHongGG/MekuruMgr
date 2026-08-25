import logging
from typing import List, Optional, Tuple, Any

from src.core.provider import BaseComicProvider
from src.domain.models.comic import ComicSearchResult, ComicDetail, Chapter, ComicExploreResult, PageImage
from src.domain.exceptions import ApiLogicError
from .http_client import ManwaHttpClient
from .models.api_models import ManwaListResponse, ManwaDetailData, ManwaPicListData

logger = logging.getLogger(__name__)

class ManwaProvider(BaseComicProvider):
    @property
    def provider_id(self) -> str:
        return "manwa"
        
    @property
    def provider_name(self) -> str:
        return "Manwa"

    def __init__(self):
        super().__init__()
        self.client = ManwaHttpClient()
        
    def _map_search_result(self, items) -> List[ComicSearchResult]:
        results = []
        for item in items:
            cover = item.picx if item.picx else item.pic
            results.append(ComicSearchResult(
                id=str(item.id),
                provider_id=self.provider_id,
                title=item.name,
                cover_url=cover,
                author=item.author
            ))
        return results

    def search_comics(self, keyword: str, page: int = 1, page_size: int = 30) -> List[ComicSearchResult]:
        params = {'k': keyword, 'page': page}
        data = self.client.get('/api/search/index', params=params)
        
        parsed = ManwaListResponse.model_validate(data)
        return self._map_search_result(parsed.list)

    def explore_comics(self, page: int = 1, page_size: int = 30) -> List[ComicExploreResult]:
        params = {
            'gender': 2, 'tag': '', 'area': 0, 'end': 0,
            'has_full': 0, 'level': 0, 'st': 0, 'page': page, 'orderBy': 0
        }
        data = self.client.get('/api/classes/index', params=params)
        parsed = ManwaListResponse.model_validate(data)
        
        results = []
        for item in parsed.list:
            cover = item.picx if item.picx else item.pic
            results.append(ComicExploreResult(
                id=str(item.id),
                provider_id=self.provider_id,
                title=item.name,
                cover_url=cover,
                tags=[]
            ))
        return results

    def get_comic_detail(self, comic_id: str) -> ComicDetail:
        params = {'id': comic_id}
        data = self.client.get('/api/detail/index', params=params)
        
        parsed = ManwaDetailData.model_validate(data)
        
        author = ", ".join(parsed.author) if parsed.author else "Unknown"
        tags = [t.name for t in parsed.tags]
        
        return ComicDetail(
            id=str(parsed.id),
            provider_id=self.provider_id,
            title=parsed.name,
            cover_url=parsed.picx,
            author=author,
            description=parsed.text,
            update_status=parsed.state,
            tags=tags
        )

    def get_chapter_list(self, comic_id: str) -> List[Chapter]:
        params = {'id': comic_id}
        data = self.client.get('/api/detail/index', params=params)
        
        parsed = ManwaDetailData.model_validate(data)
        
        chapters = []
        for ch in parsed.chapter_list:
            chapters.append(Chapter(
                id=str(ch.id),
                provider_id=self.provider_id,
                comic_id=comic_id,
                title=ch.name,
                order=ch.sort if ch.sort is not None else 0,
                publish_time=ch.addtime
            ))
            
        return chapters

    def get_chapter_images(self, comic_id: str, chapter_id: str):
        params = {'id': chapter_id, 'img_host': 0}
        data = self.client.get('/api/chapters/index', params=params)
        
        parsed = ManwaPicListData.model_validate(data)
        images = []
        for i, pic in enumerate(parsed.piclist):
            images.append(PageImage(
                id=str(i),
                url=pic.pic,
                order=i
            ))
        return images

    async def download_image(self, client: Any, url: str) -> Tuple[bytes, str]:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-A315G) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36 mwa-1.1.26+1',
            'Referer': 'http://mseeowpm1.xyz',
        }
        response = await client.get(url, headers=headers, timeout=30.0)
        response.raise_for_status()
        
        # Decrypt image
        try:
            from .crypto import ManwaCrypto
            decrypted_bytes = ManwaCrypto.decrypt_image(response.content)
            
            # Auto detect content type from magic number since encrypted payload usually gives octet-stream
            content_type = response.headers.get('content-type', '')
            if decrypted_bytes.startswith(b'RIFF') and b'WEBP' in decrypted_bytes[:16]:
                content_type = 'image/webp'
                
            return decrypted_bytes, content_type
        except Exception as e:
            logger.error(f"Failed to decrypt Manwa image {url}: {e}")
            # Fallback to returning raw bytes if decryption fails
            return response.content, response.headers.get('content-type', '')

from src.core.registry import registry
registry.register(ManwaProvider)
