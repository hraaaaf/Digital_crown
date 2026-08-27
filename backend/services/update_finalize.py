from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from backend.core.platform import get_platform_adapter
from backend.services.update_engine import UpdateEngine, UpdatePreparationError


FINALIZE_REPORT_NAME = "update-finalize-report.json"
WINDOWS_WORKER_CONTRACT = "windows-inno-v1"


class UpdateFinalizeService:
    """Commit an already health-verified packaged update into canonical trust state."""

    @staticmethod
    def _bundle_root() -> Path:
        frozen_root = getattr(sys, "_MEIPASS", None)
        if frozen_root:
            return Path(str(frozen_root)).resolve()
        return Path(__file__).resolve().parents[2]

    @classmethod
    def _current_version(cls) -> str:
        path = cls._bundle_root() / "VERSION"
        if not path.is_file():
            raise UpdatePreparationError("UPDATE_FINALIZE_VERSION_MISSING")
        value = path.read_text(encoding="utf-8").strip()
        parts = value.split(".")
        if len(parts) != 3 or any(not part.isdigit() for part in parts):
            raise UpdatePreparationError("UPDATE_FINALIZE_VERSION_INVALID")
        return value

    @classmethod
    def _validate_job(
        cls,
        job: dict[str, Any],
        *,
        current_version: str,
        platform_kind: str,
    ) -> None:
        required_truth = (
            int(job.get("schema") or 0) == 1,
            str(job.get("status") or "") == "health_pending",
            job.get("apply_certified") is True,
            str(job.get("platform") or "").lower() == platform_kind,
            str(job.get("version") or "") == current_version,
            str(job.get("worker_result") or "") == "install_verified",
            str(job.get("package_self_test") or "") == "passed",
            str(job.get("runtime_health") or "") == "passed",
            str(job.get("rollback") or "") == "not_needed",
        )
        if not all(required_truth):
            raise UpdatePreparationError("UPDATE_FINALIZE_JOB_TRUTH_INVALID")
        if platform_kind == "windows" and str(job.get("worker_contract") or "") != WINDOWS_WORKER_CONTRACT:
            raise UpdatePreparationError("UPDATE_FINALIZE_WORKER_CONTRACT_INVALID")
        try:
            sequence = int(job.get("sequence"))
        except (TypeError, ValueError) as exc:
            raise UpdatePreparationError("UPDATE_FINALIZE_SEQUENCE_INVALID") from exc
        if sequence <= 0:
            raise UpdatePreparationError("UPDATE_FINALIZE_SEQUENCE_INVALID")

    @classmethod
    def finalize_job(
        cls,
        job_id: str,
        *,
        current_version: str | None = None,
        platform_kind: str | None = None,
    ) -> dict[str, Any]:
        job = UpdateEngine.get_job(job_id)
        version = current_version or cls._current_version()
        platform_value = str(platform_kind or get_platform_adapter().kind).strip().lower()
        cls._validate_job(job, current_version=version, platform_kind=platform_value)
        finalized = UpdateEngine.mark_installed_healthy(job_id)
        if (
            finalized.get("status") != "healthy"
            or str(finalized.get("version") or "") != version
            or int(finalized.get("sequence") or 0) <= 0
        ):
            raise UpdatePreparationError("UPDATE_FINALIZE_COMMIT_INVALID")
        return finalized

    @classmethod
    def run(cls, job_path: Path) -> int:
        report_path: Path | None = None
        try:
            resolved = Path(job_path).resolve()
            if resolved.name != "job.json":
                raise UpdatePreparationError("UPDATE_FINALIZE_JOB_PATH_INVALID")
            job_id = resolved.parent.name
            canonical = (UpdateEngine._job_dir(job_id) / "job.json").resolve()
            if resolved != canonical or not resolved.is_file():
                raise UpdatePreparationError("UPDATE_FINALIZE_JOB_PATH_INVALID")
            report_path = resolved.parent / FINALIZE_REPORT_NAME
            finalized = cls.finalize_job(job_id)
            report_path.write_text(
                json.dumps(
                    {
                        "schema": 1,
                        "status": "success",
                        "job_id": job_id,
                        "version": finalized["version"],
                        "sequence": finalized["sequence"],
                    },
                    indent=2,
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            return 0
        except Exception as exc:
            if report_path is not None:
                try:
                    report_path.write_text(
                        json.dumps(
                            {
                                "schema": 1,
                                "status": "failed",
                                "error_code": str(exc),
                            },
                            indent=2,
                            sort_keys=True,
                        ),
                        encoding="utf-8",
                    )
                except Exception:
                    pass
            return 4
