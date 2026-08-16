import logging
import structlog
from rich.logging import RichHandler

def setup_logging(log_level: int = logging.INFO):
    """
    Configure structured logging with a beautiful, tight Rich console renderer.
    Removes the ugly padding from structlog and adds premium syntax highlighting.
    """
    # 1. Configure standard Python logging to use RichHandler
    # RichHandler automatically provides a beautiful Timestamp and a tightly-packed colored Level.
    rich_handler = RichHandler(
        show_time=True,
        show_level=True,
        show_path=False,  # Keep output clean
        rich_tracebacks=True,
        markup=True,
    )
    
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        datefmt="%H:%M:%S",
        handlers=[rich_handler]
    )

    # 2. Configure structlog
    structlog.configure(
        processors=[
            # IMPORTANT: We DO NOT add `add_log_level` or `TimeStamper` here!
            # If we add them, structlog's ConsoleRenderer will render them with ugly padding.
            # We let RichHandler take care of the Level and Timestamp natively.
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            # ConsoleRenderer will only render the event name and key=value pairs nicely
            structlog.dev.ConsoleRenderer(
                colors=False,  # Disable structlog colors, let Rich colorize the output
                pad_event_to=0
            ),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
