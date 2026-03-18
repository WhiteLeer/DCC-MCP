"""Mirror Action for creating symmetric geometry."""

from dcc_mcp_core.actions.base import Action
from pydantic import Field
from typing import Literal


class MirrorAction(Action):
    """Mirror geometry along specified axis to create symmetry."""

    name = "mirror"
    description = "Mirror geometry along X/Y/Z axis"
    tags = ["sop", "geometry", "mirror", "symmetry"]
    dcc = "houdini"
    order = 0

    class InputModel(Action.InputModel):
        """Input parameters for Mirror."""

        geo_path: str = Field(
            description="Path to the geometry node (e.g., '/obj/geo1')"
        )
        axis: Literal["x", "y", "z"] = Field(
            default="x",
            description="Axis to mirror along (x/y/z)",
        )
        merge: bool = Field(
            default=True,
            description="Merge mirrored geometry with original (if False, only show mirrored)",
        )
        consolidate_seam: bool = Field(
            default=True,
            description="Fuse points along the mirror seam",
        )
        output_name: str = Field(
            default="mirror",
            description="Name for the mirror node",
        )

    class OutputModel(Action.OutputModel):
        """Output data from Mirror."""

        result_node: str = Field(description="Path to the mirror node")
        original_poly_count: int = Field(description="Original polygon count")
        final_poly_count: int = Field(description="Final polygon count after mirror")
        mirrored: bool = Field(description="Whether mirroring was successful")

    def _execute(self) -> None:
        """Execute the mirror operation."""
        hou = self.context.get("hou")
        if not hou:
            raise RuntimeError("Houdini 'hou' module not available in context")

        # Get the source node
        node = hou.node(self.input.geo_path)
        if not node:
            raise ValueError(f"Node not found: {self.input.geo_path}")

        # Get display SOP if OBJ node
        if node.type().category().name() == "Object":
            geo_node = node.displayNode()
            if not geo_node:
                raise ValueError(
                    f"No display node found in {self.input.geo_path}. "
                    f"Please specify a SOP node path."
                )
        else:
            geo_node = node

        # Get original polygon count
        try:
            original_geo = geo_node.geometry()
            original_poly_count = len(original_geo.prims()) if original_geo else 0
        except Exception as e:
            raise RuntimeError(f"Failed to get geometry from node: {e}")

        # Create mirror node
        parent = geo_node.parent()
        if not parent:
            raise RuntimeError(f"Node has no parent: {self.input.geo_path}")

        # Debug: Print parent information
        print(f"[DEBUG] Parent: {parent}")
        print(f"[DEBUG] Parent type: {parent.type().name()}")
        print(f"[DEBUG] Parent category: {parent.type().category().name()}")
        print(f"[DEBUG] Parent path: {parent.path()}")
        print(f"[DEBUG] Attempting to create mirror node with name: {self.input.output_name}")

        mirror_node = parent.createNode("mirror", self.input.output_name)

        print(f"[DEBUG] mirror_node result: {mirror_node}")
        if not mirror_node:
            raise RuntimeError(
                f"Failed to create mirror node in {parent.path()}. "
                f"createNode('mirror', '{self.input.output_name}') returned None"
            )
        mirror_node.setInput(0, geo_node)

        # Set mirror axis direction vector
        axis_lower = self.input.axis.lower()
        if axis_lower == 'x':
            mirror_node.parm("dirx").set(1)
            mirror_node.parm("diry").set(0)
            mirror_node.parm("dirz").set(0)
        elif axis_lower == 'y':
            mirror_node.parm("dirx").set(0)
            mirror_node.parm("diry").set(1)
            mirror_node.parm("dirz").set(0)
        else:  # z
            mirror_node.parm("dirx").set(0)
            mirror_node.parm("diry").set(0)
            mirror_node.parm("dirz").set(1)

        # Set origin to 0
        mirror_node.parm("originx").set(0)
        mirror_node.parm("originy").set(0)
        mirror_node.parm("originz").set(0)

        # Set consolidate seam
        mirror_node.parm("consolidatepts").set(1 if self.input.consolidate_seam else 0)

        # Set whether to keep original
        if self.input.merge:
            # Keep original + mirrored
            mirror_node.parm("keepOriginal").set(1)
        else:
            # Only show mirrored part
            mirror_node.parm("keepOriginal").set(0)

        # Get final polygon count
        try:
            mirror_node.cook(force=True)
            final_geo = mirror_node.geometry()
            final_poly_count = len(final_geo.prims()) if final_geo else 0
        except Exception as e:
            # Clean up on failure
            mirror_node.destroy()
            raise RuntimeError(f"Failed to mirror geometry: {e}")

        # Set output
        self.output = self.OutputModel(
            result_node=mirror_node.path(),
            original_poly_count=original_poly_count,
            final_poly_count=final_poly_count,
            mirrored=True,
            prompt=f"Mirrored geometry at {mirror_node.path()}. "
                   f"Axis: {self.input.axis.upper()}, "
                   f"Merged: {self.input.merge}. "
                   f"Polygons: {original_poly_count} → {final_poly_count}. "
                   f"You can now apply boolean operations to remove overlaps.",
        )
