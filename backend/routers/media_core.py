from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile
from sqlalchemy.orm import Session

from backend import database, models
from backend.models_media_core import ClinicalAsset
from backend.routers.auth import get_current_user, has_permission
from backend.services.clinical_asset_ingestion import (
    ClinicalAssetIngestionError,
    MAX_IMPORT_BYTES,
    ingest_clinical_asset_bytes,
)
from backend.services.clinical_asset_service import (
    ClinicalAssetInvariantError,
    get_clinical_asset_for_patient,
    list_clinical_assets_for_patient,
)
from backend.services.clinical_asset_storage import (
    ClinicalAssetStorageError,
    read_clinical_asset_bytes,
)
from backend.services.ortho_media_record import (
    ORTHO_MEDIA_SCHEMA_VERSION,
    ORTHO_PHOTO_SOURCE_PREFIX,
    OrthoMediaRecordError,
    build_ortho_media_record,
    ortho_photo_source_ref,
    validate_ortho_photo_slot,
    validate_ortho_timepoint,
)
from backend.utils.access_control import assert_patient_access


router = APIRouter(tags=["Media Core"])
_SAFE_INLINE_MIME = {"image/jpeg", "image/png", "image/webp", "application/pdf"}


def _require_patient_permission(current_user: models.User) -> None:
    if not has_permission(current_user, "patients"):
        raise HTTPException(status_code=403, detail="Accès refusé. Permission patients requise.")


def _asset_metadata(asset: ClinicalAsset, *, thumbnail_asset_id: Optional[int] = None) -> dict:
    return {
        "id": asset.id,
        "patient_id": asset.patient_id,
        "asset_type": asset.asset_type,
        "source_kind": asset.source_kind,
        "mime_type": asset.mime_type,
        "byte_size": asset.byte_size,
        "timepoint": asset.timepoint,
        "captured_at": asset.captured_at,
        "created_at": asset.created_at,
        "thumbnail_asset_id": thumbnail_asset_id,
    }


def _asset_response(result) -> dict:
    return _asset_metadata(
        result.asset,
        thumbnail_asset_id=result.thumbnail_asset.id if result.thumbnail_asset else None,
    )


def _thumbnail_map(db: Session, *, employer_id: int, patient_id: int, parent_ids: list[int]) -> dict[int, int]:
    if not parent_ids:
        return {}
    derived = (
        db.query(ClinicalAsset)
        .filter(
            ClinicalAsset.employer_id == employer_id,
            ClinicalAsset.patient_id == patient_id,
            ClinicalAsset.source_kind == "DERIVED",
            ClinicalAsset.parent_asset_id.in_(parent_ids),
            ClinicalAsset.mime_type == "image/jpeg",
            ClinicalAsset.storage_key.isnot(None),
            ClinicalAsset.storage_format.isnot(None),
            ClinicalAsset.stored_at.isnot(None),
            ClinicalAsset.sha256.isnot(None),
            ClinicalAsset.byte_size.isnot(None),
        )
        .order_by(ClinicalAsset.id.desc())
        .all()
    )
    result: dict[int, int] = {}
    for asset in derived:
        if asset.parent_asset_id is not None and asset.parent_asset_id not in result:
            result[int(asset.parent_asset_id)] = int(asset.id)
    return result


@router.get("/{patient_id}/ortho-media-record")
def get_ortho_media_record(
    patient_id: int,
    timepoint: str = Query("T0", max_length=16),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    _require_patient_permission(current_user)
    assert_patient_access(patient_id, current_user, db)
    employer_id = int(current_user.get_employer_id())
    try:
        return build_ortho_media_record(
            db, employer_id=employer_id, patient_id=patient_id, timepoint=timepoint
        )
    except OrthoMediaRecordError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/{patient_id}/ortho-media-record/photos/{slot_id}", status_code=201)
async def import_ortho_photo_slot(
    patient_id: int,
    slot_id: str,
    file: UploadFile = File(...),
    timepoint: str = Form("T0"),
    acquired_at: datetime = Form(...),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    _require_patient_permission(current_user)
    assert_patient_access(patient_id, current_user, db)
    employer_id = int(current_user.get_employer_id())
    try:
        slot = validate_ortho_photo_slot(slot_id)
        tp = validate_ortho_timepoint(timepoint)
        content = await file.read(MAX_IMPORT_BYTES + 1)
        if len(content) > MAX_IMPORT_BYTES:
            raise HTTPException(status_code=413, detail="Clinical media exceeds the import size limit")
        result = ingest_clinical_asset_bytes(
            db,
            employer_id=employer_id,
            patient_id=patient_id,
            asset_type="PHOTO",
            source_kind="UPLOAD",
            content=content,
            original_filename=file.filename,
            claimed_mime_type=file.content_type,
            source_ref=ortho_photo_source_ref(slot),
            timepoint=tp,
            captured_at=acquired_at,
            created_by=current_user.id,
            provenance_json={
                "ingestion_channel": "ORTHO_STUDIO",
                "schema_version": ORTHO_MEDIA_SCHEMA_VERSION,
                "slot_id": slot,
                "source_type": "CLINICIAN_UPLOAD",
                "acquired_at": acquired_at.isoformat(),
                "operator_or_device": f"user:{current_user.id}",
                "patient_record_id": str(patient_id),
                "timepoint_id": tp,
            },
        )
        db.commit()
        db.refresh(result.asset)
        return {
            "schema_version": ORTHO_MEDIA_SCHEMA_VERSION,
            "slot_id": slot,
            "asset": _asset_response(result),
        }
    except HTTPException:
        db.rollback()
        raise
    except (OrthoMediaRecordError, ClinicalAssetIngestionError, ClinicalAssetInvariantError) as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except (ClinicalAssetStorageError, OSError) as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail="Clinical media storage unavailable") from exc
    finally:
        await file.close()


@router.get("/{patient_id}/assets")
def list_patient_assets(
    patient_id: int,
    limit: int = Query(200, ge=1, le=200),
    offset: int = Query(0, ge=0),
    q: Optional[str] = Query(None, max_length=120),
    asset_type: Optional[str] = Query(None, max_length=32),
    source_kind: Optional[str] = Query(None, max_length=32),
    timepoint: Optional[str] = Query(None, max_length=32),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Return a bounded, searchable patient clinical-media timeline.

    Filtering is executed inside the tenant + patient query. DERIVED assets stay hidden and
    thumbnails are batch-loaded for the returned page. One sentinel row is fetched to expose
    has_more without an unbounded COUNT query.
    """
    _require_patient_permission(current_user)
    assert_patient_access(patient_id, current_user, db)
    employer_id = int(current_user.get_employer_id())

    try:
        rows = list_clinical_assets_for_patient(
            db,
            employer_id=employer_id,
            patient_id=patient_id,
            include_derived=False,
            limit=limit + 1,
            offset=offset,
            search=q,
            asset_type=asset_type,
            source_kind=source_kind,
            timepoint=timepoint,
        )
    except ClinicalAssetInvariantError as exc:
        raise HTTPException(status_code=404, detail="Patient media timeline unavailable") from exc

    has_more = len(rows) > limit
    assets = rows[:limit]
    thumbnails = _thumbnail_map(
        db,
        employer_id=employer_id,
        patient_id=patient_id,
        parent_ids=[int(asset.id) for asset in assets],
    )
    return {
        "items": [
            _asset_metadata(asset, thumbnail_asset_id=thumbnails.get(int(asset.id)))
            for asset in assets
        ],
        "limit": limit,
        "offset": offset,
        "has_more": has_more,
    }


@router.get("/{patient_id}/assets/{asset_id}/content")
def read_patient_asset_content(
    patient_id: int,
    asset_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Return verified plaintext bytes only through authenticated patient scope."""
    _require_patient_permission(current_user)
    assert_patient_access(patient_id, current_user, db)
    employer_id = int(current_user.get_employer_id())

    asset = get_clinical_asset_for_patient(
        db,
        employer_id=employer_id,
        patient_id=patient_id,
        asset_id=asset_id,
    )
    if asset is None:
        raise HTTPException(status_code=404, detail="Clinical media asset not found")

    try:
        content = read_clinical_asset_bytes(
            db,
            employer_id=employer_id,
            patient_id=patient_id,
            asset_id=asset_id,
        )
    except ClinicalAssetStorageError as exc:
        raise HTTPException(status_code=503, detail="Clinical media storage unavailable") from exc

    media_type = asset.mime_type if asset.mime_type in _SAFE_INLINE_MIME else "application/octet-stream"
    disposition = "inline" if media_type in _SAFE_INLINE_MIME else "attachment"
    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Cache-Control": "private, no-store",
            "Pragma": "no-cache",
            "X-Content-Type-Options": "nosniff",
            "Content-Disposition": disposition,
        },
    )


@router.post("/{patient_id}/assets/import", status_code=201)
async def import_clinical_asset(
    patient_id: int,
    file: UploadFile = File(...),
    asset_type: str = Form(...),
    source_kind: str = Form("UPLOAD"),
    source_ref: Optional[str] = Form(None),
    timepoint: Optional[str] = Form(None),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Validate and ingest a supported clinical media payload."""
    _require_patient_permission(current_user)
    assert_patient_access(patient_id, current_user, db)
    employer_id = int(current_user.get_employer_id())

    try:
        if source_ref and source_ref.strip().upper().startswith(ORTHO_PHOTO_SOURCE_PREFIX):
            raise HTTPException(status_code=422, detail="Reserved orthodontic source_ref namespace")
        content = await file.read(MAX_IMPORT_BYTES + 1)
        if len(content) > MAX_IMPORT_BYTES:
            raise HTTPException(status_code=413, detail="Clinical media exceeds the import size limit")

        result = ingest_clinical_asset_bytes(
            db,
            employer_id=employer_id,
            patient_id=patient_id,
            asset_type=asset_type,
            source_kind=source_kind,
            content=content,
            original_filename=file.filename,
            claimed_mime_type=file.content_type,
            source_ref=source_ref,
            timepoint=timepoint,
            created_by=current_user.id,
            provenance_json={"ingestion_channel": "WEB_API"},
        )
        db.commit()
        db.refresh(result.asset)
        if result.thumbnail_asset is not None:
            db.refresh(result.thumbnail_asset)
        return _asset_response(result)
    except HTTPException:
        db.rollback()
        raise
    except (ClinicalAssetIngestionError, ClinicalAssetInvariantError) as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except (ClinicalAssetStorageError, OSError) as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail="Clinical media storage unavailable") from exc
    finally:
        await file.close()
