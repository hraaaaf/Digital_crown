from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVICE = ROOT / "backend" / "services" / "update_engine.py"
DOC = ROOT / "docs" / "portability" / "P10_UPDATE_ENGINE.md"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> None:
    service = SERVICE.read_text(encoding="utf-8")
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
    require("private key" in doc.lower(), "P10 doc must state private-key handling")
    require("0 EP" in doc, "P10 remains open until packaged apply/rollback certification")
    require("P6/P7" in doc, "P10 doc must state packaging dependency")
    print("P10_UPDATE_CONTRACT=SUCCESS")


if __name__ == "__main__":
    main()
