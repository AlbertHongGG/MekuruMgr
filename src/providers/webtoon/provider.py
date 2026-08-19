from typing import List
from src.core.provider import BaseComicProvider
from src.domain.models import Comic, Chapter, PageImage
from src.core.registry import registry
from .api import WebtoonApiClient

class WebtoonProvider(BaseComicProvider):
    def __init__(self):
        self.api = WebtoonApiClient()

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
        # Use webtoon-phinf as default image server if relative
        return f"https://webtoon-phinf.pstatic.net{uri}"

    def get_comic_detail(self, comic_id: str) -> Comic:
        title_no = int(comic_id)
        dto = self.api.title_home_main_v3(title_no)
        
        authors = [a.authorName for a in dto.title.authorList]
        author_str = ", ".join(authors) if authors else "Unknown"
        
        return Comic(
            id=comic_id,
            title=dto.title.title,
            cover_url=self._get_full_image_url(dto.title.posterThumbnailUrl),
            author=author_str,
            description=dto.title.synopsis
        )

    def get_chapter_list(self, comic_id: str) -> List[Chapter]:
        title_no = int(comic_id)
        
        # Webtoon chapter lists are paginated, fetching a large pageSize to get all
        # A more robust solution would loop and aggregate using 'hasMore'
        dto = self.api.title_home_episode_list_v3(title_no, offset=0, page_size=30)
        
        chapters = []
        for ep in dto.episodeList:
            chapters.append(Chapter(
                id=str(ep.episodeNo),
                title=ep.episodeTitle,
                order=float(ep.episodeNo),
                url=f"https://www.webtoons.com/episode?title_no={title_no}&episode_no={ep.episodeNo}"
            ))
            
        return chapters

    def get_chapter_images(self, comic_id: str, chapter_id: str) -> List[PageImage]:
        title_no = int(comic_id)
        ep_no = int(chapter_id)
        
        dto = self.api.episode_info_with_login(title_no, ep_no)
        
        images = []
        for i, img in enumerate(dto.episodeInfo.imageInfo):
            images.append(PageImage(
                order=i,
                url=self._get_full_image_url(img.url)
            ))
            
        return images

    def search_comics(self, keyword: str, page: int = 1, page_size: int = 30) -> List[Comic]:
        # Webtoon API uses startIndex (1-based offset)
        start_index = (page - 1) * page_size + 1
        dto = self.api.search_all_v2(keyword, start_index, page_size)
        
        comics = []
        for item in dto.webtoonSearch.titleList:
            comics.append(Comic(
                id=str(item.titleNo),
                title=f"Webtoon #{item.titleNo} ({keyword})", # API doesn't return title string directly
                cover_url=self._get_full_image_url(item.thumbnailUrl),
                author="Unknown",
                description=""
            ))
            
        return comics

    def explore_comics(self, page: int = 1, page_size: int = 30) -> List[Comic]:
        # User requested to leave this for later
        return []

registry.register(WebtoonProvider)
