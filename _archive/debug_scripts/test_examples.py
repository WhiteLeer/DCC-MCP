"""实际使用示例和测试用例"""

import sys
from houdini_mcp.server import create_server
from houdini_mcp.adapter import get_adapter

print("=" * 70)
print("Houdini MCP Server - 使用示例")
print("=" * 70)

# 创建服务器
mcp, action_mgr = create_server(
    name="Houdini",
    houdini_bin_path="C:/Program Files/Side Effects Software/Houdini 20.5.487/bin"
)

adapter = get_adapter()

print("\n" + "=" * 70)
print("示例1：创建简单几何")
print("=" * 70)

# 测试用例1：创建盒子
print("\n1️⃣ 创建一个2x2x2的盒子")
result = action_mgr.call_action(
    "create_box",
    context=adapter.get_context(),
    node_name="my_box",
    size_x=2.0,
    size_y=2.0,
    size_z=2.0
)
print(f"✅ {result.message}")
print(f"   路径: {result.context.get('node_path')}")
print(f"   多边形数: {result.context.get('poly_count')}")
print(f"   AI提示: {result.prompt}")

# 测试用例2：减面
print("\n2️⃣ 将盒子减面到25%")
box_path = result.context.get('node_path')
result = action_mgr.call_action(
    "polyreduce",
    context=adapter.get_context(),
    geo_path=box_path,
    target_percent=25.0,
    output_name="reduced_box"
)
print(f"✅ {result.message}")
print(f"   结果节点: {result.context.get('result_node')}")
print(f"   原始多边形: {result.context.get('original_poly_count')}")
print(f"   减面后: {result.context.get('reduced_poly_count')}")
print(f"   实际比例: {result.context.get('reduction_ratio'):.1f}%")
print(f"   AI提示: {result.prompt}")

print("\n" + "=" * 70)
print("示例2：批量创建")
print("=" * 70)

# 测试用例3：创建多个盒子
print("\n3️⃣ 创建3个不同尺寸的盒子")
boxes = [
    {"name": "small_box", "size": (1.0, 1.0, 1.0)},
    {"name": "medium_box", "size": (2.0, 2.0, 2.0)},
    {"name": "large_box", "size": (3.0, 3.0, 3.0)},
]

created_boxes = []
for box_spec in boxes:
    result = action_mgr.call_action(
        "create_box",
        context=adapter.get_context(),
        node_name=box_spec["name"],
        size_x=box_spec["size"][0],
        size_y=box_spec["size"][1],
        size_z=box_spec["size"][2]
    )
    if result.success:
        created_boxes.append({
            "name": box_spec["name"],
            "path": result.context.get('node_path'),
            "poly_count": result.context.get('poly_count')
        })
        print(f"✅ {box_spec['name']}: {result.context.get('node_path')}, {result.context.get('poly_count')} polys")

print("\n" + "=" * 70)
print("示例3：Pipeline - 创建并优化")
print("=" * 70)

# 测试用例4：完整流程
print("\n4️⃣ 创建一个复杂盒子并减面")
print("   步骤1: 创建5x3x2的盒子")
result = action_mgr.call_action(
    "create_box",
    context=adapter.get_context(),
    node_name="pipeline_box",
    size_x=5.0,
    size_y=3.0,
    size_z=2.0
)
if result.success:
    box_path = result.context.get('node_path')
    original_polys = result.context.get('poly_count')
    print(f"   ✅ 盒子创建: {box_path}, {original_polys} polys")

    print("   步骤2: 减面到10%")
    result = action_mgr.call_action(
        "polyreduce",
        context=adapter.get_context(),
        geo_path=box_path,
        target_percent=10.0,
        output_name="optimized"
    )
    if result.success:
        reduced_polys = result.context.get('reduced_poly_count')
        ratio = result.context.get('reduction_ratio')
        print(f"   ✅ 减面完成: {original_polys} → {reduced_polys} polys ({ratio:.1f}%)")
        print(f"   节点: {result.context.get('result_node')}")

print("\n" + "=" * 70)
print("示例4：查询场景状态")
print("=" * 70)

# 测试用例5：获取场景信息
print("\n5️⃣ 查询当前场景状态")
scene_state = adapter.get_scene_state()
print(f"✅ 场景信息:")
print(f"   当前帧: {scene_state.get('frame')}")
print(f"   HIP文件: {scene_state.get('hip_file')}")
print(f"   节点数量: {scene_state.get('node_count')}")
print(f"   节点列表:")
for node in scene_state.get('nodes', []):
    print(f"     - {node['name']} ({node['type']}) @ {node['path']}")

print("\n" + "=" * 70)
print("示例5：列出所有可用Action")
print("=" * 70)

# 测试用例6：获取Actions列表
print("\n6️⃣ 所有可用的Houdini操作")
actions_info = action_mgr.get_actions_info()
actions_dict = actions_info.context.get("actions", {})
print(f"✅ 共有 {len(actions_dict)} 个Action:")
for name, info in actions_dict.items():
    print(f"   - {name}:")
    print(f"     描述: {info['description']}")
    print(f"     标签: {', '.join(info['tags'])}")

print("\n" + "=" * 70)
print("✅ 所有测试用例执行完成！")
print("=" * 70)
print("\n💡 提示: 打开Houdini GUI查看创建的节点")
print("   或使用 houdini -foreground 启动交互式会话")
