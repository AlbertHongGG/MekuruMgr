from typing import List
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint
from src.domain.models import LocalComicItem, LocalComic, LocalChapterItem, LocalChapterImages

def render_library_list(comics: List[LocalComicItem], title: str = "Local Comic Library"):
    if not comics:
        rprint("[yellow]Library is empty or no comics found.[/yellow]")
        return
        
    table = Table(title=title, border_style="white")
    table.add_column("Provider", style="cyan")
    table.add_column("Comic ID", style="magenta")
    table.add_column("Title", style="green", no_wrap=False)
    table.add_column("Completed Chapters", justify="right")
    
    for c in comics:
        if c.completed_chapters_count > 0:
            table.add_row(
                c.provider_id,
                c.id,
                c.title,
                str(c.completed_chapters_count)
            )
        
    rprint(table)

def render_library_detail(detail: LocalComic, chapters: List[LocalChapterItem]):
    author_str = detail.author if detail.author else "N/A"
    rprint(Panel(
        f"[bold]Title:[/] {detail.title}\n"
        f"[bold]Author:[/] {author_str}\n"
        f"[bold]Tags:[/] {', '.join(detail.tags)}\n"
        f"[bold]Description:[/] {detail.description[:100]}...\n"
        f"[bold]Cover:[/] {detail.cover_url}",
        title="Comic Info",
        border_style="white"
    ))
    
    table = Table(title=f"Completed Chapters ({len(chapters)})", border_style="white")
    table.add_column("Chapter ID", style="magenta")
    table.add_column("Title", style="green")
    table.add_column("Pages", justify="right")
    
    for ch in chapters:
        table.add_row(ch.id, ch.title, str(ch.page_count))
        
    rprint(table)

def render_chapter_read(chapter_data: LocalChapterImages):
    rprint(f"[bold cyan]Reading:[/] {chapter_data.title} ({len(chapter_data.images)} pages)")
    for idx, img in enumerate(chapter_data.images, start=1):
        rprint(f"[{idx:03d}] {img}")
