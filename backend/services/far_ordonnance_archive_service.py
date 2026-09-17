"""Archive a FAR prescription output derived from one archived Digital Crown ordonnance."""
from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from backend import models
from backend.core.media_paths import get_media_root
from backend.schemas import ConflictResolution
from backend.schemas.documents import OrdonnanceData
from backend.services.archive_service import get_archive_service
from backend.services.far_ordonnance_bridge import (
    build_far_ordonnance_payload,
    patient_requires_far_ordonnance,
)
from backend.services.insurance_far_2021_1_profile import FAR_2021_1_DERIVED_TEMPLATE_SHA256
from backend.services.insurance_far_prescription_renderer import (
    FAR_PRESCRIPTION_RENDERER_VERSION,
    render_far_prescription_pdf,
)
from backend.services.insurance_source_store import load_stored_insurance_source
from backend.services.insurance_template_registry import FAR_2021_1


def get_far_source_store_root() -> Path:
    return get_media_root() / "insurance_sources"


def archive_far_ordonnance_from_source(
    db: Session,
    *,
    patient: models.Patient,
    source_ordonnance_document: models.DocumentArchive,
    ordonnance: OrdonnanceData,
    uploaded_by_id: int,
    source_store_root: Path | None = None,
) -> models.DocumentArchive | None:
    """Render/archive FAR only for explicit FAR patients and an archived ordonnance.

    Returns None for non-FAR patients. No clinical field is inferred.
    """
    if not patient_requires_far_ordonnance(assurance=patient.assurance):
        return None
    if source_ordonnance_document.id is None:
        raise ValueError("FAR ordonnance requires a persisted source archive")
    if source_ordonnance_document.patient_id != patient.id:
        raise ValueError("FAR ordonnance source archive belongs to another patient")
    if source_ordonnance_document.document_type != models.DocumentType.ORDONNANCE:
        raise ValueError("FAR ordonnance source must be an archived ordonnance")

    payload = build_far_ordonnance_payload(
        patient_id=int(patient.id),
        source_ordonnance_document_id=int(source_ordonnance_document.id),
        ordonnance=ordonnance,
    )

    root = source_store_root or get_far_source_store_root()
    loaded = load_stored_insurance_source(
        root=root,
        namespace="template-far",
        version=FAR_2021_1.version,
        sha256=FAR_2021_1_DERIVED_TEMPLATE_SHA256,
    )
    manifest = loaded.manifest
    if manifest.get("kind") != "INSURANCE_TEMPLATE":
        raise ValueError("FAR stored source kind mismatch")
    if manifest.get("organization") != "FAR":
        raise ValueError("FAR stored source organization mismatch")
    if manifest.get("trust") != FAR_2021_1.trust.value:
        raise ValueError("FAR stored source trust mismatch")
    if not str(manifest.get("cabinet_validated_by") or "").strip():
        raise ValueError("FAR cabinet-validated source has no validator identity")

    patient_full_name = " ".join(
        value for value in (
            str(getattr(patient, "prenom", "") or "").strip(),
            str(getattr(patient, "nom", "") or "").strip(),
        ) if value
    )
    rendered = render_far_prescription_pdf(
        template_bytes=loaded.pdf_bytes,
        payload=payload,
        patient_full_name=patient_full_name,
    )

    archive_service = get_archive_service(db)
    filename = f"Ordonnance_FAR_{patient.id}_source_{source_ordonnance_document.id}.pdf"
    far_doc, _ = archive_service.archive_document(
        patient_id=int(patient.id),
        file_content=rendered,
        filename=filename,
        doc_type=models.DocumentType.AUTRE,
        uploaded_by_id=uploaded_by_id,
        title="Ordonnance FAR",
        tags=["FAR", "ORDONNANCE", "AUTO_DERIVED"],
        clinical_data={
            "kind": "FAR_ORDONNANCE_DERIVED",
            "source_ordonnance_document_id": int(source_ordonnance_document.id),
            "renderer_version": FAR_PRESCRIPTION_RENDERER_VERSION,
            "template_version": FAR_2021_1.version,
            "template_sha256": FAR_2021_1_DERIVED_TEMPLATE_SHA256,
        },
        on_conflict=ConflictResolution.CREATE_VERSION,
        commit=True,
    )
    return far_doc
