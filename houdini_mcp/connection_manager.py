"""Hot-reloadable Houdini connection manager."""

import logging
import time
from typing import Optional, Dict, Any
import os

logger = logging.getLogger(__name__)


class HoudiniConnectionManager:
    """Manages Houdini connections with hot-reload support.

    This allows restarting connections without restarting the MCP process.
    """

    def __init__(self, hython_path: str):
        self.hython_path = hython_path
        self.connected = False
        self.pid: Optional[int] = None
        self.start_time = time.time()
        self._config: Dict[str, Any] = {}

        # Verify hython exists
        if not os.path.exists(hython_path):
            raise RuntimeError(f"Hython not found: {hython_path}")

        logger.info(f"✅ ConnectionManager initialized: {hython_path}")

    def connect(self) -> bool:
        """Establish connection to Houdini."""
        try:
            # For now, we just verify the path exists
            # In a full implementation, this would establish actual connection
            self.connected = os.path.exists(self.hython_path)

            if self.connected:
                # Try to find running Houdini process
                import psutil
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        if 'houdini' in proc.info['name'].lower():
                            self.pid = proc.info['pid']
                            break
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue

                logger.info(f"✅ Connected to Houdini (PID: {self.pid})")
                return True
            else:
                logger.error(f"❌ Hython not found: {self.hython_path}")
                return False

        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            self.connected = False
            return False

    def disconnect(self) -> None:
        """Disconnect from Houdini."""
        logger.info("Disconnecting from Houdini...")
        self.connected = False
        self.pid = None

    def restart(self) -> bool:
        """Hot-restart the connection without restarting MCP server.

        This is the key feature that allows GUI control.
        """
        logger.info("🔄 Hot-restarting Houdini connection...")

        # Step 1: Disconnect
        self.disconnect()
        time.sleep(0.5)

        # Step 2: Clear any cached state
        self.clear_cache()

        # Step 3: Reconnect
        success = self.connect()

        if success:
            logger.info("✅ Hot-restart completed successfully")
        else:
            logger.error("❌ Hot-restart failed")

        return success

    def clear_cache(self) -> None:
        """Clear any cached data."""
        logger.info("🧹 Clearing cache...")
        # In full implementation, clear operation caches, etc.

    def reload_config(self, config: Dict[str, Any]) -> None:
        """Reload configuration without restart.

        Args:
            config: New configuration dict
        """
        logger.info(f"⚙️ Reloading config: {config}")
        self._config.update(config)

        # Apply config changes
        if "hython_path" in config:
            new_path = config["hython_path"]
            if os.path.exists(new_path):
                self.hython_path = new_path
                logger.info(f"✅ Hython path updated: {new_path}")
            else:
                logger.warning(f"⚠️ Invalid hython path: {new_path}")

    def get_status(self) -> Dict[str, Any]:
        """Get current connection status."""
        return {
            "connected": self.connected,
            "pid": self.pid,
            "uptime_seconds": time.time() - self.start_time,
            "hython_path": self.hython_path
        }

    def is_alive(self) -> bool:
        """Check if Houdini process is still running."""
        if not self.pid:
            return False

        try:
            import psutil
            return psutil.pid_exists(self.pid)
        except ImportError:
            # If psutil not available, assume alive if connected
            return self.connected
