from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVICE = ROOT / "backend" / "services" / "disaster_recovery_service.py"
SCHEDULER = ROOT / "backend" / "services" / "daily_scheduler.py"
DOC = ROOT / "docs" / "portability" / "P9_BACKUP_RECOVERY_DR.md"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> None:
    service = SERVICE.read_text(encoding="utf-8")
    scheduler = SCHEDULER.read_text(encoding="utf-8")
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
    require("backup.key" in doc and "machine-local" in doc, "P9 documentation must state machine-local backup-key limitation")
    require(".dcbundle" in doc and "Guided Restore" in doc, "P9 documentation must describe portable restore path")
    require(".partial" in doc and "sidecar" in doc, "P9 documentation must describe interrupted snapshot promotion semantics")
    require("0 EP" in doc, "P9 remains open until real external-destination certification")

    print("P9_DR_CONTRACT=SUCCESS")


if __name__ == "__main__":
    main()
