import pytest
from tests.e2e.test_data import PROVIDERS_TEST_DATA
from tests.e2e.cli_helper import CliTestHelper

@pytest.mark.parametrize("provider, keyword, comic_id", PROVIDERS_TEST_DATA)
def test_library_cli_explore(provider, keyword, comic_id, cli_helper: CliTestHelper, mock_library: dict):
    """Test library explore command."""
    out = cli_helper.invoke("Explore Library", ["library", "explore"])
    
    # Extract primary id
    from src.core.registry import registry
    primary_id = registry.resolve_id(mock_library["provider_id"])
    
    assert "Local Comic Library" in out
    # 這個因為 comic_id 太長在 Rich Table 時會截斷，所以取 [:10]
    assert mock_library["comic_id"][:10] in out
    assert primary_id in out

@pytest.mark.parametrize("provider, keyword, comic_id", PROVIDERS_TEST_DATA)
def test_library_cli_search(provider, keyword, comic_id, cli_helper: CliTestHelper, mock_library: dict):
    """Test library search command."""
    # Mock library title is formatted as "Test Comic {comic_id}"
    out = cli_helper.invoke("Search Library (Match)", ["library", "search", f"Test Comic {comic_id}"])
    assert mock_library["comic_id"][:10] in out
    
    out2 = cli_helper.invoke("Search Library (No Match)", ["library", "search", "NonExistentKeyword123"])
    assert mock_library["comic_id"][:10] not in out2

@pytest.mark.parametrize("provider, keyword, comic_id", PROVIDERS_TEST_DATA)
def test_library_cli_show(provider, keyword, comic_id, cli_helper: CliTestHelper, mock_library: dict):
    """Test library show command."""
    cid = mock_library["comic_id"]
    pid = mock_library["provider_id"]
    
    out = cli_helper.invoke("Show Library Comic", ["library", "show", cid, "-p", pid])
    assert f"Test Comic {cid}" in out
    assert "Test Author" in out
    assert "ch1" in out

@pytest.mark.parametrize("provider, keyword, comic_id", PROVIDERS_TEST_DATA)
def test_library_cli_read(provider, keyword, comic_id, cli_helper: CliTestHelper, mock_library: dict):
    """Test library read command."""
    cid = mock_library["comic_id"]
    pid = mock_library["provider_id"]
    chid = mock_library["chapter_id"]
    
    out = cli_helper.invoke("Read Library Chapter", ["library", "read", cid, chid, "-p", pid])
    assert "001.jpg" in out or "001.jpeg" in out
    assert "002.jpg" in out or "002.jpeg" in out
    assert "file://" in out
