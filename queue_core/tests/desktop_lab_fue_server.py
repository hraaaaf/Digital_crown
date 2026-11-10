"""Explicit synthetic-only localhost FUE-G backend runner.

NEVER imported in clinic runtime. No clinical DB, no app import, no installation.
Start with DIGITALCROWN_QUEUE_FUE_RUN=1 and stop after visual proof.
"""
from __future__ import annotations

import os
from pathlib import Path
import tempfile
import threading
import time
from datetime import datetime, timedelta, timezone

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.queue_core_desktop_lab import (
    MARKER, FLAG, ROOT, attach_queue_core_lab,
)
from queue_core.persistence.base import QueueBase
from queue_core.persistence.models import (
    QueueLine, QueueResource, QueueTenant, QueueVisitRecord, QueueVisitResource,
)
from queue_core.security.local_auth import LocalIdentityStore
from queue_core.security.operator_store import LocalOperatorStore
from queue_core.security.rbac import Permission, Role


ADMIN_PASSWORD = "SyntheticAdminPassword!!2026"
OP_PASSWORD = "SyntheticStaffPassword!!2026"
QUEUE_PORT = 18987


def run() -> None:
    if os.environ.get("DIGITALCROWN_QUEUE_FUE_RUN") != "1":
        raise RuntimeError("SYNTHETIC_FUE_EXPLICIT_FLAG_REQUIRED")
    # Dedicated fresh random tmp root. Not the clinical profile or cabinet app.
    with tempfile.TemporaryDirectory(prefix="dc-queue-fue-") as tmp:
        root = Path(tmp)
        (root / ".queue-fue-marker").write_text(MARKER, encoding="utf-8")
        auth = LocalIdentityStore(root / "auth.sqlite", local_guard=lambda: None)
        challenge = auth.begin_bootstrap()
        auth.enroll_first_admin(challenge, "labadmin", ADMIN_PASSWORD)
        admin_session = auth.login("labadmin", ADMIN_PASSWORD)
        operators = LocalOperatorStore(auth)
        operators.bind_first_admin(first_admin_session=admin_session, tenant_id="T1")
        operators.create_operator(
            admin_session, "reception1", OP_PASSWORD, Role.RECEPTION,
            queue_ids=("Q1",),
        )
        staff_id = operators.create_operator(
            admin_session, "chairman1", OP_PASSWORD, Role.STAFF,
            queue_ids=("Q1",), resource_ids=("R1",),
            grants=(Permission.QUEUE_CHAIR, Permission.QUEUE_DONE),
        )
        engine = create_engine("sqlite+pysqlite:///" + (root / "queue.sqlite").as_posix())
        QueueBase.metadata.create_all(engine)
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        with Session(engine) as s:
            s.add_all([
                QueueTenant(id="T1", timezone_name="Africa/Casablanca", created_at_utc=now),
                QueueLine(id="Q1", tenant_id="T1", queue_key="FUE-LAB", is_active=True),
                QueueResource(
                    id="R1", tenant_id="T1", resource_key="SYNTHETIC-CHAIR",
                    resource_kind="CHAIR", is_active=True,
                ),
            ])
            s.flush()
            for id, hours in (("V1", 2), ("V2", 1)):
                s.add(QueueVisitRecord(
                    id=id, tenant_id="T1", queue_id="Q1",
                    visit_kind="APPOINTMENT", status="PLANNED",
                    scheduled_at_utc=now - timedelta(hours=hours), version=0,
                ))
                s.add(QueueVisitResource(tenant_id="T1", visit_id=id, resource_id="R1"))
            s.commit()
        engine.dispose()
        parent = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
        parent.add_middleware(
            CORSMiddleware,
            allow_origins=["http://127.0.0.1:5173"],
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["Authorization", "Content-Type", "Accept", "Last-Event-ID"],
            allow_credentials=False,
        )
        attach_queue_core_lab(
            parent, environment="test",
            variables={FLAG: "1", ROOT: str(root)},
        )
        # Out-of-band destructive control ONLY in this throwaway synthetic root.
        # No publicly accessible revoke endpoint or online admin credential.
        stop = threading.Event()

        def offline_revoke_when_requested() -> None:
            marker = root / "REVOKE_STAFF_SYNTHETIC"
            while not stop.wait(0.1):
                if marker.exists():
                    marker.unlink()
                    operators.disable_operator(admin_session, staff_id)
                    (root / "STAFF_REVOKED_SYNTHETIC").write_text("OK", encoding="utf-8")
                    return

        watcher = threading.Thread(target=offline_revoke_when_requested, daemon=True)
        watcher.start()
        print("SYNTHETIC_ONLY_ROOT=" + str(root), flush=True)
        print("SYNTHETIC_ONLY_PORT=" + str(QUEUE_PORT), flush=True)
        try:
            uvicorn.run(
                parent, host="127.0.0.1", port=QUEUE_PORT,
                log_level="warning", access_log=False,
            )
        finally:
            stop.set()
            watcher.join(timeout=1)
            engine.dispose()


if __name__ == "__main__":
    run()
