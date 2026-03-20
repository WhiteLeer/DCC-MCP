"""CLI bridge for Unity to invoke Houdini MCP daemon workflows."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict

from houdini_mcp.daemon_client import invoke_operation


async def _invoke(operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
    result = await invoke_operation(operation, params)
    if not result.get("success", False):
        raise RuntimeError(result.get("error", f"{operation} failed"))
    return result


def _next_geo_path(result: Dict[str, Any], fallback: str) -> str:
    context = result.get("context", {}) if isinstance(result, dict) else {}
    return str(context.get("node_path") or fallback)


async def process_lod(args: argparse.Namespace) -> Dict[str, Any]:
    input_path = str(Path(args.input).resolve())
    output_path = str(Path(args.output).resolve())

    imported = await _invoke(
        "import_geometry",
        {
            "file_path": input_path,
            "node_name": args.node_name,
        },
    )
    geo_path = _next_geo_path(imported, "")
    steps = [{"operation": "import_geometry", "context": imported.get("context", {})}]

    cleaned = await _invoke(
        "clean_mesh",
        {
            "geo_path": geo_path,
            "output_name": "clean_for_unity",
            "fuse_points": True,
            "remove_degenerate": True,
            "fix_overlaps": True,
            "delete_unused_points": True,
        },
    )
    geo_path = _next_geo_path(cleaned, geo_path)
    steps.append({"operation": "clean_mesh", "context": cleaned.get("context", {})})

    if args.enable_polyreduce:
        reduced = await _invoke(
            "polyreduce",
            {
                "geo_path": geo_path,
                "target_percent": float(args.target_percent) * 100.0,
                "output_name": "reduce_for_unity",
            },
        )
        geo_path = _next_geo_path(reduced, geo_path)
        steps.append({"operation": "polyreduce", "context": reduced.get("context", {})})

    if args.enable_smooth:
        smoothed = await _invoke(
            "smooth",
            {
                "geo_path": geo_path,
                "strength": float(args.smooth_strength),
                "output_name": "smooth_for_unity",
            },
        )
        geo_path = _next_geo_path(smoothed, geo_path)
        steps.append({"operation": "smooth", "context": smoothed.get("context", {})})

    normalized = await _invoke(
        "normalize_normals",
        {
            "geo_path": geo_path,
            "output_name": "normals_for_unity",
            "cusp_angle": 60.0,
            "reverse": False,
        },
    )
    geo_path = _next_geo_path(normalized, geo_path)
    steps.append({"operation": "normalize_normals", "context": normalized.get("context", {})})

    exported = await _invoke(
        "export_geometry",
        {
            "geo_path": geo_path,
            "output_path": output_path,
            "file_type": "fbx",
        },
    )
    steps.append({"operation": "export_geometry", "context": exported.get("context", {})})

    return {
        "success": True,
        "message": "LOD processing completed via Houdini MCP",
        "context": {
            "input_path": input_path,
            "output_path": output_path,
            "steps": steps,
        },
    }


async def ping(_: argparse.Namespace) -> Dict[str, Any]:
    scene = await _invoke("get_scene_state", {})
    return {
        "success": True,
        "message": "Houdini MCP daemon reachable",
        "context": scene.get("data", {}),
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Unity bridge CLI for Houdini MCP")
    sub = parser.add_subparsers(dest="command", required=True)

    lod = sub.add_parser("process-lod", help="Run import/clean/reduce/smooth/export workflow")
    lod.add_argument("--input", required=True, help="Input mesh file path")
    lod.add_argument("--output", required=True, help="Output mesh file path")
    lod.add_argument("--target-percent", type=float, default=1.0, help="Target ratio in [0,1]")
    lod.add_argument("--enable-polyreduce", type=int, default=1, help="1 to enable polyreduce")
    lod.add_argument("--enable-smooth", type=int, default=0, help="1 to enable smooth")
    lod.add_argument("--smooth-strength", type=float, default=0.5, help="Smooth strength in [0,1]")
    lod.add_argument("--node-name", default="unity_import", help="Temporary object name in Houdini")

    sub.add_parser("ping", help="Validate daemon connectivity")
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    if args.command == "process-lod":
        args.target_percent = max(0.01, min(1.0, float(args.target_percent)))
        args.enable_polyreduce = int(args.enable_polyreduce) == 1
        args.enable_smooth = int(args.enable_smooth) == 1
        args.smooth_strength = max(0.0, min(1.0, float(args.smooth_strength)))

    try:
        if args.command == "process-lod":
            result = asyncio.run(process_lod(args))
        elif args.command == "ping":
            result = asyncio.run(ping(args))
        else:
            raise RuntimeError(f"Unknown command: {args.command}")
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except Exception as exc:
        payload = {"success": False, "error": str(exc), "command": args.command}
        print(json.dumps(payload, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
