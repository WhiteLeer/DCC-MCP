"""Import Geometry Action for loading FBX/OBJ files."""

from dcc_mcp_core.actions.base import Action
from pydantic import Field, field_validator
import os


class ImportGeometryAction(Action):
    """Import geometry from external file (FBX/OBJ/etc)."""

    name = "import_geometry"
    description = "Import geometry from file (FBX/OBJ/Alembic)"
    tags = ["sop", "geometry", "import", "io"]
    dcc = "houdini"
    order = 0

    class InputModel(Action.InputModel):
        """Input parameters for Import Geometry."""

        file_path: str = Field(
            description="Path to the geometry file (e.g., 'C:/Models/mesh.fbx')"
        )
        node_name: str = Field(
            default="imported_geo",
            description="Name for the imported geometry node",
        )

        @field_validator("file_path")
        @classmethod
        def validate_file_path(cls, v: str) -> str:
            """Validate file exists."""
            if not os.path.exists(v):
                raise ValueError(f"File not found: {v}")
            return v

    class OutputModel(Action.OutputModel):
        """Output data from Import Geometry."""

        node_path: str = Field(description="Path to the imported geometry node")
        file_path: str = Field(description="Source file path")
        poly_count: int = Field(description="Number of polygons imported")
        point_count: int = Field(description="Number of points imported")

    def _execute(self) -> None:
        """Execute the import operation."""
        hou = self.context.get("hou")
        if not hou:
            raise RuntimeError("Houdini 'hou' module not available in context")

        # Create geo container node
        obj_network = hou.node("/obj")
        geo_node = obj_network.createNode("geo", self.input.node_name)

        # Delete default file node if exists
        for child in geo_node.children():
            child.destroy()

        # Create file SOP to load geometry
        file_node = geo_node.createNode("file", "import_file")
        file_node.parm("file").set(self.input.file_path)

        # Set as display node
        file_node.setDisplayFlag(True)
        file_node.setRenderFlag(True)

        # Get geometry info
        try:
            geo = file_node.geometry()
            poly_count = len(geo.prims()) if geo else 0
            point_count = len(geo.points()) if geo else 0
        except Exception as e:
            raise RuntimeError(f"Failed to read imported geometry: {e}")

        # Set output
        self.output = self.OutputModel(
            node_path=geo_node.path(),
            file_path=self.input.file_path,
            poly_count=poly_count,
            point_count=point_count,
            prompt=f"Imported geometry from {os.path.basename(self.input.file_path)} at {geo_node.path()}. "
                   f"{poly_count} polygons, {point_count} points. "
                   f"You can now apply polyreduce, mirror, or other operations.",
        )
