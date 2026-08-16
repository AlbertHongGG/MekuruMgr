import json
import threading
from pathlib import Path
from typing import Dict, Optional, List
import structlog
from pydantic import TypeAdapter

from src.storage.models import ArchivedComic

logger = structlog.get_logger(__name__)

class LocalLibraryStorage:
    """
    Thread-safe storage manager for the local comic library.
    It handles reading and atomic writing to a central library.json file.
    """
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_dir / "library.json"
        self._lock = threading.RLock()
        self._cache: Dict[str, ArchivedComic] = {}
        self._load_db()

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
                logger.info("library_db_loaded", count=len(self._cache))
            except Exception as e:
                logger.error("failed_to_load_library_db", error=str(e))
                self._cache = {}

    def _save_db(self):
        with self._lock:
            try:
                # Convert dict of Pydantic models to serializable dict
                data = {k: v.model_dump(mode='json') for k, v in self._cache.items()}
                
                # Write to a temporary file first for atomic write (prevent corruption)
                temp_path = self.db_path.with_suffix('.tmp')
                with open(temp_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                # Replace the original file atomically
                temp_path.replace(self.db_path)
            except Exception as e:
                logger.error("failed_to_save_library_db", error=str(e))
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
            logger.info("saved_archived_comic_to_db", comic_id=comic.comic_id, title=comic.title)

    def delete_comic(self, provider_id: str, comic_id: str):
        key = f"{provider_id}::{comic_id}"
        with self._lock:
            if key in self._cache:
                comic = self._cache.pop(key)
                self._save_db()
                logger.info("deleted_archived_comic_from_db", comic_id=comic_id)
            
    def list_comics(self) -> List[ArchivedComic]:
        with self._lock:
            return list(self._cache.values())

# Global singleton
storage = LocalLibraryStorage()
