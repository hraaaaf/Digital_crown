from __future__ import annotations

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


@router.get("/{patient_id}/assets")
def list_patient_assets(
    patient_id: int,
    limit: int = Query(200, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Return the authenticated patient's primary clinical-media timeline.

    DERIVED assets are intentionally hidden from the timeline and only referenced as
    verified stored thumbnails. Storage locators and hashes never leave the backend.
    """
    _require_patient_permission(current_user)
    assert_patient_access(patient_id, current_user, db)
    employer_id = int(current_user.get_employer_id())

    try:
        assets = list_clinical_assets_for_patient(
            db,
            employer_id=employer_id,
            patient_id=patient_id,
            include_derived=False,
            limit=limit,
            offset=offset,
        )
    except ClinicalAssetInvariantError as exc:
        raise HTTPException(status_code=404, detail="Patient media timeline unavailable") from exc

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
    """Validate and ingest a supported clinical media payload.

    Tenant identity is derived from the authenticated user and is never accepted from the
    multipart form. C3 returns metadata identifiers only; storage keys and content hashes are
    intentionally kept internal.
    """
    _require_patient_permission(current_user)
    assert_patient_access(patient_id, current_user, db)
    employer_id = int(current_user.get_employer_id())

    try:
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
