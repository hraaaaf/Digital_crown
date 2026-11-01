"""C05B-03H03 Windows native DPAPI + Ed25519 vault; LAB ONLY, NO PRODUCT ROUTES."""
import base64
import ctypes
from ctypes import wintypes
import hashlib
import hmac
import json
import os
from pathlib import Path
import sys
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat, PublicFormat

class VaultRejected(ValueError):
    """Safe error without key material or private user data."""

class _DataBlob(ctypes.Structure):
    _fields_=[("cbData",wintypes.DWORD),("pbData",ctypes.POINTER(ctypes.c_ubyte))]

def _guard():
    if not (sys.platform=="win32" and os.getenv("ENVIRONMENT")=="test"
            and os.getenv("DIGITALCROWN_ISOLATED_RUNTIME")=="true"
            and os.getenv("DC06C05B03H03_TEST_ONLY")=="1"):
        raise VaultRejected("WINDOWS_DPAPI_LAB_DISABLED")

def _scope(tenant,device,station,generation):
    if (type(tenant) is not int or tenant<1 or type(generation) is not int or generation<1
        or not isinstance(device,str) or not 1<=len(device)<=64
        or not isinstance(station,str) or not 1<=len(station)<=64):
        raise VaultRejected("INVALID_DEVICE_SCOPE")
    return dict(version=1,tenant=tenant,device=device,station=station,generation=generation)

def _canonical(data):
    return json.dumps(data,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode("ascii")

def _entropy(scope):
    return hashlib.sha256(b"DigitalCrown.LOT06.H03.DPAPI.USER.v1|"+_canonical(scope)).digest()

def _blob(data):
    arr=(ctypes.c_ubyte*len(data)).from_buffer_copy(data)
    return _DataBlob(len(data),ctypes.cast(arr,ctypes.POINTER(ctypes.c_ubyte))),arr

def _dpapi(data,entropy,*,protect):
    _guard()
    crypt32=ctypes.WinDLL("crypt32",use_last_error=True)
    kernel32=ctypes.WinDLL("kernel32",use_last_error=True)
    B=ctypes.POINTER(_DataBlob)
    crypt32.CryptProtectData.argtypes=[B,wintypes.LPCWSTR,B,ctypes.c_void_p,ctypes.c_void_p,wintypes.DWORD,B]
    crypt32.CryptProtectData.restype=wintypes.BOOL
    crypt32.CryptUnprotectData.argtypes=[B,ctypes.c_void_p,B,ctypes.c_void_p,ctypes.c_void_p,wintypes.DWORD,B]
    crypt32.CryptUnprotectData.restype=wintypes.BOOL
    kernel32.LocalFree.argtypes=[ctypes.c_void_p]
    kernel32.LocalFree.restype=ctypes.c_void_p
    src,src_mem=_blob(data)
    extra,extra_mem=_blob(entropy)
    out=_DataBlob()
    # CRYPTPROTECT_UI_FORBIDDEN=1; CRYPTPROTECT_LOCAL_MACHINE=4 is NEVER set.
    if protect:
        ok=crypt32.CryptProtectData(ctypes.byref(src),"LOT06 Synthetic Windows Gateway",
            ctypes.byref(extra),None,None,1,ctypes.byref(out))
    else:
        ok=crypt32.CryptUnprotectData(ctypes.byref(src),None,
            ctypes.byref(extra),None,None,1,ctypes.byref(out))
    if not ok:
        raise VaultRejected("DPAPI_PROTECT_FAILED" if protect else "DPAPI_UNSEAL_DENIED")
    try:
        return ctypes.string_at(out.pbData,out.cbData)
    finally:
        kernel32.LocalFree(ctypes.cast(out.pbData,ctypes.c_void_p))

def create_key(path,*,tenant,device,station,generation):
    """Exclusive create; returns public Ed25519 bytes as hex, not secret seed."""
    _guard()
    scope=_scope(tenant,device,station,generation)
    path=Path(path)
    if not path.parent.is_dir() or path.is_symlink():
        raise VaultRejected("UNSAFE_GATEWAY_KEY_PATH")
    if path.exists():
        raise VaultRejected("KEY_ALREADY_EXISTS")
    private=Ed25519PrivateKey.generate()
    seed=private.private_bytes(Encoding.Raw,PrivateFormat.Raw,NoEncryption())
    public=private.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw).hex()
    sealed=_dpapi(seed,_entropy(scope),protect=True)
    record=dict(**scope,public_hex=public,dpapi_blob=base64.b64encode(sealed).decode("ascii"))
    flags=os.O_WRONLY|os.O_CREAT|os.O_EXCL|getattr(os,"O_BINARY",0)
    try:
        fd=os.open(path,flags,0o600)
    except FileExistsError as exc:
        raise VaultRejected("KEY_ALREADY_EXISTS") from exc
    try:
        with os.fdopen(fd,"wb") as f:
            f.write(_canonical(record)+b"\n")
            f.flush()
            os.fsync(f.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    return public

def sign(path,message,*,tenant,device,station,generation):
    _guard()
    if not isinstance(message,bytes) or not message or len(message)>1048576:
        raise VaultRejected("INVALID_SIGNING_PAYLOAD")
    scope=_scope(tenant,device,station,generation)
    path=Path(path)
    if path.is_symlink() or not path.is_file():
        raise VaultRejected("KEY_UNAVAILABLE")
    try:
        content=path.read_bytes()
        if len(content)>16384: raise ValueError("size")
        record=json.loads(content)
        if set(record)!=set(scope)|{"public_hex","dpapi_blob"}:
            raise ValueError("fields")
        if any(record.get(k)!=v or type(record.get(k)) is not type(v)
               for k,v in scope.items()):
            raise ValueError("scope")
        public=bytes.fromhex(record["public_hex"])
        sealed=base64.b64decode(record["dpapi_blob"],validate=True)
        if len(public)!=32 or not sealed or len(sealed)>8192:
            raise ValueError("key")
    except (ValueError,TypeError,KeyError,OSError) as exc:
        raise VaultRejected("KEY_ENVELOPE_DENIED") from exc
    seed=_dpapi(sealed,_entropy(scope),protect=False)
    if len(seed)!=32:
        raise VaultRejected("BAD_DPAPI_SEED")
    private=Ed25519PrivateKey.from_private_bytes(seed)
    derived=private.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw)
    if not hmac.compare_digest(derived,public):
        raise VaultRejected("PUBLIC_PRIVATE_MISMATCH")
    return private.sign(message)

def revoke_local(path):
    """Local file deletion only; server SQLCipher device revocation is separate."""
    _guard()
    path=Path(path)
    if path.is_symlink() or not path.is_file():
        raise VaultRejected("KEY_UNAVAILABLE")
    path.unlink()
