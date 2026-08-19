from rich.console import Console
from rich.table import Table
from typing import List
from src.domain.user_models import UserComicInteraction

console = Console()

def render_favorites(favorites: List[UserComicInteraction]):
    if not favorites:
        console.print("[yellow]No favorites found in your library.[/yellow]")
        return
        
    table = Table(title="My Favorite Comics")
    table.add_column("Provider", style="cyan")
    table.add_column("Comic ID", style="magenta")
    table.add_column("Title", style="green")
    table.add_column("Last Read", style="yellow")
    
    for item in favorites:
        last_read = item.last_read_chapter_id or "Never read"
        table.add_row(
            item.provider_id,
            item.comic_id,
            item.title or "[No Title Saved]",
            last_read
        )
        
    console.print(table)

def render_interaction(interaction: UserComicInteraction):
    console.print(f"\n[bold cyan]User Interaction for {interaction.comic_id}[/bold cyan]")
    console.print(f"Is Favorite: [green]{interaction.is_favorite}[/green]")
    console.print(f"Last Read Chapter: [yellow]{interaction.last_read_chapter_id or 'None'}[/yellow]")
    console.print(f"Total read chapters history: {len(interaction.reading_history)}")
