from tests.e2e.server_helper import ServerTestHelper

def test_library_server_explore(server_helper: ServerTestHelper, mock_library: dict):
    """Test GET /library/explore"""
    server_helper.set_target("library_server_explore")
    
    data = server_helper.get("Explore Library", "/api/v1/library/explore")
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(c["comic_id"] == mock_library["comic_id"] for c in data)

def test_library_server_search(server_helper: ServerTestHelper, mock_library: dict):
    """Test GET /library/search"""
    server_helper.set_target("library_server_search")
    
    data = server_helper.get("Search Library", "/api/v1/library/search", params={"keyword": "Test Comic"})
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["comic_id"] == mock_library["comic_id"]
    
    data2 = server_helper.get("Search Library (Empty)", "/api/v1/library/search", params={"keyword": "NonExistentKeyword123"})
    assert len(data2) == 0

def test_library_server_detail(server_helper: ServerTestHelper, mock_library: dict):
    """Test GET /library/{p}/{c}"""
    server_helper.set_target("library_server_detail")
    p = mock_library["provider_id"]
    c = mock_library["comic_id"]
    
    data = server_helper.get("Library Comic Detail", f"/api/v1/library/{p}/{c}")
    assert data["comic_id"] == c
    assert data["title"] == "Test Comic Title"
    assert "cover.jpg" in data["cover_url"]

def test_library_server_chapters(server_helper: ServerTestHelper, mock_library: dict):
    """Test GET /library/{p}/{c}/chapters and images"""
    server_helper.set_target("library_server_chapters")
    p = mock_library["provider_id"]
    c = mock_library["comic_id"]
    ch = mock_library["chapter_id"]
    
    chapters = server_helper.get("Library Chapters", f"/api/v1/library/{p}/{c}/chapters")
    assert isinstance(chapters, list)
    assert len(chapters) == 1
    assert chapters[0]["chapter_id"] == ch
    
    images = server_helper.get("Library Chapter Images", f"/api/v1/library/{p}/{c}/chapters/{ch}")
    assert images["chapter_id"] == ch
    assert len(images["images"]) == 2
    assert any("001" in img for img in images["images"])
    assert any("/api/v1/library/media" in img for img in images["images"])
