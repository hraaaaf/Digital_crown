"""J10C: genuine JWT authorization in a real, temporary SCM signer; FAKE SQLCipher manifest."""
import base64
import hmac
import json
import os
from pathlib import Path
import re
import secrets
import sys
import time
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from backend.tests.fixtures.lot05j8_real_jwt_separate_signer_lab import _auth_real, J8Denied

PURPOSE="LOT05J10C_SQLCIPHER_FAKE"
HEX32=re.compile(r"[a-f0-9]{32}\Z")
HEX64=re.compile(r"[a-f0-9]{64}\Z")
GEN=re.compile(r"g_[a-f0-9]{32}\Z")
def main():
    if os.getenv("LOT05J9_REAL_JWT_SCM_FAKE_ONLY")!="1" or len(sys.argv)!=2:
        raise J8Denied("J10C_TEST_ONLY")
    folder=Path(sys.argv[1])
    if not folder.is_absolute() or folder.is_symlink() or not folder.is_dir() or not folder.name.startswith("lot05j9_fake_signer_"):
        raise J8Denied("SIGNER_FIXTURE_ROOT_INVALID")
    request=json.loads(sys.stdin.read(8192))
    if type(request) is not dict or set(request)!={"jwt","owner","job","generation","manifest"}:
        raise J8Denied("JWT_BOUND_REQUEST_SHAPE_DENIED")
    owner=_auth_real(request["jwt"],request["owner"])
    claim={k:request[k] for k in ("owner","job","generation","manifest")}
    if (type(owner) is not int or type(claim["owner"]) is not int or owner!=claim["owner"]
        or type(claim["job"]) is not str or not HEX32.fullmatch(claim["job"])
        or type(claim["generation"]) is not str or not GEN.fullmatch(claim["generation"])
        or type(claim["manifest"]) is not str or not HEX64.fullmatch(claim["manifest"])):
        raise J8Denied("JWT_JOB_MANIFEST_INVALID")
    binding=folder/"expected-manifest.json"
    if binding.is_symlink() or not binding.is_file() or binding.stat().st_nlink!=1:
        raise J8Denied("PINNED_MANIFEST_SOURCE_MISSING")
    expected=json.loads(binding.read_text("utf-8"))
    if type(expected) is not dict or set(expected)!=set(claim) or not hmac.compare_digest(
        json.dumps(expected,sort_keys=True,separators=(",",":")),
        json.dumps(claim,sort_keys=True,separators=(",",":"))
    ):
        raise J8Denied("PINNED_MANIFEST_MISMATCH")
    private_file=folder/"signer-private.pem"
    if private_file.is_symlink() or not private_file.is_file() or private_file.stat().st_nlink!=1:
        raise J8Denied("SIGNER_PRIVATE_KEY_UNTRUSTED")
    key=serialization.load_pem_private_key(private_file.read_bytes(),password=None)
    body=("owner=%d|audience=%s|job=%s|generation=%s|manifest=%s|nonce=%s|expires=%d" %
        (owner,PURPOSE,claim["job"],claim["generation"],claim["manifest"],secrets.token_hex(16),int(time.time())+90))
    signature=key.sign(body.encode("ascii"),padding.PKCS1v15(),hashes.SHA256())
    print(json.dumps({"body":body,"signature":base64.b64encode(signature).decode("ascii"),"signer_pid":os.getpid()}))
if __name__=="__main__":
    try:
        main()
    except Exception as exc:
        label=("HTTP_"+str(exc.status_code)) if type(exc).__name__=="HTTPException" else type(exc).__name__
        print("J9_DENIED_"+label,file=sys.stderr)
        sys.exit(61)
