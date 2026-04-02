"""Persistent Houdini session backend for stateful SOP operations."""

from __future__ import annotations

import os
import re
import math
from pathlib import Path
from typing import Any, Dict

from houdini_mcp.utils.houdini_paths import resolve_houdini_bin_path


class HoudiniSessionBackend:
    def __init__(self, houdini_bin_path: str | None = None):
        self.houdini_bin_path = str(resolve_houdini_bin_path(houdini_bin_path))
        self._hou = None
        self._initialize()

    def _initialize(self) -> None:
        houdini_root = os.path.dirname(self.houdini_bin_path)
        os.environ.setdefault("HFS", houdini_root)
        os.environ.setdefault("H", houdini_root)
        os.environ.setdefault("HB", self.houdini_bin_path)
        os.environ.setdefault("HDSO", os.path.join(houdini_root, "dsolib"))
        if self.houdini_bin_path not in os.environ.get("PATH", ""):
            os.environ["PATH"] = self.houdini_bin_path + os.pathsep + os.environ.get("PATH", "")

        import hou

        self._hou = hou

    @property
    def hou(self):
        return self._hou

    async def execute(self, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if operation == "get_scene_state":
            return self.get_scene_state()
        if operation == "get_template_catalog":
            return self.get_template_catalog(params)
        if operation == "plan_hda_from_prompt":
            return self.plan_hda_from_prompt(params)
        if operation == "build_hda_from_prompt":
            return self.build_hda_from_prompt(params)
        if operation == "build_hda_from_template":
            return self.build_hda_from_template(params)
        if operation == "repair_graph":
            return self.repair_graph(params)
        if operation == "generate_hda_ui":
            return self.generate_hda_ui(params)
        if operation == "get_node_graph_summary":
            return self.get_node_graph_summary(params)
        if operation == "create_box":
            return self.create_box(params)
        if operation == "instantiate_template":
            return self.instantiate_template(params)
        if operation == "validate_graph":
            return self.validate_graph(params)
        if operation == "validate_params":
            return self.validate_params(params)
        if operation == "dry_run_cook":
            return self.dry_run_cook(params)
        if operation == "inspect_geometry":
            return self.inspect_geometry(params)
        if operation == "clean_mesh":
            return self.clean_mesh(params)
        if operation == "cleanup_attributes":
            return self.cleanup_attributes(params)
        if operation == "fuse_points":
            return self.fuse_points(params)
        if operation == "normalize_normals":
            return self.normalize_normals(params)
        if operation == "add_output_null":
            return self.add_output_null(params)
        if operation == "freeze_transform":
            return self.freeze_transform(params)
        if operation == "create_subnet_from_nodes":
            return self.create_subnet_from_nodes(params)
        if operation == "create_hda_from_selection":
            return self.create_hda_from_selection(params)
        if operation == "mirror":
            return self.mirror(params)
        if operation == "delete_half":
            return self.delete_half(params)
        if operation == "polyreduce":
            return self.polyreduce(params)
        if operation == "smooth":
            return self.smooth(params)
        if operation == "boolean":
            return self.boolean(params)
        if operation == "import_geometry":
            return self.import_geometry(params)
        if operation == "import_model":
            return self.import_model(params)
        if operation == "capture_screenshot":
            return self.capture_screenshot(params)
        if operation == "frame_camera_on_geo":
            return self.frame_camera_on_geo(params)
        if operation == "export_geometry":
            return self.export_geometry(params)
        if operation == "export_unity_fbx":
            return self.export_unity_fbx(params)

        return {"success": False, "error": f"Unknown operation: {operation}", "error_type": "UnknownOperation"}

    def get_scene_state(self) -> Dict[str, Any]:
        obj = self.hou.node("/obj")
        nodes = []
        for node in obj.children():
            nodes.append(
                {
                    "path": node.path(),
                    "type": node.type().name(),
                    "name": node.name(),
                }
            )
        return {
            "success": True,
            "error": None,
            "data": {
                "hip_file": self.hou.hipFile.path(),
                "frame": self.hou.frame(),
                "nodes": nodes,
                "node_count": len(nodes),
                "running": True,
            },
        }

    def get_template_catalog(self, params: Dict[str, Any]) -> Dict[str, Any]:
        include_schema = bool(params.get("include_schema", True))
        templates = {
            "single_building_v1": {
                "description": "Single procedural building with roof peak.",
                "category": "building",
                "defaults": {"width": 8.0, "height": 12.0, "depth": 8.0, "roof_scale": 1.15, "roof_height": 3.0},
                "schema": {
                    "width": {"type": "float", "min": 1.0, "max": 50.0},
                    "height": {"type": "float", "min": 1.0, "max": 80.0},
                    "depth": {"type": "float", "min": 1.0, "max": 50.0},
                    "roof_scale": {"type": "float", "min": 0.5, "max": 3.0},
                    "roof_height": {"type": "float", "min": 0.2, "max": 20.0},
                },
            },
            "road_segment_v1": {
                "description": "Road segment with configurable subdivision and subtle crown.",
                "category": "road",
                "defaults": {"length": 30.0, "width": 6.0, "rows": 8, "cols": 16, "curb_height": 0.15},
                "schema": {
                    "length": {"type": "float", "min": 2.0, "max": 2000.0},
                    "width": {"type": "float", "min": 0.5, "max": 100.0},
                    "rows": {"type": "int", "min": 2, "max": 256},
                    "cols": {"type": "int", "min": 2, "max": 2048},
                    "curb_height": {"type": "float", "min": -1.0, "max": 2.0},
                },
            },
            "town_block_v1": {
                "description": "Procedural town block with roads and scattered buildings.",
                "category": "town",
                "defaults": {
                    "block_size": 120.0,
                    "road_width": 10.0,
                    "road_mode": 1,
                    "road_curve_path": "",
                    "building_density": 0.35,
                    "min_height": 6.0,
                    "max_height": 24.0,
                    "min_footprint": 2.0,
                    "max_footprint": 6.0,
                    "seed": 0,
                },
                "schema": {
                    "block_size": {"type": "float", "min": 20.0, "max": 2000.0},
                    "road_width": {"type": "float", "min": 1.0, "max": 200.0},
                    "road_mode": {"type": "int", "min": 0, "max": 2},
                    "road_curve_path": {"type": "string"},
                    "building_density": {"type": "float", "min": 0.01, "max": 1.0},
                    "min_height": {"type": "float", "min": 1.0, "max": 200.0},
                    "max_height": {"type": "float", "min": 1.0, "max": 400.0},
                    "min_footprint": {"type": "float", "min": 0.5, "max": 30.0},
                    "max_footprint": {"type": "float", "min": 0.5, "max": 60.0},
                    "seed": {"type": "int", "min": 0, "max": 100000},
                },
            },
            "crystal_courtyard_v1": {
                "description": "Procedural crystal courtyard over water with arch, pillars, and stepping stones.",
                "category": "environment",
                "defaults": {
                    "water_size": 420.0,
                    "arch_count": 16,
                    "ring_pillar_count": 18,
                    "step_count": 14,
                    "crystal_scale": 1.0,
                    "seed": 0,
                },
                "schema": {
                    "water_size": {"type": "float", "min": 40.0, "max": 4000.0},
                    "arch_count": {"type": "int", "min": 4, "max": 128},
                    "ring_pillar_count": {"type": "int", "min": 4, "max": 256},
                    "step_count": {"type": "int", "min": 4, "max": 128},
                    "crystal_scale": {"type": "float", "min": 0.2, "max": 8.0},
                    "seed": {"type": "int", "min": 0, "max": 100000},
                },
            },
            "crystal_courtyard_v2": {
                "description": "Crystal gate scene with twin leaning arches, center shard burst, and stepping path.",
                "category": "environment",
                "defaults": {
                    "water_size": 420.0,
                    "arch_count": 18,
                    "ring_pillar_count": 14,
                    "step_count": 14,
                    "crystal_scale": 1.0,
                    "seed": 0,
                },
                "schema": {
                    "water_size": {"type": "float", "min": 40.0, "max": 4000.0},
                    "arch_count": {"type": "int", "min": 4, "max": 128},
                    "ring_pillar_count": {"type": "int", "min": 4, "max": 256},
                    "step_count": {"type": "int", "min": 4, "max": 128},
                    "crystal_scale": {"type": "float", "min": 0.2, "max": 8.0},
                    "seed": {"type": "int", "min": 0, "max": 100000},
                },
            },
        }
        if not include_schema:
            for item in templates.values():
                item.pop("schema", None)
        return {
            "success": True,
            "message": "Template catalog fetched",
            "error": None,
            "context": {"templates": templates},
        }

    def plan_hda_from_prompt(self, params: Dict[str, Any]) -> Dict[str, Any]:
        prompt = str(params.get("prompt", "")).strip()
        if not prompt:
            raise RuntimeError("prompt is required")

        text = prompt.lower()
        template_id = "single_building_v1"
        overrides: Dict[str, Any] = {}
        suggested_name = "generated_building"

        if any(token in text for token in ("town", "city", "block", "district", "城镇", "城市", "街区", "小镇")):
            template_id = "town_block_v1"
            suggested_name = "generated_town"
        elif any(token in text for token in ("crystal", "ice", "water", "arch", "镜面", "冰", "水面", "晶体", "拱")):
            template_id = "crystal_courtyard_v2"
            suggested_name = "generated_crystal_scene"
        elif any(token in text for token in ("road", "street", "path", "lane", "道路", "马路", "街道", "路段")):
            template_id = "road_segment_v1"
            suggested_name = "generated_road"
        elif any(token in text for token in ("building", "house", "tower", "architecture", "建筑", "房子", "楼", "塔")):
            template_id = "single_building_v1"
            suggested_name = "generated_building"

        numbers = re.findall(r"\d+(?:\.\d+)?", text)
        if template_id == "single_building_v1":
            if len(numbers) >= 1:
                overrides["width"] = float(numbers[0])
            if len(numbers) >= 2:
                overrides["height"] = float(numbers[1])
            if len(numbers) >= 3:
                overrides["depth"] = float(numbers[2])
        elif template_id == "road_segment_v1":
            if len(numbers) >= 1:
                overrides["length"] = float(numbers[0])
            if len(numbers) >= 2:
                overrides["width"] = float(numbers[1])
        elif template_id in {"crystal_courtyard_v1", "crystal_courtyard_v2"}:
            if len(numbers) >= 1:
                overrides["water_size"] = float(numbers[0])
            if len(numbers) >= 2:
                overrides["arch_count"] = int(float(numbers[1]))
            if len(numbers) >= 3:
                overrides["ring_pillar_count"] = int(float(numbers[2]))
        else:
            if len(numbers) >= 1:
                overrides["block_size"] = float(numbers[0])
            if len(numbers) >= 2:
                overrides["road_width"] = float(numbers[1])
            if any(token in text for token in ("curve", "spline", "bezier", "曲线", "弯路")):
                overrides["road_mode"] = 1
            if any(token in text for token in ("cross", "grid", "十字", "网格")):
                overrides["road_mode"] = 0

        data = {
            "prompt": prompt,
            "template_id": template_id,
            "node_name": suggested_name,
            "overrides": overrides,
            "notes": ["heuristic_parser_v1"],
        }
        return {"success": True, "message": "Plan created from prompt", "error": None, "context": data}

    def build_hda_from_prompt(self, params: Dict[str, Any]) -> Dict[str, Any]:
        plan_result = self.plan_hda_from_prompt(params)
        plan = plan_result["context"]
        build_params = {
            "template_id": plan["template_id"],
            "parent_path": str(params.get("parent_path", "/obj")).strip() or "/obj",
            "node_name": str(params.get("node_name", "")).strip() or plan["node_name"],
            "overrides": plan["overrides"],
            "asset_name": str(params.get("asset_name", "")).strip(),
            "asset_label": str(params.get("asset_label", "")).strip(),
            "hda_file_path": str(params.get("hda_file_path", "")).strip(),
            "version": str(params.get("version", "")).strip(),
            "save_as_embedded": bool(params.get("save_as_embedded", False)),
            "ignore_validation_errors": bool(params.get("ignore_validation_errors", False)),
        }
        result = self.build_hda_from_template(build_params)
        result_context = result.get("context", {})
        result_context["plan"] = plan
        result["context"] = result_context
        return result

    def build_hda_from_template(self, params: Dict[str, Any]) -> Dict[str, Any]:
        template_id = str(params.get("template_id", "")).strip().lower()
        parent_path = str(params.get("parent_path", "/obj")).strip() or "/obj"
        node_name = str(params.get("node_name", "")).strip()
        overrides = params.get("overrides") or {}
        ignore_validation_errors = bool(params.get("ignore_validation_errors", False))

        inst = self.instantiate_template(
            {
                "template_id": template_id,
                "parent_path": parent_path,
                "node_name": node_name,
                "overrides": overrides,
            }
        )
        root_path = inst.get("context", {}).get("root_node_path", "")
        if not root_path:
            raise RuntimeError("Template instantiation did not return root_node_path")

        v_params = self.validate_params({"root_path": root_path, "schema_id": template_id})
        v_graph = self.validate_graph({"root_path": root_path})
        dry = self.dry_run_cook({"root_path": root_path})

        repair_result = None
        if not bool(v_graph.get("success")):
            repair_result = self.repair_graph({"root_path": root_path})
            v_graph = self.validate_graph({"root_path": root_path})
            if bool(v_graph.get("success")) and not bool(dry.get("success")):
                dry = self.dry_run_cook({"root_path": root_path})

        validation_ok = bool(v_params.get("success")) and bool(v_graph.get("success")) and bool(dry.get("success"))
        if not validation_ok and not ignore_validation_errors:
            return {
                "success": False,
                "message": "Build aborted due to validation failure",
                "error": "validation_failed",
                "context": {
                    "root_node_path": root_path,
                    "validate_params": v_params,
                    "validate_graph": v_graph,
                    "dry_run_cook": dry,
                    "repair_graph": repair_result,
                },
            }

        default_asset_name = f"mcp_{self._sanitize_node_name(node_name or template_id)}"
        create_hda = self.create_hda_from_selection(
            {
                "asset_name": params.get("asset_name") or default_asset_name,
                "asset_label": params.get("asset_label") or default_asset_name.replace("_", " ").title(),
                "node_paths": [root_path],
                "hda_file_path": params.get("hda_file_path", ""),
                "version": params.get("version", ""),
                "save_as_embedded": bool(params.get("save_as_embedded", False)),
            }
        )
        if not create_hda.get("success"):
            return create_hda

        data = {
            "template_id": template_id,
            "root_node_path": root_path,
            "instantiate": inst,
            "validate_params": v_params,
            "validate_graph": v_graph,
            "dry_run_cook": dry,
            "repair_graph": repair_result,
            "hda": create_hda.get("context", {}),
        }
        return {"success": True, "message": "HDA built from template", "error": None, "context": data}

    def repair_graph(self, params: Dict[str, Any]) -> Dict[str, Any]:
        root_path = str(params.get("root_path", "")).strip()
        if not root_path:
            raise RuntimeError("root_path is required")
        root = self.hou.node(root_path)
        if root is None:
            raise RuntimeError(f"Root node not found: {root_path}")

        actions: list[str] = []
        warnings: list[str] = []

        if root.type().category().name() == "Object":
            display = root.displayNode()
            out = root.node("OUT")
            if out is None and display is not None:
                out = root.createNode("null", "OUT")
                out.setInput(0, display)
                actions.append("created_OUT_node")

            if out is not None:
                if not out.isDisplayFlagSet():
                    out.setDisplayFlag(True)
                    actions.append("set_OUT_display_flag")
                if hasattr(out, "setRenderFlag") and not out.isRenderFlagSet():
                    out.setRenderFlag(True)
                    actions.append("set_OUT_render_flag")
            else:
                warnings.append("no_display_node_to_attach_OUT")

            root.layoutChildren()
        else:
            if hasattr(root, "setDisplayFlag") and not root.isDisplayFlagSet():
                root.setDisplayFlag(True)
                actions.append("set_display_flag")
            if hasattr(root, "setRenderFlag") and not root.isRenderFlagSet():
                root.setRenderFlag(True)
                actions.append("set_render_flag")

        return {
            "success": True,
            "message": "Graph repair completed",
            "error": None,
            "context": {"root_path": root_path, "actions": actions, "warnings": warnings},
        }

    def generate_hda_ui(self, params: Dict[str, Any]) -> Dict[str, Any]:
        root_path = str(params.get("root_path", "")).strip()
        if not root_path:
            raise RuntimeError("root_path is required")
        root = self.hou.node(root_path)
        if root is None:
            raise RuntimeError(f"Root node not found: {root_path}")

        schema_id = str(params.get("schema_id", "")).strip().lower()
        if not schema_id:
            schema_id = str(root.userData("mcp_template_id") or "").lower()

        if schema_id == "single_building_v1":
            self._setup_building_controls(root)
            exposed = ["width", "height", "depth", "roof_scale", "roof_height", "seed"]
        elif schema_id == "road_segment_v1":
            self._setup_road_controls(root)
            exposed = ["length", "width", "rows", "cols", "curb_height", "seed"]
        elif schema_id == "town_block_v1":
            self._setup_town_controls(root)
            exposed = [
                "block_size",
                "road_width",
                "road_mode",
                "road_curve_path",
                "building_density",
                "min_height",
                "max_height",
                "min_footprint",
                "max_footprint",
                "seed",
            ]
        elif schema_id in {"crystal_courtyard_v1", "crystal_courtyard_v2"}:
            self._setup_crystal_controls(root)
            exposed = [
                "water_size",
                "arch_count",
                "ring_pillar_count",
                "step_count",
                "crystal_scale",
                "seed",
            ]
        else:
            return {
                "success": False,
                "message": "Unsupported schema for UI generation",
                "error": f"unsupported_schema:{schema_id}",
                "context": {"root_path": root_path, "schema_id": schema_id},
            }

        return {
            "success": True,
            "message": "Generated HDA UI controls",
            "error": None,
            "context": {"root_path": root_path, "schema_id": schema_id, "exposed_params": exposed},
        }

    def get_node_graph_summary(self, params: Dict[str, Any]) -> Dict[str, Any]:
        root_path = str(params.get("root_path", "/obj")).strip() or "/obj"
        max_depth = max(1, int(params.get("max_depth", 2)))
        max_children = max(1, int(params.get("max_children", 50)))

        root = self.hou.node(root_path)
        if root is None:
            raise RuntimeError(f"Root node not found: {root_path}")

        def _walk(node, depth: int):
            item = {
                "path": node.path(),
                "name": node.name(),
                "type": node.type().name(),
                "is_bypassed": bool(node.isBypassed()) if hasattr(node, "isBypassed") else False,
                "has_error": bool(node.errors()) if hasattr(node, "errors") else False,
                "has_warning": bool(node.warnings()) if hasattr(node, "warnings") else False,
                "children": [],
            }
            if depth >= max_depth:
                return item
            children = node.children()[:max_children]
            item["children"] = [_walk(child, depth + 1) for child in children]
            return item

        graph = _walk(root, 0)
        data = {
            "root_path": root.path(),
            "max_depth": max_depth,
            "max_children": max_children,
            "graph": graph,
        }
        return {"success": True, "message": f"Collected graph summary for {root.path()}", "error": None, "context": data}

    def instantiate_template(self, params: Dict[str, Any]) -> Dict[str, Any]:
        template_id = str(params.get("template_id", "")).strip().lower()
        if not template_id:
            raise RuntimeError("template_id is required")
        parent_path = str(params.get("parent_path", "/obj")).strip() or "/obj"
        node_name = str(params.get("node_name", "")).strip()
        overrides = params.get("overrides") or {}
        if not isinstance(overrides, dict):
            raise RuntimeError("overrides must be a dict")

        parent = self.hou.node(parent_path)
        if parent is None:
            raise RuntimeError(f"Parent node not found: {parent_path}")

        if template_id == "single_building_v1":
            result = self._build_template_single_building_v1(parent, node_name, overrides)
        elif template_id == "road_segment_v1":
            result = self._build_template_road_segment_v1(parent, node_name, overrides)
        elif template_id == "town_block_v1":
            result = self._build_template_town_block_v1(parent, node_name, overrides)
        elif template_id == "crystal_courtyard_v1":
            result = self._build_template_crystal_courtyard_v1(parent, node_name, overrides)
        elif template_id == "crystal_courtyard_v2":
            result = self._build_template_crystal_courtyard_v2(parent, node_name, overrides)
        else:
            raise RuntimeError(f"Unsupported template_id: {template_id}")

        return {
            "success": True,
            "message": f"Instantiated template {template_id}",
            "error": None,
            "context": result,
        }

    def validate_graph(self, params: Dict[str, Any]) -> Dict[str, Any]:
        root_path = str(params.get("root_path", "")).strip()
        if not root_path:
            raise RuntimeError("root_path is required")
        root = self.hou.node(root_path)
        if root is None:
            raise RuntimeError(f"Root node not found: {root_path}")

        errors: list[str] = []
        warnings: list[str] = []
        checks: dict[str, Any] = {
            "root_exists": True,
            "root_type": root.type().name(),
            "has_out_node": False,
            "has_display_node": False,
            "cook_ok": False,
        }

        display_node = None
        if root.type().category().name() == "Object":
            display_node = root.displayNode()
            checks["has_display_node"] = display_node is not None
            out_node = root.node("OUT")
            checks["has_out_node"] = out_node is not None
            if out_node is None:
                warnings.append("missing_OUT_node")
        else:
            display_node = root
            checks["has_display_node"] = True

        for node in root.allSubChildren() if hasattr(root, "allSubChildren") else []:
            try:
                if node.errors():
                    errors.append(f"node_error:{node.path()}:{';'.join(node.errors())}")
                if node.warnings():
                    warnings.append(f"node_warning:{node.path()}:{';'.join(node.warnings())}")
            except Exception:
                pass

        if display_node is None:
            errors.append("missing_display_node")
        else:
            try:
                display_node.cook(force=True)
                checks["cook_ok"] = True
            except Exception as e:
                errors.append(f"cook_failed:{type(e).__name__}:{e}")

        return {
            "success": len(errors) == 0,
            "message": "Graph validation completed",
            "error": None if len(errors) == 0 else "Graph validation failed",
            "context": {"checks": checks, "errors": errors, "warnings": warnings},
        }

    def validate_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        root_path = str(params.get("root_path", "")).strip()
        schema_id = str(params.get("schema_id", "")).strip().lower()
        if not root_path:
            raise RuntimeError("root_path is required")
        root = self.hou.node(root_path)
        if root is None:
            raise RuntimeError(f"Root node not found: {root_path}")

        if not schema_id:
            schema_id = str(root.userData("mcp_template_id") or "").lower()

        errors: list[str] = []
        warnings: list[str] = []
        values: dict[str, Any] = {}

        if schema_id == "single_building_v1":
            box = root.node("base_box")
            roof_xform = root.node("roof_xform")
            if box is None or roof_xform is None:
                errors.append("missing_template_nodes")
            else:
                sx = float(box.parm("sizex").eval())
                sy = float(box.parm("sizey").eval())
                sz = float(box.parm("sizez").eval())
                roof_scale = float(roof_xform.parm("sx").eval())
                values = {"width": sx, "height": sy, "depth": sz, "roof_scale": roof_scale}
                if not (1.0 <= sx <= 50.0):
                    errors.append("width_out_of_range")
                if not (1.0 <= sy <= 80.0):
                    errors.append("height_out_of_range")
                if not (1.0 <= sz <= 50.0):
                    errors.append("depth_out_of_range")
                if not (0.5 <= roof_scale <= 3.0):
                    errors.append("roof_scale_out_of_range")

        elif schema_id == "road_segment_v1":
            road = root.node("road_grid")
            if road is None:
                errors.append("missing_template_nodes")
            else:
                length = float(road.parm("sizex").eval())
                width = float(road.parm("sizey").eval())
                rows = int(road.parm("rows").eval())
                cols = int(road.parm("cols").eval())
                values = {"length": length, "width": width, "rows": rows, "cols": cols}
                if not (2.0 <= length <= 2000.0):
                    errors.append("length_out_of_range")
                if not (0.5 <= width <= 100.0):
                    errors.append("width_out_of_range")
                if rows < 2:
                    warnings.append("rows_too_low")
                if cols < 2:
                    warnings.append("cols_too_low")
        elif schema_id == "town_block_v1":
            ground = root.node("ground_grid")
            if ground is None:
                errors.append("missing_template_nodes")
            else:
                block_size = float(root.parm("block_size").eval()) if root.parm("block_size") else float(ground.parm("sizex").eval())
                road_width = float(root.parm("road_width").eval()) if root.parm("road_width") else 0.0
                road_mode = int(root.parm("road_mode").eval()) if root.parm("road_mode") else 1
                road_curve_path = str(root.parm("road_curve_path").eval()) if root.parm("road_curve_path") else ""
                density = float(root.parm("building_density").eval()) if root.parm("building_density") else 0.0
                min_h = float(root.parm("min_height").eval()) if root.parm("min_height") else 0.0
                max_h = float(root.parm("max_height").eval()) if root.parm("max_height") else 0.0
                min_f = float(root.parm("min_footprint").eval()) if root.parm("min_footprint") else 0.0
                max_f = float(root.parm("max_footprint").eval()) if root.parm("max_footprint") else 0.0
                values = {
                    "block_size": block_size,
                    "road_width": road_width,
                    "road_mode": road_mode,
                    "road_curve_path": road_curve_path,
                    "building_density": density,
                    "min_height": min_h,
                    "max_height": max_h,
                    "min_footprint": min_f,
                    "max_footprint": max_f,
                }
                if not (20.0 <= block_size <= 2000.0):
                    errors.append("block_size_out_of_range")
                if not (1.0 <= road_width <= 200.0):
                    errors.append("road_width_out_of_range")
                if road_width >= block_size:
                    errors.append("road_width_must_be_less_than_block_size")
                if not (0 <= road_mode <= 2):
                    errors.append("road_mode_out_of_range")
                if not (0.01 <= density <= 1.0):
                    errors.append("building_density_out_of_range")
                if min_h > max_h:
                    errors.append("height_range_invalid")
                if min_f > max_f:
                    errors.append("footprint_range_invalid")
        elif schema_id in {"crystal_courtyard_v1", "crystal_courtyard_v2"}:
            water_size = float(root.parm("water_size").eval()) if root.parm("water_size") else 0.0
            arch_count = int(root.parm("arch_count").eval()) if root.parm("arch_count") else 0
            ring_pillar_count = int(root.parm("ring_pillar_count").eval()) if root.parm("ring_pillar_count") else 0
            step_count = int(root.parm("step_count").eval()) if root.parm("step_count") else 0
            crystal_scale = float(root.parm("crystal_scale").eval()) if root.parm("crystal_scale") else 0.0
            values = {
                "water_size": water_size,
                "arch_count": arch_count,
                "ring_pillar_count": ring_pillar_count,
                "step_count": step_count,
                "crystal_scale": crystal_scale,
            }
            if not (40.0 <= water_size <= 4000.0):
                errors.append("water_size_out_of_range")
            if not (4 <= arch_count <= 128):
                errors.append("arch_count_out_of_range")
            if not (4 <= ring_pillar_count <= 256):
                errors.append("ring_pillar_count_out_of_range")
            if not (4 <= step_count <= 128):
                errors.append("step_count_out_of_range")
            if not (0.2 <= crystal_scale <= 8.0):
                errors.append("crystal_scale_out_of_range")
        else:
            warnings.append(f"unknown_schema:{schema_id}")

        return {
            "success": len(errors) == 0,
            "message": "Parameter validation completed",
            "error": None if len(errors) == 0 else "Parameter validation failed",
            "context": {"schema_id": schema_id, "values": values, "errors": errors, "warnings": warnings},
        }

    def dry_run_cook(self, params: Dict[str, Any]) -> Dict[str, Any]:
        root_path = str(params.get("root_path", "")).strip()
        if not root_path:
            raise RuntimeError("root_path is required")
        root = self.hou.node(root_path)
        if root is None:
            raise RuntimeError(f"Root node not found: {root_path}")

        if root.type().category().name() == "Object":
            target = root.displayNode()
            if target is None:
                raise RuntimeError(f"No display node found in {root_path}")
        else:
            target = root

        diagnostics: list[str] = []
        try:
            target.cook(force=True)
            geo = target.geometry()
            poly_count = len(geo.prims()) if geo else 0
            point_count = len(geo.points()) if geo else 0
        except Exception as e:
            diagnostics.append(f"cook_failed:{type(e).__name__}:{e}")
            return {
                "success": False,
                "message": "Dry run cook failed",
                "error": "Dry run cook failed",
                "context": {"root_path": root_path, "target_path": target.path(), "diagnostics": diagnostics},
            }

        return {
            "success": True,
            "message": "Dry run cook passed",
            "error": None,
            "context": {
                "root_path": root_path,
                "target_path": target.path(),
                "poly_count": poly_count,
                "point_count": point_count,
                "diagnostics": diagnostics,
            },
        }

    def inspect_geometry(self, params: Dict[str, Any]) -> Dict[str, Any]:
        root_path = str(params.get("root_path") or params.get("geo_path") or "").strip()
        if not root_path:
            raise RuntimeError("root_path or geo_path is required")
        root = self.hou.node(root_path)
        if root is None:
            raise RuntimeError(f"Node not found: {root_path}")

        if root.type().category().name() == "Object":
            target = root.displayNode()
            if target is None:
                raise RuntimeError(f"No display node found in {root_path}")
        else:
            target = root

        target.cook(force=True)
        geo = target.geometry()
        if geo is None:
            raise RuntimeError(f"No geometry on node: {target.path()}")

        bbox = geo.boundingBox()
        bmin = bbox.minvec()
        bmax = bbox.maxvec()
        center = bbox.center()
        size = bbox.sizevec()

        point_count = len(geo.points())
        prim_count = len(geo.prims())
        sample_indices = []
        sample_points = []
        if point_count > 0:
            sample_indices = sorted({0, point_count // 3, (point_count * 2) // 3, point_count - 1})
            points = geo.points()
            for idx in sample_indices:
                p = points[idx].position()
                sample_points.append([float(p[0]), float(p[1]), float(p[2])])

        return {
            "success": True,
            "message": "Geometry inspection completed",
            "error": None,
            "context": {
                "root_path": root_path,
                "target_path": target.path(),
                "point_count": point_count,
                "prim_count": prim_count,
                "bbox_min": [float(bmin[0]), float(bmin[1]), float(bmin[2])],
                "bbox_max": [float(bmax[0]), float(bmax[1]), float(bmax[2])],
                "bbox_center": [float(center[0]), float(center[1]), float(center[2])],
                "bbox_size": [float(size[0]), float(size[1]), float(size[2])],
                "sample_point_indices": sample_indices,
                "sample_points": sample_points,
            },
        }

    def create_box(self, params: Dict[str, Any]) -> Dict[str, Any]:
        node_name = params.get("node_name", "box")
        size_x = params.get("size_x", 1.0)
        size_y = params.get("size_y", 1.0)
        size_z = params.get("size_z", 1.0)

        obj = self.hou.node("/obj")
        geo = obj.createNode("geo", node_name)
        for child in geo.children():
            child.destroy()

        box = geo.createNode("box", "box1")
        box.parm("sizex").set(size_x)
        box.parm("sizey").set(size_y)
        box.parm("sizez").set(size_z)
        box.setDisplayFlag(True)
        box.setRenderFlag(True)
        geo.layoutChildren()

        geo_data = box.geometry()
        poly_count = len(geo_data.prims()) if geo_data else 0
        data = {
            "node_path": geo.path(),
            "box_size": [size_x, size_y, size_z],
            "poly_count": poly_count,
            "message": f"Box created at {geo.path()} with size [{size_x}, {size_y}, {size_z}]",
        }
        return {
            "success": True,
            "message": data["message"],
            "prompt": f"Box created at {data['node_path']}. Size: {data['box_size']}, {data['poly_count']} polygons.",
            "error": None,
            "context": data,
        }

    def clean_mesh(self, params: Dict[str, Any]) -> Dict[str, Any]:
        geo_path = params["geo_path"]
        output_name = params.get("output_name", "clean_mesh")
        fuse_points = bool(params.get("fuse_points", True))
        fuse_distance = float(params.get("fuse_distance", 0.0001))
        remove_degenerate = bool(params.get("remove_degenerate", True))
        fix_overlaps = bool(params.get("fix_overlaps", True))
        delete_overlaps = bool(params.get("delete_overlaps", False))
        delete_unused_points = bool(params.get("delete_unused_points", True))
        remove_unused_groups = bool(params.get("remove_unused_groups", True))
        delete_nans = bool(params.get("delete_nans", True))
        make_manifold = bool(params.get("make_manifold", False))

        geo_node, display_node = self._resolve_display_node(geo_path)
        input_geo = display_node.geometry()
        input_poly_count, input_point_count = self._geometry_counts(input_geo)

        clean = geo_node.createNode("clean", output_name)
        clean.setInput(0, display_node)
        clean.parm("fusepts").set(1 if fuse_points else 0)
        clean.parm("fusedist").set(fuse_distance)
        clean.parm("deldegengeo").set(1 if remove_degenerate else 0)
        clean.parm("fixoverlap").set(1 if fix_overlaps else 0)
        clean.parm("deleteoverlap").set(1 if delete_overlaps else 0)
        clean.parm("delunusedpts").set(1 if delete_unused_points else 0)
        clean.parm("removeunusedgrp").set(1 if remove_unused_groups else 0)
        clean.parm("delnans").set(1 if delete_nans else 0)
        if clean.parm("make_manifold"):
            clean.parm("make_manifold").set(1 if make_manifold else 0)
        clean.setDisplayFlag(True)
        clean.setRenderFlag(True)
        geo_node.layoutChildren()
        clean.cook(force=True)

        result_geo = clean.geometry()
        output_poly_count, output_point_count = self._geometry_counts(result_geo)
        data = {
            "node_path": clean.path(),
            "input_poly_count": input_poly_count,
            "input_point_count": input_point_count,
            "output_poly_count": output_poly_count,
            "output_point_count": output_point_count,
            "fuse_points": fuse_points,
            "fuse_distance": fuse_distance,
            "remove_degenerate": remove_degenerate,
            "fix_overlaps": fix_overlaps,
            "delete_unused_points": delete_unused_points,
            "message": (
                f"Mesh cleaned from {input_poly_count} to {output_poly_count} polygons "
                f"and {input_point_count} to {output_point_count} points"
            ),
        }
        return {
            "success": True,
            "message": data["message"],
            "prompt": f"Clean mesh completed: {data['message']}. Node: {data['node_path']}",
            "error": None,
            "context": data,
        }

    def fuse_points(self, params: Dict[str, Any]) -> Dict[str, Any]:
        geo_path = params["geo_path"]
        output_name = params.get("output_name", "fuse_points")
        distance = float(params.get("distance", 0.001))

        geo_node, display_node = self._resolve_display_node(geo_path)
        fuse = geo_node.createNode("fuse", output_name)
        fuse.setInput(0, display_node)
        fuse.parm("usetol3d").set(1)
        fuse.parm("tol3d").set(distance)
        fuse.setDisplayFlag(True)
        fuse.setRenderFlag(True)
        geo_node.layoutChildren()
        fuse.cook(force=True)

        result_geo = fuse.geometry()
        poly_count, point_count = self._geometry_counts(result_geo)
        data = {
            "node_path": fuse.path(),
            "distance": distance,
            "poly_count": poly_count,
            "point_count": point_count,
            "message": f"Fused points with tolerance {distance}",
        }
        return {
            "success": True,
            "message": data["message"],
            "prompt": f"Fuse points completed: {data['message']}. Node: {data['node_path']}",
            "error": None,
            "context": data,
        }

    def normalize_normals(self, params: Dict[str, Any]) -> Dict[str, Any]:
        geo_path = params["geo_path"]
        output_name = params.get("output_name", "normalize_normals")
        cusp_angle = float(params.get("cusp_angle", 60.0))
        reverse = bool(params.get("reverse", False))

        geo_node, display_node = self._resolve_display_node(geo_path)
        normal = geo_node.createNode("normal", output_name)
        normal.setInput(0, display_node)
        normal.parm("cuspangle").set(cusp_angle)
        normal.parm("normalize").set(1)
        normal.parm("reverse").set(1 if reverse else 0)
        normal.setDisplayFlag(True)
        normal.setRenderFlag(True)
        geo_node.layoutChildren()
        normal.cook(force=True)

        result_geo = normal.geometry()
        poly_count, point_count = self._geometry_counts(result_geo)
        data = {
            "node_path": normal.path(),
            "cusp_angle": cusp_angle,
            "reverse": reverse,
            "poly_count": poly_count,
            "point_count": point_count,
            "message": f"Normalized normals (cusp {cusp_angle} degrees)",
        }
        return {
            "success": True,
            "message": data["message"],
            "prompt": f"Normal fix completed: {data['message']}. Node: {data['node_path']}",
            "error": None,
            "context": data,
        }

    def cleanup_attributes(self, params: Dict[str, Any]) -> Dict[str, Any]:
        geo_path = params["geo_path"]
        output_name = params.get("output_name", "cleanup_attributes")
        remove_standard = bool(params.get("remove_standard", True))

        point_attrs = self._normalize_attribute_patterns(params.get("point_attributes", ""))
        vertex_attrs = self._normalize_attribute_patterns(params.get("vertex_attributes", ""))
        primitive_attrs = self._normalize_attribute_patterns(params.get("primitive_attributes", ""))
        detail_attrs = self._normalize_attribute_patterns(params.get("detail_attributes", ""))

        if remove_standard:
            primitive_attrs = self._merge_attribute_patterns(primitive_attrs, "shop_materialpath")
            detail_attrs = self._merge_attribute_patterns(detail_attrs, "varmap")

        geo_node, display_node = self._resolve_display_node(geo_path)
        attribdelete = geo_node.createNode("attribdelete", output_name)
        attribdelete.setInput(0, display_node)

        attribdelete.parm("doptdel").set(1 if point_attrs else 0)
        attribdelete.parm("ptdel").set(point_attrs)
        attribdelete.parm("dovtxdel").set(1 if vertex_attrs else 0)
        attribdelete.parm("vtxdel").set(vertex_attrs)
        attribdelete.parm("doprimdel").set(1 if primitive_attrs else 0)
        attribdelete.parm("primdel").set(primitive_attrs)
        attribdelete.parm("dodtldel").set(1 if detail_attrs else 0)
        attribdelete.parm("dtldel").set(detail_attrs)
        attribdelete.setDisplayFlag(True)
        attribdelete.setRenderFlag(True)
        geo_node.layoutChildren()
        attribdelete.cook(force=True)

        result_geo = attribdelete.geometry()
        data = {
            "node_path": attribdelete.path(),
            "point_attributes": point_attrs.split(),
            "vertex_attributes": vertex_attrs.split(),
            "primitive_attributes": primitive_attrs.split(),
            "detail_attributes": detail_attrs.split(),
            "point_count": len(result_geo.points()) if result_geo else 0,
            "poly_count": len(result_geo.prims()) if result_geo else 0,
            "message": "Removed selected point/vertex/primitive/detail attributes",
        }
        return {
            "success": True,
            "message": data["message"],
            "prompt": f"Attribute cleanup completed: {data['message']}. Node: {data['node_path']}",
            "error": None,
            "context": data,
        }

    def add_output_null(self, params: Dict[str, Any]) -> Dict[str, Any]:
        node_path = params["node_path"]
        null_name = self._sanitize_node_name(params.get("null_name", "OUT"), uppercase=True)

        geo_node, display_node = self._resolve_display_node(node_path)
        output_null = geo_node.createNode("null", null_name)
        output_null.setInput(0, display_node)
        output_null.setDisplayFlag(True)
        output_null.setRenderFlag(True)
        try:
            output_null.setColor(self.hou.Color((0.95, 0.75, 0.2)))
        except Exception:
            pass
        geo_node.layoutChildren()
        output_null.cook(force=True)

        result_geo = output_null.geometry()
        poly_count, point_count = self._geometry_counts(result_geo)
        data = {
            "node_path": output_null.path(),
            "null_name": output_null.name(),
            "poly_count": poly_count,
            "point_count": point_count,
            "message": f"Created output null {output_null.name()}",
        }
        return {
            "success": True,
            "message": data["message"],
            "prompt": f"Output null created: {data['node_path']}",
            "error": None,
            "context": data,
        }

    def freeze_transform(self, params: Dict[str, Any]) -> Dict[str, Any]:
        node_path = params["node_path"]
        output_name = self._sanitize_node_name(params.get("output_name", "frozen_geo"))
        add_output_null = bool(params.get("add_output_null", True))

        source_geo_node, source_display_node = self._resolve_display_node(node_path)
        obj = self.hou.node("/obj")
        frozen_geo = obj.createNode("geo", output_name)
        for child in frozen_geo.children():
            child.destroy()

        object_merge = frozen_geo.createNode("object_merge", "frozen_input")
        object_merge.parm("objpath1").set(source_display_node.path())
        object_merge.parm("xformtype").set(1)

        result_node = object_merge
        if add_output_null:
            result_node = frozen_geo.createNode("null", "OUT")
            result_node.setInput(0, object_merge)

        result_node.setDisplayFlag(True)
        result_node.setRenderFlag(True)
        frozen_geo.layoutChildren()
        result_node.cook(force=True)

        source_transform = self._extract_object_transform(source_geo_node)
        result_geo = result_node.geometry()
        poly_count, point_count = self._geometry_counts(result_geo)
        data = {
            "node_path": frozen_geo.path(),
            "result_sop_path": result_node.path(),
            "source_node_path": source_geo_node.path(),
            "baked_transform": source_transform,
            "poly_count": poly_count,
            "point_count": point_count,
            "message": f"Created frozen geometry copy at {frozen_geo.path()}",
        }
        return {
            "success": True,
            "message": data["message"],
            "prompt": f"Freeze transform completed: {data['message']}",
            "error": None,
            "context": data,
        }

    def create_hda_from_selection(self, params: Dict[str, Any]) -> Dict[str, Any]:
        node_paths = params.get("node_paths") or []
        asset_name = self._sanitize_asset_name(params.get("asset_name", "generated_asset"))
        asset_label = params.get("asset_label", asset_name.replace("_", " ").title())
        version = params.get("version", "")
        comment = params.get("comment", "Created by houdini-mcp")
        compress_contents = bool(params.get("compress_contents", True))
        save_as_embedded = bool(params.get("save_as_embedded", False))
        ignore_external_references = bool(params.get("ignore_external_references", False))
        hda_file_path = params.get("hda_file_path", "")

        nodes = self._resolve_nodes_for_asset(node_paths)
        source_node_paths = [node.path() for node in nodes]
        parent_paths = {node.parent().path() for node in nodes}
        if len(parent_paths) != 1:
            raise RuntimeError("All nodes must share the same parent network to create one HDA")

        asset_source = nodes[0]
        source_mode = "single_node"
        if len(nodes) > 1:
            parent = nodes[0].parent()
            subnet_name = self._sanitize_node_name(params.get("subnet_name", asset_name))
            asset_source = parent.collapseIntoSubnet(tuple(nodes), subnet_name=subnet_name)
            source_mode = "collapsed_subnet"

        if not hda_file_path and not save_as_embedded:
            hda_dir = Path.cwd() / "hda_outputs"
            hda_dir.mkdir(parents=True, exist_ok=True)
            hda_file_path = str(hda_dir / f"{asset_name}.hda")
        elif hda_file_path:
            hda_path = Path(hda_file_path)
            hda_path.parent.mkdir(parents=True, exist_ok=True)
            hda_file_path = str(hda_path)

        hda_node = asset_source.createDigitalAsset(
            name=asset_name,
            hda_file_name=hda_file_path or None,
            description=asset_label,
            compress_contents=compress_contents,
            comment=comment,
            version=version or None,
            save_as_embedded=save_as_embedded,
            ignore_external_references=ignore_external_references,
            change_node_type=True,
            create_backup=True,
        )

        definition = hda_node.type().definition()
        template_id = str(hda_node.userData("mcp_template_id") or asset_source.userData("mcp_template_id") or "").lower()
        if template_id == "single_building_v1":
            self._setup_building_controls(hda_node)
        elif template_id == "road_segment_v1":
            self._setup_road_controls(hda_node)
        elif template_id == "town_block_v1":
            self._setup_town_controls(hda_node)
        elif template_id == "crystal_courtyard_v1":
            self._setup_crystal_controls(hda_node)
        elif template_id == "crystal_courtyard_v2":
            self._setup_crystal_controls(hda_node)

        if definition is not None:
            try:
                definition.setParmTemplateGroup(hda_node.parmTemplateGroup())
            except Exception:
                # Keep HDA creation robust even when parm template write-back is not supported.
                pass

        data = {
            "node_path": hda_node.path(),
            "asset_name": asset_name,
            "asset_label": asset_label,
            "source_mode": source_mode,
            "source_node_paths": source_node_paths,
            "hda_file_path": hda_file_path or "embedded",
            "definition_node_type": definition.nodeTypeName() if definition else hda_node.type().name(),
            "message": f"Created HDA {asset_label} from {len(nodes)} node(s)",
        }
        return {
            "success": True,
            "message": data["message"],
            "prompt": f"HDA created: {data['asset_name']} at {data['hda_file_path']}",
            "error": None,
            "context": data,
        }

    def create_subnet_from_nodes(self, params: Dict[str, Any]) -> Dict[str, Any]:
        node_paths = params.get("node_paths") or []
        subnet_name = self._sanitize_node_name(params.get("subnet_name", "generated_subnet"))

        nodes = self._resolve_nodes_for_asset(node_paths)
        source_node_paths = [node.path() for node in nodes]
        parent_paths = {node.parent().path() for node in nodes}
        if len(parent_paths) != 1:
            raise RuntimeError("All nodes must share the same parent network to create one subnet")

        parent = nodes[0].parent()
        subnet = parent.collapseIntoSubnet(tuple(nodes), subnet_name=subnet_name)
        subnet.setDisplayFlag(True)
        if hasattr(subnet, "setRenderFlag"):
            subnet.setRenderFlag(True)
        parent.layoutChildren()

        data = {
            "node_path": subnet.path(),
            "subnet_name": subnet.name(),
            "source_node_paths": source_node_paths,
            "message": f"Created subnet {subnet.name()} from {len(nodes)} node(s)",
        }
        return {
            "success": True,
            "message": data["message"],
            "prompt": f"Subnet created: {data['node_path']}",
            "error": None,
            "context": data,
        }

    def mirror(self, params: Dict[str, Any]) -> Dict[str, Any]:
        geo_path = params["geo_path"]
        axis = params.get("axis", "x")
        merge = params.get("merge", True)
        consolidate_seam = params.get("consolidate_seam", True)
        output_name = params.get("output_name", "mirror")

        geo_node, display_node = self._resolve_display_node(geo_path)
        mirror = geo_node.createNode("mirror", output_name)
        mirror.setInput(0, display_node)

        axis_vectors = {
            "x": (1, 0, 0),
            "y": (0, 1, 0),
            "z": (0, 0, 1),
        }
        dirx, diry, dirz = axis_vectors.get(axis, (1, 0, 0))
        mirror.parm("dirx").set(dirx)
        mirror.parm("diry").set(diry)
        mirror.parm("dirz").set(dirz)
        if mirror.parm("consolidatepts"):
            mirror.parm("consolidatepts").set(1 if consolidate_seam else 0)
        if mirror.parm("keepOriginal"):
            mirror.parm("keepOriginal").set(1 if merge else 0)

        result_node = mirror
        if merge:
            merge_node = geo_node.createNode("merge", f"{output_name}_merge")
            merge_node.setInput(0, display_node)
            merge_node.setInput(1, mirror)
            result_node = merge_node

        result_node.setDisplayFlag(True)
        result_node.setRenderFlag(True)
        geo_node.layoutChildren()
        result_node.cook(force=True)
        result_geo = result_node.geometry()
        poly_count = len(result_geo.prims()) if result_geo else 0

        data = {
            "node_path": result_node.path(),
            "poly_count": poly_count,
            "axis": axis,
            "merged": merge,
            "message": f"Mirrored geometry along {axis}-axis",
        }
        return {
            "success": True,
            "message": data["message"],
            "prompt": f"Mirror completed: {data['message']}. Node: {data['node_path']}, {data['poly_count']} polygons.",
            "error": None,
            "context": data,
        }

    def delete_half(self, params: Dict[str, Any]) -> Dict[str, Any]:
        geo_path = params["geo_path"]
        axis = params.get("axis", "x")
        keep_side = params.get("keep_side", "positive")
        output_name = params.get("output_name", "delete_half")

        geo_node, display_node = self._resolve_display_node(geo_path)
        group_expr = geo_node.createNode("groupexpression", f"{output_name}_group")
        group_expr.setInput(0, display_node)
        group_expr.parm("grouptype").set(0)
        group_expr.parm("groupname1").set("delete_half_selection")

        if keep_side == "positive":
            expr = "@P.x < 0" if axis == "x" else "@P.y < 0" if axis == "y" else "@P.z < 0"
        else:
            expr = "@P.x > 0" if axis == "x" else "@P.y > 0" if axis == "y" else "@P.z > 0"

        group_expr.parm("snippet1").set(expr)

        delete_node = geo_node.createNode("blast", output_name)
        delete_node.setInput(0, group_expr)
        delete_node.parm("group").set("delete_half_selection")
        delete_node.parm("grouptype").set(0)
        delete_node.parm("negate").set(0)
        delete_node.setDisplayFlag(True)
        delete_node.setRenderFlag(True)
        geo_node.layoutChildren()
        delete_node.cook(force=True)
        result_geo = delete_node.geometry()
        poly_count = len(result_geo.prims()) if result_geo else 0

        data = {
            "node_path": delete_node.path(),
            "poly_count": poly_count,
            "axis": axis,
            "kept_side": keep_side,
            "message": f"Deleted {keep_side} side along {axis}-axis",
        }
        return {
            "success": True,
            "message": data["message"],
            "prompt": f"Delete half completed: {data['message']}. Node: {data['node_path']}",
            "error": None,
            "context": data,
        }

    def polyreduce(self, params: Dict[str, Any]) -> Dict[str, Any]:
        geo_path = params["geo_path"]
        target_percent = params.get("target_percent", 50.0)
        output_name = params.get("output_name", "polyreduce1")

        geo_node, display_node = self._resolve_display_node(geo_path)
        original_geo = display_node.geometry()
        original_count = len(original_geo.prims()) if original_geo else 0

        polyreduce = geo_node.createNode("polyreduce", output_name)
        polyreduce.setInput(0, display_node)
        polyreduce.parm("percentage").set(target_percent)
        polyreduce.setDisplayFlag(True)
        polyreduce.setRenderFlag(True)
        geo_node.layoutChildren()
        polyreduce.cook(force=True)
        reduced_geo = polyreduce.geometry()
        reduced_count = len(reduced_geo.prims()) if reduced_geo else 0
        actual_percent = (reduced_count / original_count * 100) if original_count > 0 else 0

        data = {
            "node_path": polyreduce.path(),
            "original_poly_count": original_count,
            "reduced_poly_count": reduced_count,
            "target_percent": target_percent,
            "actual_percent": round(actual_percent, 2),
            "message": f"Reduced from {original_count} to {reduced_count} polygons ({actual_percent:.1f}%)",
        }
        return {
            "success": True,
            "message": data["message"],
            "prompt": f"Polyreduce completed: {data['message']}. Node: {data['node_path']}",
            "error": None,
            "context": data,
        }

    def smooth(self, params: Dict[str, Any]) -> Dict[str, Any]:
        geo_path = params["geo_path"]
        output_name = params.get("output_name", "smooth1")
        strength = float(params.get("strength", 0.5))
        strength = max(0.0, min(1.0, strength))

        geo_node, display_node = self._resolve_display_node(geo_path)
        smooth = geo_node.createNode("smooth", output_name)
        smooth.setInput(0, display_node)
        if smooth.parm("strength"):
            smooth.parm("strength").set(strength)
        smooth.setDisplayFlag(True)
        smooth.setRenderFlag(True)
        geo_node.layoutChildren()
        smooth.cook(force=True)

        result_geo = smooth.geometry()
        poly_count, point_count = self._geometry_counts(result_geo)
        data = {
            "node_path": smooth.path(),
            "strength": strength,
            "poly_count": poly_count,
            "point_count": point_count,
            "message": f"Smoothed geometry with strength {strength:.2f}",
        }
        return {
            "success": True,
            "message": data["message"],
            "prompt": f"Smooth completed: {data['message']}. Node: {data['node_path']}",
            "error": None,
            "context": data,
        }

    def boolean(self, params: Dict[str, Any]) -> Dict[str, Any]:
        geo_path_a = params["geo_path_a"]
        geo_path_b = params.get("geo_path_b", "")
        operation = params.get("operation", "union")
        output_name = params.get("output_name", "boolean")

        geo_node_a, display_node_a = self._resolve_display_node(geo_path_a)
        _, display_node_b = self._resolve_display_node(geo_path_b)

        obj = self.hou.node("/obj")
        container = obj.createNode("geo", f"{output_name}_container")
        for child in container.children():
            child.destroy()

        merge_a = container.createNode("object_merge", "input_a")
        merge_a.parm("objpath1").set(display_node_a.path())
        merge_a.parm("xformtype").set(1)

        merge_b = container.createNode("object_merge", "input_b")
        merge_b.parm("objpath1").set(display_node_b.path())
        merge_b.parm("xformtype").set(1)

        boolean = container.createNode("boolean", output_name)
        boolean.setInput(0, merge_a)
        boolean.setInput(1, merge_b)
        op_map = {"union": 2, "intersect": 3, "subtract": 0, "shatter": 4}
        boolean.parm("booleanop").set(op_map.get(operation, 2))
        boolean.setDisplayFlag(True)
        boolean.setRenderFlag(True)
        container.layoutChildren()
        boolean.cook(force=True)
        result_geo = boolean.geometry()
        poly_count = len(result_geo.prims()) if result_geo else 0

        data = {
            "node_path": boolean.path(),
            "poly_count": poly_count,
            "operation": operation,
            "message": f"Boolean {operation} completed with {poly_count} polygons",
        }
        return {
            "success": True,
            "message": data["message"],
            "prompt": f"Boolean {operation} completed: {data['message']}",
            "error": None,
            "context": data,
        }

    def import_geometry(self, params: Dict[str, Any]) -> Dict[str, Any]:
        file_path = params["file_path"]
        node_name = params.get("node_name", "imported_geo")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()
        obj = self.hou.node("/obj")
        geo = obj.createNode("geo", node_name)
        for child in geo.children():
            child.destroy()

        if ext == ".abc":
            file_node = geo.createNode("alembic", "import1")
            file_node.parm("fileName").set(file_path)
        else:
            file_node = geo.createNode("file", "import1")
            file_node.parm("file").set(file_path)

        file_node.setDisplayFlag(True)
        file_node.setRenderFlag(True)
        geo.layoutChildren()
        file_node.cook(force=True)
        geo_data = file_node.geometry()
        poly_count = len(geo_data.prims()) if geo_data else 0
        point_count = len(geo_data.points()) if geo_data else 0

        data = {
            "node_path": geo.path(),
            "file_path": file_path,
            "file_type": ext,
            "poly_count": poly_count,
            "point_count": point_count,
            "message": f"Imported {os.path.basename(file_path)} with {poly_count} polygons",
        }
        return {
            "success": True,
            "message": data["message"],
            "prompt": f"Import completed: {data['message']}. Node: {data['node_path']}",
            "error": None,
            "context": data,
        }

    def import_model(self, params: Dict[str, Any]) -> Dict[str, Any]:
        file_path = params["file_path"]
        node_name = params.get("node_name", "imported_geo")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        uniform_scale = float(params.get("uniform_scale", 1.0))
        center_to_origin = bool(params.get("center_to_origin", False))
        normalize_normals = bool(params.get("normalize_normals", False))
        output_name = params.get("output_name", "import_model")

        ext = os.path.splitext(file_path)[1].lower()
        obj = self.hou.node("/obj")
        geo = obj.createNode("geo", node_name)
        for child in geo.children():
            child.destroy()

        if ext == ".abc":
            file_node = geo.createNode("alembic", "import1")
            file_node.parm("fileName").set(file_path)
        else:
            file_node = geo.createNode("file", "import1")
            file_node.parm("file").set(file_path)

        current = file_node
        imported_geo = None
        try:
            file_node.cook(force=True)
            imported_geo = file_node.geometry()
        except Exception:
            imported_geo = None

        if abs(uniform_scale - 1.0) > 1e-6 or center_to_origin:
            xform = geo.createNode("xform", "xform_import")
            xform.setInput(0, current)
            if xform.parm("sx"):
                xform.parm("sx").set(uniform_scale)
            if xform.parm("sy"):
                xform.parm("sy").set(uniform_scale)
            if xform.parm("sz"):
                xform.parm("sz").set(uniform_scale)

            if center_to_origin and imported_geo is not None:
                bbox = imported_geo.boundingBox()
                center = bbox.center()
                if xform.parm("tx"):
                    xform.parm("tx").set(-center[0])
                if xform.parm("ty"):
                    xform.parm("ty").set(-center[1])
                if xform.parm("tz"):
                    xform.parm("tz").set(-center[2])
            current = xform

        if normalize_normals:
            normal = geo.createNode("normal", "normal_import")
            normal.setInput(0, current)
            if normal.parm("normalize"):
                normal.parm("normalize").set(1)
            current = normal

        current.setName(output_name, unique_name=True)
        current.setDisplayFlag(True)
        current.setRenderFlag(True)
        geo.layoutChildren()
        current.cook(force=True)

        geo_data = current.geometry()
        poly_count = len(geo_data.prims()) if geo_data else 0
        point_count = len(geo_data.points()) if geo_data else 0
        data = {
            "node_path": geo.path(),
            "result_sop_path": current.path(),
            "file_path": file_path,
            "file_type": ext,
            "uniform_scale": uniform_scale,
            "center_to_origin": center_to_origin,
            "normalize_normals": normalize_normals,
            "poly_count": poly_count,
            "point_count": point_count,
            "message": f"Imported model {os.path.basename(file_path)} with params",
        }
        return {
            "success": True,
            "message": data["message"],
            "prompt": f"Import model completed: {data['message']}. Node: {data['result_sop_path']}",
            "error": None,
            "context": data,
        }

    def capture_screenshot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        output_path = str(params.get("output_path", "")).strip()
        if not output_path:
            raise RuntimeError("output_path is required")
        camera_path = str(params.get("camera_path", "")).strip()
        width = max(64, int(params.get("width", 1024)))
        height = max(64, int(params.get("height", 1024)))
        capture_mode = str(params.get("capture_mode", "auto")).strip().lower() or "auto"

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        obj = self.hou.node("/obj")
        if not camera_path:
            camera = self.hou.node("/obj/cam1")
            if camera is None:
                camera = obj.createNode("cam", "cam1")
                camera.parm("tx").set(6)
                camera.parm("ty").set(4)
                camera.parm("tz").set(6)
                camera.parm("rx").set(-25)
                camera.parm("ry").set(35)
            camera_path = camera.path()
        else:
            camera = self.hou.node(camera_path)
            if camera is None:
                raise RuntimeError(f"Camera not found: {camera_path}")

        out = self.hou.node("/out")
        rop = out.createNode("opengl", "mcp_capture")
        rop.parm("camera").set(camera_path)
        if rop.parm("trange"):
            rop.parm("trange").set(0)
        if rop.parm("res1"):
            rop.parm("res1").set(width)
        if rop.parm("res2"):
            rop.parm("res2").set(height)
        if rop.parm("forceobjects"):
            rop.parm("forceobjects").set("*")
        if rop.parm("picture"):
            rop.parm("picture").set(str(output_file))
        elif rop.parm("vm_picture"):
            rop.parm("vm_picture").set(str(output_file))
        mode_used = "smooth"

        def _render_with_mode(mode_token: str) -> None:
            if rop.parm("shadingmode"):
                rop.parm("shadingmode").set(mode_token)
            if rop.parm("hqlighting"):
                rop.parm("hqlighting").set(1 if mode_token != "wire" else 0)
            if rop.parm("usegeocolor"):
                rop.parm("usegeocolor").set(1 if mode_token == "wire" else 0)
            rop.parm("execute").pressButton()

        def _is_mostly_black(path: Path) -> bool:
            try:
                from PIL import Image, ImageStat

                with Image.open(path) as img:
                    rgb = img.convert("RGB")
                    stat = ImageStat.Stat(rgb)
                    mean = stat.mean
                    luminance = (0.2126 * mean[0]) + (0.7152 * mean[1]) + (0.0722 * mean[2])
                    return luminance < 2.0
            except Exception:
                return False

        if capture_mode in {"wire", "smooth"}:
            mode_used = capture_mode
            _render_with_mode(capture_mode)
        else:
            _render_with_mode("smooth")
            if output_file.exists() and _is_mostly_black(output_file):
                _render_with_mode("wire")
                mode_used = "wire"
            else:
                mode_used = "smooth"

        if not output_file.exists():
            raise RuntimeError(f"Houdini screenshot failed: {output_file}")

        data = {
            "output_path": str(output_file),
            "camera_path": camera_path,
            "width": width,
            "height": height,
            "capture_mode_used": mode_used,
        }
        message = f"Captured Houdini screenshot: {output_file.name}"
        return {"success": True, "message": message, "prompt": message, "error": None, "context": data}

    def frame_camera_on_geo(self, params: Dict[str, Any]) -> Dict[str, Any]:
        geo_path = str(params.get("geo_path", "")).strip()
        if not geo_path:
            raise RuntimeError("geo_path is required")
        camera_path = str(params.get("camera_path", "/obj/cam1")).strip() or "/obj/cam1"
        distance_scale = float(params.get("distance_scale", 2.2))
        height_scale = float(params.get("height_scale", 0.65))
        view = str(params.get("view", "front")).strip().lower() or "front"

        root_node, display_node = self._resolve_display_node(geo_path)
        try:
            if root_node is not None and root_node.type().category().name() == "Object":
                for child in root_node.children():
                    if child.type().category().name() == "Sop":
                        child.setDisplayFlag(child.path() == display_node.path())
                        child.setRenderFlag(child.path() == display_node.path())
            else:
                display_node.setDisplayFlag(True)
                display_node.setRenderFlag(True)
        except Exception:
            pass
        geo = display_node.geometry()
        if geo is None:
            raise RuntimeError(f"No geometry to frame for: {display_node.path()}")

        bbox = geo.boundingBox()
        center = bbox.center()
        size = bbox.sizevec()
        sx = max(0.001, float(size[0]))
        sy = max(0.001, float(size[1]))
        sz = max(0.001, float(size[2]))
        span = max(sx, sy, sz)

        cam = self.hou.node(camera_path)
        if cam is None:
            cam = self.hou.node("/obj").createNode("cam", self._sanitize_node_name(Path(camera_path).name or "cam1"))
            camera_path = cam.path()

        cx, cy, cz = float(center[0]), float(center[1]), float(center[2])
        if view == "top":
            px = cx
            py = cy + span * distance_scale
            pz = cz
            pitch, yaw = -90.0, 0.0
        elif view == "side":
            px = cx + span * distance_scale
            py = cy + span * height_scale
            pz = cz
            dx = cx - px
            dy = cy - py
            dz = cz - pz
            yaw = math.degrees(math.atan2(-dx, -dz))
            horiz = math.sqrt(dx * dx + dz * dz)
            pitch = math.degrees(math.atan2(dy, horiz))
        else:
            px = cx
            py = cy + span * height_scale
            pz = cz + span * distance_scale
            dx = cx - px
            dy = cy - py
            dz = cz - pz
            yaw = math.degrees(math.atan2(-dx, -dz))
            horiz = math.sqrt(dx * dx + dz * dz)
            pitch = math.degrees(math.atan2(dy, horiz))

        cam.parmTuple("t").set((px, py, pz))
        cam.parmTuple("r").set((pitch, yaw, 0.0))
        if cam.parm("focal"):
            cam.parm("focal").set(35.0)
        if cam.parm("near"):
            cam.parm("near").set(max(0.01, span * 0.01))
        if cam.parm("far"):
            cam.parm("far").set(max(2000.0, span * 20.0))

        data = {
            "geo_path": geo_path,
            "display_node_path": display_node.path(),
            "camera_path": camera_path,
            "view": view,
            "center": [cx, cy, cz],
            "bbox_size": [sx, sy, sz],
            "camera_translate": [px, py, pz],
            "camera_rotate": [pitch, yaw, 0.0],
        }
        message = f"Framed camera {camera_path} on {geo_path}"
        return {"success": True, "message": message, "prompt": message, "error": None, "context": data}

    def export_geometry(self, params: Dict[str, Any]) -> Dict[str, Any]:
        geo_path = params["geo_path"]
        output_path = params["output_path"]
        file_type = params.get("file_type", "").lower().strip()
        embed_media = bool(params.get("embed_media", False))
        convert_axis = bool(params.get("convert_axis", False))
        convert_units = bool(params.get("convert_units", False))
        axis_system = str(params.get("axis_system", "")).strip()
        vc_format = str(params.get("vc_format", "maya")).strip().lower()
        sdk_version_index = int(params.get("sdk_version_index", -1))
        target_engine = str(params.get("target_engine", "")).strip().lower()

        output_ext = os.path.splitext(output_path)[1].lower()
        if not file_type:
            file_type = output_ext.lstrip(".")
        if file_type != "fbx":
            raise RuntimeError(f"Only fbx export is currently supported, got: {file_type}")

        geo_node, display_node = self._resolve_display_node(geo_path)

        # Engine presets first, allow explicit params to override after this block.
        if target_engine == "unity":
            embed_media = True if "embed_media" not in params else embed_media
            convert_axis = True if "convert_axis" not in params else convert_axis
            convert_units = True if "convert_units" not in params else convert_units
            if not axis_system:
                axis_system = "yupleft"
            if "vc_format" not in params:
                vc_format = "maya"
            if "sdk_version_index" not in params:
                sdk_version_index = 2  # FBX201800

        out = self.hou.node("/out")
        export_node = out.createNode("filmboxfbx", "export_fbx1")
        self._set_parm_if_exists(export_node, "startnode", display_node.path())
        self._set_parm_if_exists(export_node, "sopoutput", output_path)
        self._set_parm_if_exists(export_node, "embedmedia", 1 if embed_media else 0)
        self._set_parm_if_exists(export_node, "convertaxis", 1 if convert_axis else 0)
        self._set_parm_if_exists(export_node, "convertunits", 1 if convert_units else 0)
        if axis_system:
            self._set_menu_parm_if_exists(export_node, "axissystem", axis_system)
        if vc_format in {"maya", "max"}:
            self._set_parm_if_exists(export_node, "vcformat", 0 if vc_format == "maya" else 1)
        if sdk_version_index >= 0:
            self._set_menu_index_parm_if_exists(export_node, "sdkversion", sdk_version_index)

        out.layoutChildren()
        export_node.parm("execute").pressButton()

        if not os.path.exists(output_path):
            raise RuntimeError(f"Export failed, output file not found: {output_path}")

        data = {
            "node_path": export_node.path(),
            "geo_path": display_node.path(),
            "output_path": output_path,
            "file_type": file_type,
            "target_engine": target_engine,
            "embed_media": embed_media,
            "convert_axis": convert_axis,
            "convert_units": convert_units,
            "axis_system": axis_system or None,
            "vc_format": vc_format,
            "sdk_version_index": sdk_version_index,
            "message": f"Exported geometry to {output_path}",
        }
        return {
            "success": True,
            "message": data["message"],
            "prompt": f"Export completed: {data['message']}",
            "error": None,
            "context": data,
        }

    def export_unity_fbx(self, params: Dict[str, Any]) -> Dict[str, Any]:
        export_params = dict(params)
        export_params["file_type"] = "fbx"
        export_params["target_engine"] = "unity"
        if "embed_media" not in export_params:
            export_params["embed_media"] = True
        return self.export_geometry(export_params)

    def _setup_building_controls(self, geo) -> None:
        if geo.parm("width") and geo.parm("height") and geo.parm("depth"):
            return
        ptg = geo.parmTemplateGroup()

        controls_folder = self.hou.FolderParmTemplate("mcp_shape", "MCP Shape")
        controls_folder.addParmTemplate(self.hou.FloatParmTemplate("width", "Width", 1, default_value=(8.0,), min=1.0, max=50.0))
        controls_folder.addParmTemplate(self.hou.FloatParmTemplate("height", "Height", 1, default_value=(12.0,), min=1.0, max=80.0))
        controls_folder.addParmTemplate(self.hou.FloatParmTemplate("depth", "Depth", 1, default_value=(8.0,), min=1.0, max=50.0))
        controls_folder.addParmTemplate(self.hou.FloatParmTemplate("roof_scale", "Roof Scale", 1, default_value=(1.15,), min=0.5, max=3.0))
        controls_folder.addParmTemplate(self.hou.FloatParmTemplate("roof_height", "Roof Height", 1, default_value=(3.0,), min=0.2, max=20.0))
        controls_folder.addParmTemplate(self.hou.IntParmTemplate("seed", "Seed", 1, default_value=(0,), min=0, max=100000))
        ptg.append(controls_folder)
        geo.setParmTemplateGroup(ptg)

        base = geo.node("base_box")
        base_xf = geo.node("base_xform")
        roof = geo.node("roof_peak")
        roof_xf = geo.node("roof_xform")

        if base:
            base.parm("sizex").setExpression('ch("../width")')
            base.parm("sizey").setExpression('ch("../height")')
            base.parm("sizez").setExpression('ch("../depth")')
        if base_xf:
            base_xf.parm("ty").setExpression('ch("../height")*0.5')
        if roof:
            roof.parm("height").setExpression('ch("../roof_height")')
            roof.parm("rad1").setExpression('max(ch("../width"), ch("../depth"))*0.4')
        if roof_xf:
            roof_xf.parm("sx").setExpression('ch("../roof_scale")')
            roof_xf.parm("sz").setExpression('ch("../roof_scale")')
            roof_xf.parm("ty").setExpression('ch("../height")+ch("../roof_height")*0.5')

    def _setup_road_controls(self, geo) -> None:
        if geo.parm("length") and geo.parm("width") and geo.parm("rows") and geo.parm("cols"):
            return
        ptg = geo.parmTemplateGroup()

        controls_folder = self.hou.FolderParmTemplate("mcp_shape", "MCP Shape")
        controls_folder.addParmTemplate(self.hou.FloatParmTemplate("length", "Length", 1, default_value=(30.0,), min=2.0, max=2000.0))
        controls_folder.addParmTemplate(self.hou.FloatParmTemplate("width", "Width", 1, default_value=(6.0,), min=0.5, max=100.0))
        controls_folder.addParmTemplate(self.hou.IntParmTemplate("rows", "Rows", 1, default_value=(8,), min=2, max=256))
        controls_folder.addParmTemplate(self.hou.IntParmTemplate("cols", "Cols", 1, default_value=(16,), min=2, max=2048))
        controls_folder.addParmTemplate(self.hou.FloatParmTemplate("curb_height", "Curb Height", 1, default_value=(0.15,), min=-1.0, max=2.0))
        controls_folder.addParmTemplate(self.hou.IntParmTemplate("seed", "Seed", 1, default_value=(0,), min=0, max=100000))
        ptg.append(controls_folder)
        geo.setParmTemplateGroup(ptg)

        road = geo.node("road_grid")
        peak = geo.node("road_crown")

        if road:
            road.parm("sizex").setExpression('ch("../length")')
            road.parm("sizey").setExpression('ch("../width")')
            road.parm("rows").setExpression('ch("../rows")')
            road.parm("cols").setExpression('ch("../cols")')
        if peak:
            peak.parm("dist").setExpression('ch("../curb_height")')

    def _setup_town_controls(self, geo) -> None:
        if geo.parm("block_size") and geo.parm("road_width") and geo.parm("building_density"):
            return
        ptg = geo.parmTemplateGroup()

        controls_folder = self.hou.FolderParmTemplate("mcp_town", "MCP Town")
        controls_folder.addParmTemplate(
            self.hou.FloatParmTemplate("block_size", "Block Size", 1, default_value=(120.0,), min=20.0, max=2000.0)
        )
        controls_folder.addParmTemplate(
            self.hou.FloatParmTemplate("road_width", "Road Width", 1, default_value=(10.0,), min=1.0, max=200.0)
        )
        controls_folder.addParmTemplate(
            self.hou.IntParmTemplate(
                "road_mode",
                "Road Mode (0 Cross, 1 Curve, 2 Both)",
                1,
                default_value=(1,),
                min=0,
                max=2,
            )
        )
        curve_ref_template = self.hou.StringParmTemplate(
            "road_curve_path",
            "Road Curve SOP Path",
            1,
            default_value=("",),
            string_type=self.hou.stringParmType.NodeReference,
        )
        curve_ref_template.setTags(
            {
                "opfilter": "!!SOP!!",
                "oprelative": ".",
            }
        )
        controls_folder.addParmTemplate(curve_ref_template)
        controls_folder.addParmTemplate(
            self.hou.FloatParmTemplate(
                "building_density", "Building Density", 1, default_value=(0.35,), min=0.01, max=1.0
            )
        )
        controls_folder.addParmTemplate(
            self.hou.FloatParmTemplate("min_height", "Min Height", 1, default_value=(6.0,), min=1.0, max=200.0)
        )
        controls_folder.addParmTemplate(
            self.hou.FloatParmTemplate("max_height", "Max Height", 1, default_value=(24.0,), min=1.0, max=400.0)
        )
        controls_folder.addParmTemplate(
            self.hou.FloatParmTemplate("min_footprint", "Min Footprint", 1, default_value=(2.0,), min=0.5, max=30.0)
        )
        controls_folder.addParmTemplate(
            self.hou.FloatParmTemplate("max_footprint", "Max Footprint", 1, default_value=(6.0,), min=0.5, max=60.0)
        )
        controls_folder.addParmTemplate(self.hou.IntParmTemplate("seed", "Seed", 1, default_value=(0,), min=0, max=100000))
        ptg.append(controls_folder)
        geo.setParmTemplateGroup(ptg)

        ground = geo.node("ground_grid")
        road_x = geo.node("road_strip_x")
        road_z = geo.node("road_strip_z")
        road_mode_switch = geo.node("road_mode_switch")
        road_curve_input = geo.node("road_curve_input")
        road_curve_switch = geo.node("road_curve_switch")
        road_curve_polywire = geo.node("road_curve_polywire")
        road_curve_mask_points = geo.node("road_curve_mask_points")
        scatter = geo.node("building_scatter")

        if ground:
            ground.parm("sizex").setExpression('ch("../block_size")')
            ground.parm("sizey").setExpression('ch("../block_size")')
        if road_x:
            road_x.parm("sizex").setExpression('ch("../block_size")')
            road_x.parm("sizey").setExpression('ch("../road_width")')
        if road_z:
            road_z.parm("sizex").setExpression('ch("../road_width")')
            road_z.parm("sizey").setExpression('ch("../block_size")')
        if road_mode_switch and road_mode_switch.parm("input"):
            road_mode_switch.parm("input").setExpression('ch("../road_mode")')
        if road_curve_input and road_curve_input.parm("objpath1"):
            road_curve_input.parm("objpath1").setExpression('chs("../road_curve_path")')
        if road_curve_input and road_curve_input.parm("xformtype"):
            road_curve_input.parm("xformtype").set(1)
        if road_curve_switch and road_curve_switch.parm("input"):
            road_curve_switch.parm("input").setExpression('if(strlen(chs("../road_curve_path"))>0,1,0)')
        if road_curve_polywire and road_curve_polywire.parm("radius"):
            road_curve_polywire.parm("radius").setExpression('ch("../road_width")*0.5')
        if road_curve_mask_points and road_curve_mask_points.parm("length"):
            road_curve_mask_points.parm("length").setExpression('max(0.2, ch("../road_width")*0.35)')
        if scatter:
            scatter.parm("npts").setExpression('max(1, int(ch("../building_density") * pow(ch("../block_size") / 10.0, 2.0) * 12.0))')
            scatter.parm("seed").setExpression('ch("../seed")')

    def _setup_crystal_controls(self, geo) -> None:
        if geo.parm("water_size") and geo.parm("arch_count") and geo.parm("ring_pillar_count"):
            return
        ptg = geo.parmTemplateGroup()
        controls_folder = self.hou.FolderParmTemplate("mcp_crystal", "MCP Crystal")
        controls_folder.addParmTemplate(
            self.hou.FloatParmTemplate("water_size", "Water Size", 1, default_value=(420.0,), min=40.0, max=4000.0)
        )
        controls_folder.addParmTemplate(
            self.hou.IntParmTemplate("arch_count", "Arch Count", 1, default_value=(16,), min=4, max=128)
        )
        controls_folder.addParmTemplate(
            self.hou.IntParmTemplate("ring_pillar_count", "Ring Pillar Count", 1, default_value=(18,), min=4, max=256)
        )
        controls_folder.addParmTemplate(
            self.hou.IntParmTemplate("step_count", "Step Count", 1, default_value=(14,), min=4, max=128)
        )
        controls_folder.addParmTemplate(
            self.hou.FloatParmTemplate("crystal_scale", "Crystal Scale", 1, default_value=(1.0,), min=0.2, max=8.0)
        )
        controls_folder.addParmTemplate(self.hou.IntParmTemplate("seed", "Seed", 1, default_value=(0,), min=0, max=100000))
        ptg.append(controls_folder)
        geo.setParmTemplateGroup(ptg)

        water = geo.node("water_plane")
        arch_pts = geo.node("arch_points")
        ring_pts = geo.node("ring_points")
        steps_pts = geo.node("step_points")
        arch_copy = geo.node("arch_copy")
        ring_copy = geo.node("ring_copy")
        step_copy = geo.node("step_copy")
        arch_crystal = geo.node("arch_crystal")
        ring_crystal = geo.node("ring_crystal")
        step_box = geo.node("step_box")

        if water:
            water.parm("sizex").setExpression('ch("../water_size")')
            water.parm("sizey").setExpression('ch("../water_size")')
        if arch_pts and arch_pts.parm("npts"):
            arch_pts.parm("npts").setExpression('chi("../arch_count")')
        if ring_pts and ring_pts.parm("npts"):
            ring_pts.parm("npts").setExpression('chi("../ring_pillar_count")')
        if steps_pts and steps_pts.parm("npts"):
            steps_pts.parm("npts").setExpression('chi("../step_count")')
        if arch_copy and arch_copy.parm("stamp"):
            arch_copy.parm("stamp").set(1)
        if ring_copy and ring_copy.parm("stamp"):
            ring_copy.parm("stamp").set(1)
        if step_copy and step_copy.parm("stamp"):
            step_copy.parm("stamp").set(1)
        if arch_crystal:
            arch_crystal.parm("sizex").setExpression('max(0.8, ch("../water_size")*0.018*ch("../crystal_scale"))')
            arch_crystal.parm("sizey").setExpression('max(2.0, ch("../water_size")*0.13*ch("../crystal_scale"))')
            arch_crystal.parm("sizez").setExpression('max(0.8, ch("../water_size")*0.018*ch("../crystal_scale"))')
        if ring_crystal:
            ring_crystal.parm("sizex").setExpression('max(0.8, ch("../water_size")*0.015*ch("../crystal_scale"))')
            ring_crystal.parm("sizey").setExpression('max(2.0, ch("../water_size")*0.16*ch("../crystal_scale"))')
            ring_crystal.parm("sizez").setExpression('max(0.8, ch("../water_size")*0.015*ch("../crystal_scale"))')
        if step_box:
            step_box.parm("sizex").setExpression('max(2.0, ch("../water_size")*0.11)')
            step_box.parm("sizey").setExpression('max(0.25, ch("../water_size")*0.004)')
            step_box.parm("sizez").setExpression('max(1.0, ch("../water_size")*0.03)')

    def _build_template_single_building_v1(self, parent, node_name: str, overrides: Dict[str, Any]) -> Dict[str, Any]:
        name = self._sanitize_node_name(node_name or "single_building")
        width = float(overrides.get("width", 8.0))
        height = float(overrides.get("height", 12.0))
        depth = float(overrides.get("depth", 8.0))
        roof_scale = float(overrides.get("roof_scale", 1.15))
        roof_height = float(overrides.get("roof_height", 3.0))

        geo = parent.createNode("geo", name)
        for child in geo.children():
            child.destroy()

        base = geo.createNode("box", "base_box")
        base.parm("sizex").set(width)
        base.parm("sizey").set(height)
        base.parm("sizez").set(depth)
        base_xf = geo.createNode("xform", "base_xform")
        base_xf.setInput(0, base)
        base_xf.parmTuple("t").set((0, height * 0.5, 0))

        roof = geo.createNode("tube", "roof_peak")
        roof.parm("type").set(1)  # polygon
        roof.parm("cap").set(1)
        roof.parm("rad1").set(max(width, depth) * 0.4)
        roof.parm("rad2").set(0)
        roof.parm("height").set(roof_height)
        roof.parm("rows").set(1)
        roof_xf = geo.createNode("xform", "roof_xform")
        roof_xf.setInput(0, roof)
        roof_xf.parmTuple("s").set((roof_scale, 1.0, roof_scale))
        roof_xf.parmTuple("t").set((0, height + roof_height * 0.5, 0))

        merge = geo.createNode("merge", "merge_building")
        merge.setInput(0, base_xf)
        merge.setInput(1, roof_xf)
        out = geo.createNode("null", "OUT")
        out.setInput(0, merge)
        out.setDisplayFlag(True)
        out.setRenderFlag(True)
        geo.layoutChildren()
        out.cook(force=True)
        geo.setUserData("mcp_template_id", "single_building_v1")
        self._setup_building_controls(geo)

        result_geo = out.geometry()
        return {
            "template_id": "single_building_v1",
            "root_node_path": geo.path(),
            "output_node_path": out.path(),
            "params": {"width": width, "height": height, "depth": depth, "roof_scale": roof_scale, "roof_height": roof_height},
            "poly_count": len(result_geo.prims()) if result_geo else 0,
            "point_count": len(result_geo.points()) if result_geo else 0,
        }

    def _build_template_road_segment_v1(self, parent, node_name: str, overrides: Dict[str, Any]) -> Dict[str, Any]:
        name = self._sanitize_node_name(node_name or "road_segment")
        length = float(overrides.get("length", 30.0))
        width = float(overrides.get("width", 6.0))
        rows = int(overrides.get("rows", 8))
        cols = int(overrides.get("cols", 16))
        curb_height = float(overrides.get("curb_height", 0.15))

        geo = parent.createNode("geo", name)
        for child in geo.children():
            child.destroy()

        road = geo.createNode("grid", "road_grid")
        road.parm("sizex").set(length)
        road.parm("sizey").set(width)
        road.parm("rows").set(max(2, rows))
        road.parm("cols").set(max(2, cols))

        peak = geo.createNode("peak", "road_crown")
        peak.setInput(0, road)
        peak.parm("dist").set(curb_height)

        out = geo.createNode("null", "OUT")
        out.setInput(0, peak)
        out.setDisplayFlag(True)
        out.setRenderFlag(True)
        geo.layoutChildren()
        out.cook(force=True)
        geo.setUserData("mcp_template_id", "road_segment_v1")
        self._setup_road_controls(geo)

        result_geo = out.geometry()
        return {
            "template_id": "road_segment_v1",
            "root_node_path": geo.path(),
            "output_node_path": out.path(),
            "params": {"length": length, "width": width, "rows": rows, "cols": cols, "curb_height": curb_height},
            "poly_count": len(result_geo.prims()) if result_geo else 0,
            "point_count": len(result_geo.points()) if result_geo else 0,
        }

    def _build_template_town_block_v1(self, parent, node_name: str, overrides: Dict[str, Any]) -> Dict[str, Any]:
        name = self._sanitize_node_name(node_name or "town_block")
        block_size = float(overrides.get("block_size", 120.0))
        road_width = float(overrides.get("road_width", 10.0))
        road_mode = int(overrides.get("road_mode", 1))
        road_curve_path = str(overrides.get("road_curve_path", "")).strip()
        building_density = float(overrides.get("building_density", 0.35))
        min_height = float(overrides.get("min_height", 6.0))
        max_height = float(overrides.get("max_height", 24.0))
        min_footprint = float(overrides.get("min_footprint", 2.0))
        max_footprint = float(overrides.get("max_footprint", 6.0))
        seed = int(overrides.get("seed", 0))

        geo = parent.createNode("geo", name)
        for child in geo.children():
            child.destroy()

        ground = geo.createNode("grid", "ground_grid")
        ground.parm("sizex").set(block_size)
        ground.parm("sizey").set(block_size)
        ground.parm("rows").set(32)
        ground.parm("cols").set(32)

        road_x = geo.createNode("grid", "road_strip_x")
        road_x.parm("sizex").set(block_size)
        road_x.parm("sizey").set(road_width)
        road_x.parm("rows").set(2)
        road_x.parm("cols").set(32)

        road_z = geo.createNode("grid", "road_strip_z")
        road_z.parm("sizex").set(road_width)
        road_z.parm("sizey").set(block_size)
        road_z.parm("rows").set(32)
        road_z.parm("cols").set(2)

        road_merge = geo.createNode("merge", "road_merge")
        road_merge.setInput(0, road_x)
        road_merge.setInput(1, road_z)

        road_curve_base = geo.createNode("line", "road_curve_base")
        if road_curve_base.parm("points"):
            road_curve_base.parm("points").set(24)
        if road_curve_base.parm("originx"):
            road_curve_base.parm("originx").set(-0.5)
        if road_curve_base.parm("originy"):
            road_curve_base.parm("originy").set(0.0)
        if road_curve_base.parm("originz"):
            road_curve_base.parm("originz").set(0.0)
        if road_curve_base.parm("distx"):
            road_curve_base.parm("distx").set(1.0)
        if road_curve_base.parm("disty"):
            road_curve_base.parm("disty").set(0.0)
        if road_curve_base.parm("distz"):
            road_curve_base.parm("distz").set(0.0)

        road_curve_shape = geo.createNode("attribwrangle", "road_curve_shape")
        road_curve_shape.setInput(0, road_curve_base)
        road_curve_shape.parm("class").set(2)
        road_curve_shape.parm("snippet").set(
            "float s = relbbox(0, @P).x;\n"
            "float b = ch(\"../block_size\");\n"
            "float amp = b * 0.2;\n"
            "@P.x = (s - 0.5) * b;\n"
            "@P.z = sin(s * M_PI * 2.0) * amp;\n"
            "@P.y = 0.0;\n"
        )

        road_curve_input = geo.createNode("object_merge", "road_curve_input")
        if road_curve_input.parm("objpath1"):
            road_curve_input.parm("objpath1").set(road_curve_path)
        if road_curve_input.parm("xformtype"):
            road_curve_input.parm("xformtype").set(1)

        road_curve_switch = geo.createNode("switch", "road_curve_switch")
        road_curve_switch.setInput(0, road_curve_shape)
        road_curve_switch.setInput(1, road_curve_input)
        if road_curve_switch.parm("input"):
            road_curve_switch.parm("input").setExpression('if(strlen(chs("../road_curve_path"))>0,1,0)')

        road_curve_polywire = geo.createNode("polywire", "road_curve_polywire")
        road_curve_polywire.setInput(0, road_curve_switch)
        if road_curve_polywire.parm("radius"):
            road_curve_polywire.parm("radius").set(road_width * 0.5)

        road_curve_flatten = geo.createNode("attribwrangle", "road_curve_flatten")
        road_curve_flatten.setInput(0, road_curve_polywire)
        road_curve_flatten.parm("class").set(2)
        road_curve_flatten.parm("snippet").set("@P.y = 0.0;")

        road_both_merge = geo.createNode("merge", "road_both_merge")
        road_both_merge.setInput(0, road_merge)
        road_both_merge.setInput(1, road_curve_flatten)

        road_mode_switch = geo.createNode("switch", "road_mode_switch")
        road_mode_switch.setInput(0, road_merge)
        road_mode_switch.setInput(1, road_curve_flatten)
        road_mode_switch.setInput(2, road_both_merge)
        if road_mode_switch.parm("input"):
            road_mode_switch.parm("input").set(max(0, min(road_mode, 2)))

        road_curve_mask_points = geo.createNode("resample", "road_curve_mask_points")
        road_curve_mask_points.setInput(0, road_curve_switch)
        if road_curve_mask_points.parm("length"):
            road_curve_mask_points.parm("length").set(max(0.2, road_width * 0.35))

        building_scatter = geo.createNode("scatter", "building_scatter")
        building_scatter.setInput(0, ground)
        scatter_count = max(1, int(building_density * ((block_size / 10.0) ** 2.0) * 12.0))
        building_scatter.parm("npts").set(scatter_count)
        if building_scatter.parm("seed"):
            building_scatter.parm("seed").set(seed)

        remove_road_points = geo.createNode("attribwrangle", "remove_road_points")
        remove_road_points.setInput(0, building_scatter)
        remove_road_points.setInput(1, road_curve_mask_points)
        remove_road_points.parm("class").set(2)  # point
        remove_road_points.parm("snippet").set(
            "int mode = chi(\"../road_mode\");\n"
            "float rw = ch(\"../road_width\") * 0.6;\n"
            "int kill = 0;\n"
            "if (mode == 0 || mode == 2) {\n"
            "    if (abs(@P.x) < rw || abs(@P.z) < rw) kill = 1;\n"
            "}\n"
            "if ((mode == 1 || mode == 2) && npoints(1) > 0) {\n"
            "    int near = nearpoint(1, @P);\n"
            "    if (near >= 0) {\n"
            "        vector rp = point(1, \"P\", near);\n"
            "        vector2 a = set(@P.x, @P.z);\n"
            "        vector2 b = set(rp.x, rp.z);\n"
            "        if (distance(a, b) < rw) kill = 1;\n"
            "    }\n"
            "}\n"
            "if (kill != 0) {\n"
            "    removepoint(0, @ptnum);\n"
            "}\n"
        )

        building_attrs = geo.createNode("attribwrangle", "building_attrs")
        building_attrs.setInput(0, remove_road_points)
        building_attrs.parm("class").set(2)  # point
        building_attrs.parm("snippet").set(
            'float seedf = ch("../seed");\n'
            'float minf = ch("../min_footprint");\n'
            'float maxf = ch("../max_footprint");\n'
            'float minh = ch("../min_height");\n'
            'float maxh = ch("../max_height");\n'
            "float f = fit01(rand(@ptnum * 19.73 + seedf), minf, maxf);\n"
            "float h = fit01(rand(@ptnum * 53.11 + seedf + 11.3), minh, maxh);\n"
            "v@scale = set(f, h, f);\n"
            "@P.y = h * 0.5;\n"
        )

        building_unit = geo.createNode("box", "building_unit")
        building_unit.parm("sizex").set(1.0)
        building_unit.parm("sizey").set(1.0)
        building_unit.parm("sizez").set(1.0)

        copy_buildings = geo.createNode("copytopoints", "copy_buildings")
        copy_buildings.setInput(0, building_unit)
        copy_buildings.setInput(1, building_attrs)

        town_merge = geo.createNode("merge", "merge_town")
        town_merge.setInput(0, ground)
        town_merge.setInput(1, road_mode_switch)
        town_merge.setInput(2, copy_buildings)

        out = geo.createNode("null", "OUT")
        out.setInput(0, town_merge)
        out.setDisplayFlag(True)
        out.setRenderFlag(True)
        geo.layoutChildren()
        out.cook(force=True)

        geo.setUserData("mcp_template_id", "town_block_v1")
        self._setup_town_controls(geo)

        if geo.parm("block_size"):
            geo.parm("block_size").set(block_size)
        if geo.parm("road_width"):
            geo.parm("road_width").set(road_width)
        if geo.parm("road_mode"):
            geo.parm("road_mode").set(max(0, min(road_mode, 2)))
        if geo.parm("road_curve_path"):
            geo.parm("road_curve_path").set(road_curve_path)
        if geo.parm("building_density"):
            geo.parm("building_density").set(building_density)
        if geo.parm("min_height"):
            geo.parm("min_height").set(min_height)
        if geo.parm("max_height"):
            geo.parm("max_height").set(max_height)
        if geo.parm("min_footprint"):
            geo.parm("min_footprint").set(min_footprint)
        if geo.parm("max_footprint"):
            geo.parm("max_footprint").set(max_footprint)
        if geo.parm("seed"):
            geo.parm("seed").set(seed)

        out.cook(force=True)
        result_geo = out.geometry()
        return {
            "template_id": "town_block_v1",
            "root_node_path": geo.path(),
            "output_node_path": out.path(),
            "params": {
                "block_size": block_size,
                "road_width": road_width,
                "road_mode": max(0, min(road_mode, 2)),
                "road_curve_path": road_curve_path,
                "building_density": building_density,
                "min_height": min_height,
                "max_height": max_height,
                "min_footprint": min_footprint,
                "max_footprint": max_footprint,
                "seed": seed,
            },
            "poly_count": len(result_geo.prims()) if result_geo else 0,
            "point_count": len(result_geo.points()) if result_geo else 0,
        }

    def _build_template_crystal_courtyard_v1(self, parent, node_name: str, overrides: Dict[str, Any]) -> Dict[str, Any]:
        name = self._sanitize_node_name(node_name or "crystal_courtyard")
        water_size = float(overrides.get("water_size", 420.0))
        arch_count = int(overrides.get("arch_count", 16))
        ring_pillar_count = int(overrides.get("ring_pillar_count", 18))
        step_count = int(overrides.get("step_count", 14))
        crystal_scale = float(overrides.get("crystal_scale", 1.0))
        seed = int(overrides.get("seed", 0))

        geo = parent.createNode("geo", name)
        for child in geo.children():
            child.destroy()

        water = geo.createNode("grid", "water_plane")
        water.parm("sizex").set(water_size)
        water.parm("sizey").set(water_size)
        water.parm("rows").set(48)
        water.parm("cols").set(48)

        arch_pts = geo.createNode("line", "arch_points")
        self._set_parm_if_exists(arch_pts, "npts", max(4, arch_count))
        self._set_parm_if_exists(arch_pts, "points", max(4, arch_count))
        arch_shape = geo.createNode("attribwrangle", "arch_shape")
        arch_shape.setInput(0, arch_pts)
        arch_shape.parm("class").set(2)
        arch_shape.parm("snippet").set(
            "float u = float(@ptnum) / max(1.0, float(npoints(0) - 1));\n"
            "float t = (u*2.0 - 1.0);\n"
            "float r = ch(\"../water_size\") * 0.18;\n"
            "float y = (1.0 - t*t) * ch(\"../water_size\") * 0.06;\n"
            "@P = set(t * r, y, -abs(t) * ch(\"../water_size\") * 0.09);\n"
            "v@N = normalize(set(t, 0.0, -1.0));\n"
        )

        arch_crystal = geo.createNode("box", "arch_crystal")
        arch_crystal.parm("sizex").set(max(0.8, water_size * 0.018 * crystal_scale))
        arch_crystal.parm("sizey").set(max(2.0, water_size * 0.13 * crystal_scale))
        arch_crystal.parm("sizez").set(max(0.8, water_size * 0.018 * crystal_scale))
        arch_crystal_fx = geo.createNode("attribwrangle", "arch_crystal_fx")
        arch_crystal_fx.setInput(0, arch_crystal)
        arch_crystal_fx.parm("class").set(2)
        arch_crystal_fx.parm("snippet").set(
            "float s = ch(\"../seed\");\n"
            "float n = rand(@ptnum*7.13+s);\n"
            "@P += normalize(@P + set(0.1,0.0,0.1)) * fit01(n, -0.12, 0.2) * ch(\"../crystal_scale\");\n"
        )

        arch_copy = geo.createNode("copytopoints", "arch_copy")
        arch_copy.setInput(0, arch_crystal_fx)
        arch_copy.setInput(1, arch_shape)

        ring_pts = geo.createNode("circle", "ring_points")
        self._set_parm_if_exists(ring_pts, "type", 1)
        self._set_parm_if_exists(ring_pts, "arc", 360)
        self._set_parm_if_exists(ring_pts, "divs", max(4, ring_pillar_count))
        self._set_parm_if_exists(ring_pts, "numdivs", max(4, ring_pillar_count))
        self._set_parm_if_exists(ring_pts, "radx", water_size * 0.42)
        self._set_parm_if_exists(ring_pts, "rady", water_size * 0.42)

        ring_crystal = geo.createNode("box", "ring_crystal")
        ring_crystal.parm("sizex").set(max(0.8, water_size * 0.015 * crystal_scale))
        ring_crystal.parm("sizey").set(max(2.0, water_size * 0.16 * crystal_scale))
        ring_crystal.parm("sizez").set(max(0.8, water_size * 0.015 * crystal_scale))
        ring_copy = geo.createNode("copytopoints", "ring_copy")
        ring_copy.setInput(0, ring_crystal)
        ring_copy.setInput(1, ring_pts)

        steps_pts = geo.createNode("line", "step_points")
        self._set_parm_if_exists(steps_pts, "npts", max(4, step_count))
        self._set_parm_if_exists(steps_pts, "points", max(4, step_count))
        steps_shape = geo.createNode("attribwrangle", "step_shape")
        steps_shape.setInput(0, steps_pts)
        steps_shape.parm("class").set(2)
        steps_shape.parm("snippet").set(
            "float u = float(@ptnum) / max(1.0, float(npoints(0) - 1));\n"
            "@P = set(0.0, 0.22, fit(u, 0.0, 1.0, ch(\"../water_size\")*0.18, -ch(\"../water_size\")*0.2));\n"
        )
        step_box = geo.createNode("box", "step_box")
        step_box.parm("sizex").set(max(2.0, water_size * 0.11))
        step_box.parm("sizey").set(max(0.25, water_size * 0.004))
        step_box.parm("sizez").set(max(1.0, water_size * 0.03))
        step_copy = geo.createNode("copytopoints", "step_copy")
        step_copy.setInput(0, step_box)
        step_copy.setInput(1, steps_shape)

        center_pts = geo.createNode("sphere", "center_points_src")
        self._set_parm_if_exists(center_pts, "type", 1)
        self._set_parm_if_exists(center_pts, "radx", 3.5)
        self._set_parm_if_exists(center_pts, "rady", 2.2)
        self._set_parm_if_exists(center_pts, "radz", 3.5)
        center_scatter = geo.createNode("scatter", "center_scatter")
        center_scatter.setInput(0, center_pts)
        center_scatter.parm("npts").set(40)
        if center_scatter.parm("seed"):
            center_scatter.parm("seed").set(seed + 31)
        center_shard = geo.createNode("box", "center_shard")
        center_shard.parm("sizex").set(1.6)
        center_shard.parm("sizey").set(3.8)
        center_shard.parm("sizez").set(1.2)
        center_copy = geo.createNode("copytopoints", "center_copy")
        center_copy.setInput(0, center_shard)
        center_copy.setInput(1, center_scatter)

        all_merge = geo.createNode("merge", "merge_scene")
        all_merge.setInput(0, water)
        all_merge.setInput(1, arch_copy)
        all_merge.setInput(2, ring_copy)
        all_merge.setInput(3, step_copy)
        all_merge.setInput(4, center_copy)

        out = geo.createNode("null", "OUT")
        out.setInput(0, all_merge)
        out.setDisplayFlag(True)
        out.setRenderFlag(True)
        geo.layoutChildren()
        out.cook(force=True)

        geo.setUserData("mcp_template_id", "crystal_courtyard_v1")
        self._setup_crystal_controls(geo)
        if geo.parm("water_size"):
            geo.parm("water_size").set(water_size)
        if geo.parm("arch_count"):
            geo.parm("arch_count").set(max(4, arch_count))
        if geo.parm("ring_pillar_count"):
            geo.parm("ring_pillar_count").set(max(4, ring_pillar_count))
        if geo.parm("step_count"):
            geo.parm("step_count").set(max(4, step_count))
        if geo.parm("crystal_scale"):
            geo.parm("crystal_scale").set(crystal_scale)
        if geo.parm("seed"):
            geo.parm("seed").set(seed)
        out.cook(force=True)

        result_geo = out.geometry()
        return {
            "template_id": "crystal_courtyard_v1",
            "root_node_path": geo.path(),
            "output_node_path": out.path(),
            "params": {
                "water_size": water_size,
                "arch_count": max(4, arch_count),
                "ring_pillar_count": max(4, ring_pillar_count),
                "step_count": max(4, step_count),
                "crystal_scale": crystal_scale,
                "seed": seed,
            },
            "poly_count": len(result_geo.prims()) if result_geo else 0,
            "point_count": len(result_geo.points()) if result_geo else 0,
        }

    def _build_template_crystal_courtyard_v2(self, parent, node_name: str, overrides: Dict[str, Any]) -> Dict[str, Any]:
        name = self._sanitize_node_name(node_name or "crystal_courtyard_v2")
        water_size = float(overrides.get("water_size", 520.0))
        arch_count = int(overrides.get("arch_count", 28))
        ring_pillar_count = int(overrides.get("ring_pillar_count", 22))
        step_count = int(overrides.get("step_count", 26))
        crystal_scale = float(overrides.get("crystal_scale", 1.0))
        seed = int(overrides.get("seed", 0))

        geo = parent.createNode("geo", name)
        for child in geo.children():
            child.destroy()

        water = geo.createNode("grid", "water_plane")
        water.parm("sizex").set(water_size)
        water.parm("sizey").set(water_size)
        water.parm("rows").set(140)
        water.parm("cols").set(140)
        water_noise = geo.createNode("mountain", "water_noise")
        water_noise.setInput(0, water)
        self._set_parm_if_exists(water_noise, "height", max(0.01, water_size * 0.0011))
        self._set_parm_if_exists(water_noise, "elementsize", max(0.2, water_size * 0.032))
        water_ripple = geo.createNode("mountain", "water_ripple")
        water_ripple.setInput(0, water_noise)
        self._set_parm_if_exists(water_ripple, "height", max(0.004, water_size * 0.00035))
        self._set_parm_if_exists(water_ripple, "elementsize", max(0.2, water_size * 0.01))
        water_xf = geo.createNode("xform", "water_offset")
        water_xf.setInput(0, water_ripple)
        water_xf.parmTuple("t").set((0.0, -water_size * 0.03, 0.0))

        slab = geo.createNode("box", "arch_crystal")
        slab.parm("sizex").set(max(1.8, water_size * 0.035 * crystal_scale))
        slab.parm("sizey").set(max(7.0, water_size * 0.18 * crystal_scale))
        slab.parm("sizez").set(max(1.2, water_size * 0.024 * crystal_scale))
        slab_subdiv = geo.createNode("subdivide", "arch_subdiv")
        slab_subdiv.setInput(0, slab)
        self._set_parm_if_exists(slab_subdiv, "iterations", 2)
        slab_peak = geo.createNode("peak", "arch_peak")
        slab_peak.setInput(0, slab_subdiv)
        self._set_parm_if_exists(slab_peak, "dist", max(0.02, water_size * 0.0023))
        slab_fx = geo.createNode("attribwrangle", "arch_slab_fx")
        slab_fx.setInput(0, slab_peak)
        slab_fx.parm("class").set(0)
        slab_fx.parm("snippet").set(
            "float r = rand(@ptnum * 17.7 + ch(\"../seed\"));\n"
            "float taper = fit(@P.y, -0.5, 0.5, 0.85, 1.2);\n"
            "@P.x *= taper;\n"
            "@P.z *= taper;\n"
            "@P += normalize(@P + set(0.03, 0.01, 0.05)) * fit01(r, -0.12, 0.16);\n"
        )

        arch_line = geo.createNode("line", "arch_points")
        arch_points_rebuild = geo.createNode("attribwrangle", "arch_points_rebuild")
        arch_points_rebuild.setInput(0, arch_line)
        arch_points_rebuild.parm("class").set(3)
        arch_points_rebuild.parm("snippet").set(
            "int count = max(2, chi(\"../arch_count\"));\n"
            "for (int i = npoints(0)-1; i >= 0; --i) removepoint(0, i);\n"
            "for (int i = 0; i < count; i++) {\n"
            "    float u = (count <= 1) ? 0.0 : float(i) / float(count - 1);\n"
            "    addpoint(0, set(u, 0, 0));\n"
            "}\n"
        )

        left_arch_points = geo.createNode("attribwrangle", "left_arch_points")
        left_arch_points.setInput(0, arch_points_rebuild)
        left_arch_points.parm("class").set(0)
        left_arch_points.parm("snippet").set(
            "float u = float(@ptnum) / max(1.0, float(npoints(0) - 1));\n"
            "float ws = ch(\"../water_size\");\n"
            "float depth = fit(u, 0.0, 1.0, ws*0.36, -ws*0.46);\n"
            "float side = ws * (0.36 - pow(u, 1.22) * 0.19);\n"
            "float lift = ws * (0.05 + pow(sin(u*M_PI), 1.45) * 0.21);\n"
            "float jitter = fit01(rand(@ptnum*13.17 + ch(\"../seed\")), -ws*0.012, ws*0.012);\n"
            "@P = set(-side + jitter, lift, depth + jitter * 0.35);\n"
            "f@pscale = fit01(rand(@ptnum*31.17 + ch(\"../seed\")), 0.82, 1.30) * ch(\"../crystal_scale\");\n"
            "v@N = normalize(set(1.0, 0.0, 0.0));\n"
            "v@up = {0,1,0};\n"
        )
        left_arch_copy = geo.createNode("copytopoints", "left_arch_copy")
        left_arch_copy.setInput(0, slab_fx)
        left_arch_copy.setInput(1, left_arch_points)
        self._set_parm_if_exists(left_arch_copy, "pack", 0)

        right_arch_points = geo.createNode("attribwrangle", "right_arch_points")
        right_arch_points.setInput(0, arch_points_rebuild)
        right_arch_points.parm("class").set(0)
        right_arch_points.parm("snippet").set(
            "float u = float(@ptnum) / max(1.0, float(npoints(0) - 1));\n"
            "float ws = ch(\"../water_size\");\n"
            "float depth = fit(u, 0.0, 1.0, ws*0.36, -ws*0.46);\n"
            "float side = ws * (0.36 - pow(u, 1.22) * 0.19);\n"
            "float lift = ws * (0.05 + pow(sin(u*M_PI), 1.45) * 0.21);\n"
            "float jitter = fit01(rand(@ptnum*19.37 + ch(\"../seed\")), -ws*0.012, ws*0.012);\n"
            "@P = set(side + jitter, lift, depth + jitter * 0.35);\n"
            "f@pscale = fit01(rand(@ptnum*27.07 + ch(\"../seed\")), 0.82, 1.30) * ch(\"../crystal_scale\");\n"
            "v@N = normalize(set(-1.0, 0.0, 0.0));\n"
            "v@up = {0,1,0};\n"
        )
        right_arch_copy = geo.createNode("copytopoints", "right_arch_copy")
        right_arch_copy.setInput(0, slab_fx)
        right_arch_copy.setInput(1, right_arch_points)
        self._set_parm_if_exists(right_arch_copy, "pack", 0)
        arch_copy = geo.createNode("merge", "arch_copy")
        arch_copy.setInput(0, left_arch_copy)
        arch_copy.setInput(1, right_arch_copy)

        ring_pts = geo.createNode("circle", "ring_points")
        self._set_parm_if_exists(ring_pts, "type", 1)
        self._set_parm_if_exists(ring_pts, "arc", 360)
        self._set_parm_if_exists(ring_pts, "divs", max(4, ring_pillar_count))
        self._set_parm_if_exists(ring_pts, "numdivs", max(4, ring_pillar_count))
        self._set_parm_if_exists(ring_pts, "radx", water_size * 0.62)
        self._set_parm_if_exists(ring_pts, "rady", water_size * 0.62)
        ring_pts_fx = geo.createNode("attribwrangle", "ring_points_fx")
        ring_pts_fx.setInput(0, ring_pts)
        ring_pts_fx.parm("class").set(0)
        ring_pts_fx.parm("snippet").set(
            "float ws = ch(\"../water_size\");\n"
            "float ringz = @P.y;\n"
            "float r = rand(@ptnum*7.31 + ch(\"../seed\") + 9.0);\n"
            "@P = set(@P.x, fit01(r, ws*0.01, ws*0.095), ringz * 1.05);\n"
            "@P *= fit01(rand(@ptnum*4.31 + ch(\"../seed\")), 0.95, 1.06);\n"
            "f@pscale = fit01(rand(@ptnum*9.73 + ch(\"../seed\")), 0.75, 1.30) * ch(\"../crystal_scale\");\n"
            "v@N = normalize(set(@P.x, 0.0, @P.z));\n"
            "v@up = {0,1,0};\n"
        )

        ring_crystal = geo.createNode("box", "ring_crystal")
        ring_crystal.parm("sizex").set(max(1.0, water_size * 0.014 * crystal_scale))
        ring_crystal.parm("sizey").set(max(7.0, water_size * 0.21 * crystal_scale))
        ring_crystal.parm("sizez").set(max(1.0, water_size * 0.014 * crystal_scale))
        ring_peak = geo.createNode("peak", "ring_peak")
        ring_peak.setInput(0, ring_crystal)
        self._set_parm_if_exists(ring_peak, "dist", max(0.012, water_size * 0.0018))
        ring_copy = geo.createNode("copytopoints", "ring_copy")
        ring_copy.setInput(0, ring_peak)
        ring_copy.setInput(1, ring_pts_fx)
        self._set_parm_if_exists(ring_copy, "pack", 0)

        step_pts = geo.createNode("line", "step_points")
        step_points_rebuild = geo.createNode("attribwrangle", "step_points_rebuild")
        step_points_rebuild.setInput(0, step_pts)
        step_points_rebuild.parm("class").set(3)
        step_points_rebuild.parm("snippet").set(
            "int count = max(2, chi(\"../step_count\"));\n"
            "for (int i = npoints(0)-1; i >= 0; --i) removepoint(0, i);\n"
            "for (int i = 0; i < count; i++) {\n"
            "    float u = (count <= 1) ? 0.0 : float(i) / float(count - 1);\n"
            "    addpoint(0, set(u, 0, 0));\n"
            "}\n"
        )
        step_shape = geo.createNode("attribwrangle", "step_shape")
        step_shape.setInput(0, step_points_rebuild)
        step_shape.parm("class").set(0)
        step_shape.parm("snippet").set(
            "float u = float(@ptnum) / max(1.0, float(npoints(0) - 1));\n"
            "float ws = ch(\"../water_size\");\n"
            "float stair = floor(u * max(4.0, float(chi(\"../step_count\")))) * ws * 0.0019;\n"
            "float x = sin((u * 1.5 + 0.08) * M_PI) * ws * 0.028;\n"
            "@P = set(x, ws*0.004 + stair, fit(u, 0.0, 1.0, ws*0.34, -ws*0.42));\n"
            "v@N = normalize(set(-x, 0.0, -1.0));\n"
            "v@up = {0,1,0};\n"
        )
        step_box = geo.createNode("box", "step_box")
        step_box.parm("sizex").set(max(7.0, water_size * 0.13))
        step_box.parm("sizey").set(max(0.3, water_size * 0.004))
        step_box.parm("sizez").set(max(2.1, water_size * 0.03))
        step_peak = geo.createNode("peak", "step_peak")
        step_peak.setInput(0, step_box)
        self._set_parm_if_exists(step_peak, "dist", max(0.003, water_size * 0.00045))
        step_copy = geo.createNode("copytopoints", "step_copy")
        step_copy.setInput(0, step_peak)
        step_copy.setInput(1, step_shape)
        self._set_parm_if_exists(step_copy, "pack", 0)

        gate_post_points = geo.createNode("line", "gate_post_points")
        gate_points_rebuild = geo.createNode("attribwrangle", "gate_post_points_rebuild")
        gate_points_rebuild.setInput(0, gate_post_points)
        gate_points_rebuild.parm("class").set(3)
        gate_points_rebuild.parm("snippet").set(
            "for (int i = npoints(0)-1; i >= 0; --i) removepoint(0, i);\n"
            "addpoint(0, set(0,0,0));\n"
            "addpoint(0, set(1,0,0));\n"
        )
        gate_post_points_fx = geo.createNode("attribwrangle", "gate_post_points_fx")
        gate_post_points_fx.setInput(0, gate_points_rebuild)
        gate_post_points_fx.parm("class").set(0)
        gate_post_points_fx.parm("snippet").set(
            "float ws = ch(\"../water_size\");\n"
            "float side = (@ptnum == 0) ? -1.0 : 1.0;\n"
            "@P = set(side * ws * 0.16, ws * 0.14, -ws * 0.47);\n"
            "f@pscale = fit01(rand(@ptnum*3.11 + ch(\"../seed\")), 0.95, 1.06);\n"
        )
        gate_post = geo.createNode("box", "gate_post")
        gate_post.parm("sizex").set(max(2.2, water_size * 0.025))
        gate_post.parm("sizey").set(max(8.5, water_size * 0.28))
        gate_post.parm("sizez").set(max(2.0, water_size * 0.02))
        gate_post_peak = geo.createNode("peak", "gate_post_peak")
        gate_post_peak.setInput(0, gate_post)
        self._set_parm_if_exists(gate_post_peak, "dist", max(0.004, water_size * 0.0008))
        gate_posts_copy = geo.createNode("copytopoints", "gate_posts_copy")
        gate_posts_copy.setInput(0, gate_post_peak)
        gate_posts_copy.setInput(1, gate_post_points_fx)
        self._set_parm_if_exists(gate_posts_copy, "pack", 0)

        gate_lintel = geo.createNode("box", "gate_lintel")
        gate_lintel.parm("sizex").set(max(6.0, water_size * 0.36))
        gate_lintel.parm("sizey").set(max(1.6, water_size * 0.03))
        gate_lintel.parm("sizez").set(max(1.8, water_size * 0.018))
        gate_lintel_xf = geo.createNode("xform", "gate_lintel_xf")
        gate_lintel_xf.setInput(0, gate_lintel)
        gate_lintel_xf.parmTuple("t").set((0.0, water_size * 0.29, -water_size * 0.47))
        gate_structure = geo.createNode("merge", "gate_structure")
        gate_structure.setInput(0, gate_posts_copy)
        gate_structure.setInput(1, gate_lintel_xf)

        burst_src = geo.createNode("sphere", "center_points_src")
        self._set_parm_if_exists(burst_src, "type", 1)
        self._set_parm_if_exists(burst_src, "radx", water_size * 0.03)
        self._set_parm_if_exists(burst_src, "rady", water_size * 0.022)
        self._set_parm_if_exists(burst_src, "radz", water_size * 0.03)
        burst_src_xf = geo.createNode("xform", "center_points_xf")
        burst_src_xf.setInput(0, burst_src)
        burst_src_xf.parmTuple("t").set((0.0, water_size * 0.034, -water_size * 0.2))
        burst_scatter = geo.createNode("scatter", "center_scatter")
        burst_scatter.setInput(0, burst_src_xf)
        burst_scatter.parm("npts").set(24)
        if burst_scatter.parm("seed"):
            burst_scatter.parm("seed").set(seed + 17)
        burst_pts_fx = geo.createNode("attribwrangle", "center_points_fx")
        burst_pts_fx.setInput(0, burst_scatter)
        burst_pts_fx.parm("class").set(0)
        burst_pts_fx.parm("snippet").set(
            "float ws = ch(\"../water_size\");\n"
            "float r = rand(@ptnum*5.71 + ch(\"../seed\") + 77.0);\n"
            "vector dir = normalize(@P + set(0.01,0.02,0.01));\n"
            "@P += dir * fit01(r, 0.0, ws*0.022);\n"
            "f@pscale = fit01(rand(@ptnum*9.19 + ch(\"../seed\")), 0.38, 0.96) * ch(\"../crystal_scale\");\n"
            "v@N = dir;\n"
            "v@up = {0,1,0};\n"
        )
        shard = geo.createNode("box", "center_shard")
        shard.parm("sizex").set(max(0.8, water_size * 0.01))
        shard.parm("sizey").set(max(1.7, water_size * 0.032))
        shard.parm("sizez").set(max(0.7, water_size * 0.009))
        shard_fx = geo.createNode("attribwrangle", "center_shard_fx")
        shard_fx.setInput(0, shard)
        shard_fx.parm("class").set(0)
        shard_fx.parm("snippet").set(
            "float r = rand(@ptnum * 11.3 + ch(\"../seed\") + 33.0);\n"
            "@P += normalize(@P + set(0.2,0.1,0.15)) * fit01(r, -0.08, 0.12);\n"
        )
        burst_copy = geo.createNode("copytopoints", "center_copy")
        burst_copy.setInput(0, shard_fx)
        burst_copy.setInput(1, burst_pts_fx)
        self._set_parm_if_exists(burst_copy, "pack", 0)

        side_cluster_src = geo.createNode("sphere", "side_cluster_src")
        self._set_parm_if_exists(side_cluster_src, "type", 1)
        self._set_parm_if_exists(side_cluster_src, "radx", water_size * 0.09)
        self._set_parm_if_exists(side_cluster_src, "rady", water_size * 0.03)
        self._set_parm_if_exists(side_cluster_src, "radz", water_size * 0.08)
        side_cluster_xf = geo.createNode("xform", "side_cluster_xf")
        side_cluster_xf.setInput(0, side_cluster_src)
        side_cluster_xf.parmTuple("t").set((-water_size * 0.26, water_size * 0.02, -water_size * 0.12))
        side_cluster_scatter = geo.createNode("scatter", "side_cluster_scatter")
        side_cluster_scatter.setInput(0, side_cluster_xf)
        side_cluster_scatter.parm("npts").set(56)
        if side_cluster_scatter.parm("seed"):
            side_cluster_scatter.parm("seed").set(seed + 31)
        side_cluster_pts_fx = geo.createNode("attribwrangle", "side_cluster_pts_fx")
        side_cluster_pts_fx.setInput(0, side_cluster_scatter)
        side_cluster_pts_fx.parm("class").set(0)
        side_cluster_pts_fx.parm("snippet").set(
            "float ws = ch(\"../water_size\");\n"
            "f@pscale = fit01(rand(@ptnum*4.31 + ch(\"../seed\")), 0.45, 1.22) * ch(\"../crystal_scale\");\n"
            "v@N = normalize(@P + set(0.0, ws*0.02, 0.0));\n"
            "v@up = {0,1,0};\n"
        )
        side_cluster_copy_l = geo.createNode("copytopoints", "side_cluster_copy_l")
        side_cluster_copy_l.setInput(0, shard_fx)
        side_cluster_copy_l.setInput(1, side_cluster_pts_fx)
        self._set_parm_if_exists(side_cluster_copy_l, "pack", 0)
        side_cluster_copy_r = geo.createNode("xform", "side_cluster_copy_r")
        side_cluster_copy_r.setInput(0, side_cluster_copy_l)
        side_cluster_copy_r.parmTuple("s").set((-1.0, 1.0, 1.0))
        side_cluster_copy_r.parmTuple("t").set((water_size * 0.52, 0.0, 0.0))
        side_clusters = geo.createNode("merge", "side_clusters")
        side_clusters.setInput(0, side_cluster_copy_l)
        side_clusters.setInput(1, side_cluster_copy_r)

        bg_line = geo.createNode("line", "bg_spire_points")
        bg_points_rebuild = geo.createNode("attribwrangle", "bg_spire_points_rebuild")
        bg_points_rebuild.setInput(0, bg_line)
        bg_points_rebuild.parm("class").set(3)
        bg_points_rebuild.parm("snippet").set(
            "int count = 9;\n"
            "for (int i = npoints(0)-1; i >= 0; --i) removepoint(0, i);\n"
            "for (int i = 0; i < count; i++) {\n"
            "    float u = (count <= 1) ? 0.0 : float(i) / float(count - 1);\n"
            "    addpoint(0, set(u, 0, 0));\n"
            "}\n"
        )
        bg_line_fx = geo.createNode("attribwrangle", "bg_spire_points_fx")
        bg_line_fx.setInput(0, bg_points_rebuild)
        bg_line_fx.parm("class").set(0)
        bg_line_fx.parm("snippet").set(
            "float ws = ch(\"../water_size\");\n"
            "float u = float(@ptnum) / max(1.0, float(npoints(0) - 1));\n"
            "@P = set(fit(u,0,1,-ws*0.34,ws*0.34), ws*0.03, -ws*0.58 + sin(u*6.0)*ws*0.02);\n"
            "f@pscale = fit01(rand(@ptnum*8.1 + ch(\"../seed\")), 0.9, 1.18);\n"
        )
        bg_spire = geo.createNode("box", "bg_spire")
        bg_spire.parm("sizex").set(max(1.8, water_size * 0.016))
        bg_spire.parm("sizey").set(max(9.0, water_size * 0.21))
        bg_spire.parm("sizez").set(max(1.6, water_size * 0.014))
        bg_spire_peak = geo.createNode("peak", "bg_spire_peak")
        bg_spire_peak.setInput(0, bg_spire)
        self._set_parm_if_exists(bg_spire_peak, "dist", max(0.01, water_size * 0.0014))
        bg_spire_copy = geo.createNode("copytopoints", "bg_spire_copy")
        bg_spire_copy.setInput(0, bg_spire_peak)
        bg_spire_copy.setInput(1, bg_line_fx)
        self._set_parm_if_exists(bg_spire_copy, "pack", 0)

        merge_features = geo.createNode("merge", "merge_features")
        merge_features.setInput(0, arch_copy)
        merge_features.setInput(1, ring_copy)
        merge_features.setInput(2, step_copy)
        merge_features.setInput(3, gate_structure)
        merge_features.setInput(4, burst_copy)
        merge_features.setInput(5, side_clusters)
        merge_features.setInput(6, bg_spire_copy)

        out_features = geo.createNode("null", "OUT_FEATURES")
        out_features.setInput(0, merge_features)

        merge = geo.createNode("merge", "merge_scene")
        merge.setInput(0, water_xf)
        merge.setInput(1, merge_features)

        out = geo.createNode("null", "OUT")
        out.setInput(0, merge)
        out.setDisplayFlag(True)
        out.setRenderFlag(True)
        geo.layoutChildren()
        out.cook(force=True)

        geo.setUserData("mcp_template_id", "crystal_courtyard_v2")
        self._setup_crystal_controls(geo)
        if geo.parm("water_size"):
            geo.parm("water_size").set(water_size)
        if geo.parm("arch_count"):
            geo.parm("arch_count").set(max(4, arch_count))
        if geo.parm("ring_pillar_count"):
            geo.parm("ring_pillar_count").set(max(4, ring_pillar_count))
        if geo.parm("step_count"):
            geo.parm("step_count").set(max(4, step_count))
        if geo.parm("crystal_scale"):
            geo.parm("crystal_scale").set(crystal_scale)
        if geo.parm("seed"):
            geo.parm("seed").set(seed)
        out.cook(force=True)
        result_geo = out.geometry()

        return {
            "template_id": "crystal_courtyard_v2",
            "root_node_path": geo.path(),
            "output_node_path": out.path(),
            "params": {
                "water_size": water_size,
                "arch_count": max(4, arch_count),
                "ring_pillar_count": max(4, ring_pillar_count),
                "step_count": max(4, step_count),
                "crystal_scale": crystal_scale,
                "seed": seed,
            },
            "poly_count": len(result_geo.prims()) if result_geo else 0,
            "point_count": len(result_geo.points()) if result_geo else 0,
        }

    def _resolve_display_node(self, node_path: str):
        node = self.hou.node(node_path)
        if not node:
            raise RuntimeError(f"Node '{node_path}' not found")

        if node.type().category().name() == "Object":
            geo_node = node
            display_node = geo_node.displayNode()
            if not display_node:
                raise RuntimeError(f"No display node found in '{node_path}'")
            return geo_node, display_node

        return node.parent(), node

    def _geometry_counts(self, geometry):
        if geometry is None:
            return 0, 0
        return len(geometry.prims()), len(geometry.points())

    def _normalize_attribute_patterns(self, value: Any) -> str:
        if not value:
            return ""
        if isinstance(value, (list, tuple, set)):
            tokens = [str(item).strip() for item in value if str(item).strip()]
        else:
            tokens = [token.strip() for token in str(value).replace(",", " ").split() if token.strip()]
        return " ".join(dict.fromkeys(tokens))

    def _merge_attribute_patterns(self, existing: str, addition: str) -> str:
        merged = [token for token in (existing.split() + addition.split()) if token]
        return " ".join(dict.fromkeys(merged))

    def _set_parm_if_exists(self, node, parm_name: str, value: Any) -> None:
        parm = node.parm(parm_name)
        if parm is not None:
            parm.set(value)

    def _set_menu_parm_if_exists(self, node, parm_name: str, token_or_label: str) -> None:
        parm = node.parm(parm_name)
        if parm is None:
            return
        try:
            items = parm.menuItems()
            labels = parm.menuLabels()
            if token_or_label in items:
                parm.set(token_or_label)
                return
            for i, label in enumerate(labels):
                if token_or_label.lower() in str(label).lower():
                    parm.set(i)
                    return
            # Last fallback: try raw value directly.
            parm.set(token_or_label)
        except Exception:
            pass

    def _set_menu_index_parm_if_exists(self, node, parm_name: str, index: int) -> None:
        parm = node.parm(parm_name)
        if parm is None:
            return
        try:
            items = parm.menuItems()
            if not items:
                parm.set(index)
                return
            clamped = max(0, min(index, len(items) - 1))
            parm.set(items[clamped])
        except Exception:
            pass

    def _sanitize_node_name(self, value: str, uppercase: bool = False) -> str:
        text = re.sub(r"[^0-9A-Za-z_]+", "_", value.strip())
        if not text:
            text = "node"
        if text[0].isdigit():
            text = f"node_{text}"
        return text.upper() if uppercase else text.lower()

    def _sanitize_asset_name(self, value: str) -> str:
        text = self._sanitize_node_name(value, uppercase=False)
        return text if text.startswith("mcp_") else f"mcp_{text}"

    def _extract_object_transform(self, geo_node) -> Dict[str, Any]:
        transform = {}
        for name in ("tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz"):
            parm = geo_node.parm(name)
            transform[name] = parm.eval() if parm else None
        return transform

    def _resolve_nodes_for_asset(self, node_paths: Any):
        if isinstance(node_paths, str):
            node_paths = [part.strip() for part in node_paths.split(",") if part.strip()]

        if node_paths:
            nodes = []
            for path in node_paths:
                node = self.hou.node(path)
                if not node:
                    raise RuntimeError(f"Node '{path}' not found")
                nodes.append(node)
            return nodes

        selected_nodes = list(self.hou.selectedNodes())
        if not selected_nodes:
            raise RuntimeError("No node_paths provided and no nodes are selected")
        return selected_nodes
