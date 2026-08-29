from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVICE = ROOT / "backend" / "services" / "disaster_recovery_service.py"
SCHEDULER = ROOT / "backend" / "services" / "daily_scheduler.py"
GUIDED_RESTORE = ROOT / "backend" / "services" / "guided_restore.py"
WORKER = ROOT / "backend" / "services" / "guided_restore_worker.py"
CROSS_OS = ROOT / "scripts" / "p9_offmachine_cross_os_ci.py"
WORKFLOW = ROOT / ".github" / "workflows" / "portability-p9-dr-cert.yml"
DOC = ROOT / "docs" / "portability" / "P9_BACKUP_RECOVERY_DR.md"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> None:
    service = SERVICE.read_text(encoding="utf-8")
    scheduler = SCHEDULER.read_text(encoding="utf-8")
    guided_restore = GUIDED_RESTORE.read_text(encoding="utf-8")
    worker = WORKER.read_text(encoding="utf-8")
    cross_os = CROSS_OS.read_text(encoding="utf-8")
    workflow = WORKFLOW.read_text(encoding="utf-8")
    doc = DOC.read_text(encoding="utf-8")

    for marker in (
        "DIGITALCROWN_DR_DESTINATION",
        "DIGITALCROWN_DR_SECRET",
        "CabinetBundleService.create_bundle",
        "CabinetBundleService.to_local_guided_restore_archive",
        "verified_restore_path",
        "_cleanup_verified_bundles",
        "_is_verified_pair",
        'final_target.name + ".partial"',
        "os.replace(working_target, final_target)",
        "working_target.unlink(missing_ok=True)",
        "sidecar.unlink(missing_ok=True)",
        "DR_DISK_FULL",
        "DR_PORTABLE_ENGINE_UNSUPPORTED",
    ):
        require(marker in service, f"P9 DR service missing contract marker: {marker}")

    require(
        "disaster_recovery_service.run_scheduled_snapshot()" in scheduler,
        "Daily scheduler must invoke the DR snapshot service",
    )
    require(
        "backup_service.run_daily_backup()" in scheduler,
        "P9 must preserve the existing local daily backup",
    )

    for marker in (
        "runtime_apply_supported",
        'bool(getattr(sys, "frozen", False))',
        'os.environ.get("ENVIRONMENT", "").strip().lower() == "cabinet"',
        "CONFIRMATION_TOKEN",
    ):
        require(marker in guided_restore, f"P9 Guided Restore packaged gate missing: {marker}")

    for marker in (
        "_wait_parent_exit",
        "_apply_database",
        "_apply_media",
        "_smoke_check",
        "rebind_portable_restore",
        '"success"',
        '"rolled_back"',
    ):
        require(marker in worker, f"P9 restore worker missing contract marker: {marker}")

    for marker in (
        "DisasterRecoveryService.create_verified_snapshot",
        "source-proof.json",
        "source_master_fingerprint",
        "SOURCE_AND_TARGET_MASTER_KEYS_MUST_DIFFER",
        "WRONG_MIGRATION_SECRET_ACCEPTED",
        "TAMPERED_BUNDLE_ACCEPTED",
        "--guided-restore-worker",
        "FROZEN_RESTORE_WORKER_FAILED",
        "RESTORED_DATABASE_INTEGRITY_FAILED",
        "RESTORED_MEDIA_SHA256_MISMATCH",
        "CROSS_OS_BOUNDARY_NOT_PROVED",
        "P9_OFFMACHINE_PACKAGED_RESTORE=SUCCESS",
    ):
        require(marker in cross_os, f"P9 cross-OS certification missing marker: {marker}")

    for marker in (
        "source-windows:",
        "source-macos:",
        "target-macos-from-windows:",
        "target-windows-from-macos:",
        "actions/upload-artifact@v4",
        "actions/download-artifact@v4",
        "P9_SOURCE_LOCAL_DELETE=SUCCESS",
        "P9_TARGET_FRESH_BOUNDARY=SUCCESS",
        "Build real macOS frozen target",
        "Build real Windows frozen target",
        "retention-days: 2",
    ):
        require(marker in workflow, f"P9 workflow missing off-machine marker: {marker}")

    require(
        "backup.key" in doc and "machine-local" in doc,
        "P9 documentation must state machine-local backup-key limitation",
    )
    require(
        ".dcbundle" in doc and "Guided Restore" in doc,
        "P9 documentation must describe portable restore path",
    )
    require(
        ".partial" in doc and "sidecar" in doc,
        "P9 documentation must describe interrupted snapshot promotion semantics",
    )
    for marker in (
        "independently persisted off-runner artifact boundary",
        "distinct fresh runner",
        "frozen packaged executable",
        "Windows → macOS",
        "macOS → Windows",
        "P13",
        "0 EP",
        "No Vercel",
    ):
        require(marker in doc, f"P9 documentation missing certification truth: {marker}")

    print(
        "P9_DR_CONTRACT=SUCCESS "
        "off_runner_boundary=PREPARED cross_os=PREPARED frozen_restore=REQUIRED ep=0"
    )


if __name__ == "__main__":
    main()
