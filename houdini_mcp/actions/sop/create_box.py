"""CreateBox Action for creating a box geometry."""

from dcc_mcp_core.actions.base import Action
from pydantic import Field


class CreateBoxAction(Action):
    """Create a box geometry in Houdini."""

    name = "create_box"
    description = "Create a box geometry node in /obj"
    tags = ["sop", "geometry", "create", "primitive"]
    dcc = "houdini"
    order = 0

    class InputModel(Action.InputModel):
        """Input parameters for CreateBox."""

        node_name: str = Field(
            default="box",
            description="Name for the box geometry node",
        )
        size_x: float = Field(
            default=1.0,
            gt=0,
            description="Size in X direction",
        )
        size_y: float = Field(
            default=1.0,
            gt=0,
            description="Size in Y direction",
        )
        size_z: float = Field(
            default=1.0,
            gt=0,
            description="Size in Z direction",
        )

    class OutputModel(Action.OutputModel):
        """Output data from CreateBox."""

        node_path: str = Field(description="Path to the created geometry node")
        box_size: list[float] = Field(description="Box dimensions [x, y, z]")
        poly_count: int = Field(description="Number of polygons in the box")

    def _execute(self) -> None:
        """Execute the create box operation."""
        hou = self.context.get("hou")
        if not hou:
            raise RuntimeError("Houdini 'hou' module not available in context")

        # Get /obj network
        obj_network = hou.node("/obj")
        if not obj_network:
            raise RuntimeError("/obj network not found")

        # Create geometry container
        geo_node = obj_network.createNode("geo", self.input.node_name)

        # Delete default file node if exists
        for child in geo_node.children():
            child.destroy()

        # Create box SOP
        box_node = geo_node.createNode("box", "box1")

        # Set box size
        box_node.parm("sizex").set(self.input.size_x)
        box_node.parm("sizey").set(self.input.size_y)
        box_node.parm("sizez").set(self.input.size_z)

        # Set display flag
        box_node.setDisplayFlag(True)
        box_node.setRenderFlag(True)

        # Get polygon count
        box_node.cook(force=True)
        geometry = box_node.geometry()
        poly_count = len(geometry.prims()) if geometry else 0

        # Layout nodes
        geo_node.layoutChildren()

        # Set output
        self.output = self.OutputModel(
            node_path=geo_node.path(),
            box_size=[self.input.size_x, self.input.size_y, self.input.size_z],
            poly_count=poly_count,
            prompt=f"Box geometry created at {geo_node.path()}. "
                   f"Size: [{self.input.size_x}, {self.input.size_y}, {self.input.size_z}], "
                   f"{poly_count} polygons. "
                   f"You can now apply polyreduce or other operations.",
        )
