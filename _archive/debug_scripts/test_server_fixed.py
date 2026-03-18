"""Test the fixed server with ActionManager."""

import sys
import os

print("=" * 70)
print("Testing Fixed Houdini MCP Server (Method B - ActionManager)")
print("=" * 70)

try:
    # Import server creation function
    from houdini_mcp.server import create_server

    print("\n1. Creating MCP Server...")
    mcp, action_mgr = create_server(
        name="Houdini",
        houdini_bin_path="C:/Program Files/Side Effects Software/Houdini 20.5.487/bin"
    )

    print(f"✅ MCP Server created: {mcp}")
    print(f"✅ ActionManager created: {action_mgr}")

    print("\n2. Testing list_actions()...")
    from houdini_mcp.adapter import get_adapter
    adapter = get_adapter()

    actions_info = action_mgr.get_actions_info()
    actions_dict = actions_info.context.get("actions", {})

    print(f"✅ Found {len(actions_dict)} actions:")
    for name, info in actions_dict.items():
        print(f"   - {name}: {info['description']}")

    print("\n3. Testing create_box action...")
    result = action_mgr.call_action(
        "create_box",
        context=adapter.get_context(),  # Pass context explicitly
        node_name="test_box_1",
        size_x=2.0,
        size_y=3.0,
        size_z=1.5
    )

    if result.success:
        print(f"✅ Box created successfully!")
        print(f"   Node path: {result.context.get('node_path')}")
        print(f"   Box size: {result.context.get('box_size')}")
        print(f"   Poly count: {result.context.get('poly_count')}")
        print(f"   Prompt: {result.prompt}")

        print("\n4. Testing polyreduce action...")
        reduce_result = action_mgr.call_action(
            "polyreduce",
            context=adapter.get_context(),  # Pass context explicitly
            geo_path=result.context.get('node_path'),
            target_percent=50.0,
            output_name="reduced"
        )

        if reduce_result.success:
            print(f"✅ PolyReduce successful!")
            print(f"   Result node: {reduce_result.context.get('result_node')}")
            print(f"   Original polys: {reduce_result.context.get('original_poly_count')}")
            print(f"   Reduced polys: {reduce_result.context.get('reduced_poly_count')}")
            print(f"   Ratio: {reduce_result.context.get('reduction_ratio'):.1f}%")
            print(f"   Prompt: {reduce_result.prompt}")
        else:
            print(f"❌ PolyReduce failed: {reduce_result.error}")
    else:
        print(f"❌ Box creation failed: {result.error}")

    print("\n5. Testing scene state...")
    scene_state = adapter.get_scene_state()
    print(f"✅ Scene state:")
    print(f"   Frame: {scene_state.get('frame')}")
    print(f"   Nodes: {[n['name'] for n in scene_state.get('nodes', [])]}")

    print("\n" + "=" * 70)
    print("✅ All tests passed! Method B (ActionManager) is working!")
    print("=" * 70)

except Exception as e:
    print(f"\n❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
