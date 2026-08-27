import pytest
import os
from tests.e2e.cli_helper import CliTestHelper
from tests.e2e.test_data import PROVIDERS_TEST_DATA

@pytest.mark.parametrize("provider, keyword, comic_id", PROVIDERS_TEST_DATA)
def test_archive_cli_flow(provider, keyword, comic_id, cli_helper: CliTestHelper):
    """
    Test the basic flow of archive CLI commands: track, list, queue, delete.
    Note: 'sync' blocks until complete in CLI mode, so the async pause/resume 
    state machine is heavily tested in the Server test instead.
    """
    
    # 1. Track comic
    out = cli_helper.invoke("Track Comic", ["archive", "track", comic_id, "-p", provider])
    assert "Successfully tracked!" in out or "Tracking Complete" in out
    
    # 2. List archives
    out = cli_helper.invoke("List Archives", ["archive", "list"])
    assert comic_id[:10] in out
    
    # 3. Queue 
    # To test queue rendering with data without blocking on sync, we can manually inject a mock task
    from src.storage.factory import StorageFactory
    from src.domain.models.archive import DownloadTask, TaskStatus
    ts = StorageFactory.get_provider().get_task_storage()
    mock_task = DownloadTask(
        task_id=f"{provider}::{comic_id}",
        provider_id=provider,
        comic_id=comic_id,
        comic_title=f"MockTitle {comic_id}",
        cover_url="mock_cover.jpg",
        status=TaskStatus.QUEUED
    )
    ts.save_task(mock_task)
    
    out = cli_helper.invoke("List Queue", ["archive", "queue"])
    assert "Download Task Queue" in out
    assert comic_id[:10] in out
    assert f"MockTitle {comic_id}"[:10] in out
    
    # Track again and start sync via API-like behavior? Wait, CLI sync blocks. 
    # But since we just want to verify CLI queue command works, we can just ensure it doesn't crash here.
    
    # 4. Delete archive
    out = cli_helper.invoke("Delete Archive", ["archive", "delete", comic_id, "-p", provider])
    assert "Successfully deleted" in out
    
    # 5. List archives again (should be empty or not contain the comic)
    out = cli_helper.invoke("List Archives After Delete", ["archive", "list"])
    assert comic_id not in out
