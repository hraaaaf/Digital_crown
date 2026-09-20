from __future__ import annotations

import base64
import uuid
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx
from sqlalchemy.orm import Session

from backend.models_patient_companion import PatientCompanionAccess, PatientCompanionRelayBinding
from backend.services.patient_companion_key_protection import protect_os_bound, unprotect_os_bound


@dataclass(frozen=True)
class PatientRelayBootstrap:
    relay_url: str
    cabinet_inbox_id: str
    cabinet_write_capability: str
    patient_inbox_id: str
    patient_read_capability: str

    def response(self) -> dict:
        return {
            "protocol_version": "dc-relay-v1",
            "relay_url": self.relay_url,
            "cabinet_inbox": {
                "mailbox_id": self.cabinet_inbox_id,
                "write_capability": self.cabinet_write_capability,
            },
            "patient_inbox": {
                "mailbox_id": self.patient_inbox_id,
                "read_capability": self.patient_read_capability,
            },
        }


def _normalized_https_url(raw: str) -> str:
    value = raw.strip().rstrip("/")
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
        raise ValueError("Patient Companion relay URL must be an explicit HTTPS origin")
    return value


def _mailbox(payload: dict) -> tuple[str, str, str]:
    mailbox_id = str(payload.get("mailbox_id") or "")
    read_capability = str(payload.get("read_capability") or "")
    write_capability = str(payload.get("write_capability") or "")
    try:
        uuid.UUID(mailbox_id)
    except (TypeError, ValueError):
        raise ValueError("relay returned invalid mailbox identifier") from None
    if len(read_capability) < 43 or len(write_capability) < 43:
        raise ValueError("relay returned invalid mailbox capability")
    return mailbox_id, read_capability, write_capability


def _provision_mailbox(client: httpx.Client, relay_url: str, bootstrap_secret: str) -> tuple[str, str, str]:
    response = client.post(
        f"{relay_url}/v1/mailboxes",
        headers={"X-Relay-Bootstrap": bootstrap_secret},
    )
    response.raise_for_status()
    return _mailbox(response.json())


def _revoke_mailbox(client: httpx.Client, relay_url: str, bootstrap_secret: str, mailbox_id: str) -> None:
    try:
        response = client.delete(
            f"{relay_url}/v1/mailboxes/{mailbox_id}",
            headers={"X-Relay-Bootstrap": bootstrap_secret},
        )
        if response.status_code not in {204, 404}:
            response.raise_for_status()
    except Exception:
        # Best-effort cleanup. The caller still fails closed and never returns capabilities.
        pass


def provision_relay_binding(
    db: Session,
    *,
    access: PatientCompanionAccess,
    relay_url: str,
    bootstrap_secret: str,
    protect=protect_os_bound,
    client: httpx.Client | None = None,
) -> tuple[PatientCompanionRelayBinding, PatientRelayBootstrap]:
    relay_url = _normalized_https_url(relay_url)
    if len(bootstrap_secret.encode("utf-8")) < 32:
        raise ValueError("Patient Companion relay bootstrap secret must be at least 32 bytes")
    existing = db.query(PatientCompanionRelayBinding).filter(
        PatientCompanionRelayBinding.access_id == access.id,
    ).first()
    if existing is not None:
        raise ValueError("relay binding already exists for this access")

    owned_client = client is None
    client = client or httpx.Client(timeout=10.0)
    cabinet_mailbox_id = ""
    patient_mailbox_id = ""
    try:
        cabinet_mailbox_id, cabinet_read, cabinet_write = _provision_mailbox(
            client, relay_url, bootstrap_secret
        )
        try:
            patient_mailbox_id, patient_read, patient_write = _provision_mailbox(
                client, relay_url, bootstrap_secret
            )
        except Exception:
            _revoke_mailbox(client, relay_url, bootstrap_secret, cabinet_mailbox_id)
            raise

        binding = PatientCompanionRelayBinding(
            access_id=access.id,
            relay_url=relay_url,
            cabinet_inbox_id=cabinet_mailbox_id,
            patient_inbox_id=patient_mailbox_id,
            protected_cabinet_read_cap_b64=base64.b64encode(
                protect(cabinet_read.encode("utf-8"))
            ).decode("ascii"),
            protected_patient_write_cap_b64=base64.b64encode(
                protect(patient_write.encode("utf-8"))
            ).decode("ascii"),
            status="ACTIVE",
        )
        db.add(binding)
        db.flush()

        # Least privilege split:
        # patient receives cabinet WRITE + patient READ only;
        # cabinet persists cabinet READ + patient WRITE only.
        bootstrap = PatientRelayBootstrap(
            relay_url=relay_url,
            cabinet_inbox_id=cabinet_mailbox_id,
            cabinet_write_capability=cabinet_write,
            patient_inbox_id=patient_mailbox_id,
            patient_read_capability=patient_read,
        )
        return binding, bootstrap
    except Exception:
        if patient_mailbox_id:
            _revoke_mailbox(client, relay_url, bootstrap_secret, patient_mailbox_id)
        if cabinet_mailbox_id:
            _revoke_mailbox(client, relay_url, bootstrap_secret, cabinet_mailbox_id)
        raise
    finally:
        if owned_client:
            client.close()


def cabinet_relay_capabilities(
    binding: PatientCompanionRelayBinding,
    *,
    unprotect=unprotect_os_bound,
) -> tuple[str, str]:
    if binding.status != "ACTIVE" or binding.revoked_at is not None:
        raise ValueError("relay binding is not active")
    cabinet_read = unprotect(
        base64.b64decode(binding.protected_cabinet_read_cap_b64.encode("ascii"))
    ).decode("utf-8")
    patient_write = unprotect(
        base64.b64decode(binding.protected_patient_write_cap_b64.encode("ascii"))
    ).decode("utf-8")
    if len(cabinet_read) < 43 or len(patient_write) < 43:
        raise ValueError("protected relay capability is invalid")
    return cabinet_read, patient_write
