import typer
import logging
from src.core.logger import setup_logging
from src.core.registry import registry
from src.cli.commands.comic_cmd import comic_app
from src.cli.commands.archive_cmd import archive_app
from src.cli.commands.library_cmd import library_app

# Global setup

app = typer.Typer(
    help="ComicMgr - A highly extensible Comic Management Platform",
    no_args_is_help=True
)

app.add_typer(comic_app, name="comic")
app.add_typer(archive_app, name="archive")
app.add_typer(library_app, name="library")

@app.callback()
def main(verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging")):
    """
    Global callback that runs before any command.
    Used for setting up global state like logging level.
    """
    import logging
    setup_logging(log_level=logging.DEBUG if verbose else logging.INFO)
    
    # Initialize registry AFTER logging is set up
    registry.load_all_providers()

if __name__ == "__main__":
    app()
