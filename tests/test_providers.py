import pytest
import os
from typer.testing import CliRunner
from cli import app
from src.core.registry import registry
from src.application.comic_manager import ComicManager

runner = CliRunner()

PROVIDERS_TEST_DATA = [
    ("webtoon", "骷髏"),
    ("comicwifi", "骷髏"),
    ("copymanga", "骷髏"),
]

@pytest.fixture(scope="session", autouse=True)
def setup_output_dir():
    os.makedirs("test_outputs", exist_ok=True)
    registry.load_all_providers()

@pytest.mark.parametrize("provider, keyword", PROVIDERS_TEST_DATA)
def test_provider_flow(provider, keyword):
    """
    Tests the complete flow for a single provider.
    Since we use CliRunner, this all runs in the same process,
    and API calls will be automatically intercepted by conftest.py
    """
    output_file = os.path.join("test_outputs", f"{provider}_test.txt")
    
    with open(output_file, "w", encoding="utf-8") as f:
        def run_cli_cmd(args_list, title):
            f.write(f"========================================\n")
            f.write(f"=== {title}\n")
            f.write(f"=== COMMAND: cli {' '.join(args_list)}\n")
            f.write(f"========================================\n")
            
            result = runner.invoke(app, args_list)
            
            f.write(result.stdout)
            if result.exception and not isinstance(result.exception, SystemExit):
                f.write(f"\n[EXCEPTION]\n{str(result.exception)}\n")
            f.write("\n\n")
            return result

        # 1. EXPLORE
        run_cli_cmd(["comic", "explore", "--provider", provider], "1. EXPLORE")
        
        # 2. SEARCH
        run_cli_cmd(["comic", "search", keyword, "--provider", provider], "2. SEARCH")
        
        # 3. GET ID FOR FETCH
        manager = ComicManager()
        manager.use(provider)
        search_results = manager.search_comics(keyword)
        if not search_results:
            f.write("No search results found. Cannot continue test.\n")
            return
            
        comic_id = search_results[0].id
        
        # 4. FETCH
        run_cli_cmd(["comic", "fetch", comic_id, "--provider", provider], f"3. FETCH (ID: {comic_id})")
        
        # 5. LIST CHAPTERS
        run_cli_cmd(["comic", "list-chapters", comic_id, "--provider", provider], f"4. LIST CHAPTERS (ID: {comic_id})")
        
        # 6. GET CHAPTER FOR IMAGES
        chapters = manager.fetch_all_chapters(comic_id)
        if not chapters:
            f.write("No chapters found. Cannot continue test.\n")
            return
            
        chapter_id = chapters[0].id
        
        # 7. LIST IMAGES
        run_cli_cmd(["comic", "list-images", comic_id, chapter_id, "--provider", provider], f"5. LIST IMAGES (Comic: {comic_id}, Chapter: {chapter_id})")
