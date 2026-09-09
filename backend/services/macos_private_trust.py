from __future__ import annotations

import json
import plistlib
import shutil
import time
from pathlib import Path

from backend.services.macos_update_apply import (
    MACOS_APP_NAME,
    MACOS_BUNDLE_ID,
    MACOS_EXECUTABLE_REL,
    MacOSUpdateApplyService,
)
from backend.services.macos_update_worker import MacOSUpdateWorker
from backend.services.update_engine import UpdateEngine, UpdatePreparationError
from backend.services.update_post_install import (
    UpdatePostInstallError,
    verify_package_self_test,
)

PRIVATE_TRUST_MODE = "signed-manifest+adhoc-codesign-v1"

_ORIGINAL_SNAPSHOT_CURRENT_APP = MacOSUpdateApplyService._snapshot_current_app
_ORIGINAL_WORKER_VALIDATE_CONTEXT = MacOSUpdateWorker._validate_context
_ORIGINAL_WORKER_SELF_TEST = MacOSUpdateWorker._self_test
_ORIGINAL_WORKER_APPLY = MacOSUpdateWorker._apply


def _verify_private_app_bundle(cls, app: Path, *, expected_version: str) -> dict[str, str]:
    if not app.is_dir() or app.name != MACOS_APP_NAME:
        raise UpdatePreparationError("UPDATE_MACOS_DMG_APP_MISSING")
    info_path = app / "Contents" / "Info.plist"
    executable = app / MACOS_EXECUTABLE_REL
    if not info_path.is_file() or not executable.is_file():
        raise UpdatePreparationError("UPDATE_MACOS_BUNDLE_INVALID")
    try:
        info = plistlib.loads(info_path.read_bytes())
    except Exception as exc:
        raise UpdatePreparationError("UPDATE_MACOS_INFO_PLIST_INVALID") from exc
    if info.get("CFBundleIdentifier") != MACOS_BUNDLE_ID:
        raise UpdatePreparationError("UPDATE_MACOS_BUNDLE_ID_MISMATCH")
    if str(info.get("CFBundleShortVersionString") or "") != expected_version:
        raise UpdatePreparationError("UPDATE_MACOS_BUNDLE_VERSION_MISMATCH")
    cls._run_checked(
        ["/usr/bin/codesign", "--verify", "--deep", "--strict", "--verbose=4", str(app)],
        "UPDATE_MACOS_PRIVATE_CODESIGN_VERIFY_FAILED",
    )
    details = cls._run_checked(
        ["/usr/bin/codesign", "-d", "--verbose=4", str(app)],
        "UPDATE_MACOS_PRIVATE_CODESIGN_DETAILS_FAILED",
    )
    if "Signature=adhoc" not in details:
        raise UpdatePreparationError("UPDATE_MACOS_PRIVATE_ADHOC_SIGNATURE_REQUIRED")
    return {
        "bundle_id": MACOS_BUNDLE_ID,
        "version": expected_version,
        "developer_id": "not_required_private_distribution",
        "hardened_runtime": "not_claimed_private_distribution",
        "secure_timestamp": "not_required_private_distribution",
        "private_codesign": "adhoc_valid",
        "trust_mode": PRIVATE_TRUST_MODE,
    }


def _verify_private_distribution(cls, dmg: Path, *, expected_version: str) -> dict[str, str]:
    with cls._mounted_dmg(dmg) as mount:
        result = cls._verify_app_bundle(mount / MACOS_APP_NAME, expected_version=expected_version)
    result.update(
        notarization="not_required_private_distribution",
        gatekeeper="manual_first_launch_required",
    )
    return result


def _certify_rescue_self_test(
    job: dict,
    rescue_app: Path,
    manifest_sha: str,
    current_version: str,
) -> None:
    job_dir = UpdateEngine._job_dir(str(job["job_id"]))
    rescue_executable = rescue_app / MACOS_EXECUTABLE_REL
    if not rescue_executable.is_file():
        raise UpdatePreparationError("UPDATE_MACOS_RESCUE_EXECUTABLE_MISSING")
    try:
        verify_package_self_test(
            rescue_executable,
            expected_version=current_version,
            report_dir=job_dir,
            timeout=120,
        )
    except UpdatePostInstallError as exc:
        job.update(
            apply_certified=False,
            apply_blocker="UPDATE_MACOS_RESCUE_SELF_TEST_FAILED",
            rescue_package_self_test="failed",
        )
        UpdateEngine._write_job(job)
        raise UpdatePreparationError("UPDATE_MACOS_RESCUE_SELF_TEST_FAILED") from exc
    job.update(
        rescue_package_self_test="passed",
        rescue_package_self_test_manifest_sha256=manifest_sha,
        rescue_package_self_test_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    )
    UpdateEngine._write_job(job)


def _snapshot_private_current_app(cls, job: dict, install_app: Path) -> tuple[Path, str]:
    rescue_app, manifest_sha = _ORIGINAL_SNAPSHOT_CURRENT_APP(job, install_app)
    _certify_rescue_self_test(job, rescue_app, manifest_sha, cls._current_version())
    return rescue_app, manifest_sha


def _private_validate_context(cls, job_dir: Path, job: dict) -> dict:
    proof = str(job.get("rescue_package_self_test") or "")
    proof_manifest = str(job.get("rescue_package_self_test_manifest_sha256") or "").lower()
    manifest_sha = str(job.get("program_manifest_sha256") or "").lower()
    if proof != "passed":
        raise UpdatePreparationError("UPDATE_MACOS_RESCUE_SELF_TEST_REQUIRED")
    if len(proof_manifest) != 64 or proof_manifest != manifest_sha:
        raise UpdatePreparationError("UPDATE_MACOS_RESCUE_SELF_TEST_PROOF_STALE")
    return _ORIGINAL_WORKER_VALIDATE_CONTEXT(job_dir, job)


def _private_worker_self_test(cls, app: Path, version: str, report_dir: Path) -> None:
    job_dir = Path(report_dir).resolve()
    job_path = job_dir / "job.json"
    if job_path.is_file():
        try:
            job = json.loads(job_path.read_text(encoding="utf-8"))
            rescue_rel = Path(str(job.get("rescue_app_filename") or ""))
            if str(rescue_rel) and not rescue_rel.is_absolute() and ".." not in rescue_rel.parts:
                rescue_app = (job_dir / rescue_rel).resolve()
                if (
                    Path(app).resolve() == rescue_app
                    and str(version) == str(job.get("current_version") or "")
                ):
                    proof = str(job.get("rescue_package_self_test") or "")
                    proof_manifest = str(
                        job.get("rescue_package_self_test_manifest_sha256") or ""
                    ).lower()
                    manifest_sha = str(job.get("program_manifest_sha256") or "").lower()
                    if proof != "passed" or proof_manifest != manifest_sha:
                        raise UpdatePreparationError("UPDATE_MACOS_RESCUE_SELF_TEST_REQUIRED")
                    return
        except UpdatePreparationError:
            raise
        except Exception:
            pass
    return _ORIGINAL_WORKER_SELF_TEST(app, version, report_dir)


def _private_staging_root(context: dict, job_id: str) -> Path:
    return context["install_parent"] / f".digitalcrown-update-{job_id}"


def _cleanup_private_staging(context: dict, job_id: str) -> None:
    shutil.rmtree(_private_staging_root(context, job_id), ignore_errors=True)


def _private_stage_target(
    cls,
    context: dict,
    job_id: str,
    report_dir: Path,
) -> Path:
    """Stage the target on the install filesystem with a canonical .app leaf."""
    staging_root = _private_staging_root(context, job_id)
    staged = staging_root / MACOS_APP_NAME
    _cleanup_private_staging(context, job_id)
    staging_root.mkdir(parents=True)
    try:
        with MacOSUpdateApplyService._mounted_dmg(context["artifact"]) as mount:
            source = mount / MACOS_APP_NAME
            MacOSUpdateApplyService._verify_app_bundle(
                source,
                expected_version=context["target_version"],
            )
            MacOSUpdateApplyService._copy_bundle_verified(source, staged)
        cls._self_test(staged, context["target_version"], report_dir)
        return staged
    except Exception:
        shutil.rmtree(staging_root, ignore_errors=True)
        raise


def _private_apply(
    cls,
    job_path: Path,
    context: dict,
    job: dict,
    parent_pid: int,
) -> int:
    job_id = str(job["job_id"])
    try:
        return _ORIGINAL_WORKER_APPLY(job_path, context, job, parent_pid)
    finally:
        _cleanup_private_staging(context, job_id)


def install_private_macos_trust_policy() -> None:
    MacOSUpdateApplyService._verify_app_bundle = classmethod(_verify_private_app_bundle)
    MacOSUpdateApplyService._verify_macos_distribution = classmethod(_verify_private_distribution)


def install_private_macos_rescue_preflight() -> None:
    if getattr(MacOSUpdateWorker, "_private_rescue_preflight_installed", False):
        return
    MacOSUpdateApplyService._snapshot_current_app = classmethod(_snapshot_private_current_app)
    MacOSUpdateWorker._validate_context = classmethod(_private_validate_context)
    MacOSUpdateWorker._self_test = classmethod(_private_worker_self_test)
    MacOSUpdateWorker._stage_target = classmethod(_private_stage_target)
    MacOSUpdateWorker._apply = classmethod(_private_apply)
    MacOSUpdateWorker._private_rescue_preflight_installed = True


def install_private_macos_worker_diagnostics() -> None:
    from backend.core.platform import get_platform_adapter

    if getattr(MacOSUpdateWorker, "_private_diagnostics_installed", False):
        return

    def _run(cls, job_path: Path, parent_pid: int, *, recovery: bool = False) -> int:
        lock = None
        job = None
        stage = "load_job"
        try:
            resolved, job_dir, job = cls._load_job(job_path)
            stage = "validate_context"
            context = cls._validate_context(job_dir, job)
            stage = "lock"
            lock = get_platform_adapter().try_acquire_process_lock(job_dir / "worker.lock")
            if lock is None:
                return 5
            stage = "cleanup_staging"
            _cleanup_private_staging(context, str(job["job_id"]))
            stage = "recover" if recovery else "apply"
            if recovery:
                return cls._recover(resolved, context, job, parent_pid)
            return cls._apply(resolved, context, job, parent_pid)
        except Exception as exc:
            if job is not None:
                reason = (str(exc) or type(exc).__name__)[:512]
                if not recovery and str(job.get("status") or "") == "scheduled":
                    job.update(
                        status="failed_pre_apply",
                        worker_result="blocked_before_mutation",
                        failure_reason=reason,
                    )
                else:
                    job["worker_failure_reason"] = reason
                job["worker_failure_stage"] = stage
                try:
                    cls._save(job)
                except Exception:
                    pass
            return 4
        finally:
            if lock is not None:
                lock.release()

    MacOSUpdateWorker.run = classmethod(_run)
    MacOSUpdateWorker._private_diagnostics_installed = True


install_private_macos_trust_policy()
install_private_macos_rescue_preflight()
install_private_macos_worker_diagnostics()
