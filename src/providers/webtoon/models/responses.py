from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict

# --- Shared ---
class WebtoonAuthor(BaseModel):
    authorName: str

# --- Search ---
class WebtoonTitle(BaseModel):
    titleNo: int
    thumbnailUrl: str
    
class WebtoonSearchSection(BaseModel):
    titleList: List[WebtoonTitle]
    hasMore: bool

class WebtoonSearchResult(BaseModel):
    webtoonSearch: WebtoonSearchSection

# --- Title Detail ---
class WebtoonTitleDetail(BaseModel):
    titleNo: int
    title: str
    synopsis: str
    posterThumbnailUrl: str
    authorList: List[WebtoonAuthor]

class WebtoonEpisodeMeta(BaseModel):
    totalEpisodeCount: int

class WebtoonTitleHomeResult(BaseModel):
    title: WebtoonTitleDetail
    episodeMeta: WebtoonEpisodeMeta

# --- Episode List ---
class WebtoonEpisodeItem(BaseModel):
    episodeNo: int
    episodeTitle: str
    thumbnailUrl: Optional[str] = None
    # We can add more fields if needed, like readable status

class WebtoonEpisodeListResult(BaseModel):
    episodeList: List[WebtoonEpisodeItem]
    hasMore: Optional[bool] = False

# --- Episode Info (Images) ---
class WebtoonImageInfo(BaseModel):
    url: str

class WebtoonEpisodeInfo(BaseModel):
    imageInfo: List[WebtoonImageInfo]

class WebtoonEpisodeInfoResult(BaseModel):
    episodeInfo: WebtoonEpisodeInfo
    
