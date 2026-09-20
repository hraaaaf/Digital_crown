from __future__ import annotations

import uuid
from datetime import datetime, timedelta

import httpx
from sqlalchemy.orm import Session

from backend.models_patient_companion import (
    PatientCompanionAccess,
    PatientCompanionRelayBinding,
    PatientCompanionRelayOutbox,
    PatientCompanionRemoteKeyset,
)
from backend.services.patient_companion_key_protection import unprotect_os_bound
from backend.services.patient_companion_relay_client import cabinet_relay_capabilities
from backend.services.patient_companion_remote_receipts import RemoteCommandBusy
from backend.services.patient_companion_remote_worker import process_remote_envelope

RELAY_COMMAND_TTL_SECONDS = 15 * 60
RELAY_OUTBOX_RETENTION_DAYS = 7


def _capability_header(raw: str) -> dict[str, str]:
    return {"Authorization": f"RelayCap {raw}"}


def _deliver_outbox(
    db: Session,
    *,
    client: httpx.Client,
    binding: PatientCompanionRelayBinding,
    row: PatientCompanionRelayOutbox,
    cabinet_read_capability: str,
    patient_write_capability: str,
) -> bool:
    response = client.post(
        f"{binding.relay_url}/v1/mailboxes/{binding.patient_inbox_id}/envelopes",
        headers={
            **_capability_header(patient_write_capability),
            "Content-Type": "application/json",
        },
        json={
            "envelope_id": row.ack_envelope_id,
            "blob": row.blob,
            "ttl_seconds": RELAY_COMMAND_TTL_SECONDS,
        },
    )
    if response.status_code not in {201, 409}:
        response.raise_for_status()

    if row.delivered_at is None:
        row.delivered_at = datetime.utcnow()
        db.commit()

    delete = client.delete(
        f"{binding.relay_url}/v1/mailboxes/{binding.cabinet_inbox_id}/envelopes/{row.source_envelope_id}",
        headers=_capability_header(cabinet_read_capability),
    )
    if delete.status_code not in {204, 404}:
        delete.raise_for_status()
    return True


def _active_keyset(db: Session, binding: PatientCompanionRelayBinding):
    access = db.query(PatientCompanionAccess).filter(
        PatientCompanionAccess.id == binding.access_id,
        PatientCompanionAccess.revoked_at.is_(None),
    ).first()
    if access is None:
        return None, None
    keyset = db.query(PatientCompanionRemoteKeyset).filter(
        PatientCompanionRemoteKeyset.access_id == access.id,
        PatientCompanionRemoteKeyset.status == "ACTIVE",
        PatientCompanionRemoteKeyset.revoked_at.is_(None),
    ).first()
    return access, keyset


def process_relay_binding_once(
    db: Session,
    *,
    binding: PatientCompanionRelayBinding,
    client: httpx.Client,
    unprotect=unprotect_os_bound,
) -> dict[str, int]:
    if binding.status != "ACTIVE" or binding.revoked_at is not None:
        return {"processed": 0, "delivered": 0, "invalid": 0}

    access, keyset = _active_keyset(db, binding)
    if access is None or keyset is None:
        binding.status = "REVOKED"
        binding.revoked_at = datetime.utcnow()
        db.commit()
        return {"processed": 0, "delivered": 0, "invalid": 0}

    cabinet_read, patient_write = cabinet_relay_capabilities(binding, unprotect=unprotect)
    stats = {"processed": 0, "delivered": 0, "invalid": 0}

    # First drain durable ACKs. A prior push may have succeeded while the local
    # delivered marker did not; relay 409 is therefore treated as idempotent success.
    pending = db.query(PatientCompanionRelayOutbox).filter(
        PatientCompanionRelayOutbox.binding_id == binding.id,
        PatientCompanionRelayOutbox.delivered_at.is_(None),
    ).order_by(PatientCompanionRelayOutbox.created_at.asc()).limit(100).all()
    for row in pending:
        _deliver_outbox(
            db,
            client=client,
            binding=binding,
            row=row,
            cabinet_read_capability=cabinet_read,
            patient_write_capability=patient_write,
        )
        stats["delivered"] += 1

    pulled = client.get(
        f"{binding.relay_url}/v1/mailboxes/{binding.cabinet_inbox_id}/envelopes",
        headers=_capability_header(cabinet_read),
        params={"limit": 100},
    )
    pulled.raise_for_status()
    items = pulled.json().get("items", [])
    if not isinstance(items, list):
        raise ValueError("relay mailbox response is invalid")

    for item in items:
        source_id = str(item.get("envelope_id") or "")
        blob = item.get("blob")
        try:
            uuid.UUID(source_id)
        except (TypeError, ValueError):
            stats["invalid"] += 1
            continue
        if not isinstance(blob, str) or not blob:
            stats["invalid"] += 1
            continue

        existing = db.query(PatientCompanionRelayOutbox).filter(
            PatientCompanionRelayOutbox.binding_id == binding.id,
            PatientCompanionRelayOutbox.source_envelope_id == source_id,
        ).first()
        if existing is not None:
            _deliver_outbox(
                db,
                client=client,
                binding=binding,
                row=existing,
                cabinet_read_capability=cabinet_read,
                patient_write_capability=patient_write,
            )
            if existing.delivered_at is not None:
                stats["delivered"] += 1
            continue

        try:
            ack_blob = process_remote_envelope(
                db,
                access=access,
                keyset=keyset,
                compact_jwe=blob,
                unprotect=unprotect,
                commit=False,
            )
            outbox = PatientCompanionRelayOutbox(
                binding_id=binding.id,
                source_envelope_id=source_id,
                ack_envelope_id=str(uuid.uuid4()),
                blob=ack_blob,
            )
            db.add(outbox)
            # Domain mutation + replay receipt + encrypted ACK outbox become durable together.
            db.commit()
            stats["processed"] += 1
        except RemoteCommandBusy:
            db.rollback()
            continue
        except ValueError:
            db.rollback()
            stats["invalid"] += 1
            # Poisoned/expired/replayed ciphertext is terminal. It is safe to delete:
            # no domain mutation committed in this transaction.
            deleted = client.delete(
                f"{binding.relay_url}/v1/mailboxes/{binding.cabinet_inbox_id}/envelopes/{source_id}",
                headers=_capability_header(cabinet_read),
            )
            if deleted.status_code not in {204, 404}:
                deleted.raise_for_status()
            continue
        except Exception:
            db.rollback()
            raise

        _deliver_outbox(
            db,
            client=client,
            binding=binding,
            row=outbox,
            cabinet_read_capability=cabinet_read,
            patient_write_capability=patient_write,
        )
        stats["delivered"] += 1

    cutoff = datetime.utcnow() - timedelta(days=RELAY_OUTBOX_RETENTION_DAYS)
    db.query(PatientCompanionRelayOutbox).filter(
        PatientCompanionRelayOutbox.binding_id == binding.id,
        PatientCompanionRelayOutbox.delivered_at.is_not(None),
        PatientCompanionRelayOutbox.delivered_at < cutoff,
    ).delete(synchronize_session=False)
    db.commit()
    return stats


def poll_relay_bindings_once(
    db: Session,
    *,
    client: httpx.Client | None = None,
    unprotect=unprotect_os_bound,
) -> dict[str, int]:
    owned_client = client is None
    client = client or httpx.Client(timeout=10.0)
    totals = {"bindings": 0, "processed": 0, "delivered": 0, "invalid": 0, "failed": 0}
    try:
        bindings = db.query(PatientCompanionRelayBinding).filter(
            PatientCompanionRelayBinding.status == "ACTIVE",
            PatientCompanionRelayBinding.revoked_at.is_(None),
        ).all()
        for binding in bindings:
            totals["bindings"] += 1
            try:
                result = process_relay_binding_once(
                    db,
                    binding=binding,
                    client=client,
                    unprotect=unprotect,
                )
                for key in ("processed", "delivered", "invalid"):
                    totals[key] += result[key]
            except Exception:
                db.rollback()
                totals["failed"] += 1
        return totals
    finally:
        if owned_client:
            client.close()
