import json
import logging
import aiofiles
import mimetypes
import shutil
from pathlib import Path
from typing import Dict, Optional, List, Any
from pydantic import TypeAdapter
from filelock import FileLock

from src.domain.models.archive import LibraryComic, DownloadTask, TaskStatus
from src.storage.core.archive_interface import ILibraryStorage, ITaskStorage, IMediaStorage

logger = logging.getLogger(__name__)

class JsonLibraryStorage(ILibraryStorage):
    def __init__(self, db_path: str = "data/library.json"):
        self.db_path = Path(db_path)
        self.lock_path = self.db_path.with_suffix(".lock")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ta = TypeAdapter(Dict[str, LibraryComic])

    def _read_db(self) -> Dict[str, LibraryComic]:
        if not self.db_path.exists():
            return {}
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return self._ta.validate_python(data)
        except Exception as e:
            logger.error(f"Failed to read library DB: {e}")
            return {}

    def _write_db(self, data: Dict[str, LibraryComic]):
        temp_path = self.db_path.with_suffix('.tmp')
        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                json_data = {k: v.model_dump(mode='json') for k, v in data.items()}
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            temp_path.replace(self.db_path)
        except Exception as e:
            logger.error(f"Failed to save library DB: {e}")
            raise

    def get_comic(self, provider_id: str, comic_id: str) -> Optional[LibraryComic]:
        key = f"{provider_id}::{comic_id}"
        with FileLock(self.lock_path):
            db = self._read_db()
            return db.get(key)

    def save_comic(self, comic: LibraryComic) -> None:
        key = f"{comic.provider_id}::{comic.comic_id}"
        with FileLock(self.lock_path):
            db = self._read_db()
            db[key] = comic
            self._write_db(db)

    def delete_comic(self, provider_id: str, comic_id: str) -> None:
        key = f"{provider_id}::{comic_id}"
        with FileLock(self.lock_path):
            db = self._read_db()
            if key in db:
                del db[key]
                self._write_db(db)

    def list_comics(self) -> List[LibraryComic]:
        with FileLock(self.lock_path):
            db = self._read_db()
            return list(db.values())

    def search_comics(self, keyword: str) -> List[LibraryComic]:
        keyword = keyword.lower()
        results = []
        with FileLock(self.lock_path):
            db = self._read_db()
            for comic in db.values():
                if (keyword in comic.title.lower() or 
                    keyword in comic.description.lower() or 
                    keyword in comic.comic_id.lower() or
                    keyword in comic.provider_id.lower() or
                    any(keyword in tag.lower() for tag in comic.tags)):
                    results.append(comic)
        return results

class JsonTaskStorage(ITaskStorage):
    def __init__(self, db_path: str = "data/tasks.json"):
        self.db_path = Path(db_path)
        self.lock_path = self.db_path.with_suffix(".lock")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ta = TypeAdapter(Dict[str, DownloadTask])

    def _read_db(self) -> Dict[str, DownloadTask]:
        if not self.db_path.exists():
            return {}
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return self._ta.validate_python(data)
        except Exception as e:
            logger.error(f"Failed to read tasks DB: {e}")
            return {}

    def _write_db(self, data: Dict[str, DownloadTask]):
        temp_path = self.db_path.with_suffix('.tmp')
        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                json_data = {k: v.model_dump(mode='json') for k, v in data.items()}
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            temp_path.replace(self.db_path)
        except Exception as e:
            logger.error(f"Failed to save tasks DB: {e}")
            raise

    def get_task(self, task_id: str) -> Optional[DownloadTask]:
        with FileLock(self.lock_path):
            db = self._read_db()
            return db.get(task_id)

    def save_task(self, task: DownloadTask) -> None:
        with FileLock(self.lock_path):
            db = self._read_db()
            db[task.task_id] = task
            self._write_db(db)

    def delete_task(self, task_id: str) -> None:
        with FileLock(self.lock_path):
            db = self._read_db()
            if task_id in db:
                del db[task_id]
                self._write_db(db)

    def list_tasks(self) -> List[DownloadTask]:
        with FileLock(self.lock_path):
            db = self._read_db()
            return list(db.values())

class LocalMediaStorage(IMediaStorage):
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

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
        
        async with aiofiles.open(tmp_path, 'wb') as f:
            await f.write(content)
        
        tmp_path.replace(dest_path)
        return dest_path.name

    def get_chapter_images(self, provider_id: str, comic_id: str, chapter_id: str) -> List[str]:
        chapter_dir = self.data_dir / provider_id / comic_id / chapter_id
        if not chapter_dir.exists():
            return []
            
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

    def delete_media(self, provider_id: str, comic_id: str) -> None:
        target_dir = self.data_dir / provider_id / comic_id
        if target_dir.exists():
            shutil.rmtree(target_dir, ignore_errors=True)
