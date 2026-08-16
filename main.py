import sys
import structlog
from src.manager.comic_manager import ComicManager
from src.core.exceptions import AppBaseError

# Setup structlog for clean, readable output
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=False),
        structlog.dev.ConsoleRenderer(
            pad_event_to=0,
            colors=sys.stdout.isatty(),
            exception_formatter=structlog.dev.plain_traceback
        )
    ]
)
logger = structlog.get_logger(__name__)

def main():
    comic_id = "7e68b404b74ffff98a9b77d4f24abefe"

    logger.info("application_start")

    try:
        with ComicManager() as manager:
            # 1. Fetch Detail
            logger.info(">>> Step 1: Fetching Comic Detail")
            detail = manager.fetch_comic_detail(comic_id)
            print(f"Title: {detail.name}")
            print(f"Tags: {', '.join(detail.tags)}")
            print(f"Description: {detail.desc}")

            # 2. Fetch Chapters
            logger.info(">>> Step 2: Fetching Chapter List")
            chapters = manager.fetch_all_chapters(comic_id)
            print(f"Total Chapters Found: {len(chapters)}")

            if chapters:
                # 3. Fetch First Chapter Images
                first_chapter = chapters[0]
                logger.info(">>> Step 3: Fetching Images for First Chapter", chapter_name=first_chapter.chapter_name)
                images = manager.fetch_chapter_images(comic_id, str(first_chapter.chapter_id))
                
                print(f"Found {len(images)} images in chapter '{first_chapter.chapter_name}'.")
                for idx, img in enumerate(images, 1):
                    print(f"  Image {idx}: {img.url} ({img.width}x{img.height})")

    except AppBaseError as e:
        logger.error("application_error", error=str(e))
    except Exception as e:
        logger.exception("unexpected_error")
    finally:
        logger.info("application_shutdown")

if __name__ == "__main__":
    main()
