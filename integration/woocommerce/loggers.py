"""
Logging configuration.

"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from config import APP_NAME, LOG_LEVEL


def setup_logging():
    """
    Configure the logging system.

    Creates a 'logs' directory if it doesn't exist and sets up
    both console and rotating file handlers.
    """
    # Ensure logs directory exists
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Log file path
    log_file = log_dir / "app.log"

    # Create the root logger
    logger = logging.getLogger()
    logger.setLevel(LOG_LEVEL)

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )

    # 1. Console Handler (Standard Output)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 2. Rotating File Handler
    # Max size: 5MB (5 * 1024 * 1024 bytes)
    # Backup usage: 5 files
    file_handler = RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"  # 5 MB
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    if logger.hasHandlers():
        logger.handlers.clear()

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    logging.info(f"Logging initialized. Logs writing to: {log_file}")


def get_logger(name: str):
    """
    Get a logger with the specified name.
    """
    return logging.getLogger(name)
