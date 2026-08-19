import typer
from rich.console import Console

from src.core.config import app_settings
from src.application.comic_manager import ComicManager
from src.cli.views import comic_view

console = Console()
comic_app = typer.Typer(help="Manage comics (Fetch, Search, Explore, etc.)")

def get_manager(provider_id: str) -> ComicManager:
    manager = ComicManager()
    manager.use(provider_id)
    return manager

@comic_app.command(name="fetch")
def fetch_comic(
    comic_id: str = typer.Argument(None, help="The ID of the comic to fetch. Uses env default if omitted."),
    provider_id: str = typer.Option(None, "--provider", "-p", help="Provider ID. Uses env default if omitted.")
):
    """Fetch and display comic metadata."""
    comic_id = comic_id or app_settings.default_comic_id
    provider_id = provider_id or app_settings.default_provider
    if not comic_id:
        console.print("[bold red]Error:[/] No comic ID provided and no default in .env")
        raise typer.Exit(1)

    manager = get_manager(provider_id)
    with console.status(f"Fetching comic info for {comic_id} from {provider_id}...", spinner="dots"):
        comic = manager.fetch_comic_detail(comic_id)

    comic_view.render_comic_detail(manager.provider.provider_name, comic)

@comic_app.command(name="list-chapters")
def list_chapters(
    comic_id: str = typer.Argument(None, help="The ID of the comic to fetch. Uses env default if omitted."),
    provider_id: str = typer.Option(None, "--provider", "-p", help="Provider ID. Uses env default if omitted.")
):
    """Fetch and display all chapters of a comic."""
    comic_id = comic_id or app_settings.default_comic_id
    provider_id = provider_id or app_settings.default_provider
    
    manager = get_manager(provider_id)
    with console.status(f"Fetching chapters for {comic_id} from {provider_id}...", spinner="dots"):
        chapters = manager.fetch_all_chapters(comic_id)
        
    comic_view.render_chapters_list(manager.provider.provider_name, comic_id, chapters)

@comic_app.command(name="search")
def search_comic(
    keyword: str = typer.Argument(..., help="The keyword to search for."),
    page: int = typer.Option(1, help="Page number."),
    page_size: int = typer.Option(30, help="Number of items per page."),
    provider_id: str = typer.Option(None, "--provider", "-p", help="Provider ID. Uses env default if omitted.")
):
    """Search for comics by keyword."""
    provider_id = provider_id or app_settings.default_provider
    manager = get_manager(provider_id)

    with console.status(f"Searching for '{keyword}' from {provider_id}...", spinner="dots"):
        search_results = manager.search_comics(keyword, page, page_size)
        comics = []
        for res in search_results:
            try:
                detail = manager.fetch_comic_detail(res.id)
                comics.append(detail)
            except Exception as e:
                console.print(f"[yellow]Warning:[/] Failed to fetch detail for {res.id}: {e}")
        
    title = f"[{manager.provider.provider_name}] Search Results for '{keyword}'"
    comic_view.render_comic_list(title, comics)

@comic_app.command(name="list-images")
def list_images(
    comic_id: str = typer.Argument(..., help="The ID of the comic."),
    chapter_id: str = typer.Argument(..., help="The ID of the chapter."),
    provider_id: str = typer.Option(None, "--provider", "-p", help="Provider ID. Uses env default if omitted.")
):
    """Fetch and display all images of a specific chapter."""
    provider_id = provider_id or app_settings.default_provider
    manager = get_manager(provider_id)

    with console.status(f"Fetching images for comic {comic_id}, chapter {chapter_id}...", spinner="dots"):
        images = manager.fetch_chapter_images(comic_id, chapter_id)
        
    comic_view.render_images_list(manager.provider.provider_name, chapter_id, images)

@comic_app.command(name="explore")
def explore_comic(
    page: int = typer.Option(1, help="Page number."),
    page_size: int = typer.Option(30, help="Number of items per page."),
    provider_id: str = typer.Option(None, "--provider", "-p", help="Provider ID. Uses env default if omitted.")
):
    """Explore/discover comics from the provider."""
    provider_id = provider_id or app_settings.default_provider
    manager = get_manager(provider_id)

    with console.status(f"Exploring comics from {provider_id}...", spinner="dots"):
        search_results = manager.explore_comics(page, page_size)
        comics = []
        for res in search_results:
            try:
                detail = manager.fetch_comic_detail(res.id)
                comics.append(detail)
            except Exception as e:
                console.print(f"[yellow]Warning:[/] Failed to fetch detail for {res.id}: {e}")
        
    title = f"[{manager.provider.provider_name}] Explore Results"
    comic_view.render_comic_list(title, comics)
