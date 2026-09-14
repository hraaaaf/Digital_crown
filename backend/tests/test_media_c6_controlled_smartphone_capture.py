import asyncio
from pathlib import Path
from types import SimpleNamespace

from backend.routers import mobile_resource_bridge as bridge
from backend.services import clinical_asset_ingestion


class _Upload:
    content_type = "image/jpeg"
    filename = "capture.jpg"

    def __init__(self, payload=b"raw-camera-bytes", content_type=None):
        self.payload = payload
        self.closed = False
        if content_type is not None:
            self.content_type = content_type

    async def read(self, _limit):
        return self.payload

    async def close(self):
        self.closed = True


class _DB:
    def __init__(self):
        self.commits = 0
        self.rollbacks = 0
        self.refreshed = []

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def refresh(self, obj):
        self.refreshed.append(obj)


def _valid_mobile_context(monkeypatch):
    user = SimpleNamespace(id=7, get_employer_id=lambda: 41)
    context = {"resource_type": "patient", "resource_id": 19, "device_id": "device-abc"}
    patient = SimpleNamespace(id=19)
    monkeypatch.setattr(bridge, "_validated_mobile_context", lambda *_: (user, context))
    monkeypatch.setattr(bridge, "_patient_resource", lambda *_: patient)
    return user, context, patient


def test_c6_mobile_photo_uses_media_core_without_legacy_archive(monkeypatch):
    source = Path(bridge.__file__).read_text(encoding="utf-8")
    block = source[source.index("@router.post('/resource-context-photo'"):source.index("@router.post('/resource-context-document-scan'")]
    assert "ingest_clinical_asset_bytes" in block
    assert "source_kind='DEVICE_CAPTURE'" in block
    assert "archive_service.archive_document" not in block
    assert "MOBILE_RESOURCE_BRIDGE" in block

    db = _DB()
    upload = _Upload()
    _valid_mobile_context(monkeypatch)
    asset = SimpleNamespace(
        id=501, asset_type="PHOTO", source_kind="DEVICE_CAPTURE", mime_type="image/jpeg", created_at=None
    )
    thumb = SimpleNamespace(id=502)
    captured = {}

    monkeypatch.setattr(bridge, "_normalize_clinical_photo", lambda raw: b"normalized-jpeg")

    def fake_ingest(_db, **kwargs):
        captured.update(kwargs)
        return SimpleNamespace(asset=asset, thumbnail_asset=thumb)

    monkeypatch.setattr(clinical_asset_ingestion, "ingest_clinical_asset_bytes", fake_ingest)
    monkeypatch.setattr(bridge._documents.audit_service, "log", lambda **_: None)

    response = asyncio.run(bridge.upload_resource_context_photo(
        context_key="opaque-context", file=upload, authorization="Bearer mobile", db=db
    ))

    assert upload.closed is True
    assert db.commits == 1
    assert db.rollbacks == 0
    assert captured["employer_id"] == 41
    assert captured["patient_id"] == 19
    assert captured["asset_type"] == "PHOTO"
    assert captured["source_kind"] == "DEVICE_CAPTURE"
    assert captured["claimed_mime_type"] == "image/jpeg"
    assert captured["created_by"] == 7
    assert captured["source_ref"] == "MOBILE_RESOURCE_BRIDGE"
    assert captured["provenance_json"]["device_id"] == "device-abc"
    assert response["asset"]["id"] == 501
    assert response["asset"]["thumbnail_asset_id"] == 502
    assert response["document"]["document_type"] == "PHOTO_CLINIQUE"


def test_c6_invalid_context_is_rejected_before_media_write(monkeypatch):
    upload = _Upload()
    db = _DB()

    def reject(*_):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Contexte mobile incompatible avec cette session.")

    monkeypatch.setattr(bridge, "_validated_mobile_context", reject)
    called = {"ingest": False}

    def fake_ingest(*_args, **_kwargs):
        called["ingest"] = True

    monkeypatch.setattr(clinical_asset_ingestion, "ingest_clinical_asset_bytes", fake_ingest)

    try:
        asyncio.run(bridge.upload_resource_context_photo(
            context_key="bad-context", file=upload, authorization="Bearer bad", db=db
        ))
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 403
    else:
        raise AssertionError("invalid context must be rejected")

    assert called["ingest"] is False
    assert db.commits == 0


def test_c6_spoofed_jpeg_magic_bytes_are_rejected_before_media_write(monkeypatch):
    db = _DB()
    upload = _Upload(payload=b"not-a-real-jpeg", content_type="image/jpeg")
    _valid_mobile_context(monkeypatch)
    called = {"ingest": False}

    def fake_ingest(*_args, **_kwargs):
        called["ingest"] = True

    monkeypatch.setattr(clinical_asset_ingestion, "ingest_clinical_asset_bytes", fake_ingest)

    try:
        asyncio.run(bridge.upload_resource_context_photo(
            context_key="opaque-context", file=upload, authorization="Bearer mobile", db=db
        ))
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 422
    else:
        raise AssertionError("spoofed JPEG bytes must be rejected")

    assert upload.closed is True
    assert called["ingest"] is False
    assert db.commits == 0


def test_c6_non_image_mime_is_rejected_before_media_write(monkeypatch):
    db = _DB()
    upload = _Upload(payload=b"%PDF-1.7", content_type="application/pdf")
    _valid_mobile_context(monkeypatch)
    called = {"ingest": False}

    def fake_ingest(*_args, **_kwargs):
        called["ingest"] = True

    monkeypatch.setattr(clinical_asset_ingestion, "ingest_clinical_asset_bytes", fake_ingest)

    try:
        asyncio.run(bridge.upload_resource_context_photo(
            context_key="opaque-context", file=upload, authorization="Bearer mobile", db=db
        ))
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 422
    else:
        raise AssertionError("non-image MIME must be rejected")

    assert called["ingest"] is False
    assert db.commits == 0


def test_c6_oversized_photo_is_rejected_before_media_write(monkeypatch):
    db = _DB()
    upload = _Upload(payload=b"x" * (bridge._CLINICAL_PHOTO_MAX_BYTES + 1), content_type="image/jpeg")
    _valid_mobile_context(monkeypatch)
    called = {"ingest": False}

    def fake_ingest(*_args, **_kwargs):
        called["ingest"] = True

    monkeypatch.setattr(clinical_asset_ingestion, "ingest_clinical_asset_bytes", fake_ingest)

    try:
        asyncio.run(bridge.upload_resource_context_photo(
            context_key="opaque-context", file=upload, authorization="Bearer mobile", db=db
        ))
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 413
    else:
        raise AssertionError("oversized smartphone photo must be rejected")

    assert upload.closed is True
    assert called["ingest"] is False
    assert db.commits == 0
