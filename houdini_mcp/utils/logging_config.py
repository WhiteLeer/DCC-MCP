"""Enhanced logging configuration for production MCP."""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Colored log formatter for console output."""

    COLORS = {
        'DEBUG': '\033[36m',  # Cyan
        'INFO': '\033[32m',  # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',  # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname:8s}{self.RESET}"
        return super().format(record)


def setup_logging(
    name: str = "houdini-mcp",
    log_dir: Optional[str] = None,
    log_level: str = "INFO",
    enable_file_logging: bool = True,
    enable_console_logging: bool = True,
) -> logging.Logger:
    """Setup comprehensive logging system.

    Args:
        name: Logger name
        log_dir: Directory for log files (default: ~/.mcp_logs/<name>)
        log_level: Logging level (DEBUG/INFO/WARNING/ERROR/CRITICAL)
        enable_file_logging: Enable file logging
        enable_console_logging: Enable console logging

    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    logger.handlers.clear()  # Remove existing handlers

    # Setup log directory
    if log_dir is None:
        home = Path.home()
        log_dir = home / ".mcp_logs" / name

    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    # File handler (detailed logs)
    if enable_file_logging:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"{name}_{timestamp}.log"

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # Always DEBUG in file
        file_formatter = logging.Formatter(
            '%(asctime)s | %(name)-20s | %(levelname)-8s | %(filename)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # Also create a symlink to latest.log
        latest_log = log_dir / f"{name}_latest.log"
        if latest_log.exists():
            latest_log.unlink()
        try:
            latest_log.symlink_to(log_file.name)
        except (OSError, NotImplementedError):
            # Windows may not support symlinks, just copy
            import shutil
            shutil.copy2(log_file, latest_log)

        logger.info(f"📝 File logging enabled: {log_file}")

    # Console handler (stderr, colored)
    if enable_console_logging:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(getattr(logging, log_level.upper()))

        # Use colored formatter for console
        console_formatter = ColoredFormatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    # Cleanup old log files (keep last 10)
    try:
        log_files = sorted(log_dir.glob(f"{name}_*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
        for old_log in log_files[10:]:  # Keep 10 most recent
            if old_log.name != f"{name}_latest.log":
                old_log.unlink()
                logger.debug(f"Cleaned up old log: {old_log.name}")
    except Exception as e:
        logger.warning(f"Failed to cleanup old logs: {e}")

    return logger


def log_operation(logger: logging.Logger, operation_name: str, **context):
    """Log an operation with context.

    Args:
        logger: Logger instance
        operation_name: Name of the operation
        **context: Additional context to log
    """
    context_str = " | ".join(f"{k}={v}" for k, v in context.items())
    logger.info(f"🔹 {operation_name} | {context_str}")


def log_error(logger: logging.Logger, operation_name: str, error: Exception, **context):
    """Log an error with full context.

    Args:
        logger: Logger instance
        operation_name: Name of the operation
        error: The exception that occurred
        **context: Additional context to log
    """
    import traceback

    context_str = " | ".join(f"{k}={v}" for k, v in context.items())
    error_trace = ''.join(traceback.format_exception(type(error), error, error.__traceback__))

    logger.error(f"❌ {operation_name} FAILED | {context_str}")
    logger.error(f"Error: {type(error).__name__}: {str(error)}")
    logger.debug(f"Full traceback:\n{error_trace}")
