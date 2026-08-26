import pytest
import os
from tests.e2e.cli_helper import CliTestHelper
from tests.e2e.test_data import get_test_cases

def test_archive_cli_flow(cli_helper: CliTestHelper):
    """
    Test the basic flow of archive CLI commands: track, list, queue, delete.
    Note: 'sync' blocks until complete in CLI mode, so the async pause/resume 
    state machine is heavily tested in the Server test instead.
    """
    cases = get_test_cases()
    if not cases:
        pytest.skip("No test cases found in test_data.py")
        
    case = cases[0]
    provider_id = case["provider"]
    comic_id = case["comic_id"]
    
    cli_helper.set_target(f"archive_cli")
    
    # 1. Track comic
    out = cli_helper.invoke("Track Comic", ["archive", "track", comic_id, "-p", provider_id])
    assert "Successfully tracked!" in out or "Tracking Complete" in out
    
    # 2. List archives
    out = cli_helper.invoke("List Archives", ["archive", "list"])
    assert comic_id[:10] in out
    
    # 3. Queue (should be empty initially)
    out = cli_helper.invoke("List Queue", ["archive", "queue"])
    assert "Download Task Queue" in out or "No tasks" in out
    
    # 4. Delete archive
    out = cli_helper.invoke("Delete Archive", ["archive", "delete", comic_id, "-p", provider_id])
    assert "Successfully deleted" in out
    
    # 5. List archives again (should be empty or not contain the comic)
    out = cli_helper.invoke("List Archives After Delete", ["archive", "list"])
    assert comic_id not in out
