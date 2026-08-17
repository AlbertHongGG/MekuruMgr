# ComicMgr - Domain-Driven Comic Management Platform

ComicMgr is a modern comic management system built on Domain-Driven Design (DDD) and Hexagonal Architecture principles.
It provides a robust dynamic Provider plugin system, an Incremental Sync engine with resume capability, and a clean segregation of concerns between data archiving and content delivery (CQRS pattern).

## Core Features

*   **Provider Architecture**: Easily extendable to support new comic sources (default support for `comicwifi`).
*   **Storage Abstraction (`IArchiveStorage`)**: Completely decouples storage mechanisms. Switch between Local File System, Database, or AWS S3 without changing any core logic or API code.
*   **Atomic Downloads**: Uses `.tmp` files during downloading and renaming to guarantee absolutely zero corrupted images upon network interruption.
*   **Memory-Safe Media Proxy**: Serves all images using async byte streaming chunking (8KB), guaranteeing OOM (Out Of Memory) immunity even under extreme concurrency.
*   **Incremental Sync Engine**: Downloads only missing or failed chapters to preserve bandwidth and avoid bans.
*   **State Machine Lifecycle**: Tracks chapter states (PENDING, DOWNLOADING, COMPLETED, FAILED) ensuring robust resume capabilities on network failure.
*   **Bounded Contexts**: Strictly separated `archive` (Management/Writing) and `library` (Serving/Reading) domains.
*   **Pydantic V2 Validation**: Uses the latest `TypeAdapter` for strict, safe, and robust JSON array validations from external sources.

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
*   View Archive Health (Shows total downloaded vs pending/failed chapters):
    ```bash
    uv run python cli.py archive list
    ```
*   Delete Archive:
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
*   `GET /api/v1/archive/` : View tracking health status.
*   `GET /api/v1/archive/{provider_id}/{comic_id}` : Get metadata for a specific archived comic.
*   `GET /api/v1/archive/{provider_id}/{comic_id}/progress` : Get real-time detailed sync progress (active chapters and pages downloaded).
*   `POST /api/v1/archive/{provider_id}/{comic_id}/track` : Track without downloading.
*   `POST /api/v1/archive/{provider_id}/{comic_id}/sync` : Trigger background incremental sync.

### Library Serving API (Reading)
*   `GET /api/v1/library/explore` : Explore all locally available comics.
*   `GET /api/v1/library/search?keyword=...` : Search for downloaded comics.
*   `GET /api/v1/library/{provider_id}/{comic_id}` : Get comic details and its COMPLETED chapters.
*   `GET /api/v1/library/{provider_id}/{comic_id}/chapters` : Get only the COMPLETED chapters for a comic.
*   `GET /api/v1/library/{provider_id}/{comic_id}/chapters/{chapter_id}` : Get a list of absolute media proxy URLs for all images in the chapter.

### Media Streaming Proxy (Image Serving)

Once a comic is archived, its images are securely and efficiently streamed (using 8KB chunking) via the media proxy endpoint, ensuring no hard-coupling to the physical filesystem:
```text
GET /api/v1/library/media/{provider_id}/{comic_id}/cover.jpg
GET /api/v1/library/media/{provider_id}/{comic_id}/{chapter_id}/000.jpg
```
