import json
import logging
import aiosqlite
from pathlib import Path
from typing import Dict, Optional, List

from pydantic import TypeAdapter

from src.domain.models import LocalComic, DownloadTask
from src.storage.core.archive_interface import ILibraryStorage, ITaskStorage

logger = logging.getLogger(__name__)

class SqliteLibraryStorage(ILibraryStorage):
    def __init__(self, db_path: str = "data/comicmgr.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ta = TypeAdapter(LocalComic)
        self._init_task = None

    async def _init_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS library (
                    id TEXT PRIMARY KEY,
                    provider_id TEXT,
                    comic_id TEXT,
                    title TEXT,
                    data JSON
                )
            """)
            await db.commit()

    async def _ensure_init(self):
        if not hasattr(self, '_initialized') or not self._initialized:
            await self._init_db()
            self._initialized = True

    async def get_comic(self, provider_id: str, comic_id: str) -> Optional[LocalComic]:
        await self._ensure_init()
        key = f"{provider_id}::{comic_id}"
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT data FROM library WHERE id = ?", (key,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return self._ta.validate_json(row[0])
        return None

    async def save_comic(self, comic: LocalComic) -> None:
        await self._ensure_init()
        key = f"{comic.provider_id}::{comic.id}"
        data_json = comic.model_dump_json()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO library (id, provider_id, comic_id, title, data)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title = excluded.title,
                    data = excluded.data
            """, (key, comic.provider_id, comic.id, comic.title, data_json))
            await db.commit()

    async def delete_comic(self, provider_id: str, comic_id: str) -> None:
        await self._ensure_init()
        key = f"{provider_id}::{comic_id}"
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM library WHERE id = ?", (key,))
            await db.commit()

    async def list_comics(self) -> List[LocalComic]:
        await self._ensure_init()
        results = []
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT data FROM library") as cursor:
                async for row in cursor:
                    results.append(self._ta.validate_json(row[0]))
        return results

    async def search_comics(self, keyword: str) -> List[LocalComic]:
        await self._ensure_init()
        keyword = keyword.lower()
        results = []
        # Fallback to in-memory search for complex JSON tags, or we can use SQLite LIKE on JSON.
        # For simplicity and correctness with the existing logic, we fetch and filter.
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT data FROM library") as cursor:
                async for row in cursor:
                    comic = self._ta.validate_json(row[0])
                    if (keyword in comic.title.lower() or 
                        keyword in comic.description.lower() or 
                        keyword in comic.id.lower() or
                        keyword in comic.provider_id.lower() or
                        any(keyword in tag.lower() for tag in comic.tags)):
                        results.append(comic)
        return results


class SqliteTaskStorage(ITaskStorage):
    def __init__(self, db_path: str = "data/comicmgr.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ta = TypeAdapter(DownloadTask)
        self._init_task = None

    async def _init_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    provider_id TEXT,
                    comic_id TEXT,
                    status TEXT,
                    data JSON
                )
            """)
            await db.commit()

    async def _ensure_init(self):
        if not hasattr(self, '_initialized') or not self._initialized:
            await self._init_db()
            self._initialized = True

    async def get_task(self, task_id: str) -> Optional[DownloadTask]:
        await self._ensure_init()
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT data FROM tasks WHERE id = ?", (task_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return self._ta.validate_json(row[0])
        return None

    async def save_task(self, task: DownloadTask) -> None:
        await self._ensure_init()
        data_json = task.model_dump_json()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO tasks (id, provider_id, comic_id, status, data)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    status = excluded.status,
                    data = excluded.data
            """, (task.task_id, task.provider_id, task.comic_id, task.status.value, data_json))
            await db.commit()

    async def delete_task(self, task_id: str) -> None:
        await self._ensure_init()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            await db.commit()

    async def list_tasks(self) -> List[DownloadTask]:
        await self._ensure_init()
        results = []
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT data FROM tasks") as cursor:
                async for row in cursor:
                    results.append(self._ta.validate_json(row[0]))
        return results
