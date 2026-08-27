import pytest
from tests.e2e.test_data import PROVIDERS_TEST_DATA
from tests.e2e.server_helper import ServerTestHelper

@pytest.mark.parametrize("provider, keyword, comic_id", PROVIDERS_TEST_DATA)
def test_library_server_explore(provider, keyword, comic_id, server_helper: ServerTestHelper, mock_library: dict):
    """Test GET /library/explore"""
    data = server_helper.get("Explore Library", "/api/v1/library/explore")
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(c["id"] == mock_library["comic_id"] for c in data)

@pytest.mark.parametrize("provider, keyword, comic_id", PROVIDERS_TEST_DATA)
def test_library_server_search(provider, keyword, comic_id, server_helper: ServerTestHelper, mock_library: dict):
    """Test GET /library/search"""
    # Mock library title is formatted as "Test Comic {comic_id}"
    data = server_helper.get("Search Library", "/api/v1/library/search", params={"keyword": f"Test Comic {comic_id}"})
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["id"] == mock_library["comic_id"]
    
    data2 = server_helper.get("Search Library (Empty)", "/api/v1/library/search", params={"keyword": "NonExistentKeyword123"})
    assert len(data2) == 0

@pytest.mark.parametrize("provider, keyword, comic_id", PROVIDERS_TEST_DATA)
def test_library_server_detail(provider, keyword, comic_id, server_helper: ServerTestHelper, mock_library: dict):
    """Test GET /library/{p}/{c}"""
    p = mock_library["provider_id"]
    c = mock_library["comic_id"]
    
    data = server_helper.get("Library Comic Detail", f"/api/v1/library/{p}/{c}")
    assert data["id"] == c
    assert data["title"] == f"Test Comic {c}"
    assert "cover.jpg" in data["cover_url"]

@pytest.mark.parametrize("provider, keyword, comic_id", PROVIDERS_TEST_DATA)
def test_library_server_chapters(provider, keyword, comic_id, server_helper: ServerTestHelper, mock_library: dict):
    """Test GET /library/{p}/{c}/chapters and images"""
    p = mock_library["provider_id"]
    c = mock_library["comic_id"]
    ch = mock_library["chapter_id"]
    
    chapters = server_helper.get("Library Chapters", f"/api/v1/library/{p}/{c}/chapters")
    assert isinstance(chapters, list)
    assert len(chapters) == 1
    assert chapters[0]["id"] == ch
    
    images = server_helper.get("Library Chapter Images", f"/api/v1/library/{p}/{c}/chapters/{ch}")
    assert images["chapter_id"] == ch
    assert len(images["images"]) == 2
    assert any("001" in img for img in images["images"])
    assert any("/api/v1/library/media" in img for img in images["images"])
