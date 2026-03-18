"""Boolean Action for combining geometries."""

from dcc_mcp_core.actions.base import Action
from pydantic import Field
from typing import Literal


class BooleanAction(Action):
    """Boolean operations on geometry (union/subtract/intersect)."""

    name = "boolean"
    description = "Boolean operations on geometry to combine or subtract"
    tags = ["sop", "geometry", "boolean", "combine"]
    dcc = "houdini"
    order = 0

    class InputModel(Action.InputModel):
        """Input parameters for Boolean."""

        geo_path_a: str = Field(
            description="Path to the first geometry node (A)"
        )
        geo_path_b: str = Field(
            description="Path to the second geometry node (B), optional for single input operations",
            default=""
        )
        operation: Literal["union", "subtract", "intersect", "shatter"] = Field(
            default="union",
            description="Boolean operation type",
        )
        output_name: str = Field(
            default="boolean",
            description="Name for the boolean node",
        )

    class OutputModel(Action.OutputModel):
        """Output data from Boolean."""

        result_node: str = Field(description="Path to the boolean node")
        operation: str = Field(description="Boolean operation performed")
        poly_count: int = Field(description="Final polygon count")

    def _execute(self) -> None:
        """Execute the boolean operation."""
        hou = self.context.get("hou")
        if not hou:
            raise RuntimeError("Houdini 'hou' module not available in context")

        # Get the source node A
        node_a = hou.node(self.input.geo_path_a)
        if not node_a:
            raise ValueError(f"Node A not found: {self.input.geo_path_a}")

        # Get display SOP if OBJ node
        if node_a.type().category().name() == "Object":
            geo_node_a = node_a.displayNode()
            if not geo_node_a:
                raise ValueError(
                    f"No display node found in {self.input.geo_path_a}. "
                    f"Please specify a SOP node path."
                )
        else:
            geo_node_a = node_a

        parent = geo_node_a.parent()
        if not parent:
            raise RuntimeError(f"Node has no parent: {self.input.geo_path_a}")

        # For operations requiring two inputs
        geo_node_b = None
        object_merge_node = None
        if self.input.geo_path_b:
            node_b = hou.node(self.input.geo_path_b)
            if not node_b:
                raise ValueError(f"Node B not found: {self.input.geo_path_b}")

            if node_b.type().category().name() == "Object":
                geo_node_b = node_b.displayNode()
                # If node_b is from different OBJ, use object_merge
                if node_b != node_a:
                    object_merge_node = parent.createNode("object_merge", f"{self.input.output_name}_merge")
                    object_merge_node.parm("objpath1").set(self.input.geo_path_b)
                    object_merge_node.parm("xformtype").set(1)  # Transform Into This Object
                    geo_node_b = object_merge_node
            else:
                geo_node_b = node_b
                # If from different parent, also need object_merge
                if node_b.parent() != parent:
                    object_merge_node = parent.createNode("object_merge", f"{self.input.output_name}_merge")
                    object_merge_node.parm("objpath1").set(node_b.path())
                    object_merge_node.parm("xformtype").set(1)
                    geo_node_b = object_merge_node

        # Create boolean node
        boolean_node = parent.createNode("boolean", self.input.output_name)
        boolean_node.setInput(0, geo_node_a)

        if geo_node_b:
            boolean_node.setInput(1, geo_node_b)

        # Set operation type (use menu item names directly)
        operation_map = {
            "union": "union",
            "intersect": "intersect",
            "subtract": "subtract",
            "shatter": "shatter"
        }
        op_value = operation_map[self.input.operation]
        boolean_node.parm("booleanop").set(op_value)

        # For single input union, boolean will consolidate overlapping geometry automatically

        # Get final polygon count
        try:
            boolean_node.cook(force=True)
            final_geo = boolean_node.geometry()
            poly_count = len(final_geo.prims()) if final_geo else 0
        except Exception as e:
            # Clean up on failure
            boolean_node.destroy()
            if object_merge_node:
                object_merge_node.destroy()
            raise RuntimeError(f"Failed to perform boolean operation: {e}")

        # Set output
        self.output = self.OutputModel(
            result_node=boolean_node.path(),
            operation=self.input.operation,
            poly_count=poly_count,
            prompt=f"Boolean {self.input.operation} completed at {boolean_node.path()}. "
                   f"Final polygon count: {poly_count}. "
                   f"Overlapping geometry has been resolved.",
        )
