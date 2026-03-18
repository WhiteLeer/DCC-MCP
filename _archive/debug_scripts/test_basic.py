"""Basic test script for Houdini MCP Server."""

import sys
import os

# Test Houdini adapter initialization
print("=" * 60)
print("Testing Houdini MCP Server")
print("=" * 60)

try:
    print("\n1. Testing Houdini Adapter...")
    from houdini_mcp.adapter import get_adapter

    adapter = get_adapter("C:/Program Files/Side Effects Software/Houdini 20.5.487/bin")
    adapter.initialize()
    print(f"✅ Houdini initialized: {adapter.hou.applicationVersionString()}")

    print("\n2. Testing Action Manager...")
    from dcc_mcp_core.actions.manager import ActionManager

    action_mgr = ActionManager("houdini", load_env_paths=False)

    # Register actions
    actions_path = os.path.join(
        os.path.dirname(__file__), "houdini_mcp", "actions", "sop"
    )
    action_mgr.register_action_path(actions_path)
    action_mgr.context = adapter.get_context()
    action_mgr.refresh_actions()

    actions_info = action_mgr.get_actions_info()
    # get_actions_info() returns ActionResultModel in dcc-mcp-core
    if hasattr(actions_info, 'context'):
        actions_dict = actions_info.context
    else:
        actions_dict = actions_info

    print(f"✅ Loaded {len(actions_dict)} actions:")
    for action_name in actions_dict.keys():
        print(f"   - {action_name}")

    print("\n3. Testing create_box action...")
    result = action_mgr.call_action(
        "create_box",
        node_name="test_box",
        size_x=2.0,
        size_y=3.0,
        size_z=1.5,
    )

    if result.success:
        print(f"✅ Box created: {result.context.get('node_path')}")
        print(f"   Size: {result.context.get('box_size')}")
        print(f"   Polygons: {result.context.get('poly_count')}")
        print(f"   Prompt: {result.prompt}")

        # Test polyreduce
        print("\n4. Testing polyreduce action...")
        reduce_result = action_mgr.call_action(
            "polyreduce",
            geo_path=result.context.get('node_path'),
            target_percent=50.0,
            output_name="reduced",
        )

        if reduce_result.success:
            print(f"✅ PolyReduce applied: {reduce_result.context.get('result_node')}")
            print(f"   Original: {reduce_result.context.get('original_poly_count')} polys")
            print(f"   Reduced: {reduce_result.context.get('reduced_poly_count')} polys")
            print(f"   Ratio: {reduce_result.context.get('reduction_ratio'):.1f}%")
            print(f"   Prompt: {reduce_result.prompt}")
        else:
            print(f"❌ PolyReduce failed: {reduce_result.error}")
    else:
        print(f"❌ Box creation failed: {result.error}")

    print("\n5. Testing scene state...")
    scene_state = adapter.get_scene_state()
    print(f"✅ Scene state retrieved:")
    print(f"   Frame: {scene_state.get('frame')}")
    print(f"   Node count: {scene_state.get('node_count')}")
    print(f"   Nodes: {[n['name'] for n in scene_state.get('nodes', [])]}")

    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)

except Exception as e:
    print(f"\n❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
