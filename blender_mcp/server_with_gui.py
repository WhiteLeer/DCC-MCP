"""Codex MCP bridge for the persistent Blender daemon."""

from __future__ import annotations

import asyncio

from mcp.server.fastmcp import FastMCP

from blender_mcp.daemon_client import invoke_operation
from blender_mcp.daemon_launcher import ensure_daemon_running
from houdini_mcp.utils.logging_config import setup_logging

logger = setup_logging(
    name="blender-mcp-bridge",
    log_level="INFO",
    enable_file_logging=True,
    enable_console_logging=True,
)


def create_server(name: str = "Blender-Bridge") -> FastMCP:
    ensure_daemon_running()
    mcp = FastMCP(name=name)

    @mcp.tool()
    async def get_scene_state() -> dict:
        return await invoke_operation("get_scene_state", {})

    @mcp.tool()
    async def create_cube(
        size: float = 2.0,
        location: list[float] | None = None,
        output_blend: str = "",
    ) -> dict:
        return await invoke_operation(
            "create_cube",
            {
                "size": size,
                "location": location or [0.0, 0.0, 0.0],
                "output_blend": output_blend,
            },
        )

    @mcp.tool()
    async def clean_scene(output_blend: str = "") -> dict:
        return await invoke_operation("clean_scene", {"output_blend": output_blend})

    @mcp.tool()
    async def import_geometry(input_path: str, output_blend: str = "") -> dict:
        return await invoke_operation(
            "import_geometry",
            {"input_path": input_path, "output_blend": output_blend},
        )

    @mcp.tool()
    async def export_fbx(output_path: str, input_blend: str = "") -> dict:
        return await invoke_operation(
            "export_fbx",
            {"output_path": output_path, "input_blend": input_blend},
        )

    @mcp.tool()
    async def decimate_mesh(
        input_blend: str = "",
        output_blend: str = "",
        ratio: float = 0.5,
    ) -> dict:
        return await invoke_operation(
            "decimate_mesh",
            {"input_blend": input_blend, "output_blend": output_blend, "ratio": ratio},
        )

    @mcp.tool()
    async def triangulate_mesh(input_blend: str = "", output_blend: str = "") -> dict:
        return await invoke_operation(
            "triangulate_mesh",
            {"input_blend": input_blend, "output_blend": output_blend},
        )

    @mcp.tool()
    async def recalculate_normals(input_blend: str = "", output_blend: str = "") -> dict:
        return await invoke_operation(
            "recalculate_normals",
            {"input_blend": input_blend, "output_blend": output_blend},
        )

    @mcp.tool()
    async def shade_smooth(
        input_blend: str = "",
        output_blend: str = "",
        auto_smooth_angle: float = 30.0,
    ) -> dict:
        return await invoke_operation(
            "shade_smooth",
            {
                "input_blend": input_blend,
                "output_blend": output_blend,
                "auto_smooth_angle": auto_smooth_angle,
            },
        )

    @mcp.tool()
    async def merge_by_distance(
        input_blend: str = "",
        output_blend: str = "",
        distance: float = 0.0001,
    ) -> dict:
        return await invoke_operation(
            "merge_by_distance",
            {"input_blend": input_blend, "output_blend": output_blend, "distance": distance},
        )

    return mcp


def main() -> None:
    logger.info("Starting Blender MCP bridge")
    try:
        ensure_daemon_running()
        mcp = create_server()
        asyncio.run(mcp.run_stdio_async())
    except Exception as e:
        logger.error(f"Bridge crashed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
