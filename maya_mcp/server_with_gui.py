"""Codex MCP bridge for the persistent Maya daemon."""

from __future__ import annotations

import asyncio

from mcp.server.fastmcp import FastMCP

from maya_mcp.daemon_client import invoke_operation
from maya_mcp.daemon_launcher import ensure_daemon_running
from houdini_mcp.utils.logging_config import setup_logging

logger = setup_logging(
    name="maya-mcp-bridge",
    log_level="INFO",
    enable_file_logging=True,
    enable_console_logging=True,
)


def create_server(name: str = "Maya-Bridge") -> FastMCP:
    ensure_daemon_running()
    mcp = FastMCP(name=name)

    @mcp.tool()
    async def get_scene_state() -> dict:
        return await invoke_operation("get_scene_state", {})

    @mcp.tool()
    async def create_poly_cube(
        name: str = "polyCube1",
        width: float = 1.0,
        height: float = 1.0,
        depth: float = 1.0,
    ) -> dict:
        return await invoke_operation(
            "create_poly_cube",
            {"name": name, "width": width, "height": height, "depth": depth},
        )

    @mcp.tool()
    async def clean_mesh(node: str = "") -> dict:
        return await invoke_operation("clean_mesh", {"node": node})

    @mcp.tool()
    async def freeze_transform(node: str = "") -> dict:
        return await invoke_operation("freeze_transform", {"node": node})

    @mcp.tool()
    async def delete_history(node: str = "") -> dict:
        return await invoke_operation("delete_history", {"node": node})

    @mcp.tool()
    async def center_pivot(node: str = "") -> dict:
        return await invoke_operation("center_pivot", {"node": node})

    @mcp.tool()
    async def create_locator(name: str = "locator1") -> dict:
        return await invoke_operation("create_locator", {"name": name})

    @mcp.tool()
    async def combine_meshes(nodes: list[str] | None = None, name: str = "combined_mesh") -> dict:
        return await invoke_operation("combine_meshes", {"nodes": nodes or [], "name": name})

    @mcp.tool()
    async def separate_mesh(node: str = "") -> dict:
        return await invoke_operation("separate_mesh", {"node": node})

    @mcp.tool()
    async def triangulate_mesh(node: str = "") -> dict:
        return await invoke_operation("triangulate_mesh", {"node": node})

    @mcp.tool()
    async def quad_mesh(node: str = "") -> dict:
        return await invoke_operation("quad_mesh", {"node": node})

    @mcp.tool()
    async def delete_unused_nodes() -> dict:
        return await invoke_operation("delete_unused_nodes", {})

    @mcp.tool()
    async def rename_node(node: str, new_name: str) -> dict:
        return await invoke_operation("rename_node", {"node": node, "new_name": new_name})

    @mcp.tool()
    async def duplicate_node(node: str = "") -> dict:
        return await invoke_operation("duplicate_node", {"node": node})

    @mcp.tool()
    async def parent_node(node: str, parent: str) -> dict:
        return await invoke_operation("parent_node", {"node": node, "parent": parent})

    return mcp


def main() -> None:
    logger.info("Starting Maya MCP bridge")
    try:
        ensure_daemon_running()
        mcp = create_server()
        asyncio.run(mcp.run_stdio_async())
    except Exception as e:
        logger.error(f"Bridge crashed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
