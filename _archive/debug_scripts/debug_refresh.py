"""Debug refresh_actions behavior."""

import os
import glob

from houdini_mcp.adapter import get_adapter
from dcc_mcp_core.actions.manager import ActionManager

print("=== Debugging refresh_actions ===\n")

# Initialize Houdini
adapter = get_adapter("C:/Program Files/Side Effects Software/Houdini 20.5.487/bin")
adapter.initialize()

# Create ActionManager
action_mgr = ActionManager("houdini", load_env_paths=False)
action_mgr.context = adapter.get_context()

# Check registered paths
print(f"Action paths before registration: {action_mgr._action_paths}")

# Register action files
actions_dir = os.path.join(
    os.path.dirname(__file__), "houdini_mcp", "actions", "sop"
)
action_files = glob.glob(os.path.join(actions_dir, "*.py"))

print(f"\nFound {len(action_files)} Python files:")
for f in action_files:
    if not os.path.basename(f).startswith("__"):
        print(f"  - {os.path.basename(f)}: exists={os.path.exists(f)}, size={os.path.getsize(f)}")
        action_mgr.register_action_path(f)

print(f"\nAction paths after registration: {action_mgr._action_paths}")

# Check registry state BEFORE refresh
print(f"\n=== Registry BEFORE refresh ===")
print(f"Registry._actions: {len(action_mgr.registry._actions)}")
print(f"Registry._dcc_actions[houdini]: {len(action_mgr.registry._dcc_actions.get('houdini', {}))}")

# Call refresh
print("\n=== Calling refresh_actions() ===")
action_mgr.refresh_actions(force=True)

# Check registry state AFTER refresh
print(f"\n=== Registry AFTER refresh ===")
print(f"Registry._actions: {list(action_mgr.registry._actions.keys())}")
print(f"Registry._dcc_actions[houdini]: {list(action_mgr.registry._dcc_actions.get('houdini', {}).keys())}")

# Get actions info
info = action_mgr.get_actions_info()
print(f"\n=== get_actions_info() ===")
print(f"Success: {info.success}")
print(f"Actions: {info.context.get('actions', {})}")

# Try direct call to _discover_actions_from_path_sync
print(f"\n=== Testing _discover_actions_from_path_sync ===")
for action_file in action_mgr._action_paths:
    print(f"\nProcessing: {os.path.basename(action_file)}")
    try:
        action_mgr._discover_actions_from_path_sync(action_file)
    except Exception as e:
        print(f"  Error: {e}")
        import traceback
        traceback.print_exc()

print(f"\n=== Registry AFTER manual sync ===")
print(f"Registry._actions: {list(action_mgr.registry._actions.keys())}")
print(f"Registry._dcc_actions[houdini]: {list(action_mgr.registry._dcc_actions.get('houdini', {}).keys())}")
