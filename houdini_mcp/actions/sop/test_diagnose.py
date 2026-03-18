"""Test Diagnose Action for debugging node creation."""

from dcc_mcp_core.actions.base import Action
from pydantic import Field


class TestDiagnoseAction(Action):
    """Test node creation in current Houdini session."""

    name = "test_diagnose"
    description = "Diagnose node creation issues"
    tags = ["sop", "test", "debug"]
    dcc = "houdini"
    order = 0

    class InputModel(Action.InputModel):
        """Input parameters."""
        geo_path: str = Field(description="Path to test node")

    class OutputModel(Action.OutputModel):
        """Output data."""
        diagnosis: str = Field(description="Diagnostic information")

    def _execute(self) -> None:
        """Execute diagnostic tests."""
        hou = self.context.get("hou")
        if not hou:
            raise RuntimeError("Houdini 'hou' module not available")

        output_lines = []
        output_lines.append("=== DIAGNOSTIC START ===\n")

        # Get node
        node = hou.node(self.input.geo_path)
        if not node:
            raise ValueError(f"Node not found: {self.input.geo_path}")

        output_lines.append(f"Node: {node.path()}")
        output_lines.append(f"Type: {node.type().name()}")
        output_lines.append(f"Category: {node.type().category().name()}\n")

        # Get display node if OBJ
        if node.type().category().name() == "Object":
            geo_node = node.displayNode()
            if geo_node:
                output_lines.append(f"Display Node: {geo_node.path()}")
                output_lines.append(f"Display Type: {geo_node.type().name()}\n")
            else:
                output_lines.append("No display node!\n")
                geo_node = node
        else:
            geo_node = node

        # Get parent
        parent = geo_node.parent()
        output_lines.append(f"Parent: {parent}")
        if parent:
            output_lines.append(f"Parent path: {parent.path()}")
            output_lines.append(f"Parent type: {parent.type().name()}")
            output_lines.append(f"Parent category: {parent.type().category().name()}\n")

            # Test node creation
            test_types = ['mirror', 'boolean', 'attribwrangle', 'blast']
            output_lines.append("=== NODE CREATION TESTS ===\n")

            for node_type in test_types:
                try:
                    test_name = f"test_{node_type}"
                    output_lines.append(f"Testing {node_type}:")
                    output_lines.append(f"  Calling parent.createNode('{node_type}', '{test_name}')...")

                    test_node = parent.createNode(node_type, test_name)

                    if test_node:
                        output_lines.append(f"  ✓ SUCCESS: {test_node.path()}")
                        # Check if we can set parameters
                        try:
                            if node_type == 'mirror':
                                dirx_parm = test_node.parm('dirx')
                                if dirx_parm:
                                    output_lines.append(f"    parm('dirx') exists: {dirx_parm}")
                                else:
                                    output_lines.append(f"    parm('dirx') is None!")
                        except Exception as e:
                            output_lines.append(f"    Error checking params: {e}")

                        # Clean up
                        test_node.destroy()
                    else:
                        output_lines.append(f"  ✗ FAILED: createNode returned None")
                except Exception as e:
                    output_lines.append(f"  ✗ EXCEPTION: {e}")
                output_lines.append("")

        output_lines.append("=== DIAGNOSTIC END ===")

        self.output = self.OutputModel(
            diagnosis="\n".join(output_lines),
            prompt="Diagnostic complete. Check the diagnosis field for details."
        )
