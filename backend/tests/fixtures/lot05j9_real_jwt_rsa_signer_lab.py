"""LOT05.7-J9: detached JWT-authorized RSA signing for real, TEMPORARY SCM fixture.
Never import this into backend runtime. No clinical payload, restoration or patients.
"""
import base64
import json
import os
from pathlib import Path
import secrets
import sys
import time
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from backend.tests.fixtures.lot05j8_real_jwt_separate_signer_lab import _auth_real, J8Denied

FLAG = "LOT05J9_REAL_JWT_SCM_FAKE_ONLY"
AUDIENCE = "LOT05J9_FAKE_WORKER"

def main():
    if os.getenv(FLAG) != "1" or len(sys.argv) != 2:
        raise J8Denied("J9_ONLY_DISPOSABLE_TEST_FIXTURE")
    root = Path(sys.argv[1])
    if not root.is_absolute() or not root.is_dir() or not root.name.startswith("lot05j9_fake_") or root.is_symlink():
        raise J8Denied("FAKE_ROOT_INVALID")
    req = json.loads(sys.stdin.read(65536))
    if type(req) is not dict or set(req) != {"jwt", "owner"}:
        raise J8Denied("SIGNED_REQUEST_INVALID")
    owner = _auth_real(req["jwt"], req["owner"])
    # Read the test private key only AFTER true backend authorization.
    key_path = root / "signer-private.pem"
    if key_path.is_symlink() or not key_path.is_file() or key_path.stat().st_nlink != 1:
        raise J8Denied("FAKE_SIGNER_PRIVATE_KEY_UNTRUSTED")
    private = serialization.load_pem_private_key(key_path.read_bytes(), password=None)
    now = int(time.time())
    nonce = secrets.token_hex(16)
    body = "owner=%d|audience=%s|nonce=%s|expires=%d" % (owner, AUDIENCE, nonce, now + 100)
    signature = private.sign(body.encode("ascii"), padding.PKCS1v15(), hashes.SHA256())
    print(json.dumps({"body": body, "signature": base64.b64encode(signature).decode("ascii"),
                      "signer_pid": os.getpid()}, sort_keys=True))

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        label = ("HTTP_" + str(exc.status_code)) if type(exc).__name__ == "HTTPException" else type(exc).__name__
        print("J9_DENIED_" + label, file=sys.stderr)
        sys.exit(61)
