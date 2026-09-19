from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from relay.service import create_relay_app

BOOTSTRAP = "b" * 32


def _client(tmp_path):
    db_path = tmp_path / "relay.db"
    app = create_relay_app(
        database_url=f"sqlite:///{db_path}",
        bootstrap_secret=BOOTSTRAP,
        allowed_origins=("https://digitalcrown.local:8005",),
        create_schema=True,
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


def test_relay_package_has_no_cabinet_backend_imports():
    from pathlib import Path

    relay_root = Path(__file__).resolve().parents[2] / "relay"
    source = "\n".join(
        p.read_text(encoding="utf-8")
        for p in relay_root.glob("*.py")
    )
    assert "from backend" not in source
    assert "import backend" not in source
    assert "models_patient" not in source
    assert "get_db" not in source


def test_relay_responses_are_no_store_and_cors_is_origin_allowlisted(tmp_path):
    client = _client(tmp_path)
    box_response = client.post("/v1/mailboxes", headers={"X-Relay-Bootstrap": BOOTSTRAP})
    assert box_response.headers["cache-control"] == "no-store"
    box = box_response.json()

    preflight = client.options(
        f"/v1/mailboxes/{box['mailbox_id']}/envelopes",
        headers={
            "Origin": "https://digitalcrown.local:8005",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )
    assert preflight.status_code == 200
    assert preflight.headers["access-control-allow-origin"] == "https://digitalcrown.local:8005"

    denied = client.options(
        f"/v1/mailboxes/{box['mailbox_id']}/envelopes",
        headers={
            "Origin": "https://evil.example",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert denied.headers.get("access-control-allow-origin") is None


def test_relay_database_stores_only_capability_hashes(tmp_path):
    client = _client(tmp_path)
    box = _mailbox(client)

    db_path = tmp_path / "relay.db"
    with sqlite3.connect(db_path) as db:
        row = db.execute(
            "SELECT read_capability_hash, write_capability_hash FROM relay_mailboxes WHERE id = ?",
            (box["mailbox_id"],),
        ).fetchone()

    assert row is not None
    assert len(row[0]) == 64 and len(row[1]) == 64
    assert box["read_capability"] not in row
    assert box["write_capability"] not in row


def test_expired_envelope_is_not_returned(tmp_path):
    client = _client(tmp_path)
    box = _mailbox(client)
    envelope_id = str(uuid.uuid4())
    base = f"/v1/mailboxes/{box['mailbox_id']}/envelopes"
    body = {"envelope_id": envelope_id, "blob": "opaque.jwe.value", "ttl_seconds": 60}
    assert client.post(base, json=body, headers=_auth(box["write_capability"])).status_code == 201

    expired = (datetime.utcnow() - timedelta(seconds=1)).isoformat(sep=" ")
    with sqlite3.connect(tmp_path / "relay.db") as db:
        db.execute(
            "UPDATE relay_envelopes SET expires_at = ? WHERE envelope_id = ?",
            (expired, envelope_id),
        )
        db.commit()

    pulled = client.get(base, headers=_auth(box["read_capability"]))
    assert pulled.status_code == 200
    assert pulled.json()["items"] == []
