"""Houdini Adapter for initializing Houdini environment and providing API access."""

import os
import sys
import subprocess
import psutil
from pathlib import Path
from typing import Optional
import threading
import time


class HoudiniAdapter:
    """Adapter for Houdini environment initialization and API access."""

    def __init__(self, houdini_bin_path: Optional[str] = None):
        """Initialize Houdini adapter.

        Args:
            houdini_bin_path: Path to Houdini bin directory.
                If None, will try to auto-detect or use HOUDINI_PATH env var.
        """
        self.houdini_bin_path = houdini_bin_path or os.environ.get("HOUDINI_PATH")

        if not self.houdini_bin_path:
            # Try default path
            default_path = "C:/Program Files/Side Effects Software/Houdini 20.5.487/bin"
            if os.path.exists(default_path):
                self.houdini_bin_path = default_path
            else:
                raise RuntimeError(
                    "Houdini path not found. Please set HOUDINI_PATH environment variable "
                    "or provide houdini_bin_path parameter."
                )

        self._hou = None
        self._initialized = False
        self._houdini_process = None

    def _is_houdini_running(self) -> bool:
        """Check if any Houdini process is running."""
        try:
            for proc in psutil.process_iter(['name']):
                proc_name = proc.info['name'].lower()
                if 'houdini' in proc_name or 'hython' in proc_name:
                    return True
        except Exception:
            pass
        return False

    def _start_houdini_background(self) -> bool:
        """Start Houdini in background (headless mode).

        Returns:
            bool: True if started successfully, False otherwise.
        """
        try:
            print("[Houdini Adapter] No Houdini process detected, attempting to start hython...")

            # Use hython (Houdini Python) for headless operation
            hython_path = os.path.join(self.houdini_bin_path, "hython.exe")

            if not os.path.exists(hython_path):
                print(f"[Houdini Adapter] ❌ hython not found at: {hython_path}")
                return False

            # Start hython in batch mode (keeps running)
            # Use -c with infinite loop to keep process alive
            startup_script = """
import hou
import time
print('[hython] Started and ready')
# Keep alive
while True:
    time.sleep(1)
"""

            # Start process in background
            self._houdini_process = subprocess.Popen(
                [hython_path, "-c", startup_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )

            print(f"[Houdini Adapter] ✅ Started hython process (PID: {self._houdini_process.pid})")

            # Wait a bit for it to start
            time.sleep(2)

            return self._is_houdini_running()

        except Exception as e:
            print(f"[Houdini Adapter] ❌ Failed to start hython: {e}")
            return False

    def initialize(self):
        """Initialize Houdini Python environment."""
        if self._initialized:
            return

        # Add Houdini Python paths
        houdini_root = Path(self.houdini_bin_path).parent
        python_lib = houdini_root / "houdini" / "python3.11libs"

        if python_lib.exists() and str(python_lib) not in sys.path:
            sys.path.insert(0, str(python_lib))

        # Set Houdini environment variables
        os.environ["HFS"] = str(houdini_root)
        os.environ["H"] = str(houdini_root)
        os.environ["HB"] = str(self.houdini_bin_path)
        os.environ["HDSO"] = str(houdini_root / "dsolib")

        # Add Houdini bin to PATH for DLL loading
        bin_path = str(self.houdini_bin_path)
        if bin_path not in os.environ.get("PATH", ""):
            os.environ["PATH"] = bin_path + os.pathsep + os.environ.get("PATH", "")

        try:
            import hou
            self._hou = hou
            self._initialized = True
            print(f"✅ Houdini {hou.applicationVersionString()} initialized successfully")
        except ImportError as e:
            raise RuntimeError(
                f"Failed to import Houdini 'hou' module. "
                f"Ensure Houdini Python environment is correctly configured.\n"
                f"Houdini root: {houdini_root}\n"
                f"Python lib: {python_lib}\n"
                f"Error: {e}"
            )

    @property
    def hou(self):
        """Get Houdini hou module."""
        if not self._initialized:
            self.initialize()
        return self._hou

    def get_context(self) -> dict:
        """Get Houdini context for Actions."""
        if not self._initialized:
            self.initialize()

        return {
            "hou": self._hou,
            "adapter": self,
        }

    def _execute_with_timeout(self, func, timeout_seconds=3):
        """Execute a function with timeout protection.

        Args:
            func: Function to execute
            timeout_seconds: Timeout in seconds

        Returns:
            Result of function or None if timeout
        """
        result = [None]
        exception = [None]

        def wrapper():
            try:
                result[0] = func()
            except Exception as e:
                exception[0] = e

        thread = threading.Thread(target=wrapper)
        thread.daemon = True
        thread.start()
        thread.join(timeout_seconds)

        if thread.is_alive():
            return None, TimeoutError(f"Operation timed out after {timeout_seconds} seconds")

        if exception[0]:
            return None, exception[0]

        return result[0], None

    def get_scene_state(self) -> dict:
        """Get current Houdini scene state with timeout protection."""
        if not self._initialized:
            self.initialize()

        # Check if Houdini is running
        if not self._is_houdini_running():
            print("[Houdini Adapter] ⚠️ No Houdini process detected")

            # Attempt to auto-start
            if not self._start_houdini_background():
                return {
                    "error": "Houdini is not running. Please start Houdini or hython manually.",
                    "hint": "Run 'hython' from Houdini bin directory to start in headless mode",
                    "hip_file": None,
                    "nodes": [],
                    "running": False
                }

        def get_state():
            """Inner function to get state."""
            try:
                obj_network = self._hou.node("/obj")
                nodes = [
                    {
                        "path": node.path(),
                        "type": node.type().name(),
                        "name": node.name()
                    }
                    for node in obj_network.children()
                ]

                return {
                    "hip_file": self._hou.hipFile.path() if self._hou.hipFile.hasUnsavedChanges() else self._hou.hipFile.basename(),
                    "frame": self._hou.frame(),
                    "nodes": nodes,
                    "node_count": len(nodes),
                    "running": True
                }
            except Exception as e:
                return {
                    "error": str(e),
                    "hip_file": None,
                    "nodes": [],
                    "running": False
                }

        # Execute with timeout
        result, error = self._execute_with_timeout(get_state, timeout_seconds=3)

        if error:
            return {
                "error": f"Failed to get scene state: {error}",
                "hint": "Houdini might not be fully initialized or is unresponsive",
                "hip_file": None,
                "nodes": [],
                "running": self._is_houdini_running()
            }

        return result if result else {
            "error": "Unknown error occurred",
            "hip_file": None,
            "nodes": [],
            "running": False
        }

    def cleanup(self):
        """Clean up resources, stop background Houdini process if started."""
        if self._houdini_process:
            try:
                self._houdini_process.terminate()
                self._houdini_process.wait(timeout=5)
                print("[Houdini Adapter] Stopped background hython process")
            except Exception as e:
                print(f"[Houdini Adapter] Error stopping hython: {e}")


# Global adapter instance
_adapter: Optional[HoudiniAdapter] = None


def get_adapter(houdini_bin_path: Optional[str] = None) -> HoudiniAdapter:
    """Get or create global Houdini adapter instance."""
    global _adapter
    if _adapter is None:
        _adapter = HoudiniAdapter(houdini_bin_path)
    return _adapter
