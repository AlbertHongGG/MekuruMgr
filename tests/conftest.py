import pytest
import os
import json
import time
from urllib.parse import urlparse
from src.core.registry import registry

@pytest.fixture(autouse=True, scope="session")
def setup_api_dumper():
    """
    Globally attaches a JSON dumper hook to all registered providers' HTTP clients.
    This intercepts at the application layer, ensuring we save fully decrypted JSONs.
    """
    output_dir = os.path.join(os.getcwd(), "test_outputs")

    def _dump_json_hook(provider_id: str, url: str, data: dict):
        try:
            dump_dir = os.path.join(output_dir, provider_id)
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

    registry.load_all_providers()
    
    def attach_hooks_recursive(obj, hook, visited=None):
        if visited is None:
            visited = set()
        if id(obj) in visited:
            return
        visited.add(id(obj))
        
        if hasattr(obj, "add_hook"):
            obj.add_hook(hook)
            
        if hasattr(obj, "__dict__"):
            for val in obj.__dict__.values():
                attach_hooks_recursive(val, hook, visited)

    for p_id, provider in registry.get_all().items():
        attach_hooks_recursive(provider, _dump_json_hook)
            
    yield
