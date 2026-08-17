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

@comic_app.command(name="search")
def search_comic(
    keyword: str = typer.Argument(..., help="The keyword to search for."),
    page: int = typer.Option(1, help="Page number."),
    page_size: int = typer.Option(30, help="Number of items per page."),
    provider_id: str = typer.Option(
        None, "--provider", "-p", help="Provider ID. Uses env default if omitted."
    )
):
    """Search for comics by keyword."""
    provider_id = provider_id or app_settings.default_provider
    manager = ComicManager()
    manager.use(provider_id)

    with console.status(f"Searching for '{keyword}' from {provider_id}...", spinner="dots"):
        comics = manager.search_comics(keyword, page, page_size)
        
    table = Table(title=f"[{manager.provider.provider_name}] Search Results for '{keyword}'")
    table.add_column("ID", style="magenta")
    table.add_column("Title", style="green")
    table.add_column("Tags", style="yellow")
    
    for c in comics:
        table.add_row(c.id, c.title, ", ".join(c.tags))

    rprint(table)

@comic_app.command(name="list-images")
def list_images(
    comic_id: str = typer.Argument(..., help="The ID of the comic."),
    chapter_id: str = typer.Argument(..., help="The ID of the chapter."),
    provider_id: str = typer.Option(
        None, "--provider", "-p", help="Provider ID. Uses env default if omitted."
    )
):
    """Fetch and display all images of a specific chapter."""
    provider_id = provider_id or app_settings.default_provider
    manager = ComicManager()
    manager.use(provider_id)

    with console.status(f"Fetching images for comic {comic_id}, chapter {chapter_id}...", spinner="dots"):
        images = manager.fetch_chapter_images(comic_id, chapter_id)
        
    table = Table(title=f"[{manager.provider.provider_name}] Images for Chapter {chapter_id}")
    table.add_column("Order", justify="right", style="cyan", no_wrap=True)
    table.add_column("URL", style="green")
    
    for img in images:
        table.add_row(str(img.order), img.url)

    rprint(table)

@comic_app.command(name="explore")
def explore_comic(
    page: int = typer.Option(1, help="Page number."),
    page_size: int = typer.Option(30, help="Number of items per page."),
    provider_id: str = typer.Option(
        None, "--provider", "-p", help="Provider ID. Uses env default if omitted."
    )
):
    """Explore/discover comics from the provider."""
    provider_id = provider_id or app_settings.default_provider
    manager = ComicManager()
    manager.use(provider_id)

    with console.status(f"Exploring comics from {provider_id}...", spinner="dots"):
        comics = manager.explore_comics(page, page_size)
        
    table = Table(
        title=f"[{manager.provider.provider_name}] Explore Results",
        border_style="white"
    )
    table.add_column("ID", style="magenta")
    table.add_column("Title", style="green")
    table.add_column("Tags", style="yellow")
    
    for c in comics:
        table.add_row(c.id, c.title, ", ".join(c.tags))

    rprint(table)
