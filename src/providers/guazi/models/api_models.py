from pydantic import BaseModel, ConfigDict
from typing import List, Optional

class GuaziComicItem(BaseModel):
    id: str
    name: str = "Unknown"
    pic: str = ""
    pic_thumb: str = ""
    author: str = "Unknown"
    model_config = ConfigDict(extra="ignore")

class GuaziComicList(BaseModel):
    list: List[GuaziComicItem] = []
    total: int = 0
    model_config = ConfigDict(extra="ignore")

class GuaziComicDetail(BaseModel):
    id: str
    name: str = "Unknown"
    author: str = "Unknown"
    pic: str = ""
    serialize: str = "Unknown"
    content: str = ""
    category_name: str = ""
    model_config = ConfigDict(extra="ignore")

class GuaziChapterItem(BaseModel):
    id: str
    name: str = "Unknown"
    xid: int = 0
    addtime: str = ""
    model_config = ConfigDict(extra="ignore")

class GuaziImageItem(BaseModel):
    img: str
    model_config = ConfigDict(extra="ignore")

class GuaziImageList(BaseModel):
    images: List[GuaziImageItem] = []
    model_config = ConfigDict(extra="ignore")
