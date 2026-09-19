from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from relay.service import create_relay_app

BOOTSTRAP = "b" * 32


def _client(tmp_path):
    app = create_relay_app(
        database_url=f"sqlite:///{tmp_path / 'relay.db'}",
        bootstrap_secret=BOOTSTRAP,
    )
    return TestClient(app)


def _mailbox(client: TestClient):
    response = client.post("/v1/mailboxes", headers={"X-Relay-Bootstrap": BOOTSTRAP})
    assert response.status_code == 201
    return response.json()


def _auth(token: str):
    return {"Authorization": f"RelayCap {token}"}


def test_relay_separates_read_and_write_capabilities(tmp_path):
    client = _client(tmp_path)
    box = _mailbox(client)
    envelope_id = str(uuid.uuid4())
    body = {"envelope_id": envelope_id, "blob": "opaque.jwe.value", "ttl_seconds": 60}

    assert client.post(
        f"/v1/mailboxes/{box['mailbox_id']}/envelopes",
        json=body,
        headers=_auth(box["read_capability"]),
    ).status_code == 403

    pushed = client.post(
        f"/v1/mailboxes/{box['mailbox_id']}/envelopes",
        json=body,
        headers=_auth(box["write_capability"]),
    )
    assert pushed.status_code == 201

    assert client.get(
        f"/v1/mailboxes/{box['mailbox_id']}/envelopes",
        headers=_auth(box["write_capability"]),
    ).status_code == 403

    pulled = client.get(
        f"/v1/mailboxes/{box['mailbox_id']}/envelopes",
        headers=_auth(box["read_capability"]),
    )
    assert pulled.status_code == 200
    assert pulled.json()["items"][0]["blob"] == "opaque.jwe.value"


def test_relay_rejects_cross_mailbox_capability(tmp_path):
    client = _client(tmp_path)
    left = _mailbox(client)
    right = _mailbox(client)
    body = {"envelope_id": str(uuid.uuid4()), "blob": "opaque.jwe.value", "ttl_seconds": 60}

    response = client.post(
        f"/v1/mailboxes/{right['mailbox_id']}/envelopes",
        json=body,
        headers=_auth(left["write_capability"]),
    )
    assert response.status_code == 403


def test_relay_rejects_duplicate_envelope(tmp_path):
    client = _client(tmp_path)
    box = _mailbox(client)
    body = {"envelope_id": str(uuid.uuid4()), "blob": "opaque.jwe.value", "ttl_seconds": 60}
    url = f"/v1/mailboxes/{box['mailbox_id']}/envelopes"

    assert client.post(url, json=body, headers=_auth(box["write_capability"])).status_code == 201
    assert client.post(url, json=body, headers=_auth(box["write_capability"])).status_code == 409


def test_relay_rejects_clinical_metadata_even_if_sender_attempts_it(tmp_path):
    client = _client(tmp_path)
    box = _mailbox(client)
    body = {
        "envelope_id": str(uuid.uuid4()),
        "blob": "opaque.jwe.value",
        "ttl_seconds": 60,
        "patient_id": 123,
    }
    response = client.post(
        f"/v1/mailboxes/{box['mailbox_id']}/envelopes",
        json=body,
        headers=_auth(box["write_capability"]),
    )
    assert response.status_code == 422


def test_relay_delete_requires_read_capability_and_removes_blob(tmp_path):
    client = _client(tmp_path)
    box = _mailbox(client)
    envelope_id = str(uuid.uuid4())
    base = f"/v1/mailboxes/{box['mailbox_id']}/envelopes"
    body = {"envelope_id": envelope_id, "blob": "opaque.jwe.value", "ttl_seconds": 60}

    assert client.post(base, json=body, headers=_auth(box["write_capability"])).status_code == 201
    assert client.delete(f"{base}/{envelope_id}", headers=_auth(box["write_capability"])).status_code == 403
    assert client.delete(f"{base}/{envelope_id}", headers=_auth(box["read_capability"])).status_code == 204
    assert client.get(base, headers=_auth(box["read_capability"])).json()["items"] == []


def test_relay_mailbox_revocation_destroys_queue_and_access(tmp_path):
    client = _client(tmp_path)
    box = _mailbox(client)
    base = f"/v1/mailboxes/{box['mailbox_id']}"
    body = {"envelope_id": str(uuid.uuid4()), "blob": "opaque.jwe.value", "ttl_seconds": 60}

    assert client.post(f"{base}/envelopes", json=body, headers=_auth(box["write_capability"])).status_code == 201
    assert client.delete(base, headers={"X-Relay-Bootstrap": BOOTSTRAP}).status_code == 204
    assert client.get(f"{base}/envelopes", headers=_auth(box["read_capability"])).status_code == 404
