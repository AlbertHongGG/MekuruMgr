import subprocess
import sys
import os
import time

def main():
    PROVIDERS = {
        "webtoon": "骷髏",
        "comicwifi": "骷髏",
        "copymanga": "骷髏",        
    }

    output_dir = "test_outputs"
    os.makedirs(output_dir, exist_ok=True)
    
    print("Starting automated tests for all providers...")

    for provider, keyword in PROVIDERS.items():
        print(f"\n=========================================")
        print(f"Testing provider: {provider}")
        output_file = os.path.join(output_dir, f"{provider}_test.txt")
        
        with open(output_file, "w", encoding="utf-8") as f:
            def run_cmd(cmd_args, title):
                f.write(f"========================================\n")
                f.write(f"=== {title}\n")
                f.write(f"=== COMMAND: uv run cli.py {' '.join(cmd_args)}\n")
                f.write(f"========================================\n")
                
                env = os.environ.copy()
                env["NO_COLOR"] = "1"
                
                full_cmd = ["uv", "run", "cli.py"] + cmd_args
                
                print(f"  -> Running: {title}")
                result = subprocess.run(
                    full_cmd,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    env=env
                )
                
                f.write(result.stdout)
                if result.stderr:
                    f.write("\n[STDERR]\n")
                    f.write(result.stderr)
                f.write("\n\n")
                
                time.sleep(1)

            run_cmd(["comic", "explore", "--provider", provider], "1. EXPLORE")
            run_cmd(["comic", "search", keyword, "--provider", provider], "2. SEARCH")
            
            try:
                from src.application.comic_manager import ComicManager
                from src.core.registry import registry
                registry.load_all_providers()
                
                provider_instance = registry.get_provider(provider)
                manager = ComicManager()
                manager.use(provider)
                
                search_results = manager.search_comics(keyword)
                if not search_results:
                    f.write("No search results found. Cannot continue test.\n")
                    print("  -> Search returned no results. Skipping rest.")
                    continue
                    
                comic_id = search_results[0].id
                
                run_cmd(["comic", "fetch", comic_id, "--provider", provider], f"3. FETCH (ID: {comic_id})")
                run_cmd(["comic", "list-chapters", comic_id, "--provider", provider], f"4. LIST CHAPTERS (ID: {comic_id})")
                
                chapters = manager.fetch_all_chapters(comic_id)
                if not chapters:
                    f.write("No chapters found. Cannot continue test.\n")
                    print("  -> No chapters found. Skipping image list.")
                    continue
                    
                chapter_id = chapters[0].id
                
                run_cmd(["comic", "list-images", comic_id, chapter_id, "--provider", provider], f"5. LIST IMAGES (Comic: {comic_id}, Chapter: {chapter_id})")
                
            except Exception as e:
                msg = f"\n[INTERNAL TEST SCRIPT ERROR] {str(e)}\n"
                f.write(msg)
                print(msg)
                
        print(f"Finished testing {provider}. Output saved to {output_file}")

if __name__ == "__main__":
    main()
