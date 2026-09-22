from __future__ import annotations

import argparse
import json
from pathlib import Path

from backend.services.patient_companion_remote_crypto import decrypt_and_verify, sign_and_encrypt

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "backend" / "tests" / "fixtures" / "patient_companion_remote_test_keys.json"


def _keys() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _public(value: dict) -> dict:
    return {key: item for key, item in value.items() if key != "d"}


def emit(path: Path) -> None:
    keys = _keys()
    payload = {
        "protocol_version": "dc-pc-remote-v1",
        "direction": "cabinet-to-patient",
        "proof": "python-jwcrypto-to-js-jose",
    }
    token = sign_and_encrypt(
        payload,
        sender_signing_private_jwk=keys["cabinet_signing"],
        recipient_encryption_public_jwk=_public(keys["patient_encryption"]),
        sender_signing_kid=keys["cabinet_signing"]["kid"],
        recipient_encryption_kid=keys["patient_encryption"]["kid"],
    )
    path.write_text(json.dumps({"token": token, "payload": payload}), encoding="utf-8")


def verify(path: Path) -> None:
    keys = _keys()
    data = json.loads(path.read_text(encoding="utf-8"))
    decoded = decrypt_and_verify(
        data["token"],
        recipient_encryption_private_jwk=keys["cabinet_encryption"],
        sender_signing_public_jwk=_public(keys["patient_signing"]),
        expected_sender_signing_kid=keys["patient_signing"]["kid"],
        expected_recipient_encryption_kid=keys["cabinet_encryption"]["kid"],
    )
    if decoded != data["payload"]:
        raise SystemExit("JS -> Python JOSE payload mismatch")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("emit", "verify"))
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    if args.mode == "emit":
        emit(args.path)
    else:
        verify(args.path)


if __name__ == "__main__":
    main()
