"""
Centralized logging configuration for the trading bot.

Logs go to BOTH the console (INFO+) and a rotating log file (DEBUG+),
so the file contains full request/response detail while the console
stays clean for the user.
"""

import logging
import os
from logging.handlers import RotatingFileHandler

DEFAULT_LOG_DIR = "logs"
DEFAULT_LOG_FILE = "trading_bot.log"


def setup_logger(
    name: str = "trading_bot",
    log_dir: str = DEFAULT_LOG_DIR,
    log_file: str = DEFAULT_LOG_FILE,
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG,
) -> logging.Logger:
    """
    Create and return a configured logger.

    - Console handler: concise, INFO and above (keeps CLI output readable).
    - File handler: verbose, DEBUG and above (full API request/response trail).
    - Rotates at 2MB, keeps 5 backups, so logs don't grow unbounded.
    """
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, log_file)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    # Avoid attaching duplicate handlers if setup_logger() is called twice.
    if logger.handlers:
        return logger

    file_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )
    console_formatter = logging.Formatter("%(levelname)-8s | %(message)s")

    file_handler = RotatingFileHandler(
        log_path, maxBytes=2 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setLevel(file_level)
    file_handler.setFormatter(file_formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
