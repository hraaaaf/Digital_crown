"""DC-DOS-05 isolated candidate: fail-closed study/media identity + content proof.

A persisted link proves an explicit association and encrypted original bytes.
It does NOT prove the cephalometric landmarks were computed from this file,
calibration correctness, clinical accuracy or authorization for clinical use.
No mutable source_ref, filename or longitudinal timepoint can create a link.
"""
from __future__ import annotations

import hashlib
import re

from sqlalchemy.orm import Session

from backend import models
from backend.models_cephalo_study_media import CephaloStudyMediaBinding
from backend.models_media_core import ClinicalAsset
from backend.services.cephalo_runtime_chain import project_runtime_chain_read_path
from backend.services.cephalo_typed_read import CephaloTypedReadError
from backend.services.clinical_asset_storage import (
    ClinicalAssetStorageError, read_clinical_asset_bytes,
)

_ALLOWED_ROLES = {"RADIO_SOURCE": "RADIOGRAPH", "PHOTO_CONTEXT": "PHOTO"}
_SHA_RE = re.compile(r"^[0-9a-f]{64}$")


class StudyMediaBindingError(ValueError):
    def __init__(self, detail: str, status_code: int = 409):
        super().__init__(detail)
        self.status_code = status_code


def _study(db: Session, *, employer_id: int, patient_id: int, study_id: int):
    study = (
        db.query(models.CephaloAnalysis)
        .join(models.Patient, models.CephaloAnalysis.patient_id == models.Patient.id)
        .filter(
            models.CephaloAnalysis.id == study_id,
            models.CephaloAnalysis.patient_id == patient_id,
            models.Patient.employer_id == employer_id,
        )
        .first()
    )
    if study is None:
        raise StudyMediaBindingError("Study not found in current tenant/patient", 404)
    return study


def _study_revision(study) -> int:
    if not isinstance(study.angles_data, dict):
        raise StudyMediaBindingError("Study has no verified scientific revision")
    try:
        projection = project_runtime_chain_read_path(
            study.angles_data, patient_id=study.patient_id
        )
    except (CephaloTypedReadError, ValueError, KeyError, TypeError) as exc:
        raise StudyMediaBindingError("Study scientific evidence is invalid") from exc
    evidence = projection.get("scientific_read_path")
    if not isinstance(evidence, dict) or (
        evidence.get("authority") != "EVIDENCE_GRAPH_V1"
        or evidence.get("active_chain") != "VERIFIED"
        or type(evidence.get("revision")) is not int
        or evidence["revision"] < 1
    ):
        raise StudyMediaBindingError("Study does not have an authoritative revision")
    return evidence["revision"]


def _original(db, *, employer_id, patient_id, asset_id, role):
    if role not in _ALLOWED_ROLES:
        raise StudyMediaBindingError("Unsupported binding role", 422)
    asset = db.query(ClinicalAsset).filter(
        ClinicalAsset.id == asset_id,
        ClinicalAsset.employer_id == employer_id,
        ClinicalAsset.patient_id == patient_id,
    ).first()
    if asset is None:
        raise StudyMediaBindingError("Media not found in current tenant/patient", 404)
    if asset.asset_type != _ALLOWED_ROLES[role] or asset.source_kind not in {
        "UPLOAD", "IMPORT", "DEVICE_CAPTURE",
    }:
        raise StudyMediaBindingError("Role requires matching original media type")
    if not isinstance(asset.sha256, str) or not _SHA_RE.fullmatch(asset.sha256):
        raise StudyMediaBindingError("Media digest missing or invalid")
    try:
        plaintext = read_clinical_asset_bytes(
            db, employer_id=employer_id, patient_id=patient_id, asset_id=asset_id
        )
    except (ClinicalAssetStorageError, OSError) as exc:
        raise StudyMediaBindingError("Media ciphertext/integrity verification failed") from exc
    if hashlib.sha256(plaintext).hexdigest() != asset.sha256:
        raise StudyMediaBindingError("Media SHA-256 disagrees with verified bytes")
    return asset


def bind_study_original_media(
    db: Session, *, employer_id: int, patient_id: int, study_id: int,
    asset_id: int, role: str, expected_revision: int, created_by: int,
) -> tuple[CephaloStudyMediaBinding, bool]:
    """Write once; repeated exact request is safe; changed role/asset/revision is 409.

    Caller owns commit/rollback. The unique SQL constraint handles concurrent
    writers and the route maps IntegrityError to 409.
    """
    study = _study(db, employer_id=employer_id, patient_id=patient_id, study_id=study_id)
    revision = _study_revision(study)
    if type(expected_revision) is not int or expected_revision != revision:
        raise StudyMediaBindingError("Stale/missing study scientific revision")
    user = db.get(models.User, created_by)
    if user is None or user.get_employer_id() != employer_id:
        raise StudyMediaBindingError("Operator belongs to another cabinet", 403)
    original = _original(
        db, employer_id=employer_id, patient_id=patient_id,
        asset_id=asset_id, role=role,
    )
    existing = db.query(CephaloStudyMediaBinding).filter(
        CephaloStudyMediaBinding.study_id == study_id,
        CephaloStudyMediaBinding.role == role,
    ).first()
    if existing is not None:
        if (existing.asset_id, existing.asset_sha256, existing.revision) == (
            original.id, original.sha256, revision,
        ):
            return existing, False
        raise StudyMediaBindingError("Study/media role is already bound (write-once)")
    binding = CephaloStudyMediaBinding(
        employer_id=employer_id,
        patient_id=patient_id,
        study_id=study_id,
        asset_id=original.id,
        role=role,
        asset_sha256=original.sha256,
        revision=revision,
        created_by=created_by,
    )
    db.add(binding)
    db.flush()
    return binding, True


def read_verified_study_media(
    db: Session, *, employer_id: int, patient_id: int, study_id: int,
) -> dict:
    """All links revalidate study revision, scope, original SHA and AES-GCM bytes."""
    study = _study(db, employer_id=employer_id, patient_id=patient_id, study_id=study_id)
    current_revision = _study_revision(study)
    rows = db.query(CephaloStudyMediaBinding).filter(
        CephaloStudyMediaBinding.employer_id == employer_id,
        CephaloStudyMediaBinding.patient_id == patient_id,
        CephaloStudyMediaBinding.study_id == study_id,
    ).order_by(CephaloStudyMediaBinding.role).all()
    if not rows:
        raise StudyMediaBindingError("No authoritative study-media association", 409)
    for row in rows:
        if row.revision != current_revision:
            raise StudyMediaBindingError("Binding refers to stale study revision")
        original = _original(
            db, employer_id=employer_id, patient_id=patient_id,
            asset_id=row.asset_id, role=row.role,
        )
        if original.sha256 != row.asset_sha256:
            raise StudyMediaBindingError("Binding digest no longer matches original")
    return {
        "study_id": study_id,
        "patient_id": patient_id,
        "revision": current_revision,
        "binding_state": "EXPLICIT_VERIFIED_ORIGINALS",
        "clinical_release": False,
        "cephalo_computation_from_source_proven": False,
        "items": [{
            "role": row.role, "asset_id": row.asset_id,
            "sha256": row.asset_sha256, "revision": row.revision,
        } for row in rows],
    }
