import os
import logging
import json
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict

from config import LOG_LEVEL

class CustomLogger(logging.Logger):
    """
    A professional custom logger that includes structured JSON logging.
    """
    def json(self, title: str, data: Dict[str, Any], level: int = logging.INFO):
        """
        Log structured data as a pretty-printed JSON block.
        """
        try:
            formatted_json = json.dumps(data, indent=2, default=str)
            separator = "=" * 50
            message = (
                f"\n{separator}\n"
                f"{title}\n"
                f"{separator}\n"
                f"{formatted_json}\n"
                f"{separator}"
            )
            self.log(level, message)
        except Exception as e:
            self.error(f"Failed to log JSON for {title}: {e}")

# Register the custom logger class
logging.setLoggerClass(CustomLogger)

def setup_logging():
    """
    Configure the logging system globally.
    
    Ensures 'logs' directory exists and sets up console and rotating file handlers
    with a 5MB limit and 5-file rotation.
    """
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / "app.log"
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(LOG_LEVEL)
    
    # Clean up existing handlers to avoid duplicates
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
    
    # Standard Professional Formatter
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )
    
    # 1. Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 2. Rotating File Handler (Strictly 5MB, 5 Backups)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    logging.info(f"Logging system initialized. Output: {log_file} (Max 5MB, 5 backups)")

def get_logger(name: str) -> CustomLogger:
    """
    Factory function to get a professional custom logger instance.
    """
    return logging.getLogger(name)
