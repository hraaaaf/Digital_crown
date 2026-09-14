"""Versioned, fail-closed NGAP reference primitives for dental insurance submissions.

The production reference deliberately remains locked while the authoritative source
binary/hash is unavailable. A database mapping can resolve EXACT only when the primary
source is SHA-256 locked and the mapping itself was explicitly validated by a
practitioner. No label/fuzzy matching exists here.
"""

from __future__ import annotations

import hashlib
import unicodedata
from dataclasses import dataclass, field, replace
from datetime import date, datetime
from enum import Enum
from typing import Mapping, Optional

import fitz
from sqlalchemy.orm import Session

from backend import models
from backend.schemas.insurance_submission import InsuranceMappingStatus


class NgapCodeKind(str, Enum):
    NGAP = "NGAP"
    INTERNAL = "INTERNAL"
    OTHER = "OTHER"


class NgapReferenceStatus(str, Enum):
    PRIMARY_HASH_PENDING = "PRIMARY_HASH_PENDING"
    VERIFIED_PRIMARY = "VERIFIED_PRIMARY"
    OUTDATED = "OUTDATED"


@dataclass(frozen=True)
class NgapEntry:
    code: str
    coefficient: float
    official_label: str
    mapping_rule_id: str
    requires_prior_approval: bool = False
    requires_radiograph: bool = False


@dataclass(frozen=True)
class NgapRelease:
    version: str
    authority: str
    source_url: str
    status: NgapReferenceStatus
    source_hash: Optional[str] = None
    publication_reference: Optional[str] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    entries: Mapping[str, NgapEntry] = field(default_factory=dict)

    def is_locked_for_automatic_mapping(self, on_date: Optional[date] = None) -> bool:
        if self.status != NgapReferenceStatus.VERIFIED_PRIMARY:
            return False
        if not self.source_hash or len(self.source_hash) != 64:
            return False
        effective_date = on_date or date.today()
        if self.valid_from and effective_date < self.valid_from:
            return False
        if self.valid_to and effective_date > self.valid_to:
            return False
        return True


@dataclass(frozen=True)
class NgapResolution:
    status: InsuranceMappingStatus
    code: Optional[str] = None
    coefficient: Optional[float] = None
    official_label: Optional[str] = None
    mapping_rule_id: Optional[str] = None
    release_version: Optional[str] = None
    release_hash: Optional[str] = None
    requires_prior_approval: bool = False
    requires_radiograph: bool = False


def _normalized_pdf_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_text = "".join(char for char in normalized if not unicodedata.combining(char))
    return " ".join(ascii_text.lower().split())


def lock_ngap_primary_pdf(
    *,
    release: NgapRelease,
    pdf_bytes: bytes,
    source_url: Optional[str] = None,
) -> NgapRelease:
    """Verify legal identity markers then SHA-256 lock one primary NGAP PDF.

    Hashing arbitrary PDF bytes is insufficient. The binary must be readable and contain
    both the arrêté identifier and the NGAP title before the release can become
    VERIFIED_PRIMARY. This does not populate or validate regulatory mappings.
    """
    if release.status != NgapReferenceStatus.PRIMARY_HASH_PENDING:
        raise ValueError("NGAP release is not awaiting a primary binary lock")
    if not pdf_bytes or not pdf_bytes.startswith(b"%PDF"):
        raise ValueError("NGAP primary source is not a PDF binary")

    try:
        document = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = "\n".join(page.get_text("text") for page in document)
        page_count = int(document.page_count)
        document.close()
    except Exception as exc:
        raise ValueError("NGAP primary PDF binary is unreadable") from exc

    if page_count <= 0:
        raise ValueError("NGAP primary PDF has no pages")

    normalized = _normalized_pdf_text(text)
    required_markers = (
        "177-06",
        "nomenclature generale des actes professionnels",
    )
    missing = [marker for marker in required_markers if marker not in normalized]
    if missing:
        raise ValueError("NGAP primary PDF identity markers are missing")

    effective_source_url = str(source_url or release.source_url or "").strip()
    if not effective_source_url:
        raise ValueError("NGAP primary source provenance is required")

    return replace(
        release,
        source_url=effective_source_url,
        status=NgapReferenceStatus.VERIFIED_PRIMARY,
        source_hash=hashlib.sha256(pdf_bytes).hexdigest(),
    )


def certify_catalog_act_ngap_mapping(
    db: Session,
    *,
    mapping_id: int,
    locked_release: NgapRelease,
    practitioner_id: int,
    validated_at: Optional[datetime] = None,
):
    """Promote one pending mapping only against the same locked primary release.

    This is the explicit métier-validation step. It never commits; the caller owns the
    transaction and may still roll back the certification atomically.
    """
    from backend.models_ngap_reference import NgapCatalogMapping

    validation_time = validated_at or datetime.utcnow()
    if not locked_release.is_locked_for_automatic_mapping(on_date=validation_time.date()):
        raise ValueError("NGAP primary release is not locked/current")

    mapping = db.query(NgapCatalogMapping).filter(NgapCatalogMapping.id == int(mapping_id)).first()
    if mapping is None:
        raise ValueError("NGAP mapping not found")
    if mapping.reference_version != locked_release.version:
        raise ValueError("NGAP mapping/reference version mismatch")

    practitioner = db.query(models.User).filter(
        models.User.id == int(practitioner_id),
        models.User.is_active.is_(True),
    ).first()
    if practitioner is None:
        raise ValueError("Active practitioner validator not found")

    mapping.source_authority = locked_release.authority
    mapping.source_url = locked_release.source_url
    mapping.source_hash = locked_release.source_hash
    mapping.verification_status = NgapReferenceStatus.VERIFIED_PRIMARY.value
    mapping.valid_from = locked_release.valid_from
    mapping.valid_to = locked_release.valid_to
    mapping.validated_by_practitioner_id = practitioner.id
    mapping.validated_at = validation_time
    db.flush()
    return mapping


def resolve_ngap_code(
    *,
    catalog_code: Optional[str],
    code_kind: NgapCodeKind,
    release: NgapRelease,
    on_date: Optional[date] = None,
) -> NgapResolution:
    """Resolve an explicit code against one locked in-memory reference release.

    This helper is used only with explicitly constructed/versioned release data. The
    production DB path is ``resolve_catalog_act_ngap`` because legacy CatalogAct.code
    can contain internal values.
    """
    if code_kind != NgapCodeKind.NGAP or not str(catalog_code or "").strip():
        return NgapResolution(status=InsuranceMappingStatus.NO_MATCH)

    if not release.is_locked_for_automatic_mapping(on_date=on_date):
        return NgapResolution(
            status=InsuranceMappingStatus.OUTDATED,
            release_version=release.version,
            release_hash=release.source_hash,
        )

    normalized = str(catalog_code).strip().upper()
    entry = release.entries.get(normalized)
    if entry is None:
        return NgapResolution(
            status=InsuranceMappingStatus.NO_MATCH,
            release_version=release.version,
            release_hash=release.source_hash,
        )

    return NgapResolution(
        status=InsuranceMappingStatus.EXACT,
        code=entry.code,
        coefficient=entry.coefficient,
        official_label=entry.official_label,
        mapping_rule_id=entry.mapping_rule_id,
        release_version=release.version,
        release_hash=release.source_hash,
        requires_prior_approval=entry.requires_prior_approval,
        requires_radiograph=entry.requires_radiograph,
    )


def resolve_catalog_act_ngap(
    db: Session,
    *,
    catalog_act_id: int,
    reference_version: str,
    on_date: Optional[date] = None,
) -> NgapResolution:
    """Resolve one CatalogAct through an explicit versioned regulatory mapping row.

    ``CatalogAct.code`` is never interpreted. EXACT additionally requires source lock
    and explicit practitioner validation of the mapping row.
    """
    from backend.models_ngap_reference import NgapCatalogMapping

    catalog_act = db.query(models.CatalogAct).filter(
        models.CatalogAct.id == int(catalog_act_id),
        models.CatalogAct.is_active.is_(True),
    ).first()
    if catalog_act is None:
        return NgapResolution(status=InsuranceMappingStatus.NO_MATCH)

    mapping = db.query(NgapCatalogMapping).filter(
        NgapCatalogMapping.catalog_act_id == catalog_act.id,
        NgapCatalogMapping.reference_version == str(reference_version),
    ).first()
    if mapping is None:
        return NgapResolution(status=InsuranceMappingStatus.NO_MATCH)

    if mapping.code_kind != NgapCodeKind.NGAP.value:
        return NgapResolution(status=InsuranceMappingStatus.NO_MATCH)

    effective_date = on_date or date.today()
    source_hash = str(mapping.source_hash or "")
    locked = (
        mapping.verification_status == NgapReferenceStatus.VERIFIED_PRIMARY.value
        and len(source_hash) == 64
        and mapping.validated_by_practitioner_id is not None
        and mapping.validated_at is not None
        and (mapping.valid_from is None or effective_date >= mapping.valid_from)
        and (mapping.valid_to is None or effective_date <= mapping.valid_to)
    )
    if not locked:
        return NgapResolution(
            status=InsuranceMappingStatus.OUTDATED,
            release_version=mapping.reference_version,
            release_hash=mapping.source_hash,
        )

    if not mapping.ngap_code or mapping.coefficient is None or not mapping.mapping_rule_id:
        return NgapResolution(
            status=InsuranceMappingStatus.OUTDATED,
            release_version=mapping.reference_version,
            release_hash=mapping.source_hash,
        )

    return NgapResolution(
        status=InsuranceMappingStatus.EXACT,
        code=mapping.ngap_code,
        coefficient=float(mapping.coefficient),
        official_label=mapping.official_label,
        mapping_rule_id=mapping.mapping_rule_id,
        release_version=mapping.reference_version,
        release_hash=mapping.source_hash,
        requires_prior_approval=bool(mapping.requires_prior_approval),
        requires_radiograph=bool(mapping.requires_radiograph),
    )


# Primary authority is the Moroccan Ministry of Health regulation database.
# The same arrêté is indexed by the SGG Bulletin Officiel n°5414, data.gov.ma and
# CNOPS. Exact primary bytes still need reproducible retrieval; no hash is fabricated.
DENTAL_NGAP_PRIMARY_PENDING = NgapRelease(
    version="arrete-177-06",
    authority="Ministere de la Sante et de la Protection Sociale",
    source_url=(
        "https://www.sante.gov.ma/Reglementation/Nomenclature/Documents/"
        "Arr%C3%AAt%C3%A9%20n%C2%B0%20177-06.pdf"
    ),
    publication_reference="B.O. n° 5414 du 20/04/2006",
    status=NgapReferenceStatus.PRIMARY_HASH_PENDING,
    source_hash=None,
    entries={},
)

DENTAL_NGAP_CORROBORATING_URLS = (
    "https://www.sgg.gov.ma/BO/bo_fr/2006/bo_5414_fr.pdf",
    "https://data.gov.ma/data/fr/dataset/b8425cb6-828f-4fa9-9f02-cdd372d18f65/resource/"
    "f66d23ac-012f-4439-ac99-4beb129ce640/download/ngap-cnops-2014.pdf",
    "https://cnops.org.ma/sites/default/files/2022-10/Nomeclature_0.pdf",
)
