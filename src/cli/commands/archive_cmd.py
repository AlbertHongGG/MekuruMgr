import typer
import asyncio
from rich.console import Console

from src.application.comic_manager import ComicManager
from src.application.archive_engine import ArchiveEngine
from src.storage.factory import StorageFactory
from src.cli.views import archive_view
from src.domain.models.archive import TaskStatus
from src.core.registry import registry
from src.domain.exceptions import AppBaseError

archive_app = typer.Typer(help="Manage local comic archives (Track, Sync, Delete, Queue)")
console = Console()



def resolve_provider(container, provider_id: str) -> str:
    provider_id = provider_id or container.config.default_provider
    try:
        return container.comic_manager.resolve_id(provider_id)
    except AppBaseError as e:
        archive_view.render_error(str(e))
        raise typer.Exit(1)
@archive_app.command(name="track")
def track_comic(ctx: typer.Context, 
    comic_id: str = typer.Argument(..., help="The ID of the comic to track."),
    provider_id: str = typer.Option(None, "--provider", "-p", help="Provider ID. Uses env default if omitted.")
):
    """Add a comic to the local tracking library (fetch metadata only)."""
    container = ctx.obj
    provider_id = resolve_provider(container, provider_id)
    
    qs = container.archive_engine
    
    with console.status(f"[cyan]Tracking comic {comic_id} from {provider_id}...[/cyan]", spinner="dots"):
        archived = asyncio.run(qs.track_comic(provider_id, comic_id))
        
    archive_view.render_track_success(archived)

async def _sync_and_wait(qs: ArchiveEngine, provider_id: str, comic_id: str):
    task = await qs.submit_sync(provider_id, comic_id)
    await qs.start()
    
    task_id = f"{provider_id}::{comic_id}"
    
    console.print(f"[cyan]Starting sync for {comic_id}...[/cyan]")
    try:
        while True:
            current = await qs.get_progress(provider_id, comic_id)
            if not current:
                break
                
            if current.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED, TaskStatus.PAUSED]:
                console.print(f"Task finished with status: {current.status.value}")
                if current.error_message:
                    console.print(f"[red]Error: {current.error_message}[/red]")
                break
                
            comp = current.completed_chapters
            tot = current.total_chapters
            console.print(f"Progress: {comp}/{tot} chapters completed...", end="\r")
            
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        await qs.pause_task_async(task_id)
        console.print("\n[yellow]Sync paused by user.[/yellow]")
    finally:
        await qs.stop()

@archive_app.command(name="sync")
def sync_comic(ctx: typer.Context, 
    comic_id: str = typer.Argument(..., help="The ID of the comic to sync."),
    provider_id: str = typer.Option(None, "--provider", "-p", help="Provider ID. Uses env default if omitted.")
):
    """Perform an incremental sync (adds to queue and starts downloading)."""
    container = ctx.obj
    provider_id = resolve_provider(container, provider_id)
    
    qs = container.archive_engine
    
    try:
        asyncio.run(_sync_and_wait(qs, provider_id, comic_id))
    except KeyboardInterrupt:
        asyncio.run(qs.pause_task_async(f"{provider_id}::{comic_id}"))
        console.print("\n[bold yellow]Sync manually paused. Run sync again to resume.[/bold yellow]")

@archive_app.command(name="pause")
def pause_comic(ctx: typer.Context, 
    comic_id: str = typer.Argument(..., help="The ID of the comic to pause."),
    provider_id: str = typer.Option(None, "--provider", "-p", help="Provider ID. Uses env default if omitted.")
):
    """Pause an active sync task."""
    container = ctx.obj
    provider_id = resolve_provider(container, provider_id)
    container = ctx.obj
    qs = container.archive_engine
    success = asyncio.run(qs.pause_task_async(f"{provider_id}::{comic_id}"))
    if success:
        console.print(f"[green]Task paused: {comic_id}[/green]")
    else:
        console.print(f"[red]Task not found or cannot be paused: {comic_id}[/red]")

@archive_app.command(name="resume")
def resume_comic(ctx: typer.Context, 
    comic_id: str = typer.Argument(..., help="The ID of the comic to resume."),
    provider_id: str = typer.Option(None, "--provider", "-p", help="Provider ID. Uses env default if omitted.")
):
    """Resume a paused sync task."""
    container = ctx.obj
    provider_id = resolve_provider(container, provider_id)
    container = ctx.obj
    qs = container.archive_engine
    success = asyncio.run(qs.resume_task_async(f"{provider_id}::{comic_id}"))
    if success:
        console.print(f"[green]Task queued for resume: {comic_id}[/green]")
        console.print("Run 'sync' to start processing or let the server handle it.")
    else:
        console.print(f"[red]Task not found or cannot be resumed: {comic_id}[/red]")

@archive_app.command(name="list")
def list_archives(ctx: typer.Context):
    """List all locally tracked comics."""
    container = ctx.obj
    container = ctx.obj
    qs = container.archive_engine
    comics = asyncio.run(qs.library_storage.list_comics())
    archive_view.render_archive_list(comics)

@archive_app.command(name="queue")
def list_queue(ctx: typer.Context):
    """List all tasks in the download queue."""
    container = ctx.obj
    container = ctx.obj
    qs = container.archive_engine
    tasks = asyncio.run(qs.task_storage.list_tasks())
    archive_view.render_task_list(tasks)

async def _delete_archive(qs: ArchiveEngine, provider_id: str, comic_id: str):
    await qs.library_storage.delete_comic(provider_id, comic_id)
    await qs.media_storage.delete_media(provider_id, comic_id)
    task_id = f"{provider_id}::{comic_id}"
    await qs.cancel_task_async(task_id)
    await qs.task_storage.delete_task(task_id)

@archive_app.command(name="delete")
def delete_archive(ctx: typer.Context, 
    comic_id: str = typer.Argument(..., help="The ID of the comic to delete"),
    provider_id: str = typer.Option(None, "--provider", "-p", help="Provider ID. Uses env default if omitted.")
):
    """Delete a comic from the local archive."""
    container = ctx.obj
    provider_id = resolve_provider(container, provider_id)
    container = ctx.obj
    qs = container.archive_engine
    try:
        asyncio.run(_delete_archive(qs, provider_id, comic_id))
        archive_view.render_delete_success(comic_id)
    except Exception as e:
        archive_view.render_error(str(e))
        raise typer.Exit(1)
