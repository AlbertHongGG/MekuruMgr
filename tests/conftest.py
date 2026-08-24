import pytest
import os
import json
import time
import httpx
from urllib.parse import urlparse

@pytest.fixture(autouse=True, scope="session")
def setup_api_dumper():
    """
    Globally intercepts httpx API calls during the test session and 
    dumps the JSON responses into the test_outputs directory.
    """
    _orig_client_send = httpx.Client.send
    
    # Define dump directory base
    output_dir = os.path.join(os.getcwd(), "test_outputs")

    def _dump_json(request, response):
        try:
            # Only intercept JSON or text responses
            content_type = response.headers.get("Content-Type", "")
            if "application/json" not in content_type and "text/plain" not in content_type:
                return

            url = str(request.url)
            
            # Determine provider by heuristic based on URL
            provider = "unknown"
            if "copy202601.com" in url:
                provider = "copymanga"
            elif "webtoon" in url or "naver.com" in url:
                provider = "webtoon"
            elif "comicwifi" in url or "ciyixiu" in url or "cxxapi" in url:
                provider = "comicwifi"
                
            dump_dir = os.path.join(output_dir, provider)
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
            
            response.read()
            try:
                data = response.json()
            except:
                return
                
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def patched_send(self, request, *args, **kwargs):
        response = _orig_client_send(self, request, *args, **kwargs)
        _dump_json(request, response)
        return response

    httpx.Client.send = patched_send
    
    yield
    
    # Restore after tests
    httpx.Client.send = _orig_client_send
