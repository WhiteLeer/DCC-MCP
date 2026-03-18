"""Debug ActionRegistry behavior."""

import os
from pathlib import Path

from houdini_mcp.adapter import get_adapter
from dcc_mcp_core.actions.manager import ActionManager
from dcc_mcp_core.actions.registry import ActionRegistry

print("=== Testing ActionRegistry directly ===")

# Initialize Houdini
adapter = get_adapter("C:/Program Files/Side Effects Software/Houdini 20.5.487/bin")
adapter.initialize()

# Create registry directly
registry = ActionRegistry()

# Discover actions
actions_path = Path(__file__).parent / "houdini_mcp" / "actions" / "sop"
print(f"\nDiscovering from: {actions_path}")

discovered = registry.discover_actions_from_path(str(actions_path), dcc_name="houdini")
print(f"Discovered {len(discovered)} actions:")
for action_cls in discovered:
    print(f"   - {action_cls.name} ({action_cls.__name__})")

# Get all actions from registry
all_actions = registry.get_all_actions()
print(f"\nAll actions in registry: {len(all_actions)}")
for action_name, action_cls in all_actions.items():
    print(f"   - {action_name}: {action_cls}")

# Now test with ActionManager
print("\n=== Testing ActionManager ===")

action_mgr = ActionManager("houdini", load_env_paths=False)
action_mgr.context = adapter.get_context()

# Register path
print(f"Registering path: {actions_path}")
action_mgr.register_action_path(str(actions_path))

# Refresh
print("Refreshing actions...")
action_mgr.refresh_actions()

# Get info
print("Getting actions info...")
info = action_mgr.get_actions_info()
print(f"Type: {type(info)}")
print(f"Info: {info.to_dict()}")

# Try to access registry directly
if hasattr(action_mgr, 'registry'):
    print(f"\nActionManager registry: {action_mgr.registry}")
    all_actions = action_mgr.registry.get_all_actions()
    print(f"Registry has {len(all_actions)} actions:")
    for name in all_actions.keys():
        print(f"   - {name}")
