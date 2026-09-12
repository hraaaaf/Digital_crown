"""P3 multi-practitioner document provenance facades.

Generation keeps the authenticated user as the technical actor while binding a
validated clinical author. Signature provenance is a separate explicit action: only
the authenticated practitioner who authored the exact active archive bytes may record it.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend import database, models, schemas
from backend.routers.auth import get_current_user, require_permission
from backend.schemas.document_provenance_p3 import DocumentArchiveOutP3
from backend.services.audit_service import audit_service
from backend.services.document_provenance_context import (
    reset_document_author_practitioner_id,
    set_document_author_practitioner_id,
)
from backend.services.document_signature_p3 import (
    sign_document,
    verification_state_for_document,
)
from backend.services.practitioner_policy import resolve_document_author
from backend.utils.access_control import assert_patient_access

from . import documents as legacy_documents
from . import patients as legacy_patients
from . import verification as legacy_verification


logger = logging.getLogger(__name__)
documents_router = APIRouter()
patients_router = APIRouter()
verification_router = APIRouter()


class DocumentRequestP3(schemas.DocumentRequest):
    author_practitioner_id: Optional[int] = None


class CephaloPDFRequestP3(schemas.CephaloPDFRequest):
    author_practitioner_id: Optional[int] = None


@documents_router.post(
    "/generate",
    summary="Générer un document PDF avec provenance praticien",
)
async def generate_document_with_provenance(
    req: DocumentRequestP3,
    archive: bool = False,
    preview: bool = False,
    force: bool = False,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    legacy_documents.require_document_permission(req.type, current_user)
    assert_patient_access(req.patient_id, current_user, db)
    author = resolve_document_author(db, current_user, req.author_practitioner_id)

    token = set_document_author_practitioner_id(author.id)
    try:
        legacy_req = schemas.DocumentRequest.model_validate(
            req.model_dump(exclude={"author_practitioner_id"})
        )
        return await legacy_documents.generate_document(
            req=legacy_req,
            archive=archive,
            preview=preview,
            force=force,
            db=db,
            current_user=current_user,
        )
    finally:
        reset_document_author_practitioner_id(token)


@documents_router.post(
    "/{document_id}/sign",
    response_model=DocumentArchiveOutP3,
    summary="Enregistrer la signature praticien P3",
)
def sign_document_with_provenance(
    document_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    doc = db.query(models.DocumentArchive).filter(
        models.DocumentArchive.id == document_id
    ).first()
    if doc is None:
        raise HTTPException(status_code=404, detail="Document introuvable")

    assert_patient_access(doc.patient_id, current_user, db)
    doc_type = getattr(doc.document_type, "value", str(doc.document_type))
    legacy_documents.require_document_permission(doc_type, current_user)

    signed = sign_document(db, doc, current_user)
    audit_service.log(
        db=db,
        user_id=current_user.id,
        employer_id=current_user.get_employer_id(),
        action="DOCUMENT_SIGNED",
        resource_type="Document",
        resource_id=str(doc.id),
        severity="INFO",
        details=f"SHA256: {doc.file_hash}",
    )
    return signed


@patients_router.get("/{patient_id}/documents")
def get_patient_documents_with_provenance(
    patient_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients")),
):
    """Keep canonical listing and enrich canonical rows with P3 proof only."""
    results = legacy_patients.get_patient_documents(
        patient_id=patient_id,
        db=db,
        current_user=current_user,
    )

    canonical_ids = [
        int(item["id"])
        for item in results
        if str(item.get("id", "")).isdigit()
    ]
    if not canonical_ids:
        return results

    docs = db.query(models.DocumentArchive).filter(
        models.DocumentArchive.id.in_(canonical_ids),
        models.DocumentArchive.patient_id == patient_id,
    ).all()
    docs_by_id = {doc.id: doc for doc in docs}

    practitioner_ids = {
        practitioner_id
        for doc in docs
        for practitioner_id in (
            doc.author_practitioner_id,
            doc.signed_by_practitioner_id,
        )
        if practitioner_id is not None
    }
    practitioners = (
        db.query(models.User).filter(models.User.id.in_(practitioner_ids)).all()
        if practitioner_ids else []
    )
    names = {
        user.id: (user.nom_complet or user.email or f"Praticien {user.id}")
        for user in practitioners
    }

    for item in results:
        raw_id = str(item.get("id", ""))
        if not raw_id.isdigit():
            continue
        doc = docs_by_id.get(int(raw_id))
        if doc is None:
            continue
        item.update({
            "author_practitioner_id": doc.author_practitioner_id,
            "author_practitioner_name": names.get(doc.author_practitioner_id),
            "signed_by_practitioner_id": doc.signed_by_practitioner_id,
            "signed_by_practitioner_name": names.get(doc.signed_by_practitioner_id),
            "signed_at": doc.signed_at.isoformat() if doc.signed_at else None,
        })

    return results


@patients_router.post("/{patient_id}/pdf")
def generate_cephalo_pdf_with_provenance(
    patient_id: int,
    req: CephaloPDFRequestP3,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("cephalo")),
):
    assert_patient_access(patient_id, current_user, db)
    author = resolve_document_author(db, current_user, req.author_practitioner_id)

    token = set_document_author_practitioner_id(author.id)
    try:
        legacy_req = schemas.CephaloPDFRequest.model_validate(
            req.model_dump(exclude={"author_practitioner_id"})
        )
        return legacy_patients.generate_cephalo_pdf(
            patient_id=patient_id,
            req=legacy_req,
            db=db,
            current_user=current_user,
        )
    finally:
        reset_document_author_practitioner_id(token)


@verification_router.get("/verify/{doc_id}", response_class=HTMLResponse)
def verify_document_with_p3_signature(
    doc_id: str,
    db: Session = Depends(database.get_db),
):
    """Public verification never claims proof that P3 did not record."""
    config = db.query(models.CabinetConfig).first()
    primary_color = config.primary_color if config else "#003380"
    cabinet_name = config.nom_cabinet if config else "Cabinet Digital Crown"

    try:
        doc = None
        if doc_id.isdigit():
            doc = db.query(models.DocumentArchive).filter(
                models.DocumentArchive.id == int(doc_id)
            ).first()
        if doc is None:
            doc = db.query(models.DocumentArchive).filter(
                or_(
                    models.DocumentArchive.filename.contains(doc_id),
                    models.DocumentArchive.original_filename.contains(doc_id),
                )
            ).first()

        if doc is not None:
            patient = db.query(models.Patient).filter(
                models.Patient.id == doc.patient_id
            ).first()
            patient_name = (
                f"{patient.nom.upper()} {patient.prenom[0]}."
                if patient else "PATIENT INCONNU"
            )
            state = verification_state_for_document(doc)
            title = (
                "Document Médical • Signature enregistrée"
                if state.is_signed
                else "Document Médical • Intégrité vérifiée"
                if state.is_valid
                else "Document Médical Invalide"
            )
            return HTMLResponse(content=legacy_verification.get_verification_html(
                title=title,
                subtitle=cabinet_name,
                doc_type=doc.document_type.value,
                patient_name=patient_name,
                doc_date=doc.created_at.strftime("%d/%m/%Y à %H:%M"),
                primary_color=primary_color,
                status_text=state.status_text,
                status_color=state.status_color,
                is_valid=state.is_valid,
                warning_msg=state.warning_msg,
            ))
    except Exception as exc:
        logger.error("P3 document verification failed: %s", exc)

    return HTMLResponse(content=legacy_verification.get_verification_html(
        title="Document Introuvable",
        subtitle="Erreur de Vérification",
        doc_type="INCONNU",
        patient_name="NON DISPONIBLE",
        doc_date="NON SPÉCIFIÉE",
        primary_color="#ef4444",
        status_text="Non vérifié / Invalide",
        status_color="#ef4444",
        is_valid=False,
        warning_msg="Ce document n'a pas été vérifié par Digital Crown.",
    ))


# Preserve historical file discovery while replacing only the canonical patient list facade.
legacy_patients.router.routes = [
    route
    for route in legacy_patients.router.routes
    if not (
        getattr(route, "path", None) == "/{patient_id}/documents"
        and "GET" in (getattr(route, "methods", set()) or set())
    )
]

# Keep special two-segment RADIO/BILAN verification untouched.
legacy_verification.router.routes = [
    route
    for route in legacy_verification.router.routes
    if not (
        getattr(route, "path", None) == "/verify/{doc_id}"
        and "GET" in (getattr(route, "methods", set()) or set())
    )
]
legacy_verification.router.include_router(verification_router)
