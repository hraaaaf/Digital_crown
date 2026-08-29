from __future__ import annotations

from backend.services.update_db_rollback import UpdateDatabaseRollback, UpdateDatabaseRollbackError


class MacOSUpdateDatabaseRollback(UpdateDatabaseRollback):
    """Authorize the existing replay-safe SQLite rescue for the macOS package worker."""

    @classmethod
    def _require_authorized_rollback_state(cls, job: dict) -> None:
        if (
            str(job.get("platform") or "").lower() != "macos"
            or str(job.get("worker_contract") or "") != "macos-dmg-v1"
            or job.get("apply_certified") is not True
            or str(job.get("status") or "") != "database_rolling_back"
            or str(job.get("worker_result") or "") != "rollback_failed"
            or str(job.get("rollback") or "") != "failed"
            or str(job.get("rollback_failure_reason") or "")
            != "UPDATE_MACOS_PACKAGE_ROLLBACK_HEALTH_FAILED"
            or str(job.get("database_rollback") or "") != "running"
        ):
            raise UpdateDatabaseRollbackError("UPDATE_DB_ROLLBACK_NOT_AUTHORIZED")
