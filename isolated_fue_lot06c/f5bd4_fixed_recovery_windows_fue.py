"""F5B-D4b: restore an independently PREBUILT public synthetic corpus on Windows.

The CI run NEVER seals its positive backup or computes its expected oracle.
The fixture is public/test-only; this is not offsite custody or a human DR drill.
"""
from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import types

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
FIXTURE = HERE / "f5bd4_fixed_synthetic_oracle.json"
PINNED_FIXTURE_SHA256 = "3de7f99acfba9b5bcc7df3394dc5272ace316c62c2331cd2e3091a80c257bd2e"


def fixture():
    raw = FIXTURE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == PINNED_FIXTURE_SHA256, "FIXTURE_DRIFT"
    data = json.loads(raw)
    assert data["schema"] == "dc06-f5bd4-fixed-synthetic-v1"
    assert data["provenance"] == "prebuilt-before-ci-run-2026-11-05-not-offsite-or-human-attested"
    envelope = base64.b64decode(data["envelope_b64"], validate=True)
    assert hashlib.sha256(envelope).hexdigest() == data["envelope_sha256"]
    assert len(data["media_vectors"]) == len(data["locator_vectors"]) == 2
    assert {v["media_key_id"] for v in data["media_vectors"]} == {"media1", "media2"}
    assert {v["locator_key_id"] for v in data["locator_vectors"]} == {"loc1", "loc2"}
    return data, envelope


def modules():
    # Avoid importing backend.__init__ (the standalone Windows job has no SQLAlchemy).
    for name in ("backend", "backend.services"):
        mod = types.ModuleType(name)
        mod.__path__ = [str(ROOT / name.replace(".", "/"))]
        sys.modules[name] = mod

    def load(name, path):
        spec = importlib.util.spec_from_file_location(name, ROOT / path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
        return mod

    load("backend.services.windows_keyring_handle_probe",
         "backend/services/windows_keyring_handle_probe.py")
    recovery = load("backend.services.clinical_media_keyring_recovery",
                    "backend/services/clinical_media_keyring_recovery.py")
    restore = load("backend.services.windows_keyring_restore",
                   "backend/services/windows_keyring_restore.py")
    product = load("backend.services.clinical_media_crypto_v2",
                   "backend/services/clinical_media_crypto_v2.py")
    return recovery, restore, product


def check_vectors(f, keyring, product, expect_missing=False):
    assert f["tenant"] == 7
    seen = set()
    for v in f["media_vectors"]:
        blob = base64.b64decode(v["envelope_b64"], validate=True)
        if expect_missing and v["media_key_id"] == "media1":
            try:
                keyring.decrypt(tenant=f["tenant"], digest=f["test_digest"], envelope=blob)
            except product.MediaCryptoV2Denied as exc:
                assert str(exc) == "KEY_UNAVAILABLE"
            else:
                raise AssertionError("MISSING_RETAINED_KEY_FALSE_PASS")
        else:
            plain = keyring.decrypt(tenant=f["tenant"], digest=f["test_digest"], envelope=blob)
            assert hashlib.sha256(plain).hexdigest() == v["plaintext_sha256"] == f["test_digest"]
            seen.add(v["media_key_id"])
            bad = blob[:-1] + bytes([blob[-1] ^ 1])
            try:
                keyring.decrypt(tenant=f["tenant"], digest=f["test_digest"], envelope=bad)
            except product.MediaCryptoV2Denied as exc:
                assert str(exc) == "AUTHENTICATION_FAILED"
            else:
                raise AssertionError("MEDIA_TAMPER_FALSE_PASS")
    if expect_missing:
        assert seen == {"media2"}
    else:
        assert seen == {"media1", "media2"}
    for v in f["locator_vectors"]:
        assert keyring.locator(
            tenant=f["tenant"], digest=f["test_digest"],
            locator_key_id=v["locator_key_id"]) == v["expected"]


def child(mode):
    f, _ = fixture()
    _, _, product = modules()
    ring, media_id, locator_id = product.configured_keyring()
    assert (media_id, locator_id) == (f["active_media_id"], f["active_locator_id"])
    check_vectors(f, ring, product, expect_missing=(mode == "missing"))
    if mode == "missing":
        print("DC06_F5BD4_RETAINED_MISSING_DENIED_PASS")
    else:
        print("DC06_F5BD4_FRESH_PROCESS_MEDIA_LOCATOR_ORACLE_PASS")


def deny(call, exception, expected):
    try:
        call()
    except exception as exc:
        assert str(exc) in expected, (str(exc), expected)
    else:
        raise AssertionError("NEGATIVE_FALSE_PASS")


def main():
    if os.name != "nt" or os.environ.get("DIGITALCROWN_ISOLATED_RUNTIME") != "true":
        raise RuntimeError("F5BD4_GITHUB_WINDOWS_LAB_ONLY")
    f, envelope = fixture()
    print("DC06_F5BD4_PRECOMMITTED_SHA_ORACLE_PASS")
    recovery, restore, _ = modules()
    pw = f["test_password_ascii"].encode("ascii")  # PUBLIC fake fixture password
    loaded = recovery.open_keyring(envelope, pw)
    assert loaded["active_media_id"] == f["active_media_id"]
    assert loaded["active_locator_id"] == f["active_locator_id"]
    assert set(loaded["media_keys"]) == {"media1", "media2"}
    assert set(loaded["locator_keys"]) == {"loc1", "loc2"}
    print("DC06_F5BD4_PREBUILT_BACKUP_AUTH_PASS")
    deny(lambda: recovery.open_keyring(envelope, b"wrong-public-synthetic-password"),
         recovery.KeyringRecoveryDenied, {"RECOVERY_AUTHENTICATION_FAILED"})
    deny(lambda: recovery.open_keyring(envelope[:-1] + bytes([envelope[-1] ^ 1]), pw),
         recovery.KeyringRecoveryDenied, {"RECOVERY_AUTHENTICATION_FAILED"})
    deny(lambda: recovery.open_keyring(envelope[:35], pw),
         recovery.KeyringRecoveryDenied, {"RECOVERY_ENVELOPE_INVALID"})

    root = Path(tempfile.mkdtemp(prefix="dc06-f5bd4-", dir=os.environ["RUNNER_TEMP"]))
    try:
        target = root / "recovered.json"
        raw = recovery._canonical(loaded)
        deny(lambda: restore.restore_new_private_file(str(root / "malformed.json"), b"{broken"),
             restore.WindowsRestoreDenied, {"RESTORE_KEYRING_INVALID"})
        assert not (root / "malformed.json").exists()
        restore.restore_new_private_file(str(target), raw)
        assert target.is_file()
        print("DC06_F5BD4_WINDOWS_CREATE_NEW_PRIVATE_PASS")
        previous_digest = hashlib.sha256(target.read_bytes()).hexdigest()
        deny(lambda: restore.restore_new_private_file(str(target), raw),
             restore.WindowsRestoreDenied, {"RESTORE_CREATE_NEW_DENIED"})
        assert hashlib.sha256(target.read_bytes()).hexdigest() == previous_digest
        deny(lambda: restore.restore_new_private_file("relative.json", raw),
             restore.WindowsRestoreDenied, {"RESTORE_PATH_DENIED"})

        env = dict(os.environ)
        env["DC_MEDIA_V2_KEYRING_FILE"] = str(target)
        subprocess.run([sys.executable, str(Path(__file__).resolve()), "readback"],
                       env=env, check=True)

        missing = dict(loaded)
        missing["media_keys"] = dict(missing["media_keys"])
        del missing["media_keys"]["media1"]
        missing_path = root / "missing-history.json"
        restore.restore_new_private_file(str(missing_path), recovery._canonical(missing))
        env["DC_MEDIA_V2_KEYRING_FILE"] = str(missing_path)
        subprocess.run([sys.executable, str(Path(__file__).resolve()), "missing"],
                       env=env, check=True)
        print("DC06_F5BD4_BACKUP_AND_RESTORE_NEGATIVES_PASS")
    finally:
        # Only synthetic GitHub runner temp; no production file or patient data.
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        main()
    elif len(sys.argv) == 2 and sys.argv[1] in ("readback", "missing"):
        child(sys.argv[1])
    else:
        raise RuntimeError("F5BD4_BAD_MODE")
