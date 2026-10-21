"""Patient uploads must not invalidate an immutable cabinet release."""
import asyncio
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi import BackgroundTasks, HTTPException, UploadFile

from backend.core.media_paths import get_imaging_root


def test_imaging_root_uses_isolated_media_root(monkeypatch, tmp_path):
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("MEDIA_ROOT", str(tmp_path / "media"))
    assert get_imaging_root() == tmp_path / "media" / "uploads"


def test_rehearsal_imaging_rejects_unisolated_root(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "storage_rehearsal")
    monkeypatch.delenv("MEDIA_ROOT", raising=False)
    with pytest.raises(RuntimeError, match="Unsafe MEDIA_ROOT"):
        get_imaging_root()


def test_radio_upload_does_not_write_release(monkeypatch, tmp_path):
    from backend.routers import ia

    monkeypatch.setenv("MEDIA_ROOT", str(tmp_path / "media"))
    release = tmp_path / "release" / "backend"
    release.mkdir(parents=True)
    monkeypatch.setattr(ia, "BASE_DIR", str(release))
    guard = MagicMock()
    monkeypatch.setattr(ia, "assert_patient_access", guard)
    service = MagicMock()
    service.process_new_radio.return_value = {"id": 1}
    monkeypatch.setattr(ia, "CephaloService", lambda db: service)
    db, user = MagicMock(), MagicMock()
    upload = UploadFile(filename="synthetic.jpg", file=BytesIO(b"synthetic-test-bytes"))
    result = asyncio.run(ia.upload_radio(1, BackgroundTasks(), upload, db, user))
    guard.assert_called_once_with(1, user, db)
    path = Path(service.process_new_radio.call_args.args[1])
    assert path.parent == get_imaging_root() / "radios"
    assert path.read_bytes() == b"synthetic-test-bytes"
    assert result["image_path"].startswith("api/static/uploads/radios/")
    assert not list(release.rglob("*"))


@pytest.mark.parametrize("modality", ["radios", "panoramic"])
def test_radio_read_uses_external_storage_after_tenant_guard(monkeypatch, tmp_path, modality):
    import backend.main as main

    monkeypatch.setenv("MEDIA_ROOT", str(tmp_path / "media"))
    root = get_imaging_root() / modality
    root.mkdir(parents=True)
    (root / "synthetic.jpg").write_bytes(b"synthetic-test-bytes")
    guard = MagicMock()
    monkeypatch.setattr(main, "_assert_media_tenant", guard)
    # This positive storage test must explicitly supply the clinical permission.
    # Other tests below prove that missing permission is denied before tenant lookup.
    monkeypatch.setattr(main, "has_permission", lambda _user, permission: permission == "cephalo")
    user, db = MagicMock(), MagicMock()
    route = main.serve_radios if modality == "radios" else main.serve_panoramic
    response = asyncio.run(route("synthetic.jpg", user, db))
    guard.assert_called_once()
    assert Path(response.path) == root / "synthetic.jpg"


def test_radio_read_preserves_legacy_storage(monkeypatch, tmp_path):
    import backend.main as main

    monkeypatch.setenv("MEDIA_ROOT", str(tmp_path / "media"))
    legacy = tmp_path / "legacy"
    (legacy / "radios").mkdir(parents=True)
    (legacy / "radios" / "synthetic.jpg").write_bytes(b"synthetic-test-bytes")
    monkeypatch.setattr(main, "UPLOAD_DIR", str(legacy))
    monkeypatch.setattr(main, "_assert_media_tenant", MagicMock())
    monkeypatch.setattr(main, "has_permission", lambda _user, permission: permission == "cephalo")
    response = asyncio.run(main.serve_radios("synthetic.jpg", MagicMock(), MagicMock()))
    assert Path(response.path) == legacy / "radios" / "synthetic.jpg"


def test_radio_read_requires_cephalo_permission_before_tenant_query(monkeypatch):
    import backend.main as main

    tenant_guard = MagicMock()
    file_serve = MagicMock()
    monkeypatch.setattr(main, "_assert_media_tenant", tenant_guard)
    monkeypatch.setattr(main, "_serve_protected_file", file_serve)
    monkeypatch.setattr(main, "has_permission", lambda _user, _permission: False)

    with pytest.raises(HTTPException) as denied:
        asyncio.run(main.serve_radios("synthetic.jpg", MagicMock(), MagicMock()))

    assert denied.value.status_code == 403
    assert "cephalo" in str(denied.value.detail)
    tenant_guard.assert_not_called()
    file_serve.assert_not_called()


def test_radio_read_denied_before_serving_file(monkeypatch):
    import backend.main as main

    def deny(*args, **kwargs):
        raise HTTPException(status_code=403, detail="Denied")

    monkeypatch.setattr(main, "_assert_media_tenant", deny)
    serve = MagicMock()
    monkeypatch.setattr(main, "_serve_protected_file", serve)
    with pytest.raises(HTTPException) as error:
        asyncio.run(main.serve_radios("synthetic.jpg", MagicMock(), MagicMock()))
    assert error.value.status_code == 403
    serve.assert_not_called()


def test_srpose_failure_upload_is_denied_and_uncommitted_radio_erased(monkeypatch, tmp_path):
    """A failed initial analysis is never exposed as a successful manual draft."""
    from backend.routers import ia

    storage = tmp_path / "isolated-radios"
    storage.mkdir()
    monkeypatch.setattr(ia, "RADIO_DIR", str(storage))
    monkeypatch.setattr(ia, "assert_patient_access", MagicMock())
    service = MagicMock()
    service.process_new_radio.side_effect = ValueError(
        "L'IA n'a détecté aucun point sur cette image. Placement manuel requis."
    )
    monkeypatch.setattr(ia, "CephaloService", lambda db: service)

    upload = UploadFile(filename="synthetic.jpg", file=BytesIO(b"synthetic-test-bytes"))
    with pytest.raises(HTTPException) as failure:
        asyncio.run(ia.upload_radio(1, BackgroundTasks(), upload, MagicMock(), MagicMock()))

    assert failure.value.status_code == 400
    assert "Placement manuel requis" in str(failure.value.detail)
    assert list(storage.iterdir()) == []
    service.process_new_radio.assert_called_once()
