import typer
import asyncio

from src.core.config import app_settings
from src.application.library_service import LibraryService
from src.storage.factory import StorageFactory
from src.domain.exceptions import AppBaseError
from src.cli.views import library_view
from src.core.registry import registry
from rich import print as rprint

library_app = typer.Typer(help="Read and access locally downloaded comics")

def get_cli_service() -> LibraryService:
    provider = StorageFactory.get_provider()
    media_storage = provider.get_media_storage()
    base_file_url = f"file:///{media_storage.data_dir.absolute().as_posix()}/"
    return LibraryService(
        library_storage=provider.get_library_storage(),
        task_storage=provider.get_task_storage(),
        media_storage=media_storage,
        base_media_url=base_file_url
    )

def resolve_provider(provider_id: str) -> str:
    provider_id = provider_id or app_settings.default_provider
    try:
        return registry.resolve_id(provider_id)
    except AppBaseError as e:
        rprint(f"[bold red]Error:[/] {e}")
        raise typer.Exit(1)

@library_app.command(name="explore")
def explore_library():
    """Explore all available comics in the local library."""
    service = get_cli_service()
    comics = asyncio.run(service.list_comics())
    library_view.render_library_list(comics)

@library_app.command(name="search")
def search_library(keyword: str = typer.Argument(..., help="Keyword to search in library")):
    """Search for comics in the local library."""
    service = get_cli_service()
    comics = asyncio.run(service.search_comics(keyword))
    library_view.render_library_list(comics, title=f"Local Search Results: '{keyword}'")

async def _show_library_comic(service: LibraryService, provider_id: str, comic_id: str):
    try:
        detail = await service.get_comic_detail(provider_id, comic_id)
        chapters = await service.get_comic_chapters(provider_id, comic_id)
        library_view.render_library_detail(detail, chapters)
    except AppBaseError as e:
        rprint(f"[bold red]Error:[/] {e}")

@library_app.command(name="show")
def show_library_comic(
    comic_id: str = typer.Argument(..., help="The ID of the comic to show"),
    provider_id: str = typer.Option(None, "--provider", "-p", help="Provider ID. Uses env default if omitted.")
):
    """Show details and available chapters for a specific comic."""
    provider_id = resolve_provider(provider_id)
    service = get_cli_service()
    asyncio.run(_show_library_comic(service, provider_id, comic_id))

@library_app.command(name="read")
def read_library_chapter(
    comic_id: str = typer.Argument(..., help="The ID of the comic"),
    chapter_id: str = typer.Argument(..., help="The ID of the chapter to read"),
    provider_id: str = typer.Option(None, "--provider", "-p", help="Provider ID. Uses env default if omitted.")
):
    """Get all image paths for a specific chapter."""
    provider_id = resolve_provider(provider_id)
    service = get_cli_service()
    
    async def _read():
        try:
            chapter_data = await service.get_chapter_images(provider_id, comic_id, chapter_id)
            library_view.render_chapter_read(chapter_data)
        except AppBaseError as e:
            rprint(f"[bold red]Error:[/] {e}")
            
    asyncio.run(_read())
