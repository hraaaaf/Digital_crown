from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVICE = ROOT / "backend" / "services" / "update_engine.py"
POST_INSTALL = ROOT / "backend" / "services" / "update_post_install.py"
WINDOWS_WORKER = ROOT / "scripts" / "windows_update_worker.ps1"
WINDOWS_WORKER_CI = ROOT / "scripts" / "p10_windows_worker_ci.ps1"
WORKFLOW = ROOT / ".github" / "workflows" / "portability-p10-update-engine.yml"
RUN = ROOT / "run.py"
SPEC = ROOT / "DigitalCrown.spec"
DOC = ROOT / "docs" / "portability" / "P10_UPDATE_ENGINE.md"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> None:
    service = SERVICE.read_text(encoding="utf-8")
    post_install = POST_INSTALL.read_text(encoding="utf-8")
    worker = WINDOWS_WORKER.read_text(encoding="utf-8")
    worker_ci = WINDOWS_WORKER_CI.read_text(encoding="utf-8")
    workflow = WORKFLOW.read_text(encoding="utf-8")
    run = RUN.read_text(encoding="utf-8")
    spec = SPEC.read_text(encoding="utf-8")
    doc = DOC.read_text(encoding="utf-8")

    for marker in (
        "Ed25519PublicKey",
        "UPDATE_ROLLBACK_BLOCKED",
        "UPDATE_REPLAY_CONFLICT",
        "UPDATE_MANIFEST_EXPIRED",
        "UPDATE_TARGET_URL_HTTPS_REQUIRED",
        ".partial",
        "UPDATE_ARTIFACT_SHA256_MISMATCH",
        "BackupService.backup_active_database()",
        "rescue_staged",
        'job.get("status") != "health_pending"',
        "UPDATE_PLATFORM_APPLY_NOT_CERTIFIED",
        "highest_sequence",
        "last_trusted_time",
    ):
        require(marker in service, f"P10 update engine missing marker: {marker}")

    for marker in (
        "--package-self-test",
        "DIGITALCROWN_PACKAGE_SELF_TEST_REPORT",
        '"version":',
        '"scientific_capabilities": "FAIL_CLOSED_NO_WEIGHTS"',
    ):
        require(marker in run, f"P10 packaged self-test dependency missing: {marker}")
    require("(_required('VERSION'), '.')" in spec, "P10 requires bundled canonical VERSION")

    for marker in (
        "verify_package_self_test",
        "expected_version",
        "UPDATE_POST_INSTALL_PACKAGE_TRUTH_FAILED",
        "FAIL_CLOSED_NO_WEIGHTS",
        "UPDATE_POST_INSTALL_HEALTH_URL_NOT_LOOPBACK",
        "wait_runtime_health",
        'payload.get("status") == "ok"',
        'payload.get("db") == "ok"',
        "verify_post_install",
    ):
        require(marker in post_install, f"P10 post-install truth missing marker: {marker}")

    for marker in (
        "windows-inno-v1",
        "UPDATE_PLATFORM_APPLY_NOT_CERTIFIED",
        "UPDATE_WINDOWS_ARTIFACT_SHA256_MISMATCH",
        "UPDATE_WINDOWS_RESCUE_BACKUP_SHA256_MISMATCH",
        "Snapshot-Program",
        "program-manifest.json",
        "Export-UninstallRegistry",
        "Assert-UninstallRegistryVersion",
        "Invoke-PackageSelfTest",
        "Wait-RuntimeHealth",
        "Restore-Program",
        "Restore-UninstallRegistry",
        '"health_pending"',
        '"rolled_back"',
        '"rollback_failed"',
        '"required_but_not_wired"',
        "param([int]$ProcessId",
        "Wait-ParentExit -ProcessId $ParentPid",
        "#requires -Version 5.1",
        "[IO.Path]::IsPathRooted",
        "Expand-ManifestRows",
        "UPDATE_WINDOWS_PROGRAM_RESCUE_INTEGRITY_FAILED",
        '$ErrorCode`:COUNT:',
        '$ErrorCode`:ENTRY:',
    ):
        require(marker in worker, f"P10 Windows worker missing marker: {marker}")
    require("param([int]$Pid" not in worker, "P10 Windows worker must not shadow PowerShell automatic $PID")
    require("#requires -Version 7.0" not in worker, "P10 Windows worker must not require PowerShell 7")
    require("IsPathFullyQualified" not in worker, "P10 Windows worker must stay compatible with Windows PowerShell 5.1")

    for marker in (
        "P10_WINDOWS_WORKER_CONTRACT=SUCCESS",
        "ApplyCertified $false",
        "ExpectedExitCode 1",
        "ExpectedExitCode 0",
        "ExpectedExitCode 2",
        'rollback.database_rollback -ne "not_needed"',
        "rollback registry not restored",
    ):
        require(marker in worker_ci, f"P10 Windows worker CI missing drill: {marker}")

    for marker in (
        "Windows PowerShell 5.1 external worker contract",
        "WindowsPowerShell\\v1.0\\powershell.exe",
        "P10_WINDOWS_POWERSHELL=5.1",
        "dc-p10-ps51-shim",
    ):
        require(marker in workflow, f"P10 Windows PowerShell 5.1 workflow missing marker: {marker}")

    require("private key" in doc.lower(), "P10 doc must state private-key handling")
    require("0 EP" in doc, "P10 remains open until packaged apply/rollback certification")
    require("P6/P7" in doc, "P10 doc must state packaging dependency")
    require("package self-test" in doc.lower(), "P10 doc must state exact packaged VERSION proof")
    require("/health" in doc, "P10 doc must state runtime health proof")
    require("program snapshot" in doc.lower(), "P10 doc must state Windows program rollback")
    require("uninstall registry" in doc.lower(), "P10 doc must state Windows uninstall metadata rollback")
    require("required_but_not_wired" in doc, "P10 doc must state DB rollback boundary")
    require("Windows PowerShell 5.1" in doc, "P10 doc must state native Windows PowerShell 5.1 runtime")
    print("P10_UPDATE_CONTRACT=SUCCESS post_install_truth=READY windows_worker=PS51_CONTRACT_READY apply=BLOCKED")


if __name__ == "__main__":
    main()
