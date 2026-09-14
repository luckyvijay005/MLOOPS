"""Structured logging utility for Hospital Readmission Analytics.

Adheres strictly to healthcare privacy standards: never logs raw patient
identifiers or unhashed patient data.
"""

import logging
import sys
from pathlib import Path
from src.utils.config import Config


def setup_logger(name: str = "hospital_pipeline", log_file: str = "pipeline.log") -> logging.Logger:
    """Configures and returns a structured logger instance."""
    logger = logging.getLogger(name)

    # Avoid duplicate handlers if already configured
    if logger.handlers:
        return logger

    log_level = getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)

    # Formatter for structured logs
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(module)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler
    log_dir = Config.LOGS_DIR
    log_dir.mkdir(parents=True, exist_ok=True)
    file_path = log_dir / log_file
    file_handler = logging.FileHandler(file_path, encoding="utf-8")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


# Default application logger
logger = setup_logger()
