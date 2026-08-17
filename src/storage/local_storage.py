import json
import logging
import threading
import aiofiles
import mimetypes
import shutil
from pathlib import Path
from typing import Dict, Optional, List, Any
from pydantic import TypeAdapter

from src.domain.models import ArchivedComic
from src.storage.interface import IArchiveStorage

logger = logging.getLogger(__name__)

class LocalJsonStorage(IArchiveStorage):
    """
    Local JSON + File System implementation of IArchiveStorage.
    Completely encapsulates all path, mkdir, glob, and temporary file logic.
    """
    def __init__(self, db_path: str = "data/library.json"):
        self.db_path = Path(db_path)
        self.data_dir = self.db_path.parent
        self._lock = threading.RLock()
        self._cache: Dict[str, ArchivedComic] = {}
        self._load_db()

    # --- Private Metadata Helpers ---
    def _load_db(self):
        with self._lock:
            if not self.db_path.exists():
                return
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    data = json.loads(f.read())
                    
                ta = TypeAdapter(Dict[str, ArchivedComic])
                self._cache = ta.validate_python(data)
                logger.info(f"Loaded [cyan]{len(self._cache)}[/] comics from JSON DB")
            except Exception as e:
                logger.error(f"[red]Failed to load library DB: {e}[/]")
                self._cache = {}

    def _save_db(self):
        with self._lock:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            # Atomic JSON write
            temp_path = self.db_path.with_suffix('.tmp')
            try:
                with open(temp_path, 'w', encoding='utf-8') as f:
                    data = {k: v.model_dump(mode='json') for k, v in self._cache.items()}
                    json.dump(data, f, ensure_ascii=False, indent=2)
                temp_path.replace(self.db_path)
            except Exception as e:
                logger.error(f"[red]Failed to save library DB: {e}[/]")
                raise

    # --- IArchiveStorage: Metadata ---
    def get_comic(self, provider_id: str, comic_id: str) -> Optional[ArchivedComic]:
        key = f"{provider_id}::{comic_id}"
        with self._lock:
            return self._cache.get(key)

    def save_comic(self, comic: ArchivedComic) -> None:
        key = f"{comic.provider_id}::{comic.comic_id}"
        with self._lock:
            self._cache[key] = comic
            self._save_db()
            logger.debug(f"Saved comic to DB: [green]{comic.title}[/] (ID: {comic.comic_id})")

    def delete_comic(self, provider_id: str, comic_id: str) -> None:
        key = f"{provider_id}::{comic_id}"
        with self._lock:
            if key in self._cache:
                del self._cache[key]
            self._save_db()
            
        target_dir = self.data_dir / provider_id / comic_id
        if target_dir.exists():
            shutil.rmtree(target_dir, ignore_errors=True)
            
        logger.info(f"Deleted comic and media from DB: (Provider: [magenta]{provider_id}[/], ID: {comic_id})")
            
    def list_comics(self) -> List[ArchivedComic]:
        with self._lock:
            return list(self._cache.values())

    # --- IArchiveStorage: Media ---
    async def save_image(self, provider_id: str, comic_id: str, chapter_id: str, index: int, content: bytes, content_type: str) -> str:
        comic_dir = self.data_dir / provider_id / comic_id
        
        if chapter_id == 'cover':
            dest_dir = comic_dir
            base_name = "cover"
        else:
            dest_dir = comic_dir / chapter_id
            base_name = f"{index:03d}"
            
        ext = mimetypes.guess_extension(content_type) or '.jpg'
        dest_path = dest_dir / f"{base_name}{ext}"
        tmp_path = dest_path.with_suffix(f"{ext}.tmp")
        
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        # Atomic Binary Write
        async with aiofiles.open(tmp_path, 'wb') as f:
            await f.write(content)
        
        # Rename only when fully written and closed
        tmp_path.replace(dest_path)
            
        return dest_path.name

    def get_chapter_images(self, provider_id: str, comic_id: str, chapter_id: str) -> List[str]:
        chapter_dir = self.data_dir / provider_id / comic_id / chapter_id
        if not chapter_dir.exists():
            return []
            
        # Ignore .tmp files when reading images
        files = [f for f in chapter_dir.iterdir() if f.is_file() and not f.name.endswith('.tmp')]
        files.sort(key=lambda f: f.name)
        return [f"{provider_id}/{comic_id}/{chapter_id}/{f.name}" for f in files]

    def count_downloaded_images(self, provider_id: str, comic_id: str, chapter_id: str) -> int:
        chapter_dir = self.data_dir / provider_id / comic_id / chapter_id
        if not chapter_dir.exists():
            return 0
        return len([f for f in chapter_dir.iterdir() if f.is_file() and not f.name.endswith('.tmp')])

    def check_image_exists(self, provider_id: str, comic_id: str, chapter_id: str, index: int) -> bool:
        chapter_dir = self.data_dir / provider_id / comic_id / chapter_id
        if not chapter_dir.exists():
            return False
            
        base_name = f"{index:03d}"
        existing_files = list(chapter_dir.glob(f"{base_name}.*"))
        
        # Must not be a .tmp file and must be > 0 bytes
        for f in existing_files:
            if not f.name.endswith('.tmp') and f.stat().st_size > 0:
                return True
        return False

    def is_chapter_missing(self, provider_id: str, comic_id: str, chapter_id: str) -> bool:
        chapter_dir = self.data_dir / provider_id / comic_id / chapter_id
        return not chapter_dir.exists()

    def get_image_stream(self, relative_path: str) -> tuple[Any, str]:
        file_path = self.data_dir / relative_path
        if not file_path.exists() or not file_path.is_file():
            from src.domain.exceptions import AppBaseError
            raise AppBaseError(f"Image not found: {relative_path}")
        
        ctype, _ = mimetypes.guess_type(str(file_path))
        if not ctype:
            ctype = "application/octet-stream"
            
        def file_iterator():
            with open(file_path, "rb") as f:
                while chunk := f.read(8192):
                    yield chunk
                    
        return file_iterator(), ctype
