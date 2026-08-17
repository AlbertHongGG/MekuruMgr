import typer
from rich.console import Console

from src.core.config import app_settings
from src.application.user_service import UserService
from src.application.library_service import LibraryService
from src.storage.factory import StorageFactory, StorageEngine
from src.cli.views import user_view

user_app = typer.Typer(help="Manage user preferences, favorites, and reading history")
console = Console()

def get_user_service():
    provider = StorageFactory.get_provider(StorageEngine.JSON)
    library_service = LibraryService(storage=provider.get_archive_storage(), base_media_url="")
    return UserService(user_storage=provider.get_user_storage(), library_service=library_service)

@user_app.command(name="favorites")
def list_favorites():
    """List all your favorite comics."""
    service = get_user_service()
    favorites = service.get_composed_favorites()
    user_view.render_favorites(favorites)

@user_app.command(name="favorite")
def toggle_favorite(
    comic_id: str = typer.Argument(..., help="The ID of the comic to favorite/unfavorite"),
    provider_id: str = typer.Option(None, "--provider", "-p", help="Provider ID. Uses env default if omitted.")
):
    """Toggle the favorite status of a comic."""
    provider_id = provider_id or app_settings.default_provider
    service = get_user_service()
    
    new_status = service.toggle_favorite(provider_id, comic_id)
    if new_status:
        console.print(f"[green]Successfully added[/green] {comic_id} to favorites!")
    else:
        console.print(f"[yellow]Removed[/yellow] {comic_id} from favorites.")

@user_app.command(name="read")
def update_read_progress(
    comic_id: str = typer.Argument(..., help="The ID of the comic"),
    chapter_id: str = typer.Argument(..., help="The ID of the chapter"),
    page: int = typer.Argument(..., help="The page index you are reading"),
    provider_id: str = typer.Option(None, "--provider", "-p", help="Provider ID. Uses env default if omitted.")
):
    """Manually update reading progress for a comic chapter."""
    provider_id = provider_id or app_settings.default_provider
    service = get_user_service()
    
    service.update_reading_progress(provider_id, comic_id, chapter_id, page)
    console.print(f"[green]Reading progress updated![/green] Comic: {comic_id}, Chapter: {chapter_id}, Page: {page}")

@user_app.command(name="status")
def view_interaction(
    comic_id: str = typer.Argument(..., help="The ID of the comic"),
    provider_id: str = typer.Option(None, "--provider", "-p", help="Provider ID. Uses env default if omitted.")
):
    """View full user interaction status for a comic."""
    provider_id = provider_id or app_settings.default_provider
    service = get_user_service()
    
    interaction = service.get_interaction(provider_id, comic_id)
    user_view.render_interaction(interaction)
