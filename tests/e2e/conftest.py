import pytest
import os
import shutil
import json
import time
from urllib.parse import urlparse

from cli import app as cli_app
from server import app as server_app
from src.core.registry import registry
from tests.e2e.cli_helper import CliTestHelper
from tests.e2e.server_helper import ServerTestHelper

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """初始化測試環境，清理舊有輸出檔，並載入 Providers，同時掛載封包側錄 Hook"""
    output_dir = os.path.join(os.getcwd(), "test_outputs")
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir, ignore_errors=True)
        
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
    return ServerTestHelper(app=server_app)
