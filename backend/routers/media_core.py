from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from backend import database, models
from backend.routers.auth import get_current_user, has_permission
from backend.services.clinical_asset_ingestion import (
    ClinicalAssetIngestionError,
    MAX_IMPORT_BYTES,
    ingest_clinical_asset_bytes,
)
from backend.services.clinical_asset_service import ClinicalAssetInvariantError
from backend.services.clinical_asset_storage import ClinicalAssetStorageError
from backend.utils.access_control import assert_patient_access


router = APIRouter(tags=["Media Core"])


def _asset_response(result) -> dict:
    asset = result.asset
    thumbnail = result.thumbnail_asset
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
        "thumbnail_asset_id": thumbnail.id if thumbnail else None,
    }


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
    if not has_permission(current_user, "patients"):
        raise HTTPException(status_code=403, detail="Accès refusé. Permission patients requise.")

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
