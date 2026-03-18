"""Pre-defined Houdini operation scripts for process execution."""


# Script template for creating a box
CREATE_BOX_SCRIPT = '''
import hou

# Get parameters from context
node_name = _MCP_CONTEXT.get("node_name", "box")
size_x = _MCP_CONTEXT.get("size_x", 1.0)
size_y = _MCP_CONTEXT.get("size_y", 1.0)
size_z = _MCP_CONTEXT.get("size_z", 1.0)

# Create geometry container
obj = hou.node("/obj")
geo = obj.createNode("geo", node_name)

# Create box node
box = geo.createNode("box", "box1")
box.parm("sizex").set(size_x)
box.parm("sizey").set(size_y)
box.parm("sizez").set(size_z)

# Set display flag
box.setDisplayFlag(True)
box.setRenderFlag(True)

# Get poly count
geo_data = box.geometry()
poly_count = len(geo_data.prims())

# Store result
_MCP_RESULT["data"] = {
    "node_path": geo.path(),
    "box_size": [size_x, size_y, size_z],
    "poly_count": poly_count,
    "message": f"Box created at {geo.path()} with size [{size_x}, {size_y}, {size_z}]"
}
'''


# Script template for polyreduce
POLYREDUCE_SCRIPT = '''
import hou

# Get parameters
geo_path = _MCP_CONTEXT.get("geo_path")
target_percent = _MCP_CONTEXT.get("target_percent", 50.0)
output_name = _MCP_CONTEXT.get("output_name", "polyreduce1")

# Get geometry node
try:
    geo_node = hou.node(geo_path)
    if not geo_node:
        raise RuntimeError(f"Node '{geo_path}' not found")
except Exception as e:
    raise RuntimeError(f"Failed to get node '{geo_path}': {e}")

# Get current display node
display_node = geo_node.displayNode()
if not display_node:
    raise RuntimeError(f"No display node found in '{geo_path}'")

# Count original polygons
original_geo = display_node.geometry()
original_count = len(original_geo.prims())

# Create polyreduce node
polyreduce = geo_node.createNode("polyreduce", output_name)
polyreduce.setInput(0, display_node)

# Set parameters
polyreduce.parm("percentage").set(target_percent)

# Set display flag
polyreduce.setDisplayFlag(True)
polyreduce.setRenderFlag(True)

# Force cook and get result
polyreduce.cook(force=True)
reduced_geo = polyreduce.geometry()
reduced_count = len(reduced_geo.prims())

# Calculate actual reduction
actual_percent = (reduced_count / original_count * 100) if original_count > 0 else 0

# Store result
_MCP_RESULT["data"] = {
    "node_path": polyreduce.path(),
    "original_poly_count": original_count,
    "reduced_poly_count": reduced_count,
    "target_percent": target_percent,
    "actual_percent": round(actual_percent, 2),
    "message": f"Reduced from {original_count} to {reduced_count} polygons ({actual_percent:.1f}%)"
}
'''


# Script template for get scene state
GET_SCENE_STATE_SCRIPT = '''
import hou

# Get scene info
hip_file = hou.hipFile.path()
frame = hou.frame()

# Get all geometry nodes
obj = hou.node("/obj")
nodes = []

for node in obj.children():
    if node.type().name() == "geo":
        nodes.append({
            "path": node.path(),
            "type": node.type().name(),
            "name": node.name(),
        })

# Store result
_MCP_RESULT["data"] = {
    "hip_file": hip_file,
    "frame": frame,
    "nodes": nodes,
    "node_count": len(nodes),
    "running": True
}
'''


# Script template for mirror
MIRROR_SCRIPT = '''
import hou

# Get parameters
geo_path = _MCP_CONTEXT.get("geo_path")
axis = _MCP_CONTEXT.get("axis", "x")
merge = _MCP_CONTEXT.get("merge", True)
consolidate_seam = _MCP_CONTEXT.get("consolidate_seam", True)
output_name = _MCP_CONTEXT.get("output_name", "mirror")

# Get geometry node
geo_node = hou.node(geo_path)
if not geo_node:
    raise RuntimeError(f"Node '{geo_path}' not found")

display_node = geo_node.displayNode()
if not display_node:
    raise RuntimeError(f"No display node found in '{geo_path}'")

# Create mirror node
mirror = geo_node.createNode("mirror", output_name)
mirror.setInput(0, display_node)

# Set parameters
axis_map = {"x": 0, "y": 1, "z": 2}
mirror.parm("dir").set(axis_map.get(axis, 0))
mirror.parm("consolidateseam").set(1 if consolidate_seam else 0)

# Create merge if needed
if merge:
    merge_node = geo_node.createNode("merge", f"{output_name}_merge")
    merge_node.setInput(0, display_node)
    merge_node.setInput(1, mirror)
    merge_node.setDisplayFlag(True)
    merge_node.setRenderFlag(True)
    result_node = merge_node
else:
    mirror.setDisplayFlag(True)
    mirror.setRenderFlag(True)
    result_node = mirror

# Get result
result_node.cook(force=True)
result_geo = result_node.geometry()
poly_count = len(result_geo.prims())

_MCP_RESULT["data"] = {
    "node_path": result_node.path(),
    "poly_count": poly_count,
    "axis": axis,
    "merged": merge,
    "message": f"Mirrored geometry along {axis}-axis"
}
'''


# Script template for delete half
DELETE_HALF_SCRIPT = '''
import hou

# Get parameters
geo_path = _MCP_CONTEXT.get("geo_path")
axis = _MCP_CONTEXT.get("axis", "x")
keep_side = _MCP_CONTEXT.get("keep_side", "positive")
output_name = _MCP_CONTEXT.get("output_name", "delete_half")

# Get geometry node
geo_node = hou.node(geo_path)
if not geo_node:
    raise RuntimeError(f"Node '{geo_path}' not found")

display_node = geo_node.displayNode()
if not display_node:
    raise RuntimeError(f"No display node found in '{geo_path}'")

# Create delete node
delete_node = geo_node.createNode("delete", output_name)
delete_node.setInput(0, display_node)

# Set parameters (use bounding box)
delete_node.parm("group").set("")
delete_node.parm("negate").set(0)
delete_node.parm("entity").set(0)  # points

# Create expression for deletion
axis_map = {"x": 0, "y": 1, "z": 2}
axis_idx = axis_map.get(axis, 0)

if keep_side == "positive":
    expr = f"$X < 0" if axis == "x" else f"$Y < 0" if axis == "y" else f"$Z < 0"
else:
    expr = f"$X > 0" if axis == "x" else f"$Y > 0" if axis == "y" else f"$Z > 0"

delete_node.parm("filter").set(expr)

delete_node.setDisplayFlag(True)
delete_node.setRenderFlag(True)

# Get result
delete_node.cook(force=True)
result_geo = delete_node.geometry()
poly_count = len(result_geo.prims())

_MCP_RESULT["data"] = {
    "node_path": delete_node.path(),
    "poly_count": poly_count,
    "axis": axis,
    "kept_side": keep_side,
    "message": f"Deleted {keep_side} side along {axis}-axis"
}
'''


# Script template for boolean operations
BOOLEAN_SCRIPT = '''
import hou

# Get parameters
geo_path_a = _MCP_CONTEXT.get("geo_path_a")
geo_path_b = _MCP_CONTEXT.get("geo_path_b", "")
operation = _MCP_CONTEXT.get("operation", "union")
output_name = _MCP_CONTEXT.get("output_name", "boolean")

# Get geometry nodes
geo_node_a = hou.node(geo_path_a)
if not geo_node_a:
    raise RuntimeError(f"Node A '{geo_path_a}' not found")

display_node_a = geo_node_a.displayNode()
if not display_node_a:
    raise RuntimeError(f"No display node in '{geo_path_a}'")

# Get parent to create boolean node
parent = geo_node_a.parent()

# If geo_path_b provided, it's a different node
if geo_path_b and geo_path_b != geo_path_a:
    geo_node_b = hou.node(geo_path_b)
    if not geo_node_b:
        raise RuntimeError(f"Node B '{geo_path_b}' not found")
    display_node_b = geo_node_b.displayNode()
else:
    # Single node, need two inputs (TODO: handle this case)
    raise RuntimeError("Boolean requires two geometry inputs")

# Create object merge nodes to bring geometry together
container = parent.createNode("geo", f"{output_name}_container")
merge_a = container.createNode("object_merge", "input_a")
merge_a.parm("objpath1").set(display_node_a.path())
merge_a.parm("xformtype").set(1)  # Into This Object

merge_b = container.createNode("object_merge", "input_b")
merge_b.parm("objpath1").set(display_node_b.path())
merge_b.parm("xformtype").set(1)

# Create boolean node
boolean = container.createNode("boolean", output_name)
boolean.setInput(0, merge_a)
boolean.setInput(1, merge_b)

# Set operation
op_map = {"union": 2, "intersect": 3, "subtract": 0, "shatter": 4}
boolean.parm("operation").set(op_map.get(operation, 2))

boolean.setDisplayFlag(True)
boolean.setRenderFlag(True)

# Get result
boolean.cook(force=True)
result_geo = boolean.geometry()
poly_count = len(result_geo.prims())

_MCP_RESULT["data"] = {
    "node_path": boolean.path(),
    "poly_count": poly_count,
    "operation": operation,
    "message": f"Boolean {operation} completed with {poly_count} polygons"
}
'''


# Script template for import geometry
IMPORT_GEOMETRY_SCRIPT = '''
import hou
import os

# Get parameters
file_path = _MCP_CONTEXT.get("file_path")
node_name = _MCP_CONTEXT.get("node_name", "imported_geo")

# Validate file
if not os.path.exists(file_path):
    raise FileNotFoundError(f"File not found: {file_path}")

# Detect file type
ext = os.path.splitext(file_path)[1].lower()

# Create geometry container
obj = hou.node("/obj")
geo = obj.createNode("geo", node_name)

# Create appropriate import node
if ext in [".fbx"]:
    # FBX import
    file_node = geo.createNode("file", "import1")
    file_node.parm("file").set(file_path)
elif ext in [".obj"]:
    # OBJ import
    file_node = geo.createNode("file", "import1")
    file_node.parm("file").set(file_path)
elif ext in [".abc"]:
    # Alembic import
    file_node = geo.createNode("alembic", "import1")
    file_node.parm("fileName").set(file_path)
else:
    # Generic file node
    file_node = geo.createNode("file", "import1")
    file_node.parm("file").set(file_path)

file_node.setDisplayFlag(True)
file_node.setRenderFlag(True)

# Force cook and get stats
file_node.cook(force=True)
geo_data = file_node.geometry()
poly_count = len(geo_data.prims()) if geo_data else 0
point_count = len(geo_data.points()) if geo_data else 0

_MCP_RESULT["data"] = {
    "node_path": geo.path(),
    "file_path": file_path,
    "file_type": ext,
    "poly_count": poly_count,
    "point_count": point_count,
    "message": f"Imported {os.path.basename(file_path)} with {poly_count} polygons"
}
'''
