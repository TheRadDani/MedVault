"""
Loguru configuration for MedVault RAG pipeline.

Provides structured logging with file rotation and proper formatting.
"""

import sys
from pathlib import Path
from loguru import logger

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)


def configure_logging(level: str = "INFO", log_file: bool = True) -> None:
    """
    Configure loguru with optimal settings for production.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Whether to also log to file
    """
    
    # Remove default handler
    logger.remove()
    
    # Console handler with colors
    console_format = (
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )
    
    logger.add(
        sys.stdout,
        format=console_format,
        level=level,
        colorize=True,
    )
    
    # File handler with rotation
    if log_file:
        file_format = (
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
            "{level: <8} | "
            "{name}:{function}:{line} - {message}"
        )
        
        logger.add(
            LOG_DIR / "medvault_{time:YYYY-MM-DD}.log",
            format=file_format,
            level=level,
            rotation="500 MB",  # Rotate every 500MB
            retention="7 days",  # Keep 7 days of logs
            compression="zip",  # Compress rotated logs
            encoding="utf-8",
        )
    
    logger.info(f"Logging configured | Level: {level} | File logging: {log_file}")


# Initialize on import
configure_logging()
