import base64
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from backend.services.device_identity import DeviceIdentityError, DeviceIdentityService


class _MachineProtector:
    def __init__(self, machine_marker: bytes):
        self.marker = machine_marker

    def protect(self, plaintext: bytes) -> bytes:
        return self.marker + b":" + plaintext[::-1]

    def unprotect(self, protected: bytes) -> bytes:
        prefix = self.marker + b":"
        if not protected.startswith(prefix):
            raise DeviceIdentityError("wrong machine")
        return protected[len(prefix):][::-1]


def _raw_public(public_b64url: str) -> bytes:
    return base64.urlsafe_b64decode(public_b64url + "=" * (-len(public_b64url) % 4))


def test_same_machine_reuses_same_cryptographic_device_id(tmp_path):
    key_path = tmp_path / "device_identity.bin"
    protector = _MachineProtector(b"machine-a")

    first = DeviceIdentityService(
        protector=protector,
        key_path=key_path,
        platform_kind="windows",
    ).get_identity()
    second = DeviceIdentityService(
        protector=protector,
        key_path=key_path,
        platform_kind="windows",
    ).get_identity()

    assert first == second
    assert key_path.exists()
    assert _raw_public(first.public_key_b64url) not in key_path.read_bytes()


def test_copying_protected_device_key_to_other_machine_fails_closed(tmp_path):
    source = tmp_path / "source" / "device_identity.bin"
    source_service = DeviceIdentityService(
        protector=_MachineProtector(b"machine-a"),
        key_path=source,
        platform_kind="windows",
    )
    source_identity = source_service.get_identity()

    destination = tmp_path / "destination" / "device_identity.bin"
    destination.parent.mkdir(parents=True)
    destination.write_bytes(source.read_bytes())

    cloned_service = DeviceIdentityService(
        protector=_MachineProtector(b"machine-b"),
        key_path=destination,
        platform_kind="windows",
    )
    with pytest.raises(DeviceIdentityError, match="cannot be recovered"):
        cloned_service.get_identity()

    fresh_destination = tmp_path / "fresh" / "device_identity.bin"
    fresh_identity = DeviceIdentityService(
        protector=_MachineProtector(b"machine-b"),
        key_path=fresh_destination,
        platform_kind="windows",
    ).get_identity()
    assert fresh_identity.device_id != source_identity.device_id


def test_possession_signature_matches_public_key(tmp_path):
    service = DeviceIdentityService(
        protector=_MachineProtector(b"machine-a"),
        key_path=tmp_path / "device_identity.bin",
        platform_kind="windows",
    )
    identity = service.get_identity()
    challenge = b"digital-crown-device-possession-v1"
    signature = service.sign_possession_challenge(challenge)

    public_key = Ed25519PublicKey.from_public_bytes(_raw_public(identity.public_key_b64url))
    public_key.verify(signature, challenge)


def test_device_identity_source_does_not_use_hardware_serial_fingerprints():
    source = Path("backend/services/device_identity.py").read_text(encoding="utf-8").lower()
    forbidden = (
        "wmic",
        "win32_bios",
        "serialnumber",
        "getnode()",
        "platform.node",
        "machineguid",
    )
    assert all(marker not in source for marker in forbidden)
