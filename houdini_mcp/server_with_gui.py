"""Codex MCP bridge for the persistent Houdini daemon."""

from __future__ import annotations

import asyncio
import logging

from mcp.server.fastmcp import FastMCP

from houdini_mcp.daemon_client import invoke_operation
from houdini_mcp.daemon_launcher import ensure_daemon_running
from houdini_mcp.utils.logging_config import setup_logging
from houdini_mcp.utils.pipeline_tools import PipelineOrchestrator

logger = setup_logging(
    name="houdini-mcp-bridge",
    log_level="INFO",
    enable_file_logging=True,
    enable_console_logging=True,
)


def create_server(name: str = "Houdini-Bridge") -> FastMCP:
    ensure_daemon_running()
    mcp = FastMCP(name=name)
    pipeline = PipelineOrchestrator("houdini", invoke_operation)

    @mcp.tool()
    async def get_scene_state() -> dict:
        return await invoke_operation("get_scene_state", {})

    @mcp.tool()
    async def create_box(
        node_name: str = "box",
        size_x: float = 1.0,
        size_y: float = 1.0,
        size_z: float = 1.0,
    ) -> dict:
        return await invoke_operation(
            "create_box",
            {
                "node_name": node_name,
                "size_x": size_x,
                "size_y": size_y,
                "size_z": size_z,
            },
        )

    @mcp.tool()
    async def clean_mesh(
        geo_path: str,
        output_name: str = "clean_mesh",
        fuse_points: bool = True,
        fuse_distance: float = 0.0001,
        remove_degenerate: bool = True,
        fix_overlaps: bool = True,
        delete_unused_points: bool = True,
    ) -> dict:
        return await invoke_operation(
            "clean_mesh",
            {
                "geo_path": geo_path,
                "output_name": output_name,
                "fuse_points": fuse_points,
                "fuse_distance": fuse_distance,
                "remove_degenerate": remove_degenerate,
                "fix_overlaps": fix_overlaps,
                "delete_unused_points": delete_unused_points,
            },
        )

    @mcp.tool()
    async def cleanup_attributes(
        geo_path: str,
        output_name: str = "cleanup_attributes",
        point_attributes: str = "",
        vertex_attributes: str = "",
        primitive_attributes: str = "",
        detail_attributes: str = "",
        remove_standard: bool = True,
    ) -> dict:
        return await invoke_operation(
            "cleanup_attributes",
            {
                "geo_path": geo_path,
                "output_name": output_name,
                "point_attributes": point_attributes,
                "vertex_attributes": vertex_attributes,
                "primitive_attributes": primitive_attributes,
                "detail_attributes": detail_attributes,
                "remove_standard": remove_standard,
            },
        )

    @mcp.tool()
    async def fuse_points(
        geo_path: str,
        output_name: str = "fuse_points",
        distance: float = 0.001,
    ) -> dict:
        return await invoke_operation(
            "fuse_points",
            {
                "geo_path": geo_path,
                "output_name": output_name,
                "distance": distance,
            },
        )

    @mcp.tool()
    async def normalize_normals(
        geo_path: str,
        output_name: str = "normalize_normals",
        cusp_angle: float = 60.0,
        reverse: bool = False,
    ) -> dict:
        return await invoke_operation(
            "normalize_normals",
            {
                "geo_path": geo_path,
                "output_name": output_name,
                "cusp_angle": cusp_angle,
                "reverse": reverse,
            },
        )

    @mcp.tool()
    async def add_output_null(
        node_path: str,
        null_name: str = "OUT",
    ) -> dict:
        return await invoke_operation(
            "add_output_null",
            {
                "node_path": node_path,
                "null_name": null_name,
            },
        )

    @mcp.tool()
    async def freeze_transform(
        node_path: str,
        output_name: str = "frozen_geo",
        add_output_null: bool = True,
    ) -> dict:
        return await invoke_operation(
            "freeze_transform",
            {
                "node_path": node_path,
                "output_name": output_name,
                "add_output_null": add_output_null,
            },
        )

    @mcp.tool()
    async def create_subnet_from_nodes(
        node_paths: list[str] | None = None,
        subnet_name: str = "generated_subnet",
    ) -> dict:
        return await invoke_operation(
            "create_subnet_from_nodes",
            {
                "node_paths": node_paths or [],
                "subnet_name": subnet_name,
            },
        )

    @mcp.tool()
    async def create_hda_from_selection(
        asset_name: str,
        node_paths: list[str] | None = None,
        hda_file_path: str = "",
        asset_label: str = "",
        version: str = "",
        save_as_embedded: bool = False,
    ) -> dict:
        return await invoke_operation(
            "create_hda_from_selection",
            {
                "asset_name": asset_name,
                "node_paths": node_paths or [],
                "hda_file_path": hda_file_path,
                "asset_label": asset_label,
                "version": version,
                "save_as_embedded": save_as_embedded,
            },
        )

    @mcp.tool()
    async def polyreduce(
        geo_path: str,
        target_percent: float = 50.0,
        output_name: str = "polyreduce1",
    ) -> dict:
        return await invoke_operation(
            "polyreduce",
            {
                "geo_path": geo_path,
                "target_percent": target_percent,
                "output_name": output_name,
            },
        )

    @mcp.tool()
    async def smooth(
        geo_path: str,
        strength: float = 0.5,
        output_name: str = "smooth1",
    ) -> dict:
        return await invoke_operation(
            "smooth",
            {
                "geo_path": geo_path,
                "strength": strength,
                "output_name": output_name,
            },
        )

    @mcp.tool()
    async def mirror(
        geo_path: str,
        axis: str = "x",
        merge: bool = True,
        consolidate_seam: bool = True,
        output_name: str = "mirror",
    ) -> dict:
        return await invoke_operation(
            "mirror",
            {
                "geo_path": geo_path,
                "axis": axis,
                "merge": merge,
                "consolidate_seam": consolidate_seam,
                "output_name": output_name,
            },
        )

    @mcp.tool()
    async def delete_half(
        geo_path: str,
        axis: str = "x",
        keep_side: str = "positive",
        output_name: str = "delete_half",
    ) -> dict:
        return await invoke_operation(
            "delete_half",
            {
                "geo_path": geo_path,
                "axis": axis,
                "keep_side": keep_side,
                "output_name": output_name,
            },
        )

    @mcp.tool()
    async def boolean(
        geo_path_a: str,
        geo_path_b: str = "",
        operation: str = "union",
        output_name: str = "boolean",
    ) -> dict:
        return await invoke_operation(
            "boolean",
            {
                "geo_path_a": geo_path_a,
                "geo_path_b": geo_path_b,
                "operation": operation,
                "output_name": output_name,
            },
        )

    @mcp.tool()
    async def import_geometry(
        file_path: str,
        node_name: str = "imported_geo",
    ) -> dict:
        return await invoke_operation(
            "import_geometry",
            {
                "file_path": file_path,
                "node_name": node_name,
            },
        )

    @mcp.tool()
    async def import_model(
        file_path: str,
        node_name: str = "imported_geo",
        uniform_scale: float = 1.0,
        center_to_origin: bool = False,
        normalize_normals: bool = False,
        output_name: str = "import_model",
    ) -> dict:
        return await invoke_operation(
            "import_model",
            {
                "file_path": file_path,
                "node_name": node_name,
                "uniform_scale": uniform_scale,
                "center_to_origin": center_to_origin,
                "normalize_normals": normalize_normals,
                "output_name": output_name,
            },
        )

    @mcp.tool()
    async def export_geometry(
        geo_path: str,
        output_path: str,
        file_type: str = "fbx",
    ) -> dict:
        return await invoke_operation(
            "export_geometry",
            {
                "geo_path": geo_path,
                "output_path": output_path,
                "file_type": file_type,
            },
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
    logger.info("Starting Houdini MCP bridge")
    try:
        ensure_daemon_running()
        mcp = create_server()
        asyncio.run(mcp.run_stdio_async())
    except Exception as e:
        logger.error(f"Bridge crashed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
