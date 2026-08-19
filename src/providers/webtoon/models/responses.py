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

# --- Explore (Challenge Genre Title List) ---
class WebtoonGenre(BaseModel):
    displayName: str

class WebtoonChallengeTitleItem(BaseModel):
    titleNo: int
    readingTitle: str
    thumbnailImageUrl: str
    representGenre: WebtoonGenre

class WebtoonChallengeGenreTitleListResult(BaseModel):
    challengeTitleList: List[WebtoonChallengeTitleItem]
    
# --- Title Detail ---
class WebtoonTitleDetail(BaseModel):
    titleNo: int
    title: str
    synopsis: str
    posterThumbnailUrl: str
    authorList: List[WebtoonAuthor]

class WebtoonEpisodeMeta(BaseModel):
    totalEpisodeCount: int

class WebtoonTagItem(BaseModel):
    text: str
    type: str

class WebtoonTagInfo(BaseModel):
    tagList: List[WebtoonTagItem]

class WebtoonTitleHomeResult(BaseModel):
    title: WebtoonTitleDetail
    tag: Optional[WebtoonTagInfo] = None
    episodeMeta: WebtoonEpisodeMeta

# --- Episode List ---
class WebtoonEpisodeItem(BaseModel):
    episodeNo: int
    episodeTitle: str
    thumbnailUrl: Optional[str] = None
    exposureYmdt: Optional[int] = None

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
    
