import structlog
from src.core.http_client import BaseHttpClient
from src.models.comic import (
    ComicDetailRequest, ComicDetail,
    ChapterListRequest, ChapterListData,
    ReadRequest, ReadData
)

logger = structlog.get_logger(__name__)

class ComicApiClient:
    """
    High-level client for interacting with the Comic API.
    Uses BaseHttpClient for underlying network operations and Pydantic models for data validation.
    """
    def __init__(self, http_client: BaseHttpClient):
        self._http = http_client

    def get_comic_detail(self, comic_id: str) -> ComicDetail:
        """Fetch details for a specific comic."""
        req = ComicDetailRequest(comicId=comic_id)
        logger.info("fetching_comic_detail", comic_id=comic_id)
        
        raw_data = self._http.post("/api/comic/detail_page", data=req.model_dump())
        return ComicDetail.model_validate(raw_data)

    def get_chapter_list(self, comic_id: str, page: int = 1, page_size: int = 999999) -> ChapterListData:
        """Fetch the list of chapters for a specific comic."""
        req = ChapterListRequest(comicId=comic_id, page=page, pageSize=page_size)
        logger.info("fetching_chapter_list", comic_id=comic_id, page=page)
        
        raw_data = self._http.post("/api/comic/chapter_list", data=req.model_dump())
        return ChapterListData.model_validate(raw_data)

    def get_chapter_images(self, comic_id: str, chapter_id: int) -> ReadData:
        """Fetch the images for a specific chapter."""
        req = ReadRequest(comicId=comic_id, chapterId=chapterId)
        logger.info("fetching_chapter_images", comic_id=comic_id, chapter_id=chapter_id)
        
        raw_data = self._http.post("/api/comic/read", data=req.model_dump())
        return ReadData.model_validate(raw_data)
