from typing import List
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint
from src.domain.models import Comic, Chapter, PageImage

def render_comic_detail(provider_name: str, comic: Comic):
    panel = Panel(
        f"[bold]Title:[/] {comic.title}\n"
        f"[bold]Author:[/] {comic.author}\n"
        f"[bold]Status:[/] {comic.update_status}\n"
        f"[bold]Tags:[/] {', '.join(comic.tags)}\n"
        f"[bold]Desc:[/] {comic.description[:100]}...\n"
        f"[bold]Cover:[/] {comic.cover_url}",
        title=f"[{provider_name}] Comic Info",
        border_style="white"
    )
    rprint(panel)

def render_chapters_list(provider_name: str, comic_id: str, chapters: List[Chapter]):
    table = Table(title=f"[{provider_name}] Chapters for {comic_id}", border_style="white")
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

def render_comic_list(title: str, comics: List[Comic]):
    table = Table(title=title, border_style="white")
    table.add_column("ID", style="magenta")
    table.add_column("Title", style="green")
    table.add_column("Tags", style="yellow")
    
    for c in comics:
        table.add_row(c.id, c.title, ", ".join(c.tags))

    rprint(table)

def render_images_list(provider_name: str, chapter_id: str, images: List[PageImage]):
    table = Table(title=f"[{provider_name}] Images for Chapter {chapter_id}", border_style="white")
    table.add_column("Order", justify="right", style="cyan", no_wrap=True)
    table.add_column("URL", style="green")
    
    for img in images:
        table.add_row(str(img.order), img.url)

    rprint(table)
