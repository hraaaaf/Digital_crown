"""Server-authorized, exact-byte clinician approval for descriptive cephalometric A4 V1.

No advanced/qualified e-signature. No patient data leaves the local backend;
there is no second archive engine, new SQL column, or persistent preview copy.
A time-bound HMAC claim identifies the exact candidate PDF the authenticated
dentist reviewed. All scientific identity is re-read under the existing SQL
study writer lock before the trusted archive service may persist those bytes.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any

from fastapi import HTTPException

from backend import models
from backend.security import SECRET_KEY
from backend.services.practitioner_policy import is_assignable_practitioner

VERSION = "CEPH_A4_DESCRIPTIVE_APPROVAL_V1"
TOKEN_SECONDS = 600
MAX_PDF_BYTES = 7 * 1024 * 1024
_DOMAIN = b"DIGITAL_CROWN_CEPH_A4_DESCRIPTIVE_APPROVAL_V1\x00"


def require_dentist(user: models.User) -> None:
    """A generic admin or secretary must never approve patient cephalometry."""
    if (
        getattr(user, "role", None) != models.UserRole.DENTISTE
        or not is_assignable_practitioner(user, user.get_employer_id())
    ):
        raise HTTPException(status_code=403, detail="Validation réservée au chirurgien-dentiste habilité")


def scientific_fingerprint(study: models.CephaloAnalysis) -> str:
    """Include actual scientific data, calibration and image; not only revision."""
    stable = {
        "analysis_id": study.id,
        "patient_id": study.patient_id,
        "angles_data": study.angles_data,
        "landmarks_data": study.landmarks_data,
        "image_original_path": study.image_original_path,
        "mm_per_pixel": study.mm_per_pixel,
        "is_calibrated": study.is_calibrated,
    }
    body = json.dumps(stable, sort_keys=True, ensure_ascii=False, default=str, separators=(",", ":"))
    return hashlib.sha256(body.encode("utf-8")).hexdigest()




def require_real_cabinet_letterhead(*, cabinet: models.CabinetConfig, user: models.User) -> None:
    """No 'Dr. Nom Prénom', 'Votre adresse', or 'Contact' in official A4.

    The existing base template falls back to example text when the cabinet
    setup is incomplete. The descriptive approval candidate must refuse,
    not silently turn such a template into an official patient archive.
    """
    if not cabinet or not str(cabinet.nom_cabinet or "").strip():
        raise HTTPException(status_code=422, detail="Cachet professionnel du cabinet à configurer")
    address = str(
        getattr(cabinet, "footer_address", None)
        or getattr(user, "adresse_complete", None) or ""
    ).strip()
    phone = str(
        getattr(cabinet, "footer_phones", None)
        or getattr(user, "telephone_mobile", None) or ""
    ).strip()
    contacts = getattr(cabinet, "contacts_json", None)
    has_contact = bool(phone)
    if isinstance(contacts, dict):
        has_contact = has_contact or any(
            isinstance(row, dict)
            and row.get("enabled") is True
            and bool(str(row.get("value") or "").strip())
            for row in contacts.values()
        )
    from backend.services.base_template import BaseTemplate

    # Use the SAME stored Document Studio configuration and its existing
    # letterhead visibility rules; this validation does not inject A4-specific
    # header/footer content. A real uploaded letterhead can contain both.
    config = {column.key: getattr(cabinet, column.key)
              for column in models.CabinetConfig.__table__.columns}
    base = BaseTemplate()
    actual_letterhead = bool(
        base.has_active_letterhead(config)
        and base._resolve_brand_asset(config.get("letterhead_path"))
    )
    draws_header = not actual_letterhead or not bool(config.get("hide_header", True))
    draws_footer = not actual_letterhead or not bool(config.get("hide_footer", True))
    # An unarchived preview cannot render a truthful archive-verification or
    # payment QR. Never silently drop that element from the user's template:
    # require choosing a static QR type, or disable QR in Document Studio.
    if (
        cabinet.qr_code_enabled is True
        and cabinet.qr_code_type in (models.QRCodeType.VALIDATION, models.QRCodeType.PAYMENT)
    ):
        raise HTTPException(
            status_code=422,
            detail="QR de validation/paiement non disponible pour le bilan A4 non encore archivé ; "
                   "choisissez un QR statique ou désactivez-le dans Documents",
        )
    if draws_header:
        fr_lines = [str(v).strip() for v in (cabinet.header_lines_fr or []) if str(v).strip()]
        ar_lines = [str(v).strip() for v in (cabinet.header_lines_ar or []) if str(v).strip()]
        placeholders = ("dr. nom prénom", "dr. nom prenom", "د. الإسم الكامل", "d. nom")
        if (
            not fr_lines or not ar_lines
            or any(any(marker in line.casefold() for marker in placeholders)
                   for line in fr_lines + ar_lines)
        ):
            raise HTTPException(
                status_code=422,
                detail="En-tête du modèle Documents incomplet : configurez les lignes FR/AR "
                       "dans les paramètres du cabinet avant l'archivage A4",
            )
    if draws_footer and (not address or not has_contact):
        raise HTTPException(
            status_code=422,
            detail="Papier à en-tête du bilan A4 incomplet : adresse et contact du cabinet requis",
        )


def rendered_identity_fingerprint(*, patient: models.Patient, user: models.User, cabinet: models.CabinetConfig) -> str:
    """Bind the PDF's patient demographics and visible practitioner/cabinet text.

    This is separate from the scientific study revision: a patient rename,
    date-of-birth correction or cabinet-stamp change must invalidate a preview
    even when the cephalometric graph's revision remains unchanged.
    """
    if (
        patient is None or cabinet is None or user is None
        or type(patient.id) is not int or patient.id <= 0
        or type(user.id) is not int or user.id <= 0
        or cabinet.owner_id != user.get_employer_id()
        or not str(user.nom_complet or "").strip()
        or not str(cabinet.nom_cabinet or "").strip()
    ):
        raise HTTPException(status_code=409, detail="Identité ou cachet du bilan non vérifiable")
    # Use *every persisted Document Studio setting*, not a curated subset:
    # typography, geometry, margins, QR, theme and legal footer fields all
    # influence the official A4 at render time. Changing any of them after
    # preview invalidates the practitioner's exact-document approval.
    studio_config = {
        column.key: getattr(cabinet, column.key)
        for column in models.CabinetConfig.__table__.columns
    }
    identity = {
        "document_studio_config": studio_config,
        "patient_id": patient.id,
        "nom": patient.nom,
        "prenom": patient.prenom,
        "date_naissance": patient.date_naissance.isoformat() if patient.date_naissance else None,
        "sexe": patient.sexe,
        "practitioner_id": user.id,
        "practitioner_name": user.nom_complet,
        "cabinet_owner": cabinet.owner_id,
        "cabinet_stamp": cabinet.nom_cabinet,
        "cabinet_nom_praticien": cabinet.nom_praticien,
        "header_lines_fr": cabinet.header_lines_fr,
        "header_lines_ar": cabinet.header_lines_ar,
        "footer_address": cabinet.footer_address,
        "footer_phones": cabinet.footer_phones,
        "contacts_json": getattr(cabinet, "contacts_json", None),
        "user_address": getattr(user, "adresse_complete", None),
        "user_phone": getattr(user, "telephone_mobile", None),
        "user_phone_fixe": getattr(user, "telephone_fixe", None),
        "user_specialties": getattr(user, "specialites", None),
        "user_legal_ids": getattr(user, "identifiants_legaux", None),
        "letterhead_path": cabinet.letterhead_path,
        "use_letterhead": cabinet.use_letterhead,
        "logo_path": cabinet.logo_path,
        "selected_template": cabinet.selected_template,
        "selected_theme": cabinet.selected_theme,
    }
    text = json.dumps(
        identity, sort_keys=True, ensure_ascii=False, default=str, separators=(",", ":"),
    )
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def require_descriptive_science(study, *, patient_id: int, revision: int) -> None:
    """Descriptive measurements only; NEVER waive the typed evidence gate."""
    from backend.services.cephalo_pdf_projection import build_cephalo_pdf_projection
    from backend.services.cephalo_consistency_validator import cephalo_consistency_validator
    projection = build_cephalo_pdf_projection(
        patient_id=patient_id, analysis_id=study.id, angles_data=study.angles_data
    )
    if (
        projection.get("active_runtime_chain_verified") is not True
        or projection.get("analysis_revision") != revision
    ):
        raise HTTPException(status_code=409, detail="Preuve scientifique active non vérifiable")
    if (
        not study.is_calibrated
        or not isinstance(study.mm_per_pixel, (int, float))
        or isinstance(study.mm_per_pixel, bool)
        or not (0 < study.mm_per_pixel < float("inf"))
    ):
        raise HTTPException(status_code=409, detail="Calibration persistée non admissible")
    landmarks = study.landmarks_data
    if not isinstance(landmarks, list) or len(landmarks) < 38:
        raise HTTPException(status_code=409, detail="Repères de l'étude incomplets")
    ids = [point.get("id") for point in landmarks if isinstance(point, dict)]
    if len(ids) != len(landmarks) or any(not isinstance(item, str) or not item for item in ids) or len(set(ids)) != len(ids):
        raise HTTPException(status_code=409, detail="Repères incomplets ou dupliqués")
    result = cephalo_consistency_validator.validate(study.angles_data or {})
    if not result.is_valid:
        raise HTTPException(status_code=422, detail="Mesures incohérentes : validation A4 refusée")


def _secret() -> bytes:
    if not isinstance(SECRET_KEY, str) or SECRET_KEY == "SET_A_REAL_SECRET_KEY_IN_ENV" or len(SECRET_KEY) < 32:
        raise HTTPException(status_code=503, detail="Clé serveur d'approbation non configurée")
    return hashlib.sha256(_DOMAIN + SECRET_KEY.encode("utf-8")).digest()


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _decode(raw: str) -> bytes:
    if not isinstance(raw, str) or len(raw) > 4096:
        raise ValueError("Encodage invalide")
    return base64.urlsafe_b64decode(raw + "=" * (-len(raw) % 4))


def make_approval_token(
    *, user: models.User, patient_id: int, analysis_id: int, revision: int,
    source_sha256: str, rendered_identity_sha256: str, pdf_sha256: str, pdf_length: int, now: int | None = None,
) -> str:
    require_dentist(user)
    issued = int(time.time()) if now is None else int(now)
    claims = {
        "v": VERSION,
        "patient_id": patient_id,
        "analysis_id": analysis_id,
        "revision": revision,
        "user_id": user.id,
        "cabinet_id": user.get_employer_id(),
        "source_sha256": source_sha256,
        "rendered_identity_sha256": rendered_identity_sha256,
        "pdf_sha256": pdf_sha256,
        "pdf_length": pdf_length,
        "iat": issued,
    }
    body = json.dumps(claims, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    payload = _b64(body)
    mac = hmac.new(_secret(), _DOMAIN + payload.encode("ascii"), hashlib.sha256).digest()
    return payload + "." + _b64(mac)


def verify_approval_token(
    token: str, *, user: models.User, patient_id: int, analysis_id: int,
    revision: int, source_sha256: str, rendered_identity_sha256: str, pdf: bytes, now: int | None = None,
) -> dict[str, Any]:
    require_dentist(user)
    try:
        payload, mac = token.split(".")
        expected = hmac.new(_secret(), _DOMAIN + payload.encode("ascii"), hashlib.sha256).digest()
        if not hmac.compare_digest(_decode(mac), expected):
            raise ValueError("Signature du reçu invalide")
        claims = json.loads(_decode(payload))
    except (AttributeError, ValueError, TypeError, KeyError, UnicodeDecodeError) as exc:
        raise HTTPException(status_code=409, detail="Preuve de relecture du bilan invalide") from exc
    issued = claims.get("iat")
    clock = int(time.time()) if now is None else int(now)
    if (
        claims.get("v") != VERSION
        or type(issued) is not int or issued > clock + 30
        or issued < clock - TOKEN_SECONDS
        or claims.get("user_id") != user.id
        or claims.get("cabinet_id") != user.get_employer_id()
        or claims.get("patient_id") != patient_id
        or claims.get("analysis_id") != analysis_id
        or claims.get("revision") != revision
        or claims.get("source_sha256") != source_sha256
        or not isinstance(rendered_identity_sha256, str)
        or len(rendered_identity_sha256) != 64
        or claims.get("rendered_identity_sha256") != rendered_identity_sha256
    ):
        raise HTTPException(status_code=409, detail="Preuve périmée, non autorisée ou étude modifiée")
    if (
        not isinstance(pdf, bytes)
        or not pdf.startswith(b"%PDF")
        or len(pdf) == 0
        or len(pdf) > MAX_PDF_BYTES
        or len(pdf) != claims.get("pdf_length")
        or hashlib.sha256(pdf).hexdigest() != claims.get("pdf_sha256")
    ):
        raise HTTPException(status_code=409, detail="Le PDF ne correspond pas à la version relue")
    return claims


def decode_pdf(pdf_base64: str) -> bytes:
    if not isinstance(pdf_base64, str) or len(pdf_base64) > MAX_PDF_BYTES * 4 // 3 + 16:
        raise HTTPException(status_code=413, detail="Bilan A4 trop volumineux")
    try:
        pdf = base64.b64decode(pdf_base64, validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise HTTPException(status_code=422, detail="Encodage PDF invalide") from exc
    if not pdf or len(pdf) > MAX_PDF_BYTES:
        raise HTTPException(status_code=413, detail="Bilan A4 trop volumineux")
    return pdf


def archive_payload_digest(*, user_id: int, pdf_sha256: str, source_sha256: str) -> str:
    payload = {
        "kind": VERSION,
        "practitioner_id": user_id,
        "pdf_sha256": pdf_sha256,
        "scientific_source_sha256": source_sha256,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
