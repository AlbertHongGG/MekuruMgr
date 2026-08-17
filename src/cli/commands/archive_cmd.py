import typer
import asyncio
from rich.console import Console

from src.core.config import app_settings
from src.application.comic_manager import ComicManager
from src.application.archiver_engine import ArchiverEngine
from src.storage.factory import StorageFactory, StorageEngine
from src.cli.views import archive_view
from src.cli.components.progress import RichProgressObserver

archive_app = typer.Typer(help="Manage local comic archives (Track, Sync, Delete)")
console = Console()

def get_archiver():
    manager = ComicManager()
    storage = StorageFactory.get_storage(StorageEngine.JSON)
    return ArchiverEngine(manager, storage)

@archive_app.command(name="track")
def track_comic(
    comic_id: str = typer.Argument(None, help="The ID of the comic to track. Uses env default if omitted."),
    provider_id: str = typer.Option(None, "--provider", "-p", help="Provider ID. Uses env default if omitted.")
):
    """Add a comic to the local tracking library (fetch metadata only)."""
    comic_id = comic_id or app_settings.default_comic_id
    provider_id = provider_id or app_settings.default_provider
    if not comic_id:
        archive_view.render_error("No comic ID provided and no default in .env")
        raise typer.Exit(1)
        
    archiver = get_archiver()
    
    with console.status(f"[cyan]Tracking comic {comic_id} from {provider_id}...[/cyan]", spinner="dots"):
        archived = asyncio.run(archiver.track_comic(provider_id, comic_id))
        
    archive_view.render_track_success(archived)

@archive_app.command(name="sync")
def sync_comic(
    comic_id: str = typer.Argument(None, help="The ID of the comic to sync. Uses env default if omitted."),
    provider_id: str = typer.Option(None, "--provider", "-p", help="Provider ID. Uses env default if omitted.")
):
    """Perform an incremental sync to download missing or failed chapters."""
    comic_id = comic_id or app_settings.default_comic_id
    provider_id = provider_id or app_settings.default_provider
    if not comic_id:
        archive_view.render_error("No comic ID provided and no default in .env")
        raise typer.Exit(1)
        
    archiver = get_archiver()
    console.print(f"[cyan]Starting incremental sync for comic {comic_id} from {provider_id}...[/cyan]")
    
    observer = RichProgressObserver()
    try:
        archived = asyncio.run(archiver.sync_comic(provider_id, comic_id, observer=observer))
    finally:
        observer.progress.stop()
        
    archive_view.render_sync_success(archived)

@archive_app.command(name="list")
def list_archives():
    """List all locally archived comics."""
    storage = StorageFactory.get_storage(StorageEngine.JSON)
    comics = storage.list_comics()
    archive_view.render_archive_list(comics)

@archive_app.command(name="delete")
def delete_archive(
    comic_id: str = typer.Argument(..., help="The ID of the comic to delete"),
    provider_id: str = typer.Option(None, "--provider", "-p", help="Provider ID. Uses env default if omitted.")
):
    """Delete a comic from the local archive."""
    provider_id = provider_id or app_settings.default_provider
    archiver = get_archiver()
    try:
        archiver.delete_archived_comic(provider_id, comic_id)
        archive_view.render_delete_success(comic_id)
    except Exception as e:
        archive_view.render_error(str(e))
        raise typer.Exit(1)
