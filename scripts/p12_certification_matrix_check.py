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
    for marker in (
        "0 EP credited",
        "BLOCKED_MACOS",
        "OPEN_REAL_TARGET",
        "BLOCKED_PACKAGED_APPLY",
        "Hardware truth matrix | certified conservative boundary | certified conservative boundary | P8 | AVAILABLE",
        "P7 exact signed/notarized macOS artifact is not yet certified",
        "Any future `SUPPORTED` hardware claim still requires real-device evidence",
        "No Vercel",
    ):
        require(marker in matrix, f"P12 matrix truth marker missing: {marker}")

    p8 = (doc_dir / "P8_HARDWARE_COMPATIBILITY_MATRIX.md").read_text(encoding="utf-8")
    require("**Status:** CLOSED ✅ — **21 EP**" in p8, "P12 must consume the closed P8 compatibility boundary")
    require(
        "No direct dental device is certified as `SUPPORTED`" in p8,
        "P12 must preserve P8's conservative no-direct-support truth",
    )

    p9 = (doc_dir / "P9_BACKUP_RECOVERY_DR.md").read_text(encoding="utf-8")
    require("P9 does not close until" in p9, "P12 must preserve P9 real-target gate")

    p10 = (doc_dir / "P10_UPDATE_ENGINE.md").read_text(encoding="utf-8")
    require("apply_certified=false" in p10, "P12 must preserve P10 packaged-apply gate")

    print("P12_CERTIFICATION_MATRIX_PREP=SUCCESS state=PREPARED ep=0 p8=AVAILABLE")


if __name__ == "__main__":
    main()
