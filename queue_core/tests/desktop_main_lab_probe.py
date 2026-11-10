"""One-shot actual backend.main import + ASGI request FUE-I in synthetic isolation.

Requires explicitly set DIGITALCROWN_QUEUE_MAIN_FUE_RUN=1 and an ephemeral
unshared in-memory clinical database. NEVER starts clinical app lifespan, opens
network ports, installs software or accesses user/cabinet clinical databases.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
import tempfile

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.core.runtime_safety import database_target_fingerprint
from queue_core.persistence.base import QueueBase
from queue_core.persistence.models import (
    QueueLine, QueueResource, QueueTenant, QueueVisitRecord, QueueVisitResource,
)
from queue_core.security.local_auth import LocalIdentityStore
from queue_core.security.operator_store import LocalOperatorStore
from queue_core.security.rbac import Role

CLINICAL_URL = "sqlite:///:memory:"
ADMIN_PASSWORD = "SyntheticMainFUEAdminPassword!!2026"
RECEPTION_PASSWORD = "SyntheticMainFUEReceptionPassword!!2026"

def run() -> None:
    if os.environ.get("DIGITALCROWN_QUEUE_MAIN_FUE_RUN") != "1":
        raise RuntimeError("MAIN_FUE_EXPLICIT_FLAG_REQUIRED")
    with tempfile.TemporaryDirectory(prefix="dc-queue-fue-main-") as temp:
        root = Path(temp)
        (root / ".queue-fue-marker").write_text(
            "DIGITALCROWN_QUEUE_FUE_SYNTHETIC_ONLY_V1", encoding="utf-8"
        )
        os.environ.update({
            "ENVIRONMENT": "test",
            "DATABASE_URL": CLINICAL_URL,
            "DIGITALCROWN_ISOLATED_RUNTIME": "1",
            "DIGITALCROWN_ISOLATION_DB_FINGERPRINT":
                database_target_fingerprint(CLINICAL_URL),
            "DIGITALCROWN_QUEUE_CORE_LAB_ENABLE": "1",
            "DIGITALCROWN_QUEUE_CORE_LAB_ROOT": str(root),
            "SECRET_KEY": "Synthetic_Secret_For_Only_Memory_DB_Main_FUE_2026",
            "SQLCIPHER_KEY_HEX": "c7" * 32,
            "SENTRY_DSN": "",
            "TELEMETRY_ENABLED": "false",
        })
        auth = LocalIdentityStore(root / "auth.sqlite", local_guard=lambda: None)
        challenge = auth.begin_bootstrap()
        auth.enroll_first_admin(challenge, "labadmin", ADMIN_PASSWORD)
        admin = auth.login("labadmin", ADMIN_PASSWORD)
        operators = LocalOperatorStore(auth)
        operators.bind_first_admin(first_admin_session=admin, tenant_id="SYNTHETIC")
        operators.create_operator(
            admin, "reception1", RECEPTION_PASSWORD,
            Role.RECEPTION, queue_ids=("Q1",),
        )
        engine = create_engine("sqlite+pysqlite:///" + (root / "queue.sqlite").as_posix())
        QueueBase.metadata.create_all(engine)
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        with Session(engine) as s:
            s.add_all([
                QueueTenant(id="SYNTHETIC", timezone_name="Africa/Casablanca", created_at_utc=now),
                QueueLine(id="Q1", tenant_id="SYNTHETIC", queue_key="SYN-Q1", is_active=True),
                QueueResource(
                    id="R1", tenant_id="SYNTHETIC", resource_key="SYN-R1",
                    resource_kind="CHAIR", is_active=True,
                ),
            ])
            s.flush()
            s.add(QueueVisitRecord(
                id="V1", tenant_id="SYNTHETIC", queue_id="Q1",
                visit_kind="APPOINTMENT", status="PLANNED",
                scheduled_at_utc=now - timedelta(hours=1), version=0,
            ))
            s.add(QueueVisitResource(
                tenant_id="SYNTHETIC", visit_id="V1", resource_id="R1"
            ))
            s.commit()
        engine.dispose()
        # This import MUST happen after process-local isolation attestation.
        from backend.main import _QUEUE_CORE_LAB_MOUNTED, app
        from backend import database
        from backend.queue_core_desktop_lab import MOUNT_PATH
        assert _QUEUE_CORE_LAB_MOUNTED is True
        assert any(route.path == MOUNT_PATH for route in app.routes)
        assert database.SQLALCHEMY_DATABASE_URL.lower().find("memory:") >= 0
        # DO NOT use TestClient as context manager: that would run the
        # clinical lifespan (and seed/migrate). ASGI calls without context
        # exercise actual backend.main routing + middleware without lifespan.
        # Production-configuration child denies TestClient's fictitious
        # 'testclient' peer. Only real loopback peers are admitted.
        assert TestClient(app).get(MOUNT_PATH + "/v1/queues/Q1/snapshot").status_code == 403

        import anyio
        import httpx

        async def check_real_main():
            transport = httpx.ASGITransport(app=app, client=("127.0.0.1", 51515))
            async with httpx.AsyncClient(
                transport=transport, base_url="http://localhost",
                follow_redirects=False,
            ) as client:
                url = MOUNT_PATH + "/v1"
                preauth = await client.get(url + "/queues/Q1/snapshot")
                assert preauth.status_code == 401, (preauth.status_code, preauth.text[:150])
                response = await client.post(
                    url + "/operators/session",
                    json={"username": "reception1", "password": RECEPTION_PASSWORD},
                )
                assert response.status_code == 200, (response.status_code, response.text[:150])
                token = response.json()["token"]
                headers = {"Authorization": "Bearer " + token}
                snapshot = await client.get(url + "/queues/Q1/snapshot", headers=headers)
                assert snapshot.status_code == 200, (snapshot.status_code, snapshot.text[:150])
                assert {x["id"] for x in snapshot.json()["visits"]} == {"V1"}
                command = await client.post(
                    url + "/visits/V1/commands",
                    headers=headers, json={"command": "check_in", "expected_version": 0},
                )
                assert command.status_code == 200, (command.status_code, command.text[:150])
                assert command.json()["status"] == "WAITING"
                assert (await client.post(url + "/operators/logout", headers=headers)).status_code == 200
                assert (await client.get(url + "/queues/Q1/snapshot", headers=headers)).status_code == 401
        try:
            anyio.run(check_real_main)
        finally:
            # Mandatory on Windows: SQLAlchemy QueuePool otherwise keeps the
            # temporary queue SQLite file locked beyond the test context.
            app.state.queue_core_lab_service._engine.dispose()
            database.engine.dispose()
        print("ACTUAL_BACKEND_MAIN_ROUTING_AND_RBAC_PASS_NO_CLINICAL_LIFESPAN", flush=True)

if __name__ == "__main__":
    run()
