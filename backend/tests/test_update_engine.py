import base64
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from backend.core.paths import AppPaths
from backend.services.backup_service import BackupService
from backend.services.update_engine import (
    UpdateEngine,
    UpdatePreparationError,
    UpdateSecurityError,
    _canonical_json,
)


def _keys():
    private = Ed25519PrivateKey.generate()
    public_raw = private.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return private, base64.b64encode(public_raw).decode(), hashlib.sha256(public_raw).hexdigest()


def _envelope(private, keyid, *, sequence=1, version="1.0.1", expires_delta=timedelta(days=1),
              sha="0" * 64, size=5, url="https://example.invalid/update.bin", os_name="windows", arch="amd64"):
    now = datetime(2026, 8, 24, 12, 0, tzinfo=timezone.utc)
    signed = {
        "schema": 1,
        "sequence": sequence,
        "version": version,
        "issued_at": now.isoformat().replace("+00:00", "Z"),
        "expires_at": (now + expires_delta).isoformat().replace("+00:00", "Z"),
        "targets": [{
            "os": os_name,
            "arch": arch,
            "filename": "update.bin",
            "size_bytes": size,
            "sha256": sha,
            "url": url,
        }],
    }
    sig = private.sign(_canonical_json(signed))
    return json.dumps({
        "signed": signed,
        "signature": {"keyid": keyid, "algorithm": "ed25519", "sig": base64.b64encode(sig).decode()},
    }, separators=(",", ":")).encode(), now


def _patch_data(monkeypatch, tmp_path):
    data = tmp_path / "appdata"
    data.mkdir()
    monkeypatch.setattr(AppPaths, "get_user_data_dir", staticmethod(lambda: data))
    return data


def test_valid_manifest_and_exact_target(monkeypatch, tmp_path):
    _patch_data(monkeypatch, tmp_path)
    private, pub, keyid = _keys()
    raw, now = _envelope(private, keyid)
    result = UpdateEngine.verify_manifest(
        raw, public_key_b64=pub, now=now, platform_kind="windows",
        architecture="x86_64", current_version="1.0.0"
    )
    assert result["sequence"] == 1
    assert result["target"]["arch"] == "amd64"


def test_invalid_signature_rejected(monkeypatch, tmp_path):
    _patch_data(monkeypatch, tmp_path)
    private, pub, keyid = _keys()
    raw, now = _envelope(private, keyid)
    payload = json.loads(raw)
    payload["signed"]["version"] = "1.0.2"
    tampered = json.dumps(payload, separators=(",", ":")).encode()
    with pytest.raises(UpdateSecurityError, match="SIGNATURE"):
        UpdateEngine.verify_manifest(tampered, public_key_b64=pub, now=now, platform_kind="windows", architecture="amd64", current_version="1.0.0")


def test_expired_manifest_rejected(monkeypatch, tmp_path):
    _patch_data(monkeypatch, tmp_path)
    private, pub, keyid = _keys()
    raw, now = _envelope(private, keyid, expires_delta=timedelta(seconds=1))
    with pytest.raises(UpdateSecurityError, match="EXPIRED"):
        UpdateEngine.verify_manifest(raw, public_key_b64=pub, now=now + timedelta(seconds=2), platform_kind="windows", architecture="amd64", current_version="1.0.0")


def test_rollback_and_replay_conflict_rejected(monkeypatch, tmp_path):
    _patch_data(monkeypatch, tmp_path)
    private, pub, keyid = _keys()
    raw2, now = _envelope(private, keyid, sequence=2, version="1.0.2")
    UpdateEngine.verify_manifest(raw2, public_key_b64=pub, now=now, platform_kind="windows", architecture="amd64", current_version="1.0.0")

    raw1, _ = _envelope(private, keyid, sequence=1, version="1.0.1")
    with pytest.raises(UpdateSecurityError, match="ROLLBACK"):
        UpdateEngine.verify_manifest(raw1, public_key_b64=pub, now=now, platform_kind="windows", architecture="amd64", current_version="1.0.0")

    conflict, _ = _envelope(private, keyid, sequence=2, version="1.0.3")
    with pytest.raises(UpdateSecurityError, match="REPLAY_CONFLICT"):
        UpdateEngine.verify_manifest(conflict, public_key_b64=pub, now=now, platform_kind="windows", architecture="amd64", current_version="1.0.0")


def test_same_manifest_retry_allowed(monkeypatch, tmp_path):
    _patch_data(monkeypatch, tmp_path)
    private, pub, keyid = _keys()
    raw, now = _envelope(private, keyid, sequence=3, version="1.0.3")
    first = UpdateEngine.verify_manifest(raw, public_key_b64=pub, now=now, platform_kind="windows", architecture="amd64", current_version="1.0.0")
    second = UpdateEngine.verify_manifest(raw, public_key_b64=pub, now=now, platform_kind="windows", architecture="amd64", current_version="1.0.0")
    assert first["manifest_sha256"] == second["manifest_sha256"]


def test_platform_arch_mismatch_rejected(monkeypatch, tmp_path):
    _patch_data(monkeypatch, tmp_path)
    private, pub, keyid = _keys()
    raw, now = _envelope(private, keyid, os_name="macos", arch="arm64")
    with pytest.raises(UpdateSecurityError, match="TARGET_NOT_UNIQUE"):
        UpdateEngine.verify_manifest(raw, public_key_b64=pub, now=now, platform_kind="windows", architecture="amd64", current_version="1.0.0")


def test_http_target_rejected(monkeypatch, tmp_path):
    _patch_data(monkeypatch, tmp_path)
    private, pub, keyid = _keys()
    raw, now = _envelope(private, keyid, url="http://example.invalid/update.bin")
    with pytest.raises(UpdateSecurityError, match="HTTPS_REQUIRED"):
        UpdateEngine.verify_manifest(raw, public_key_b64=pub, now=now, platform_kind="windows", architecture="amd64", current_version="1.0.0")


def test_artifact_integrity_and_rescue_prepare(monkeypatch, tmp_path):
    data = _patch_data(monkeypatch, tmp_path)
    artifact = tmp_path / "update.bin"
    artifact.write_bytes(b"hello")
    private, pub, keyid = _keys()
    raw, now = _envelope(private, keyid, sha=hashlib.sha256(b"hello").hexdigest(), size=5)
    verified = UpdateEngine.verify_manifest(raw, public_key_b64=pub, now=now, platform_kind="windows", architecture="amd64", current_version="1.0.0")

    backups = data / "backups"
    backups.mkdir()
    rescue = backups / "db_backup_test.db.enc"
    rescue.write_bytes(b"rescue")
    rescue_sha = hashlib.sha256(b"rescue").hexdigest()
    monkeypatch.setattr(BackupService, "backup_active_database", staticmethod(lambda: {
        "status": "SUCCESS", "backup_filename": rescue.name, "checksum": rescue_sha
    }))

    job = UpdateEngine.prepare_update(verified, artifact_path=artifact)
    assert job["status"] == "prepared"
    assert job["rescue_backup_sha256"] == rescue_sha
    staged_rescue = data / "updates" / "jobs" / job["job_id"] / "rescue" / rescue.name
    assert staged_rescue.read_bytes() == b"rescue"
    rescue.unlink()
    assert staged_rescue.exists()
    assert job["apply_certified"] is False
    with pytest.raises(UpdatePreparationError, match="APPLY_NOT_CERTIFIED"):
        UpdateEngine.require_certified_apply(job["job_id"])


def test_artifact_hash_mismatch_rejected_before_rescue(monkeypatch, tmp_path):
    _patch_data(monkeypatch, tmp_path)
    artifact = tmp_path / "update.bin"
    artifact.write_bytes(b"wrong")
    private, pub, keyid = _keys()
    raw, now = _envelope(private, keyid, sha="0" * 64, size=5)
    verified = UpdateEngine.verify_manifest(raw, public_key_b64=pub, now=now, platform_kind="windows", architecture="amd64", current_version="1.0.0")
    monkeypatch.setattr(BackupService, "backup_active_database", staticmethod(lambda: pytest.fail("rescue must not run")))
    with pytest.raises(UpdateSecurityError, match="SHA256_MISMATCH"):
        UpdateEngine.prepare_update(verified, artifact_path=artifact)


def test_rescue_failure_aborts(monkeypatch, tmp_path):
    _patch_data(monkeypatch, tmp_path)
    artifact = tmp_path / "update.bin"
    artifact.write_bytes(b"hello")
    private, pub, keyid = _keys()
    raw, now = _envelope(private, keyid, sha=hashlib.sha256(b"hello").hexdigest(), size=5)
    verified = UpdateEngine.verify_manifest(raw, public_key_b64=pub, now=now, platform_kind="windows", architecture="amd64", current_version="1.0.0")
    monkeypatch.setattr(BackupService, "backup_active_database", staticmethod(lambda: {"status": "FAILED"}))
    with pytest.raises(UpdatePreparationError, match="RESCUE_BACKUP_FAILED"):
        UpdateEngine.prepare_update(verified, artifact_path=artifact)


def test_prepared_job_cannot_be_marked_healthy(monkeypatch, tmp_path):
    data = _patch_data(monkeypatch, tmp_path)
    artifact = tmp_path / "renamed.tmp"
    artifact.write_bytes(b"hello")
    private, pub, keyid = _keys()
    raw, now = _envelope(private, keyid, sha=hashlib.sha256(b"hello").hexdigest(), size=5)
    verified = UpdateEngine.verify_manifest(raw, public_key_b64=pub, now=now, platform_kind="windows", architecture="amd64", current_version="1.0.0")
    backups = data / "backups"
    backups.mkdir()
    rescue = backups / "db_backup_test.db.enc"
    rescue.write_bytes(b"rescue")
    rescue_sha = hashlib.sha256(b"rescue").hexdigest()
    monkeypatch.setattr(BackupService, "backup_active_database", staticmethod(lambda: {
        "status": "SUCCESS", "backup_filename": rescue.name, "checksum": rescue_sha
    }))
    job = UpdateEngine.prepare_update(verified, artifact_path=artifact)
    assert job["artifact_filename"] == "update.bin"
    with pytest.raises(UpdatePreparationError, match="JOB_STATE_INVALID"):
        UpdateEngine.mark_installed_healthy(job["job_id"])
