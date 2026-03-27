"""Shared pipeline orchestration helpers for DCC MCP bridges."""

from __future__ import annotations

import asyncio
import hashlib
import json
import shutil
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Awaitable, Callable

InvokeOperation = Callable[[str, dict[str, Any]], Awaitable[dict[str, Any]]]


class PipelineOrchestrator:
    """In-memory orchestration layer for batch/workflow and publish tracking."""

    def __init__(self, dcc_name: str, invoke_operation: InvokeOperation):
        self.dcc_name = dcc_name
        self.invoke_operation = invoke_operation
        self._jobs: dict[str, dict[str, Any]] = {}
        self._job_order: list[str] = []
        self._lock = asyncio.Lock()

    async def workflow_run(
        self,
        steps: list[dict[str, Any]],
        stop_on_error: bool = True,
        workflow_name: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return await self._run_job(
            job_kind="workflow",
            steps=steps,
            stop_on_error=stop_on_error,
            workflow_name=workflow_name or "workflow",
            metadata=metadata or {},
        )

    async def batch_run(
        self,
        operations: list[dict[str, Any]],
        continue_on_error: bool = True,
        batch_name: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return await self._run_job(
            job_kind="batch",
            steps=operations,
            stop_on_error=not continue_on_error,
            workflow_name=batch_name or "batch",
            metadata=metadata or {},
        )

    async def get_job_status(self, job_id: str = "", include_steps: bool = True) -> dict[str, Any]:
        async with self._lock:
            if job_id:
                job = self._jobs.get(job_id)
                if not job:
                    return {"success": False, "error": f"job_id not found: {job_id}", "error_type": "JobNotFound"}
                return {"success": True, "job": self._clone_job(job, include_steps=include_steps)}

            latest = [self._clone_job(self._jobs[jid], include_steps=False) for jid in self._job_order[-20:]]
            return {
                "success": True,
                "jobs": latest,
                "total_jobs": len(self._jobs),
            }

    async def validate_asset(
        self,
        path: str,
        expected_types: list[str] | None = None,
        required_tokens: list[str] | None = None,
        min_size_bytes: int = 1,
    ) -> dict[str, Any]:
        asset_path = Path(path)
        expected_types = [x.lower() for x in (expected_types or [])]
        required_tokens = required_tokens or []

        issues: list[str] = []
        warnings: list[str] = []
        checks: dict[str, Any] = {
            "exists": asset_path.exists(),
            "is_file": asset_path.is_file(),
            "path": str(asset_path),
        }

        if not asset_path.exists():
            issues.append("file_not_found")
            return {
                "success": False,
                "path": str(asset_path),
                "checks": checks,
                "issues": issues,
                "warnings": warnings,
                "error": f"Asset not found: {asset_path}",
                "error_type": "AssetNotFound",
            }

        if not asset_path.is_file():
            issues.append("path_is_not_file")

        file_size = asset_path.stat().st_size
        checks["size_bytes"] = file_size
        checks["extension"] = asset_path.suffix.lower()
        checks["name"] = asset_path.name

        if file_size < max(0, min_size_bytes):
            issues.append(f"file_too_small<{min_size_bytes}")

        if expected_types and asset_path.suffix.lower() not in expected_types:
            issues.append(f"unexpected_extension:{asset_path.suffix.lower()}")

        stem_lower = asset_path.stem.lower()
        for token in required_tokens:
            if token.lower() not in stem_lower:
                warnings.append(f"missing_token:{token}")

        # Practical naming hygiene for DCC handoff.
        if " " in asset_path.name:
            warnings.append("filename_contains_space")
        if len(asset_path.name) > 96:
            warnings.append("filename_too_long")

        return {
            "success": len(issues) == 0,
            "path": str(asset_path),
            "checks": checks,
            "issues": issues,
            "warnings": warnings,
            "summary": {
                "issue_count": len(issues),
                "warning_count": len(warnings),
            },
        }

    async def publish_asset(
        self,
        input_path: str,
        publish_dir: str,
        asset_name: str = "",
        version: str = "",
        write_manifest: bool = True,
    ) -> dict[str, Any]:
        source = Path(input_path)
        if not source.exists() or not source.is_file():
            return {
                "success": False,
                "error": f"Source asset not found: {input_path}",
                "error_type": "AssetNotFound",
            }

        target_dir = Path(publish_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        safe_stem = (asset_name or source.stem).strip() or source.stem
        suffix = source.suffix
        version_tag = f"_v{version.strip()}" if version.strip() else ""
        target = target_dir / f"{safe_stem}{version_tag}{suffix}"

        if target.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            target = target_dir / f"{safe_stem}{version_tag}_{timestamp}{suffix}"

        shutil.copy2(source, target)
        sha256 = _sha256_file(target)

        manifest_path = None
        manifest = {
            "dcc": self.dcc_name,
            "published_at": datetime.now().isoformat(),
            "source_path": str(source),
            "target_path": str(target),
            "version": version,
            "size_bytes": target.stat().st_size,
            "sha256": sha256,
        }
        if write_manifest:
            manifest_path = target.with_suffix(target.suffix + ".manifest.json")
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

        return {
            "success": True,
            "message": f"Published asset to {target}",
            "context": {
                "source_path": str(source),
                "target_path": str(target),
                "manifest_path": str(manifest_path) if manifest_path else "",
                "sha256": sha256,
                "size_bytes": target.stat().st_size,
                "version": version,
            },
        }

    async def _run_job(
        self,
        job_kind: str,
        steps: list[dict[str, Any]],
        stop_on_error: bool,
        workflow_name: str,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        job_id = f"{self.dcc_name}_{job_kind}_{uuid.uuid4().hex[:12]}"
        started_at = datetime.now().isoformat()
        started_ts = time.time()
        normalized_steps = [self._normalize_step(step, idx) for idx, step in enumerate(steps or [])]

        job: dict[str, Any] = {
            "job_id": job_id,
            "dcc": self.dcc_name,
            "kind": job_kind,
            "name": workflow_name,
            "status": "running",
            "stop_on_error": stop_on_error,
            "metadata": metadata,
            "started_at": started_at,
            "finished_at": "",
            "duration_seconds": 0.0,
            "steps_total": len(normalized_steps),
            "steps_completed": 0,
            "results": [],
            "error": "",
        }
        await self._save_job(job)

        for step in normalized_steps:
            step_start = time.time()
            op = step["operation"]
            params = step["params"]
            result = await self.invoke_operation(op, params)
            ok = bool(result.get("success"))
            item = {
                "index": step["index"],
                "name": step["name"],
                "operation": op,
                "params": params,
                "success": ok,
                "duration_seconds": round(time.time() - step_start, 4),
                "result": result,
            }
            job["results"].append(item)
            job["steps_completed"] += 1
            if not ok and stop_on_error:
                job["status"] = "failed"
                job["error"] = result.get("error", f"Step failed: {op}")
                break

        if job["status"] == "running":
            job["status"] = "success"

        job["finished_at"] = datetime.now().isoformat()
        job["duration_seconds"] = round(time.time() - started_ts, 4)
        await self._save_job(job)

        return {
            "success": job["status"] == "success",
            "job_id": job_id,
            "status": job["status"],
            "summary": {
                "steps_total": job["steps_total"],
                "steps_completed": job["steps_completed"],
                "failed_steps": len([r for r in job["results"] if not r["success"]]),
                "duration_seconds": job["duration_seconds"],
            },
            "results": job["results"],
            "error": job["error"] or None,
        }

    async def _save_job(self, job: dict[str, Any]) -> None:
        async with self._lock:
            self._jobs[job["job_id"]] = job
            if job["job_id"] not in self._job_order:
                self._job_order.append(job["job_id"])
            # Keep bounded memory.
            while len(self._job_order) > 500:
                old_id = self._job_order.pop(0)
                self._jobs.pop(old_id, None)

    def _normalize_step(self, step: dict[str, Any], idx: int) -> dict[str, Any]:
        if not isinstance(step, dict):
            raise RuntimeError(f"Step at index {idx} must be an object")
        operation = str(step.get("operation", "")).strip()
        if not operation:
            raise RuntimeError(f"Step at index {idx} missing operation")
        params = step.get("params", {}) or {}
        if not isinstance(params, dict):
            raise RuntimeError(f"Step params at index {idx} must be an object")
        return {
            "index": idx,
            "name": str(step.get("name", f"step_{idx + 1}")),
            "operation": operation,
            "params": params,
        }

    def _clone_job(self, job: dict[str, Any], include_steps: bool) -> dict[str, Any]:
        cloned = dict(job)
        if not include_steps:
            cloned.pop("results", None)
        return cloned


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()
