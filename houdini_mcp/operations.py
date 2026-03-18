"""Shared Houdini operation execution for daemon-backed architecture."""

from __future__ import annotations

import asyncio
from typing import Any, Dict

from houdini_mcp.core.operation_scripts import (
    BOOLEAN_SCRIPT,
    CREATE_BOX_SCRIPT,
    DELETE_HALF_SCRIPT,
    GET_SCENE_STATE_SCRIPT,
    IMPORT_GEOMETRY_SCRIPT,
    MIRROR_SCRIPT,
    POLYREDUCE_SCRIPT,
)
from houdini_mcp.core.process_executor import ProcessExecutor, ProcessTimeoutError


async def execute_operation(
    executor: ProcessExecutor,
    operation: str,
    params: Dict[str, Any],
) -> Dict[str, Any]:
    """Execute a named Houdini operation and normalize the response."""
    if operation == "get_scene_state":
        return await _run_get_scene_state(executor)
    if operation == "create_box":
        return await _run_create_box(executor, params)
    if operation == "polyreduce":
        return await _run_polyreduce(executor, params)
    if operation == "mirror":
        return await _run_mirror(executor, params)
    if operation == "delete_half":
        return await _run_delete_half(executor, params)
    if operation == "boolean":
        return await _run_boolean(executor, params)
    if operation == "import_geometry":
        return await _run_import_geometry(executor, params)

    return {
        "success": False,
        "error": f"Unknown operation: {operation}",
        "error_type": "UnknownOperation",
    }


async def _execute(
    executor: ProcessExecutor,
    script: str,
    timeout: float,
    params: Dict[str, Any],
) -> Dict[str, Any]:
    return await asyncio.to_thread(
        executor.execute,
        script,
        timeout=timeout,
        context=params,
    )


async def _run_get_scene_state(executor: ProcessExecutor) -> Dict[str, Any]:
    try:
        return await _execute(executor, GET_SCENE_STATE_SCRIPT, 10.0, {})
    except ProcessTimeoutError as e:
        return {"success": False, "error": str(e), "error_type": "Timeout"}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def _run_create_box(executor: ProcessExecutor, params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        result = await _execute(executor, CREATE_BOX_SCRIPT, 15.0, params)
        if result.get("success"):
            data = result["data"]
            return {
                "success": True,
                "message": data["message"],
                "prompt": f"Box created at {data['node_path']}. Size: {data['box_size']}, {data['poly_count']} polygons.",
                "error": None,
                "context": data,
                "_timing": result.get("_timing"),
            }
        return result
    except ProcessTimeoutError:
        return {"success": False, "error": "Operation timed out after 15s", "error_type": "Timeout"}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def _run_polyreduce(executor: ProcessExecutor, params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        result = await _execute(executor, POLYREDUCE_SCRIPT, 30.0, params)
        if result.get("success"):
            data = result["data"]
            return {
                "success": True,
                "message": data["message"],
                "prompt": f"Polyreduce completed: {data['message']}. Node: {data['node_path']}",
                "error": None,
                "context": data,
                "_timing": result.get("_timing"),
            }
        return result
    except ProcessTimeoutError:
        return {"success": False, "error": "Operation timed out after 30 seconds", "error_type": "Timeout"}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def _run_mirror(executor: ProcessExecutor, params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        result = await _execute(executor, MIRROR_SCRIPT, 30.0, params)
        if result.get("success"):
            data = result["data"]
            return {
                "success": True,
                "message": data["message"],
                "prompt": f"Mirror completed: {data['message']}. Node: {data['node_path']}, {data['poly_count']} polygons.",
                "error": None,
                "context": data,
                "_timing": result.get("_timing"),
            }
        return result
    except ProcessTimeoutError:
        return {"success": False, "error": "Operation timed out after 30s", "error_type": "Timeout"}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def _run_delete_half(executor: ProcessExecutor, params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        result = await _execute(executor, DELETE_HALF_SCRIPT, 20.0, params)
        if result.get("success"):
            data = result["data"]
            return {
                "success": True,
                "message": data["message"],
                "prompt": f"Delete half completed: {data['message']}. Node: {data['node_path']}",
                "error": None,
                "context": data,
                "_timing": result.get("_timing"),
            }
        return result
    except ProcessTimeoutError:
        return {"success": False, "error": "Operation timed out after 20s", "error_type": "Timeout"}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def _run_boolean(executor: ProcessExecutor, params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        result = await _execute(executor, BOOLEAN_SCRIPT, 45.0, params)
        if result.get("success"):
            data = result["data"]
            return {
                "success": True,
                "message": data["message"],
                "prompt": f"Boolean {data['operation']} completed: {data['message']}",
                "error": None,
                "context": data,
                "_timing": result.get("_timing"),
            }
        return result
    except ProcessTimeoutError:
        return {"success": False, "error": "Operation timed out after 45s", "error_type": "Timeout"}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def _run_import_geometry(executor: ProcessExecutor, params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        result = await _execute(executor, IMPORT_GEOMETRY_SCRIPT, 60.0, params)
        if result.get("success"):
            data = result["data"]
            return {
                "success": True,
                "message": data["message"],
                "prompt": f"Import completed: {data['message']}. Node: {data['node_path']}",
                "error": None,
                "context": data,
                "_timing": result.get("_timing"),
            }
        return result
    except ProcessTimeoutError:
        return {"success": False, "error": "Import timed out after 60s", "error_type": "Timeout"}
    except Exception as e:
        return {"success": False, "error": str(e)}
