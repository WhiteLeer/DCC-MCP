"""Persistent Substance Designer backend powered by CLI tools."""

from __future__ import annotations

import json
import os
import subprocess
import shutil
import tempfile
import textwrap
from pathlib import Path
from typing import Any, Dict

import numpy as np
from PIL import Image, ImageDraw
from PIL import ImageEnhance, ImageFilter
import psutil


class SubstanceSessionBackend:
    def __init__(self, designer_exe: str | None = None):
        self.designer_exe = self._resolve_designer_exe(designer_exe)
        self.install_dir = Path(self.designer_exe).parent
        self.sbsrender_exe = str(self.install_dir / "sbsrender.exe")
        self.sbscooker_exe = str(self.install_dir / "sbscooker.exe")
        self.blender_exe = self._resolve_blender_exe()
        self.current_project_path = "untitled"

    async def execute(self, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if operation == "get_scene_state":
            return self.get_scene_state()
        if operation == "launch_designer":
            return self.launch_designer(params)
        if operation == "inspect_sbsar":
            return self.inspect_sbsar(params)
        if operation == "render_sbsar":
            return self.render_sbsar(params)
        if operation == "cook_sbs":
            return self.cook_sbs(params)
        if operation == "list_outputs":
            return self.list_outputs(params)
        if operation == "import_texture":
            return self.import_texture(params)
        if operation == "process_texture":
            return self.process_texture(params)
        if operation == "capture_screenshot":
            return self.capture_screenshot(params)
        if operation == "analyze_image_palette":
            return self.analyze_image_palette(params)
        if operation == "harmonize_image_color":
            return self.harmonize_image_color(params)
        if operation == "harmonize_images_batch":
            return self.harmonize_images_batch(params)
        if operation == "extract_model_uv_reference":
            return self.extract_model_uv_reference(params)
        if operation == "paint_heart_on_texture":
            return self.paint_heart_on_texture(params)

        return {"success": False, "error": f"Unknown operation: {operation}", "error_type": "UnknownOperation"}

    def get_scene_state(self) -> Dict[str, Any]:
        process_count = 0
        for proc in psutil.process_iter(["name"]):
            try:
                if "substance 3d designer" in (proc.info["name"] or "").lower():
                    process_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return {
            "success": True,
            "error": None,
            "data": {
                "scene_path": self.current_project_path,
                "node_count": 0,
                "assemblies": [],
                "selection": [],
                "running": True,
                "designer_process_count": process_count,
                "designer_exe": self.designer_exe,
            },
        }

    def launch_designer(self, params: Dict[str, Any]) -> Dict[str, Any]:
        project_path = str(params.get("project_path", "")).strip()
        cmd = [self.designer_exe]
        if project_path:
            cmd.append(project_path)
            self.current_project_path = project_path

        subprocess.Popen(cmd, cwd=str(self.install_dir), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        message = f"Launched Substance Designer{' with project ' + project_path if project_path else ''}"
        return {"success": True, "message": message, "prompt": message, "error": None, "context": {"project_path": project_path or "untitled"}}

    def inspect_sbsar(self, params: Dict[str, Any]) -> Dict[str, Any]:
        input_path = self._require_file(params.get("input_path", ""), ".sbsar")
        cmd = [self.sbsrender_exe, "info", "--input", input_path]
        completed = subprocess.run(cmd, capture_output=True, text=True, check=False, cwd=str(self.install_dir))
        if completed.returncode != 0:
            return {
                "success": False,
                "error": completed.stderr.strip() or completed.stdout.strip() or "sbsrender info failed",
                "error_type": "SubstanceRenderError",
            }

        output_text = completed.stdout.strip()
        message = f"Inspected sbsar: {Path(input_path).name}"
        return {
            "success": True,
            "message": message,
            "prompt": message,
            "error": None,
            "context": {
                "input_path": input_path,
                "raw_output": output_text,
            },
        }

    def render_sbsar(self, params: Dict[str, Any]) -> Dict[str, Any]:
        input_path = self._require_file(params.get("input_path", ""), ".sbsar")
        output_path = str(params.get("output_path", "")).strip()
        if not output_path:
            raise RuntimeError("output_path is required")
        output_format = str(params.get("output_format", "png")).strip()
        graph = str(params.get("graph", "")).strip()
        output_name = str(params.get("output_name", "")).strip()
        preset = str(params.get("preset", "")).strip()
        set_values = params.get("set_values", []) or []

        Path(output_path).mkdir(parents=True, exist_ok=True)
        cmd = [
            self.sbsrender_exe,
            "render",
            "--input",
            input_path,
            "--output-path",
            output_path,
            "--output-format",
            output_format,
            "--no-report",
        ]
        if graph:
            cmd.extend(["--input-graph", graph])
        if output_name:
            cmd.extend(["--output-name", output_name])
        if preset:
            cmd.extend(["--use-preset", preset])
        for entry in set_values:
            cmd.extend(["--set-value", str(entry)])

        completed = subprocess.run(cmd, capture_output=True, text=True, check=False, cwd=str(self.install_dir))
        if completed.returncode != 0:
            return {
                "success": False,
                "error": completed.stderr.strip() or completed.stdout.strip() or "sbsrender render failed",
                "error_type": "SubstanceRenderError",
            }

        files = [str(p) for p in Path(output_path).glob("*.*")]
        message = f"Rendered {Path(input_path).name} to {output_path} ({len(files)} files)"
        return {
            "success": True,
            "message": message,
            "prompt": message,
            "error": None,
            "context": {
                "input_path": input_path,
                "output_path": output_path,
                "output_format": output_format,
                "files": files[:50],
            },
        }

    def cook_sbs(self, params: Dict[str, Any]) -> Dict[str, Any]:
        input_path = self._require_file(params.get("input_path", ""), ".sbs")
        output_path = str(params.get("output_path", "")).strip() or str(Path(input_path).parent)
        output_name = str(params.get("output_name", "{inputName}")).strip()
        Path(output_path).mkdir(parents=True, exist_ok=True)

        cmd = [
            self.sbscooker_exe,
            "--inputs",
            input_path,
            "--output-path",
            output_path,
            "--output-name",
            output_name,
        ]
        completed = subprocess.run(cmd, capture_output=True, text=True, check=False, cwd=str(self.install_dir))
        if completed.returncode != 0:
            return {
                "success": False,
                "error": completed.stderr.strip() or completed.stdout.strip() or "sbscooker failed",
                "error_type": "SubstanceCookError",
            }

        files = [str(p) for p in Path(output_path).glob("*.sbsar")]
        message = f"Cooked {Path(input_path).name} into {len(files)} sbsar file(s)"
        return {
            "success": True,
            "message": message,
            "prompt": message,
            "error": None,
            "context": {
                "input_path": input_path,
                "output_path": output_path,
                "files": files[:50],
            },
        }

    def list_outputs(self, params: Dict[str, Any]) -> Dict[str, Any]:
        output_path = str(params.get("output_path", "")).strip()
        if not output_path:
            raise RuntimeError("output_path is required")
        pattern = str(params.get("pattern", "*.*")).strip() or "*.*"
        base = Path(output_path)
        if not base.exists():
            raise RuntimeError(f"Directory not found: {output_path}")
        files = [str(p) for p in base.glob(pattern)]
        message = f"Found {len(files)} file(s) in {output_path}"
        return {
            "success": True,
            "message": message,
            "prompt": message,
            "error": None,
            "context": {"output_path": output_path, "files": files[:200]},
        }

    def import_texture(self, params: Dict[str, Any]) -> Dict[str, Any]:
        input_path = self._require_existing_file(params.get("input_path", ""))
        output_dir = str(params.get("output_dir", "")).strip() or str(Path(input_path).parent)
        output_name = str(params.get("output_name", "")).strip() or Path(input_path).name
        convert_to = str(params.get("convert_to", "")).strip().lower()
        resize_width = int(params.get("resize_width", 0))
        resize_height = int(params.get("resize_height", 0))
        keep_aspect = bool(params.get("keep_aspect", True))

        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / output_name
        if convert_to:
            out_path = out_path.with_suffix(f".{convert_to.lstrip('.')}")

        image = Image.open(input_path)
        if resize_width > 0 and resize_height > 0:
            if keep_aspect:
                image.thumbnail((resize_width, resize_height), Image.Resampling.LANCZOS)
            else:
                image = image.resize((resize_width, resize_height), Image.Resampling.LANCZOS)

        if not convert_to and (resize_width <= 0 or resize_height <= 0):
            shutil.copy2(input_path, out_path)
        else:
            save_kwargs = {}
            if out_path.suffix.lower() in {".jpg", ".jpeg"}:
                image = image.convert("RGB")
                save_kwargs["quality"] = 95
            image.save(out_path, **save_kwargs)

        data = {
            "input_path": input_path,
            "output_path": str(out_path),
            "size": [int(image.size[0]), int(image.size[1])],
            "mode": image.mode,
            "convert_to": convert_to or out_path.suffix.lstrip("."),
            "message": f"Imported texture to {out_path}",
        }
        return {
            "success": True,
            "message": data["message"],
            "prompt": data["message"],
            "error": None,
            "context": data,
        }

    def process_texture(self, params: Dict[str, Any]) -> Dict[str, Any]:
        input_path = self._require_existing_file(params.get("input_path", ""))
        output_path = str(params.get("output_path", "")).strip()
        if not output_path:
            suffix = str(params.get("output_format", "")).strip().lower()
            src = Path(input_path)
            output_path = str(src.with_name(f"{src.stem}_processed{('.' + suffix) if suffix else src.suffix}"))

        brightness = float(params.get("brightness", 1.0))
        contrast = float(params.get("contrast", 1.0))
        saturation = float(params.get("saturation", 1.0))
        sharpness = float(params.get("sharpness", 1.0))
        blur_radius = max(0.0, float(params.get("blur_radius", 0.0)))
        slope_blur_intensity = max(0.0, float(params.get("slope_blur_intensity", 0.0)))
        slope_blur_samples = max(1, int(params.get("slope_blur_samples", 8)))
        slope_blur_blend = max(0.0, min(1.0, float(params.get("slope_blur_blend", 1.0))))
        resize_width = int(params.get("resize_width", 0))
        resize_height = int(params.get("resize_height", 0))
        keep_aspect = bool(params.get("keep_aspect", True))

        image = Image.open(input_path).convert("RGBA")
        if resize_width > 0 and resize_height > 0:
            if keep_aspect:
                image.thumbnail((resize_width, resize_height), Image.Resampling.LANCZOS)
            else:
                image = image.resize((resize_width, resize_height), Image.Resampling.LANCZOS)

        if abs(brightness - 1.0) > 1e-6:
            image = ImageEnhance.Brightness(image).enhance(brightness)
        if abs(contrast - 1.0) > 1e-6:
            image = ImageEnhance.Contrast(image).enhance(contrast)
        if abs(saturation - 1.0) > 1e-6:
            image = ImageEnhance.Color(image).enhance(saturation)
        if abs(sharpness - 1.0) > 1e-6:
            image = ImageEnhance.Sharpness(image).enhance(sharpness)
        if blur_radius > 0.0:
            image = image.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        if slope_blur_intensity > 0.0:
            image = self._apply_slope_blur(
                image=image,
                intensity_px=slope_blur_intensity,
                samples=slope_blur_samples,
                blend=slope_blur_blend,
            )

        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        save_kwargs = {}
        if out_path.suffix.lower() in {".jpg", ".jpeg"}:
            image = image.convert("RGB")
            save_kwargs["quality"] = 95
        image.save(out_path, **save_kwargs)

        data = {
            "input_path": input_path,
            "output_path": str(out_path),
            "size": [int(image.size[0]), int(image.size[1])],
            "brightness": brightness,
            "contrast": contrast,
            "saturation": saturation,
            "sharpness": sharpness,
            "blur_radius": blur_radius,
            "slope_blur_intensity": slope_blur_intensity,
            "slope_blur_samples": slope_blur_samples,
            "slope_blur_blend": slope_blur_blend,
            "message": f"Processed texture to {out_path}",
        }
        return {
            "success": True,
            "message": data["message"],
            "prompt": data["message"],
            "error": None,
            "context": data,
        }

    def capture_screenshot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        input_path = self._require_existing_file(params.get("input_path", ""))
        output_path = str(params.get("output_path", "")).strip()
        if not output_path:
            src = Path(input_path)
            output_path = str(src.with_name(f"{src.stem}_preview{src.suffix}"))

        compare_path = str(params.get("compare_path", "")).strip()
        label_left = str(params.get("label_left", "Input")).strip() or "Input"
        label_right = str(params.get("label_right", "Compare")).strip() or "Compare"
        max_width = max(128, int(params.get("max_width", 1024)))
        max_height = max(128, int(params.get("max_height", 1024)))

        left = Image.open(input_path).convert("RGBA")
        left.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

        if compare_path:
            right_file = self._require_existing_file(compare_path)
            right = Image.open(right_file).convert("RGBA")
            right.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            w = left.width + right.width + 24
            h = max(left.height, right.height) + 56
            canvas = Image.new("RGBA", (w, h), (24, 24, 24, 255))
            canvas.paste(left, (8, 40))
            canvas.paste(right, (left.width + 16, 40))
            draw = ImageDraw.Draw(canvas)
            draw.text((12, 12), label_left, fill=(220, 220, 220, 255))
            draw.text((left.width + 20, 12), label_right, fill=(220, 220, 220, 255))
            out = canvas
        else:
            out = left

        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out.save(out_path)

        data = {
            "input_path": input_path,
            "compare_path": compare_path,
            "output_path": str(out_path),
            "size": [out.width, out.height],
            "message": f"Captured Substance preview: {out_path.name}",
        }
        return {
            "success": True,
            "message": data["message"],
            "prompt": data["message"],
            "error": None,
            "context": data,
        }

    def _apply_slope_blur(self, image: Image.Image, intensity_px: float, samples: int, blend: float) -> Image.Image:
        arr = np.asarray(image.convert("RGBA"), dtype=np.float32) / 255.0
        h, w, _ = arr.shape
        if h < 2 or w < 2:
            return image

        gray = 0.2126 * arr[:, :, 0] + 0.7152 * arr[:, :, 1] + 0.0722 * arr[:, :, 2]
        gy, gx = np.gradient(gray)
        mag = np.sqrt(gx * gx + gy * gy) + 1e-8
        gx = gx / mag
        gy = gy / mag

        ys, xs = np.indices((h, w), dtype=np.float32)
        acc = arr.copy()
        for i in range(1, samples + 1):
            step = (i / samples) * intensity_px
            sample_x = np.clip(np.round(xs + gx * step), 0, w - 1).astype(np.int32)
            sample_y = np.clip(np.round(ys + gy * step), 0, h - 1).astype(np.int32)
            acc += arr[sample_y, sample_x]

        blurred = np.clip(acc / (samples + 1), 0.0, 1.0)
        out = arr * (1.0 - blend) + blurred * blend
        out = np.clip(out * 255.0, 0, 255).astype(np.uint8)
        return Image.fromarray(out, mode="RGBA")

    def analyze_image_palette(self, params: Dict[str, Any]) -> Dict[str, Any]:
        input_path = self._require_existing_file(params.get("input_path", ""))
        top_k = max(1, int(params.get("top_k", 8)))

        rgb_image = Image.open(input_path).convert("RGB")
        rgb_arr = np.asarray(rgb_image, dtype=np.uint8)
        lab_arr = np.asarray(rgb_image.convert("LAB"), dtype=np.uint8)

        rgb_mean = rgb_arr.reshape(-1, 3).mean(axis=0)
        rgb_std = rgb_arr.reshape(-1, 3).std(axis=0)
        lab_mean = lab_arr.reshape(-1, 3).mean(axis=0)
        lab_std = lab_arr.reshape(-1, 3).std(axis=0)

        dominant = self._dominant_colors(rgb_arr, top_k=top_k)
        message = f"Analyzed palette for {Path(input_path).name}"
        return {
            "success": True,
            "message": message,
            "prompt": message,
            "error": None,
            "context": {
                "input_path": input_path,
                "size": [rgb_arr.shape[1], rgb_arr.shape[0]],
                "rgb_mean": [float(x) for x in rgb_mean],
                "rgb_std": [float(x) for x in rgb_std],
                "lab_mean": [float(x) for x in lab_mean],
                "lab_std": [float(x) for x in lab_std],
                "dominant_colors": dominant,
            },
        }

    def harmonize_image_color(self, params: Dict[str, Any]) -> Dict[str, Any]:
        reference_path = self._require_existing_file(params.get("reference_path", ""))
        target_path = self._require_existing_file(params.get("target_path", ""))
        output_path = str(params.get("output_path", "")).strip()
        if not output_path:
            raise RuntimeError("output_path is required")

        intensity = float(params.get("intensity", 1.0))
        intensity = max(0.0, min(1.0, intensity))
        preserve_luminance = float(params.get("preserve_luminance", 0.6))
        preserve_luminance = max(0.0, min(1.0, preserve_luminance))

        ref_rgb = Image.open(reference_path).convert("RGB")
        tgt_rgb = Image.open(target_path).convert("RGB")
        ref_lab = np.asarray(ref_rgb.convert("LAB"), dtype=np.float32)
        tgt_lab = np.asarray(tgt_rgb.convert("LAB"), dtype=np.float32)

        ref_stats = self._channel_stats(ref_lab)
        tgt_stats = self._channel_stats(tgt_lab)
        matched_lab = self._reinhard_match(tgt_lab, ref_stats, tgt_stats)

        # Preserve original lightness structure to avoid flattening details.
        matched_lab[:, :, 0] = (
            tgt_lab[:, :, 0] * preserve_luminance + matched_lab[:, :, 0] * (1.0 - preserve_luminance)
        )
        final_lab = tgt_lab * (1.0 - intensity) + matched_lab * intensity
        final_lab = np.clip(final_lab, 0, 255).astype(np.uint8)

        out_image = Image.fromarray(final_lab, mode="LAB").convert("RGB")
        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_image.save(out_path)

        out_lab = np.asarray(out_image.convert("LAB"), dtype=np.float32)
        delta_before = self._mean_color_distance(tgt_stats["mean"], ref_stats["mean"])
        delta_after = self._mean_color_distance(out_lab.reshape(-1, 3).mean(axis=0), ref_stats["mean"])
        message = f"Harmonized {Path(target_path).name} to match {Path(reference_path).name}"
        return {
            "success": True,
            "message": message,
            "prompt": message,
            "error": None,
            "context": {
                "reference_path": reference_path,
                "target_path": target_path,
                "output_path": str(out_path),
                "intensity": intensity,
                "preserve_luminance": preserve_luminance,
                "lab_distance_before": float(delta_before),
                "lab_distance_after": float(delta_after),
            },
        }

    def harmonize_images_batch(self, params: Dict[str, Any]) -> Dict[str, Any]:
        reference_path = self._require_existing_file(params.get("reference_path", ""))
        input_dir = str(params.get("input_dir", "")).strip()
        output_dir = str(params.get("output_dir", "")).strip()
        pattern = str(params.get("pattern", "*.png")).strip() or "*.png"
        if not input_dir or not output_dir:
            raise RuntimeError("input_dir and output_dir are required")

        intensity = float(params.get("intensity", 1.0))
        preserve_luminance = float(params.get("preserve_luminance", 0.6))

        in_dir = Path(input_dir)
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        targets = [p for p in sorted(in_dir.glob(pattern)) if p.is_file()]
        outputs = []
        for target in targets:
            if target.resolve() == Path(reference_path).resolve():
                continue
            out_file = out_dir / target.name
            result = self.harmonize_image_color(
                {
                    "reference_path": reference_path,
                    "target_path": str(target),
                    "output_path": str(out_file),
                    "intensity": intensity,
                    "preserve_luminance": preserve_luminance,
                }
            )
            if result.get("success"):
                outputs.append(str(out_file))

        message = f"Harmonized {len(outputs)} image(s) using {Path(reference_path).name}"
        return {
            "success": True,
            "message": message,
            "prompt": message,
            "error": None,
            "context": {
                "reference_path": reference_path,
                "input_dir": input_dir,
                "output_dir": output_dir,
                "outputs": outputs,
            },
        }

    def extract_model_uv_reference(self, params: Dict[str, Any]) -> Dict[str, Any]:
        input_model_path = self._require_existing_file(params.get("input_model_path", ""))
        output_dir = str(params.get("output_dir", "")).strip()
        if not output_dir:
            output_dir = str(Path(input_model_path).with_suffix("")) + "_uv"
        image_size = max(256, int(params.get("image_size", 2048)))
        material_filter = str(params.get("material_filter", "")).strip()

        blender_data = self._inspect_fbx_uv(input_model_path, material_filter=material_filter)
        materials = blender_data.get("materials", [])
        out_root = Path(output_dir)
        out_root.mkdir(parents=True, exist_ok=True)

        material_outputs: list[dict[str, Any]] = []
        for mat in materials:
            mat_name = str(mat.get("name", "material"))
            safe_name = self._safe_filename(mat_name)
            img = Image.new("RGBA", (image_size, image_size), (255, 255, 255, 0))
            draw = ImageDraw.Draw(img, "RGBA")
            for poly in mat.get("polygons", []):
                pts = []
                for uv in poly:
                    u = float(uv[0])
                    v = float(uv[1])
                    x = int(round(u * (image_size - 1)))
                    y = int(round((1.0 - v) * (image_size - 1)))
                    pts.append((x, y))
                if len(pts) >= 2:
                    draw.line(pts + [pts[0]], fill=(255, 64, 64, 230), width=1)

            out_file = out_root / f"{safe_name}_uv.png"
            img.save(out_file)
            bounds = self._compute_uv_bounds(mat.get("polygons", []))
            material_outputs.append(
                {
                    "name": mat_name,
                    "polygon_count": int(mat.get("polygon_count", 0)),
                    "uv_bounds": bounds,
                    "uv_layout_path": str(out_file),
                }
            )

        json_path = out_root / "uv_reference.json"
        json_path.write_text(
            json.dumps(
                {
                    "input_model_path": input_model_path,
                    "image_size": image_size,
                    "material_filter": material_filter,
                    "materials": material_outputs,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        message = f"Extracted UV reference for {Path(input_model_path).name} ({len(material_outputs)} materials)"
        return {
            "success": True,
            "message": message,
            "prompt": message,
            "error": None,
            "context": {
                "input_model_path": input_model_path,
                "output_dir": str(out_root),
                "image_size": image_size,
                "material_filter": material_filter,
                "materials": material_outputs,
                "json_path": str(json_path),
            },
        }

    def paint_heart_on_texture(self, params: Dict[str, Any]) -> Dict[str, Any]:
        input_path = self._require_existing_file(params.get("input_path", ""))
        output_path = str(params.get("output_path", "")).strip()
        if not output_path:
            src = Path(input_path)
            output_path = str(src.with_name(f"{src.stem}_heart{src.suffix}"))

        center_uv = params.get("center_uv", [0.5, 0.5]) or [0.5, 0.5]
        if len(center_uv) != 2:
            raise RuntimeError("center_uv must be [u, v]")
        center_u = max(0.0, min(1.0, float(center_uv[0])))
        center_v = max(0.0, min(1.0, float(center_uv[1])))

        size_uv = max(0.005, min(1.0, float(params.get("size_uv", 0.08))))
        softness = max(0.0, min(1.0, float(params.get("softness", 0.35))))
        opacity = max(0.0, min(1.0, float(params.get("opacity", 0.88))))
        color = params.get("color_rgba", [255, 120, 180, 255]) or [255, 120, 180, 255]
        if len(color) != 4:
            raise RuntimeError("color_rgba must be [r, g, b, a]")

        image = Image.open(input_path).convert("RGBA")
        width, height = image.size
        cx = float(center_u * (width - 1))
        cy = float((1.0 - center_v) * (height - 1))
        radius = float(size_uv * min(width, height))

        xs = np.arange(width, dtype=np.float32)[None, :]
        ys = np.arange(height, dtype=np.float32)[:, None]
        x = (xs - cx) / max(radius, 1e-4)
        y = (ys - cy) / max(radius, 1e-4)

        # Implicit heart curve: (x^2 + y^2 - 1)^3 - x^2*y^3 <= 0
        eq = (x * x + y * y - 1.0) ** 3 - (x * x * y * y * y)
        inside = np.clip(-eq * 7.0, 0.0, 1.0)
        edge_pow = max(0.2, 2.5 - softness * 2.0)
        alpha_mask = np.power(inside, edge_pow) * opacity * (float(color[3]) / 255.0)

        base = np.asarray(image, dtype=np.float32) / 255.0
        heart_rgb = np.array([float(color[0]), float(color[1]), float(color[2])], dtype=np.float32) / 255.0
        alpha = alpha_mask[:, :, None]
        out_rgb = base[:, :, :3] * (1.0 - alpha) + heart_rgb[None, None, :] * alpha
        out_a = np.clip(base[:, :, 3:4], 0.0, 1.0)
        out = np.concatenate([np.clip(out_rgb, 0.0, 1.0), out_a], axis=2)
        out_img = Image.fromarray((out * 255.0).astype(np.uint8), mode="RGBA")

        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        if out_file.suffix.lower() in {".jpg", ".jpeg"}:
            out_img.convert("RGB").save(out_file, quality=95)
        else:
            out_img.save(out_file)

        message = f"Painted heart on texture: {out_file.name}"
        return {
            "success": True,
            "message": message,
            "prompt": message,
            "error": None,
            "context": {
                "input_path": input_path,
                "output_path": str(out_file),
                "center_uv": [center_u, center_v],
                "size_uv": size_uv,
                "softness": softness,
                "opacity": opacity,
                "color_rgba": [int(color[0]), int(color[1]), int(color[2]), int(color[3])],
                "texture_size": [width, height],
            },
        }

    def _resolve_designer_exe(self, designer_exe: str | None) -> str:
        candidates = [
            designer_exe,
            os.environ.get("SUBSTANCE_DESIGNER_EXE"),
            r"D:\常用软件\Substance 3D Designer\Adobe Substance 3D Designer.exe",
        ]
        for candidate in candidates:
            if candidate and Path(candidate).exists():
                return str(Path(candidate))
        raise RuntimeError("Substance Designer executable not found")

    def _resolve_blender_exe(self) -> str:
        candidates = [
            os.environ.get("BLENDER_EXE"),
            r"D:\常用软件\Blender 4.2\blender.exe",
            shutil.which("blender"),
        ]
        for candidate in candidates:
            if candidate and Path(candidate).exists():
                return str(Path(candidate))
        return ""

    def _require_file(self, path_value: str, ext: str) -> str:
        path = str(path_value).strip()
        if not path:
            raise RuntimeError("input_path is required")
        file_path = Path(path)
        if not file_path.exists():
            raise RuntimeError(f"File not found: {path}")
        if ext and file_path.suffix.lower() != ext:
            raise RuntimeError(f"Expected {ext} file, got: {file_path.suffix}")
        return str(file_path)

    def _require_existing_file(self, path_value: str) -> str:
        path = str(path_value).strip()
        if not path:
            raise RuntimeError("path is required")
        file_path = Path(path)
        if not file_path.exists():
            raise RuntimeError(f"File not found: {path}")
        return str(file_path)

    def _inspect_fbx_uv(self, input_model_path: str, material_filter: str = "") -> Dict[str, Any]:
        if not self.blender_exe:
            raise RuntimeError("Blender executable not configured, cannot inspect FBX UV")
        model_suffix = Path(input_model_path).suffix.lower()
        if model_suffix not in {".fbx", ".obj", ".gltf", ".glb"}:
            raise RuntimeError(f"Unsupported model format for UV inspect: {model_suffix}")

        if model_suffix == ".fbx":
            import_stmt = f"bpy.ops.import_scene.fbx(filepath=r'''{input_model_path}''')"
        elif model_suffix == ".obj":
            import_stmt = f"bpy.ops.wm.obj_import(filepath=r'''{input_model_path}''')"
        else:
            import_stmt = f"bpy.ops.import_scene.gltf(filepath=r'''{input_model_path}''')"

        with tempfile.TemporaryDirectory(prefix="substance_uv_probe_") as tmpdir:
            tmp_path = Path(tmpdir)
            out_json = tmp_path / "uv_data.json"
            script_file = tmp_path / "probe.py"
            script_body = f"""
import bpy
import json
from pathlib import Path

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
{import_stmt}

material_filter = r'''{material_filter}'''.strip().lower()
mat_polys = {{}}
mat_counts = {{}}

for obj in bpy.data.objects:
    if obj.type != 'MESH' or obj.data is None:
        continue
    mesh = obj.data
    if not mesh.uv_layers:
        continue
    uv_layer = mesh.uv_layers.active.data
    mats = mesh.materials
    for poly in mesh.polygons:
        mat_idx = poly.material_index
        mat_name = mats[mat_idx].name if mats and mat_idx < len(mats) and mats[mat_idx] else f"Material_{{mat_idx}}"
        if material_filter and material_filter not in mat_name.lower():
            continue
        loops = []
        for li in poly.loop_indices:
            uv = uv_layer[li].uv
            loops.append([float(uv.x), float(uv.y)])
        if len(loops) >= 3:
            mat_polys.setdefault(mat_name, []).append(loops)
            mat_counts[mat_name] = mat_counts.get(mat_name, 0) + 1

materials = []
for name, polys in mat_polys.items():
    materials.append({{
        "name": name,
        "polygon_count": int(mat_counts.get(name, len(polys))),
        "polygons": polys,
    }})

Path(r'''{str(out_json)}''').write_text(json.dumps({{"materials": materials}}, ensure_ascii=False), encoding="utf-8")
"""
            script_file.write_text(textwrap.dedent(script_body), encoding="utf-8")
            proc = subprocess.run(
                [self.blender_exe, "--background", "--factory-startup", "--python", str(script_file)],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=180,
            )
            if proc.returncode != 0:
                err = (proc.stderr or proc.stdout or "").strip()
                raise RuntimeError(f"Blender UV probe failed: {err[-800:] if len(err) > 800 else err}")
            if not out_json.exists():
                raise RuntimeError("Blender UV probe did not produce output")
            return json.loads(out_json.read_text(encoding="utf-8"))

    def _compute_uv_bounds(self, polygons: list[Any]) -> list[float]:
        u_values: list[float] = []
        v_values: list[float] = []
        for poly in polygons:
            for uv in poly:
                try:
                    u_values.append(float(uv[0]))
                    v_values.append(float(uv[1]))
                except Exception:
                    continue
        if not u_values or not v_values:
            return [0.0, 0.0, 1.0, 1.0]
        return [float(min(u_values)), float(min(v_values)), float(max(u_values)), float(max(v_values))]

    def _safe_filename(self, name: str) -> str:
        cleaned = "".join(ch if ch.isalnum() or ch in {"_", "-", "."} else "_" for ch in str(name))
        cleaned = cleaned.strip("._")
        return cleaned or "material"

    def _channel_stats(self, arr: np.ndarray) -> Dict[str, np.ndarray]:
        flat = arr.reshape(-1, 3)
        return {"mean": flat.mean(axis=0), "std": flat.std(axis=0)}

    def _reinhard_match(self, target_lab: np.ndarray, ref_stats: Dict[str, np.ndarray], tgt_stats: Dict[str, np.ndarray]) -> np.ndarray:
        eps = 1e-5
        result = np.empty_like(target_lab)
        for c in range(3):
            t_mean = tgt_stats["mean"][c]
            t_std = max(float(tgt_stats["std"][c]), eps)
            r_mean = ref_stats["mean"][c]
            r_std = max(float(ref_stats["std"][c]), eps)
            result[:, :, c] = ((target_lab[:, :, c] - t_mean) * (r_std / t_std)) + r_mean
        return result

    def _dominant_colors(self, rgb_arr: np.ndarray, top_k: int = 8) -> list[Dict[str, Any]]:
        # Quantize to 16 levels/channel for robust dominant color extraction.
        q = (rgb_arr // 16).reshape(-1, 3)
        packed = (q[:, 0].astype(np.int32) << 8) + (q[:, 1].astype(np.int32) << 4) + q[:, 2].astype(np.int32)
        uniq, counts = np.unique(packed, return_counts=True)
        order = np.argsort(counts)[::-1][:top_k]
        total = counts.sum()
        colors = []
        for idx in order:
            code = int(uniq[idx])
            r = ((code >> 8) & 0xF) * 16 + 8
            g = ((code >> 4) & 0xF) * 16 + 8
            b = (code & 0xF) * 16 + 8
            colors.append(
                {
                    "rgb": [int(r), int(g), int(b)],
                    "ratio": float(counts[idx] / total),
                }
            )
        return colors

    def _mean_color_distance(self, a: np.ndarray, b: np.ndarray) -> float:
        return float(np.linalg.norm(np.asarray(a, dtype=np.float32) - np.asarray(b, dtype=np.float32)))
