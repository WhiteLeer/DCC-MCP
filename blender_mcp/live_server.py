"""Live bridge script executed inside an interactive Blender process."""

from __future__ import annotations

import json
import os
import queue
import socketserver
import threading
import time
from pathlib import Path

import bpy


HOST = "127.0.0.1"
PORT_RANGE = range(9940, 9960)
STATE_DIR = Path(os.environ.get("BLENDER_MCP_LIVE_STATE_DIR", Path.home() / ".codex" / "mcp" / "blender-mcp" / "live"))
REQUESTS: "queue.Queue[tuple[dict, threading.Event, dict]]" = queue.Queue()
SERVER = None


def _scene_state() -> dict:
    selected = list(bpy.context.selected_objects)
    active = bpy.context.view_layer.objects.active
    return {
        "scene_path": bpy.data.filepath or "untitled",
        "node_count": len(bpy.data.objects),
        "object_count": len(bpy.data.objects),
        "mesh_count": sum(1 for obj in bpy.data.objects if obj.type == "MESH"),
        "assemblies": [],
        "selection": [obj.name for obj in selected],
        "active_object": active.name if active else "",
        "active_object_type": active.type if active else "",
        "scene_name": bpy.context.scene.name,
        "blender_exe": bpy.app.binary_path,
        "blender_version": list(bpy.app.version),
        "running": True,
        "source": "live_gui",
        "pid": os.getpid(),
    }


def _handle(payload: dict) -> dict:
    op = payload.get("operation")
    params = payload.get("params") or {}
    if op == "get_scene_state":
        return {"success": True, "error": None, "data": _scene_state()}
    if op == "open_blend":
        path = str(params.get("path", "")).strip()
        if not path:
            return {"success": False, "error": "path is required", "error_type": "InvalidRequest"}
        bpy.ops.wm.open_mainfile(filepath=path)
        return {"success": True, "error": None, "data": _scene_state()}
    return {"success": False, "error": f"Unknown operation: {op}", "error_type": "UnknownOperation"}


def _drain_requests() -> float:
    while True:
        try:
            payload, event, result = REQUESTS.get_nowait()
        except queue.Empty:
            break
        try:
            result["value"] = _handle(payload)
        except Exception as exc:
            result["value"] = {"success": False, "error": str(exc), "error_type": type(exc).__name__}
        finally:
            event.set()
    _write_state()
    return 0.5


class _Handler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        raw = self.rfile.readline().decode("utf-8", errors="replace").strip()
        try:
            payload = json.loads(raw)
        except Exception as exc:
            self.wfile.write((json.dumps({"success": False, "error": str(exc), "error_type": "JsonError"}) + "\n").encode("utf-8"))
            return

        event = threading.Event()
        result: dict = {}
        REQUESTS.put((payload, event, result))
        if not event.wait(timeout=10):
            response = {"success": False, "error": "Timed out waiting for Blender main thread", "error_type": "TimeoutError"}
        else:
            response = result.get("value", {"success": False, "error": "No result", "error_type": "EmptyResult"})
        self.wfile.write((json.dumps(response, ensure_ascii=False) + "\n").encode("utf-8"))


def _write_state() -> None:
    if SERVER is None:
        return
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "host": HOST,
        "port": SERVER.server_address[1],
        "pid": os.getpid(),
        "blend_file": bpy.data.filepath or "",
        "timestamp": int(time.time()),
    }
    (STATE_DIR / f"live_{os.getpid()}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (STATE_DIR / "live_latest.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _start() -> None:
    global SERVER
    if SERVER is not None:
        return
    for port in PORT_RANGE:
        try:
            SERVER = socketserver.ThreadingTCPServer((HOST, port), _Handler)
            break
        except OSError:
            continue
    if SERVER is None:
        raise RuntimeError("Unable to bind Blender MCP live bridge")
    thread = threading.Thread(target=SERVER.serve_forever, name="blender-mcp-live", daemon=True)
    thread.start()
    _write_state()
    bpy.app.timers.register(_drain_requests, persistent=True)
    print(f"Blender MCP live bridge listening on {HOST}:{SERVER.server_address[1]}")


_start()
