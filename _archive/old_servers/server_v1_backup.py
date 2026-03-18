"""Houdini MCP Server main module."""

import logging
import os
import sys
import threading
import time
from typing import Optional

from mcp.server.fastmcp import FastMCP
from dcc_mcp_core.actions.manager import ActionManager

from houdini_mcp.adapter.houdini_adapter import get_adapter
# Production utilities
from houdini_mcp.utils.logging_config import setup_logging, log_operation, log_error
from houdini_mcp.utils.tool_wrapper import production_tool
from houdini_mcp.utils.health_check import create_simple_health_checker
from houdini_mcp.utils.timeout import TimeoutError


# Enable hot reload
try:
    # Add houdini-mcp root to path
    houdini_mcp_root = os.path.dirname(os.path.dirname(__file__))
    if houdini_mcp_root not in sys.path:
        sys.path.insert(0, houdini_mcp_root)

    from fix_hot_reload import enable_hot_reload
    enable_hot_reload()
except Exception as e:
    print(f"[WARNING] Failed to enable hot reload: {e}", file=sys.stderr)

# Configure production logging
logger = setup_logging(
    name="houdini-mcp",
    log_level="INFO",
    enable_file_logging=True,
    enable_console_logging=True,
)
logger.info("=" * 80)
logger.info("🚀 Houdini MCP Server - Production Mode")
logger.info("=" * 80)


def create_server(
    name: str = "Houdini",
    houdini_bin_path: Optional[str] = None,
) -> tuple[FastMCP, ActionManager]:
    """Create and configure the MCP server.

    Args:
        name: The name of the MCP server.
        houdini_bin_path: Path to Houdini bin directory.

    Returns:
        tuple: (FastMCP server, ActionManager)
    """
    # Create MCP server
    mcp = FastMCP(name=name)

    # Initialize Houdini adapter
    logger.info("Initializing Houdini adapter...")
    adapter = get_adapter(houdini_bin_path)

    try:
        adapter.initialize()
    except Exception as e:
        logger.error(f"Failed to initialize Houdini: {e}")
        raise

    # Create Action Manager with hot reload enabled
    logger.info("Creating Action Manager...")
    action_mgr = ActionManager(
        "houdini",
        load_env_paths=False,
        auto_refresh=True,
        refresh_interval=5,  # Check every 5 seconds
        cache_ttl=1  # Force refresh (1 second cache)
    )

    # Inject Houdini context
    action_mgr.context = adapter.get_context()

    # Discover actions using Registry directly (bypassing ActionManager's path walking)
    actions_dir = os.path.join(
        os.path.dirname(__file__), "actions", "sop"
    )
    logger.info(f"Discovering actions from: {actions_dir}")

    # Register the actions directory for hot reload
    action_mgr.register_action_path(actions_dir)

    # Use ActionRegistry.discover_actions_from_path() for each file
    import glob
    action_files = glob.glob(os.path.join(actions_dir, "*.py"))
    total_discovered = 0
    for action_file in action_files:
        if os.path.basename(action_file).startswith("__"):
            continue
        logger.info(f"  Loading: {os.path.basename(action_file)}")
        try:
            discovered = action_mgr.registry.discover_actions_from_path(
                path=action_file,
                dependencies=adapter.get_context(),
                dcc_name="houdini"
            )
            total_discovered += len(discovered)
            for action_cls in discovered:
                logger.info(f"    ✅ {action_cls.name} ({action_cls.__name__})")
        except Exception as e:
            logger.error(f"    ❌ Error loading {os.path.basename(action_file)}: {e}")

    logger.info(f"✅ Loaded {total_discovered} actions total")

    # Get actions info to verify
    actions_info = action_mgr.get_actions_info()
    actions_dict = actions_info.context.get("actions", {})
    logger.info(f"✅ Registered actions: {list(actions_dict.keys())}")


    # Initialize health checker
    logger.info("🏥 Starting health checker...")
    health_checker = create_simple_health_checker(
        get_scene_state_func=adapter.get_scene_state,
        interval=15.0,  # Check every 15 seconds
    )
    health_checker.start()
    logger.info("🏥 Health checker active")

    # Register MCP Tools
    @production_tool(timeout_seconds=30.0, retry_count=1)
    @mcp.tool()
    def list_actions() -> dict:
        """List all available Houdini actions.

        Returns:
            dict: Dictionary of available actions with their metadata.
        """
        try:
            actions_info = action_mgr.get_actions_info()
            actions_dict = actions_info.to_dict()
            actions_context = actions_dict.get("context", {})
            actions = actions_context.get("actions", {})
            return {
                "success": True,
                "actions": actions_dict,
                "count": len(actions)
            }
        except Exception as e:
            logger.error(f"Error listing actions: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    @production_tool(timeout_seconds=30.0, retry_count=1)
    @mcp.tool()
    def execute_action(action_name: str, **params) -> dict:
        """Execute a Houdini action.

        Args:
            action_name: Name of the action to execute.
            **params: Parameters for the action.

        Returns:
            dict: Result of the action execution.
        """
        try:
            logger.info(f"Executing action: {action_name} with params: {params}")
            # Pass Houdini context explicitly
            result = action_mgr.call_action(
                action_name,
                context=adapter.get_context(),
                **params
            )
            return result.to_dict()
        except Exception as e:
            logger.error(f"Error executing action {action_name}: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to execute action '{action_name}'"
            }

    @production_tool(timeout_seconds=30.0, retry_count=1)
    @mcp.tool()
    def get_scene_state() -> dict:
        """Get current Houdini scene state.

        Returns:
            dict: Current scene information including nodes, frame, etc.
        """
        try:
            state = adapter.get_scene_state()
            return {
                "success": True,
                "scene": state
            }
        except Exception as e:
            logger.error(f"Error getting scene state: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    @production_tool(timeout_seconds=30.0, retry_count=1)
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
            result = action_mgr.call_action(
                "create_box",
                context=adapter.get_context(),
                node_name=node_name,
                size_x=size_x,
                size_y=size_y,
                size_z=size_z,
            )
            return result.to_dict()
        except Exception as e:
            logger.error(f"Error creating box: {e}", exc_info=True)
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
        from houdini_mcp.utils.timeout import with_timeout, TimeoutError
        import time

        start_time = time.time()
        logger.info(f"🔹 START polyreduce | geo_path={geo_path}, target_percent={target_percent}")

        try:
            # Execute with 30 second timeout
            result = with_timeout(
                action_mgr.call_action,
                timeout_seconds=30.0,
                action_name="polyreduce",
                context=adapter.get_context(),
                geo_path=geo_path,
                target_percent=target_percent,
                output_name=output_name,
            )

            elapsed = time.time() - start_time
            logger.info(f"✅ SUCCESS polyreduce | {elapsed:.2f}s")
            return result.to_dict()

        except TimeoutError as e:
            elapsed = time.time() - start_time
            logger.error(f"⏰ TIMEOUT polyreduce | {elapsed:.2f}s | {str(e)}")
            return {
                "success": False,
                "error": "Operation timed out after 30 seconds",
                "error_type": "TimeoutError",
                "_timing": {"duration_seconds": elapsed}
            }
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"❌ ERROR polyreduce | {elapsed:.2f}s | {str(e)}", exc_info=True)
            return {"success": False, "error": str(e), "_timing": {"duration_seconds": elapsed}}

    @production_tool(timeout_seconds=30.0, retry_count=1)
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
            result = action_mgr.call_action(
                "import_geometry",
                context=adapter.get_context(),
                file_path=file_path,
                node_name=node_name,
            )
            return result.to_dict()
        except Exception as e:
            logger.error(f"Error importing geometry: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    @production_tool(timeout_seconds=30.0, retry_count=1)
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
            result = action_mgr.call_action(
                "delete_half",
                context=adapter.get_context(),
                geo_path=geo_path,
                axis=axis,
                keep_side=keep_side,
                output_name=output_name,
            )
            return result.to_dict()
        except Exception as e:
            logger.error(f"Error deleting half: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    @production_tool(timeout_seconds=30.0, retry_count=1)
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
            result = action_mgr.call_action(
                "mirror",
                context=adapter.get_context(),
                geo_path=geo_path,
                axis=axis,
                merge=merge,
                consolidate_seam=consolidate_seam,
                output_name=output_name,
            )
            return result.to_dict()
        except Exception as e:
            logger.error(f"Error mirroring geometry: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    @production_tool(timeout_seconds=30.0, retry_count=1)
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
            result = action_mgr.call_action(
                "boolean",
                context=adapter.get_context(),
                geo_path_a=geo_path_a,
                geo_path_b=geo_path_b,
                operation=operation,
                output_name=output_name,
            )
            return result.to_dict()
        except Exception as e:
            logger.error(f"Error in boolean operation: {e}", exc_info=True)
            return {"success": False, "error": str(e)}


    @mcp.tool()
    @production_tool(timeout_seconds=5.0)
    def health_check() -> dict:
        """Check MCP server and Houdini health status.

        Returns:
            dict: Health status information.
        """
        try:
            health_status = health_checker.get_status()
            scene_state = adapter.get_scene_state()

            return {
                "success": True,
                "server_healthy": health_status["healthy"],
                "houdini_running": scene_state is not None,
                "consecutive_failures": health_status["consecutive_failures"],
                "last_check": health_status["last_check"],
            }
        except Exception as e:
            log_error(logger, "health_check", e)
            return {
                "success": False,
                "error": str(e)
            }


    # Register resources
    @mcp.resource("houdini://scene/state")
    def scene_state_resource() -> str:
        """Get current Houdini scene state as a resource."""
        import json
        state = adapter.get_scene_state()
        return json.dumps(state, indent=2)

    @mcp.resource("houdini://actions/list")
    def actions_list_resource() -> str:
        """Get list of available actions as a resource."""
        import json
        actions_info = action_mgr.get_actions_info()
        actions_dict = actions_info.to_dict()
        return json.dumps(actions_dict, indent=2)

    # Start hot reload background thread
    def hot_reload_worker():
        """Background worker that periodically checks for file changes."""
        logger.info("[HOT RELOAD] Background worker started (5s interval)")
        while True:
            try:
                time.sleep(5)  # Check every 5 seconds

                # Trigger discovery to check for file changes
                # This will call our patched _discover_actions_from_path_with_reload
                if hasattr(action_mgr, '_discover_actions_from_path'):
                    action_mgr._discover_actions_from_path(actions_dir)

            except Exception as e:
                logger.error(f"[HOT RELOAD] Error in background worker: {e}")

    # Start daemon thread (will exit when main program exits)
    reload_thread = threading.Thread(target=hot_reload_worker, daemon=True)
    reload_thread.start()
    logger.info("[HOT RELOAD] ✅ Background scanning enabled (5s interval)")

    logger.info(f"✅ Server '{name}' configured successfully")
    logger.info(f"Registered tools: list_actions, execute_action, get_scene_state, create_box, polyreduce, import_geometry, delete_half, mirror, boolean")
    logger.info(f"Registered resources: houdini://scene/state, houdini://actions/list")

    return mcp, action_mgr


def main():
    """Main entry point for the MCP server."""
    import argparse

    parser = argparse.ArgumentParser(description="Houdini MCP Server")
    parser.add_argument("--name", default="Houdini", help="Server name")
    parser.add_argument(
        "--houdini-path",
        default=None,
        help="Path to Houdini bin directory (default: auto-detect)",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")

    try:
        logger.info("🚀 Starting Houdini MCP Server...")
        mcp, _ = create_server(name=args.name, houdini_bin_path=args.houdini_path)
        logger.info("✅ Server ready, running...")
        mcp.run()
    except Exception as e:
        logger.error(f"❌ Error starting server: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
