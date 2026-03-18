"""Fix hot reload for Houdini MCP by patching ActionManager and ActionRegistry."""

import importlib
import os
import sys
import time
from typing import Dict, Optional

# Monkey patch the ActionManager and ActionRegistry to support real hot reload


def patch_action_manager():
    """Patch ActionManager to support hot reload with file modification detection."""
    from dcc_mcp_core.actions.manager import ActionManager

    # Store original methods
    original_discover = ActionManager._discover_actions_from_path

    # Add file modification time tracking
    if not hasattr(ActionManager, '_file_mtimes'):
        ActionManager._file_mtimes = {}

    def _discover_actions_from_path_with_reload(self, path: str) -> None:
        """Discover actions from a path with hot reload support."""
        # Find Python files in the path
        action_files = []
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith(".py") and not file.startswith("__"):
                    action_files.append(os.path.join(root, file))

        # Check each file for modifications
        for file_path in action_files:
            try:
                # Get current modification time
                current_mtime = os.path.getmtime(file_path)

                # Check if file was modified
                if file_path in self._file_mtimes:
                    if current_mtime > self._file_mtimes[file_path]:
                        print(f"[HOT RELOAD] Detected modification: {os.path.basename(file_path)}", file=sys.stderr)
                        # File was modified, need to reload
                        self._reload_action_file(file_path)

                # Update modification time
                self._file_mtimes[file_path] = current_mtime

            except Exception as e:
                print(f"[HOT RELOAD] Error checking file {file_path}: {e}", file=sys.stderr)

        # Call original method (for new files)
        original_discover(self, path)

    def _reload_action_file(self, file_path: str) -> None:
        """Reload a modified action file."""
        try:
            # Clear module cache in registry
            if file_path in self.registry._module_cache:
                print(f"[HOT RELOAD] Clearing registry cache for: {file_path}", file=sys.stderr)
                del self.registry._module_cache[file_path]

            # Find and clear sys.modules entries
            # Convert file path to potential module names
            file_dir = os.path.dirname(file_path)
            file_name = os.path.basename(file_path).replace('.py', '')

            # Clear all sys.modules entries that might be related
            modules_to_clear = []
            for module_name in list(sys.modules.keys()):
                if file_name in module_name or 'houdini_mcp' in module_name:
                    # Check if this module's file matches
                    try:
                        module = sys.modules[module_name]
                        if hasattr(module, '__file__') and module.__file__:
                            if os.path.normpath(module.__file__) == os.path.normpath(file_path):
                                modules_to_clear.append(module_name)
                    except:
                        pass

            for module_name in modules_to_clear:
                print(f"[HOT RELOAD] Clearing sys.modules['{module_name}']", file=sys.stderr)
                del sys.modules[module_name]

            # Unregister old actions from this file
            actions_to_remove = []
            for action_name, action_class in list(self.registry._actions.items()):
                if hasattr(action_class, '_source_file'):
                    if os.path.normpath(action_class._source_file) == os.path.normpath(file_path):
                        actions_to_remove.append(action_name)

            for action_name in actions_to_remove:
                print(f"[HOT RELOAD] Unregistering old action: {action_name}", file=sys.stderr)
                if action_name in self.registry._actions:
                    del self.registry._actions[action_name]
                # Also remove from DCC-specific registry
                for dcc_name in self.registry._dcc_actions:
                    if action_name in self.registry._dcc_actions[dcc_name]:
                        del self.registry._dcc_actions[dcc_name][action_name]

            # Now reload the file
            print(f"[HOT RELOAD] Reloading actions from: {os.path.basename(file_path)}", file=sys.stderr)
            discovered = self.registry.discover_actions_from_path(
                path=file_path,
                dependencies=self.context,
                dcc_name=self.dcc_name
            )

            print(f"[HOT RELOAD] ✅ Reloaded {len(discovered)} actions from {os.path.basename(file_path)}", file=sys.stderr)
            for action_cls in discovered:
                print(f"[HOT RELOAD]    - {action_cls.name} ({action_cls.__name__})", file=sys.stderr)

        except Exception as e:
            print(f"[HOT RELOAD] ❌ Error reloading {file_path}: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)

    # Apply patches
    ActionManager._discover_actions_from_path = _discover_actions_from_path_with_reload
    ActionManager._reload_action_file = _reload_action_file

    print("[HOT RELOAD] ✅ Patched ActionManager with hot reload support", file=sys.stderr)


def patch_action_registry():
    """Patch ActionRegistry to always reload modules."""
    from dcc_mcp_core.actions.registry import ActionRegistry

    original_discover = ActionRegistry._discover_actions_from_module

    def _discover_actions_from_module_with_reload(
        self, path, dependencies, dcc_name, discovered_actions, discovered_action_classes
    ):
        """Discover actions with forced reload."""
        # Always clear cache for this path
        if path in self._module_cache:
            del self._module_cache[path]

        # Call original method
        return original_discover(self, path, dependencies, dcc_name, discovered_actions, discovered_action_classes)

    # Apply patch
    ActionRegistry._discover_actions_from_module = _discover_actions_from_module_with_reload

    print("[HOT RELOAD] ✅ Patched ActionRegistry to force reload", file=sys.stderr)


def enable_hot_reload():
    """Enable hot reload by patching the necessary classes."""
    print("\n" + "="*60, file=sys.stderr)
    print("ENABLING HOT RELOAD FOR HOUDINI MCP", file=sys.stderr)
    print("="*60, file=sys.stderr)

    try:
        patch_action_manager()
        patch_action_registry()

        print("\n[HOT RELOAD] ✅ Hot reload is now ENABLED!", file=sys.stderr)
        print("[HOT RELOAD] Modified action files will be automatically reloaded", file=sys.stderr)
        print("="*60 + "\n", file=sys.stderr)

        return True
    except Exception as e:
        print(f"\n[HOT RELOAD] ❌ Failed to enable hot reload: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return False


if __name__ == "__main__":
    enable_hot_reload()
