import logging
from rich.logging import RichHandler

def setup_logging(log_level: int = logging.INFO):
    """
    Configure pure standard logging with a beautiful Rich console renderer.
    No structlog, no complicated processor chains. Simple and clean.
    """
    # 1. Configure standard Python logging to use RichHandler
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        datefmt="[%X]",  # E.g., [14:05:33]
        handlers=[
            RichHandler(
                show_time=True,
                show_level=True,
                show_path=False,
                rich_tracebacks=True,
                markup=True,      # Enable [color]text[/] markup in log messages
                highlighter=None, # Disable auto-highlighting to keep colors strictly manual
            )
        ],
        force=True # Force override any existing loggers
    )

    # 2. Suppress overly verbose third-party loggers if needed
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
