from typing import List
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint
from src.domain.models import ComicDetail, Chapter, PageImage, ComicExploreResult

def render_comic_detail(provider_name: str, comic: ComicDetail):
    author_str = comic.author if comic.author else "N/A"
    status_str = comic.update_status if comic.update_status else "N/A"
    tags_str = ", ".join(comic.tags) if comic.tags else "N/A"
    
    panel = Panel(
        f"[bold]Title:[/] {comic.title}\n"
        f"[bold]Author:[/] {author_str}\n"
        f"[bold]Status:[/] {status_str}\n"
        f"[bold]Tags:[/] {tags_str}\n"
        f"[bold]Desc:[/] {comic.description[:100]}...\n"
        f"[bold]Cover:[/] {comic.cover_url}",
        title=f"[{provider_name}] Comic Info",
        border_style="white"
    )
    rprint(panel)

def render_chapters_list(provider_name: str, comic_id: str, chapters: List[Chapter]):
    table = Table(title=f"[{provider_name}] Chapters for {comic_id}", border_style="white")
    table.add_column("ID", style="magenta")
    table.add_column("Title", style="green")
    table.add_column("Publish Time", style="yellow")

    for ch in chapters:
        table.add_row(
            ch.id, 
            ch.title, 
            ch.publish_time
        )

    rprint(table)

def render_comic_list(title: str, comics: List[ComicDetail]):
    table = Table(title=title, border_style="white")
    table.add_column("ID", style="magenta")
    table.add_column("Title", style="green")
    table.add_column("Tags", style="yellow")
    
    for c in comics:
        tags_str = ", ".join(c.tags) if c.tags else ""
        table.add_row(c.id, c.title, tags_str)

    rprint(table)

def render_explore_list(title: str, comics: List[ComicExploreResult]):
    table = Table(title=title, border_style="white")
    table.add_column("ID", style="magenta")
    table.add_column("Title", style="green")
    table.add_column("Tags", style="yellow")
    
    for c in comics:
        tags_str = ", ".join(c.tags) if c.tags else ""
        table.add_row(c.id, c.title, tags_str)

    rprint(table)

def render_images_list(provider_name: str, chapter_id: str, images: List[PageImage]):
    table = Table(title=f"[{provider_name}] Images for Chapter {chapter_id}", border_style="white")
    table.add_column("Index", justify="right", style="cyan", no_wrap=True)
    table.add_column("URL", style="green")
    
    for img in images:
        table.add_row(str(img.index), img.url)

    rprint(table)
