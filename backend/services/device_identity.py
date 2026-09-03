from __future__ import annotations

import base64
import ctypes
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat, PublicFormat

from backend.core.paths import AppPaths
from backend.core.platform import get_platform_adapter
from backend.device_security import derive_device_id


DEVICE_KEY_FILENAME = "device_identity.bin"
CRYPTPROTECT_UI_FORBIDDEN = 0x1


class DeviceIdentityError(RuntimeError):
    """Local machine identity cannot be created or recovered safely."""


class DevicePrivateKeyProtector(Protocol):
    def protect(self, plaintext: bytes) -> bytes: ...
    def unprotect(self, protected: bytes) -> bytes: ...


@dataclass(frozen=True)
class DeviceIdentity:
    device_id: str
    public_key_b64url: str
    platform: str


class _DATA_BLOB(ctypes.Structure):
    _fields_ = [
        ("cbData", ctypes.c_ulong),
        ("pbData", ctypes.POINTER(ctypes.c_ubyte)),
    ]


class WindowsDPAPIProtector:
    """Current-user DPAPI wrapper. Protected blobs are not portable to another PC."""

    @staticmethod
    def _blob(data: bytes):
        buffer = ctypes.create_string_buffer(data, len(data))
        blob = _DATA_BLOB(
            len(data),
            ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)),
        )
        return blob, buffer

    @staticmethod
    def _crypt32():
        if os.name != "nt":
            raise DeviceIdentityError("Windows DPAPI is unavailable on this platform")
        crypt32 = ctypes.windll.crypt32
        kernel32 = ctypes.windll.kernel32
        crypt32.CryptProtectData.restype = ctypes.c_bool
        crypt32.CryptUnprotectData.restype = ctypes.c_bool
        kernel32.LocalFree.restype = ctypes.c_void_p
        return crypt32, kernel32

    def protect(self, plaintext: bytes) -> bytes:
        crypt32, kernel32 = self._crypt32()
        input_blob, input_buffer = self._blob(plaintext)
        output_blob = _DATA_BLOB()
        ok = crypt32.CryptProtectData(
            ctypes.byref(input_blob),
            "Digital Crown device identity",
            None,
            None,
            None,
            CRYPTPROTECT_UI_FORBIDDEN,
            ctypes.byref(output_blob),
        )
        _ = input_buffer
        if not ok:
            raise DeviceIdentityError("DPAPI protection failed")
        try:
            return ctypes.string_at(output_blob.pbData, output_blob.cbData)
        finally:
            if output_blob.pbData:
                kernel32.LocalFree(output_blob.pbData)

    def unprotect(self, protected: bytes) -> bytes:
        crypt32, kernel32 = self._crypt32()
        input_blob, input_buffer = self._blob(protected)
        output_blob = _DATA_BLOB()
        # Description output is deliberately omitted. Passing NULL avoids an
        # extra LocalAlloc-owned string and the easy-to-get-wrong free path.
        ok = crypt32.CryptUnprotectData(
            ctypes.byref(input_blob),
            None,
            None,
            None,
            None,
            CRYPTPROTECT_UI_FORBIDDEN,
            ctypes.byref(output_blob),
        )
        _ = input_buffer
        if not ok:
            raise DeviceIdentityError("DPAPI unprotection failed")
        try:
            return ctypes.string_at(output_blob.pbData, output_blob.cbData)
        finally:
            if output_blob.pbData:
                kernel32.LocalFree(output_blob.pbData)


class DeviceIdentityService:
    """Owns the per-machine Ed25519 keypair; only the public key leaves the device."""

    def __init__(
        self,
        *,
        protector: DevicePrivateKeyProtector | None = None,
        key_path: Path | None = None,
        platform_kind: str | None = None,
    ) -> None:
        adapter = get_platform_adapter()
        self.platform = platform_kind or adapter.kind
        self.key_path = key_path or (AppPaths.get_user_data_dir() / DEVICE_KEY_FILENAME)
        if protector is not None:
            self.protector = protector
        elif self.platform == "windows":
            self.protector = WindowsDPAPIProtector()
        elif self.platform == "macos":
            # macOS must use a ThisDeviceOnly Keychain item. A plain file or a
            # migratable Keychain item would defeat the binding after restore.
            raise DeviceIdentityError(
                "macOS device identity requires ThisDeviceOnly Keychain storage; not provisioned yet"
            )
        else:
            raise DeviceIdentityError(
                f"secure device identity storage unsupported on platform: {self.platform}"
            )

    @staticmethod
    def _b64url(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

    def _atomic_write(self, data: bytes) -> None:
        self.key_path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(
            prefix=f".{self.key_path.name}.",
            suffix=".tmp",
            dir=str(self.key_path.parent),
        )
        temp_path = Path(temp_name)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            if os.name != "nt":
                temp_path.chmod(0o600)
            os.replace(temp_path, self.key_path)
        finally:
            temp_path.unlink(missing_ok=True)

    def _load_or_create_private_raw(self) -> bytes:
        if self.key_path.exists():
            try:
                raw = self.protector.unprotect(self.key_path.read_bytes())
            except Exception as exc:
                raise DeviceIdentityError(
                    "device private key cannot be recovered on this machine"
                ) from exc
            if len(raw) != 32:
                raise DeviceIdentityError("invalid protected device private key")
            return raw

        private_key = Ed25519PrivateKey.generate()
        raw = private_key.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
        try:
            protected = self.protector.protect(raw)
            if not protected:
                raise DeviceIdentityError("empty protected device private key")
            self._atomic_write(protected)
            recovered = self.protector.unprotect(self.key_path.read_bytes())
        except Exception as exc:
            self.key_path.unlink(missing_ok=True)
            if isinstance(exc, DeviceIdentityError):
                raise
            raise DeviceIdentityError("device private key persistence failed") from exc
        if recovered != raw:
            self.key_path.unlink(missing_ok=True)
            raise DeviceIdentityError("device private key persistence verification failed")
        return raw

    def get_identity(self) -> DeviceIdentity:
        raw = self._load_or_create_private_raw()
        private_key = Ed25519PrivateKey.from_private_bytes(raw)
        public_raw = private_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
        public_b64url = self._b64url(public_raw)
        return DeviceIdentity(
            device_id=derive_device_id(public_b64url),
            public_key_b64url=public_b64url,
            platform=self.platform,
        )

    def sign_possession_challenge(self, challenge: bytes) -> bytes:
        if not isinstance(challenge, bytes) or not challenge:
            raise DeviceIdentityError("device possession challenge is empty")
        raw = self._load_or_create_private_raw()
        return Ed25519PrivateKey.from_private_bytes(raw).sign(challenge)
