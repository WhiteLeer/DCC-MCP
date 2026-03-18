"""Timeout utilities for MCP operations."""

import functools
import signal
import threading
import time
from typing import Any, Callable, Optional

import logging

logger = logging.getLogger(__name__)


class TimeoutError(Exception):
    """Raised when an operation times out."""
    pass


def timeout(seconds: float = 30.0, error_message: Optional[str] = None):
    """Decorator to add timeout to a function.

    Args:
        seconds: Timeout in seconds (default: 30.0)
        error_message: Custom error message

    Raises:
        TimeoutError: If the function exceeds the timeout
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            result = [TimeoutError(error_message or f"Operation '{func.__name__}' timed out after {seconds}s")]

            def target():
                try:
                    result[0] = func(*args, **kwargs)
                except Exception as e:
                    result[0] = e

            thread = threading.Thread(target=target, daemon=True)
            thread.start()
            thread.join(timeout=seconds)

            if thread.is_alive():
                msg = error_message or f"Operation '{func.__name__}' timed out after {seconds}s"
                logger.error(f"⏰ TIMEOUT: {msg}")
                raise TimeoutError(msg)

            if isinstance(result[0], Exception):
                raise result[0]

            return result[0]

        return wrapper
    return decorator


def with_timeout(func: Callable, timeout_seconds: float, *args, **kwargs) -> Any:
    """Execute a function with timeout.

    Args:
        func: Function to execute
        timeout_seconds: Timeout in seconds
        *args, **kwargs: Arguments to pass to func

    Returns:
        Result of the function

    Raises:
        TimeoutError: If the function exceeds the timeout
    """
    result = [TimeoutError(f"Operation timed out after {timeout_seconds}s")]

    def target():
        try:
            result[0] = func(*args, **kwargs)
        except Exception as e:
            result[0] = e

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join(timeout=timeout_seconds)

    if thread.is_alive():
        msg = f"Operation timed out after {timeout_seconds}s"
        logger.error(f"⏰ TIMEOUT: {msg}")
        raise TimeoutError(msg)

    if isinstance(result[0], Exception):
        raise result[0]

    return result[0]
