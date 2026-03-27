"""Codex MCP bridge for the persistent Blender daemon."""

from __future__ import annotations

import asyncio

from mcp.server.fastmcp import FastMCP

from blender_mcp.daemon_client import invoke_operation
from blender_mcp.daemon_launcher import ensure_daemon_running
from houdini_mcp.gui.gui_launcher import ensure_unified_gui_running
from houdini_mcp.utils.logging_config import setup_logging
from houdini_mcp.utils.pipeline_tools import PipelineOrchestrator

logger = setup_logging(
    name="blender-mcp-bridge",
    log_level="INFO",
    enable_file_logging=True,
    enable_console_logging=True,
)


def create_server(name: str = "Blender-Bridge") -> FastMCP:
    ensure_unified_gui_running()
    ensure_daemon_running()
    mcp = FastMCP(name=name)
    pipeline = PipelineOrchestrator("blender", invoke_operation)

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
    async def import_model(
        input_path: str,
        output_blend: str = "",
        clear_scene: bool = True,
        location: list[float] | None = None,
        rotation: list[float] | None = None,
        scale: list[float] | None = None,
        apply_transform: bool = False,
        auto_triangulate: bool = False,
        recalculate_normals: bool = False,
        merge_by_distance: bool = False,
        merge_distance: float = 0.0001,
    ) -> dict:
        return await invoke_operation(
            "import_model",
            {
                "input_path": input_path,
                "output_blend": output_blend,
                "clear_scene": clear_scene,
                "location": location or [0.0, 0.0, 0.0],
                "rotation": rotation or [0.0, 0.0, 0.0],
                "scale": scale or [1.0, 1.0, 1.0],
                "apply_transform": apply_transform,
                "auto_triangulate": auto_triangulate,
                "recalculate_normals": recalculate_normals,
                "merge_by_distance": merge_by_distance,
                "merge_distance": merge_distance,
            },
        )

    @mcp.tool()
    async def export_fbx(output_path: str, input_blend: str = "") -> dict:
        return await invoke_operation(
            "export_fbx",
            {"output_path": output_path, "input_blend": input_blend},
        )

    @mcp.tool()
    async def capture_screenshot(
        output_path: str,
        input_blend: str = "",
        width: int = 1024,
        height: int = 1024,
    ) -> dict:
        return await invoke_operation(
            "capture_screenshot",
            {"output_path": output_path, "input_blend": input_blend, "width": width, "height": height},
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

    @mcp.tool()
    async def workflow_run(
        steps: list[dict],
        stop_on_error: bool = True,
        workflow_name: str = "",
        metadata: dict | None = None,
    ) -> dict:
        return await pipeline.workflow_run(
            steps=steps,
            stop_on_error=stop_on_error,
            workflow_name=workflow_name,
            metadata=metadata,
        )

    @mcp.tool()
    async def batch_run(
        operations: list[dict],
        continue_on_error: bool = True,
        batch_name: str = "",
        metadata: dict | None = None,
    ) -> dict:
        return await pipeline.batch_run(
            operations=operations,
            continue_on_error=continue_on_error,
            batch_name=batch_name,
            metadata=metadata,
        )

    @mcp.tool()
    async def validate_asset(
        path: str,
        expected_types: list[str] | None = None,
        required_tokens: list[str] | None = None,
        min_size_bytes: int = 1,
    ) -> dict:
        return await pipeline.validate_asset(
            path=path,
            expected_types=expected_types,
            required_tokens=required_tokens,
            min_size_bytes=min_size_bytes,
        )

    @mcp.tool()
    async def publish_asset(
        input_path: str,
        publish_dir: str,
        asset_name: str = "",
        version: str = "",
        write_manifest: bool = True,
    ) -> dict:
        return await pipeline.publish_asset(
            input_path=input_path,
            publish_dir=publish_dir,
            asset_name=asset_name,
            version=version,
            write_manifest=write_manifest,
        )

    @mcp.tool()
    async def get_job_status(job_id: str = "", include_steps: bool = True) -> dict:
        return await pipeline.get_job_status(job_id=job_id, include_steps=include_steps)

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
