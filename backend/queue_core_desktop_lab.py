"""LOT08.2-B: strictly test-only Desktop FastAPI mount of Queue Core.

No production mount, no database/schema auto-create, no clinical data or auth
bypass. The caller owns an already isolated, synthetic lab root.
This is NOT a cabinet runtime feature or a release/installer hook.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping

from fastapi import FastAPI
from sqlalchemy import create_engine

from queue_core.security.local_auth import LocalIdentityStore, LocalIdentityError
from queue_core.security.operator_store import LocalOperatorStore
from queue_core.service.authorized_queue import AuthorizedLocalQueue
from queue_core.service.http_transport import create_local_queue_app


MOUNT_PATH = "/api/queue-core-lab"
MARKER = "DIGITALCROWN_QUEUE_FUE_SYNTHETIC_ONLY_V1"
FLAG = "DIGITALCROWN_QUEUE_CORE_LAB_ENABLE"
ROOT = "DIGITALCROWN_QUEUE_CORE_LAB_ROOT"


class DesktopQueueLabError(RuntimeError):
    """Static, secret-free fail-closed startup reason."""


def resolve_isolated_lab_root(
    environment: str,
    variables: Mapping[str, str],
    *,
    clinical_db_path: str | Path | None = None,
) -> Path:
    if environment != "test" or variables.get(FLAG) != "1":
        raise DesktopQueueLabError("QUEUE_LAB_DISABLED")
    value = variables.get(ROOT, "")
    if not isinstance(value, str) or not value or not Path(value).is_absolute():
        raise DesktopQueueLabError("QUEUE_LAB_ABSOLUTE_ROOT_REQUIRED")
    root = Path(value)
    if root.is_symlink() or not root.is_dir() or not root.name.startswith("dc-queue-fue-"):
        raise DesktopQueueLabError("QUEUE_LAB_ROOT_NOT_ISOLATED")
    for filename in (".queue-fue-marker", "auth.sqlite", "queue.sqlite"):
        file = root / filename
        if file.is_symlink() or not file.is_file():
            raise DesktopQueueLabError("QUEUE_LAB_FILES_MISSING")
    if (root / ".queue-fue-marker").read_text(encoding="utf-8").strip() != MARKER:
        raise DesktopQueueLabError("QUEUE_LAB_MARKER_INVALID")
    if clinical_db_path is not None and Path(clinical_db_path).resolve() in {
        (root / "auth.sqlite").resolve(),
        (root / "queue.sqlite").resolve(),
    }:
        raise DesktopQueueLabError("QUEUE_LAB_CLINICAL_DB_COLLISION")
    return root.resolve()


def attach_queue_core_lab(
    desktop: FastAPI,
    *,
    environment: str,
    variables: Mapping[str, str] | None = None,
    clinical_db_path: str | Path | None = None,
    allow_synthetic_testclient: bool = False,
    max_sse_frames: int | None = None,
) -> AuthorizedLocalQueue:
    """Attach to the actual Desktop FastAPI router, never to remote services.

    Normal application imports cannot trigger a mount; the caller must set
    the test-only flag and the synthetic databases must already exist.
    Operator enrollment and grants remain privileged local operations.
    """
    if not isinstance(desktop, FastAPI):
        raise TypeError("FASTAPI_APP_REQUIRED")
    env = variables if variables is not None else os.environ
    root = resolve_isolated_lab_root(
        environment, env, clinical_db_path=clinical_db_path,
    )
    if any(getattr(route, "path", "") == MOUNT_PATH for route in desktop.routes):
        raise DesktopQueueLabError("QUEUE_LAB_ALREADY_MOUNTED")
    auth_store = LocalIdentityStore(
        root / "auth.sqlite",
        local_guard=lambda: (_ for _ in ()).throw(
            LocalIdentityError("LAB_PROVISIONING_FORBIDDEN")
        ),
    )
    operators = LocalOperatorStore(auth_store)
    engine = create_engine(f"sqlite+pysqlite:///{(root / 'queue.sqlite').as_posix()}")
    service = AuthorizedLocalQueue(operators, engine)
    subapp = create_local_queue_app(
        service,
        lab_allow_operator_login=True,
        lab_allow_testclient=allow_synthetic_testclient,
        lab_max_sse_frames=max_sse_frames,
    )
    desktop.mount(MOUNT_PATH, subapp, name="queue-core-lab")
    desktop.state.queue_core_lab_service = service
    return service
