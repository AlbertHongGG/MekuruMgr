import json
import logging
import threading
from pathlib import Path
from typing import Dict, Optional, List
from pydantic import TypeAdapter

from src.domain.models import ArchivedComic
from src.storage.interface import IStorage

logger = logging.getLogger(__name__)

class LocalJsonStorage(IStorage):
    """
    Thread-safe storage manager for the local comic library.
    It handles reading and atomic writing to a central library.json file.
    """
    def __init__(self, data_dir: str = "data"):
        self._data_dir = Path(data_dir)
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self._data_dir / "library.json"
        self._lock = threading.RLock()
        self._cache: Dict[str, ArchivedComic] = {}
        self._load_db()

    @property
    def data_dir(self) -> Path:
        return self._data_dir

    def _load_db(self):
        with self._lock:
            if not self.db_path.exists():
                self._cache = {}
                return
            
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                ta = TypeAdapter(Dict[str, ArchivedComic])
                self._cache = ta.validate_python(data)
                logger.info(f"Loaded [cyan]{len(self._cache)}[/] comics from library DB")
            except Exception as e:
                logger.error(f"[red]Failed to load library DB: {e}[/]")
                self._cache = {}

    def _save_db(self):
        with self._lock:
            try:
                data = {k: v.model_dump(mode='json') for k, v in self._cache.items()}
                temp_path = self.db_path.with_suffix('.tmp')
                with open(temp_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                temp_path.replace(self.db_path)
            except Exception as e:
                logger.error(f"[red]Failed to save library DB: {e}[/]")
                raise

    def get_comic(self, provider_id: str, comic_id: str) -> Optional[ArchivedComic]:
        key = f"{provider_id}::{comic_id}"
        with self._lock:
            return self._cache.get(key)

    def save_comic(self, comic: ArchivedComic):
        key = f"{comic.provider_id}::{comic.comic_id}"
        with self._lock:
            self._cache[key] = comic
            self._save_db()
            logger.debug(f"Saved comic to DB: [green]{comic.title}[/] (ID: {comic.comic_id})")

    def delete_comic(self, provider_id: str, comic_id: str):
        key = f"{provider_id}::{comic_id}"
        with self._lock:
            if key in self._cache:
                del self._cache[key]
            self._save_db()
            logger.info(f"Deleted comic from DB: (Provider: [magenta]{provider_id}[/], ID: {comic_id})")
            
    def list_comics(self) -> List[ArchivedComic]:
        with self._lock:
            return list(self._cache.values())
