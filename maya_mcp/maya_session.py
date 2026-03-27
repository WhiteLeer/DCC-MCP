"""Persistent Maya session backend for stateful operations."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict


class MayaSessionBackend:
    def __init__(self, maya_bin_path: str | None = None):
        self.maya_bin_path = maya_bin_path
        self._cmds = None
        self._initialize()

    def _initialize(self) -> None:
        if self.maya_bin_path and self.maya_bin_path not in os.environ.get("PATH", ""):
            os.environ["PATH"] = self.maya_bin_path + os.pathsep + os.environ.get("PATH", "")

        import maya.standalone
        maya.standalone.initialize(name="python")

        import maya.cmds as cmds
        self._cmds = cmds

    @property
    def cmds(self):
        return self._cmds

    async def execute(self, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if operation == "get_scene_state":
            return self.get_scene_state()
        if operation == "create_poly_cube":
            return self.create_poly_cube(params)
        if operation == "clean_mesh":
            return self.clean_mesh(params)
        if operation == "freeze_transform":
            return self.freeze_transform(params)
        if operation == "delete_history":
            return self.delete_history(params)
        if operation == "center_pivot":
            return self.center_pivot(params)
        if operation == "create_locator":
            return self.create_locator(params)
        if operation == "combine_meshes":
            return self.combine_meshes(params)
        if operation == "separate_mesh":
            return self.separate_mesh(params)
        if operation == "triangulate_mesh":
            return self.triangulate_mesh(params)
        if operation == "quad_mesh":
            return self.quad_mesh(params)
        if operation == "delete_unused_nodes":
            return self.delete_unused_nodes()
        if operation == "rename_node":
            return self.rename_node(params)
        if operation == "duplicate_node":
            return self.duplicate_node(params)
        if operation == "parent_node":
            return self.parent_node(params)
        if operation == "import_geometry":
            return self.import_geometry(params)
        if operation == "import_model":
            return self.import_model(params)

        return {"success": False, "error": f"Unknown operation: {operation}", "error_type": "UnknownOperation"}

    def get_scene_state(self) -> Dict[str, Any]:
        assemblies = self.cmds.ls(assemblies=True) or []
        selection = self.cmds.ls(selection=True) or []
        scene_path = self.cmds.file(query=True, sceneName=True) or "untitled"
        return {
            "success": True,
            "error": None,
            "data": {
                "scene_path": scene_path,
                "node_count": len(self.cmds.ls(long=True) or []),
                "assemblies": assemblies,
                "selection": selection,
                "running": True,
            },
        }

    def create_poly_cube(self, params: Dict[str, Any]) -> Dict[str, Any]:
        name = params.get("name", "polyCube1")
        width = float(params.get("width", 1.0))
        height = float(params.get("height", 1.0))
        depth = float(params.get("depth", 1.0))

        transform, shape = self.cmds.polyCube(w=width, h=height, d=depth, name=name)
        data = {
            "transform": transform,
            "shape": shape,
            "size": [width, height, depth],
            "message": f"Created polyCube {transform}",
        }
        return {
            "success": True,
            "message": data["message"],
            "prompt": f"Created polyCube {transform} with size {data['size']}",
            "error": None,
            "context": data,
        }

    def freeze_transform(self, params: Dict[str, Any]) -> Dict[str, Any]:
        node = self._resolve_transform(params.get("node", ""))
        self.cmds.makeIdentity(node, apply=True, translate=True, rotate=True, scale=True, normal=False)
        data = {"node": node, "message": f"Froze transforms on {node}"}
        return {
            "success": True,
            "message": data["message"],
            "prompt": data["message"],
            "error": None,
            "context": data,
        }

    def delete_history(self, params: Dict[str, Any]) -> Dict[str, Any]:
        node = self._resolve_transform(params.get("node", ""))
        self.cmds.delete(node, ch=True)
        data = {"node": node, "message": f"Deleted history on {node}"}
        return {
            "success": True,
            "message": data["message"],
            "prompt": data["message"],
            "error": None,
            "context": data,
        }

    def center_pivot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        node = self._resolve_transform(params.get("node", ""))
        self.cmds.xform(node, centerPivots=True)
        data = {"node": node, "message": f"Centered pivot on {node}"}
        return {
            "success": True,
            "message": data["message"],
            "prompt": data["message"],
            "error": None,
            "context": data,
        }

    def create_locator(self, params: Dict[str, Any]) -> Dict[str, Any]:
        name = params.get("name", "locator1")
        locator = self.cmds.spaceLocator(name=name)[0]
        data = {"node": locator, "message": f"Created locator {locator}"}
        return {
            "success": True,
            "message": data["message"],
            "prompt": data["message"],
            "error": None,
            "context": data,
        }

    def clean_mesh(self, params: Dict[str, Any]) -> Dict[str, Any]:
        node = self._resolve_transform(params.get("node", ""))
        self.cmds.delete(node, ch=True)
        self.cmds.makeIdentity(node, apply=True, translate=True, rotate=True, scale=True, normal=False)
        self.cmds.xform(node, centerPivots=True)
        data = {"node": node, "message": f"Cleaned mesh {node} (history+freeze+pivot)"}
        return {
            "success": True,
            "message": data["message"],
            "prompt": data["message"],
            "error": None,
            "context": data,
        }

    def combine_meshes(self, params: Dict[str, Any]) -> Dict[str, Any]:
        nodes = params.get("nodes") or []
        name = params.get("name", "combined_mesh")
        if not nodes:
            nodes = self.cmds.ls(selection=True) or []
        if len(nodes) < 2:
            raise RuntimeError("Need at least two meshes to combine")
        result = self.cmds.polyUnite(nodes, name=name, mergeUVSets=True, centerPivot=True)[0]
        data = {"node": result, "inputs": nodes, "message": f"Combined {len(nodes)} meshes into {result}"}
        return {
            "success": True,
            "message": data["message"],
            "prompt": data["message"],
            "error": None,
            "context": data,
        }

    def separate_mesh(self, params: Dict[str, Any]) -> Dict[str, Any]:
        node = self._resolve_transform(params.get("node", ""))
        parts = self.cmds.polySeparate(node) or []
        data = {"node": node, "parts": parts, "message": f"Separated mesh {node} into {len(parts)} parts"}
        return {
            "success": True,
            "message": data["message"],
            "prompt": data["message"],
            "error": None,
            "context": data,
        }

    def triangulate_mesh(self, params: Dict[str, Any]) -> Dict[str, Any]:
        node = self._resolve_transform(params.get("node", ""))
        self.cmds.polyTriangulate(node)
        data = {"node": node, "message": f"Triangulated {node}"}
        return {
            "success": True,
            "message": data["message"],
            "prompt": data["message"],
            "error": None,
            "context": data,
        }

    def quad_mesh(self, params: Dict[str, Any]) -> Dict[str, Any]:
        node = self._resolve_transform(params.get("node", ""))
        self.cmds.polyQuad(node)
        data = {"node": node, "message": f"Quadrangulated {node}"}
        return {
            "success": True,
            "message": data["message"],
            "prompt": data["message"],
            "error": None,
            "context": data,
        }

    def delete_unused_nodes(self) -> Dict[str, Any]:
        try:
            self.cmds.hyperShade(deleteUnusedNodes=True)
            message = "Deleted unused nodes via hyperShade"
        except Exception:
            message = "Failed to delete unused nodes"
        data = {"message": message}
        return {
            "success": True,
            "message": message,
            "prompt": message,
            "error": None,
            "context": data,
        }

    def rename_node(self, params: Dict[str, Any]) -> Dict[str, Any]:
        node = self._resolve_transform(params.get("node", ""))
        new_name = params.get("new_name", "")
        if not new_name:
            raise RuntimeError("new_name is required")
        renamed = self.cmds.rename(node, new_name)
        data = {"node": renamed, "message": f"Renamed {node} to {renamed}"}
        return {
            "success": True,
            "message": data["message"],
            "prompt": data["message"],
            "error": None,
            "context": data,
        }

    def duplicate_node(self, params: Dict[str, Any]) -> Dict[str, Any]:
        node = self._resolve_transform(params.get("node", ""))
        duplicates = self.cmds.duplicate(node, rr=True) or []
        result = duplicates[0] if duplicates else ""
        data = {"node": result, "message": f"Duplicated {node} -> {result}"}
        return {
            "success": True,
            "message": data["message"],
            "prompt": data["message"],
            "error": None,
            "context": data,
        }

    def parent_node(self, params: Dict[str, Any]) -> Dict[str, Any]:
        node = self._resolve_transform(params.get("node", ""))
        parent = params.get("parent", "")
        if not parent:
            raise RuntimeError("parent is required")
        result = self.cmds.parent(node, parent)[0]
        data = {"node": result, "parent": parent, "message": f"Parented {node} under {parent}"}
        return {
            "success": True,
            "message": data["message"],
            "prompt": data["message"],
            "error": None,
            "context": data,
        }

    def import_geometry(self, params: Dict[str, Any]) -> Dict[str, Any]:
        input_path = str(params.get("input_path", "")).strip()
        if not input_path:
            raise RuntimeError("input_path is required")
        if not Path(input_path).exists():
            raise RuntimeError(f"File not found: {input_path}")

        namespace = str(params.get("namespace", "mcp")).strip() or "mcp"
        clean_scene = bool(params.get("clean_scene", False))
        group_name = str(params.get("group_name", "")).strip()
        file_options = str(params.get("file_options", "")).strip() or "v=0;"
        merge_namespaces = bool(params.get("merge_namespaces_on_clash", True))

        if clean_scene:
            self.cmds.file(new=True, force=True)

        file_type = self._maya_import_type(input_path)
        self._ensure_import_plugin(file_type)

        before = set(self.cmds.ls(long=True) or [])
        try:
            new_nodes = self.cmds.file(
                input_path,
                i=True,
                type=file_type,
                ignoreVersion=True,
                ra=True,
                mergeNamespacesOnClash=merge_namespaces,
                namespace=namespace,
                options=file_options,
                pr=True,
                returnNewNodes=True,
            ) or []
        except Exception:
            # Fallback for files that do not accept explicit type/options.
            new_nodes = self.cmds.file(
                input_path,
                i=True,
                ignoreVersion=True,
                ra=True,
                mergeNamespacesOnClash=merge_namespaces,
                namespace=namespace,
                pr=True,
                returnNewNodes=True,
            ) or []

        if not new_nodes:
            after = set(self.cmds.ls(long=True) or [])
            new_nodes = sorted(list(after - before))

        transforms = [n for n in new_nodes if self.cmds.objExists(n) and self.cmds.nodeType(n) == "transform"]
        roots = [n for n in transforms if not self.cmds.listRelatives(n, parent=True)]
        group_node = ""
        if group_name and roots:
            group_node = self.cmds.group(roots, name=group_name)

        data = {
            "input_path": input_path,
            "file_type": file_type,
            "namespace": namespace,
            "new_node_count": len(new_nodes),
            "transform_count": len(transforms),
            "root_transforms": roots[:200],
            "group_node": group_node,
            "message": f"Imported {Path(input_path).name} ({len(transforms)} transforms)",
        }
        return {
            "success": True,
            "message": data["message"],
            "prompt": data["message"],
            "error": None,
            "context": data,
        }

    def import_model(self, params: Dict[str, Any]) -> Dict[str, Any]:
        result = self.import_geometry(params)
        if not result.get("success"):
            return result

        context = result.get("context", {})
        roots = list(context.get("root_transforms") or [])
        if context.get("group_node"):
            roots = [context["group_node"]]

        uniform_scale = float(params.get("uniform_scale", 1.0))
        freeze_after_import = bool(params.get("freeze_after_import", False))
        center_pivot_after_import = bool(params.get("center_pivot_after_import", False))
        delete_history_after_import = bool(params.get("delete_history_after_import", False))

        if abs(uniform_scale - 1.0) > 1e-6:
            for node in roots:
                if self.cmds.objExists(node):
                    self.cmds.setAttr(f"{node}.scaleX", uniform_scale)
                    self.cmds.setAttr(f"{node}.scaleY", uniform_scale)
                    self.cmds.setAttr(f"{node}.scaleZ", uniform_scale)

        for node in roots:
            if not self.cmds.objExists(node):
                continue
            if delete_history_after_import:
                self.cmds.delete(node, ch=True)
            if freeze_after_import:
                self.cmds.makeIdentity(node, apply=True, translate=True, rotate=True, scale=True, normal=False)
            if center_pivot_after_import:
                self.cmds.xform(node, centerPivots=True)

        context["uniform_scale"] = uniform_scale
        context["freeze_after_import"] = freeze_after_import
        context["center_pivot_after_import"] = center_pivot_after_import
        context["delete_history_after_import"] = delete_history_after_import
        context["message"] = f"Imported model with params: {Path(context['input_path']).name}"
        result["message"] = context["message"]
        result["prompt"] = context["message"]
        return result

    def _maya_import_type(self, path_value: str) -> str:
        ext = Path(path_value).suffix.lower()
        if ext == ".fbx":
            return "FBX"
        if ext == ".obj":
            return "OBJ"
        if ext == ".abc":
            return "Alembic"
        if ext == ".ma":
            return "mayaAscii"
        if ext == ".mb":
            return "mayaBinary"
        raise RuntimeError(f"Unsupported import format: {ext}")

    def _ensure_import_plugin(self, import_type: str) -> None:
        plugin_map = {
            "FBX": "fbxmaya",
            "OBJ": "objExport",
            "Alembic": "AbcImport",
        }
        plugin = plugin_map.get(import_type)
        if not plugin:
            return
        try:
            if not self.cmds.pluginInfo(plugin, query=True, loaded=True):
                self.cmds.loadPlugin(plugin)
        except Exception:
            # Keep import attempt behavior unchanged when plugin probing is unsupported.
            pass

    def _resolve_transform(self, node: str) -> str:
        if not node:
            selection = self.cmds.ls(selection=True) or []
            if not selection:
                raise RuntimeError("No node provided and nothing selected")
            node = selection[0]

        if self.cmds.nodeType(node) == "transform":
            return node

        parents = self.cmds.listRelatives(node, parent=True) or []
        if not parents:
            raise RuntimeError(f"Node '{node}' has no transform parent")
        return parents[0]
