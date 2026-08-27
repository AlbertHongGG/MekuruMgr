from typing import List, Any

from src.core.provider import BaseComicProvider
from src.domain.models import ComicSearchResult, ComicDetail, Chapter, PageImage, ComicExploreResult
from src.core.registry import registry
from .api import CopymangaApiClient

class CopymangaProvider(BaseComicProvider):
    def __init__(self, api_client=None):
        self.api = api_client or CopymangaApiClient()

    def add_api_hook(self, hook: Any) -> None:
        self.api.http_client.add_hook(hook)

    @property
    def provider_id(self) -> str:
        return "copymanga"

    @property
    def aliases(self) -> List[str]:
        return ["copymg"]

    @property
    def provider_name(self) -> str:
        return "Copymanga"

    def get_comic_detail(self, comic_id: str) -> ComicDetail:
        res = self.api.get_comic_detail(path_word=comic_id)
        if not res.results or not res.results.comic:
            raise ValueError(f"Comic detail not found for {comic_id}")
            
        comic = res.results.comic
        
        # Parse authors
        authors = [a.name for a in comic.author] if comic.author else []
        author_str = ", ".join(authors) if authors else None
        
        # Parse tags/themes
        tags = [t.name for t in comic.theme] if comic.theme else []
        
        # Status
        status_str = str(comic.status)
        if isinstance(comic.status, dict) and "display" in comic.status:
            status_str = comic.status["display"]
        elif comic.status == 0:
            status_str = "連載中"
        elif comic.status == 1:
            status_str = "已完結"
        elif comic.status is None:
            status_str = ""

        return ComicDetail(
            id=comic_id,
            provider_id=self.provider_id,
            title=comic.name,
            cover_url=comic.cover,
            author=author_str,
            description=comic.brief or "",
            tags=tags,
            update_status=status_str
        )

    def get_chapter_list(self, comic_id: str) -> List[Chapter]:
        chapters: List[Chapter] = []
        offset = 0
        limit = 100  # Copymanga silently returns empty list if limit is too large (>100)
        
        while True:
            res = self.api.get_chapter_list(path_word=comic_id, limit=limit, offset=offset)
            if not res.results or not res.results.list:
                break
                
            for item in res.results.list:
                chapters.append(Chapter(
                    id=item.uuid,
                    title=item.name,
                    comic_id=comic_id,
                    provider_id=self.provider_id,
                    publish_time=item.datetime_created
                ))
                
            if len(chapters) >= res.results.total:
                break
            
            offset += limit
            
        return chapters

    def get_chapter_images(self, comic_id: str, chapter_id: str) -> List[PageImage]:
        res = self.api.get_chapter_images(path_word=comic_id, chapter_uuid=chapter_id)
        if not res.results or not res.results.chapter or not res.results.chapter.contents:
            return []
            
        images = []
        for idx, img in enumerate(res.results.chapter.contents):
            # Some Copymanga image endpoints also use "words" to descramble but
            # standard viewing might just need the url.
            images.append(PageImage(
                url=img.url,
                index=idx
            ))
            
        return images

    def search_comics(self, keyword: str, page: int = 1, page_size: int = 18) -> List[ComicSearchResult]:
        offset = (page - 1) * page_size
        res = self.api.search_comics(keyword=keyword, limit=page_size, offset=offset)
        
        if not res.results or not res.results.list:
            return []
            
        comics = []
        for item in res.results.list:
            comics.append(ComicSearchResult(
                id=item.path_word,
                provider_id=self.provider_id,
                title=item.name,
                cover_url=item.cover
            ))
            
        return comics

    def explore_comics(self, page: int = 1, page_size: int = 18) -> List[ComicExploreResult]:
        offset = (page - 1) * page_size
        res = self.api.get_explore_comics(limit=page_size, offset=offset)
        
        if not res.results or not res.results.list:
            return []
            
        comics = []
        for item in res.results.list:
            tags = []
            comics.append(ComicExploreResult(
                id=item.path_word,
                provider_id=self.provider_id,
                title=item.name,
                cover_url=item.cover,
                tags=tags
            ))
            
        return comics

    async def download_image(self, client: Any, url: str) -> tuple[bytes, str]:
        # The user mentioned there is no hotlink protection for images.
        headers = {
            "User-Agent": "COPY/3.0.9"
        }
        response = await client.get(url, headers=headers, timeout=30.0)
        response.raise_for_status()
        content_type = response.headers.get('content-type', '')
        return response.content, content_type

# Register the provider
