"""PolyReduce Action for reducing polygon count."""

from dcc_mcp_core.actions.base import Action
from pydantic import Field, field_validator


class PolyReduceAction(Action):
    """Reduce polygon count of a geometry node using Houdini's polyreduce SOP."""

    name = "polyreduce"
    description = "Reduce the polygon count of a geometry node"
    tags = ["sop", "geometry", "optimize", "reduce"]
    dcc = "houdini"
    order = 0

    class InputModel(Action.InputModel):
        """Input parameters for PolyReduce."""

        geo_path: str = Field(
            description="Path to the geometry node (e.g., '/obj/geo1')"
        )
        target_percent: float = Field(
            default=50.0,
            ge=0.1,
            le=100.0,
            description="Target percentage of polygons to keep (0.1-100)",
        )
        output_name: str = Field(
            default="polyreduce1",
            description="Name for the polyreduce node",
        )

        @field_validator("geo_path")
        @classmethod
        def validate_geo_path(cls, v: str) -> str:
            """Validate geometry path format."""
            if not v.startswith("/"):
                raise ValueError("Geometry path must start with '/'")
            return v

    class OutputModel(Action.OutputModel):
        """Output data from PolyReduce."""

        result_node: str = Field(description="Path to the created polyreduce node")
        original_poly_count: int = Field(description="Original polygon count")
        reduced_poly_count: int = Field(description="Reduced polygon count")
        reduction_ratio: float = Field(description="Actual reduction ratio achieved")

    def _execute(self) -> None:
        """Execute the polyreduce operation."""
        hou = self.context.get("hou")
        if not hou:
            raise RuntimeError("Houdini 'hou' module not available in context")

        # Get the node
        node = hou.node(self.input.geo_path)
        if not node:
            raise ValueError(f"Node not found: {self.input.geo_path}")

        # If it's an OBJ node, get the display SOP
        if node.type().category().name() == "Object":
            geo_node = node.displayNode()
            if not geo_node:
                raise ValueError(
                    f"No display node found in {self.input.geo_path}. "
                    f"Please specify a SOP node path (e.g., '{self.input.geo_path}/box1')"
                )
        else:
            geo_node = node

        # Get original polygon count
        try:
            original_geo = geo_node.geometry()
            original_poly_count = len(original_geo.prims()) if original_geo else 0
        except Exception as e:
            raise RuntimeError(f"Failed to get geometry from node: {e}")

        # Create polyreduce node
        parent = geo_node.parent()
        if not parent:
            raise RuntimeError(f"Node has no parent: {self.input.geo_path}")

        polyreduce_node = parent.createNode("polyreduce", self.input.output_name)
        polyreduce_node.setInput(0, geo_node)

        # Set parameters
        polyreduce_node.parm("percentage").set(self.input.target_percent)

        # Get reduced polygon count
        try:
            polyreduce_node.cook(force=True)
            reduced_geo = polyreduce_node.geometry()
            reduced_poly_count = len(reduced_geo.prims()) if reduced_geo else 0
        except Exception as e:
            # Clean up on failure
            polyreduce_node.destroy()
            raise RuntimeError(f"Failed to cook polyreduce node: {e}")

        # Calculate actual reduction ratio
        reduction_ratio = (
            (reduced_poly_count / original_poly_count * 100.0)
            if original_poly_count > 0
            else 0.0
        )

        # Set output
        self.output = self.OutputModel(
            result_node=polyreduce_node.path(),
            original_poly_count=original_poly_count,
            reduced_poly_count=reduced_poly_count,
            reduction_ratio=reduction_ratio,
            prompt=f"PolyReduce created at {polyreduce_node.path()}. "
                   f"Reduced from {original_poly_count} to {reduced_poly_count} polygons "
                   f"({reduction_ratio:.1f}% remaining). "
                   f"You can now apply smooth or export the geometry.",
        )
