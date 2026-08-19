from typing import List
from src.core.provider import BaseComicProvider
from src.domain.models import ComicSearchResult, ComicDetail, Chapter, PageImage
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
        return f"https://webtoon-phinf.pstatic.net{uri}"

    def get_comic_detail(self, comic_id: str) -> ComicDetail:
        title_no = int(comic_id)
        dto = self.api.title_home_main_v3(title_no)
        
        authors = [a.authorName for a in dto.title.authorList]
        author_str = ", ".join(authors) if authors else None
        
        # Parse tags if available
        tags = []
        if dto.tag and dto.tag.tagList:
            tags = [tag.text for tag in dto.tag.tagList]
        
        return ComicDetail(
            id=comic_id,
            provider_id=self.provider_id,
            title=dto.title.title,
            cover_url=self._get_full_image_url(dto.title.posterThumbnailUrl),
            author=author_str,
            description=dto.title.synopsis,
            tags=tags
        )

    def get_chapter_list(self, comic_id: str) -> List[Chapter]:
        title_no = int(comic_id)
        
        dto = self.api.title_home_episode_list_v3(title_no, offset=0, page_size=30)
        
        chapters = []
        for ep in dto.episodeList:
            chapters.append(Chapter(
                id=str(ep.episodeNo),
                title=ep.episodeTitle
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
                provider_id=self.provider_id
            ))
            
        return comics

    def explore_comics(self, page: int = 1, page_size: int = 30) -> List[ComicSearchResult]:
        return []

registry.register(WebtoonProvider)
