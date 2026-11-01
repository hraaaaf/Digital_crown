"""LOT06 C05B-03L: TEST-only durable signed synthetic HTTP receipt acknowledgement.

An HMAC with the synthetic device token authenticates the isolated LAB reply.
This is NOT independent server trust, PKI, TLS validation, or clinical clearance.
No product API imports or service activation; never infer patient identity here.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import tempfile

from tools.imaging_gateway.gateway import GatewayError

_FIELDS = ("receipt_id", "capture", "tenant", "patient", "device", "asset_id",
           "digest", "size", "lab_only", "clinical_receipt_authorized")


def _guard(collector) -> None:
    if (os.getenv("ENVIRONMENT") != "test"
            or os.getenv("DIGITALCROWN_ISOLATED_RUNTIME") != "true"
            or os.getenv("DC_V15_06_HTTP_ACK_LAB") != "1"):
        raise GatewayError("LAB_HTTP_ACK_DISABLED")
    # The collector itself MUST have been opened through a marked TEMP-only lab root.
    root = Path(collector.config.watch).parent
    temp = Path(tempfile.gettempdir()).resolve(strict=True)
    try:
        if not root.resolve(strict=True).parent.samefile(temp):
            # Nested fixture directories are valid: require strict ancestry.
            if not any(part.samefile(temp) for part in root.resolve(strict=True).parents):
                raise GatewayError("LAB_HTTP_ACK_UNSAFE_ROOT")
        marker = root / ".digitalcrown-imaging-lab-only"
        if marker.is_symlink() or marker.read_text(encoding="utf-8") != (
            "DIGITALCROWN_IMAGING_LAB_ONLY_V1\n"
        ):
            raise GatewayError("LAB_HTTP_ACK_MARKER_REQUIRED")
    except (OSError, ValueError):
        raise GatewayError("LAB_HTTP_ACK_UNSAFE_ROOT") from None


def _message(reply: dict) -> bytes:
    if not isinstance(reply, dict) or set(reply) != set(_FIELDS):
        raise GatewayError("LAB_HTTP_ACK_INVALID_FIELDS")
    if (type(reply["tenant"]) is not int or reply["tenant"] <= 0
            or type(reply["patient"]) is not int or reply["patient"] <= 0
            or type(reply["asset_id"]) is not int or reply["asset_id"] <= 0
            or type(reply["size"]) is not int or reply["size"] <= 0
            or reply["lab_only"] is not True
            or reply["clinical_receipt_authorized"] is not False
            or not isinstance(reply["receipt_id"], str)
            or re.fullmatch(r"LAB-ONLY-[0-9a-f]{32}", reply["receipt_id"]) is None
            or not isinstance(reply["capture"], str)
            or re.fullmatch(r"[A-Za-z0-9_-]{1,128}", reply["capture"]) is None
            or not isinstance(reply["device"], str)
            or re.fullmatch(r"[A-Za-z0-9_-]{1,64}", reply["device"]) is None
            or not isinstance(reply["digest"], str)
            or re.fullmatch(r"[0-9a-f]{64}", reply["digest"]) is None):
        raise GatewayError("LAB_HTTP_ACK_INVALID_BINDING")
    return json.dumps(reply, sort_keys=True, separators=(",", ":")).encode("ascii")


def sign_lab_receipt(reply: dict, device_token: str) -> str:
    """Only the isolated TEST server fixture calls this signature helper."""
    if not isinstance(device_token, str) or not 16 <= len(device_token) <= 256:
        raise GatewayError("LAB_HTTP_ACK_INVALID_DEVICE_TOKEN")
    return hmac.new(device_token.encode("utf-8"), _message(reply), hashlib.sha256).hexdigest()


def record_lab_http_ack(
    collector, *, item_id: int, reply: dict, device_token: str,
    expected_capture: str, expected_device: str, expected_tenant: int,
    expected_patient: int,
) -> str:
    """Verify signed and byte-bound LAB receipt before one SQLite WAL commit."""
    _guard(collector)
    if type(item_id) is not int or item_id < 1:
        raise GatewayError("LAB_HTTP_ACK_INVALID_ITEM")
    if not isinstance(reply, dict) or "receipt_mac" not in reply:
        raise GatewayError("LAB_HTTP_ACK_SIGNATURE_REQUIRED")
    body = {key: value for key, value in reply.items() if key != "receipt_mac"}
    mac = reply["receipt_mac"]
    if not isinstance(mac, str) or re.fullmatch(r"[0-9a-f]{64}", mac) is None:
        raise GatewayError("LAB_HTTP_ACK_SIGNATURE_REQUIRED")
    expected_mac = sign_lab_receipt(body, device_token)
    if not hmac.compare_digest(mac, expected_mac):
        raise GatewayError("LAB_HTTP_ACK_SIGNATURE_MISMATCH")
    if (body["capture"] != expected_capture or body["device"] != expected_device
            or body["tenant"] != expected_tenant
            or body["patient"] != expected_patient):
        raise GatewayError("LAB_HTTP_ACK_SCOPE_CONFLICT")

    # AES-GCM + digest verify the REAL private spool before local confirmation.
    actual = collector.read_verified(item_id)
    digest = hashlib.sha256(actual).hexdigest()
    if digest != body["digest"] or len(actual) != body["size"]:
        raise GatewayError("LAB_HTTP_ACK_MEDIA_CONFLICT")

    with collector._db() as db:
        db.execute("BEGIN IMMEDIATE")
        db.execute("""
            CREATE TABLE IF NOT EXISTS c05b03l_lab_acks (
                item_id INTEGER PRIMARY KEY,
                capture TEXT NOT NULL UNIQUE,
                receipt_id TEXT NOT NULL UNIQUE,
                digest TEXT NOT NULL,
                size INTEGER NOT NULL
            )
        """)
        item = db.execute(
            "SELECT digest,size,state FROM items WHERE id=?", (item_id,)
        ).fetchone()
        if item is None or item[0] != digest or item[1] != len(actual):
            raise GatewayError("LAB_HTTP_ACK_ITEM_CHANGED")
        previous = db.execute(
            "SELECT capture,receipt_id,digest,size FROM c05b03l_lab_acks WHERE item_id=?",
            (item_id,),
        ).fetchone()
        binding = (body["capture"], body["receipt_id"], digest, len(actual))
        if previous is not None:
            if previous != binding or item[2] != "LAB_ACK_CONFIRMED":
                raise GatewayError("LAB_HTTP_ACK_REPLAY_CONFLICT")
            return body["receipt_id"]
        if item[2] not in ("PENDING_CONFIRMATION", "RETRY_PENDING"):
            raise GatewayError("LAB_HTTP_ACK_ITEM_NOT_PENDING")
        db.execute(
            "INSERT INTO c05b03l_lab_acks(item_id,capture,receipt_id,digest,size) "
            "VALUES(?,?,?,?,?)", (item_id, *binding),
        )
        changed = db.execute(
            "UPDATE items SET state='LAB_ACK_CONFIRMED' "
            "WHERE id=? AND digest=? AND size=? AND state IN "
            "('PENDING_CONFIRMATION','RETRY_PENDING')",
            (item_id, digest, len(actual)),
        )
        if changed.rowcount != 1:
            raise GatewayError("LAB_HTTP_ACK_STATE_CONFLICT")
        db.execute(
            "INSERT INTO audit(item_id,event,at) VALUES(?,?,strftime('%s','now'))",
            (item_id, "LAB_ACK_CONFIRMED"),
        )
    return body["receipt_id"]
