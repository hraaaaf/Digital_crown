"""F5B-D offline synthetic recovery proof: no secret or plaintext artifact."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, Path(filename))
    module = importlib.util.module_from_spec(spec)
    import sys
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


recovery = load("dc06_recovery", "backend/services/clinical_media_keyring_recovery.py")
media = load("dc06_media", "backend/services/clinical_media_crypto_v2.py")
data = {
    "active_media_id": "media2", "active_locator_id": "loc2",
    "media_keys": {"media1": "11" * 32, "media2": "22" * 32},
    "locator_keys": {"loc1": "33" * 32, "loc2": "44" * 32},
}
password = b"synthetic-offline-recovery-password-32-bytes"
sealed = recovery.seal_keyring(data, password)
assert b"media1" not in sealed and b"media2" not in sealed
assert sealed != recovery.seal_keyring(data, password)
restored = recovery.open_keyring(sealed, password)
assert restored == data
print("DC06_F5BD_ENCRYPTED_BACKUP_ROUNDTRIP_PASS")

def keyring(payload):
    return media.MediaKeyringV2(
        {k: bytes.fromhex(v) for k, v in payload["media_keys"].items()},
        {k: bytes.fromhex(v) for k, v in payload["locator_keys"].items()},
    )


before, after = keyring(data), keyring(restored)
plaintext = b"synthetic-dental-media-non-patient"
digest = hashlib.sha256(plaintext).hexdigest()
for media_id in ("media1", "media2"):
    envelope = before.encrypt(tenant=7, digest=digest, plaintext=plaintext,
                              media_key_id=media_id)
    assert after.decrypt(tenant=7, digest=digest, envelope=envelope) == plaintext
for locator_id in ("loc1", "loc2"):
    assert before.locator(tenant=7, digest=digest, locator_key_id=locator_id) == (
        after.locator(tenant=7, digest=digest, locator_key_id=locator_id)
    )
print("DC06_F5BD_RETAINED_MEDIA_LOCATOR_CONTINUITY_PASS")

for label, blob, secret in (
    ("wrong_password", sealed, b"synthetic-wrong-password-not-real"),
    ("tampered", sealed[:-1] + bytes([sealed[-1] ^ 1]), password),
    ("truncated", sealed[:35], password),
):
    try:
        recovery.open_keyring(blob, secret)
    except recovery.KeyringRecoveryDenied:
        print("DC06_F5BD_" + label.upper() + "_DENIED_PASS")
    else:
        raise AssertionError("RECOVERY_ACCEPTED_" + label)

invalid = dict(data)
invalid["media_keys"] = {"media2": "22" * 32}
invalid["active_media_id"] = "media1"
try:
    recovery.seal_keyring(invalid, password)
except recovery.KeyringRecoveryDenied:
    print("DC06_F5BD_MISSING_RETAINED_KEY_DENIED_PASS")
else:
    raise AssertionError("INVALID_KEYRING_BACKUP_ACCEPTED")
