import base64
import hashlib
import importlib.util
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

import backend.services.update_engine as update_engine_module
from backend.core.paths import AppPaths
from backend.services.update_engine import UpdateEngine
from backend.services.update_prepare import UpdatePrepareService

ROOT = Path(__file__).resolve().parents[2]


def _load_script(name: str, relative: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


builder = _load_script("p10_build_update_manifest_payload", "scripts/p10_build_update_manifest_payload.py")
signer = _load_script("p10_sign_update_manifest_offline", "scripts/p10_sign_update_manifest_offline.py")


def _test_key():
    private = Ed25519PrivateKey.generate()
    public_raw = private.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    public_b64 = base64.b64encode(public_raw).decode("ascii")
    key_id = hashlib.sha256(public_raw).hexdigest()
    return private, public_b64, key_id


def _payload(*, key_version: str = "1.0.1"):
    now = datetime(2026, 8, 29, 20, 0, tzinfo=timezone.utc)
    payload = {
        "schema": 1,
        "sequence": 301,
        "version": key_version,
        "issued_at": now.isoformat().replace("+00:00", "Z"),
        "expires_at": (now + timedelta(hours=8)).isoformat().replace("+00:00", "Z"),
        "targets": [
            {
                "os": "windows",
                "arch": "amd64",
                "filename": "DigitalCrownSetup-1.0.1.exe",
                "size_bytes": 5,
                "sha256": hashlib.sha256(b"hello").hexdigest(),
                "url": "https://example.invalid/DigitalCrownSetup-1.0.1.exe",
            },
            {
                "os": "macos",
                "arch": "arm64",
                "filename": "DigitalCrown-1.0.1-arm64.dmg",
                "size_bytes": 5,
                "sha256": hashlib.sha256(b"hello").hexdigest(),
                "url": "https://example.invalid/DigitalCrown-1.0.1-arm64.dmg",
            },
        ],
    }
    return payload, now


def test_offline_signer_pinned_map_matches_runtime_trust_roots():
    runtime = {
        key_id: record["public_key_b64"]
        for key_id, record in update_engine_module.PINNED_UPDATE_KEYS.items()
        if record.get("status") == "active"
    }
    assert signer.PINNED_UPDATE_PUBLIC_KEYS == runtime


def test_offline_signed_envelope_verifies_through_pinned_runtime_without_key_injection(monkeypatch, tmp_path):
    private, public_b64, key_id = _test_key()
    monkeypatch.setattr(signer, "PINNED_UPDATE_PUBLIC_KEYS", {key_id: public_b64})
    monkeypatch.setattr(
        update_engine_module,
        "PINNED_UPDATE_KEYS",
        {key_id: {"public_key_b64": public_b64, "status": "active"}},
    )
    data = tmp_path / "data"
    data.mkdir()
    monkeypatch.setattr(AppPaths, "get_user_data_dir", staticmethod(lambda: data))

    payload, now = _payload()
    envelope = signer.sign_payload(payload, private, expected_key_id=key_id)
    raw = json.dumps(envelope, separators=(",", ":")).encode("utf-8")

    verified = UpdateEngine.verify_manifest(
        raw,
        now=now,
        platform_kind="windows",
        architecture="amd64",
        current_version="1.0.0",
    )
    assert verified["version"] == "1.0.1"
    assert verified["target"]["filename"] == "DigitalCrownSetup-1.0.1.exe"


def test_offline_signer_rejects_unpinned_private_key(monkeypatch):
    private, _, key_id = _test_key()
    monkeypatch.setattr(signer, "PINNED_UPDATE_PUBLIC_KEYS", {})
    payload, _ = _payload()
    with pytest.raises(signer.OfflineSigningError, match="PRIVATE_KEY_NOT_PINNED"):
        signer.sign_payload(payload, private, expected_key_id=key_id)


def test_manifest_builder_hashes_exact_cross_platform_packages(tmp_path):
    windows = tmp_path / "DigitalCrownSetup-1.0.1.exe"
    macos = tmp_path / "DigitalCrown-1.0.1-arm64.dmg"
    windows.write_bytes(b"windows-package")
    macos.write_bytes(b"mac-package")
    issued = datetime(2026, 8, 29, 21, 0, tzinfo=timezone.utc)

    payload = builder.build_payload(
        sequence=302,
        version="1.0.1",
        windows_artifact=windows,
        windows_url="https://example.invalid/windows",
        macos_artifact=macos,
        macos_url="https://example.invalid/macos",
        issued_at=issued,
        expires_hours=8,
    )

    targets = {target["os"]: target for target in payload["targets"]}
    assert targets["windows"]["arch"] == "amd64"
    assert targets["windows"]["sha256"] == hashlib.sha256(b"windows-package").hexdigest()
    assert targets["windows"]["size_bytes"] == len(b"windows-package")
    assert targets["macos"]["arch"] == "arm64"
    assert targets["macos"]["sha256"] == hashlib.sha256(b"mac-package").hexdigest()
    assert payload["expires_at"] == "2026-08-30T05:00:00Z"


def test_prepare_service_uses_pinned_verification_download_and_cleans_transient_staging(monkeypatch, tmp_path):
    update_root = tmp_path / "updates"
    update_root.mkdir()
    observed = {}
    verified = {
        "sequence": 303,
        "version": "1.0.1",
        "manifest_sha256": "a" * 64,
        "target": {
            "os": "windows",
            "arch": "amd64",
            "filename": "DigitalCrownSetup-1.0.1.exe",
            "size_bytes": 5,
            "sha256": hashlib.sha256(b"hello").hexdigest(),
            "url": "https://example.invalid/update.exe",
        },
    }

    def fake_verify(manifest_bytes):
        observed["manifest_bytes"] = manifest_bytes
        return verified

    def fake_download(manifest, job_id):
        observed["download_id"] = job_id
        observed["download_manifest"] = manifest
        path = update_root / "jobs" / job_id / manifest["target"]["filename"]
        path.parent.mkdir(parents=True)
        path.write_bytes(b"hello")
        return path

    def fake_prepare(manifest, *, artifact_path):
        observed["prepare_manifest"] = manifest
        observed["artifact_path"] = artifact_path
        return {
            "job_id": "b" * 32,
            "status": "prepared",
            "sequence": 303,
            "version": "1.0.1",
            "manifest_sha256": "a" * 64,
            "platform": "windows",
            "architecture": "amd64",
            "artifact_filename": "DigitalCrownSetup-1.0.1.exe",
            "apply_certified": False,
            "apply_blocker": "P6/P7_PACKAGED_INSTALLER_CERTIFICATION_REQUIRED",
        }

    monkeypatch.setattr(UpdateEngine, "root", staticmethod(lambda: update_root))
    monkeypatch.setattr(UpdateEngine, "verify_manifest", staticmethod(fake_verify))
    monkeypatch.setattr(UpdateEngine, "download_target", staticmethod(fake_download))
    monkeypatch.setattr(UpdateEngine, "prepare_update", staticmethod(fake_prepare))

    result = UpdatePrepareService.prepare_from_manifest({"signed": {}, "signature": {}})

    # fake_verify intentionally accepts only one positional argument. If the
    # service ever injects public_key_b64, this test fails immediately.
    assert result["job_id"] == "b" * 32
    assert observed["download_manifest"] is verified
    assert observed["prepare_manifest"] is verified
    assert not (update_root / "jobs" / observed["download_id"]).exists()


def test_update_routes_are_registered_in_frozen_application_surface():
    from backend.main import app

    routes = {(route.path, method) for route in app.routes for method in getattr(route, "methods", set())}
    assert ("/api/update/prepare", "POST") in routes
    assert ("/api/update/{job_id}/status", "GET") in routes
    assert ("/api/update/{job_id}/apply", "POST") in routes
