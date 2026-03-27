"""Persistent Houdini session backend for stateful SOP operations."""

from __future__ import annotations

import os
import re
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
        if operation == "create_box":
            return self.create_box(params)
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
        if operation == "export_geometry":
            return self.export_geometry(params)

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

    def export_geometry(self, params: Dict[str, Any]) -> Dict[str, Any]:
        geo_path = params["geo_path"]
        output_path = params["output_path"]
        file_type = params.get("file_type", "").lower().strip()

        output_ext = os.path.splitext(output_path)[1].lower()
        if not file_type:
            file_type = output_ext.lstrip(".")
        if file_type != "fbx":
            raise RuntimeError(f"Only fbx export is currently supported, got: {file_type}")

        geo_node, display_node = self._resolve_display_node(geo_path)
        export_node = geo_node.createNode("rop_fbx", "export_fbx1")
        export_node.parm("startnode").set(display_node.path())
        export_node.parm("sopoutput").set(output_path)
        if export_node.parm("vcformat"):
            export_node.parm("vcformat").set(1)
        geo_node.layoutChildren()
        export_node.parm("execute").pressButton()

        if not os.path.exists(output_path):
            raise RuntimeError(f"Export failed, output file not found: {output_path}")

        data = {
            "node_path": export_node.path(),
            "geo_path": display_node.path(),
            "output_path": output_path,
            "file_type": file_type,
            "message": f"Exported geometry to {output_path}",
        }
        return {
            "success": True,
            "message": data["message"],
            "prompt": f"Export completed: {data['message']}",
            "error": None,
            "context": data,
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
