from __future__ import annotations

import os
from typing import Any

from backend.services.macos_update_apply import MacOSUpdateApplyService
from backend.services.update_apply import CONFIRMATION_TOKEN, UpdateApplyService
from backend.services.update_engine import UpdateEngine, UpdatePreparationError


class UpdateApplyDispatchService:
    """Select the already-certified OS-specific mutation boundary."""

    @staticmethod
    def _version_tuple(value: str) -> tuple[int, int, int]:
        parts = str(value or "").strip().split(".")
        if len(parts) != 3 or any(not part.isdigit() for part in parts):
            raise UpdatePreparationError("UPDATE_VERSION_FORMAT_UNSUPPORTED")
        return tuple(int(part) for part in parts)  # type: ignore[return-value]

    @classmethod
    def _require_macos_upgrade(cls, job: dict[str, Any], confirmation: str) -> None:
        # Preserve MacOSUpdateApplyService's public error ordering for invalid
        # confirmation/runtime gates. The preflight only runs once those gates pass.
        if confirmation != CONFIRMATION_TOKEN:
            return
        if not MacOSUpdateApplyService.runtime_apply_supported():
            return
        current = MacOSUpdateApplyService._current_version()
        target = str(job.get("version") or "")
        if cls._version_tuple(target) <= cls._version_tuple(current):
            raise UpdatePreparationError("UPDATE_VERSION_NOT_NEWER")
        install_app = MacOSUpdateApplyService._installed_app()
        if not os.access(install_app.parent, os.W_OK):
            raise UpdatePreparationError("UPDATE_MACOS_INSTALL_PARENT_NOT_WRITABLE")

    @classmethod
    def request_apply(cls, job_id: str, confirmation: str) -> dict[str, Any]:
        job = UpdateEngine.get_job(job_id)
        platform = str(job.get("platform") or "").strip().lower()
        if platform == "windows":
            return UpdateApplyService.request_apply(job_id, confirmation)
        if platform == "macos":
            cls._require_macos_upgrade(job, confirmation)
            return MacOSUpdateApplyService.request_apply(job_id, confirmation)
        raise UpdatePreparationError("UPDATE_PLATFORM_APPLY_NOT_WIRED")

    @staticmethod
    def get_public_job(job_id: str) -> dict[str, Any]:
        job = UpdateEngine.get_job(job_id)
        public = UpdateApplyService.public_job(job)
        if str(job.get("platform") or "").strip().lower() == "macos":
            for key in (
                "macos_developer_id",
                "macos_hardened_runtime",
                "macos_secure_timestamp",
                "macos_notarization",
                "macos_gatekeeper",
            ):
                if key in job:
                    public[key] = job[key]
        return public
