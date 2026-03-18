"""Test correct way to load actions with ActionManager."""

import os
from pathlib import Path

from houdini_mcp.adapter import get_adapter
from dcc_mcp_core.actions.manager import ActionManager
from dcc_mcp_core.actions.registry import ActionRegistry

print("=== Testing Action Loading Fix ===\n")

# Initialize Houdini
adapter = get_adapter("C:/Program Files/Side Effects Software/Houdini 20.5.487/bin")
adapter.initialize()

# Method 1: Direct registry approach
print("Method 1: Direct ActionRegistry.discover_actions_from_path()\n")
registry = ActionRegistry()

actions_dir = Path(__file__).parent / "houdini_mcp" / "actions" / "sop"
print(f"Actions directory: {actions_dir}")
print(f"Exists: {actions_dir.exists()}\n")

# Discover each Python file individually
for py_file in actions_dir.glob("*.py"):
    if py_file.name.startswith("__"):
        continue

    print(f"Discovering from file: {py_file.name}")
    try:
        discovered = registry.discover_actions_from_path(
            path=str(py_file),
            dependencies=adapter.get_context(),
            dcc_name="houdini"
        )
        print(f"  ✅ Discovered {len(discovered)} actions:")
        for action_cls in discovered:
            print(f"     - {action_cls.name} ({action_cls.__name__})")
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()

# Check registry state
print(f"\n=== Registry State ===")
print(f"All actions in registry: {len(registry._actions)}")
for name in registry._actions.keys():
    print(f"  - {name}")

print(f"\nDCC-specific registry (houdini): {len(registry._dcc_actions.get('houdini', {}))}")
for name in registry._dcc_actions.get('houdini', {}).keys():
    print(f"  - {name}")

# Now test list_actions
print(f"\n=== list_actions() ===")
actions_list = registry.list_actions(dcc_name="houdini")
print(f"Found {len(actions_list)} actions:")
for action_info in actions_list:
    print(f"  - {action_info['name']}: {action_info['description']}")

# Method 2: ActionManager approach (corrected)
print(f"\n\nMethod 2: ActionManager with individual file paths\n")
action_mgr = ActionManager("houdini", load_env_paths=False)
action_mgr.context = adapter.get_context()

# Register individual files instead of directory
for py_file in actions_dir.glob("*.py"):
    if py_file.name.startswith("__"):
        continue
    print(f"Registering: {py_file.name}")
    action_mgr.register_action_path(str(py_file))

# Refresh
action_mgr.refresh_actions()

# Get info
info = action_mgr.get_actions_info()
print(f"\nActionManager info:")
print(f"  Success: {info.success}")
print(f"  Message: {info.message}")
print(f"  Actions count: {len(info.context.get('actions', {}))}")
print(f"  Actions: {list(info.context.get('actions', {}).keys())}")

# Test calling an action
print(f"\n=== Testing action execution ===")
if info.context.get('actions'):
    result = action_mgr.call_action(
        "create_box",
        node_name="test_box",
        size_x=2.0,
        size_y=2.0,
        size_z=2.0
    )
    print(f"Result: {result.to_dict()}")
