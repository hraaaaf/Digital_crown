from __future__ import annotations

import uuid
from datetime import datetime

import httpx

from backend import models
from backend.models_patient_companion import PatientCompanionAccess, PatientCompanionIdentity, PatientCompanionRelayBinding
from backend.services.patient_companion_relay_client import (
    cabinet_relay_capabilities,
    provision_relay_binding,
)


def _access(db, dentiste):
    patient = models.Patient(
        numero_dossier=f"PCRL-{uuid.uuid4().hex[:8]}",
        nom="Relay",
        prenom="Aya",
        date_naissance=datetime(2010, 1, 1),
        sexe="F",
        employer_id=dentiste.id,
    )
    identity = PatientCompanionIdentity(provider="local_bridge", subject=f"device:{uuid.uuid4()}")
    db.add_all([patient, identity])
    db.flush()
    access = PatientCompanionAccess(
        identity_id=identity.id,
        employer_id=dentiste.id,
        patient_id=patient.id,
        relationship_type="SELF",
    )
    db.add(access)
    db.flush()
    return access


def test_relay_provisioning_splits_patient_and_cabinet_capabilities(db, dentiste):
    access = _access(db, dentiste)
    cabinet_id = str(uuid.uuid4())
    patient_id = str(uuid.uuid4())
    caps = {
        "cabinet_read": "c-read-" + "a" * 43,
        "cabinet_write": "c-write-" + "b" * 43,
        "patient_read": "p-read-" + "c" * 43,
        "patient_write": "p-write-" + "d" * 43,
    }
    provision_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal provision_count
        if request.method == "POST" and request.url.path == "/v1/mailboxes":
            provision_count += 1
            if provision_count == 1:
                return httpx.Response(201, json={
                    "mailbox_id": cabinet_id,
                    "read_capability": caps["cabinet_read"],
                    "write_capability": caps["cabinet_write"],
                })
            return httpx.Response(201, json={
                "mailbox_id": patient_id,
                "read_capability": caps["patient_read"],
                "write_capability": caps["patient_write"],
            })
        return httpx.Response(404)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    protect = lambda clear: b"protected:" + clear
    unprotect = lambda protected: protected.removeprefix(b"protected:")

    binding, bootstrap = provision_relay_binding(
        db,
        access=access,
        relay_url="https://relay.test",
        bootstrap_secret="s" * 32,
        protect=protect,
        client=client,
    )

    assert bootstrap.cabinet_write_capability == caps["cabinet_write"]
    assert bootstrap.patient_read_capability == caps["patient_read"]
    assert caps["cabinet_read"] not in repr(bootstrap)
    assert caps["patient_write"] not in repr(bootstrap)

    cabinet_read, patient_write = cabinet_relay_capabilities(binding, unprotect=unprotect)
    assert cabinet_read == caps["cabinet_read"]
    assert patient_write == caps["patient_write"]
    assert caps["cabinet_write"] not in binding.protected_cabinet_read_cap_b64
    assert caps["patient_read"] not in binding.protected_patient_write_cap_b64
    assert db.query(PatientCompanionRelayBinding).filter_by(access_id=access.id).count() == 1


def test_revoke_pending_becomes_revoked_only_after_both_mailboxes_are_deprovisioned(db, dentiste):
    from backend.services.patient_companion_relay_worker import poll_relay_bindings_once

    access = _access(db, dentiste)
    binding = PatientCompanionRelayBinding(
        access_id=access.id,
        relay_url="https://relay.test",
        cabinet_inbox_id=str(uuid.uuid4()),
        patient_inbox_id=str(uuid.uuid4()),
        protected_cabinet_read_cap_b64="unused",
        protected_patient_write_cap_b64="unused",
        status="REVOKE_PENDING",
    )
    db.add(binding)
    db.commit()

    deleted = []
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "DELETE":
            deleted.append(request.url.path)
            return httpx.Response(204)
        return httpx.Response(404)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    result = poll_relay_bindings_once(
        db,
        client=client,
        bootstrap_secret="s" * 32,
    )
    db.refresh(binding)

    assert binding.status == "REVOKED"
    assert binding.revoked_at is not None
    assert len(deleted) == 2
    assert result["failed"] == 0


def test_delivered_ack_marker_survives_source_delete_failure(db, dentiste):
    from backend.models_patient_companion import PatientCompanionRelayOutbox
    from backend.services.patient_companion_relay_worker import _deliver_outbox

    access = _access(db, dentiste)
    binding = PatientCompanionRelayBinding(
        access_id=access.id,
        relay_url="https://relay.test",
        cabinet_inbox_id=str(uuid.uuid4()),
        patient_inbox_id=str(uuid.uuid4()),
        protected_cabinet_read_cap_b64="unused",
        protected_patient_write_cap_b64="unused",
        status="ACTIVE",
    )
    db.add(binding)
    db.flush()
    row = PatientCompanionRelayOutbox(
        binding_id=binding.id,
        source_envelope_id=str(uuid.uuid4()),
        ack_envelope_id=str(uuid.uuid4()),
        blob="opaque-ack",
    )
    db.add(row)
    db.commit()

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            return httpx.Response(201, json={})
        if request.method == "DELETE":
            return httpx.Response(503, json={"detail": "temporary"})
        return httpx.Response(404)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    try:
        _deliver_outbox(
            db,
            client=client,
            binding=binding,
            row=row,
            cabinet_read_capability="r" * 43,
            patient_write_capability="w" * 43,
        )
    except httpx.HTTPStatusError:
        pass
    db.refresh(row)
    assert row.delivered_at is not None
