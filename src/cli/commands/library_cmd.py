import typer
import asyncio
from pathlib import Path
import urllib.parse
from rich import print as rprint

from src.core.interfaces import ILibraryService, IComicManager
from src.core.container import AppContainer
from src.domain.exceptions import AppBaseError
from src.cli.views import library_view

library_app = typer.Typer(help="Read and access locally downloaded comics")

def resolve_provider(container: AppContainer, provider_id: str) -> str:
    provider_id = provider_id or container.config.default_provider
    try:
        return container.comic_manager.resolve_id(provider_id)
    except AppBaseError as e:
        rprint(f"[bold red]Error:[/] {e}")
        raise typer.Exit(1)

def _format_cover(container: AppContainer, cover_url: str) -> str:
    if not cover_url or cover_url.startswith("http"):
        return cover_url
    data_dir_path = Path(container.config.storage.data_dir).absolute().as_posix()
    base_url = f"file:///{data_dir_path}/"
    parts = cover_url.split('/')
    encoded_parts = [urllib.parse.quote(p) for p in parts]
    return base_url + "/".join(encoded_parts)

@library_app.command(name="explore")
def explore_library(ctx: typer.Context):
    """Explore all available comics in the local library."""
    container = ctx.obj
    container: AppContainer = ctx.obj
    service: ILibraryService = container.library_service
    comics = asyncio.run(service.list_comics())
    for c in comics:
        c.cover_url = _format_cover(container, c.cover_url)
    library_view.render_library_list(comics)

@library_app.command(name="search")
def search_library(ctx: typer.Context, keyword: str = typer.Argument(..., help="Keyword to search in library")
):
    """Search for comics in the local library."""
    container = ctx.obj
    container: AppContainer = ctx.obj
    service: ILibraryService = container.library_service
    comics = asyncio.run(service.search_comics(keyword))
    for c in comics:
        c.cover_url = _format_cover(container, c.cover_url)
    library_view.render_library_list(comics, title=f"Local Search Results: '{keyword}'")

async def _show_library_comic(container: AppContainer, service: ILibraryService, provider_id: str, comic_id: str):
    try:
        detail = await service.get_comic_detail(provider_id, comic_id)
        detail.cover_url = _format_cover(container, detail.cover_url)
        chapters = await service.get_comic_chapters(provider_id, comic_id)
        library_view.render_library_detail(detail, chapters)
    except AppBaseError as e:
        rprint(f"[bold red]Error:[/] {e}")

@library_app.command(name="show")
def show_library_comic(ctx: typer.Context, 
    comic_id: str = typer.Argument(..., help="The ID of the comic to show"),
    provider_id: str = typer.Option(None, "--provider", "-p", help="Provider ID. Uses env default if omitted.")
):
    """Show details and available chapters for a specific comic."""
    container = ctx.obj
    container: AppContainer = ctx.obj
    provider_id = resolve_provider(container, provider_id)
    service: ILibraryService = container.library_service
    asyncio.run(_show_library_comic(container, service, provider_id, comic_id))

@library_app.command(name="read")
def read_library_chapter(ctx: typer.Context, 
    comic_id: str = typer.Argument(..., help="The ID of the comic"),
    chapter_id: str = typer.Argument(..., help="The ID of the chapter to read"),
    provider_id: str = typer.Option(None, "--provider", "-p", help="Provider ID. Uses env default if omitted.")
):
    """Get all image paths for a specific chapter."""
    container = ctx.obj
    container: AppContainer = ctx.obj
    provider_id = resolve_provider(container, provider_id)
    service: ILibraryService = container.library_service
    
    async def _read():
        try:
            chapter_data = await service.get_chapter_images(provider_id, comic_id, chapter_id)
            
            data_dir_path = Path(container.config.storage.data_dir).absolute().as_posix()
            base_url = f"file:///{data_dir_path}/"
            
            formatted_images = []
            for img in chapter_data.images:
                parts = img.split('/')
                encoded_parts = [urllib.parse.quote(p) for p in parts]
                formatted_images.append(base_url + "/".join(encoded_parts))
                
            chapter_data.images = formatted_images
            
            library_view.render_chapter_read(chapter_data)
        except AppBaseError as e:
            rprint(f"[bold red]Error:[/] {e}")
            
    asyncio.run(_read())
