from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from backend.config import settings


class LicenseControlPlaneError(RuntimeError):
    def __init__(self, message: str, *, status_code: int = 503):
        super().__init__(message)
        self.status_code = status_code


@dataclass(frozen=True)
class TrialRedemption:
    signed_license: str
    signed_device_certificate: str
    device_id: str
    expires_at: str
    feature_set: str
    license_type: str


class LicenseControlPlaneClient:
    """Cabinet-side client for public licence/device issuance operations.

    No signing secret, Firebase credential, SuperAdmin credential or device
    private key is ever sent to the control plane. Only the public device
    identity accompanies the one-time Trial redemption.
    """

    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or settings.LICENSE_CONTROL_PLANE_URL).strip().rstrip("/")

    def _url(self, path: str) -> str:
        if not self.base_url:
            raise LicenseControlPlaneError(
                "Service de licences distant non configuré."
            )
        return f"{self.base_url}{path}"

    async def preview_trial(self, code: str) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    self._url(f"/api/public/license-control/trial-code/{code.strip().upper()}"),
                )
        except (httpx.HTTPError, LicenseControlPlaneError) as exc:
            if isinstance(exc, LicenseControlPlaneError):
                raise
            raise LicenseControlPlaneError("Service de licences distant indisponible.") from exc

        if response.status_code >= 400:
            detail = _response_detail(response)
            raise LicenseControlPlaneError(detail, status_code=response.status_code)
        payload = response.json()
        if not isinstance(payload, dict):
            raise LicenseControlPlaneError("Réponse control-plane invalide.")
        return payload

    async def redeem_trial(
        self,
        *,
        code: str,
        email: str,
        cabinet_id: str,
        device_id: str,
        device_public_key: str,
        platform: str,
    ) -> TrialRedemption:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    self._url("/api/public/license-control/activate-trial"),
                    json={
                        "code": code.strip().upper(),
                        "email": email.strip().lower(),
                        "cabinet_id": str(cabinet_id),
                        "device_id": str(device_id),
                        "device_public_key": str(device_public_key),
                        "platform": str(platform),
                    },
                )
        except (httpx.HTTPError, LicenseControlPlaneError) as exc:
            if isinstance(exc, LicenseControlPlaneError):
                raise
            raise LicenseControlPlaneError("Service de licences distant indisponible.") from exc

        if response.status_code >= 400:
            detail = _response_detail(response)
            raise LicenseControlPlaneError(detail, status_code=response.status_code)

        payload = response.json()
        required = (
            "signed_license",
            "signed_device_certificate",
            "device_id",
            "expires_at",
            "feature_set",
            "license_type",
        )
        if not isinstance(payload, dict) or any(not payload.get(key) for key in required):
            raise LicenseControlPlaneError("Réponse d'activation control-plane invalide.")
        if str(payload["device_id"]) != str(device_id):
            raise LicenseControlPlaneError("Réponse control-plane liée à une autre machine.")
        return TrialRedemption(
            signed_license=str(payload["signed_license"]),
            signed_device_certificate=str(payload["signed_device_certificate"]),
            device_id=str(payload["device_id"]),
            expires_at=str(payload["expires_at"]),
            feature_set=str(payload["feature_set"]),
            license_type=str(payload["license_type"]),
        )


def _response_detail(response: httpx.Response) -> str:
    try:
        payload = response.json()
        if isinstance(payload, dict) and payload.get("detail"):
            return str(payload["detail"])
    except ValueError:
        pass
    return f"Erreur control-plane ({response.status_code})."
