import typer
from rich.table import Table
from rich.panel import Panel
from rich.console import Console
from rich import print as rprint
from pathlib import Path

from src.core.config import app_settings
from src.application.library_service import LibraryService
from src.storage.factory import StorageFactory, StorageEngine
from src.domain.exceptions import AppBaseError

console = Console()
library_app = typer.Typer(help="Read and access locally downloaded comics")

def get_cli_service() -> LibraryService:
    # For CLI, we return local absolute file paths instead of HTTP URLs.
    # This makes it easy for users to click the paths in their terminal.
    storage = StorageFactory.get_storage(StorageEngine.JSON)
    base_file_url = f"file:///{storage.data_dir.absolute().as_posix()}/"
    return LibraryService(storage=storage, base_media_url=base_file_url)

@library_app.command(name="list")
def list_library():
    """List all available comics in the local library."""
    service = get_cli_service()
    comics = service.list_comics()
    
    if not comics:
        rprint("[yellow]Library is empty. Use 'archive sync' to download comics.[/yellow]")
        return
        
    table = Table(title="Local Comic Library", border_style="blue")
    table.add_column("Provider", style="cyan")
    table.add_column("Comic ID", style="magenta")
    table.add_column("Title", style="green", no_wrap=False)
    table.add_column("Completed Chapters", justify="right")
    
    for c in comics:
        # Hide comics that have no completed chapters yet
        if c.completed_chapters_count > 0:
            table.add_row(
                c.provider_id,
                c.comic_id,
                c.title,
                str(c.completed_chapters_count)
            )
        
    rprint(table)

@library_app.command(name="search")
def search_library(keyword: str = typer.Argument(..., help="Keyword to search in library")):
    """Search for comics in the local library."""
    service = get_cli_service()
    comics = service.search_comics(keyword)
    
    if not comics:
        rprint(f"[yellow]No comics found matching '{keyword}' in the local library.[/yellow]")
        return
        
    table = Table(title=f"Local Search Results: '{keyword}'", border_style="white")
    table.add_column("Provider", style="cyan")
    table.add_column("Comic ID", style="magenta")
    table.add_column("Title", style="green", no_wrap=False)
    table.add_column("Completed Chapters", justify="right")
    
    for c in comics:
        table.add_row(
            c.provider_id,
            c.comic_id,
            c.title,
            str(c.completed_chapters_count)
        )
        
    rprint(table)

@library_app.command(name="show")
def show_library_comic(
    comic_id: str = typer.Argument(..., help="The ID of the comic to show"),
    provider_id: str = typer.Option(
        None, "--provider", "-p", help="Provider ID. Uses env default if omitted."
    )
):
    """Show details and available chapters for a specific comic."""
    provider_id = provider_id or app_settings.default_provider
    service = get_cli_service()
    
    try:
        detail = service.get_comic_detail(provider_id, comic_id)
        chapters = service.get_comic_chapters(provider_id, comic_id)
        
        rprint(Panel(
            f"[bold]Title:[/] {detail.title}\n"
            f"[bold]Tags:[/] {', '.join(detail.tags)}\n"
            f"[bold]Description:[/] {detail.description[:100]}...\n"
            f"[bold]Cover:[/] {detail.cover_url}",
            title="Comic Info",
            border_style="green"
        ))
        
        table = Table(title=f"Completed Chapters ({len(chapters)})", border_style="cyan")
        table.add_column("Chapter ID", style="magenta")
        table.add_column("Title", style="green")
        table.add_column("Pages", justify="right")
        
        for ch in chapters:
            table.add_row(ch.chapter_id, ch.title, str(ch.page_count))
            
        rprint(table)
        
    except AppBaseError as e:
        rprint(f"[bold red]Error:[/] {e}")

@library_app.command(name="read")
def read_library_chapter(
    comic_id: str = typer.Argument(..., help="The ID of the comic"),
    chapter_id: str = typer.Argument(..., help="The ID of the chapter to read"),
    provider_id: str = typer.Option(
        None, "--provider", "-p", help="Provider ID. Uses env default if omitted."
    )
):
    """Get all image paths for a specific chapter."""
    provider_id = provider_id or app_settings.default_provider
    service = get_cli_service()
    
    try:
        chapter_data = service.get_chapter_images(provider_id, comic_id, chapter_id)
        
        rprint(f"[bold cyan]Reading:[/] {chapter_data.title} ({len(chapter_data.images)} pages)")
        for idx, img in enumerate(chapter_data.images, start=1):
            rprint(f"[{idx:03d}] {img}")
            
    except AppBaseError as e:
        rprint(f"[bold red]Error:[/] {e}")
