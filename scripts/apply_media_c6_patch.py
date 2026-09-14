from pathlib import Path

TARGET = Path("backend/routers/mobile_resource_bridge.py")
TEST = Path("backend/tests/test_media_c6_controlled_smartphone_capture.py")
WORKFLOW = Path(".github/workflows/media-c6-patch-helper.yml")
SELF = Path("scripts/apply_media_c6_patch.py")

text = TARGET.read_text(encoding="utf-8")
start = text.index("@router.post('/resource-context-photo'")
end = text.index("@router.post('/resource-context-document-scan'", start)
old = text[start:end]
if "archive_service.archive_document" not in old:
    raise SystemExit("C6 patch guard failed: legacy DocumentArchive photo path not found")

new = '''@router.post('/resource-context-photo', summary='Capturer une photo clinique dans le Media Core patient')
async def upload_resource_context_photo(
    context_key: str = Form(...),
    file: UploadFile = File(...),
    authorization: str = Header(...),
    db: Session = Depends(database.get_db),
):
    from backend.services.clinical_asset_ingestion import (
        ClinicalAssetIngestionError,
        ingest_clinical_asset_bytes,
    )
    from backend.services.clinical_asset_service import ClinicalAssetInvariantError
    from backend.services.clinical_asset_storage import ClinicalAssetStorageError

    mobile_user, context = _validated_mobile_context(db, authorization, context_key)
    if str(context['resource_type']).lower() != 'patient':
        raise HTTPException(status_code=422, detail="La photo clinique exige un contexte Patient.")

    patient = _patient_resource(db, mobile_user, int(context['resource_id']))
    claimed_type = str(file.content_type or '').strip().lower()
    if claimed_type and not claimed_type.startswith('image/'):
        raise HTTPException(status_code=422, detail="Le fichier sélectionné n'est pas une image.")

    try:
        raw = await file.read(_CLINICAL_PHOTO_MAX_BYTES + 1)
    finally:
        await file.close()
    normalized = _normalize_clinical_photo(raw)

    captured_at = datetime.utcnow()
    filename = f"device-capture-{captured_at.strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(4)}.jpg"
    try:
        result = ingest_clinical_asset_bytes(
            db,
            employer_id=int(mobile_user.get_employer_id()),
            patient_id=int(patient.id),
            asset_type='PHOTO',
            source_kind='DEVICE_CAPTURE',
            content=normalized,
            original_filename=filename,
            claimed_mime_type='image/jpeg',
            source_ref='MOBILE_RESOURCE_BRIDGE',
            captured_at=captured_at,
            created_by=int(mobile_user.id),
            provenance_json={
                'ingestion_channel': 'MOBILE_RESOURCE_BRIDGE',
                'capture_kind': 'SMARTPHONE_CAMERA',
                'bridge_resource_type': 'patient',
                'device_id': str(context.get('device_id') or ''),
            },
        )
        db.commit()
        db.refresh(result.asset)
        if result.thumbnail_asset is not None:
            db.refresh(result.thumbnail_asset)
    except HTTPException:
        db.rollback()
        raise
    except (ClinicalAssetIngestionError, ClinicalAssetInvariantError) as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except (ClinicalAssetStorageError, OSError) as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail="Clinical media storage unavailable") from exc

    _documents.audit_service.log(
        db=db,
        user_id=mobile_user.id,
        employer_id=mobile_user.get_employer_id(),
        action='CLINICAL_PHOTO_CAPTURED',
        resource_type='CLINICAL_ASSET',
        resource_id=str(result.asset.id),
        severity='INFO',
        details=(
            f"Photo clinique mobile enregistrée asset_id={result.asset.id} "
            f"source_kind=DEVICE_CAPTURE patient_id={patient.id}"
        ),
    )
    thumbnail_id = result.thumbnail_asset.id if result.thumbnail_asset is not None else None
    created_at = result.asset.created_at.isoformat() if result.asset.created_at else None
    return {
        'success': True,
        'asset': {
            'id': result.asset.id,
            'asset_type': result.asset.asset_type,
            'source_kind': result.asset.source_kind,
            'mime_type': result.asset.mime_type,
            'thumbnail_asset_id': thumbnail_id,
            'created_at': created_at,
        },
        # Backward-compatible mobile contract: the UI only checks this marker.
        # The identifier now belongs to ClinicalAsset; no DocumentArchive row is created.
        'document': {
            'id': result.asset.id,
            'document_type': models.DocumentType.PHOTO_CLINIQUE.value,
            'title': 'Photo clinique',
            'created_at': created_at,
        },
    }


'''
TARGET.write_text(text[:start] + new + text[end:], encoding="utf-8")

TEST.write_text('''import asyncio\nfrom pathlib import Path\nfrom types import SimpleNamespace\n\nfrom backend.routers import mobile_resource_bridge as bridge\nfrom backend.services import clinical_asset_ingestion\n\n\nclass _Upload:\n    content_type = "image/jpeg"\n    filename = "capture.jpg"\n\n    def __init__(self, payload=b"raw-camera-bytes"):\n        self.payload = payload\n        self.closed = False\n\n    async def read(self, _limit):\n        return self.payload\n\n    async def close(self):\n        self.closed = True\n\n\nclass _DB:\n    def __init__(self):\n        self.commits = 0\n        self.rollbacks = 0\n        self.refreshed = []\n\n    def commit(self):\n        self.commits += 1\n\n    def rollback(self):\n        self.rollbacks += 1\n\n    def refresh(self, obj):\n        self.refreshed.append(obj)\n\n\ndef test_c6_mobile_photo_uses_media_core_without_legacy_archive(monkeypatch):\n    source = Path(bridge.__file__).read_text(encoding="utf-8")\n    block = source[source.index("@router.post('/resource-context-photo'"):source.index("@router.post('/resource-context-document-scan'")]\n    assert "ingest_clinical_asset_bytes" in block\n    assert "source_kind='DEVICE_CAPTURE'" in block\n    assert "archive_service.archive_document" not in block\n    assert "MOBILE_RESOURCE_BRIDGE" in block\n\n    db = _DB()\n    upload = _Upload()\n    user = SimpleNamespace(id=7, get_employer_id=lambda: 41)\n    context = {"resource_type": "patient", "resource_id": 19, "device_id": "device-abc"}\n    patient = SimpleNamespace(id=19)\n    asset = SimpleNamespace(\n        id=501, asset_type="PHOTO", source_kind="DEVICE_CAPTURE", mime_type="image/jpeg", created_at=None\n    )\n    thumb = SimpleNamespace(id=502)\n    captured = {}\n\n    monkeypatch.setattr(bridge, "_validated_mobile_context", lambda *_: (user, context))\n    monkeypatch.setattr(bridge, "_patient_resource", lambda *_: patient)\n    monkeypatch.setattr(bridge, "_normalize_clinical_photo", lambda raw: b"normalized-jpeg")\n\n    def fake_ingest(_db, **kwargs):\n        captured.update(kwargs)\n        return SimpleNamespace(asset=asset, thumbnail_asset=thumb)\n\n    monkeypatch.setattr(clinical_asset_ingestion, "ingest_clinical_asset_bytes", fake_ingest)\n    monkeypatch.setattr(bridge._documents.audit_service, "log", lambda **_: None)\n\n    response = asyncio.run(bridge.upload_resource_context_photo(\n        context_key="opaque-context", file=upload, authorization="Bearer mobile", db=db\n    ))\n\n    assert upload.closed is True\n    assert db.commits == 1\n    assert db.rollbacks == 0\n    assert captured["employer_id"] == 41\n    assert captured["patient_id"] == 19\n    assert captured["asset_type"] == "PHOTO"\n    assert captured["source_kind"] == "DEVICE_CAPTURE"\n    assert captured["claimed_mime_type"] == "image/jpeg"\n    assert captured["created_by"] == 7\n    assert captured["source_ref"] == "MOBILE_RESOURCE_BRIDGE"\n    assert captured["provenance_json"]["device_id"] == "device-abc"\n    assert response["asset"]["id"] == 501\n    assert response["asset"]["thumbnail_asset_id"] == 502\n    assert response["document"]["document_type"] == "PHOTO_CLINIQUE"\n\n\ndef test_c6_invalid_context_is_rejected_before_media_write(monkeypatch):\n    upload = _Upload()\n    db = _DB()\n\n    def reject(*_):\n        from fastapi import HTTPException\n        raise HTTPException(status_code=403, detail="Contexte mobile incompatible avec cette session.")\n\n    monkeypatch.setattr(bridge, "_validated_mobile_context", reject)\n    called = {"ingest": False}\n\n    def fake_ingest(*_args, **_kwargs):\n        called["ingest"] = True\n\n    monkeypatch.setattr(clinical_asset_ingestion, "ingest_clinical_asset_bytes", fake_ingest)\n\n    try:\n        asyncio.run(bridge.upload_resource_context_photo(\n            context_key="bad-context", file=upload, authorization="Bearer bad", db=db\n        ))\n    except Exception as exc:\n        assert getattr(exc, "status_code", None) == 403\n    else:\n        raise AssertionError("invalid context must be rejected")\n\n    assert called["ingest"] is False\n    assert db.commits == 0\n''', encoding="utf-8")

# The helper must not survive the atomic patch commit.
SELF.unlink(missing_ok=True)
WORKFLOW.unlink(missing_ok=True)
