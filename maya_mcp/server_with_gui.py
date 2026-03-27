"""Codex MCP bridge for the persistent Maya daemon."""

from __future__ import annotations

import asyncio

from mcp.server.fastmcp import FastMCP

from maya_mcp.daemon_client import invoke_operation
from maya_mcp.daemon_launcher import ensure_daemon_running
from houdini_mcp.gui.gui_launcher import ensure_unified_gui_running
from houdini_mcp.utils.logging_config import setup_logging
from houdini_mcp.utils.pipeline_tools import PipelineOrchestrator

logger = setup_logging(
    name="maya-mcp-bridge",
    log_level="INFO",
    enable_file_logging=True,
    enable_console_logging=True,
)


def create_server(name: str = "Maya-Bridge") -> FastMCP:
    ensure_unified_gui_running()
    ensure_daemon_running()
    mcp = FastMCP(name=name)
    pipeline = PipelineOrchestrator("maya", invoke_operation)

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

    @mcp.tool()
    async def import_geometry(
        input_path: str,
        namespace: str = "mcp",
        clean_scene: bool = False,
        group_name: str = "",
        merge_namespaces_on_clash: bool = True,
        file_options: str = "v=0;",
    ) -> dict:
        return await invoke_operation(
            "import_geometry",
            {
                "input_path": input_path,
                "namespace": namespace,
                "clean_scene": clean_scene,
                "group_name": group_name,
                "merge_namespaces_on_clash": merge_namespaces_on_clash,
                "file_options": file_options,
            },
        )

    @mcp.tool()
    async def import_model(
        input_path: str,
        namespace: str = "mcp",
        clean_scene: bool = False,
        group_name: str = "",
        merge_namespaces_on_clash: bool = True,
        file_options: str = "v=0;",
        uniform_scale: float = 1.0,
        freeze_after_import: bool = False,
        center_pivot_after_import: bool = False,
        delete_history_after_import: bool = False,
    ) -> dict:
        return await invoke_operation(
            "import_model",
            {
                "input_path": input_path,
                "namespace": namespace,
                "clean_scene": clean_scene,
                "group_name": group_name,
                "merge_namespaces_on_clash": merge_namespaces_on_clash,
                "file_options": file_options,
                "uniform_scale": uniform_scale,
                "freeze_after_import": freeze_after_import,
                "center_pivot_after_import": center_pivot_after_import,
                "delete_history_after_import": delete_history_after_import,
            },
        )

    @mcp.tool()
    async def capture_screenshot(
        output_path: str,
        camera: str = "persp",
        width: int = 1024,
        height: int = 1024,
    ) -> dict:
        return await invoke_operation(
            "capture_screenshot",
            {"output_path": output_path, "camera": camera, "width": width, "height": height},
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
