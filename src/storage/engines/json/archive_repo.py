import json
import logging
import aiofiles
import aiofiles.os
import mimetypes
import shutil
import asyncio
from pathlib import Path
from typing import Dict, Optional, List, Any, Tuple
from pydantic import TypeAdapter

from src.domain.models import LocalComic, DownloadTask, TaskStatus
from src.storage.core.archive_interface import ILibraryStorage, ITaskStorage, IMediaStorage

logger = logging.getLogger(__name__)

class JsonLibraryStorage(ILibraryStorage):
    def __init__(self, db_path: str = "data/library.json"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ta = TypeAdapter(Dict[str, LocalComic])
        self._lock = asyncio.Lock()

    async def _read_db(self) -> Dict[str, LocalComic]:
        if not await asyncio.to_thread(self.db_path.exists):
            return {}
        try:
            async with aiofiles.open(self.db_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                data = json.loads(content)
            return self._ta.validate_python(data)
        except Exception as e:
            logger.error(f"Failed to read library DB: {e}")
            return {}

    async def _write_db(self, data: Dict[str, LocalComic]):
        temp_path = self.db_path.with_suffix('.tmp')
        try:
            json_data = {k: v.model_dump(mode='json') for k, v in data.items()}
            content = json.dumps(json_data, ensure_ascii=False, indent=2)
            
            async with aiofiles.open(temp_path, 'w', encoding='utf-8') as f:
                await f.write(content)
                
            await asyncio.to_thread(temp_path.replace, self.db_path)
        except Exception as e:
            logger.error(f"Failed to save library DB: {e}")
            raise

    async def get_comic(self, provider_id: str, comic_id: str) -> Optional[LocalComic]:
        key = f"{provider_id}::{comic_id}"
        async with self._lock:
            db = await self._read_db()
            return db.get(key)

    async def save_comic(self, comic: LocalComic) -> None:
        key = f"{comic.provider_id}::{comic.id}"
        async with self._lock:
            db = await self._read_db()
            db[key] = comic
            await self._write_db(db)

    async def delete_comic(self, provider_id: str, comic_id: str) -> None:
        key = f"{provider_id}::{comic_id}"
        async with self._lock:
            db = await self._read_db()
            if key in db:
                del db[key]
                await self._write_db(db)

    async def list_comics(self) -> List[LocalComic]:
        async with self._lock:
            db = await self._read_db()
            return list(db.values())

    async def search_comics(self, keyword: str) -> List[LocalComic]:
        keyword = keyword.lower()
        results = []
        async with self._lock:
            db = await self._read_db()
            for comic in db.values():
                if (keyword in comic.title.lower() or 
                    keyword in comic.description.lower() or 
                    keyword in comic.id.lower() or
                    keyword in comic.provider_id.lower() or
                    any(keyword in tag.lower() for tag in comic.tags)):
                    results.append(comic)
        return results

class JsonTaskStorage(ITaskStorage):
    def __init__(self, db_path: str = "data/tasks.json"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ta = TypeAdapter(Dict[str, DownloadTask])
        self._lock = asyncio.Lock()

    async def _read_db(self) -> Dict[str, DownloadTask]:
        if not await asyncio.to_thread(self.db_path.exists):
            return {}
        try:
            async with aiofiles.open(self.db_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                data = json.loads(content)
            return self._ta.validate_python(data)
        except Exception as e:
            logger.error(f"Failed to read tasks DB: {e}")
            return {}

    async def _write_db(self, data: Dict[str, DownloadTask]):
        temp_path = self.db_path.with_suffix('.tmp')
        try:
            json_data = {k: v.model_dump(mode='json') for k, v in data.items()}
            content = json.dumps(json_data, ensure_ascii=False, indent=2)
            
            async with aiofiles.open(temp_path, 'w', encoding='utf-8') as f:
                await f.write(content)
                
            await asyncio.to_thread(temp_path.replace, self.db_path)
        except Exception as e:
            logger.error(f"Failed to save tasks DB: {e}")
            raise

    async def get_task(self, task_id: str) -> Optional[DownloadTask]:
        async with self._lock:
            db = await self._read_db()
            return db.get(task_id)

    async def save_task(self, task: DownloadTask) -> None:
        async with self._lock:
            db = await self._read_db()
            db[task.task_id] = task
            await self._write_db(db)

    async def delete_task(self, task_id: str) -> None:
        async with self._lock:
            db = await self._read_db()
            if task_id in db:
                del db[task_id]
                await self._write_db(db)

    async def list_tasks(self) -> List[DownloadTask]:
        async with self._lock:
            db = await self._read_db()
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
        
        await asyncio.to_thread(dest_dir.mkdir, parents=True, exist_ok=True)
        
        async with aiofiles.open(tmp_path, 'wb') as f:
            await f.write(content)
        
        await asyncio.to_thread(tmp_path.replace, dest_path)
        return dest_path.name

    async def get_chapter_images(self, provider_id: str, comic_id: str, chapter_id: str) -> List[str]:
        chapter_dir = self.data_dir / provider_id / comic_id / chapter_id
        
        def _get():
            if not chapter_dir.exists():
                return []
            files = [f for f in chapter_dir.iterdir() if f.is_file() and not f.name.endswith('.tmp')]
            files.sort(key=lambda f: f.name)
            return [f"{provider_id}/{comic_id}/{chapter_id}/{f.name}" for f in files]
            
        return await asyncio.to_thread(_get)

    async def count_downloaded_images(self, provider_id: str, comic_id: str, chapter_id: str) -> int:
        chapter_dir = self.data_dir / provider_id / comic_id / chapter_id
        
        def _count():
            if not chapter_dir.exists():
                return 0
            return len([f for f in chapter_dir.iterdir() if f.is_file() and not f.name.endswith('.tmp')])
            
        return await asyncio.to_thread(_count)

    async def check_image_exists(self, provider_id: str, comic_id: str, chapter_id: str, index: int) -> bool:
        chapter_dir = self.data_dir / provider_id / comic_id / chapter_id
        
        def _check():
            if not chapter_dir.exists():
                return False
            base_name = f"{index:03d}"
            existing_files = list(chapter_dir.glob(f"{base_name}.*"))
            for f in existing_files:
                if not f.name.endswith('.tmp') and f.stat().st_size > 0:
                    return True
            return False
            
        return await asyncio.to_thread(_check)

    async def is_chapter_missing(self, provider_id: str, comic_id: str, chapter_id: str) -> bool:
        chapter_dir = self.data_dir / provider_id / comic_id / chapter_id
        return not await asyncio.to_thread(chapter_dir.exists)

    async def get_image_stream(self, relative_path: str) -> Tuple[Any, str]:
        file_path = self.data_dir / relative_path
        
        def _check_exists():
            return file_path.exists() and file_path.is_file()
            
        if not await asyncio.to_thread(_check_exists):
            from src.domain.exceptions import AppBaseError
            raise AppBaseError(f"Image not found: {relative_path}")
        
        ctype, _ = mimetypes.guess_type(str(file_path))
        if not ctype:
            ctype = "application/octet-stream"
            
        async def file_iterator():
            async with aiofiles.open(file_path, "rb") as f:
                while chunk := await f.read(8192):
                    yield chunk
                    
        return file_iterator(), ctype

    async def delete_media(self, provider_id: str, comic_id: str) -> None:
        target_dir = self.data_dir / provider_id / comic_id
        
        def _delete():
            if target_dir.exists():
                shutil.rmtree(target_dir, ignore_errors=True)
                
        await asyncio.to_thread(_delete)
