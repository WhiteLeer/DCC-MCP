"""Blender session backend (daemon-side)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import textwrap
from pathlib import Path
from typing import Any, Dict


class BlenderSessionBackend:
    def __init__(self, blender_exe: str | None = None):
        self.blender_exe = (blender_exe or os.environ.get("BLENDER_EXE") or "").strip()
        self.default_blender_exe = "D:/常用软件/Blender 4.2/blender.exe"

    async def execute(self, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if operation == "get_scene_state":
            return self.get_scene_state()
        if operation == "create_cube":
            return self.create_cube(params)
        if operation == "clean_scene":
            return self.clean_scene(params)
        if operation == "import_geometry":
            return self.import_geometry(params)
        if operation == "export_fbx":
            return self.export_fbx(params)
        if operation == "decimate_mesh":
            return self.decimate_mesh(params)
        if operation == "triangulate_mesh":
            return self.triangulate_mesh(params)
        if operation == "recalculate_normals":
            return self.recalculate_normals(params)
        if operation == "shade_smooth":
            return self.shade_smooth(params)
        if operation == "merge_by_distance":
            return self.merge_by_distance(params)

        return {"success": False, "error": f"Unknown operation: {operation}", "error_type": "UnknownOperation"}

    def _check_blender_exe(self) -> None:
        if self.blender_exe:
            if Path(self.blender_exe).exists():
                return
            raise RuntimeError(f"Blender executable not found: {self.blender_exe}")

        blender_on_path = shutil.which("blender")
        if blender_on_path:
            self.blender_exe = blender_on_path
            return

        if Path(self.default_blender_exe).exists():
            self.blender_exe = self.default_blender_exe
            return

        raise RuntimeError("Blender executable not configured. Set BLENDER_EXE first.")

    def _run_blender_script(self, script_body: str, timeout_seconds: int = 120) -> Dict[str, Any]:
        self._check_blender_exe()

        with tempfile.TemporaryDirectory(prefix="blender_mcp_") as tmpdir:
            tmp_path = Path(tmpdir)
            result_file = tmp_path / "result.json"
            script_file = tmp_path / "run.py"

            indented_body = textwrap.indent(script_body.strip("\n"), "    ")
            full_script = (
                "import json\n"
                "import traceback\n"
                "from pathlib import Path\n\n"
                f"RESULT_PATH = Path(r\"{str(result_file)}\")\n\n"
                "def _ok(data):\n"
                "    RESULT_PATH.write_text(json.dumps({\"success\": True, \"data\": data}, ensure_ascii=False), encoding=\"utf-8\")\n\n"
                "def _err(msg):\n"
                "    RESULT_PATH.write_text(json.dumps({\"success\": False, \"error\": msg}, ensure_ascii=False), encoding=\"utf-8\")\n\n"
                "try:\n"
                f"{indented_body}\n"
                "except Exception:\n"
                "    _err(traceback.format_exc())\n"
            )
            script_file.write_text(full_script, encoding="utf-8")

            proc = subprocess.run(
                [self.blender_exe, "--background", "--factory-startup", "--python", str(script_file)],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout_seconds,
            )

            if not result_file.exists():
                std_msg = (proc.stderr or proc.stdout or "").strip()
                if len(std_msg) > 1200:
                    std_msg = std_msg[-1200:]
                if not std_msg:
                    std_msg = "no stdout/stderr"
                return {
                    "success": False,
                    "error": f"Blender script did not produce result. rc={proc.returncode}, detail={std_msg}",
                    "error_type": "BlenderRuntimeError",
                }

            payload = json.loads(result_file.read_text(encoding="utf-8"))
            if not payload.get("success"):
                return {"success": False, "error": payload.get("error", "Unknown Blender error"), "error_type": "BlenderOperationError"}
            return {"success": True, "data": payload.get("data", {})}

    def get_scene_state(self) -> Dict[str, Any]:
        result = self._run_blender_script(
            """
import bpy
_ok({
    "blender_exe": bpy.app.binary_path,
    "blender_version": list(bpy.app.version),
    "object_count": len(bpy.data.objects),
    "scene_name": bpy.context.scene.name,
})
"""
        )
        if not result.get("success"):
            return result
        data = result["data"]
        return {
            "success": True,
            "error": None,
            "data": {
                "scene_path": "factory-startup",
                "node_count": int(data.get("object_count", 0)),
                "assemblies": [],
                "selection": [],
                "running": True,
                **data,
            },
        }

    def create_cube(self, params: Dict[str, Any]) -> Dict[str, Any]:
        output_blend = params.get("output_blend", "")
        size = float(params.get("size", 2.0))
        loc = params.get("location") or [0.0, 0.0, 0.0]

        script = f"""
import bpy
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.mesh.primitive_cube_add(size={size}, location=({float(loc[0])}, {float(loc[1])}, {float(loc[2])}))
obj = bpy.context.active_object
out_path = r\"{output_blend}\".strip()
if out_path:
    bpy.ops.wm.save_as_mainfile(filepath=out_path)
_ok({{"object_name": obj.name, "output_blend": out_path}})
"""
        result = self._run_blender_script(script)
        if not result.get("success"):
            return result
        data = result["data"]
        message = f"Created cube {data.get('object_name', 'Cube')}"
        return {"success": True, "message": message, "prompt": message, "error": None, "context": data}

    def clean_scene(self, params: Dict[str, Any]) -> Dict[str, Any]:
        output_blend = params.get("output_blend", "")
        script = f"""
import bpy
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
out_path = r\"{output_blend}\".strip()
if out_path:
    bpy.ops.wm.save_as_mainfile(filepath=out_path)
_ok({{"output_blend": out_path}})
"""
        result = self._run_blender_script(script)
        if not result.get("success"):
            return result
        data = result["data"]
        message = "Cleaned scene"
        return {"success": True, "message": message, "prompt": message, "error": None, "context": data}

    def import_geometry(self, params: Dict[str, Any]) -> Dict[str, Any]:
        input_path = params.get("input_path", "")
        output_blend = params.get("output_blend", "")
        if not input_path:
            raise RuntimeError("input_path is required")

        suffix = Path(input_path).suffix.lower()
        if suffix == ".fbx":
            import_stmt = f"bpy.ops.import_scene.fbx(filepath=r\"{input_path}\")"
        elif suffix == ".obj":
            import_stmt = f"bpy.ops.wm.obj_import(filepath=r\"{input_path}\")"
        elif suffix in {".glb", ".gltf"}:
            import_stmt = f"bpy.ops.import_scene.gltf(filepath=r\"{input_path}\")"
        else:
            raise RuntimeError(f"Unsupported import format: {suffix}")

        script = f"""
import bpy
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
{import_stmt}
out_path = r\"{output_blend}\".strip()
if out_path:
    bpy.ops.wm.save_as_mainfile(filepath=out_path)
_ok({{"input_path": r\"{input_path}\", "output_blend": out_path, "object_count": len(bpy.data.objects)}})
"""
        result = self._run_blender_script(script)
        if not result.get("success"):
            return result
        data = result["data"]
        message = f"Imported geometry: {Path(input_path).name}"
        return {"success": True, "message": message, "prompt": message, "error": None, "context": data}

    def export_fbx(self, params: Dict[str, Any]) -> Dict[str, Any]:
        output_path = params.get("output_path", "")
        input_blend = params.get("input_blend", "")
        if not output_path:
            raise RuntimeError("output_path is required")

        open_blend_stmt = ""
        if input_blend:
            open_blend_stmt = f"bpy.ops.wm.open_mainfile(filepath=r\"{input_blend}\")"

        script = f"""
import bpy
{open_blend_stmt}
bpy.ops.export_scene.fbx(filepath=r\"{output_path}\", use_selection=False, add_leaf_bones=False)
_ok({{"input_blend": r\"{input_blend}\", "output_path": r\"{output_path}\"}})
"""
        result = self._run_blender_script(script)
        if not result.get("success"):
            return result
        data = result["data"]
        message = f"Exported FBX: {Path(output_path).name}"
        return {"success": True, "message": message, "prompt": message, "error": None, "context": data}

    def decimate_mesh(self, params: Dict[str, Any]) -> Dict[str, Any]:
        input_blend = params.get("input_blend", "")
        output_blend = params.get("output_blend", "")
        ratio = max(0.01, min(1.0, float(params.get("ratio", 0.5))))

        open_stmt = f'bpy.ops.wm.open_mainfile(filepath=r"{input_blend}")' if input_blend else ""
        script = f"""
import bpy
{open_stmt}
mesh_count = 0
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        mesh_count += 1
        mod = obj.modifiers.new(name='DecimateMCP', type='DECIMATE')
        mod.ratio = {ratio}
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
out_path = r\"{output_blend}\".strip()
if out_path:
    bpy.ops.wm.save_as_mainfile(filepath=out_path)
_ok({{"input_blend": r\"{input_blend}\", "output_blend": out_path, "ratio": {ratio}, "mesh_count": mesh_count}})
"""
        result = self._run_blender_script(script)
        if not result.get("success"):
            return result
        data = result["data"]
        message = f"Decimated {data.get('mesh_count', 0)} mesh(es), ratio={ratio:.2f}"
        return {"success": True, "message": message, "prompt": message, "error": None, "context": data}

    def triangulate_mesh(self, params: Dict[str, Any]) -> Dict[str, Any]:
        input_blend = params.get("input_blend", "")
        output_blend = params.get("output_blend", "")

        open_stmt = f'bpy.ops.wm.open_mainfile(filepath=r"{input_blend}")' if input_blend else ""
        script = f"""
import bpy
{open_stmt}
mesh_count = 0
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        mesh_count += 1
        mod = obj.modifiers.new(name='TriangulateMCP', type='TRIANGULATE')
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
out_path = r\"{output_blend}\".strip()
if out_path:
    bpy.ops.wm.save_as_mainfile(filepath=out_path)
_ok({{"input_blend": r\"{input_blend}\", "output_blend": out_path, "mesh_count": mesh_count}})
"""
        result = self._run_blender_script(script)
        if not result.get("success"):
            return result
        data = result["data"]
        message = f"Triangulated {data.get('mesh_count', 0)} mesh(es)"
        return {"success": True, "message": message, "prompt": message, "error": None, "context": data}

    def recalculate_normals(self, params: Dict[str, Any]) -> Dict[str, Any]:
        input_blend = params.get("input_blend", "")
        output_blend = params.get("output_blend", "")

        open_stmt = f'bpy.ops.wm.open_mainfile(filepath=r"{input_blend}")' if input_blend else ""
        script = f"""
import bpy
mesh_count = 0
{open_stmt}
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        mesh_count += 1
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.object.mode_set(mode='OBJECT')
out_path = r\"{output_blend}\".strip()
if out_path:
    bpy.ops.wm.save_as_mainfile(filepath=out_path)
_ok({{"input_blend": r\"{input_blend}\", "output_blend": out_path, "mesh_count": mesh_count}})
"""
        result = self._run_blender_script(script)
        if not result.get("success"):
            return result
        data = result["data"]
        message = f"Recalculated normals on {data.get('mesh_count', 0)} mesh(es)"
        return {"success": True, "message": message, "prompt": message, "error": None, "context": data}

    def shade_smooth(self, params: Dict[str, Any]) -> Dict[str, Any]:
        input_blend = params.get("input_blend", "")
        output_blend = params.get("output_blend", "")
        auto_smooth_angle = float(params.get("auto_smooth_angle", 30.0))

        open_stmt = f'bpy.ops.wm.open_mainfile(filepath=r"{input_blend}")' if input_blend else ""
        script = f"""
import bpy, math
{open_stmt}
mesh_count = 0
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        mesh_count += 1
        obj.data.use_auto_smooth = True
        obj.data.auto_smooth_angle = math.radians({auto_smooth_angle})
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.shade_smooth()
out_path = r\"{output_blend}\".strip()
if out_path:
    bpy.ops.wm.save_as_mainfile(filepath=out_path)
_ok({{"input_blend": r\"{input_blend}\", "output_blend": out_path, "mesh_count": mesh_count, "auto_smooth_angle": {auto_smooth_angle}}})
"""
        result = self._run_blender_script(script)
        if not result.get("success"):
            return result
        data = result["data"]
        message = f"Shaded smooth on {data.get('mesh_count', 0)} mesh(es)"
        return {"success": True, "message": message, "prompt": message, "error": None, "context": data}

    def merge_by_distance(self, params: Dict[str, Any]) -> Dict[str, Any]:
        input_blend = params.get("input_blend", "")
        output_blend = params.get("output_blend", "")
        distance = max(0.0, float(params.get("distance", 0.0001)))

        open_stmt = f'bpy.ops.wm.open_mainfile(filepath=r"{input_blend}")' if input_blend else ""
        script = f"""
import bpy
{open_stmt}
mesh_count = 0
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        mesh_count += 1
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold={distance})
        bpy.ops.object.mode_set(mode='OBJECT')
out_path = r\"{output_blend}\".strip()
if out_path:
    bpy.ops.wm.save_as_mainfile(filepath=out_path)
_ok({{"input_blend": r\"{input_blend}\", "output_blend": out_path, "mesh_count": mesh_count, "distance": {distance}}})
"""
        result = self._run_blender_script(script)
        if not result.get("success"):
            return result
        data = result["data"]
        message = f"Merged vertices by distance on {data.get('mesh_count', 0)} mesh(es)"
        return {"success": True, "message": message, "prompt": message, "error": None, "context": data}
