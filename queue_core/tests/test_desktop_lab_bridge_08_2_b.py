"""Desktop main-application mount integration with real FastAPI and synthetic SQLite.

No backend.main import, no clinical startup, no installation or real clinic data.
"""
from pathlib import Path
import shutil

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from queue_core.service.desktop_lab_bridge import (
    MARKER, FLAG, ROOT, MOUNT_PATH, DesktopQueueLabError, attach_queue_core_lab,
    resolve_isolated_lab_root,
)
from queue_core.tests.test_service_auth_08_2_b import local, PASS2


def synthetic_mounted(local, tmp_path):
    root = tmp_path / "dc-queue-fue-fixture"
    root.mkdir()
    (root / ".queue-fue-marker").write_text(MARKER, encoding="utf-8")
    shutil.copyfile(local[0].path, root / "auth.sqlite")
    shutil.copyfile(Path(local[8].url.database), root / "queue.sqlite")
    parent = FastAPI()
    service = attach_queue_core_lab(
        parent, environment="test",
        variables={FLAG: "1", ROOT: str(root)},
        clinical_db_path=tmp_path / "totally-different-clinical.sqlite",
        allow_synthetic_testclient=True, max_sse_frames=2,
    )
    # The shared synthetic operator fixtures use a deterministic test clock.
    # Keep the copied fixture's sessions valid independently of wall-clock date.
    service._operators._clock = lambda: 1_800_000_000
    return parent, service, root


def test_actual_desktop_parent_mount_login_command_and_logout(local, tmp_path):
    parent, _service, _root = synthetic_mounted(local, tmp_path)
    with TestClient(parent) as client:
        base = MOUNT_PATH + "/v1"
        assert client.get(base + "/queues/Q1/snapshot").status_code == 401
        response = client.post(
            base + "/operators/session",
            json={"username": "reception1", "password": PASS2},
        )
        assert response.status_code == 200, response.text
        token = response.json()["token"]
        assert token and len(token) >= 30
        assert response.json()["roles"] == ["reception"]
        assert response.json()["explicit_permissions"] == []
        assert "tenant_id" not in response.json()
        headers = {"Authorization": "Bearer " + token}
        rows = client.get(base + "/queues/Q1/snapshot", headers=headers)
        assert rows.status_code == 200, rows.text
        assert any(x["id"] == "V1" for x in rows.json()["visits"])
        arrived = client.post(
            base + "/visits/V1/commands", headers=headers,
            json={"command": "check_in", "expected_version": 0},
        )
        assert arrived.status_code == 200, arrived.text
        assert arrived.json()["status"] == "WAITING"
        assert client.get(base + "/queues/Q3/snapshot", headers=headers).status_code == 403
        logout = client.post(base + "/operators/logout", headers=headers)
        assert logout.status_code == 200 and logout.json() == {"closed": True}
        assert client.get(base + "/queues/Q1/snapshot", headers=headers).status_code == 401


@pytest.mark.parametrize("environment", ["cabinet", "production", "development", "local"])
def test_lab_mount_never_runs_in_non_test_environment(local, tmp_path, environment):
    root = tmp_path / "dc-queue-fue-fixture"
    root.mkdir()
    (root / ".queue-fue-marker").write_text(MARKER, encoding="utf-8")
    shutil.copyfile(local[0].path, root / "auth.sqlite")
    shutil.copyfile(Path(local[8].url.database), root / "queue.sqlite")
    parent = FastAPI()
    with pytest.raises(DesktopQueueLabError, match="QUEUE_LAB_DISABLED"):
        attach_queue_core_lab(
            parent, environment=environment,
            variables={FLAG: "1", ROOT: str(root)},
        )
    assert all(getattr(x, "path", None) != MOUNT_PATH for x in parent.routes)


def test_mount_requires_prior_existing_synthetic_files_and_marker(tmp_path):
    root = tmp_path / "dc-queue-fue-empty"
    root.mkdir()
    with pytest.raises(DesktopQueueLabError, match="QUEUE_LAB_FILES_MISSING"):
        resolve_isolated_lab_root("test", {FLAG: "1", ROOT: str(root)})
    (root / ".queue-fue-marker").write_text("WRONG", encoding="utf-8")
    (root / "auth.sqlite").touch()
    (root / "queue.sqlite").touch()
    with pytest.raises(DesktopQueueLabError, match="QUEUE_LAB_MARKER_INVALID"):
        resolve_isolated_lab_root("test", {FLAG: "1", ROOT: str(root)})


def test_mount_rejects_clinical_db_collision_and_duplicate_attach(local, tmp_path):
    parent, _service, root = synthetic_mounted(local, tmp_path)
    with pytest.raises(DesktopQueueLabError, match="QUEUE_LAB_CLINICAL_DB_COLLISION"):
        attach_queue_core_lab(
            FastAPI(), environment="test", variables={FLAG: "1", ROOT: str(root)},
            clinical_db_path=root / "queue.sqlite",
        )
    with pytest.raises(DesktopQueueLabError, match="QUEUE_LAB_ALREADY_MOUNTED"):
        attach_queue_core_lab(
            parent, environment="test",
            variables={FLAG: "1", ROOT: str(root)},
        )


def test_mount_login_bad_credentials_and_no_caller_tenant(local, tmp_path):
    parent, _, _ = synthetic_mounted(local, tmp_path)
    with TestClient(parent) as client:
        base = MOUNT_PATH + "/v1"
        bad = client.post(
            base + "/operators/session",
            json={"username": "reception1", "password": "wrong-password-too-long"},
        )
        assert bad.status_code == 401 and bad.json() == {"code": "INVALID_CREDENTIALS"}
        forged = client.post(
            base + "/operators/session",
            json={"username": "reception1", "password": PASS2, "tenant_id": "T2"},
        )
        assert forged.status_code == 422 and forged.json() == {"code": "INVALID_REQUEST"}

def test_queue_lab_import_in_clean_interpreter_never_imports_clinical_backend():
    """Linux slim CI must collect this suite without backend clinical deps."""
    import subprocess
    import sys

    root = Path(__file__).resolve().parents[2]
    code = (
        "import sys; "
        "from queue_core.service.desktop_lab_bridge import attach_queue_core_lab; "
        "assert 'backend' not in sys.modules, 'backend imported by Queue Core LAB'"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=root, capture_output=True, text=True, timeout=30, check=False,
    )
    assert result.returncode == 0, result.stderr
