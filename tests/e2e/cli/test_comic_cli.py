import pytest
from tests.e2e.test_data import PROVIDERS_TEST_DATA
from src.application.comic_manager import ComicManager

@pytest.mark.parametrize("provider, keyword", PROVIDERS_TEST_DATA)
def test_provider_flow_cli(provider, keyword, cli_helper):
    cli_helper.set_target(provider)
    
    # 1. EXPLORE
    cli_helper.invoke("1. EXPLORE", ["comic", "explore", "--provider", provider])
    
    # 2. SEARCH
    cli_helper.invoke("2. SEARCH", ["comic", "search", keyword, "--provider", provider])
    
    # --- Intercept domain logic to get ID for next steps ---
    manager = ComicManager()
    manager.use(provider)
    search_results = manager.search_comics(keyword)
    if not search_results:
        cli_helper.log_message("No search results found. Stop.")
        return
    comic_id = search_results[0].id
    
    # 3. FETCH
    cli_helper.invoke(f"3. FETCH (ID: {comic_id})", ["comic", "fetch", comic_id, "--provider", provider])
    
    # 4. LIST CHAPTERS
    cli_helper.invoke(f"4. LIST CHAPTERS (ID: {comic_id})", ["comic", "list-chapters", comic_id, "--provider", provider])
    
    # --- Intercept domain logic to get chapter ID for next step ---
    chapters = manager.fetch_all_chapters(comic_id)
    if not chapters:
        cli_helper.log_message("No chapters found. Stop.")
        return
    chapter_id = chapters[0].id
    
    # 5. LIST IMAGES
    cli_helper.invoke(f"5. LIST IMAGES (Comic: {comic_id}, Chapter: {chapter_id})", 
                      ["comic", "list-images", comic_id, chapter_id, "--provider", provider])
