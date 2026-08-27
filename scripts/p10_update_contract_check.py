from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVICE = ROOT / "backend" / "services" / "update_engine.py"
POST_INSTALL = ROOT / "backend" / "services" / "update_post_install.py"
RUN = ROOT / "run.py"
SPEC = ROOT / "DigitalCrown.spec"
DOC = ROOT / "docs" / "portability" / "P10_UPDATE_ENGINE.md"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> None:
    service = SERVICE.read_text(encoding="utf-8")
    post_install = POST_INSTALL.read_text(encoding="utf-8")
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

    require("private key" in doc.lower(), "P10 doc must state private-key handling")
    require("0 EP" in doc, "P10 remains open until packaged apply/rollback certification")
    require("P6/P7" in doc, "P10 doc must state packaging dependency")
    require("package self-test" in doc.lower(), "P10 doc must state exact packaged VERSION proof")
    require("/health" in doc, "P10 doc must state runtime health proof")
    print("P10_UPDATE_CONTRACT=SUCCESS post_install_truth=READY apply=BLOCKED")


if __name__ == "__main__":
    main()
