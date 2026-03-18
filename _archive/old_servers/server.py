"""Houdini MCP Server v2 - Process-Isolated Architecture.

This version runs each Houdini operation in an isolated process,
ensuring true timeout protection and stability.
"""

import logging
import os
import sys
from typing import Optional

from mcp.server.fastmcp import FastMCP

from houdini_mcp.utils.logging_config import setup_logging
from houdini_mcp.core.process_executor import ProcessExecutor, ProcessTimeoutError, ProcessExecutionError
from houdini_mcp.core.operation_scripts import (
    CREATE_BOX_SCRIPT,
    POLYREDUCE_SCRIPT,
    GET_SCENE_STATE_SCRIPT,
    MIRROR_SCRIPT,
    DELETE_HALF_SCRIPT,
    BOOLEAN_SCRIPT,
    IMPORT_GEOMETRY_SCRIPT,
)

# Configure production logging
logger = setup_logging(
    name="houdini-mcp-v2",
    log_level="INFO",
    enable_file_logging=True,
    enable_console_logging=True,
)

logger.info("=" * 80)
logger.info("🚀 Houdini MCP Server v2 - Process-Isolated Architecture")
logger.info("=" * 80)


def create_server(
    name: str = "Houdini-v2",
    houdini_bin_path: Optional[str] = None,
) -> tuple[FastMCP, ProcessExecutor]:
    """Create and configure the MCP server v2.

    Args:
        name: The name of the MCP server.
        houdini_bin_path: Path to Houdini bin directory.

    Returns:
        tuple: (FastMCP server, ProcessExecutor)
    """
    # Detect hython path
    if houdini_bin_path:
        hython_path = os.path.join(houdini_bin_path, "hython.exe")
    else:
        # Auto-detect (Windows)
        hython_path = "C:/Program Files/Side Effects Software/Houdini 20.5.487/bin/hython.exe"

    if not os.path.exists(hython_path):
        raise RuntimeError(f"Hython not found at: {hython_path}")

    logger.info(f"Hython path: {hython_path}")

    # Create MCP server
    mcp = FastMCP(name=name)

    # Create process executor
    executor = ProcessExecutor(hython_path, default_timeout=30.0)
    logger.info("✅ Process executor initialized (default timeout: 30s)")

    # === MCP Tools ===

    @mcp.tool()
    def get_scene_state() -> dict:
        """Get current Houdini scene state.

        Returns:
            dict: Current scene information including nodes, frame, etc.
        """
        try:
            result = executor.execute(GET_SCENE_STATE_SCRIPT, timeout=10.0)

            if result["success"]:
                return {
                    "success": True,
                    "scene": result["data"],
                    "_timing": result.get("_timing")
                }
            else:
                return result

        except ProcessTimeoutError as e:
            logger.error(f"⏰ get_scene_state timeout: {e}")
            return {"success": False, "error": str(e), "error_type": "Timeout"}
        except Exception as e:
            logger.error(f"❌ get_scene_state error: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def create_box(
        node_name: str = "box",
        size_x: float = 1.0,
        size_y: float = 1.0,
        size_z: float = 1.0,
    ) -> dict:
        """Create a box geometry in Houdini.

        Args:
            node_name: Name for the box geometry node.
            size_x: Size in X direction.
            size_y: Size in Y direction.
            size_z: Size in Z direction.

        Returns:
            dict: Result of the operation.
        """
        try:
            result = executor.execute(
                CREATE_BOX_SCRIPT,
                timeout=15.0,
                context={
                    "node_name": node_name,
                    "size_x": size_x,
                    "size_y": size_y,
                    "size_z": size_z,
                }
            )

            if result["success"]:
                data = result["data"]
                return {
                    "success": True,
                    "message": data["message"],
                    "prompt": f"Box created at {data['node_path']}. Size: {data['box_size']}, {data['poly_count']} polygons.",
                    "error": None,
                    "context": data,
                    "_timing": result.get("_timing")
                }
            else:
                return result

        except ProcessTimeoutError as e:
            logger.error(f"⏰ create_box timeout: {e}")
            return {"success": False, "error": "Operation timed out after 15s", "error_type": "Timeout"}
        except Exception as e:
            logger.error(f"❌ create_box error: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def polyreduce(
        geo_path: str,
        target_percent: float = 50.0,
        output_name: str = "polyreduce1",
    ) -> dict:
        """Reduce polygon count of a geometry node.

        Args:
            geo_path: Path to the geometry node (e.g., '/obj/geo1').
            target_percent: Target percentage of polygons to keep (0.1-100).
            output_name: Name for the polyreduce node.

        Returns:
            dict: Result of the operation including polygon counts.
        """
        try:
            logger.info(f"🔹 polyreduce | geo_path={geo_path}, target={target_percent}%")

            result = executor.execute(
                POLYREDUCE_SCRIPT,
                timeout=30.0,
                context={
                    "geo_path": geo_path,
                    "target_percent": target_percent,
                    "output_name": output_name,
                }
            )

            if result["success"]:
                data = result["data"]
                elapsed = result.get("_timing", {}).get("duration_seconds", 0)
                logger.info(f"✅ polyreduce completed in {elapsed:.2f}s")

                return {
                    "success": True,
                    "message": data["message"],
                    "prompt": f"Polyreduce completed: {data['message']}. Node: {data['node_path']}",
                    "error": None,
                    "context": data,
                    "_timing": result.get("_timing")
                }
            else:
                error = result.get("error", "Unknown error")
                logger.error(f"❌ polyreduce failed: {error}")
                return result

        except ProcessTimeoutError as e:
            logger.error(f"⏰ polyreduce TIMEOUT: {e}")
            return {
                "success": False,
                "error": "Operation timed out after 30 seconds",
                "error_type": "Timeout",
                "message": "Polyreduce operation took too long. The process was killed.",
            }
        except Exception as e:
            logger.error(f"❌ polyreduce ERROR: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def mirror(
        geo_path: str,
        axis: str = "x",
        merge: bool = True,
        consolidate_seam: bool = True,
        output_name: str = "mirror",
    ) -> dict:
        """Mirror geometry along specified axis to create symmetry.

        Args:
            geo_path: Path to the geometry node (e.g., '/obj/geo1').
            axis: Axis to mirror along (x/y/z).
            merge: Merge mirrored geometry with original.
            consolidate_seam: Fuse points along the mirror seam.
            output_name: Name for the mirror node.

        Returns:
            dict: Result of the mirror operation.
        """
        try:
            result = executor.execute(
                MIRROR_SCRIPT,
                timeout=30.0,
                context={
                    "geo_path": geo_path,
                    "axis": axis,
                    "merge": merge,
                    "consolidate_seam": consolidate_seam,
                    "output_name": output_name,
                }
            )

            if result["success"]:
                data = result["data"]
                return {
                    "success": True,
                    "message": data["message"],
                    "prompt": f"Mirror completed: {data['message']}. Node: {data['node_path']}, {data['poly_count']} polygons.",
                    "error": None,
                    "context": data,
                    "_timing": result.get("_timing")
                }
            else:
                return result

        except ProcessTimeoutError as e:
            return {"success": False, "error": "Operation timed out after 30s", "error_type": "Timeout"}
        except Exception as e:
            logger.error(f"❌ mirror error: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def delete_half(
        geo_path: str,
        axis: str = "x",
        keep_side: str = "positive",
        output_name: str = "delete_half",
    ) -> dict:
        """Delete half of geometry along specified axis.

        Args:
            geo_path: Path to the geometry node (e.g., '/obj/geo1').
            axis: Axis to split along (x/y/z).
            keep_side: Which side to keep (positive/negative).
            output_name: Name for the delete node.

        Returns:
            dict: Result of the delete operation.
        """
        try:
            result = executor.execute(
                DELETE_HALF_SCRIPT,
                timeout=20.0,
                context={
                    "geo_path": geo_path,
                    "axis": axis,
                    "keep_side": keep_side,
                    "output_name": output_name,
                }
            )

            if result["success"]:
                data = result["data"]
                return {
                    "success": True,
                    "message": data["message"],
                    "prompt": f"Delete half completed: {data['message']}. Node: {data['node_path']}",
                    "error": None,
                    "context": data,
                    "_timing": result.get("_timing")
                }
            else:
                return result

        except ProcessTimeoutError as e:
            return {"success": False, "error": "Operation timed out after 20s", "error_type": "Timeout"}
        except Exception as e:
            logger.error(f"❌ delete_half error: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def boolean(
        geo_path_a: str,
        geo_path_b: str = "",
        operation: str = "union",
        output_name: str = "boolean",
    ) -> dict:
        """Boolean operations on geometry (union/subtract/intersect).

        Args:
            geo_path_a: Path to the first geometry node (A).
            geo_path_b: Path to the second geometry node (B), optional.
            operation: Boolean operation type (union/subtract/intersect/shatter).
            output_name: Name for the boolean node.

        Returns:
            dict: Result of the boolean operation.
        """
        try:
            result = executor.execute(
                BOOLEAN_SCRIPT,
                timeout=45.0,  # Boolean can be slow
                context={
                    "geo_path_a": geo_path_a,
                    "geo_path_b": geo_path_b,
                    "operation": operation,
                    "output_name": output_name,
                }
            )

            if result["success"]:
                data = result["data"]
                return {
                    "success": True,
                    "message": data["message"],
                    "prompt": f"Boolean {operation} completed: {data['message']}",
                    "error": None,
                    "context": data,
                    "_timing": result.get("_timing")
                }
            else:
                return result

        except ProcessTimeoutError as e:
            return {"success": False, "error": "Operation timed out after 45s", "error_type": "Timeout"}
        except Exception as e:
            logger.error(f"❌ boolean error: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def import_geometry(
        file_path: str,
        node_name: str = "imported_geo",
    ) -> dict:
        """Import geometry from file (FBX/OBJ/Alembic).

        Args:
            file_path: Path to the geometry file (e.g., 'C:/Models/mesh.fbx').
            node_name: Name for the imported geometry node.

        Returns:
            dict: Result of the import operation.
        """
        try:
            result = executor.execute(
                IMPORT_GEOMETRY_SCRIPT,
                timeout=60.0,  # Import can be slow for large files
                context={
                    "file_path": file_path,
                    "node_name": node_name,
                }
            )

            if result["success"]:
                data = result["data"]
                return {
                    "success": True,
                    "message": data["message"],
                    "prompt": f"Import completed: {data['message']}. Node: {data['node_path']}",
                    "error": None,
                    "context": data,
                    "_timing": result.get("_timing")
                }
            else:
                return result

        except ProcessTimeoutError as e:
            return {"success": False, "error": "Import timed out after 60s", "error_type": "Timeout"}
        except Exception as e:
            logger.error(f"❌ import_geometry error: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    logger.info(f"✅ Server '{name}' configured successfully")
    logger.info(f"Registered tools: get_scene_state, create_box, polyreduce, mirror, delete_half, boolean, import_geometry")
    logger.info(f"Process isolation: ENABLED ✅")
    logger.info(f"Timeout protection: ACTIVE ✅")

    return mcp, executor


def main():
    """Main entry point for the MCP server v2."""
    import argparse

    parser = argparse.ArgumentParser(description="Houdini MCP Server v2 (Process-Isolated)")
    parser.add_argument("--name", default="Houdini-v2", help="Server name")
    parser.add_argument(
        "--houdini-path",
        default=None,
        help="Path to Houdini bin directory (default: auto-detect)",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")

    try:
        logger.info("🚀 Starting Houdini MCP Server v2...")
        mcp, _ = create_server(name=args.name, houdini_bin_path=args.houdini_path)
        logger.info("✅ Server ready, running...")
        mcp.run()
    except Exception as e:
        logger.error(f"❌ Error starting server: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
