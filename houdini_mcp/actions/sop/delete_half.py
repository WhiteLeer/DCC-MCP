"""Delete Half Action for removing half of geometry along an axis."""

from dcc_mcp_core.actions.base import Action
from pydantic import Field
from typing import Literal


class DeleteHalfAction(Action):
    """Delete half of geometry along specified axis."""

    name = "delete_half"
    description = "Delete half of geometry along X/Y/Z axis"
    tags = ["sop", "geometry", "edit", "delete"]
    dcc = "houdini"
    order = 0

    class InputModel(Action.InputModel):
        """Input parameters for Delete Half."""

        geo_path: str = Field(
            description="Path to the geometry node (e.g., '/obj/geo1')"
        )
        axis: Literal["x", "y", "z"] = Field(
            default="x",
            description="Axis to split along (x/y/z)",
        )
        keep_side: Literal["positive", "negative"] = Field(
            default="positive",
            description="Which side to keep (positive: +axis, negative: -axis)",
        )
        output_name: str = Field(
            default="delete_half",
            description="Name for the delete node",
        )

    class OutputModel(Action.OutputModel):
        """Output data from Delete Half."""

        result_node: str = Field(description="Path to the delete node")
        original_poly_count: int = Field(description="Original polygon count")
        remaining_poly_count: int = Field(description="Remaining polygon count")
        deleted_percent: float = Field(description="Percentage of polygons deleted")

    def _execute(self) -> None:
        """Execute the delete half operation."""
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

        # Get parent node (SOP container)
        parent = geo_node.parent()
        if not parent:
            raise RuntimeError(f"Node has no parent: {self.input.geo_path}")

        # Use clip node to delete half
        clip_node = parent.createNode("clip", self.input.output_name)
        clip_node.setInput(0, geo_node)

        # Set clip direction based on axis
        axis_lower = self.input.axis.lower()
        if axis_lower == 'x':
            if self.input.keep_side == "positive":
                # Keep positive X side, clip direction points to negative X
                clip_node.parm("dirx").set(-1)
            else:
                # Keep negative X side, clip direction points to positive X
                clip_node.parm("dirx").set(1)
            clip_node.parm("diry").set(0)
            clip_node.parm("dirz").set(0)
        elif axis_lower == 'y':
            clip_node.parm("dirx").set(0)
            if self.input.keep_side == "positive":
                clip_node.parm("diry").set(-1)
            else:
                clip_node.parm("diry").set(1)
            clip_node.parm("dirz").set(0)
        else:  # z
            clip_node.parm("dirx").set(0)
            clip_node.parm("diry").set(0)
            if self.input.keep_side == "positive":
                clip_node.parm("dirz").set(-1)
            else:
                clip_node.parm("dirz").set(1)

        # Set clip origin to 0
        clip_node.parm("originx").set(0)
        clip_node.parm("originy").set(0)
        clip_node.parm("originz").set(0)

        # Get remaining polygon count
        try:
            clip_node.cook(force=True)
            remaining_geo = clip_node.geometry()
            remaining_poly_count = len(remaining_geo.prims()) if remaining_geo else 0
        except Exception as e:
            # Clean up on failure
            clip_node.destroy()
            raise RuntimeError(f"Failed to delete half: {e}")

        # Calculate deletion percentage
        deleted_percent = (
            ((original_poly_count - remaining_poly_count) / original_poly_count * 100.0)
            if original_poly_count > 0
            else 0.0
        )

        # Set output
        self.output = self.OutputModel(
            result_node=clip_node.path(),
            original_poly_count=original_poly_count,
            remaining_poly_count=remaining_poly_count,
            deleted_percent=deleted_percent,
            prompt=f"Deleted half of geometry at {clip_node.path()}. "
                   f"Kept {self.input.keep_side} {self.input.axis.upper()} side. "
                   f"Reduced from {original_poly_count} to {remaining_poly_count} polygons "
                   f"({deleted_percent:.1f}% deleted). "
                   f"You can now apply mirror to create symmetry.",
        )
