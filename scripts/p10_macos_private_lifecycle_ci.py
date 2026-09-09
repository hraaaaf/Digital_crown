from __future__ import annotations

import json
import plistlib
import sys
import time
from pathlib import Path

import p10_macos_signed_lifecycle_ci as lifecycle


PRIVATE_DISTRIBUTION = "signed_manifest_sha256+adhoc_codesign"
_ORIGINAL_PREPARE_JOB = lifecycle.prepare_job


def verify_private_app(app: Path, expected_version: str) -> None:
    info_path = app / "Contents" / "Info.plist"
    if not info_path.is_file():
        raise lifecycle.LifecycleError(f"INFO_PLIST_MISSING {info_path}")
    info = plistlib.loads(info_path.read_bytes())
    if info.get("CFBundleIdentifier") != "com.saninova.digitalcrown":
        raise lifecycle.LifecycleError(f"BUNDLE_ID_INVALID {info.get('CFBundleIdentifier')}")
    if str(info.get("CFBundleShortVersionString") or "") != expected_version:
        raise lifecycle.LifecycleError("BUNDLE_VERSION_INVALID")
    lifecycle.run_checked(
        ["/usr/bin/codesign", "--verify", "--deep", "--strict", "--verbose=4", str(app)],
        timeout=120,
    )
    detail = lifecycle.run_checked(
        ["/usr/bin/codesign", "-d", "--verbose=4", str(app)],
        timeout=120,
    )
    details = (detail.stdout or "") + (detail.stderr or "")
    if "Signature=adhoc" not in details:
        raise lifecycle.LifecycleError("PRIVATE_ADHOC_SIGNATURE_REQUIRED")
    if "Authority=Developer ID Application" in details:
        raise lifecycle.LifecycleError("PRIVATE_BUILD_MUST_NOT_CLAIM_DEVELOPER_ID")


def verify_private_distribution(dmg: Path, expected_version: str, mount_root: Path) -> None:
    with lifecycle.mounted_dmg(dmg, mount_root) as mount:
        verify_private_app(mount / lifecycle.APP_NAME, expected_version)


def prepare_private_job(**kwargs) -> Path:
    job_path = _ORIGINAL_PREPARE_JOB(**kwargs)
    payload = json.loads(job_path.read_text(encoding="utf-8"))
    job_dir = job_path.parent.resolve()
    rescue_rel = Path(str(payload.get("rescue_app_filename") or ""))
    if not str(rescue_rel) or rescue_rel.is_absolute() or ".." in rescue_rel.parts:
        raise lifecycle.LifecycleError("PRIVATE_RESCUE_PATH_INVALID")
    rescue_app = (job_dir / rescue_rel).resolve()
    try:
        rescue_app.relative_to(job_dir)
    except ValueError as exc:
        raise lifecycle.LifecycleError("PRIVATE_RESCUE_PATH_INVALID") from exc

    env = lifecycle.make_case_env(
        Path(kwargs["data_dir"]).resolve(),
        int(kwargs["port"]),
    )
    lifecycle.run_self_test(
        lifecycle.app_executable(rescue_app),
        str(payload.get("current_version") or ""),
        env,
        job_dir / "rescue-preflight-self-test.json",
    )
    manifest_sha = str(payload.get("program_manifest_sha256") or "").lower()
    if len(manifest_sha) != 64:
        raise lifecycle.LifecycleError("PRIVATE_RESCUE_MANIFEST_SHA_INVALID")
    payload["rescue_package_self_test"] = "passed"
    payload["rescue_package_self_test_manifest_sha256"] = manifest_sha
    payload["rescue_package_self_test_at"] = time.strftime(
        "%Y-%m-%dT%H:%M:%SZ",
        time.gmtime(),
    )
    job_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return job_path


def _report_arg() -> Path:
    try:
        idx = sys.argv.index("--report")
        return Path(sys.argv[idx + 1]).resolve()
    except (ValueError, IndexError) as exc:
        raise SystemExit("P10_MACOS_PRIVATE_REPORT_ARG_MISSING") from exc


def _rewrite_private_proof(report: Path) -> dict | None:
    if not report.is_file():
        return None
    proof = json.loads(report.read_text(encoding="utf-8"))
    proof["trust_mode"] = PRIVATE_DISTRIBUTION
    for key in ("baseline", "target"):
        if isinstance(proof.get(key), dict):
            proof[key]["distribution"] = PRIVATE_DISTRIBUTION
    proof["apple_developer_id_claim"] = False
    proof["apple_notarization_claim"] = False
    proof["rescue_preflight_policy"] = "required_before_worker"
    if proof.get("status") == "success":
        proof["rescue_preflight_self_test"] = "passed_all_cases"
    report.write_text(
        json.dumps(proof, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return proof


def main() -> None:
    lifecycle.verify_app = verify_private_app
    lifecycle.verify_distribution = verify_private_distribution
    lifecycle.prepare_job = prepare_private_job

    report = _report_arg()
    try:
        lifecycle.main()
    except Exception:
        proof = _rewrite_private_proof(report)
        if proof is not None:
            print("P10_MACOS_PRIVATE_FAILURE_PROOF=" + json.dumps(proof, sort_keys=True))
        raise

    proof = _rewrite_private_proof(report)
    if proof is None or proof.get("status") != "success":
        raise SystemExit("P10_MACOS_PRIVATE_LIFECYCLE_NOT_SUCCESS")
    if proof.get("rescue_preflight_self_test") != "passed_all_cases":
        raise SystemExit("P10_MACOS_PRIVATE_RESCUE_PREFLIGHT_NOT_PROVEN")
    print("P10_MACOS_PRIVATE_LIFECYCLE=SUCCESS")


if __name__ == "__main__":
    main()
