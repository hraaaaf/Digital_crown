"""LOT06-N synthetic checkpoint C negative-proof experiment — TEST ONLY.

No physical separation, durable C, WORM, immutable custody, remote freshness,
HSM, clinical integration, network service, or anti-rollback certification.
All lab signers and witness/anchor data share one test harness. A CURRENT
checkpoint from independent C is an UNPROVEN PRECONDITION in this laboratory.
"""
from __future__ import annotations

import base64
import binascii
from copy import deepcopy
import hashlib
import re
from dataclasses import dataclass

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey,
)

from tools.imaging_gateway.durable_cas_lab import (
    AUTHORITY, EPOCH, GENESIS_MAC, CasRefusal, canonical, signer_pub, verify_receipt,
)
from tools.imaging_gateway.independent_witness_lab import verify_response

DOMAIN = b"DC06N|checkpoint-C|synthetic-v1\0"
PROTOCOL = "DC06N_C_ANCHOR_SYNTHETIC_V1"
HEX32 = re.compile(r"[0-9a-f]{32}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
SCHEMA = frozenset({
    "protocol", "authority_id", "epoch", "scope", "witness_pin_sha256",
    "seq", "mac", "op_id", "receipt_sha256", "prev_checkpoint_sha256",
})


def _refuse(condition: bool, reason: str) -> None:
    if not condition:
        raise CasRefusal(reason)


def _hex(value: object, regex: re.Pattern[str]) -> bool:
    return type(value) is str and regex.fullmatch(value) is not None


def _packet_bytes(checkpoint: dict) -> bytes:
    _refuse(type(checkpoint) is dict and set(checkpoint) == SCHEMA,
            "C_CHECKPOINT_SCHEMA_REFUSE")
    _refuse(checkpoint["protocol"] == PROTOCOL and checkpoint["authority_id"] == AUTHORITY
            and checkpoint["epoch"] == EPOCH and _hex(checkpoint["scope"], HEX32)
            and _hex(checkpoint["witness_pin_sha256"], HEX64)
            and type(checkpoint["seq"]) is int and 0 <= checkpoint["seq"] <= 256
            and _hex(checkpoint["mac"], HEX64) and _hex(checkpoint["op_id"], HEX32)
            and _hex(checkpoint["receipt_sha256"], HEX64)
            and _hex(checkpoint["prev_checkpoint_sha256"], HEX64),
            "C_CHECKPOINT_FIELDS_REFUSE")
    return DOMAIN + canonical(checkpoint)


def verify_anchor(packet: dict, c_pin: bytes, b_pin: bytes, scope: str) -> dict:
    """Authenticates historical C authorship, NOT whether C is still current."""
    _refuse(type(packet) is dict and set(packet) == {"checkpoint", "signature_b64"},
            "C_ANCHOR_PACKET_REFUSE")
    _refuse(type(c_pin) is bytes and len(c_pin) == 32
            and type(b_pin) is bytes and len(b_pin) == 32
            and _hex(scope, HEX32), "C_PIN_REFUSE")
    message = _packet_bytes(packet["checkpoint"])
    signature = packet["signature_b64"]
    _refuse(type(signature) is str and len(signature) <= 128, "C_SIGNATURE_SHAPE_REFUSE")
    try:
        raw = base64.b64decode(signature, validate=True)
        Ed25519PublicKey.from_public_bytes(c_pin).verify(raw, message)
    except (InvalidSignature, ValueError, binascii.Error, TypeError) as exc:
        raise CasRefusal("C_SIGNATURE_REFUSE") from exc
    proof = packet["checkpoint"]
    _refuse(proof["scope"] == scope
            and proof["witness_pin_sha256"] == hashlib.sha256(b_pin).hexdigest()
            and (proof["seq"] != 0 or
                 (proof["mac"] == GENESIS_MAC and proof["op_id"] == "0" * 32
                  and proof["receipt_sha256"] == "0" * 64
                  and proof["prev_checkpoint_sha256"] == "0" * 64)),
            "C_ANCHOR_BINDING_REFUSE")
    return proof


@dataclass(frozen=True)
class AnchorDecision:
    status: str
    witness_seq: int | None = None
    checkpoint_seq: int | None = None


def classify_verified_head(witness_packet: dict | None, fresh_head_request: dict,
                           c_packet: dict | None, b_pin: bytes, c_pin: bytes) -> AnchorDecision:
    """Signed HEAD and signed C checkpoint agreement, conditional on trusted CURRENT C.

    Caller-supplied/stale C packet can still be replayed. MATCH is NOT a freshness
    certificate and C's genuine independent high-watermark is NEVER proved here.
    """
    _refuse(type(fresh_head_request) is dict
            and fresh_head_request.get("method") == "HEAD", "C_EXPECT_HEAD_REFUSE")
    if witness_packet is None or c_packet is None:
        return AnchorDecision("UNKNOWN_NO_INDEPENDENT_CURRENT_C_LAB")
    witness = verify_response(witness_packet, b_pin, fresh_head_request)
    _refuse(witness["status"] == "HEAD_ONLY", "C_EXPECT_HEAD_RESPONSE_REFUSE")
    checkpoint = verify_anchor(c_packet, c_pin, b_pin, fresh_head_request["scope"])
    if witness["seq"] < checkpoint["seq"]:
        return AnchorDecision("B_ROLLBACK_DETECTED_LAB", witness["seq"], checkpoint["seq"])
    if witness["seq"] > checkpoint["seq"]:
        return AnchorDecision("PENDING_C_ANCHOR_LAB", witness["seq"], checkpoint["seq"])
    if witness["mac"] != checkpoint["mac"]:
        return AnchorDecision("SAME_SEQ_FORK_REFUSED_LAB", witness["seq"], checkpoint["seq"])
    return AnchorDecision("MATCH_LAB_NOT_GLOBAL_FRESHNESS", witness["seq"], checkpoint["seq"])


class SyntheticCheckpointC:
    """Volatile, single-process, disposable C fixture. NOT a trusted durable store."""

    def __init__(self, scope: str, witness_pin: bytes,
                 signer: Ed25519PrivateKey):
        _refuse(_hex(scope, HEX32) and type(witness_pin) is bytes
                and len(witness_pin) == 32
                and isinstance(signer, Ed25519PrivateKey), "C_ENROLLMENT_REFUSE")
        self.scope, self.witness_pin, self.signer = scope, witness_pin, signer
        self._head_seq, self._head_mac = 0, GENESIS_MAC
        self._ops: dict[str, tuple[bytes, dict]] = {}
        self._previous_sha = "0" * 64
        self._latest = self._sign("0" * 32, "0" * 64, self._previous_sha)

    def _sign(self, op_id: str, receipt_sha: str, prev_sha: str,\n              *, seq: int | None = None, mac: str | None = None) -> dict:
        body = {
            "protocol": PROTOCOL, "authority_id": AUTHORITY, "epoch": EPOCH,
            "scope": self.scope,
            "witness_pin_sha256": hashlib.sha256(self.witness_pin).hexdigest(),
            "seq": self._head_seq if seq is None else seq,\n            "mac": self._head_mac if mac is None else mac,
            "op_id": op_id, "receipt_sha256": receipt_sha,
            "prev_checkpoint_sha256": prev_sha,
        }
        packet = {
            "checkpoint": body,
            "signature_b64": base64.b64encode(self.signer.sign(_packet_bytes(body))).decode("ascii"),
        }
        return packet

    @property
    def latest(self) -> dict:
        # A real C client must authenticate a FRESH response over its enrolled pin.
        # This direct getter has no independent provenance or freshness.
        return {"checkpoint": dict(self._latest["checkpoint"]),
                "signature_b64": self._latest["signature_b64"]}

    def anchor(self, receipt: bytes) -> dict:
        """Advance C only for exact next witness receipt; no clinical authorization."""
        _refuse(type(receipt) is bytes and len(receipt) <= 4096,
                "C_RECEIPT_SIZE_REFUSE")
        body = verify_receipt(receipt, self.witness_pin)
        _refuse(body["authority_id"] == AUTHORITY and body["epoch"] == EPOCH
                and body["scope"] == self.scope and _hex(body["op_id"], HEX32)
                and type(body["before_seq"]) is int and type(body["after_seq"]) is int,
                "C_RECEIPT_IDENTITY_REFUSE")
        op_id = body["op_id"]
        if op_id in self._ops:
            old_receipt, old_packet = self._ops[op_id]
            _refuse(old_receipt == receipt, "C_OP_ID_REBIND_REFUSE")
            return deepcopy(old_packet)
        _refuse(body["before_seq"] == self._head_seq
                and body["before_mac"] == self._head_mac
                and body["after_seq"] == self._head_seq + 1
                and _hex(body["after_mac"], HEX64),
                "C_STALE_FORK_OR_GAP_REFUSE")
        _refuse(self._head_seq < 256, "C_ANCHOR_LIMIT_REFUSE")
        previous_sha = hashlib.sha256(canonical(self._latest)).hexdigest()
        self._head_seq, self._head_mac = body["after_seq"], body["after_mac"]
        result = self._sign(op_id, hashlib.sha256(receipt).hexdigest(), previous_sha)
        # This is ONLY in-process ordering, not an atomic/durable C/WORM proof.
        self._ops[op_id] = (receipt, result)
        self._latest = result
        return deepcopy(result)
