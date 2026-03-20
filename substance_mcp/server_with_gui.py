"""Codex MCP bridge for the persistent Substance Designer daemon."""

from __future__ import annotations

import asyncio

from mcp.server.fastmcp import FastMCP

from substance_mcp.daemon_client import invoke_operation
from substance_mcp.daemon_launcher import ensure_daemon_running
from houdini_mcp.utils.logging_config import setup_logging

logger = setup_logging(
    name="substance-designer-mcp-bridge",
    log_level="INFO",
    enable_file_logging=True,
    enable_console_logging=True,
)


def create_server(name: str = "Substance-Designer-Bridge") -> FastMCP:
    ensure_daemon_running()
    mcp = FastMCP(name=name)

    @mcp.tool()
    async def get_scene_state() -> dict:
        return await invoke_operation("get_scene_state", {})

    @mcp.tool()
    async def launch_designer(project_path: str = "") -> dict:
        return await invoke_operation("launch_designer", {"project_path": project_path})

    @mcp.tool()
    async def inspect_sbsar(input_path: str) -> dict:
        return await invoke_operation("inspect_sbsar", {"input_path": input_path})

    @mcp.tool()
    async def render_sbsar(
        input_path: str,
        output_path: str,
        output_format: str = "png",
        graph: str = "",
        output_name: str = "",
        preset: str = "",
        set_values: list[str] | None = None,
    ) -> dict:
        return await invoke_operation(
            "render_sbsar",
            {
                "input_path": input_path,
                "output_path": output_path,
                "output_format": output_format,
                "graph": graph,
                "output_name": output_name,
                "preset": preset,
                "set_values": set_values or [],
            },
        )

    @mcp.tool()
    async def cook_sbs(input_path: str, output_path: str = "", output_name: str = "{inputName}") -> dict:
        return await invoke_operation(
            "cook_sbs",
            {"input_path": input_path, "output_path": output_path, "output_name": output_name},
        )

    @mcp.tool()
    async def list_outputs(output_path: str, pattern: str = "*.*") -> dict:
        return await invoke_operation("list_outputs", {"output_path": output_path, "pattern": pattern})

    @mcp.tool()
    async def analyze_image_palette(input_path: str, top_k: int = 8) -> dict:
        return await invoke_operation(
            "analyze_image_palette",
            {"input_path": input_path, "top_k": top_k},
        )

    @mcp.tool()
    async def harmonize_image_color(
        reference_path: str,
        target_path: str,
        output_path: str,
        intensity: float = 1.0,
        preserve_luminance: float = 0.6,
    ) -> dict:
        return await invoke_operation(
            "harmonize_image_color",
            {
                "reference_path": reference_path,
                "target_path": target_path,
                "output_path": output_path,
                "intensity": intensity,
                "preserve_luminance": preserve_luminance,
            },
        )

    @mcp.tool()
    async def harmonize_images_batch(
        reference_path: str,
        input_dir: str,
        output_dir: str,
        pattern: str = "*.png",
        intensity: float = 1.0,
        preserve_luminance: float = 0.6,
    ) -> dict:
        return await invoke_operation(
            "harmonize_images_batch",
            {
                "reference_path": reference_path,
                "input_dir": input_dir,
                "output_dir": output_dir,
                "pattern": pattern,
                "intensity": intensity,
                "preserve_luminance": preserve_luminance,
            },
        )

    return mcp


def main() -> None:
    logger.info("Starting Substance Designer MCP bridge")
    try:
        ensure_daemon_running()
        mcp = create_server()
        asyncio.run(mcp.run_stdio_async())
    except Exception as e:
        logger.error(f"Bridge crashed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
