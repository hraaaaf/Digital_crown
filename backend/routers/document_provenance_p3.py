"""P3 multi-practitioner document provenance facades.

These handlers replace only the stable generation endpoints. They delegate all legacy
business logic to the existing handlers while binding a validated clinical author in a
request-scoped ContextVar. The authenticated user remains the technical actor.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend import database, models, schemas
from backend.routers.auth import get_current_user, require_permission
from backend.services.document_provenance_context import (
    reset_document_author_practitioner_id,
    set_document_author_practitioner_id,
)
from backend.services.practitioner_policy import resolve_document_author
from backend.utils.access_control import assert_patient_access

from . import documents as legacy_documents
from . import patients as legacy_patients


documents_router = APIRouter()
patients_router = APIRouter()


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
    # Preserve legacy authorization ordering before practitioner lookup.
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


@patients_router.post("/{patient_id}/pdf")
def generate_cephalo_pdf_with_provenance(
    patient_id: int,
    req: CephaloPDFRequestP3,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("cephalo")),
):
    # Prevent cross-tenant practitioner probing before author resolution.
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
