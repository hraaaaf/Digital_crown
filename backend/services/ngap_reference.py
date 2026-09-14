"""Versioned, fail-closed NGAP reference primitives for dental insurance submissions.

The production reference deliberately remains locked while the authoritative source
binary/hash is unavailable. A release can resolve EXACT only when it is explicitly
VERIFIED_PRIMARY, carries a SHA-256 source hash, and contains an exact code entry.
No label/fuzzy matching exists here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Mapping, Optional

from backend.schemas.insurance_submission import InsuranceMappingStatus


class NgapCodeKind(str, Enum):
    NGAP = "NGAP"
    INTERNAL = "INTERNAL"


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


def resolve_ngap_code(
    *,
    catalog_code: Optional[str],
    code_kind: NgapCodeKind,
    release: NgapRelease,
    on_date: Optional[date] = None,
) -> NgapResolution:
    """Resolve an explicit catalog code against one locked reference release.

    INTERNAL codes and missing codes are never interpreted as NGAP. An unlocked,
    pending or expired release returns OUTDATED before inspecting entries.
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
    )


# Real authority metadata is known, but the official binary could not yet be
# retrieved reproducibly for SHA-256 locking. Therefore entries remain empty and
# automatic mapping is intentionally impossible on this release object.
DENTAL_NGAP_PRIMARY_PENDING = NgapRelease(
    version="arrete-177-06",
    authority="Ministere de la Sante / CNOPS",
    source_url="https://cnops.org.ma/sites/default/files/2022-10/Nomeclature_0.pdf",
    status=NgapReferenceStatus.PRIMARY_HASH_PENDING,
    source_hash=None,
    entries={},
)
