"""Versioned insurer template registry and reproducible binary locking.

Layout/render code must consume a locked template snapshot. The registry itself contains
no PDF coordinates and no fabricated fields. A template becomes renderable only after
its exact PDF bytes have been inspected and SHA-256 locked.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

import fitz

from backend.schemas.insurance_submission import (
    InsuranceOrganization,
    InsuranceTemplateSnapshot,
    InsuranceTemplateTrust,
)


@dataclass(frozen=True)
class InsuranceTemplateDefinition:
    organization: InsuranceOrganization
    version: str
    label: str
    trust: InsuranceTemplateTrust
    expected_page_count: int | None = None


@dataclass(frozen=True)
class LockedInsuranceTemplate:
    definition: InsuranceTemplateDefinition
    source_url: str
    sha256: str
    page_count: int

    def as_submission_snapshot(self) -> InsuranceTemplateSnapshot:
        return InsuranceTemplateSnapshot(
            template_version=self.definition.version,
            template_hash=self.sha256,
            source_url=self.source_url,
            trust=self.definition.trust,
        )


def lock_template_pdf(
    *,
    definition: InsuranceTemplateDefinition,
    pdf_bytes: bytes,
    source_url: str,
) -> LockedInsuranceTemplate:
    """Inspect exact PDF bytes and return an immutable lock record.

    Page-count mismatch is blocking because a visually similar but different form must
    never inherit the identity/hash contract of a validated template version.
    """
    if not pdf_bytes or not pdf_bytes.startswith(b"%PDF"):
        raise ValueError("Template source is not a PDF binary")
    if not str(source_url or "").strip():
        raise ValueError("Template source URL/provenance is required")

    try:
        document = fitz.open(stream=pdf_bytes, filetype="pdf")
        page_count = int(document.page_count)
        document.close()
    except Exception as exc:
        raise ValueError("Template PDF binary is unreadable") from exc

    if page_count <= 0:
        raise ValueError("Template PDF has no pages")
    if (
        definition.expected_page_count is not None
        and page_count != definition.expected_page_count
    ):
        raise ValueError(
            f"Template page count mismatch: expected {definition.expected_page_count}, got {page_count}"
        )

    return LockedInsuranceTemplate(
        definition=definition,
        source_url=str(source_url).strip(),
        sha256=hashlib.sha256(pdf_bytes).hexdigest(),
        page_count=page_count,
    )


CNSS_610_1_04 = InsuranceTemplateDefinition(
    organization=InsuranceOrganization.CNSS,
    version="CNSS-610-1-04",
    label="Feuille de soins dentaires CNSS 610-1-04",
    trust=InsuranceTemplateTrust.CABINET_VALIDATED_BINARY,
    expected_page_count=2,
)

# Exact two-page CNOPS dental form validated by the cabinet on 2026-09-16.
# Binary identity is enforced by the source store/profile layer; this registry entry
# only promotes the validated form version/trust and does not claim official provenance.
CNOPS_DENTAL_CABINET_2026_09_16 = InsuranceTemplateDefinition(
    organization=InsuranceOrganization.CNOPS,
    version="CNOPS-DENTAL-CABINET-2026-09-16",
    label="Feuille de soins dentaires CNOPS — binaire valide cabinet",
    trust=InsuranceTemplateTrust.CABINET_VALIDATED_BINARY,
    expected_page_count=2,
)

# Backward-compatible alias for code/scripts that previously referenced the pending
# placeholder. It now resolves to the exact cabinet-validated template definition.
CNOPS_DENTAL_PENDING = CNOPS_DENTAL_CABINET_2026_09_16

# Cabinet-accepted printable reconstruction. This definition is deliberately distinct
# from CABINET_VALIDATED_BINARY/OFFICIAL_PRIMARY because the exact original FAR binary
# was not recovered. Runtime rendering is still hash-bound to the frozen derived bytes.
FAR_2021_1 = InsuranceTemplateDefinition(
    organization=InsuranceOrganization.FAR,
    version="FAR-2021-1-DERIVED-CABINET-2026-09-17",
    label="Feuille de Mutuelle FAR 2021-1 — référence dérivée validée cabinet",
    trust=InsuranceTemplateTrust.CABINET_VALIDATED_DERIVED_REFERENCE,
    expected_page_count=2,
)
