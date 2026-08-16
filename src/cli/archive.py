import typer
import asyncio
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from src.core.config import app_settings
from src.application.comic_manager import ComicManager
from src.application.archiver_engine import ArchiverEngine
from src.storage.factory import StorageFactory, StorageEngine
from src.domain.models import DownloadStatus

archive_app = typer.Typer(help="Manage local comic archives (Track, Sync, Delete)")

def get_archiver():
    manager = ComicManager()
    return ArchiverEngine(manager)

@archive_app.command(name="track")
def track_comic(
    comic_id: str = typer.Argument(
        None, help="The ID of the comic to track. Uses env default if omitted."
    ),
    provider_id: str = typer.Option(
        None, "--provider", "-p", help="Provider ID. Uses env default if omitted."
    )
):
    """Add a comic to the local tracking library (fetch metadata only)."""
    comic_id = comic_id or app_settings.default_comic_id
    provider_id = provider_id or app_settings.default_provider
    
    if not comic_id:
        rprint("[bold red]Error:[/] No comic ID provided and no default in .env")
        raise typer.Exit(1)
        
    archiver = get_archiver()
    
    rprint(f"[cyan]Tracking comic {comic_id} from {provider_id}...[/cyan]")
    archived = asyncio.run(archiver.track_comic(provider_id, comic_id))
    
    rprint(Panel(
        f"[green]Successfully tracked![/green]\n"
        f"Title: {archived.title}\n"
        f"Local Path: {archived.local_path}",
        title="[bold]Tracking Complete[/bold]"
    ))

@archive_app.command(name="sync")
def sync_comic(
    comic_id: str = typer.Argument(
        None, help="The ID of the comic to sync. Uses env default if omitted."
    ),
    provider_id: str = typer.Option(
        None, "--provider", "-p", help="Provider ID. Uses env default if omitted."
    )
):
    """Perform an incremental sync to download missing or failed chapters."""
    comic_id = comic_id or app_settings.default_comic_id
    provider_id = provider_id or app_settings.default_provider
    
    if not comic_id:
        rprint("[bold red]Error:[/] No comic ID provided and no default in .env")
        raise typer.Exit(1)
        
    archiver = get_archiver()
    
    rprint(f"[cyan]Starting incremental sync for comic {comic_id} from {provider_id}...[/cyan]")
    archived = asyncio.run(archiver.sync_comic(provider_id, comic_id))
    
    rprint(Panel(
        f"[green]Sync completed![/green]\n"
        f"Title: {archived.title}\n"
        f"Total Tracked Chapters: {len(archived.chapters)}\n"
        f"Local Path: {archived.local_path}",
        title="[bold]Sync Complete[/bold]"
    ))

@archive_app.command(name="list")
def list_archives():
    """List all locally archived comics."""
    storage = StorageFactory.get_storage(StorageEngine.JSON)
    comics = storage.list_comics()
    
    if not comics:
        rprint("[yellow]No comics found in the local archive.[/yellow]")
        return
        
    table = Table(title="Local Comic Archive")
    table.add_column("Provider", style="cyan")
    table.add_column("Comic ID", style="magenta")
    table.add_column("Title", style="green")
    table.add_column("Downloaded", justify="right")
    table.add_column("Pending/Failed", justify="right")
    table.add_column("Local Path", style="dim")
    
    for c in comics:
        completed = sum(1 for ch in c.chapters.values() if ch.status == DownloadStatus.COMPLETED)
        pending = len(c.chapters) - completed
        
        table.add_row(
            c.provider_id,
            c.comic_id,
            c.title,
            str(completed),
            f"[yellow]{pending}[/yellow]" if pending > 0 else "0",
            c.local_path
        )
        
    rprint(table)

@archive_app.command(name="delete")
def delete_archive(
    comic_id: str = typer.Argument(..., help="The ID of the comic to delete"),
    provider_id: str = typer.Option(
        None, "--provider", "-p", help="Provider ID. Uses env default if omitted."
    )
):
    """Delete a comic from the local archive."""
    provider_id = provider_id or app_settings.default_provider
    archiver = get_archiver()
    
    try:
        archiver.delete_archived_comic(provider_id, comic_id)
        rprint(f"[green]Successfully deleted archive for comic {comic_id}.[/green]")
    except Exception as e:
        rprint(f"[bold red]Error:[/] {str(e)}")
        raise typer.Exit(1)
