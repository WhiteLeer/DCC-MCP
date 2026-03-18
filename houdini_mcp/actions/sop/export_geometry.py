"""Export Geometry Action for exporting geometry to file."""

from dcc_mcp_core.actions.base import Action
from pydantic import Field
from typing import Literal


class ExportGeometryAction(Action):
    """Export geometry to file (FBX/OBJ)."""

    name = "export_geometry"
    description = "Export geometry to FBX/OBJ file"
    tags = ["sop", "geometry", "export", "io"]
    dcc = "houdini"
    order = 0

    class InputModel(Action.InputModel):
        """Input parameters for Export Geometry."""

        geo_path: str = Field(
            description="Path to the geometry node to export (e.g., '/obj/geo1' or '/obj/geo1/box1')"
        )
        file_path: str = Field(
            description="Output file path (e.g., 'C:/Models/output.fbx')"
        )
        file_format: Literal["fbx", "obj"] = Field(
            default="fbx",
            description="Export file format",
        )

    class OutputModel(Action.OutputModel):
        """Output data from Export Geometry."""

        exported_file: str = Field(description="Path to the exported file")
        poly_count: int = Field(description="Number of polygons exported")
        point_count: int = Field(description="Number of points exported")

    def _execute(self) -> None:
        """Execute the export geometry operation."""
        hou = self.context.get("hou")
        if not hou:
            raise RuntimeError("Houdini 'hou' module not available in context")

        # Get the source node
        node = hou.node(self.input.geo_path)
        if not node:
            raise ValueError(f"Node not found: {self.input.geo_path}")

        # Get SOP node to export
        if node.type().category().name() == "Object":
            # OBJ node - get display node
            geo_node = node.displayNode()
            if not geo_node:
                raise ValueError(
                    f"No display node found in {self.input.geo_path}. "
                    f"Please specify a SOP node path."
                )
        else:
            # SOP node
            geo_node = node

        # Get geometry info
        try:
            geometry = geo_node.geometry()
            if not geometry:
                raise ValueError(f"No geometry found in {geo_node.path()}")
            poly_count = len(geometry.prims())
            point_count = len(geometry.points())
        except Exception as e:
            raise RuntimeError(f"Failed to get geometry: {e}")

        # Get parent node (SOP container)
        parent = geo_node.parent()
        if not parent:
            raise RuntimeError(f"Node has no parent: {self.input.geo_path}")

        # Create ROP geometry output node
        if self.input.file_format == "fbx":
            # Use filmboxfbx ROP
            rop = parent.createNode("rop_fbx", "fbx_export")
            rop.parm("sopoutput").set(self.input.file_path)
            rop.parm("startnode").set(geo_node.path())
        else:
            # Use geometry ROP for OBJ
            rop = parent.createNode("rop_geometry", "geo_export")
            rop.parm("sopoutput").set(self.input.file_path)
            rop.parm("soppath").set(geo_node.path())

        # Execute export
        try:
            rop.render()
        except Exception as e:
            # Clean up on failure
            rop.destroy()
            raise RuntimeError(f"Failed to export geometry: {e}")

        # Clean up ROP node
        rop.destroy()

        # Set output
        self.output = self.OutputModel(
            exported_file=self.input.file_path,
            poly_count=poly_count,
            point_count=point_count,
            prompt=f"Exported {poly_count} polygons ({point_count} points) to {self.input.file_path}. "
                   f"File format: {self.input.file_format.upper()}.",
        )
