"""LOT08.2-B real FastAPI ASGI + SSE FUE-I, synthetic local-only LAB.

No listening port, deployment, clinic DB, actual patients or devices.
"""
from __future__ import annotations

import json
import re

import anyio
import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from queue_core.persistence.models import QueueVisitRecord
from queue_core.security.rbac import Permission as P
from queue_core.service.http_transport import (
    authenticated_event_frames, create_local_queue_app,
)
from queue_core.tests.test_service_auth_08_2_b import local, PASS2


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


def body(command, version, *, resource_id=None, reason_code=None):
    return {
        "command": command,
        "expected_version": version,
        "resource_id": resource_id,
        "reason_code": reason_code,
    }


def app_for(lab, *, cap=2):
    return create_local_queue_app(
        lab[7], lab_allow_testclient=True,
        lab_max_sse_frames=cap, poll_interval=0.01,
    )


def test_http_real_command_transition_snapshot_and_event_replay(local):
    _, _, _, reception, worker, _, _, service, engine = local
    with TestClient(app_for(local)) as client:
        checkin = client.post("/v1/visits/V1/commands", headers=bearer(reception),
                              json=body("check_in", 0))
        assert checkin.status_code == 200, checkin.text
        assert checkin.json()["status"] == "WAITING"
        assert checkin.json()["version"] == 2
        call = client.post("/v1/visits/V1/commands", headers=bearer(worker),
                           json=body("call", 2, resource_id="R1"))
        assert call.status_code == 200, call.text
        chair = client.post("/v1/visits/V1/commands", headers=bearer(worker),
                            json=body("chair", 3, resource_id="R1"))
        assert chair.status_code == 200, chair.text
        done = client.post("/v1/visits/V1/commands", headers=bearer(worker),
                           json=body("done", 5))
        assert done.status_code == 200, done.text
        assert done.json()["version"] == 7
        snapshot = client.get("/v1/queues/Q1/snapshot", headers=bearer(reception))
        assert snapshot.status_code == 200
        assert {v["id"]: v["status"] for v in snapshot.json()["visits"]} == {
            "V1": "DONE", "V2": "PLANNED",
        }
        page1 = client.get("/v1/queues/Q1/events?limit=3", headers=bearer(worker))
        assert page1.status_code == 200, page1.text
        assert len(page1.json()["events"]) == 3
        after = page1.json()["events"][-1]["id"]
        page2 = client.get(
            f"/v1/queues/Q1/events?limit=3&after_event_id={after}",
            headers=bearer(worker),
        )
        assert page2.status_code == 200
        assert len(page2.json()["events"]) == 3
        assert [x["aggregate_version"] for x in page1.json()["events"]] == [1, 2, 3]
        assert [x["aggregate_version"] for x in page2.json()["events"]] == [4, 5, 6]
        for response in (checkin, call, chair, done, snapshot, page1):
            assert "no-store" in response.headers["cache-control"]
            assert response.headers["x-content-type-options"] == "nosniff"
    with Session(engine) as s:
        row = s.get(QueueVisitRecord, "V1")
        assert row.status == "DONE" and row.version == 7


def test_http_never_accepts_missing_bearer_url_token_or_client_scope(local):
    _, _, _, reception, worker, _, _, _, engine = local
    with TestClient(app_for(local)) as client:
        no_auth = client.get("/v1/queues/Q1/snapshot")
        assert (no_auth.status_code, no_auth.json()) == (401, {"code": "AUTH_REQUIRED"})
        old_cookie = client.get("/v1/queues/Q1/snapshot", cookies={"session": worker})
        assert old_cookie.status_code == 401
        q_token = client.get(
            f"/v1/queues/Q1/snapshot?token={worker}",
            headers=bearer(worker),
        )
        assert q_token.status_code == 401
        assert worker not in q_token.text
        forged = client.post(
            "/v1/visits/V1/commands", headers=bearer(reception),
            json={
                **body("check_in", 0),
                "tenant_id": "T2",
                "actor_id": "admin",
                "authorized": True,
            },
        )
        assert forged.status_code == 422
        assert forged.json() == {"code": "INVALID_REQUEST"}
        unknown = client.post(
            "/v1/visits/V1/commands", headers=bearer(reception),
            json=body("superadmin", 0),
        )
        assert unknown.status_code == 422
        invalid_session = client.post(
            "/v1/visits/V1/commands", headers=bearer("a" * 43),
            json=body("check_in", 0),
        )
        assert invalid_session.status_code == 401
    with Session(engine) as s:
        assert s.get(QueueVisitRecord, "V1").version == 0


def test_http_no_tenant_or_resource_idor_and_no_implicit_admin_ops(local):
    _, _, admin, reception, worker, _, _, _, engine = local
    with TestClient(app_for(local)) as client:
        denied_cases = [
            client.post("/v1/visits/V3/commands", headers=bearer(reception),
                        json=body("check_in", 0)),
            client.post("/v1/visits/V4/commands", headers=bearer(reception),
                        json=body("check_in", 0)),
            client.post("/v1/visits/V1/commands", headers=bearer(worker),
                        json=body("call", 0, resource_id="R2")),
            client.post("/v1/visits/V1/commands", headers=bearer(admin),
                        json=body("check_in", 0)),
            client.get("/v1/queues/Q3/snapshot", headers=bearer(reception)),
            client.get("/v1/queues/Q3/events", headers=bearer(worker)),
        ]
        assert all(x.status_code == 403 for x in denied_cases)
        assert all(x.json() == {"code": "AUTHZ_DENIED"} for x in denied_cases)
    with Session(engine) as s:
        assert s.get(QueueVisitRecord, "V1").version == 0
        assert s.get(QueueVisitRecord, "V3").version == 0


def test_http_sse_authenticated_handshake_replay_and_last_event_id(local):
    _, _, _, reception, worker, _, _, service, _ = local
    service.perform(reception, service_command("check_in"), "V1", expected_version=0)
    with TestClient(app_for(local, cap=2)) as client:
        resp = client.get(
            "/v1/queues/Q1/stream",
            headers={**bearer(worker), "Accept": "text/event-stream"},
        )
        assert resp.status_code == 200, resp.text
        assert resp.headers["content-type"].startswith("text/event-stream")
        assert "no-store" in resp.headers["cache-control"]
        assert resp.headers["x-accel-buffering"] == "no"
        lines = resp.text.splitlines()
        ids = [s.split(": ", 1)[1] for s in lines if s.startswith("id: ")]
        data = [json.loads(s.split(": ", 1)[1]) for s in lines if s.startswith("data: ")]
        assert len(ids) == 2 and len(data) == 2
        assert [i["version"] for i in data] == [1, 2]
        assert all(x["type"] in {"ARRIVED", "WAITING_ENTERED"} for x in data)
        assert all("token" not in x and "patient" not in x for x in data)
        assert worker not in resp.text
        unauthorized = client.get("/v1/queues/Q1/stream", headers=bearer("Z" * 43))
        assert unauthorized.status_code == 401
        wrong_tenant = client.get("/v1/queues/Q3/stream", headers=bearer(worker))
        assert wrong_tenant.status_code == 403
        invalid_cursor = client.get(
            "/v1/queues/Q1/stream",
            headers={**bearer(worker), "Last-Event-ID": "foreign_event"},
        )
        assert invalid_cursor.status_code == 403
    # A valid cursor after the first event yields the second, using a LAB cap.
    with TestClient(app_for(local, cap=1)) as client:
        remainder = client.get(
            "/v1/queues/Q1/stream",
            headers={**bearer(worker), "Last-Event-ID": ids[0]},
        )
        assert remainder.status_code == 200
        versions = [json.loads(s.split(": ", 1)[1])["version"]
                    for s in remainder.text.splitlines() if s.startswith("data: ")]
        assert versions == [2]


def service_command(text):
    from queue_core.service.authorized_queue import HumanCommand
    return HumanCommand(text)


def test_sse_live_revocation_drops_buffered_event_not_only_next_page(local):
    _, operators, admin, reception, worker, _, staff_id, svc, _ = local
    svc.perform(reception, service_command("check_in"), "V1", expected_version=0)

    async def scenario():
        frames = authenticated_event_frames(
            svc, worker, "Q1", poll_interval=0.01,
        )
        try:
            first = await anext(frames)
            assert "version" in first and '"version":1' in first
            # The first poll already buffered two real events. Revoke between
            # these frames: the second must NOT be emitted.
            await anyio.to_thread.run_sync(
                lambda: operators.replace_rights(admin, staff_id, queue_ids=()),
            )
            with pytest.raises(StopAsyncIteration):
                await anext(frames)
        finally:
            await frames.aclose()
    anyio.run(scenario)


def test_http_sse_cross_queue_cursor_denied_before_200(local):
    _, _, _, reception, worker, _, _, svc, _ = local
    svc.perform(reception, service_command("check_in"), "V1", expected_version=0)
    first_id = svc.replay_events(worker, "Q1")[0].id
    with TestClient(app_for(local, cap=1)) as client:
        foreign = client.get(
            "/v1/queues/Q2/stream",
            headers={**bearer(worker), "Last-Event-ID": first_id},
        )
        assert foreign.status_code == 403
        bad_host = client.get(
            "/v1/queues/Q1/snapshot",
            headers={**bearer(worker), "Host": "external.example"},
        )
        assert bad_host.status_code == 400


def test_http_does_not_accept_non_loopback_asgi_peer(local):
    app = create_local_queue_app(local[7], lab_allow_testclient=False)
    async def scenario():
        transport = httpx.ASGITransport(app=app, client=("192.0.2.1", 4432))
        async with httpx.AsyncClient(transport=transport, base_url="http://localhost") as client:
            response = await client.get(
                "/v1/queues/Q1/snapshot", headers=bearer(local[4]),
            )
            assert response.status_code == 403
            assert response.json() == {"code": "LOCAL_ONLY"}
    anyio.run(scenario)


def test_http_revoke_then_next_command_and_new_session_with_new_rights(local):
    _, operators, admin, reception, worker, _, staff_id, _, _ = local
    with TestClient(app_for(local)) as client:
        assert client.post(
            "/v1/visits/V1/commands", headers=bearer(reception),
            json=body("check_in", 0),
        ).status_code == 200
        operators.replace_rights(admin, staff_id, queue_ids=("Q2",))
        denied = client.post(
            "/v1/visits/V1/commands", headers=bearer(worker),
            json=body("call", 2, resource_id="R1"),
        )
        assert denied.status_code == 401
        fresh = operators.login_operator("T1", "chairman1", PASS2)
        no_scope = client.post(
            "/v1/visits/V1/commands", headers=bearer(fresh),
            json=body("call", 2, resource_id="R1"),
        )
        assert no_scope.status_code == 403


def test_invalid_http_body_returns_safe_code_without_reflecting_payload(local):
    _, _, _, reception, _, _, _, _, _ = local
    patient_text = "SensitiveSyntheticValueDoNotEcho"
    with TestClient(app_for(local)) as client:
        response = client.post(
            "/v1/visits/V1/commands",
            headers=bearer(reception),
            json={**body("check_in", 0), "patient_name": patient_text},
        )
        assert response.status_code == 422
        assert response.json() == {"code": "INVALID_REQUEST"}
        assert patient_text not in response.text


def test_openapi_docs_disabled_by_default(local):
    with TestClient(app_for(local)) as client:
        assert client.get("/docs").status_code == 404
        assert client.get("/openapi.json").status_code == 404
        assert client.get("/redoc").status_code == 404


def test_unauthenticated_malformed_command_is_401_before_input_validation(local):
    with TestClient(app_for(local)) as client:
        response = client.post(
            "/v1/visits/V1/commands",
            json={"command": "not-a-real-command", "expected_version": "wrong"},
        )
        assert response.status_code == 401
        assert response.json() == {"code": "AUTH_REQUIRED"}
        response = client.post(
            "/v1/visits/V1/commands",
            headers=bearer("X" * 43),
            json={"command": "not-a-real-command", "expected_version": "wrong"},
        )
        assert response.status_code == 401
        assert response.json() == {"code": "AUTH_REQUIRED"}


def test_real_asgi_sse_revocation_after_first_frame_emits_no_second(local, monkeypatch):
    _, operators, admin, reception, worker, _, staff_id, svc, _ = local
    svc.perform(reception, service_command("check_in"), "V1", expected_version=0)
    original = svc.require_queue_read
    checks = [0]

    def revoke_before_second_frame(token, queue_id):
        checks[0] += 1
        if checks[0] == 2:
            operators.replace_rights(admin, staff_id, queue_ids=())
        return original(token, queue_id)

    monkeypatch.setattr(svc, "require_queue_read", revoke_before_second_frame)
    with TestClient(app_for(local, cap=2)) as client:
        response = client.get(
            "/v1/queues/Q1/stream",
            headers={**bearer(worker), "Accept": "text/event-stream"},
        )
        assert response.status_code == 200
        versions = [
            json.loads(line.split(": ", 1)[1])["version"]
            for line in response.text.splitlines()
            if line.startswith("data: ")
        ]
        assert versions == [1], response.text
        assert checks[0] == 2
        assert client.get("/v1/queues/Q1/snapshot", headers=bearer(worker)).status_code == 401


def test_corrupted_event_id_cannot_inject_sse_fields():
    from datetime import datetime, timezone
    from queue_core.security.rbac import AuthorizationError
    from queue_core.service.authorized_queue import QueueEventView
    from queue_core.service.http_transport import _frame

    forged = QueueEventView(
        id="attacker\nid: another_event",
        visit_ref="V1", event_type="CALLED",
        aggregate_version=1, occurred_at_utc=datetime.now(timezone.utc),
    )
    with pytest.raises(AuthorizationError, match="AUTHZ_DENIED"):
        _frame(forged)
