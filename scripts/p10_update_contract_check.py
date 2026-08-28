from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLATFORM = ROOT / "backend" / "core" / "platform.py"
SERVICE = ROOT / "backend" / "services" / "update_engine.py"
APPLY_SERVICE = ROOT / "backend" / "services" / "update_apply.py"
RECOVERY_SERVICE = ROOT / "backend" / "services" / "update_recovery.py"
FINALIZE_SERVICE = ROOT / "backend" / "services" / "update_finalize.py"
POST_INSTALL = ROOT / "backend" / "services" / "update_post_install.py"
DB_ROLLBACK = ROOT / "backend" / "services" / "update_db_rollback.py"
UPDATE_ROUTER = ROOT / "backend" / "routers" / "update_portability_p10.py"
ROUTERS_INIT = ROOT / "backend" / "routers" / "__init__.py"
WINDOWS_ENTRY = ROOT / "scripts" / "windows_update_worker_entry.ps1"
WINDOWS_ORCHESTRATOR = ROOT / "scripts" / "windows_update_worker.ps1"
WINDOWS_WORKER_CORE = ROOT / "scripts" / "windows_update_worker_core.ps1"
WINDOWS_RECOVERY = ROOT / "scripts" / "windows_update_recovery.ps1"
WINDOWS_WORKER_CI = ROOT / "scripts" / "p10_windows_worker_ci.ps1"
WINDOWS_DB_ROLLBACK_CI = ROOT / "scripts" / "p10_windows_db_rollback_ci.ps1"
WINDOWS_PACKAGED_FINALIZATION_CI = ROOT / "scripts" / "p10_windows_packaged_finalization_ci.py"
WORKFLOW = ROOT / ".github" / "workflows" / "portability-p10-update-engine.yml"
RUN = ROOT / "run.py"
SPEC = ROOT / "DigitalCrown.spec"
DOC = ROOT / "docs" / "portability" / "P10_UPDATE_ENGINE.md"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> None:
    platform = PLATFORM.read_text(encoding="utf-8")
    service = SERVICE.read_text(encoding="utf-8")
    apply_service = APPLY_SERVICE.read_text(encoding="utf-8")
    recovery_service = RECOVERY_SERVICE.read_text(encoding="utf-8")
    finalize_service = FINALIZE_SERVICE.read_text(encoding="utf-8")
    post_install = POST_INSTALL.read_text(encoding="utf-8")
    db_rollback = DB_ROLLBACK.read_text(encoding="utf-8")
    update_router = UPDATE_ROUTER.read_text(encoding="utf-8")
    routers_init = ROUTERS_INIT.read_text(encoding="utf-8")
    entry = WINDOWS_ENTRY.read_text(encoding="utf-8")
    orchestrator = WINDOWS_ORCHESTRATOR.read_text(encoding="utf-8")
    worker_core = WINDOWS_WORKER_CORE.read_text(encoding="utf-8")
    recovery = WINDOWS_RECOVERY.read_text(encoding="utf-8")
    worker_ci = WINDOWS_WORKER_CI.read_text(encoding="utf-8")
    db_rollback_ci = WINDOWS_DB_ROLLBACK_CI.read_text(encoding="utf-8")
    packaged_finalization_ci = WINDOWS_PACKAGED_FINALIZATION_CI.read_text(encoding="utf-8")
    workflow = WORKFLOW.read_text(encoding="utf-8")
    run = RUN.read_text(encoding="utf-8")
    spec = SPEC.read_text(encoding="utf-8")
    doc = DOC.read_text(encoding="utf-8")

    for marker in (
        "Ed25519PublicKey", "UPDATE_ROLLBACK_BLOCKED", "UPDATE_REPLAY_CONFLICT",
        "UPDATE_MANIFEST_EXPIRED", "UPDATE_TARGET_URL_HTTPS_REQUIRED", ".partial",
        "UPDATE_ARTIFACT_SHA256_MISMATCH", "BackupService.backup_active_database()",
        "rescue_staged", 'job.get("status") != "health_pending"',
        "UPDATE_PLATFORM_APPLY_NOT_CERTIFIED", "highest_sequence", "last_trusted_time",
        "installed_sequence", "installed_version", "mark_installed_healthy",
    ):
        require(marker in service, f"P10 update engine missing marker: {marker}")

    for marker in ("windows_powershell51_path", "WindowsPowerShell", "powershell.exe", "try_acquire_process_lock"):
        require(marker in platform, f"P10/P1 platform boundary missing marker: {marker}")

    for marker in (
        'CONFIRMATION_TOKEN = "METTRE_A_JOUR"', "bool(getattr(sys, \"frozen\", False))",
        'os.environ.get("ENVIRONMENT", "").strip().lower() == "cabinet"', "adapter.is_windows",
        "windows_powershell51_path", "windows-inno-v1", "windows-interruption-v1",
        "windows_update_worker_entry.ps1", "windows_update_worker.ps1", "windows_update_worker_core.ps1",
        "windows_update_recovery.ps1", "_stage_windows_workers", "_verify_staged_workers",
        "Get-AuthenticodeSignature", "TimeStamperCertificate", 'status != "Valid"',
        "UPDATE_WINDOWS_AUTHENTICODE_TIMESTAMP_REQUIRED", "apply_certified=True",
        'job["status"] = "scheduled"', "_launch_detached_worker", '"-JobPath"', '"-ParentPid"',
        "detached_process_kwargs", "_terminate_parent_after_response", "os._exit(0)",
    ):
        require(marker in apply_service, f"P10 production apply wiring missing marker: {marker}")
    require("powershell.exe" not in apply_service, "P10 apply service must use the P1 OS boundary for PowerShell")
    require("backup.key" not in apply_service, "P10 apply launcher must not pass backup secrets")
    require("Fernet" not in apply_service, "P10 apply launcher must not decrypt cabinet backups")

    for marker in (
        "RECOVERABLE_STATES", '"scheduled"', '"applying"', '"rolling_back"', '"health_pending"',
        '"database_rolling_back"', "UPDATE_RECOVERY_MULTIPLE_ACTIVE_JOBS",
        "UPDATE_RECOVERY_WORKER_SHA256_MISMATCH", 'os.environ.get("DIGITALCROWN_RESTORE_RESTART") == "1"',
        "schedule_startup_recovery", "worker_recovery_filename", "windows-interruption-v1", "detached_process_kwargs",
    ):
        require(marker in recovery_service, f"P10 startup recovery missing marker: {marker}")
    require("DigitalCrownSetup" not in recovery_service, "P10 startup recovery service must never launch an installer")

    for marker in (
        "health_pending", "apply_certified", "install_verified", "package_self_test", "runtime_health",
        "not_needed", "windows-inno-v1", "mark_installed_healthy", "UPDATE_FINALIZE_JOB_TRUTH_INVALID",
        "UPDATE_FINALIZE_COMMIT_INVALID", "update-finalize-report.json", "atomic_write_text",
    ):
        require(marker in finalize_service, f"P10 installed-truth finalizer missing marker: {marker}")

    for marker in (
        '@router.post("/update/{job_id}/apply")', '@router.get("/update/{job_id}/status")',
        "require_permission(\"admin\")", "UPDATE_APPLY_REQUESTED", "JSONResponse(status_code=202",
    ):
        require(marker in update_router, f"P10 update API missing marker: {marker}")
    require("admin.router.include_router(update_portability_p10.router)" in routers_init,
            "P10 update API must be mounted on the authenticated admin router")

    for marker in (
        "--package-self-test", "DIGITALCROWN_PACKAGE_SELF_TEST_REPORT", '"version":',
        '"scientific_capabilities": "FAIL_CLOSED_NO_WEIGHTS"', "--update-db-rollback-worker",
        "UpdateDatabaseRollback.run", "--update-finalize-worker", "UpdateFinalizeService.run",
        "UpdateRecoveryService.schedule_startup_recovery", "update_recovery_scheduled",
    ):
        require(marker in run, f"P10 packaged runtime dependency missing: {marker}")
    require("_setup_frozen_logging()\n_maybe_run_update_db_rollback_worker()\n_maybe_run_update_finalize_worker()\n_first_boot_bootstrap()" in run,
            "P10 rollback/finalize workers must run before first-boot secret generation")
    require("(_required('VERSION'), '.')" in spec, "P10 requires bundled canonical VERSION")
    require("(_required('scripts/windows_update_worker_entry.ps1'), 'scripts')" in spec, "P10 Windows package must bundle update worker entry")
    require("(_required('scripts/windows_update_worker.ps1'), 'scripts')" in spec, "P10 Windows package must bundle update orchestrator")
    require("(_required('scripts/windows_update_worker_core.ps1'), 'scripts')" in spec, "P10 Windows package must bundle update worker core")
    require("(_required('scripts/windows_update_recovery.ps1'), 'scripts')" in spec, "P10 Windows package must bundle recovery worker")

    for marker in (
        "verify_package_self_test", "expected_version", "UPDATE_POST_INSTALL_PACKAGE_TRUTH_FAILED",
        "FAIL_CLOSED_NO_WEIGHTS", "UPDATE_POST_INSTALL_HEALTH_URL_NOT_LOOPBACK", "wait_runtime_health",
        'payload.get("status") == "ok"', 'payload.get("db") == "ok"', "verify_post_install",
    ):
        require(marker in post_install, f"P10 post-install truth missing marker: {marker}")

    for marker in (
        "UPDATE_DB_ROLLBACK_NOT_AUTHORIZED", 'str(job.get("platform") or "").lower() != "windows"',
        'str(job.get("worker_contract") or "") != "windows-inno-v1"', 'job.get("apply_certified") is not True',
        'str(job.get("status") or "") != "database_rolling_back"', '!= "UPDATE_WINDOWS_PACKAGE_ROLLBACK_HEALTH_FAILED"',
        'str(job.get("database_rollback") or "") != "running"', "UPDATE_DB_ROLLBACK_POSTGRES_UNSUPPORTED",
        "UPDATE_DB_ROLLBACK_BACKUP_KEY_MISSING", "UPDATE_DB_ROLLBACK_SQLCIPHER_KEY_MISSING",
        "UPDATE_DB_ROLLBACK_RESCUE_SHA256_MISMATCH", ".db.enc", 'user_data / "backup.key"',
        "BackupService._verify_sqlcipher_file(temp, passphrase)", "BackupService._verify_sqlcipher_file(target, passphrase)",
        'job_dir / "rescue" / "pre-db-rollback"', "ROLLBACK_STATE_NAME", "_prepare_or_verify_quarantine",
        '"phase": "quarantined"', 'state["phase"] = "restored"', '"replay_safe": True',
        "os.replace(temp, target)", "UPDATE_DB_ROLLBACK_RESTORED_DB_INVALID",
        "UPDATE_DB_ROLLBACK_ORIGINAL_RESTORE_VERIFY_FAILED", "UPDATE_DB_ROLLBACK_ORIGINAL_RESTORE_INVALID",
        '"db-rollback-report.json"',
    ):
        require(marker in db_rollback, f"P10 DB rollback bridge missing marker: {marker}")
    require("_get_or_create_key" not in db_rollback, "P10 DB rollback must never create a replacement backup key")

    for marker in (
        "worker.lock", '"worker_pid"', '"worker_role" "apply"', "windows-interruption-v1",
        "windows_update_worker.ps1_sha256", "windows_update_worker_core.ps1_sha256",
        "windows_update_recovery.ps1_sha256", "Start-Process -FilePath $nativePs",
    ):
        require(marker in entry, f"P10 Windows entry ownership missing marker: {marker}")
    require("Invoke-InnoInstaller" not in entry, "P10 entry must delegate installer mutation to certified core")

    for marker in (
        "windows-inno-v1", "UPDATE_PLATFORM_APPLY_NOT_CERTIFIED", "UPDATE_WINDOWS_ARTIFACT_SHA256_MISMATCH",
        "UPDATE_WINDOWS_RESCUE_BACKUP_SHA256_MISMATCH", "Snapshot-Program", "program-manifest.json",
        "Export-UninstallRegistry", "Assert-UninstallRegistryVersion", "Invoke-PackageSelfTest", "Wait-RuntimeHealth",
        "Restore-Program", "Restore-UninstallRegistry", '"health_pending"', '"rolled_back"', '"rollback_failed"',
        '"required_but_not_wired"', "param([int]$ProcessId", "Wait-ParentExit -ProcessId $ParentPid",
        "#requires -Version 5.1", "[IO.Path]::IsPathRooted", "Expand-ManifestRows",
        "UPDATE_WINDOWS_PROGRAM_RESCUE_INTEGRITY_FAILED",
    ):
        require(marker in worker_core, f"P10 Windows worker core missing marker: {marker}")
    require("param([int]$Pid" not in worker_core, "P10 Windows worker core must not shadow PowerShell automatic $PID")
    require("#requires -Version 7.0" not in worker_core, "P10 Windows worker core must not require PowerShell 7")
    require("IsPathFullyQualified" not in worker_core, "P10 Windows worker core must stay compatible with Windows PowerShell 5.1")

    for marker in (
        "windows_update_worker_core.ps1", "UPDATE_WINDOWS_PACKAGE_ROLLBACK_HEALTH_FAILED",
        'database_rollback -eq "required_but_not_wired"', '"database_rolling_back"',
        '"--update-db-rollback-worker"', '"database_rollback" "passed"', '"database_rollback" "failed"',
        "UPDATE_WINDOWS_DB_ROLLBACK_RUNTIME_HEALTH_FAILED", "DigitalCrown.exe", '"--update-finalize-worker"',
        'finalization=passed', 'status -ne "healthy"', "Stop-Process -Id $failedRuntimePid",
    ):
        require(marker in orchestrator, f"P10 Windows orchestrator missing marker: {marker}")
    require("Fernet" not in orchestrator, "P10 PowerShell orchestrator must never decrypt cabinet backups")
    require("windows_update_worker_entry.ps1_sha256" in entry, "P10 Windows entry must self-verify its staged SHA256")
    require("windows_update_recovery.ps1_sha256" in recovery, "P10 recovery worker must self-verify its staged SHA256")
    require("windows-interruption-v1" in recovery, "P10 recovery worker must require the recovery contract")

    for marker in (
        "worker.lock", "Acquire-WorkerLock", '"scheduled"', '"applying"', '"rolling_back"', '"health_pending"',
        '"database_rolling_back"', "UPDATE_INTERRUPTED_BEFORE_APPLY", "Restore-Program", "Restore-UninstallRegistry",
        "Invoke-PackageRollback", "Invoke-DatabaseFallback", '"--update-db-rollback-worker"',
        '"--update-finalize-worker"', "UPDATE_RECOVERY_WORKER_BUSY",
    ):
        require(marker in recovery, f"P10 Windows recovery missing marker: {marker}")
    require("Invoke-InnoInstaller" not in recovery, "P10 recovery must never invoke installer apply")
    require("FakeInstaller" not in recovery, "P10 recovery must not contain test installer logic")

    for marker in (
        "P10_WINDOWS_WORKER_CONTRACT=SUCCESS", "ApplyCertified $false", "ExpectedExitCode 1", "ExpectedExitCode 0",
        "ExpectedExitCode 2", 'rollback.database_rollback -ne "not_needed"', "rollback registry not restored",
    ):
        require(marker in worker_ci, f"P10 Windows worker CI missing drill: {marker}")

    for marker in (
        "P10_WINDOWS_DB_ROLLBACK_BRIDGE=SUCCESS", "UPDATE_WINDOWS_PACKAGE_ROLLBACK_HEALTH_FAILED",
        "UPDATE_WINDOWS_UNINSTALL_REGISTRY_IMPORT_FAILED", 'ExpectedExitCode 2', 'ExpectedExitCode 3',
        'database_rollback -ne "passed"', 'database_rollback -ne "failed"', "db-cli-invoked",
    ):
        require(marker in db_rollback_ci, f"P10 Windows DB rollback CI missing drill: {marker}")

    for marker in (
        'job.get("status") != "healthy"', "installed_version", "installed_sequence", "update-finalize-report.json",
        '"finalization": "passed"', "windows_update_worker_entry.ps1", "windows_update_recovery.ps1",
        "INTERRUPTION_WINDOW_MISSED", '"interrupted_state"', '"reinstall_attempted": False',
        "P10_WINDOWS_INTERRUPTION_RECOVERY=SUCCESS", '"production_wiring_claim"] = "WINDOWS_ENTRY_AND_RECOVERY_ASSERTED"',
    ):
        require(marker in packaged_finalization_ci, f"P10 packaged finalization/recovery CI missing marker: {marker}")

    for marker in (
        "Windows PowerShell 5.1 external worker contract", "WindowsPowerShell\\v1.0\\powershell.exe",
        "P10_WINDOWS_POWERSHELL=5.1", "windows_update_worker_entry.ps1", "windows_update_recovery.ps1",
        "backend/services/update_recovery.py", "test_update_recovery.py", "interruption recovery",
        "p10_windows_db_rollback_ci.ps1", "p10_windows_packaged_finalization_ci.py",
        "backend/services/update_finalize.py", "test_update_db_rollback.py", "test_update_apply.py",
        "backend/services/update_apply.py", "backend/routers/update_portability_p10.py", "windows-update-recovery.log",
        "db-rollback-state.json", "update-finalize-report.json", "trusted_state.json",
    ):
        require(marker in workflow, f"P10 workflow missing marker: {marker}")

    require("private key" in doc.lower(), "P10 doc must state private-key handling")
    require("0 EP" in doc, "P10 remains open until packaged apply/rollback certification")
    require("P6/P7" in doc, "P10 doc must state packaging dependency")
    require("package self-test" in doc.lower(), "P10 doc must state exact packaged VERSION proof")
    require("/health" in doc, "P10 doc must state runtime health proof")
    require("program snapshot" in doc.lower(), "P10 doc must state Windows program rollback")
    require("uninstall registry" in doc.lower(), "P10 doc must state Windows uninstall metadata rollback")
    require("Windows PowerShell 5.1" in doc, "P10 doc must state native Windows PowerShell 5.1 runtime")
    require("old packaged executable" in doc.lower(), "P10 doc must state old-package DB rollback ownership")
    require("PostgreSQL" in doc, "P10 doc must state PostgreSQL DB rollback boundary")
    require("interrupted" in doc.lower(), "P10 doc must state interruption recovery contract")
    print("P10_UPDATE_CONTRACT=SUCCESS installed_truth=FINALIZER_READY windows_worker=PS51_DB_ROLLBACK_READY interruption_recovery=CONTRACT_READY production_wiring=FAIL_CLOSED")


if __name__ == "__main__":
    main()
