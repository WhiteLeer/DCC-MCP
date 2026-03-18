"""Debug Action loading."""

import sys
import os
import inspect
from pathlib import Path

# Add actions to path
actions_path = Path(__file__).parent / "houdini_mcp" / "actions" / "sop"
sys.path.insert(0, str(actions_path))

print(f"Actions path: {actions_path}")
print(f"Files: {list(actions_path.glob('*.py'))}")

# Try to import Action base
try:
    from dcc_mcp_core.actions.base import Action
    print(f"\n✅ Action base imported: {Action}")
except Exception as e:
    print(f"\n❌ Failed to import Action base: {e}")
    import traceback
    traceback.print_exc()

# Try to import our actions
print("\n=== Importing create_box ===")
try:
    from create_box import CreateBoxAction
    print(f"✅ CreateBoxAction imported: {CreateBoxAction}")
    print(f"   Name: {CreateBoxAction.name}")
    print(f"   DCC: {CreateBoxAction.dcc}")
    print(f"   Is subclass of Action: {issubclass(CreateBoxAction, Action)}")
    print(f"   MRO: {[c.__name__ for c in CreateBoxAction.__mro__]}")
except Exception as e:
    print(f"❌ Failed to import CreateBoxAction: {e}")
    import traceback
    traceback.print_exc()

# Try to import polyreduce
print("\n=== Importing polyreduce ===")
try:
    from polyreduce import PolyReduceAction
    print(f"✅ PolyReduceAction imported: {PolyReduceAction}")
    print(f"   Name: {PolyReduceAction.name}")
    print(f"   DCC: {PolyReduceAction.dcc}")
    print(f"   Is subclass of Action: {issubclass(PolyReduceAction, Action)}")
except Exception as e:
    print(f"❌ Failed to import PolyReduceAction: {e}")
    import traceback
    traceback.print_exc()

# Try direct module loading like dcc-mcp-core does
print("\n=== Testing module loading (like dcc-mcp-core) ===")
try:
    from dcc_mcp_core.utils.module_loader import load_module_from_path

    create_box_path = str(actions_path / "create_box.py")
    print(f"Loading from: {create_box_path}")

    module = load_module_from_path(create_box_path, dcc_name="houdini")
    print(f"✅ Module loaded: {module}")

    # Find Action subclasses
    actions_found = []
    for name, obj in inspect.getmembers(module):
        if inspect.isclass(obj) and issubclass(obj, Action) and obj is not Action:
            print(f"   Found action class: {name} -> {obj}")
            print(f"     name={obj.name}, dcc={obj.dcc}")
            actions_found.append(obj)

    if not actions_found:
        print("   ⚠️ No Action subclasses found!")
        print("   All classes in module:")
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj):
                print(f"     - {name}: {obj}")

except Exception as e:
    print(f"❌ Module loading failed: {e}")
    import traceback
    traceback.print_exc()
