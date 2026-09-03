from __future__ import annotations

import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from backend.core.paths import AppPaths
from backend.device_security import DeviceSecurityError, VerifiedDeviceCertificate, verify_device_certificate
from backend.license_trust import TRUSTED_LICENSE_PUBLIC_KEYS
from backend.services.device_identity import DeviceIdentityService


DEVICE_CERT_FILENAME = "device_certificate.txt"


class DeviceBindingError(RuntimeError):
    """The current installation is not cryptographically bound to this device."""


class DeviceBindingService:
    def __init__(
        self,
        *,
        identity_service: DeviceIdentityService | None = None,
        certificate_path: Path | None = None,
    ) -> None:
        self.identity_service = identity_service or DeviceIdentityService()
        self.certificate_path = certificate_path or (
            AppPaths.get_user_data_dir() / DEVICE_CERT_FILENAME
        )

    def _atomic_write(self, token: str) -> None:
        self.certificate_path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(
            prefix=f".{self.certificate_path.name}.",
            suffix=".tmp",
            dir=str(self.certificate_path.parent),
            text=True,
        )
        temp_path = Path(temp_name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(token)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            if os.name != "nt":
                temp_path.chmod(0o600)
            os.replace(temp_path, self.certificate_path)
            if os.name != "nt":
                self.certificate_path.chmod(0o600)
        finally:
            temp_path.unlink(missing_ok=True)

    def clear(self) -> None:
        self.certificate_path.unlink(missing_ok=True)

    def _verify(
        self,
        token: str,
        *,
        cabinet_id: str,
        license_id: str,
        now: datetime | None = None,
    ) -> VerifiedDeviceCertificate:
        identity = self.identity_service.get_identity()
        try:
            return verify_device_certificate(
                token,
                TRUSTED_LICENSE_PUBLIC_KEYS,
                expected_cabinet_id=cabinet_id,
                expected_license_id=license_id,
                expected_device_id=identity.device_id,
                expected_platform=identity.platform,
                now=now or datetime.now(timezone.utc),
            )
        except DeviceSecurityError as exc:
            raise DeviceBindingError(str(exc)) from exc

    def install(
        self,
        token: str,
        *,
        cabinet_id: str,
        license_id: str,
    ) -> VerifiedDeviceCertificate:
        verified = self._verify(
            token,
            cabinet_id=cabinet_id,
            license_id=license_id,
        )
        try:
            self._atomic_write(token.strip())
            reread = self.certificate_path.read_text(encoding="utf-8").strip()
            reread_verified = self._verify(
                reread,
                cabinet_id=cabinet_id,
                license_id=license_id,
            )
        except Exception:
            self.clear()
            raise
        if reread_verified.certificate_id != verified.certificate_id:
            self.clear()
            raise DeviceBindingError("device certificate persistence verification failed")
        return verified

    def verify_current(
        self,
        *,
        cabinet_id: str,
        license_id: str,
        now: datetime | None = None,
    ) -> VerifiedDeviceCertificate:
        if not self.certificate_path.exists():
            raise DeviceBindingError("signed device certificate missing")
        token = self.certificate_path.read_text(encoding="utf-8").strip()
        if not token:
            raise DeviceBindingError("signed device certificate missing")
        return self._verify(
            token,
            cabinet_id=cabinet_id,
            license_id=license_id,
            now=now,
        )
