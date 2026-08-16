import typer
from rich.table import Table
from rich.panel import Panel
from rich.console import Console
from rich import print as rprint

from src.core.config import app_settings
from src.application.comic_manager import ComicManager

console = Console()
comic_app = typer.Typer(help="Manage comics (Fetch, Search, etc.)")

@comic_app.command(name="fetch")
def fetch_comic(
    comic_id: str = typer.Argument(
        None, help="The ID of the comic to fetch. Uses env default if omitted."
    ),
    provider_id: str = typer.Option(
        None, "--provider", "-p", help="Provider ID. Uses env default if omitted."
    )
):
    """Fetch and display comic metadata."""
    comic_id = comic_id or app_settings.default_comic_id
    provider_id = provider_id or app_settings.default_provider
    
    if not comic_id:
        rprint("[bold red]Error:[/] No comic ID provided and no default in .env")
        raise typer.Exit(1)

    manager = ComicManager()
    manager.use(provider_id)
    
    with console.status(f"Fetching comic info for {comic_id} from {provider_id}...", spinner="dots"):
        comic = manager.fetch_comic_detail(comic_id)

    panel = Panel(
        f"[bold]Title:[/] {comic.title}\n"
        f"[bold]Author:[/] {comic.author}\n"
        f"[bold]Status:[/] {comic.update_status}\n"
        f"[bold]Tags:[/] {', '.join(comic.tags)}\n"
        f"[bold]Desc:[/] {comic.description[:100]}...\n"
        f"[bold]Cover:[/] {comic.cover_url}",
        title=f"[{manager.provider.provider_name}] Comic Info",
        border_style="green"
    )
    rprint(panel)

@comic_app.command(name="list-chapters")
def list_chapters(
    comic_id: str = typer.Argument(
        None, help="The ID of the comic to fetch. Uses env default if omitted."
    ),
    provider_id: str = typer.Option(
        None, "--provider", "-p", help="Provider ID. Uses env default if omitted."
    )
):
    """Fetch and display all chapters of a comic."""
    comic_id = comic_id or app_settings.default_comic_id
    provider_id = provider_id or app_settings.default_provider
    
    manager = ComicManager()
    manager.use(provider_id)

    with console.status(f"Fetching chapters for {comic_id} from {provider_id}...", spinner="dots"):
        chapters = manager.fetch_all_chapters(comic_id)
        
    table = Table(title=f"[{manager.provider.provider_name}] Chapters for {comic_id}")
    table.add_column("Order", justify="right", style="cyan", no_wrap=True)
    table.add_column("ID", style="magenta")
    table.add_column("Title", style="green")
    table.add_column("Publish Time", style="yellow")
    table.add_column("VIP", justify="center")

    for ch in chapters:
        vip_status = "[red]Yes[/red]" if ch.is_vip else "[green]No[/green]"
        table.add_row(
            str(ch.order), 
            ch.id, 
            ch.title, 
            ch.publish_time, 
            vip_status
        )

    rprint(table)
