from typing import List
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint
from src.domain.models.archive import LibraryComic, DownloadTask, TaskStatus

def render_track_success(comic: LibraryComic):
    author_str = comic.author if comic.author else "N/A"
    rprint(Panel(
        f"[green]Successfully tracked![/green]\n"
        f"Title: {comic.title}\n"
        f"Author: {author_str}\n"
        f"Local Path: {comic.local_path}",
        title="[bold]Tracking Complete[/bold]"
    ))

def render_sync_success(comic: LibraryComic):
    rprint(Panel(
        f"[green]Sync queued and tracking metadata saved![/green]\n"
        f"Title: {comic.title}\n"
        f"Local Path: {comic.local_path}",
        title="[bold]Sync Queued[/bold]"
    ))

def render_archive_list(comics: List[LibraryComic]):
    if not comics:
        rprint("[yellow]No comics found in the local library.[/yellow]")
        return
        
    table = Table(title="Local Comic Library", border_style="white")
    table.add_column("Provider", style="cyan")
    table.add_column("Comic ID", style="magenta")
    table.add_column("Title", style="green")
    table.add_column("Local Path", style="dim")
    
    for c in comics:
        table.add_row(
            c.provider_id,
            c.comic_id,
            c.title,
            c.local_path
        )
        
    rprint(table)

def render_task_list(tasks: List[DownloadTask]):
    if not tasks:
        rprint("[yellow]No tasks in the download queue.[/yellow]")
        return
        
    table = Table(title="Download Task Queue", border_style="white")
    table.add_column("Provider", style="cyan")
    table.add_column("Comic ID", style="magenta")
    table.add_column("Status", style="bold")
    table.add_column("Progress (Chapters)", justify="right")
    table.add_column("Progress (Pages)", justify="right")
    
    for t in tasks:
        status_color = {
            TaskStatus.QUEUED: "yellow",
            TaskStatus.DOWNLOADING: "blue",
            TaskStatus.PAUSED: "magenta",
            TaskStatus.COMPLETED: "green",
            TaskStatus.FAILED: "red",
            TaskStatus.CANCELLED: "dim"
        }.get(t.status, "white")
        
        # Calculate total pages across all chapters
        total_pages = sum(c.total_pages for c in t.chapters.values())
        downloaded_pages = sum(c.downloaded_pages for c in t.chapters.values())
        page_progress = f"{downloaded_pages}/{total_pages}" if total_pages > 0 else "N/A"
        
        table.add_row(
            t.provider_id,
            t.comic_id,
            f"[{status_color}]{t.status.value}[/{status_color}]",
            f"{t.completed_chapters}/{t.total_chapters}",
            page_progress
        )
        
    rprint(table)
    
def render_delete_success(comic_id: str):
    rprint(f"[green]Successfully deleted archive for comic {comic_id}.[/green]")

def render_error(message: str):
    rprint(f"[bold red]Error:[/] {message}")
