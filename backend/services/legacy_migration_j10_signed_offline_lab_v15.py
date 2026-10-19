"""J10 dormant RSA-authorized CLONE of an already verified synthetic generation."""
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import time
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from backend.services.legacy_migration_safe_restore_lab_v15 import (
    FakeRecoveryDenied, read_fake_current, clone_current_into_new_fake_dir)

FLAG = "LOT05J10_SIGNED_OFFLINE_FAKE_ONLY"
PURPOSE = "LOT05J10_OFFLINE_GENERATION_FAKE_ONLY"
CLAIMS = {"v", "purpose", "owner", "job", "generation", "manifest", "nonce", "issued", "expires"}
H32 = re.compile(r"[0-9a-f]{32}\Z")
H64 = re.compile(r"[0-9a-f]{64}\Z")
GEN = re.compile(r"g_[0-9a-f]{32}\Z")

class J10Denied(FakeRecoveryDenied):
    pass

def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")

def digest(record):
    return hashlib.sha256(canonical(record["manifest"])).hexdigest()

def unique(items):
    result = {}
    for k, v in items:
        if k in result:
            raise J10Denied("DUPLICATE_TICKET_FIELD")
        result[k] = v
    return result

def _claims(ticket, pin):
    if type(ticket) is not bytes or len(ticket) > 8192 or type(pin) is not bytes or len(pin) > 4096:
        raise J10Denied("INPUT_TYPE_OR_SIZE")
    try:
        envelope = json.loads(ticket.decode("ascii"), object_pairs_hook=unique)
        if type(envelope) is not dict or set(envelope) != {"claims", "signature"}:
            raise J10Denied("TICKET_FIELDS")
        claims = envelope["claims"]
        if type(claims) is not dict or set(claims) != CLAIMS:
            raise J10Denied("CLAIMS_FIELDS")
        sig = envelope["signature"]
        if type(sig) is not str or len(sig) > 400:
            raise J10Denied("SIGNATURE_FORMAT")
        key = serialization.load_pem_public_key(pin)
        if not isinstance(key, rsa.RSAPublicKey) or key.key_size != 2048:
            raise J10Denied("PUBLIC_PIN_UNSUPPORTED")
        binary = base64.b64decode(sig, validate=True)
        if len(binary) != 256:
            raise J10Denied("SIGNATURE_SIZE")
        key.verify(binary, canonical(claims), padding.PKCS1v15(), hashes.SHA256())
    except (UnicodeError, ValueError, TypeError, InvalidSignature) as exc:
        raise J10Denied("SIGNATURE_OR_FORMAT_DENIED") from exc
    return claims

def clone_signed_fake(root, destination, *, ticket, public_pin, expected_owner, job_id):
    """This can NEVER apply an active backup, only clone fake source into temporary folder."""
    if (os.getenv(FLAG) != "1" or not isinstance(root, Path)
            or not root.is_absolute() or not root.is_dir() or root.is_symlink()
            or not root.name.startswith("lot05j_fake_")
            or root.parent.resolve(strict=True) != Path(tempfile.gettempdir()).resolve(strict=True)):
        raise J10Denied("DISPOSABLE_TEMP_ROOT_REQUIRED")
    if (type(expected_owner) is not int or expected_owner <= 0
            or type(job_id) is not str or not H32.fullmatch(job_id)):
        raise J10Denied("TRUSTED_LAB_OWNER_AND_JOB_REQUIRED")
    if (not isinstance(destination, Path) or destination.parent != root
            or destination.name != "isolated-recovery" or destination.exists()
            or destination.is_symlink()):
        raise J10Denied("NEW_ISOLATED_DESTINATION_REQUIRED")
    c = _claims(ticket, public_pin)
    now = int(time.time())
    if (type(c["v"]) is not int or c["v"] != 1 or c["purpose"] != PURPOSE
            or type(c["owner"]) is not int or c["owner"] != expected_owner
            or c["job"] != job_id
            or type(c["generation"]) is not str or not GEN.fullmatch(c["generation"])
            or type(c["manifest"]) is not str or not H64.fullmatch(c["manifest"])
            or type(c["nonce"]) is not str or not H32.fullmatch(c["nonce"])
            or type(c["issued"]) is not int or type(c["expires"]) is not int
            or c["issued"] > now or c["issued"] < now-120
            or c["expires"] <= now or c["expires"] > now+120
            or c["expires"]-c["issued"] > 120):
        raise J10Denied("SIGNED_SCOPE_DENIED")
    _,record=read_fake_current(root, request_owner=expected_owner, expected_owner=expected_owner)
    if c["generation"] != record["generation"] or c["manifest"] != digest(record):
        raise J10Denied("SIGNED_MANIFEST_MISMATCH")
    ledger = root / "consumed-nonces"
    if ledger.is_symlink():
        raise J10Denied("LEDGER_REDIRECTED")
    ledger.mkdir(mode=0o700, exist_ok=True)
    if not ledger.is_dir() or ledger.is_symlink() or ledger.resolve(strict=True).parent != root.resolve(strict=True):
        raise J10Denied("LEDGER_REDIRECTED")
    _,again=read_fake_current(root, request_owner=expected_owner, expected_owner=expected_owner)
    if record != again:
        raise J10Denied("GENERATION_CHANGED")
    try:
        fd=os.open(str(ledger/(c["nonce"]+".nonce")),os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    except FileExistsError as exc:
        raise J10Denied("NONCE_REPLAY_DENIED") from exc
    except OSError as exc:
        raise J10Denied("NONCE_LEDGER_FAILED") from exc
    with os.fdopen(fd,"wb") as f:
        f.write(hashlib.sha256(ticket).hexdigest().encode("ascii"))
        f.flush()
        os.fsync(f.fileno())
    # A copy failure burns the nonce. Existing helper removes partial destination.
    clone_current_into_new_fake_dir(root,destination,request_owner=expected_owner,expected_owner=expected_owner)
    return {"job":job_id,"generation":record["generation"],"fake_destination":destination.name,
            "clinical_restore_permitted":False}
