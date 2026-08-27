from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLATFORM = ROOT / "backend" / "core" / "platform.py"
SERVICE = ROOT / "backend" / "services" / "update_windows_apply.py"
TESTS = ROOT / "backend" / "tests" / "test_update_windows_apply.py"
RUN = ROOT / "run.py"
SPEC = ROOT / "DigitalCrown.spec"
INSTALLER = ROOT / "installer" / "DigitalCrown.iss"
WORKER = ROOT / "scripts" / "windows_update_worker.ps1"
WORKER_CORE = ROOT / "scripts" / "windows_update_worker_core.ps1"
LIFECYCLE = ROOT / "scripts" / "p10_windows_packaged_lifecycle_ci.ps1"
WORKFLOW = ROOT / ".github" / "workflows" / "portability-p10-windows-packaged-lifecycle.yml"
DOC = ROOT / "docs" / "portability" / "P10_WINDOWS_PACKAGED_LIFECYCLE.md"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> None:
    platform = PLATFORM.read_text(encoding="utf-8")
    service = SERVICE.read_text(encoding="utf-8")
    tests = TESTS.read_text(encoding="utf-8")
    run = RUN.read_text(encoding="utf-8")
    spec = SPEC.read_text(encoding="utf-8")
    installer = INSTALLER.read_text(encoding="utf-8")
    worker = WORKER.read_text(encoding="utf-8")
    worker_core = WORKER_CORE.read_text(encoding="utf-8")
    lifecycle = LIFECYCLE.read_text(encoding="utf-8")
    workflow = WORKFLOW.read_text(encoding="utf-8")
    doc = DOC.read_text(encoding="utf-8")

    for marker in (
        "prepare_signed",
        "signed-manifest.json",
        "verify_manifest(",
        "UPDATE_WINDOWS_SIGNED_JOB_MISMATCH",
        "UPDATE_WINDOWS_TRUST_STATE_STALE",
        "UPDATE_WINDOWS_ARCHITECTURE_NOT_CERTIFIED",
        "UPDATE_WINDOWS_ARTIFACT_FORMAT_UNSUPPORTED",
        "UPDATE_WINDOWS_BACKUP_KEY_MISSING",
        "windows-inno-v1",
        "windows_powershell_executable(",
        "launch_detached(",
        "failed_pre_apply",
        "scheduler_launch_failed",
    ):
        require(marker in service, f"packaged scheduler missing marker: {marker}")
    require("powershell.exe" not in service.lower(), "scheduler must not embed Windows PowerShell executable token")
    require("subprocess.Popen" not in service, "scheduler must launch through PlatformAdapter")

    for marker in (
        "def windows_powershell_executable(",
        "def launch_detached(",
        "powershell.exe",
    ):
        require(marker in platform, f"platform boundary missing Windows process marker: {marker}")

    for marker in (
        "test_prepare_and_schedule_signed_windows_job",
        "test_schedule_rejects_job_tampering_against_signed_manifest",
        "test_schedule_rejects_missing_backup_key",
        "test_worker_launch_failure_is_fail_closed_before_apply",
        "adapter.launch_error",
    ):
        require(marker in tests, f"scheduler tests missing: {marker}")

    for marker in (
        "--prepare-signed-windows-update",
        "--schedule-windows-update",
        "DIGITALCROWN_UPDATE_PREPARE_REPORT",
        "DIGITALCROWN_UPDATE_SCHEDULE_REPORT",
        "_maybe_run_update_db_rollback_worker()",
        "_maybe_prepare_signed_windows_update()",
        "_maybe_schedule_windows_update()",
        "_first_boot_bootstrap()",
    ):
        require(marker in run, f"packaged CLI missing marker: {marker}")
    require(
        run.rindex("_maybe_run_update_db_rollback_worker()")
        < run.rindex("_maybe_prepare_signed_windows_update()")
        < run.rindex("_maybe_schedule_windows_update()")
        < run.rindex("_first_boot_bootstrap()"),
        "update helpers must execute before first-boot secret generation",
    )

    for marker in (
        "_required('scripts/windows_update_worker.ps1')",
        "_required('scripts/windows_update_worker_core.ps1')",
        "'backend.services.update_windows_apply'",
    ):
        require(marker in spec, f"PyInstaller packaged lifecycle dependency missing: {marker}")

    require(
        "UninstallDisplayName={#MyAppName}" in installer,
        "Inno uninstall DisplayName must stay stable for worker registry matching",
    )

    require("#requires -Version 5.1" in worker, "public worker must support Windows PowerShell 5.1")
    require("#requires -Version 5.1" in worker_core, "core worker must support Windows PowerShell 5.1")
    require("#requires -Version 7.0" not in worker_core, "core worker regressed to PowerShell 7")

    for marker in (
        "P10_WINDOWS_PACKAGED_LIFECYCLE=SUCCESS",
        "--prepare-signed-windows-update",
        "--schedule-windows-update",
        "health_pending",
        "DisplayVersion",
        "signed-manifest",
        "Ed25519",
    ):
        require(marker in lifecycle, f"packaged lifecycle drill missing marker: {marker}")

    for marker in (
        "windows-2025",
        "backend/core/platform.py",
        "p10_windows_packaged_lifecycle_check.py",
        "p10_windows_packaged_lifecycle_ci.ps1",
        "DigitalCrownSetup-",
        "PyInstaller",
        "INNO_SETUP_SHA256",
    ):
        require(marker in workflow, f"packaged lifecycle workflow missing marker: {marker}")

    require("0 EP" in doc, "packaged lifecycle candidate must not credit P10 before closure")
    require("Ed25519" in doc, "doc must state signed-manifest revalidation")
    require("P7" in doc, "doc must retain macOS closure dependency")
    require("No Vercel" in doc, "doc must state deployment boundary")

    print("P10_WINDOWS_PACKAGED_CONTRACT=SUCCESS scheduler=SIGNED_REVERIFY os_boundary=PLATFORM_ADAPTER worker=PS51 lifecycle=READY")


if __name__ == "__main__":
    main()
