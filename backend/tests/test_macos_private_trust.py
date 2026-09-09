import json
import plistlib
from pathlib import Path

import pytest

import backend.services.macos_private_trust as private_trust
from backend.services.macos_private_trust import PRIVATE_TRUST_MODE
from backend.services.macos_update_apply import MacOSUpdateApplyService
from backend.services.macos_update_worker import MacOSUpdateWorker
from backend.services.update_engine import UpdateEngine, UpdatePreparationError
from backend.services.update_post_install import UpdatePostInstallError


def _app(tmp_path: Path, version: str = "1.0.1") -> Path:
    app = tmp_path / "DigitalCrown.app"
    exe = app / "Contents" / "MacOS" / "DigitalCrown"
    exe.parent.mkdir(parents=True)
    exe.write_bytes(b"binary")
    (app / "Contents" / "Info.plist").write_bytes(
        plistlib.dumps(
            {
                "CFBundleIdentifier": "com.saninova.digitalcrown",
                "CFBundleShortVersionString": version,
            }
        )
    )
    return app


def test_private_trust_accepts_only_verified_adhoc_bundle(monkeypatch, tmp_path):
    app = _app(tmp_path)
    calls = []

    def fake_run(args, error_code, timeout=120.0):
        calls.append((args, error_code))
        if "-d" in args:
            return "Executable=/tmp/DigitalCrown\nIdentifier=com.saninova.digitalcrown\nSignature=adhoc\n"
        return "valid on disk\nsatisfies its Designated Requirement\n"

    monkeypatch.setattr(MacOSUpdateApplyService, "_run_checked", staticmethod(fake_run))
    proof = MacOSUpdateApplyService._verify_app_bundle(app, expected_version="1.0.1")
    assert proof["trust_mode"] == PRIVATE_TRUST_MODE
    assert proof["private_codesign"] == "adhoc_valid"
    assert proof["developer_id"] == "not_required_private_distribution"
    assert any("--verify" in args for args, _ in calls)


def test_private_trust_rejects_unsigned_or_identity_signed_bundle(monkeypatch, tmp_path):
    app = _app(tmp_path)

    def fake_run(args, error_code, timeout=120.0):
        if "-d" in args:
            return "Identifier=com.saninova.digitalcrown\nSignature=Developer ID Application: Someone\n"
        return "ok"

    monkeypatch.setattr(MacOSUpdateApplyService, "_run_checked", staticmethod(fake_run))
    with pytest.raises(UpdatePreparationError, match="PRIVATE_ADHOC_SIGNATURE_REQUIRED"):
        MacOSUpdateApplyService._verify_app_bundle(app, expected_version="1.0.1")


def test_private_trust_rejects_wrong_bundle_or_version(monkeypatch, tmp_path):
    app = _app(tmp_path, version="1.0.0")
    monkeypatch.setattr(
        MacOSUpdateApplyService,
        "_run_checked",
        staticmethod(lambda *a, **k: "Signature=adhoc"),
    )
    with pytest.raises(UpdatePreparationError, match="BUNDLE_VERSION_MISMATCH"):
        MacOSUpdateApplyService._verify_app_bundle(app, expected_version="1.0.1")

    info = app / "Contents" / "Info.plist"
    info.write_bytes(
        plistlib.dumps(
            {
                "CFBundleIdentifier": "com.example.wrong",
                "CFBundleShortVersionString": "1.0.1",
            }
        )
    )
    with pytest.raises(UpdatePreparationError, match="BUNDLE_ID_MISMATCH"):
        MacOSUpdateApplyService._verify_app_bundle(app, expected_version="1.0.1")


def test_private_rescue_preflight_binds_self_test_to_manifest(monkeypatch, tmp_path):
    job_dir = tmp_path / "job"
    rescue_app = _app(job_dir / "rescue" / "program", version="1.0.0")
    manifest_sha = "a" * 64
    job = {"job_id": "b" * 32, "apply_certified": False}
    writes = []

    monkeypatch.setattr(UpdateEngine, "_job_dir", classmethod(lambda cls, job_id: job_dir))
    monkeypatch.setattr(
        UpdateEngine,
        "_write_job",
        classmethod(lambda cls, stored: writes.append(dict(stored))),
    )
    monkeypatch.setattr(
        private_trust,
        "verify_package_self_test",
        lambda *args, **kwargs: {"status": "ok"},
    )

    private_trust._certify_rescue_self_test(job, rescue_app, manifest_sha, "1.0.0")

    assert job["rescue_package_self_test"] == "passed"
    assert job["rescue_package_self_test_manifest_sha256"] == manifest_sha
    assert writes[-1]["rescue_package_self_test"] == "passed"


def test_private_rescue_preflight_failure_never_arms_apply(monkeypatch, tmp_path):
    job_dir = tmp_path / "job"
    rescue_app = _app(job_dir / "rescue" / "program", version="1.0.0")
    job = {"job_id": "c" * 32, "apply_certified": True}
    writes = []

    monkeypatch.setattr(UpdateEngine, "_job_dir", classmethod(lambda cls, job_id: job_dir))
    monkeypatch.setattr(
        UpdateEngine,
        "_write_job",
        classmethod(lambda cls, stored: writes.append(dict(stored))),
    )

    def fail_self_test(*args, **kwargs):
        raise UpdatePostInstallError("UPDATE_POST_INSTALL_SELF_TEST_FAILED")

    monkeypatch.setattr(private_trust, "verify_package_self_test", fail_self_test)

    with pytest.raises(UpdatePreparationError, match="RESCUE_SELF_TEST_FAILED"):
        private_trust._certify_rescue_self_test(job, rescue_app, "d" * 64, "1.0.0")

    assert job["apply_certified"] is False
    assert job["apply_blocker"] == "UPDATE_MACOS_RESCUE_SELF_TEST_FAILED"
    assert job["rescue_package_self_test"] == "failed"
    assert writes[-1]["apply_certified"] is False


def test_private_worker_requires_manifest_bound_rescue_preflight(tmp_path):
    with pytest.raises(UpdatePreparationError, match="RESCUE_SELF_TEST_REQUIRED"):
        MacOSUpdateWorker._validate_context(tmp_path, {})

    stale = {
        "rescue_package_self_test": "passed",
        "rescue_package_self_test_manifest_sha256": "a" * 64,
        "program_manifest_sha256": "b" * 64,
    }
    with pytest.raises(UpdatePreparationError, match="RESCUE_SELF_TEST_PROOF_STALE"):
        MacOSUpdateWorker._validate_context(tmp_path, stale)


def test_private_worker_reuses_only_exact_preflighted_rescue_self_test(tmp_path):
    job_dir = tmp_path / "job"
    rescue_app = job_dir / "rescue" / "program" / "DigitalCrown.app"
    rescue_app.mkdir(parents=True)
    manifest_sha = "e" * 64
    (job_dir / "job.json").write_text(
        json.dumps(
            {
                "current_version": "1.0.0",
                "rescue_app_filename": "rescue/program/DigitalCrown.app",
                "rescue_package_self_test": "passed",
                "rescue_package_self_test_manifest_sha256": manifest_sha,
                "program_manifest_sha256": manifest_sha,
            }
        ),
        encoding="utf-8",
    )

    assert MacOSUpdateWorker._self_test(rescue_app, "1.0.0", job_dir) is None


def test_private_target_staging_preserves_canonical_app_name(monkeypatch, tmp_path):
    mount = tmp_path / "mount"
    source = _app(mount, version="1.0.1")
    artifact = tmp_path / "target.dmg"
    artifact.write_bytes(b"dmg")
    install_parent = tmp_path / "Applications"
    install_parent.mkdir()

    class Mounted:
        def __enter__(self):
            return mount

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(
        MacOSUpdateApplyService,
        "_mounted_dmg",
        classmethod(lambda cls, dmg: Mounted()),
    )
    monkeypatch.setattr(
        MacOSUpdateApplyService,
        "_verify_app_bundle",
        classmethod(lambda cls, app, expected_version: {"version": expected_version}),
    )

    def fake_copy(cls, source_app, destination):
        destination.mkdir(parents=True)
        return []

    monkeypatch.setattr(
        MacOSUpdateApplyService,
        "_copy_bundle_verified",
        classmethod(fake_copy),
    )
    seen = []
    monkeypatch.setattr(
        MacOSUpdateWorker,
        "_self_test",
        classmethod(
            lambda cls, app, version, report_dir: seen.append(
                (Path(app), version, Path(report_dir))
            )
        ),
    )

    context = {
        "install_parent": install_parent,
        "artifact": artifact,
        "target_version": "1.0.1",
    }
    report_dir = tmp_path / "report"
    staged = private_trust._private_stage_target(
        MacOSUpdateWorker,
        context,
        "abc123",
        report_dir,
    )

    assert source.name == "DigitalCrown.app"
    assert staged.name == "DigitalCrown.app"
    assert staged.parent.name == ".digitalcrown-update-abc123"
    assert staged.parent.parent == install_parent
    assert seen == [(staged, "1.0.1", report_dir)]


def test_private_cleanup_removes_interrupted_staging_container(tmp_path):
    install_parent = tmp_path / "Applications"
    install_parent.mkdir()
    context = {"install_parent": install_parent}
    staging_root = private_trust._private_staging_root(context, "interrupted123")
    (staging_root / "DigitalCrown.app").mkdir(parents=True)

    private_trust._cleanup_private_staging(context, "interrupted123")

    assert not staging_root.exists()


def test_private_apply_cleans_staging_container(monkeypatch, tmp_path):
    install_parent = tmp_path / "Applications"
    install_parent.mkdir()
    staging_root = install_parent / ".digitalcrown-update-job123"
    staging_root.mkdir()
    (staging_root / "sentinel").write_text("x", encoding="utf-8")

    monkeypatch.setattr(
        private_trust,
        "_ORIGINAL_WORKER_APPLY",
        lambda job_path, context, job, parent_pid: 0,
    )

    context = {"install_parent": install_parent}
    job = {"job_id": "job123"}
    assert (
        private_trust._private_apply(
            MacOSUpdateWorker,
            tmp_path / "job.json",
            context,
            job,
            1234,
        )
        == 0
    )
    assert not staging_root.exists()


def test_private_worker_persists_pre_mutation_failure(monkeypatch, tmp_path):
    job = {
        "job_id": "a" * 32,
        "status": "scheduled",
        "platform": "macos",
        "apply_certified": True,
    }
    job_path = tmp_path / "job.json"
    job_path.write_text("{}", encoding="utf-8")
    saved = []

    monkeypatch.setattr(
        MacOSUpdateWorker,
        "_load_job",
        classmethod(lambda cls, path: (job_path, tmp_path, job)),
    )
    monkeypatch.setattr(
        MacOSUpdateWorker,
        "_validate_context",
        classmethod(
            lambda cls, job_dir, stored: (_ for _ in ()).throw(
                UpdatePreparationError("UPDATE_TEST_CONTEXT_FAILURE")
            )
        ),
    )
    monkeypatch.setattr(
        MacOSUpdateWorker,
        "_save",
        classmethod(lambda cls, stored: saved.append(dict(stored))),
    )

    assert MacOSUpdateWorker.run(job_path, 1234) == 4
    assert saved[-1]["status"] == "failed_pre_apply"
    assert saved[-1]["worker_result"] == "blocked_before_mutation"
    assert saved[-1]["worker_failure_stage"] == "validate_context"
    assert saved[-1]["failure_reason"] == "UPDATE_TEST_CONTEXT_FAILURE"
