import typer
import asyncio
from src.core.container import AppContainer
from src.cli.commands import comic_cmd, archive_cmd, library_cmd

app = typer.Typer(
    help="ComicMgr CLI - Manage your comic downloads and library",
    no_args_is_help=True
)

app.add_typer(comic_cmd.comic_app, name="comic")
app.add_typer(archive_cmd.archive_app, name="archive")
app.add_typer(library_cmd.library_app, name="library")

@app.callback()
def main(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output")
):
    container = AppContainer()
    container.config.debug = verbose or container.config.debug
    ctx.obj = container

if __name__ == "__main__":
    app()
