from __future__ import annotations

import json
import os
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Any

from backend.services.patient_companion_remote_crypto import generate_p256_keypair
from backend.services.windows_dpapi import protect_for_current_user, unprotect_for_current_user

KEY_FILE_NAME = "patient-companion-remote-keys.dpapi"


class CabinetRemoteKeyVault:
    """Persist cabinet private JWKs only as current-user DPAPI protected bytes."""

    def __init__(self, path: Path):
        self.path = path

    @classmethod
    def from_runtime(cls) -> "CabinetRemoteKeyVault":
        if sys.platform != "win32":
            raise RuntimeError("Patient Companion remote cabinet keys require Windows DPAPI")
        root = Path(os.environ.get("LOCALAPPDATA", "")).expanduser()
        if not str(root):
            raise RuntimeError("LOCALAPPDATA is required for cabinet remote key storage")
        return cls(root / "DigitalCrown" / "keys" / KEY_FILE_NAME)

    def _read(self) -> dict[str, Any] | None:
        if not self.path.exists():
            return None
        protected = self.path.read_bytes()
        clear = unprotect_for_current_user(protected)
        payload = json.loads(clear.decode("utf-8"))
        if payload.get("version") != 1:
            raise RuntimeError("unsupported cabinet remote key vault")
        return payload

    def _atomic_write(self, payload: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        clear = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
        protected = protect_for_current_user(clear)
        fd, tmp_name = tempfile.mkstemp(prefix=self.path.name + ".", dir=self.path.parent)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(protected)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_name, self.path)
        finally:
            try:
                os.unlink(tmp_name)
            except FileNotFoundError:
                pass

    def get_or_create_active_keys(self) -> dict[str, Any]:
        existing = self._read()
        if existing is not None:
            return existing

        signing_kid = str(uuid.uuid4())
        encryption_kid = str(uuid.uuid4())
        signing_private, signing_public = generate_p256_keypair(kid=signing_kid, use="sig")
        encryption_private, encryption_public = generate_p256_keypair(kid=encryption_kid, use="enc")
        payload = {
            "version": 1,
            "signing": {
                "kid": signing_kid,
                "private_jwk": signing_private,
                "public_jwk": signing_public,
            },
            "encryption": {
                "kid": encryption_kid,
                "private_jwk": encryption_private,
                "public_jwk": encryption_public,
            },
        }
        self._atomic_write(payload)
        return payload

    def public_bundle(self) -> dict[str, Any]:
        keys = self.get_or_create_active_keys()
        return {
            "version": 1,
            "signing": {
                "kid": keys["signing"]["kid"],
                "public_jwk": keys["signing"]["public_jwk"],
            },
            "encryption": {
                "kid": keys["encryption"]["kid"],
                "public_jwk": keys["encryption"]["public_jwk"],
            },
        }
