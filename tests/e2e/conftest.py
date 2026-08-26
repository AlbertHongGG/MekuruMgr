import pytest
import os
import shutil
import json
import time
from urllib.parse import urlparse

# Force test isolation BEFORE any app imports
os.environ["APP_DATA_DIR"] = os.path.join(os.getcwd(), "test_outputs", "data")


from cli import app as cli_app
from server import app as server_app
from src.core.registry import registry
from tests.e2e.cli_helper import CliTestHelper
from tests.e2e.server_helper import ServerTestHelper

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """初始化測試環境，清理舊有輸出檔，並載入 Providers，同時掛載封包側錄 Hook"""
    output_dir = os.path.join(os.getcwd(), "test_outputs")
    
    # We don't want to blindly delete everything in test_outputs if we want to keep some logs, 
    # but for isolation, deleting the whole test_outputs is the safest to avoid stale DBs.
    if os.path.exists(output_dir):
        # We might run into permission issues if files are locked, but Windows usually handles it if tests aren't running
        try:
            shutil.rmtree(output_dir, ignore_errors=True)
        except Exception as e:
            print(f"Warning: could not fully clear test_outputs: {e}")
            
    # Re-create isolation data dir
    os.makedirs(os.environ["APP_DATA_DIR"], exist_ok=True)
        
    registry.load_all_providers()
    
    # 乾淨的封包側錄 Hook (不再用 __dict__ 暴力破解)
    def _dump_json_hook(provider_id: str, url: str, data: dict):
        from tests.e2e import logger as e2e_logger
        mode = e2e_logger.current_test_mode
        if mode == "unknown":
            return
            
        try:
            dump_dir = os.path.join(output_dir, mode, provider_id)
            os.makedirs(dump_dir, exist_ok=True)
            
            parsed = urlparse(url)
            safe_endpoint = parsed.path.strip("/").replace("/", "_")
            if not safe_endpoint:
                safe_endpoint = "root"
                
            timestamp = int(time.time() * 1000)
            filename = f"{timestamp}_{safe_endpoint}.json"
            
            if len(filename) > 100:
                filename = filename[:95] + ".json"
                
            filepath = os.path.join(dump_dir, filename)
            
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Failed to dump json: {e}")
            
    # 對所有註冊的 Provider 掛載標準的 API Hook
    for p_id, provider in registry.get_all().items():
        provider.add_api_hook(_dump_json_hook)
        
    yield

@pytest.fixture
def cli_helper():
    """注入 CliTestHelper，供所有 CLI E2E 測試使用"""
    return CliTestHelper(app=cli_app)

@pytest.fixture
def server_helper():
    """注入 ServerTestHelper，供所有 Server E2E 測試使用"""
    from fastapi.testclient import TestClient
    with TestClient(server_app) as client:
        helper = ServerTestHelper(app=server_app)
        helper.client = client
        yield helper

@pytest.fixture
def mock_library():
    """Inject a dummy comic into the isolated data_dir for library tests."""
    from src.storage.factory import StorageFactory
    from src.domain.models.archive import LibraryComic, DownloadTask, ChapterTask, TaskStatus
    import asyncio
    
    provider_id = "test_provider"
    comic_id = "test_comic"
    
    provider = StorageFactory.get_provider()
    
    # 1. Save Library Metadata
    lib_comic = LibraryComic(
        provider_id=provider_id,
        comic_id=comic_id,
        title="Test Comic Title",
        author="Test Author",
        description="A comic for testing",
        tags=["test", "mock"],
        cover_url="http://example.com/cover.jpg",
        local_path=f"{provider_id}/{comic_id}"
    )
    provider.get_library_storage().save_comic(lib_comic)
    
    # 2. Save Task State (Completed)
    task = DownloadTask(
        task_id=f"{provider_id}::{comic_id}",
        provider_id=provider_id,
        comic_id=comic_id,
        status=TaskStatus.COMPLETED,
        total_chapters=1,
        completed_chapters=1,
        chapters={
            "ch1": ChapterTask(
                chapter_id="ch1",
                title="Chapter 1",
                status=TaskStatus.COMPLETED,
                total_pages=2,
                downloaded_pages=2
            )
        }
    )
    provider.get_task_storage().save_task(task)
    
    # 3. Create mock image files
    media_storage = provider.get_media_storage()
    asyncio.run(media_storage.save_image(provider_id, comic_id, "cover", 0, b"fake_cover", "image/jpeg"))
    asyncio.run(media_storage.save_image(provider_id, comic_id, "ch1", 1, b"fake_img1", "image/jpeg"))
    asyncio.run(media_storage.save_image(provider_id, comic_id, "ch1", 2, b"fake_img2", "image/jpeg"))
    
    yield {"provider_id": provider_id, "comic_id": comic_id, "chapter_id": "ch1"}
    
    # Teardown
    provider.get_library_storage().delete_comic(provider_id, comic_id)
    provider.get_task_storage().delete_task(task.task_id)
    media_storage.delete_media(provider_id, comic_id)
