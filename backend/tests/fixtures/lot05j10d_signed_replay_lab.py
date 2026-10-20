"""LOT05/J10D: DENY-only verifier for J10C RSA tickets with durable nonce evidence.

Lab contract, not an installed SCM consumer, product trust root or clinical restore.
The installation must separately enforce an ACL protected by the consumer Service SID;
local Administrator/SYSTEM, ledger rollback and path-swap remain outside proof.
"""
import base64
import binascii
import hashlib
import os
from pathlib import Path
import re
import stat
import time

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa

AUDIENCE = "LOT05J10C_SQLCIPHER_FAKE"
HEX32 = re.compile(r"[a-f0-9]{32}\\Z")
HEX64 = re.compile(r"[a-f0-9]{64}\\Z")
GEN = re.compile(r"g_[a-f0-9]{32}\\Z")


class SignedReplayDenied(PermissionError):
    pass


def _decode(value, *, max_size):
    if type(value) is not str or len(value) > max_size or not value:
        raise SignedReplayDenied("SIGNED_FORMAT")
    try:
        return base64.b64decode(value, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise SignedReplayDenied("SIGNED_BASE64") from exc


def _validate(ticket, pin, *, owner, job, generation, manifest, now):
    if (type(ticket) is not dict or set(ticket) != {"body", "signature", "signer_pid"} or
        type(owner) is not int or owner <= 0 or type(job) is not str or not HEX32.fullmatch(job) or
        type(generation) is not str or not GEN.fullmatch(generation) or
        type(manifest) is not str or not HEX64.fullmatch(manifest) or
        type(now) is not int):
        raise SignedReplayDenied("SIGNED_SCOPE")
    body = ticket["body"]
    if type(body) is not str or len(body) > 512 or not body.isascii():
        raise SignedReplayDenied("SIGNED_BODY")
    fields = body.split("|")
    if (len(fields) != 7 or fields[:5] != [
        f"owner={owner}", f"audience={AUDIENCE}", f"job={job}",
        f"generation={generation}", f"manifest={manifest}"] or
        not fields[5].startswith("nonce=") or not fields[6].startswith("expires=")):
        raise SignedReplayDenied("SIGNED_BINDING")
    nonce = fields[5][6:]
    expiry_str = fields[6][8:]
    if not HEX32.fullmatch(nonce) or not re.fullmatch(r"[1-9][0-9]{0,11}", expiry_str):
        raise SignedReplayDenied("SIGNED_NONCE_EXPIRY")
    expires = int(expiry_str)
    if expires <= now or expires > now + 90:
        raise SignedReplayDenied("SIGNED_EXPIRED")
    if type(pin) is not str:
        raise SignedReplayDenied("SIGNED_PIN")
    lines = pin.splitlines()
    if len(lines) != 3 or lines[2] != str(owner):
        raise SignedReplayDenied("SIGNED_PIN_OWNER")
    modulus = _decode(lines[0], max_size=400)
    exponent = _decode(lines[1], max_size=16)
    signature = _decode(ticket["signature"], max_size=400)
    if len(modulus) != 256 or not (1 <= len(exponent) <= 8) or len(signature) != 256:
        raise SignedReplayDenied("SIGNED_KEY_SIZE")
    try:
        public = rsa.RSAPublicNumbers(
            int.from_bytes(exponent, "big"), int.from_bytes(modulus, "big")
        ).public_key()
        public.verify(signature, body.encode("ascii"), padding.PKCS1v15(), hashes.SHA256())
    except (ValueError, TypeError, InvalidSignature) as exc:
        raise SignedReplayDenied("SIGNED_RSA_DENY") from exc
    return nonce, body


def verify_and_burn(ticket, pin, *, owner, job, generation, manifest, ledger_dir, now=None):
    """Verify J10C signature/binding, burn nonce once, ALWAYS return DENY.

    Failure or inability to persist means denial. Reservation deliberately occurs
    before any imaginary clinical action; this function never calls one.
    """
    now = int(time.time()) if now is None else now
    nonce, body = _validate(ticket, pin, owner=owner, job=job,
                            generation=generation, manifest=manifest, now=now)
    folder = Path(ledger_dir)
    try:
        directory = folder.lstat()
        if not stat.S_ISDIR(directory.st_mode) or folder.is_symlink():
            raise SignedReplayDenied("LEDGER_DIRECTORY")
        marker = folder / (nonce + ".nonce")
        # Never follow a known symlink; atomic O_EXCL makes duplicate burn fail.
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        flags |= getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(marker, flags, 0o600)
        try:
            with os.fdopen(fd, "wb") as output:
                output.write(hashlib.sha256(body.encode("ascii")).hexdigest().encode("ascii"))
                output.flush()
                os.fsync(output.fileno())
        except BaseException:
            # Failed burn is never authorization. Do not un-burn partial markers;
            # fail closed until an authenticated human review.
            raise
        # POSIX parent fsync establishes durable directory entry where supported.
        # Windows crash/power-loss durability requires an independent OS proof.
        if os.name == "posix":
            directory_fd = os.open(folder, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
    except FileExistsError as exc:
        raise SignedReplayDenied("NONCE_REPLAY") from exc
    except SignedReplayDenied:
        raise
    except (OSError, ValueError) as exc:
        raise SignedReplayDenied("LEDGER_UNAVAILABLE") from exc
    return "DENY_J10D_SIGNED_NONCE_BURNED"
