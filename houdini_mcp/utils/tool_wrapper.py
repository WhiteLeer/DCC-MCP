"""Production-grade tool wrapper with timeout, logging, and retry."""

import functools
import logging
import time
import traceback
from typing import Any, Callable, Optional

from .timeout import timeout, TimeoutError

logger = logging.getLogger(__name__)


def production_tool(
    timeout_seconds: float = 30.0,
    retry_count: int = 0,
    retry_delay: float = 1.0,
):
    """Decorator to wrap MCP tools with production features.

    Features:
    - Timeout protection
    - Detailed logging (start, params, duration, result)
    - Optional retry on failure
    - Error context capture

    Args:
        timeout_seconds: Maximum execution time
        retry_count: Number of retries on failure (0 = no retry)
        retry_delay: Delay between retries in seconds
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> dict:
            func_name = func.__name__
            start_time = time.time()

            # Log operation start
            params_str = ", ".join(f"{k}={v}" for k, v in kwargs.items())
            logger.info(f"🔹 START | {func_name} | {params_str}")

            attempts = 0
            max_attempts = retry_count + 1
            last_error = None

            while attempts < max_attempts:
                attempts += 1
                try:
                    if attempts > 1:
                        logger.info(f"🔄 RETRY {attempts}/{max_attempts} | {func_name}")
                        time.sleep(retry_delay)

                    # Execute with timeout
                    @timeout(seconds=timeout_seconds)
                    def execute():
                        return func(*args, **kwargs)

                    result = execute()

                    # Log success
                    elapsed = time.time() - start_time
                    logger.info(f"✅ SUCCESS | {func_name} | {elapsed:.2f}s")

                    # Add timing info to result
                    if isinstance(result, dict):
                        result["_timing"] = {
                            "duration_seconds": elapsed,
                            "attempts": attempts,
                        }

                    return result

                except TimeoutError as e:
                    elapsed = time.time() - start_time
                    logger.error(f"⏰ TIMEOUT | {func_name} | {elapsed:.2f}s | {str(e)}")
                    last_error = e

                    # Don't retry on timeout (likely permanent issue)
                    break

                except Exception as e:
                    elapsed = time.time() - start_time
                    error_trace = traceback.format_exc()

                    if attempts < max_attempts:
                        logger.warning(f"⚠️  ERROR (will retry) | {func_name} | {elapsed:.2f}s | {type(e).__name__}: {str(e)}")
                    else:
                        logger.error(f"❌ FAILED | {func_name} | {elapsed:.2f}s | {type(e).__name__}: {str(e)}")
                        logger.debug(f"Traceback:\n{error_trace}")

                    last_error = e

            # All attempts failed
            elapsed = time.time() - start_time
            error_msg = str(last_error) if last_error else "Unknown error"
            error_type = type(last_error).__name__ if last_error else "UnknownError"

            return {
                "success": False,
                "error": error_msg,
                "error_type": error_type,
                "message": f"Operation '{func_name}' failed after {attempts} attempt(s)",
                "_timing": {
                    "duration_seconds": elapsed,
                    "attempts": attempts,
                },
                "_context": {
                    "function": func_name,
                    "params": kwargs,
                    "timeout_seconds": timeout_seconds,
                    "max_attempts": max_attempts,
                }
            }

        return wrapper
    return decorator
