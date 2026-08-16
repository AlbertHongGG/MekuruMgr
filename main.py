from src.core.exceptions import AppBaseError
from src.core.constants import BuiltinProvider
from src.core.logger import setup_logging

# Setup logging FIRST, before importing any modules that might log during initialization
setup_logging()

from src.manager.comic_manager import ComicManager

# IMPORT PROVIDERS TO REGISTER THEM
import src.providers.comicwifi.provider
import structlog

logger = structlog.get_logger(__name__)

def main():
    comic_id = "7e68b404b74ffff98a9b77d4f24abefe"

    logger.info("application_start")

    try:
        # Initialize the generic manager
        manager = ComicManager()
        
        # Check what providers are available
        available = manager.get_available_providers()
        logger.info("available_providers", providers=available)

        # Tell the manager to use the "comicwifi" plugin
        manager.use(BuiltinProvider.COMICWIFI)

        # 1. Fetch Detail (Now returns Standardized Core.Comic Model)
        logger.info(">>> Step 1: Fetching Comic Detail")
        detail = manager.fetch_comic_detail(comic_id)
        print(f"[{manager.provider.provider_name}] Title: {detail.title}")
        print(f"Tags: {', '.join(detail.tags)}")
        print(f"Description: {detail.description}")

        # 2. Fetch Chapters (Standardized Core.Chapter List)
        logger.info(">>> Step 2: Fetching Chapter List")
        chapters = manager.fetch_all_chapters(comic_id)
        print(f"Total Chapters Found: {len(chapters)}")

        if chapters:
            # 3. Fetch First Chapter Images (Standardized Core.PageImage List)
            first_chapter = chapters[0]
            logger.info(">>> Step 3: Fetching Images for First Chapter", chapter_title=first_chapter.title)
            images = manager.fetch_chapter_images(comic_id, first_chapter.id)
            
            print(f"Found {len(images)} images in chapter '{first_chapter.title}'.")
            for img in images:
                print(f"  Page {img.order + 1}: {img.url} ({img.width}x{img.height})")

    except AppBaseError as e:
        logger.error("application_error", error=str(e))
    except Exception as e:
        logger.exception("unexpected_error")
    finally:
        logger.info("application_shutdown")

if __name__ == "__main__":
    main()
