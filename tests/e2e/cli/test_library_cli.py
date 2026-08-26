from tests.e2e.cli_helper import CliTestHelper

def test_library_cli_explore(cli_helper: CliTestHelper, mock_library: dict):
    """Test library explore command."""
    cli_helper.set_target("library_cli_explore")
    out = cli_helper.invoke("Explore Library", ["library", "explore"])
    
    assert "Local Comic Library" in out
    assert mock_library["comic_id"] in out
    assert mock_library["provider_id"] in out

def test_library_cli_search(cli_helper: CliTestHelper, mock_library: dict):
    """Test library search command."""
    cli_helper.set_target("library_cli_search")
    
    out = cli_helper.invoke("Search Library (Match)", ["library", "search", "Test Comic Title"])
    assert mock_library["comic_id"] in out
    
    out2 = cli_helper.invoke("Search Library (No Match)", ["library", "search", "NonExistentKeyword123"])
    assert mock_library["comic_id"] not in out2

def test_library_cli_show(cli_helper: CliTestHelper, mock_library: dict):
    """Test library show command."""
    cli_helper.set_target("library_cli_show")
    comic_id = mock_library["comic_id"]
    provider_id = mock_library["provider_id"]
    
    out = cli_helper.invoke("Show Library Comic", ["library", "show", comic_id, "-p", provider_id])
    assert "Test Comic Title" in out
    assert "Test Author" in out
    assert "ch1" in out

def test_library_cli_read(cli_helper: CliTestHelper, mock_library: dict):
    """Test library read command."""
    cli_helper.set_target("library_cli_read")
    comic_id = mock_library["comic_id"]
    provider_id = mock_library["provider_id"]
    chapter_id = mock_library["chapter_id"]
    
    out = cli_helper.invoke("Read Library Chapter", ["library", "read", comic_id, chapter_id, "-p", provider_id])
    assert "001.jpg" in out or "001.jpeg" in out
    assert "002.jpg" in out or "002.jpeg" in out
    assert "file://" in out
