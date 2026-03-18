"""
Direct export via Houdini Python SOP.
This will be executed in the running Houdini session via a Python SOP node.
"""
import hou

def export_geometry():
    # Get the cleaned geometry node
    geo_node = hou.node('/obj/symmetry_workflow/cleaned1')
    if not geo_node:
        return "ERROR: Node /obj/symmetry_workflow/cleaned1 not found"

    # Get parent
    parent = geo_node.parent()

    # Create FBX ROP node
    output_path = "C:/Users/wepie/Desktop/AI_生成_对称模型.fbx"
    rop = parent.createNode("rop_fbx", "fbx_export_temp")
    rop.parm("sopoutput").set(output_path)
    rop.parm("startnode").set(geo_node.path())

    # Execute export
    try:
        rop.render()
        result = f"SUCCESS: Exported to {output_path}"
    except Exception as e:
        result = f"ERROR: {e}"
    finally:
        rop.destroy()

    return result

# Execute
print(export_geometry())
