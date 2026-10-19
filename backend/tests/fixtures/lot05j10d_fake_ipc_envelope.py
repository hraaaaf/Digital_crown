"""LOT05/J10D: fail-closed *synthetic* IPC envelope validation.

Pure parser only. Does NOT authenticate Windows pipe peers, install a SCM worker,
verify RSA/JWT, authorize restore, or provide a production IPC transport.
"""
import json
import re
import time

MAX_FRAME = 1024
HEX32 = re.compile(r"[0-9a-f]{32}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
GEN = re.compile(r"g_[0-9a-f]{32}\Z")
PURPOSE = "LOT05J10D_FAKE_IPC_V1"

class IpcDenied(PermissionError):
    pass

def _unique(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise IpcDenied("DUPLICATE_FIELD")
        obj[key] = value
    return obj

def parse_frame(raw, *, expected_owner, expected_job, expected_generation,
                expected_manifest, now=None):
    """Validate a length-bounded, canonical JSON fake message; no side effects."""
    if type(raw) is not bytes or not (1 <= len(raw) <= MAX_FRAME):
        raise IpcDenied("FRAME_SIZE")
    try:
        text = raw.decode("utf-8", errors="strict")
        data = json.loads(text, object_pairs_hook=_unique,
                          parse_constant=lambda _: (_ for _ in ()).throw(IpcDenied("NONFINITE")))
    except (UnicodeError, ValueError, TypeError, RecursionError) as exc:
        raise IpcDenied("FRAME_JSON") from exc
    if type(data) is not dict or set(data) != {
        "purpose", "owner", "job", "generation", "manifest", "nonce", "expires"
    }:
        raise IpcDenied("FRAME_FIELDS")
    if (type(expected_owner) is not int or expected_owner <= 0 or
        type(expected_job) is not str or not HEX32.fullmatch(expected_job) or
        type(expected_generation) is not str or not GEN.fullmatch(expected_generation) or
        type(expected_manifest) is not str or not HEX64.fullmatch(expected_manifest)):
        raise IpcDenied("EXPECTED_SCOPE")
    if (data["purpose"] != PURPOSE or type(data["owner"]) is not int or
        data["owner"] != expected_owner or type(data["job"]) is not str or
        data["job"] != expected_job or type(data["generation"]) is not str or
        data["generation"] != expected_generation or type(data["manifest"]) is not str or
        data["manifest"] != expected_manifest):
        raise IpcDenied("FRAME_SCOPE")
    if type(data["nonce"]) is not str or not HEX32.fullmatch(data["nonce"]):
        raise IpcDenied("FRAME_NONCE")
    if type(data["expires"]) is not int:
        raise IpcDenied("FRAME_EXPIRY")
    instant = int(time.time()) if now is None else now
    if type(instant) is not int or data["expires"] <= instant or data["expires"] > instant + 90:
        raise IpcDenied("FRAME_EXPIRED")
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    if raw != canonical:
        raise IpcDenied("FRAME_NONCANONICAL")
    return data
