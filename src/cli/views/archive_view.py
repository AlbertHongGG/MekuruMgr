from typing import List
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint
from src.domain.models import ArchivedComic, DownloadStatus

def render_track_success(archived: ArchivedComic):
    rprint(Panel(
        f"[green]Successfully tracked![/green]\n"
        f"Title: {archived.title}\n"
        f"Local Path: {archived.local_path}",
        title="[bold]Tracking Complete[/bold]"
    ))

def render_sync_success(archived: ArchivedComic):
    rprint(Panel(
        f"[green]Sync completed![/green]\n"
        f"Title: {archived.title}\n"
        f"Total Tracked Chapters: {len(archived.chapters)}\n"
        f"Local Path: {archived.local_path}",
        title="[bold]Sync Complete[/bold]"
    ))

def render_archive_list(comics: List[ArchivedComic]):
    if not comics:
        rprint("[yellow]No comics found in the local archive.[/yellow]")
        return
        
    table = Table(title="Local Comic Archive", border_style="white")
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
    
def render_delete_success(comic_id: str):
    rprint(f"[green]Successfully deleted archive for comic {comic_id}.[/green]")

def render_error(message: str):
    rprint(f"[bold red]Error:[/] {message}")
