import logging
import sys
import structlog
from rich.logging import RichHandler

def setup_logging(log_level: int = logging.INFO):
    """
    Configure structured logging with a beautiful Rich console renderer.
    """
    # 1. Clear existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(log_level)

    # 2. Configure standard Python logging to use RichHandler
    rich_handler = RichHandler(
        show_time=True,
        show_level=True,
        show_path=False,
        rich_tracebacks=True,
        markup=True,
        highlighter=None,  # Disable auto-highlighting to keep key=value clean
    )
    
    # We use a simple message format because structlog will format the key-values
    # into the message string, and RichHandler will just print it.
    formatter = logging.Formatter("%(message)s")
    rich_handler.setFormatter(formatter)
    root_logger.addHandler(rich_handler)

    # 3. Configure structlog to output plain text to the standard logger
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer(
                colors=False,  # Let Rich handle all coloring
                pad_event_to=0 # Disable padding, let Rich format freely
            ),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Suppress overly verbose third-party loggers if needed
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
