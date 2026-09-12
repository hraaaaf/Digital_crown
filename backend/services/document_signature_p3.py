"""Fail-closed P3 document signing and public verification state.

A signature is meaningful only when it is bound to the exact archived bytes.
The authenticated practitioner signs only their own authored canonical document.
Legacy documents without author provenance remain unsigned until explicitly
regenerated under P3 provenance.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend import models
from backend.core.media_paths import get_media_root
from backend.services.practitioner_policy import is_assignable_practitioner


BASE_DIR = Path(__file__).resolve().parent.parent
MEDIA_DIR = get_media_root()


@dataclass(frozen=True)
class DocumentVerificationState:
    is_valid: bool
    is_signed: bool
    status_text: str
    status_color: str
    warning_msg: str = ""


def resolve_document_storage_path(doc: models.DocumentArchive) -> Path:
    """Resolve canonical archive storage without mutating the document."""
    file_path = str(doc.file_path or "")
    if file_path.startswith("static/archives/") or file_path.startswith("static/documents/"):
        return MEDIA_DIR / file_path.replace("static/", "", 1)
    return BASE_DIR / file_path


def verify_document_integrity(doc: models.DocumentArchive) -> tuple[bool, str]:
    """Verify that the physical bytes still match the persisted SHA-256 and size."""
    path = resolve_document_storage_path(doc)
    if not path.is_file():
        return False, "Fichier physique introuvable"

    content = path.read_bytes()
    calculated_hash = hashlib.sha256(content).hexdigest()
    if calculated_hash != doc.file_hash:
        return False, "Empreinte SHA-256 du fichier non conforme"

    if doc.file_size is not None and len(content) != int(doc.file_size):
        return False, "Taille physique du fichier non conforme"

    return True, "OK"


def verification_state_for_document(doc: models.DocumentArchive) -> DocumentVerificationState:
    """Return truthful public verification state for one canonical archive."""
    if doc.status != models.DocumentStatus.ACTIF:
        return DocumentVerificationState(
            is_valid=False,
            is_signed=False,
            status_text="Document non actif / invalide",
            status_color="#ef4444",
            warning_msg="Ce document n'est plus dans un état actif vérifiable.",
        )

    integrity_ok, integrity_reason = verify_document_integrity(doc)
    if not integrity_ok:
        return DocumentVerificationState(
            is_valid=False,
            is_signed=False,
            status_text="Intégrité non vérifiée",
            status_color="#ef4444",
            warning_msg=integrity_reason,
        )

    has_signer = doc.signed_by_practitioner_id is not None
    has_timestamp = doc.signed_at is not None
    if has_signer != has_timestamp:
        return DocumentVerificationState(
            is_valid=False,
            is_signed=False,
            status_text="Signature incohérente",
            status_color="#ef4444",
            warning_msg="La provenance de signature enregistrée est incomplète.",
        )

    if has_signer and has_timestamp:
        return DocumentVerificationState(
            is_valid=True,
            is_signed=True,
            status_text="Authentique & Signé",
            status_color="#10b981",
        )

    return DocumentVerificationState(
        is_valid=True,
        is_signed=False,
        status_text="Authentique • Non signé",
        status_color="#f59e0b",
        warning_msg="Aucune signature praticien n'est enregistrée pour ce document.",
    )


def sign_document(
    db: Session,
    doc: models.DocumentArchive,
    current_user: models.User,
) -> models.DocumentArchive:
    """Bind the current authenticated author to the exact current archive bytes."""
    employer_id = current_user.get_employer_id()
    if not is_assignable_practitioner(current_user, employer_id):
        raise HTTPException(status_code=403, detail="Seul un praticien actif et approuvé peut signer")

    if doc.status != models.DocumentStatus.ACTIF:
        raise HTTPException(status_code=409, detail="Seul un document actif peut être signé")

    if doc.author_practitioner_id is None:
        raise HTTPException(
            status_code=409,
            detail="Document sans auteur P3 : régénération requise avant signature",
        )

    if int(doc.author_practitioner_id) != int(current_user.id):
        raise HTTPException(
            status_code=403,
            detail="Le praticien connecté ne peut signer que ses propres documents",
        )

    if doc.signed_by_practitioner_id is not None or doc.signed_at is not None:
        if (
            doc.signed_by_practitioner_id == current_user.id
            and doc.signed_at is not None
        ):
            # Idempotence: a second click must not rewrite the proof timestamp.
            return doc
        raise HTTPException(status_code=409, detail="Signature existante incohérente")

    integrity_ok, integrity_reason = verify_document_integrity(doc)
    if not integrity_ok:
        raise HTTPException(
            status_code=409,
            detail=f"Signature refusée : {integrity_reason}",
        )

    doc.signed_by_practitioner_id = current_user.id
    doc.signed_at = datetime.utcnow()
    db.commit()
    db.refresh(doc)
    return doc
