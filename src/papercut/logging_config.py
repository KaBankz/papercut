"""
Logging configuration for Papercut.
Configures structured logging for the application.
"""

import logging
import sys


class ColoredFormatter(logging.Formatter):
    """Colored log formatter using ANSI escape codes."""

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    def format(self, record):
        # Color the level name with colon and padding
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}:{' ' * (8 - len(levelname))}{self.RESET}"

        # Dim the logger name
        record.name = f"{self.DIM}{record.name}{self.RESET}"

        return super().format(record)


def setup_logging(level: str = "INFO") -> None:
    """
    Configure application logging with colors.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    # Create handler with colored formatter
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(ColoredFormatter("%(levelname)s %(name)s: %(message)s"))

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    root_logger.addHandler(handler)

    # Suppress noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
