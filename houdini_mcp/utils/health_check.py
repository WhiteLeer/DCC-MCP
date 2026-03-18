"""Health check utilities for MCP server."""

import logging
import threading
import time
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class HealthChecker:
    """Background health checker for DCC application."""

    def __init__(
        self,
        check_function: Callable[[], bool],
        interval: float = 10.0,
        timeout: float = 5.0,
        on_unhealthy: Optional[Callable] = None,
    ):
        """Initialize health checker.

        Args:
            check_function: Function that returns True if healthy
            interval: Check interval in seconds
            timeout: Timeout for each check
            on_unhealthy: Callback when application becomes unhealthy
        """
        self.check_function = check_function
        self.interval = interval
        self.timeout = timeout
        self.on_unhealthy = on_unhealthy

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._healthy = True
        self._consecutive_failures = 0
        self._last_check_time: Optional[float] = None

    def start(self):
        """Start health checking in background."""
        if self._running:
            logger.warning("Health checker already running")
            return

        self._running = True
        self._thread = threading.Thread(target=self._check_loop, daemon=True)
        self._thread.start()
        logger.info(f"🏥 Health checker started (interval={self.interval}s, timeout={self.timeout}s)")

    def stop(self):
        """Stop health checking."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        logger.info("🏥 Health checker stopped")

    def is_healthy(self) -> bool:
        """Check if the application is currently healthy."""
        return self._healthy

    def get_status(self) -> dict:
        """Get detailed health status."""
        return {
            "healthy": self._healthy,
            "consecutive_failures": self._consecutive_failures,
            "last_check": self._last_check_time,
            "running": self._running,
        }

    def _check_loop(self):
        """Background loop for health checking."""
        while self._running:
            try:
                start_time = time.time()

                # Perform health check with timeout
                result = [False]

                def check_target():
                    try:
                        result[0] = self.check_function()
                    except Exception as e:
                        logger.error(f"Health check error: {e}")
                        result[0] = False

                check_thread = threading.Thread(target=check_target, daemon=True)
                check_thread.start()
                check_thread.join(timeout=self.timeout)

                elapsed = time.time() - start_time
                self._last_check_time = time.time()

                if check_thread.is_alive():
                    # Timeout
                    logger.warning(f"🏥 Health check timed out after {self.timeout}s")
                    self._handle_unhealthy()
                elif result[0]:
                    # Healthy
                    if not self._healthy:
                        logger.info("🏥 ✅ Application is healthy again")
                    self._healthy = True
                    self._consecutive_failures = 0
                    logger.debug(f"🏥 Health check passed ({elapsed:.2f}s)")
                else:
                    # Unhealthy
                    self._handle_unhealthy()

            except Exception as e:
                logger.error(f"🏥 Error in health check loop: {e}")
                self._handle_unhealthy()

            # Wait for next check
            time.sleep(self.interval)

    def _handle_unhealthy(self):
        """Handle unhealthy state."""
        self._consecutive_failures += 1

        if self._healthy:
            logger.error(f"🏥 ❌ Application became unhealthy (failures={self._consecutive_failures})")
            self._healthy = False

            # Trigger callback
            if self.on_unhealthy:
                try:
                    self.on_unhealthy()
                except Exception as e:
                    logger.error(f"Error in on_unhealthy callback: {e}")
        else:
            logger.warning(f"🏥 Still unhealthy (failures={self._consecutive_failures})")


def create_simple_health_checker(
    get_scene_state_func: Callable,
    interval: float = 10.0,
) -> HealthChecker:
    """Create a simple health checker that calls get_scene_state().

    Args:
        get_scene_state_func: Function to get scene state
        interval: Check interval in seconds

    Returns:
        Configured HealthChecker instance
    """
    def check():
        try:
            state = get_scene_state_func()
            return state is not None and state.get("running", False)
        except Exception:
            return False

    return HealthChecker(
        check_function=check,
        interval=interval,
        timeout=5.0,
    )
