import pytest
import os
import shutil
import json
import time
from urllib.parse import urlparse

# Force test isolation BEFORE any app imports
os.environ["APP_STORAGE__DATA_DIR"] = os.path.join(os.getcwd(), "test_outputs", "data")


from cli import app as cli_app
from server import app as server_app
from src.core.registry import registry
from tests.e2e.cli_helper import CliTestHelper
from tests.e2e.server_helper import ServerTestHelper
from tests.e2e.logger import TestOutputLogger

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """初始化測試環境，清理舊有輸出檔，並載入 Providers，同時掛載封包側錄 Hook"""
    output_dir = os.path.join(os.getcwd(), "test_outputs")
    
    if os.path.exists(output_dir):
        try:
            shutil.rmtree(output_dir, ignore_errors=True)
        except Exception as e:
            print(f"Warning: could not fully clear test_outputs: {e}")
            
    # Re-create isolation data dir
    os.makedirs(os.environ["APP_STORAGE__DATA_DIR"], exist_ok=True)
        
    registry.load_all_providers()
    
    # 乾淨的封包側錄 Hook (不再用 __dict__ 暴力破解)
    def _dump_json_hook(provider_id: str, url: str, data: dict):
        # We don't have global test mode anymore. Just dump in a flat JSON hooks dir.
        try:
            dump_dir = os.path.join(output_dir, "api_hooks", provider_id)
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
            
    for p_id, provider_class in registry.get_all_classes().items():
        pass # We mock hooks globally later_dump_json_hook)
        
    yield

@pytest.fixture
def current_test_info(request):
    """解析當前測試節點，取得介面、Provider 與 Domain"""
    node_id = request.node.nodeid
    
    # Extract interface (cli or server) from path
    interface = "unknown"
    if "cli/" in node_id:
        interface = "cli"
    elif "server/" in node_id:
        interface = "server"
        
    # Extract domain (comic, archive, library)
    domain = "unknown"
    if "test_comic_" in node_id:
        domain = "comic"
    elif "test_archive_" in node_id:
        domain = "archive"
    elif "test_library_" in node_id:
        domain = "library"
        
    # Extract provider and comic_id from callspec if parameterized
    if hasattr(request.node, "callspec"):
        provider = request.node.callspec.params.get("provider", "unknown_provider")
        comic_id = request.node.callspec.params.get("comic_id", "unknown_comic")
    else:
        provider = "unknown_provider"
        comic_id = "unknown_comic"
    
    return {
        "interface": interface,
        "domain": domain,
        "provider": provider,
        "comic_id": comic_id,
        "test_name": request.node.name
    }

@pytest.fixture
def test_logger(current_test_info):
    interface = current_test_info["interface"]
    provider = current_test_info["provider"]
    domain = current_test_info["domain"]
    
    log_path = os.path.join(os.getcwd(), "test_outputs", interface, provider, f"{domain}.log")
    title = f"{interface.upper()} - {domain} ({provider})"
    
    return TestOutputLogger(file_path=log_path, title=title)

@pytest.fixture
def cli_helper(test_logger):
    """注入 CliTestHelper，供所有 CLI E2E 測試使用"""
    return CliTestHelper(app=cli_app, logger=test_logger)

@pytest.fixture
def server_helper(test_logger):
    """注入 ServerTestHelper，供所有 Server E2E 測試使用"""
    from fastapi.testclient import TestClient
    with TestClient(server_app) as client:
        helper = ServerTestHelper(app=server_app, logger=test_logger)
        helper.client = client
        yield helper

@pytest.fixture
def mock_library(current_test_info):
    """Inject a dummy comic into the isolated data_dir for library tests."""
    
    from src.domain.models import LocalComic, DownloadTask, ChapterTask, TaskStatus
    import asyncio
    
    # 使用當前執行的 provider 和 comic_id 來建立 mock，確保一致性
    original_provider_id = current_test_info["provider"]
    provider_id = original_provider_id
    comic_id = current_test_info["comic_id"]
    
    if provider_id == "unknown_provider":
        provider_id = "test_provider"
        original_provider_id = "test_provider"
    else:
        try:
            provider_id = registry.resolve_id(provider_id)
        except Exception:
            pass
            
    if comic_id == "unknown_comic":
        comic_id = "test_comic"
    
    from src.storage.engines.sqlite.provider import SqliteStorageProvider
    import os
    provider = SqliteStorageProvider(os.environ["APP_STORAGE__DATA_DIR"])
    
    lib_comic = LocalComic(
        provider_id=provider_id,
        id=comic_id,
        title=f"Test Comic {comic_id}",
        author="Test Author",
        description="A comic for testing",
        tags=["test", "mock"],
        cover_url="http://example.com/cover.jpg",
        local_path=f"{provider_id}/{comic_id}"
    )
    asyncio.run(provider.get_library_storage().save_comic(lib_comic))
    
    task = DownloadTask(
        task_id=f"{provider_id}::{comic_id}",
        provider_id=provider_id,
        comic_id=comic_id,
        comic_title=lib_comic.title,
        cover_url=lib_comic.cover_url,
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
    asyncio.run(provider.get_task_storage().save_task(task))
    
    media_storage = provider.get_media_storage()
    asyncio.run(media_storage.save_image(provider_id, comic_id, "cover", 0, b"fake_cover", "image/jpeg"))
    asyncio.run(media_storage.save_image(provider_id, comic_id, "ch1", 1, b"fake_img1", "image/jpeg"))
    asyncio.run(media_storage.save_image(provider_id, comic_id, "ch1", 2, b"fake_img2", "image/jpeg"))
    
    yield {"provider_id": original_provider_id, "comic_id": comic_id, "chapter_id": "ch1"}
    
    asyncio.run(provider.get_library_storage().delete_comic(provider_id, comic_id))
    asyncio.run(provider.get_task_storage().delete_task(task.task_id))
    asyncio.run(media_storage.delete_media(provider_id, comic_id))
