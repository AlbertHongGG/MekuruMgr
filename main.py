import os
import sys
import structlog
from src.core.http_client import BaseHttpClient
from src.core.auth import DummySigner
from src.client.api import ComicApiClient
from src.core.exceptions import AppBaseError, NetworkError

# Setup structlog for clean, readable output (V2 Requirements)
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
    base_url = os.getenv("COMIC_API_BASE_URL", "https://api.comicwifi.com")
    comic_id = "7e68b404b74ffff98a9b77d4f24abefe"

    logger.info("application_start", base_url=base_url)

    signer = DummySigner()
    http_client = BaseHttpClient(base_url=base_url, signer=signer)
    api = ComicApiClient(http_client=http_client)

    try:
        logger.info(">>> Fetching Comic Detail")
        detail = api.get_comic_detail(comic_id=comic_id)
        print(f"Detail Retrieved: {detail.name}")

        logger.info(">>> Fetching Chapter List")
        chapter_list = api.get_chapter_list(comic_id=comic_id)
        print(f"Found {len(chapter_list.chapters)} chapters.")

        if chapter_list.chapters:
            first_chapter_id = chapter_list.chapters[0].chapter_id
            logger.info(">>> Fetching Images for Chapter", chapter_id=first_chapter_id)
            read_data = api.get_chapter_images(comic_id=comic_id, chapter_id=first_chapter_id)
            print(f"Found {len(read_data.imgs)} images.")

    except NetworkError as e:
        # V2: Catch explicit network errors cleanly without dumping tracebacks
        logger.error("network_failure_after_retries", error=str(e))
    except AppBaseError as e:
        # V2: Catch explicit API logic errors (like sign validation failed)
        logger.error("api_logic_error", error=str(e))
    except Exception as e:
        # Only dump traceback for truly unexpected runtime exceptions
        logger.exception("unexpected_system_crash")
    finally:
        http_client.close()
        logger.info("application_shutdown")

if __name__ == "__main__":
    main()
