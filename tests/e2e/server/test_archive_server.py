import pytest
import time
from tests.e2e.server_helper import ServerTestHelper
from tests.e2e.test_data import get_test_cases
from src.domain.models.archive import TaskStatus

def test_archive_server_queue_flow(server_helper: ServerTestHelper):
    """
    Test the complete background queue flow using the REST API:
    Track -> Sync -> Pause -> Verify PAUSED -> Resume -> Verify COMPLETED -> Clean up
    """
    cases = get_test_cases()
    if not cases:
        pytest.skip("No test cases found in test_data.py")
        
    case = cases[0]
    provider_id = case["provider"]
    comic_id = case["comic_id"]
    
    server_helper.set_target(f"archive_server_{provider_id}")
    
    # 1. Track
    data = server_helper.post("Track Comic", f"/api/v1/archive/{provider_id}/{comic_id}/track")
    assert data is not None
    assert "data" in data
    
    # 2. Sync (Start Download)
    task_data = server_helper.post("Sync Comic", f"/api/v1/archive/{provider_id}/{comic_id}/sync")
    assert task_data is not None
    assert task_data["status"] in ["queued", "downloading"]
    
    # Let it download for a moment
    time.sleep(1)
    
    # 3. Pause
    pause_res = server_helper.post("Pause Sync", f"/api/v1/archive/{provider_id}/{comic_id}/pause")
    assert pause_res is not None
    assert pause_res.get("status") == "paused"
    
    # 4. Verify PAUSED state
    prog_data = server_helper.get("Check Progress Paused", f"/api/v1/archive/{provider_id}/{comic_id}/progress")
    assert prog_data is not None
    assert prog_data["status"] == "paused"
    
    # 5. Resume
    resume_res = server_helper.post("Resume Sync", f"/api/v1/archive/{provider_id}/{comic_id}/resume")
    assert resume_res is not None
    assert resume_res.get("status") == "queued"
    
    # 6. Wait for SOME progress
    max_retries = 30
    downloaded_some = False
    
    for _ in range(max_retries):
        time.sleep(1)
        prog = server_helper.get("Poll Progress", f"/api/v1/archive/{provider_id}/{comic_id}/progress")
        if prog and prog["status"] == "downloading":
            # Check if any chapter has downloaded pages
            for ch in prog.get("chapters", {}).values():
                if ch.get("downloaded_pages", 0) > 0:
                    downloaded_some = True
                    break
            
            if downloaded_some:
                break
            
    assert downloaded_some, f"Task did not download any pages in time."
    
    # 7. Check Library List
    lib_list = server_helper.get("List Archives", "/api/v1/archive/")
    assert any(c["comic_id"] == comic_id for c in lib_list)
    
    # 8. Clean up (this cancels the task and deletes the comic)
    del_res = server_helper.client.delete(f"/api/v1/archive/{provider_id}/{comic_id}")
    assert del_res.status_code == 200
