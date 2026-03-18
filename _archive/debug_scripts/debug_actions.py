"""Debug script to inspect ActionManager behavior."""

import os
import json

from houdini_mcp.adapter import get_adapter
from dcc_mcp_core.actions.manager import ActionManager

print("Debugging ActionManager...")

# Initialize Houdini
adapter = get_adapter("C:/Program Files/Side Effects Software/Houdini 20.5.487/bin")
adapter.initialize()

# Create Action Manager
action_mgr = ActionManager("houdini", load_env_paths=False)

# Register actions
actions_path = os.path.join(
    os.path.dirname(__file__), "houdini_mcp", "actions", "sop"
)
print(f"\nActions path: {actions_path}")
print(f"Path exists: {os.path.exists(actions_path)}")
print(f"Files in path: {os.listdir(actions_path)}")

action_mgr.register_action_path(actions_path)
action_mgr.context = adapter.get_context()
action_mgr.refresh_actions()

# Get actions info
print("\n=== get_actions_info() ===")
actions_info = action_mgr.get_actions_info()
print(f"Type: {type(actions_info)}")
print(f"Dir: {[x for x in dir(actions_info) if not x.startswith('_')]}")

if hasattr(actions_info, '__dict__'):
    print(f"\nAttributes: {actions_info.__dict__}")

if hasattr(actions_info, 'to_dict'):
    print(f"\nto_dict(): {actions_info.to_dict()}")

if hasattr(actions_info, 'context'):
    print(f"\ncontext: {actions_info.context}")
    print(f"context type: {type(actions_info.context)}")

# Try to list actions directly
print("\n=== action_mgr._registry ===")
if hasattr(action_mgr, '_registry'):
    registry = action_mgr._registry
    print(f"Registry type: {type(registry)}")
    if hasattr(registry, 'get_all_actions'):
        all_actions = registry.get_all_actions()
        print(f"All actions: {all_actions}")
