import structlog
from typing import List

from src.core.http_client import BaseHttpClient
from src.client.api import ComicApiClient
from src.models.requests import ComicDetailRequest, ChapterListRequest, ChapterImagesRequest
from src.models.responses import ComicDetail, ChapterInfo, ChapterImage

logger = structlog.get_logger(__name__)

class ComicManager:
    """
    High-level business logic orchestrator for the Comic platform.
    Abstracts away HTTP and API details.
    """
    def __init__(self):
        self._http_client = BaseHttpClient()
        self._api = ComicApiClient(self._http_client)

    def close(self):
        """Closes the underlying HTTP session."""
        self._http_client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def fetch_comic_detail(self, comic_id: str) -> ComicDetail:
        """Fetch the details of a specific comic."""
        logger.info("fetch_comic_detail", comic_id=comic_id)
        req = ComicDetailRequest(comicId=comic_id)
        return self._api.get_comic_detail(req)

    def fetch_all_chapters(self, comic_id: str) -> List[ChapterInfo]:
        """Fetch all chapters for a specific comic."""
        logger.info("fetch_all_chapters", comic_id=comic_id)
        req = ChapterListRequest(comicId=comic_id, order="asc", page=1, pageSize=999999)
        return self._api.get_chapter_list(req).chapters

    def fetch_chapter_images(self, comic_id: str, chapter_id: str) -> List[ChapterImage]:
        """Fetch all images for a specific chapter."""
        logger.info("fetch_chapter_images", comic_id=comic_id, chapter_id=chapter_id)
        req = ChapterImagesRequest(comicId=comic_id, chapterId=chapter_id)
        return self._api.get_chapter_images(req).imgs
