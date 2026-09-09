from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> None:
    required_workflows = {
        "portability-p5-native-cert.yml",
        "portability-p6-windows-packaging.yml",
        "portability-p7-macos-packaging.yml",
        "portability-p8-hardware-contract.yml",
        "portability-p9-dr-cert.yml",
        "portability-p10-update-engine.yml",
        "portability-p11-launcher-recovery.yml",
    }
    workflow_dir = ROOT / ".github" / "workflows"
    missing = sorted(name for name in required_workflows if not (workflow_dir / name).is_file())
    require(not missing, f"P12 upstream workflow missing: {missing}")

    required_docs = {
        "P8_HARDWARE_COMPATIBILITY_MATRIX.md",
        "P9_BACKUP_RECOVERY_DR.md",
        "P10_UPDATE_ENGINE.md",
        "P11_LAUNCHER_RECOVERY_UX.md",
        "PORTABILITY_P6_CLOSEOUT.md",
        "P12_CERTIFICATION_MATRIX.md",
    }
    doc_dir = ROOT / "docs" / "portability"
    missing_docs = sorted(name for name in required_docs if not (doc_dir / name).is_file())
    require(not missing_docs, f"P12 upstream evidence doc missing: {missing_docs}")

    matrix = (doc_dir / "P12_CERTIFICATION_MATRIX.md").read_text(encoding="utf-8")
    p8 = (doc_dir / "P8_HARDWARE_COMPATIBILITY_MATRIX.md").read_text(encoding="utf-8")
    p9 = (doc_dir / "P9_BACKUP_RECOVERY_DR.md").read_text(encoding="utf-8")
    p10 = (doc_dir / "P10_UPDATE_ENGINE.md").read_text(encoding="utf-8")
    p11 = (doc_dir / "P11_LAUNCHER_RECOVERY_UX.md").read_text(encoding="utf-8")
    p6 = (doc_dir / "PORTABILITY_P6_CLOSEOUT.md").read_text(encoding="utf-8")

    require("**Status:** CLOSED ✅ — **21 EP**" in p8, "P12 must consume closed P8")
    require(
        "No direct dental device is certified as `SUPPORTED`" in p8,
        "P12 must preserve P8 conservative hardware truth",
    )
    require("**Status:** CLOSED" in p9 and "8 EP credited" in p9, "P12 requires P9 CLOSED")
    for marker in (
        "4590e2975e71ca89fc404e96e717646155b8fc14",
        "33276520623",
        "9721759555",
        "9721742568",
    ):
        require(marker in p9, f"P12 missing P9 evidence: {marker}")

    for marker in (
        "P6/P7",
        "package self-test",
        "/health",
        "program snapshot",
        "uninstall registry",
        "Windows PowerShell 5.1",
        "old packaged executable",
        "PostgreSQL",
        "interrupted",
        "private key",
        "Clean Hosted",
    ):
        require(marker.lower() in p10.lower(), f"P12 must preserve P10 truth: {marker}")

    require("**Status:** CLOSED" in p11, "P12 requires P11 CLOSED")
    require("Status: **CLOSED / VERIFIED**" in p6, "P12 requires P6 CLOSED")
    require("FAIL_CLOSED_NO_WEIGHTS" in p6, "P12 requires P6 frozen scientific truth")

    closed = "**Status:** CLOSED" in matrix
    if closed:
        for marker in (
            "13 EP credited",
            "Core/runtime + single-instance | certified | certified | P2/P5 | CERTIFIED",
            "Frozen/package lifecycle | certified P6/private-PKI successor | certified P7 private distribution | P6/P7/P10 | CERTIFIED",
            "Scientific assets/runtime policy | native fail-closed + frozen `FAIL_CLOSED_NO_WEIGHTS` | native fail-closed + frozen `FAIL_CLOSED_NO_WEIGHTS` | P5/P6/P9 | CERTIFIED",
            "Hardware truth matrix | conservative boundary certified | conservative boundary certified | P8 | CERTIFIED",
            "Disaster recovery | certified macOS → Windows frozen restore | certified Windows → macOS frozen restore | P9 | CERTIFIED",
            "Authenticated update | certified signed current → next + rollback | certified private current → next + rollback | P10 | CERTIFIED",
            "Launcher/recovery UX | certified | certified shared UX | P11 | CERTIFIED",
            "Clean-machine technical E2E | certified on fresh Windows runners | certified on fresh Apple Silicon runners | P6/P7/P9/P10 | CERTIFIED",
            "32601811079",
            "32999393374",
            "33274684195",
            "33276520623",
            "33274684115",
            "33274684087",
            "33274684081",
            "32783305559",
            "P13 boundary retained",
            "No Vercel",
        ):
            require(marker in matrix, f"P12 CLOSED evidence missing: {marker}")
        print(
            "P12_CERTIFICATION_MATRIX=SUCCESS state=CLOSED ep=13 "
            "windows=CERTIFIED macos=CERTIFIED p9=AVAILABLE p13=SEPARATE_REAL_CABINET"
        )
        return

    for marker in (
        "0 EP credited",
        "Hardware truth matrix | certified conservative boundary | certified conservative boundary | P8 | AVAILABLE",
        "Frozen/package lifecycle | proved by P6 | proved by P7 private distribution | P6/P7 | AVAILABLE",
        "Update secure core | certified signed lifecycle | certified private lifecycle | P10 | AVAILABLE",
        "Any future `SUPPORTED` hardware claim still requires real-device evidence",
        "No Vercel",
    ):
        require(marker in matrix, f"P12 PREPARED truth marker missing: {marker}")
    print(
        "P12_CERTIFICATION_MATRIX_PREP=SUCCESS state=PREPARED ep=0 "
        "p7=AVAILABLE p10=AVAILABLE p9=AVAILABLE"
    )


if __name__ == "__main__":
    main()
