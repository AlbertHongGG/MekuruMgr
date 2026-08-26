import pytest
from tests.e2e.test_data import PROVIDERS_TEST_DATA

@pytest.mark.parametrize("provider, keyword", PROVIDERS_TEST_DATA)
def test_provider_flow_server(provider, keyword, server_helper):
    server_helper.set_target(provider)
    
    # 1. EXPLORE
    server_helper.get("1. EXPLORE", f"/api/v1/comics/{provider}/explore")
    
    # 2. SEARCH
    search_res = server_helper.get("2. SEARCH", f"/api/v1/comics/{provider}/search", params={"keyword": keyword})
    if not search_res:
        server_helper.log_message("No search results found. Stop.")
        return
        
    comic_id = search_res[0].get("id")
    if not comic_id:
        server_helper.log_message("Search result has no ID. Stop.")
        return
        
    # 3. FETCH
    server_helper.get(f"3. FETCH (ID: {comic_id})", f"/api/v1/comics/{provider}/{comic_id}")
    
    # 4. LIST CHAPTERS
    chapters_res = server_helper.get(f"4. LIST CHAPTERS (ID: {comic_id})", f"/api/v1/comics/{provider}/{comic_id}/chapters")
    if not chapters_res:
        server_helper.log_message("No chapters found. Stop.")
        return
        
    chapter_id = chapters_res[0].get("id")
    if not chapter_id:
        server_helper.log_message("Chapter has no ID. Stop.")
        return
        
    # 5. LIST IMAGES
    server_helper.get(f"5. LIST IMAGES (Comic: {comic_id}, Chapter: {chapter_id})", 
                      f"/api/v1/comics/{provider}/{comic_id}/chapters/{chapter_id}/images")
