import typer
from rich import print as rprint

from src.core.logger import setup_logging
from src.core.registry import registry
from src.cli.commands import comic, archive

# Dynamically discover and load all providers
registry.load_all_providers()

app = typer.Typer(
    help="ComicMgr - A highly extensible Comic Management Platform",
    no_args_is_help=True
)

app.add_typer(comic.app, name="comic")
app.add_typer(archive.app, name="archive")

@app.callback()
def main(verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging")):
    """Global configuration for the CLI."""
    import logging
    log_level = logging.DEBUG if verbose else logging.INFO
    setup_logging(log_level)

if __name__ == "__main__":
    app()
