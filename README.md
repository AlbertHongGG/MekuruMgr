# ComicMgr - Domain-Driven Comic Management Platform

ComicMgr is a modern comic management system built on Domain-Driven Design (DDD) and Hexagonal Architecture principles.
It provides a robust dynamic Provider plugin system, an Incremental Sync engine with resume capability, and a clean segregation of concerns between data archiving and content delivery (CQRS pattern).

## Core Features

*   **Provider Architecture**: Easily extendable to support new comic sources (default support for `comicwifi`).
*   **Storage Abstraction (`IArchiveStorage`)**: Completely decouples storage mechanisms. Switch between Local File System, Database, or AWS S3 without changing any core logic or API code.
*   **Atomic Downloads**: Uses `.tmp` files during downloading and renaming to guarantee absolutely zero corrupted images upon network interruption.
*   **Memory-Safe Media Proxy**: Serves all images using async byte streaming chunking (8KB), guaranteeing OOM (Out Of Memory) immunity even under extreme concurrency.
*   **Global Task Management**: Robust async background task orchestrator with Graceful Shutdown (interrupt-safe), global download concurrency limits, and Task Idempotence (prevents duplicate syncing).
*   **Incremental Sync Engine**: Downloads only missing or failed chapters to preserve bandwidth and avoid bans.
*   **State Machine Lifecycle**: Tracks chapter states (PENDING, DOWNLOADING, COMPLETED, FAILED) ensuring robust resume capabilities on network failure.
*   **Bounded Contexts**: Strictly separated `archive` (Management/Writing), `library` (Serving/Reading), and `user` (Personalization/History) domains.
*   **Storage Abstract Factory Pattern**: The `StorageProvider` pattern strictly isolates storage mechanisms (JSON, SQLite) from domain repositories (`ArchiveRepo`, `UserRepo`). 
*   **CQRS Data Projection**: The `UserService` perfectly aggregates physical file status from the Library with personal reading metadata into unified models (`UserLibraryItem`), serving pristine data straight to the Frontend.
*   **Pydantic V2 Validation**: Uses the latest `TypeAdapter` for strict, safe, and robust JSON array validations from external sources.

---

## Adding a New Provider

ComicMgr's dynamic Provider plugin system allows you to easily integrate new comic sources. To add a new provider, you need to create a class that inherits from `BaseComicProvider` located in `src/core/provider.py`. 

Your provider class must implement the following properties and API interfaces to ensure standard domain models are returned:

### Required Properties
*   `provider_id` (str): A unique identifier for your provider (e.g., `'comicwifi'`).
*   `provider_name` (str): A human-readable name for your provider (e.g., `'ComicWifi Official'`).

### Required API Interfaces

*   **`get_comic_detail(comic_id: str) -> Comic`**
    Fetches basic metadata for a specific comic. This includes title, author, description, and cover image URL.
    
*   **`get_chapter_list(comic_id: str) -> List[Chapter]`**
    Fetches the list of all available chapters for a specific comic.

*   **`get_chapter_images(comic_id: str, chapter_id: str) -> List[PageImage]`**
    Fetches the actual image pages (URLs or paths) for a specific chapter.

*   **`search_comics(keyword: str, page: int = 1, page_size: int = 30) -> List[Comic]`**
    Performs a search based on a keyword and returns a paginated list of matching comics.

*   **`explore_comics(page: int = 1, page_size: int = 30) -> List[Comic]`**
    Returns a paginated list of comics for the discovery/explore page.

### Example Provider Skeleton

```python
from typing import List
from src.core.provider import BaseComicProvider
from src.domain.models import Comic, Chapter, PageImage

class MyCustomProvider(BaseComicProvider):
    @property
    def provider_id(self) -> str:
        return "my_custom_provider"

    @property
    def provider_name(self) -> str:
        return "My Custom Provider"

    def get_comic_detail(self, comic_id: str) -> Comic:
        # Implementation to fetch metadata
        pass

    def get_chapter_list(self, comic_id: str) -> List[Chapter]:
        # Implementation to fetch chapters
        pass

    def get_chapter_images(self, comic_id: str, chapter_id: str) -> List[PageImage]:
        # Implementation to fetch images
        pass

    def search_comics(self, keyword: str, page: int = 1, page_size: int = 30) -> List[Comic]:
        # Implementation to search comics
        pass

    def explore_comics(self, page: int = 1, page_size: int = 30) -> List[Comic]:
        # Implementation to discover comics
        pass
```

---

## Installation & Setup

This project uses `uv` for fast dependency management.

1. Clone and enter the directory:
   ```bash
   git clone <your_repo_url>
   cd ComicMgr
   ```

2. Configure environment:
   ```bash
   cp .env.example .env
   ```
   *Tip: Set `DEFAULT_PROVIDER=comicwifi` in `.env` to omit the `-p` parameter in CLI commands.*

3. Install dependencies:
   ```bash
   uv sync
   ```

---

## CLI Usage

The CLI interface provides three primary command groups: `comic` (remote fetching), `archive` (management), and `library` (reading).

### Remote Fetching (comic)

*   Explore Comics (Discover popular comics):
    ```bash
    uv run python cli.py comic explore
    # With parameters:
    uv run python cli.py comic explore --page 2 --page-size 50
    ```
*   Search Comics:
    ```bash
    uv run python cli.py comic search "keyword"
    ```
*   Fetch Comic Metadata:
    ```bash
    uv run python cli.py comic fetch <comic_id>
    ```
*   List All Remote Chapters:
    ```bash
    uv run python cli.py comic list-chapters <comic_id>
    ```
*   List All Remote Chapter Images:
    ```bash
    uv run python cli.py comic list-images <comic_id> <chapter_id>
    ```

### Archival Management (archive)

*   Track a Comic (Fetches metadata only, creates database entry):
    ```bash
    uv run python cli.py archive track <comic_id>
    ```
*   Incremental Sync (Downloads missing or failed chapters automatically):
    ```bash
    uv run python cli.py archive sync <comic_id>
    ```
*   Pause an Active Sync Task:
    ```bash
    uv run python cli.py archive pause <comic_id>
    ```
*   Resume a Paused Sync Task:
    ```bash
    uv run python cli.py archive resume <comic_id>
    ```
*   View All Tracked Comics in Archive:
    ```bash
    uv run python cli.py archive list
    ```
*   View Download Task Queue:
    ```bash
    uv run python cli.py archive queue
    ```
*   Delete Archive (Removes all local files and metadata):
    ```bash
    uv run python cli.py archive delete <comic_id>
    ```

### Library Access (library)

*   Explore Local Library (Clean view of readable comics):
    ```bash
    uv run python cli.py library explore
    ```
*   Search Local Library:
    ```bash
    uv run python cli.py library search "keyword"
    ```
*   Show Comic Details (Lists only fully completed chapters):
    ```bash
    uv run python cli.py library show <comic_id>
    ```
*   Read Chapter (Outputs absolute paths for all images in a chapter):
    ```bash
    uv run python cli.py library read <comic_id> <chapter_id>
    ```

### User Management (user)

*   List Favorite Comics (Projected with library metadata):
    ```bash
    uv run python cli.py user favorites
    ```
*   Toggle Favorite Status:
    ```bash
    uv run python cli.py user favorite <comic_id>
    ```
*   Update Chapter Reading Progress:
    ```bash
    uv run python cli.py user read <comic_id> <chapter_id> <page_index>
    ```
*   View User Interaction Status for a Comic:
    ```bash
    uv run python cli.py user status <comic_id>
    ```

---

## Server API

Start the FastAPI server to serve the API:

```bash
uv run uvicorn server:app --reload --host 127.0.0.1 --port 8000
```

### Remote API (Proxy)
*   `GET /api/v1/comics/{provider_id}/explore?page=1&page_size=30`
*   `GET /api/v1/comics/{provider_id}/search?keyword=...&page=1&page_size=30`
*   `GET /api/v1/comics/{provider_id}/{comic_id}`
*   `GET /api/v1/comics/{provider_id}/{comic_id}/chapters`
*   `GET /api/v1/comics/{provider_id}/{comic_id}/chapters/{chapter_id}/images`

### Archival Management API (Writing)
*   `GET /api/v1/archive/` : List all locally tracked comics metadata.
*   `GET /api/v1/archive/queue` : Get a list of all active download tasks in the background queue. Includes `comic_title` and `cover_url` for UI display.
*   `GET /api/v1/archive/{provider_id}/{comic_id}` : Get metadata for a specific tracked comic.
*   `GET /api/v1/archive/{provider_id}/{comic_id}/progress` : Get real-time detailed sync progress (task status, active chapters, and downloaded pages).
*   `POST /api/v1/archive/{provider_id}/{comic_id}/track` : Add a comic to the tracking library without downloading chapters.
*   `POST /api/v1/archive/{provider_id}/{comic_id}/sync` : Trigger idempotent background incremental sync (queues for download).
*   `POST /api/v1/archive/{provider_id}/{comic_id}/pause` : Pause an active background sync task.
*   `POST /api/v1/archive/{provider_id}/{comic_id}/resume` : Resume a paused background sync task.
*   `DELETE /api/v1/archive/{provider_id}/{comic_id}/cancel` : Gracefully cancel an active background sync task.
*   `DELETE /api/v1/archive/{provider_id}/{comic_id}` : Delete an archived comic and all its downloaded local files.

### Library Serving API (Reading)
*   `GET /api/v1/library/explore` : Explore all locally available comics.
*   `GET /api/v1/library/search?keyword=...` : Search for downloaded comics.
*   `GET /api/v1/library/{provider_id}/{comic_id}` : Get comic details and its COMPLETED chapters.
*   `GET /api/v1/library/{provider_id}/{comic_id}/chapters` : Get only the COMPLETED chapters for a comic.
*   `GET /api/v1/library/{provider_id}/{comic_id}/chapters/{chapter_id}` : Get a list of absolute media proxy URLs for all images in the chapter.

### User Profile API (History & Preferences)
*   `GET /api/v1/user/favorites` : Get a combined list of favorite comics and their library completion status.
*   `GET /api/v1/user/interactions/{provider_id}/{comic_id}` : Get the complete interaction status (favorites, reading history) for a specific comic.
*   `POST /api/v1/user/interactions/{provider_id}/{comic_id}/favorite` : Toggle favorite status.
*   `POST /api/v1/user/interactions/{provider_id}/{comic_id}/read` : Update reading progress for a specific chapter and page.

### Media Streaming Proxy (Image Serving)

Once a comic is archived, its images are securely and efficiently streamed (using 8KB chunking) via the media proxy endpoint, ensuring no hard-coupling to the physical filesystem:
```text
GET /api/v1/library/media/{provider_id}/{comic_id}/cover.jpg
GET /api/v1/library/media/{provider_id}/{comic_id}/{chapter_id}/000.jpg
```

## Testing

To run the automated test suite and generate manual inspection logs, run:

```bash
uv run pytest tests/e2e
```

### Important Testing Information

*   **Test Outputs**: All test results and raw API packets are generated in the `test_outputs/` directory.
    *   **CLI Tests**: Output is stored in `test_outputs/cli/<provider_name>/`.
    *   **Server Tests**: Output is stored in `test_outputs/server/<provider_name>/`.
*   **Auto-Cleaning**: The `test_outputs/` directory is automatically cleared at the beginning of each test run, ensuring no stale data remains.
*   **Packet Sniffing**: Tests will automatically intercept and save the raw JSON responses from remote Provider APIs into the provider's respective `cli` or `server` output directory. This is useful for manually verifying the actual data returned by the source without needing a proxy.