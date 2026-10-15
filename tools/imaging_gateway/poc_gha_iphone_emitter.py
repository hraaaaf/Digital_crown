"""LOT06-M synthetic GitHub Actions -> iPhone Ed25519 transport POC.

Ephemeral private signing key, never persisted. NOT a witness, durable CAS or
clinical authorization. Synthetic-only fixture, no patient data or network I/O.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path
import re
import secrets
import shutil

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

DOMAIN = b"DC06M|gha-to-iphone|synthetic-only|v1\0"
SHA40 = re.compile(r"[0-9a-f]{40}\Z")
MAX_PAYLOAD_BYTES = 4096


def canonical(message: dict) -> bytes:
    """Strict synthetic schema and deterministically serialized bytes."""
    if type(message) is not dict or set(message) != {
        "protocol", "authority_id", "epoch", "scope", "operation_id",
        "previous_sequence", "previous_mac", "next_sequence", "next_mac",
        "manifest_digest", "source_sha", "run_id", "decision",
    }:
        raise ValueError("SCHEMA_REFUSE")
    if (message["protocol"] != "DC06M-IPHONE-POC-v1"
            or message["authority_id"] != "github-actions-ephemeral-demo"
            or message["epoch"] != "SYNTHETIC_ONLY"
            or message["decision"] != "DEMO_NOT_AUTHORITY_ACK"
            or type(message["previous_sequence"]) is not int
            or message["previous_sequence"] != 4
            or type(message["next_sequence"]) is not int
            or message["next_sequence"] != 5
            or type(message["run_id"]) is not str
            or not re.fullmatch(r"[1-9][0-9]{0,19}", message["run_id"])
            or type(message["source_sha"]) is not str
            or not SHA40.fullmatch(message["source_sha"])):
        raise ValueError("SCHEMA_REFUSE")
    for key, length in (("scope", 32), ("operation_id", 32),
                        ("previous_mac", 64), ("next_mac", 64),
                        ("manifest_digest", 64)):
        if type(message[key]) is not str or not re.fullmatch(r"[0-9a-f]{" + str(length) + r"}", message[key]):
            raise ValueError("SCHEMA_REFUSE")
    payload = json.dumps(message, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("ascii")
    if len(payload) > MAX_PAYLOAD_BYTES:
        raise ValueError("SIZE_REFUSE")
    return DOMAIN + payload


def create_demo(source_sha: str, run_id: str) -> tuple[dict, str]:
    """Return signed public packet and out-of-artifact public key only."""
    key = Ed25519PrivateKey.generate()
    pub = key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)
    message = {
        "protocol": "DC06M-IPHONE-POC-v1",
        "authority_id": "github-actions-ephemeral-demo",
        "epoch": "SYNTHETIC_ONLY",
        "scope": secrets.token_hex(16),
        "operation_id": secrets.token_hex(16),
        "previous_sequence": 4,
        "previous_mac": "1" * 64,
        "next_sequence": 5,
        "next_mac": secrets.token_hex(32),
        "manifest_digest": hashlib.sha256(b"synthetic_fixture_no_patient_data_v1").hexdigest(),
        "source_sha": source_sha,
        "run_id": run_id,
        "decision": "DEMO_NOT_AUTHORITY_ACK",
    }
    payload = canonical(message)
    signature = key.sign(payload)
    packet = {
        "payload_b64": base64.b64encode(payload).decode("ascii"),
        "signature_b64": base64.b64encode(signature).decode("ascii"),
        "public_key_sha256": hashlib.sha256(pub).hexdigest(),
        "disclaimer": "Synthetic GitHub-to-iPhone transport only; not durable witness/CAS or clinical ACK",
    }
    return packet, base64.b64encode(pub).decode("ascii")


def verify_demo(packet: dict, public_key_b64: str, *, expected_sha: str, expected_run_id: str) -> dict:
    """Python negative-test oracle, NOT a freshness oracle."""
    if type(packet) is not dict or set(packet) != {
        "payload_b64", "signature_b64", "public_key_sha256", "disclaimer"
    }:
        raise ValueError("PACKET_REFUSE")
    try:
        pub = base64.b64decode(public_key_b64, validate=True)
        payload = base64.b64decode(packet["payload_b64"], validate=True)
        signature = base64.b64decode(packet["signature_b64"], validate=True)
        if (len(pub) != 32 or len(signature) != 64 or len(payload) > MAX_PAYLOAD_BYTES
                or hashlib.sha256(pub).hexdigest() != packet["public_key_sha256"]):
            raise ValueError("PIN_OR_SHAPE_REFUSE")
        Ed25519PublicKey.from_public_bytes(pub).verify(signature, payload)
        if not payload.startswith(DOMAIN):
            raise ValueError("DOMAIN_REFUSE")
        decoded = json.loads(payload[len(DOMAIN):].decode("ascii"))
        if canonical(decoded) != payload:
            raise ValueError("NON_CANONICAL_REFUSE")
        if decoded["source_sha"] != expected_sha or decoded["run_id"] != expected_run_id:
            raise ValueError("RUN_BINDING_REFUSE")
        return decoded
    except (InvalidSignature, TypeError, KeyError, UnicodeError, json.JSONDecodeError, OverflowError) as exc:
        raise ValueError("SIGNATURE_OR_FORMAT_REFUSE") from exc


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--summary", required=True, type=Path)
    args = parser.parse_args()
    packet, public_key = create_demo(args.source_sha, args.run_id)
    assert verify_demo(packet, public_key, expected_sha=args.source_sha, expected_run_id=args.run_id)
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / "receipt.json").write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    corrupt = dict(packet)
    raw = bytearray(base64.b64decode(packet["payload_b64"]))
    raw[-1] ^= 1
    corrupt["payload_b64"] = base64.b64encode(raw).decode("ascii")
    (args.out / "receipt_tampered.json").write_text(json.dumps(corrupt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    # DEMO only. Public key ships with signed receipt to simplify phone UX.
    # It is NOT independent issuer authentication, trusted pinning or witness CAS.
    (args.out / "public_key_b64.txt").write_text(public_key + "\n", encoding="ascii")
    (args.out / "receiver_bundle.json").write_text(
        json.dumps({
            "protocol": "DC06M-IPHONE-POC-BUNDLE-v1",
            "public_key_b64": public_key,
            "expected_sha": args.source_sha,
            "expected_run_id": args.run_id,
            "valid": packet,
            "tampered": corrupt,
            "trust_limit": "DEMO_ONLY_SELF_DISTRIBUTED_PUBKEY_NOT_INDEPENDENT_AUTHORITY",
        }, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    shutil.copyfile(Path(__file__).with_name("poc_gha_iphone_receiver.html"), args.out / "receiver.html")
    (args.out / "README.txt").write_text(
        "LOT06-M SYNTHETIC ED25519 DEMO - NO PATIENT DATA / NO CAS / NO CLINICAL ACK\n"
        "1. The artifact ZIP now includes public_key_b64.txt and receiver_bundle.json.\n"
        "2. Bundling key with receipt is a DEMO convenience, NOT independent pinning.\n"
        "3. Prefer the in-chat iPhone WebCrypto receiver preloaded with bundle.\n"
        "4. Valid must VERIFY; tampered must REJECT.\n"
        "5. Local HTML from iOS Files preview may block JS or crypto.subtle.\n"
        "6. Device gate only closes with actual observed iPhone results.\n",
        encoding="utf-8")
    with args.summary.open("a", encoding="utf-8") as s:
        s.write("\n## LOT06-M synthetic iPhone receipt POC\n\n")
        s.write("**TEST ONLY: no durable witness, no clinical ACK; private key ephemeral.**\n\n")
        s.write(f"- Workflow run: {args.run_id}\n- Source SHA: {args.source_sha}\n")
        s.write("- Copy the following PUBLIC KEY on GitHub run summary to iPhone verifier, NOT from artifact:\n\n")
        s.write(public_key + "\n\n")
        s.write("- Download artifact: dc06m-iphone-synthetic-receipt\n")
        s.write("- Good packet expected: SIGNATURE VERIFIED / SYNTHETIC ONLY.\n")
        s.write("- Tampered packet expected: REJECTED.\n")


if __name__ == "__main__":
    main()
