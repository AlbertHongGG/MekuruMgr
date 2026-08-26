from typing import List, Any
from src.core.provider import BaseComicProvider
from src.domain.models import ComicSearchResult, ComicDetail, Chapter, PageImage, ComicExploreResult
from src.core.registry import registry
from .api import WebtoonApiClient

class WebtoonProvider(BaseComicProvider):
    def __init__(self, api_client=None):
        self.api = api_client or WebtoonApiClient()

    def add_api_hook(self, hook: Any) -> None:
        self.api.http.add_hook(hook)

    @property
    def provider_id(self) -> str:
        return "webtoon"

    @property
    def provider_name(self) -> str:
        return "Webtoon"

    def _get_full_image_url(self, uri: str) -> str:
        """
        Convert relative Webtoon thumbnail URIs to absolute URLs.
        """
        if not uri:
            return ""
        if uri.startswith("http"):
            return uri
        return f"https://webtoon-phinf.pstatic.net{uri}"

    def get_comic_detail(self, comic_id: str) -> ComicDetail:
        title_no = int(comic_id)
        dto = self.api.title_home_main_v3(title_no)
        
        authors = [a.authorName for a in dto.title.authorList]
        author_str = ", ".join(authors) if authors else None
        
        # Parse tags and status if available
        tags = []
        status = ""
        if dto.tag and dto.tag.tagList:
            for tag in dto.tag.tagList:
                if tag.type and "STATUS" in tag.type.upper():
                    status = tag.text
                else:
                    tags.append(tag.text)
        
        return ComicDetail(
            id=comic_id,
            provider_id=self.provider_id,
            title=dto.title.title,
            cover_url=self._get_full_image_url(dto.title.posterThumbnailUrl),
            author=author_str,
            description=dto.title.synopsis,
            tags=tags,
            update_status=status
        )

    def get_chapter_list(self, comic_id: str) -> List[Chapter]:
        title_no = int(comic_id)
        
        dto = self.api.title_home_episode_list_v3(title_no, offset=0, page_size=30)
        
        from datetime import datetime
        chapters = []
        for ep in dto.episodeList:
            pub_time = ""
            if ep.exposureYmdt:
                # convert ms timestamp to YYYY-MM-DD HH:MM:SS
                pub_time = datetime.fromtimestamp(ep.exposureYmdt / 1000.0).strftime('%Y-%m-%d %H:%M:%S')
                
            chapters.append(Chapter(
                id=str(ep.episodeNo),
                title=ep.episodeTitle,
                publish_time=pub_time
            ))
            
        return chapters

    def get_chapter_images(self, comic_id: str, chapter_id: str) -> List[PageImage]:
        title_no = int(comic_id)
        ep_no = int(chapter_id)
        
        dto = self.api.episode_info_with_login(title_no, ep_no)
        
        images = []
        for idx, img in enumerate(dto.episodeInfo.imageInfo):
            images.append(PageImage(
                url=self._get_full_image_url(img.url),
                index=idx
            ))
            
        return images

    def search_comics(self, keyword: str, page: int = 1, page_size: int = 30) -> List[ComicSearchResult]:
        start_index = (page - 1) * page_size + 1
        dto = self.api.search_all_v2(keyword, start_index, page_size)
        
        comics = []
        for item in dto.webtoonSearch.titleList:
            comics.append(ComicSearchResult(
                id=str(item.titleNo),
                provider_id=self.provider_id,
                title="..."
            ))
            
        return comics

    def explore_comics(self, page: int = 1, page_size: int = 20) -> List[ComicExploreResult]:
        # Webtoon explore uses 0-based startIndex
        start_index = (page - 1) * page_size
        dto = self.api.challenge_genre_title_list_v1(start_index=start_index, page_size=page_size)
        
        comics = []
        for item in dto.challengeTitleList:
            comics.append(ComicExploreResult(
                id=str(item.titleNo),
                provider_id=self.provider_id,
                title=item.readingTitle,
                cover_url=self._get_full_image_url(item.thumbnailImageUrl),
                tags=[item.representGenre.displayName] if item.representGenre else []
            ))
            
        return comics

    async def download_image(self, client: Any, url: str) -> tuple[bytes, str]:
        headers = {
            "Referer": "https://www.webtoons.com/",
            "User-Agent": "nApps (Android 9; 22081212C; linewebtoon; 3.9.9)"
        }
        response = await client.get(url, headers=headers, timeout=30.0)
        response.raise_for_status()
        content_type = response.headers.get('content-type', '')
        return response.content, content_type

registry.register(WebtoonProvider)
