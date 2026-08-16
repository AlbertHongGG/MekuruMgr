import typer
import structlog
from typing import Optional
from rich import print as rprint
from rich.panel import Panel
from rich.table import Table

from src.core.config import app_settings
from src.core.constants import BuiltinProvider
from src.manager.comic_manager import ComicManager
from src.core.exceptions import AppBaseError

logger = structlog.get_logger(__name__)
app = typer.Typer(help="Comic data fetching commands")

def get_manager(provider_id: Optional[str] = None) -> ComicManager:
    provider = provider_id or app_settings.default_provider
    try:
        provider = BuiltinProvider(provider)
    except ValueError:
        pass
    return ComicManager(provider)

@app.command("fetch")
def fetch_comic(
    comic_id: str = typer.Argument(None, help="The ID of the comic"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="Specific plugin provider ID to use")
):
    """Fetch basic details of a comic and print them to the console."""
    if not comic_id:
        comic_id = app_settings.default_comic_id
        rprint(f"[yellow]No comic ID provided, using default from .env:[/yellow] {comic_id}")
    
    manager = get_manager(provider)
    try:
        detail = manager.fetch_comic_detail(comic_id)
        content = f"[bold cyan]Title:[/bold cyan] {detail.title}\n"
        content += f"[bold cyan]Tags:[/bold cyan] {', '.join(detail.tags)}\n"
        content += f"[bold cyan]Description:[/bold cyan] {detail.description}"
        rprint(Panel(content, title=f"[{manager.provider.provider_name}] Comic Info", border_style="green"))
    except AppBaseError as e:
        rprint(f"[bold red]Error:[/bold red] {e}")

@app.command("list-chapters")
def list_chapters(
    comic_id: str = typer.Argument(None, help="The ID of the comic"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="Specific plugin provider ID to use")
):
    """Fetch all chapters of a comic and present them in a table."""
    if not comic_id:
        comic_id = app_settings.default_comic_id
    
    manager = get_manager(provider)
    try:
        chapters = manager.fetch_all_chapters(comic_id)
        table = Table(title=f"Chapters for {comic_id}")
        table.add_column("Order", justify="right", style="cyan", no_wrap=True)
        table.add_column("Chapter ID", style="magenta")
        table.add_column("Title", style="green")
        
        for ch in chapters:
            table.add_row(str(ch.order), ch.id, ch.title)
            
        rprint(table)
    except AppBaseError as e:
        rprint(f"[bold red]Error:[/bold red] {e}")
