"""LOT05.7-A: untrusted evidence coherence gate, NOT a clinical importer.

Pure Python; no runtime imports, SQL, network, storage, filesystem, or API.
Claims are untrusted metadata; successful checks NEVER authorize a write.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
import re

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_CURRENT_HEAD = "neo000000031"  # Explicit fail-closed pin; update only with migration review.


@dataclass(frozen=True)
class UntrustedImportEvidence:
    """Only fingerprints, version labels, aggregate counts and claimed controls.

    Caller MUST NOT send patient names, credentials, source SQL, or DB paths.
    No field is a trusted authentication assertion or restore certificate.
    """

    tenant_id: int
    authenticated_owner_id: int
    asserted_tenant_owner_id: int
    staged_source_sha256: str
    inspector_source_sha256: str
    mapping_source_sha256: str
    dryrun_source_sha256: str
    mapping_profile_sha256: str
    dryrun_mapping_sha256: str
    mapping_target_revision: str
    dryrun_target_revision: str
    observed_target_revision: str
    critical_count: int
    unresolved_duplicate_count: int
    unmapped_required_count: int
    cross_tenant_link_count: int
    undocumented_media_count: int
    source_offline_copy_attested: bool
    source_provenance_claimed: bool
    mapping_owner_review_claimed: bool
    dryrun_zero_target_writes_claimed: bool
    restore_rehearsal_claimed: bool
    replay_rehearsal_claimed: bool
    tenant_isolation_rehearsal_claimed: bool


@dataclass(frozen=True, slots=True)
class EvidenceGateReport:
    """Planning evidence only. A caller cannot opt in to import through it."""

    status: str
    claims_coherent: bool
    blockers: tuple[str, ...]

    @property
    def import_permitted(self) -> Literal[False]:
        return False

    @property
    def full_schema_certified(self) -> Literal[False]:
        return False

    @property
    def real_restore_certified(self) -> Literal[False]:
        return False

    @property
    def human_authorization_verified(self) -> Literal[False]:
        return False

    def to_dict(self) -> dict[str, object]:
        # No tenant ID, source digest, file path or source values in output.
        return {
            "status": self.status,
            "claims_coherent": self.claims_coherent,
            "blockers": list(self.blockers),
            "import_permitted": False,
            "full_schema_certified": False,
            "real_restore_certified": False,
            "human_authorization_verified": False,
        }


# These gates cannot be satisfied by caller-supplied flags or synthetic tests.
_UNPROVEN = (
    "REAL_IMPORT_NOT_IMPLEMENTED",
    "AUTHENTICATED_RUNTIME_OWNER_GATE_NOT_CONNECTED",
    "REAL_SOURCE_PROVENANCE_NOT_VERIFIED",
    "REAL_BACKUP_RESTORE_NOT_CERTIFIED",
    "REAL_TARGET_AND_TENANT_NOT_CERTIFIED",
    "HUMAN_SIGNOFF_NOT_VERIFIED",
)


def check_untrusted_import_evidence(evidence: object) -> EvidenceGateReport:
    """Check *reported* coherence without interpreting it as verified proof.

    Use only as an offline, synthetic planning helper. Never connect this
    function to an import authorization path. Fail closed for unknown input.
    """
    if type(evidence) is not UntrustedImportEvidence:
        return EvidenceGateReport(
            status="CONSTRUCTION_REJECTED",
            claims_coherent=False,
            blockers=("INVALID_EVIDENCE_SHAPE",) + _UNPROVEN,
        )

    issues: list[str] = []
    if (type(evidence.tenant_id) is not int or evidence.tenant_id <= 0
            or type(evidence.authenticated_owner_id) is not int
            or evidence.authenticated_owner_id <= 0
            or type(evidence.asserted_tenant_owner_id) is not int
            or evidence.asserted_tenant_owner_id <= 0):
        issues.append("INVALID_TENANT_OR_OWNER_CLAIM")
    elif evidence.authenticated_owner_id != evidence.asserted_tenant_owner_id:
        issues.append("OWNER_SCOPE_CLAIM_MISMATCH")

    hashes = (
        evidence.staged_source_sha256,
        evidence.inspector_source_sha256,
        evidence.mapping_source_sha256,
        evidence.dryrun_source_sha256,
        evidence.mapping_profile_sha256,
        evidence.dryrun_mapping_sha256,
    )
    if any(type(h) is not str or _SHA256.fullmatch(h) is None for h in hashes):
        issues.append("INVALID_SHA256_CLAIM")
    elif len(set(hashes[:4])) != 1:
        issues.append("SOURCE_DIGEST_BINDING_MISMATCH")
    if (type(evidence.mapping_profile_sha256) is str
            and type(evidence.dryrun_mapping_sha256) is str
            and evidence.mapping_profile_sha256 != evidence.dryrun_mapping_sha256):
        issues.append("MAPPING_DIGEST_BINDING_MISMATCH")

    revisions = (
        evidence.mapping_target_revision,
        evidence.dryrun_target_revision,
        evidence.observed_target_revision,
    )
    if any(type(r) is not str or r != _CURRENT_HEAD for r in revisions):
        issues.append("TARGET_REVISION_UNVERIFIED_OR_STALE")

    counters = (
        evidence.critical_count,
        evidence.unresolved_duplicate_count,
        evidence.unmapped_required_count,
        evidence.cross_tenant_link_count,
        evidence.undocumented_media_count,
    )
    if any(type(c) is not int or c < 0 for c in counters):
        issues.append("INVALID_ANOMALY_COUNT")
    elif any(c != 0 for c in counters):
        issues.append("UNRESOLVED_IMPORT_ANOMALIES")

    required_claims = (
        evidence.source_offline_copy_attested,
        evidence.source_provenance_claimed,
        evidence.mapping_owner_review_claimed,
        evidence.dryrun_zero_target_writes_claimed,
        evidence.restore_rehearsal_claimed,
        evidence.replay_rehearsal_claimed,
        evidence.tenant_isolation_rehearsal_claimed,
    )
    if any(flag is not True for flag in required_claims):
        issues.append("MISSING_OR_INVALID_CONTROL_CLAIM")

    return EvidenceGateReport(
        status="CONSTRUCTION_CLAIMS_COHERENT" if not issues else "CONSTRUCTION_REJECTED",
        claims_coherent=not issues,
        blockers=tuple(issues) + _UNPROVEN,
    )
