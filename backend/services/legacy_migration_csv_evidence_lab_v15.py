"""LOT05.7C-D: reproducible FAKE-only CSV simulation evidence (NO IMPORT).

A SHA256 evidence digest detects accidental changes; it is NOT a signature,
a vendor-provenance certificate, staff authorization or clinical clearance.
No patient values, paths, target DB, API, ORM, network or write operations.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import hmac
import json
import re
from pathlib import Path

from .legacy_migration_csv_mapping_lab_v15 import (
    SyntheticCsvDryRun,
    SyntheticCsvMappingRefused,
    simulate_synthetic_patient_csv,
)
from .legacy_sql_mapping_v15 import MappingDraft

_DOMAIN = b"DIGITAL-CROWN-LOT05-7C-D-LAB-REPLAY-V1\x00"
_SHA = re.compile(r"[a-f0-9]{64}\Z")


class CsvLabEvidenceRefused(ValueError):
    """Non-sensitive stable error codes only."""


@dataclass(frozen=True)
class CsvLabEvidence:
    """Only digests and aggregates, NEVER patient details or vendor claims."""

    source_sha256: str
    mapping_profile_sha256: str
    synthetic_target_schema_sha256: str
    report_sha256: str
    evidence_sha256: str
    patient_row_count: int
    candidate_row_count: int
    critical_row_count: int
    unmapped_column_count: int
    target_collisions: None = None
    source_provenance_verified: bool = False
    vendor_format_compatible: bool = False
    real_clinical_target_verified: bool = False
    backup_restore_verified: bool = False
    mapping_human_approved: bool = False
    import_permitted: bool = False
    target_rows_written: int = 0
    evidence_kind: str = "SYNTHETIC_CSV_AGGREGATE_REPLAY_ONLY"

    def public_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class CsvLabReplayReceipt:
    evidence_sha256: str
    source_sha256: str
    mapping_profile_sha256: str
    lab_replay_matched: bool = True
    source_provenance_verified: bool = False
    vendor_format_compatible: bool = False
    clinical_import_permitted: bool = False
    target_rows_written: int = 0

    def public_dict(self) -> dict:
        return asdict(self)


def _canonical(value: dict) -> bytes:
    # The input is composed only from fixed keys and non-PHI aggregate primitives.
    return json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("ascii")


def _evidence_hash(payload: dict) -> str:
    return hashlib.sha256(_DOMAIN + _canonical(payload)).hexdigest()


def _report_hash(report: SyntheticCsvDryRun) -> str:
    if type(report) is not SyntheticCsvDryRun:
        raise CsvLabEvidenceRefused("UNEXPECTED_SIMULATION_REPORT")
    # The existing LOT05.7C-C public report contains no source-row values.
    return hashlib.sha256(_DOMAIN + b"report\x00" + _canonical(
        report.to_public_dict()
    )).hexdigest()


def _payload(evidence: CsvLabEvidence) -> dict:
    obj = evidence.public_dict()
    obj.pop("evidence_sha256")
    return obj


def _validate_immutable_flags(evidence: CsvLabEvidence) -> None:
    if (evidence.target_collisions is not None
            or evidence.source_provenance_verified is not False
            or evidence.vendor_format_compatible is not False
            or evidence.real_clinical_target_verified is not False
            or evidence.backup_restore_verified is not False
            or evidence.mapping_human_approved is not False
            or evidence.import_permitted is not False
            or type(evidence.target_rows_written) is not int
            or evidence.target_rows_written != 0
            or evidence.evidence_kind != "SYNTHETIC_CSV_AGGREGATE_REPLAY_ONLY"):
        raise CsvLabEvidenceRefused("CLINICAL_OR_VENDOR_APPROVAL_FORBIDDEN")


def _make_bundle(report: SyntheticCsvDryRun, draft: MappingDraft) -> CsvLabEvidence:
    if type(draft) is not MappingDraft:
        raise CsvLabEvidenceRefused("MAPPING_DRAFT_REQUIRED")
    if (report.import_permitted is not False
            or report.mapping_approved is not False
            or report.full_schema_certified is not False
            or report.target_backup_verified is not False
            or report.target_rows_written != 0
            or report.collisions is not None):
        raise CsvLabEvidenceRefused("SIMULATION_AUTHORIZATION_FORBIDDEN")
    if (report.input_sha256 != draft.source_file_sha256
            or report.mapping_profile_sha256 != draft.profile_sha256):
        raise CsvLabEvidenceRefused("MAPPING_OR_SOURCE_FINGERPRINT_MISMATCH")
    if (any(type(value) is not int for value in (
            report.counts_by_entity.get("patients"),
            report.accepted_candidate_rows, report.critical_count,
            report.unmapped_columns))
            or report.counts_by_entity.get("patients", 0) < 1
            or report.accepted_candidate_rows < 0
            or report.critical_count < 0
            or report.accepted_candidate_rows + report.critical_count
            != report.counts_by_entity["patients"]):
        raise CsvLabEvidenceRefused("INVALID_SIMULATION_COUNTS")
    if not all(type(x) is str and _SHA.fullmatch(x) for x in (
        draft.source_file_sha256, draft.profile_sha256,
        draft.target_schema_sha256,
    )):
        raise CsvLabEvidenceRefused("INVALID_EVIDENCE_FINGERPRINT")

    fields = {
        "source_sha256": draft.source_file_sha256,
        "mapping_profile_sha256": draft.profile_sha256,
        "synthetic_target_schema_sha256": draft.target_schema_sha256,
        "report_sha256": _report_hash(report),
        "patient_row_count": report.counts_by_entity["patients"],
        "candidate_row_count": report.accepted_candidate_rows,
        "critical_row_count": report.critical_count,
        "unmapped_column_count": report.unmapped_columns,
    }
    # Use the same typed invariant defaults as CsvLabEvidence for the digest.
    provisional = CsvLabEvidence(evidence_sha256="", **fields)
    _validate_immutable_flags(provisional)
    return CsvLabEvidence(evidence_sha256=_evidence_hash(_payload(provisional)), **fields)


def build_synthetic_csv_evidence(
    source_path: Path,
    staging_root: Path,
    draft: MappingDraft,
    *,
    lab_only_synthetic_fixture: bool = False,
    attested_offline_copy: bool = False,
) -> CsvLabEvidence:
    """Replay existing mapping/simulation gates; emit count-only evidence."""
    if lab_only_synthetic_fixture is not True:
        raise CsvLabEvidenceRefused("LAB_SYNTHETIC_ONLY")
    if attested_offline_copy is not True:
        raise CsvLabEvidenceRefused("OFFLINE_COPY_ATTESTATION_REQUIRED")
    try:
        report = simulate_synthetic_patient_csv(
            source_path, staging_root, draft,
            lab_only_synthetic_fixture=True, attested_offline_copy=True,
        )
    except SyntheticCsvMappingRefused as exc:
        # Existing stable, non-PHI refusal codes only.
        raise CsvLabEvidenceRefused(str(exc)) from None
    return _make_bundle(report, draft)


def verify_synthetic_csv_evidence(
    evidence: CsvLabEvidence,
    source_path: Path,
    staging_root: Path,
    draft: MappingDraft,
    *,
    lab_only_synthetic_fixture: bool = False,
    attested_offline_copy: bool = False,
) -> CsvLabReplayReceipt:
    """Replay against unchanged source and MappingDraft; never grant clinical use.

    A matching SHA digest alone proves neither vendor authorship nor an
    approved clinical import. It is only reproducibility of fake lab evidence.
    """
    if type(evidence) is not CsvLabEvidence:
        raise CsvLabEvidenceRefused("EVIDENCE_BUNDLE_REQUIRED")
    _validate_immutable_flags(evidence)
    if (type(evidence.evidence_sha256) is not str
            or not _SHA.fullmatch(evidence.evidence_sha256)):
        raise CsvLabEvidenceRefused("INVALID_EVIDENCE_FINGERPRINT")
    try:
        current_hash = _evidence_hash(_payload(evidence))
    except (TypeError, ValueError, OverflowError, RecursionError):
        raise CsvLabEvidenceRefused("INVALID_EVIDENCE_BUNDLE") from None
    if not hmac.compare_digest(current_hash, evidence.evidence_sha256):
        raise CsvLabEvidenceRefused("EVIDENCE_BUNDLE_TAMPERED")
    current = build_synthetic_csv_evidence(
        source_path, staging_root, draft,
        lab_only_synthetic_fixture=lab_only_synthetic_fixture,
        attested_offline_copy=attested_offline_copy,
    )
    if not hmac.compare_digest(current.evidence_sha256, evidence.evidence_sha256):
        raise CsvLabEvidenceRefused("EVIDENCE_REPLAY_MISMATCH")
    return CsvLabReplayReceipt(
        evidence_sha256=evidence.evidence_sha256,
        source_sha256=current.source_sha256,
        mapping_profile_sha256=current.mapping_profile_sha256,
    )
