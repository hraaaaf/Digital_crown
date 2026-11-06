"""LOT05.7C-C — OFFLINE FAKE-only patient CSV mapping + count-only simulation.

Not an importer. Deliberately reuses 05.2 MappingDraft and 05.1 staging gates.
No database, ORM, API, UI, customer vendor parser, credentials or patient rows in output.
"""
from __future__ import annotations

import csv
import re
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

from .legacy_migration_csv_preview_v15 import _ID, _ISO_DATE, _MAX_FIELD, _MAX_ROWS, _safe_cell
from .legacy_sql_inspector_v15 import (
    ColumnInventory, InspectionReport, TableInventory, UnsafeSource, _copy_path, _hash,
)
from .legacy_sql_mapping_v15 import (
    ColumnDecision, MappingDraft, MappingRejected, TableDecision,
    TargetSnapshot, TargetTable, _is_secret, build_mapping_draft,
    revalidate_mapping_draft,
)


class SyntheticCsvMappingRefused(ValueError):
    """Stable code only; never put source row, path, column or vendor in message."""


_TARGET = TargetSnapshot(
    schema_revision="lot05-7c-c-patient-admin-synthetic-v1",
    tables=(TargetTable("patients", ("legacy_id", "given_name", "family_name", "birth_date")),),
)
_REQUIRED = frozenset(("legacy_id", "given_name", "family_name"))
_HEADER = re.compile(r"[A-Za-z][A-Za-z0-9_]{0,39}\Z")
_MAX_HEADERS = 16


@dataclass(frozen=True)
class SyntheticCsvDryRun:
    input_sha256: str
    mapping_profile_sha256: str
    counts_by_entity: dict[str, int]
    accepted_candidate_rows: int
    anomalies: dict[str, int]
    duplicates: int
    ignored: int
    collisions: int
    unmapped_columns: int
    ambiguous_dates: int
    critical_count: int
    warnings: tuple[str, ...] = (
        "LAB_FAKE_ONLY_NOT_A_CLINICAL_DRY_RUN",
        "HUMAN_MAPPING_APPROVAL_NOT_IMPLEMENTED",
        "SOURCE_VENDOR_EXPORT_NOT_VERIFIED",
        "TARGET_IDENTITY_RECONCILIATION_NOT_PERFORMED",
    )
    dry_run_completed: bool = True
    mapping_approved: bool = False
    target_backup_verified: bool = False
    target_rows_written: int = 0
    full_schema_certified: bool = False
    import_permitted: bool = False

    def to_public_dict(self) -> dict:
        """Never disclose source names, identifiers, dates, row content, or paths."""
        return asdict(self)


def _source_schema(
    source_path: Path,
    staging_root: Path,
    *,
    lab_only_synthetic_fixture: bool,
    attested_offline_copy: bool,
) -> tuple[Path, InspectionReport, tuple[str, ...]]:
    if lab_only_synthetic_fixture is not True:
        raise SyntheticCsvMappingRefused("LAB_SYNTHETIC_ONLY")
    if attested_offline_copy is not True:
        raise SyntheticCsvMappingRefused("OFFLINE_COPY_ATTESTATION_REQUIRED")
    if not isinstance(source_path, Path) or not isinstance(staging_root, Path):
        raise SyntheticCsvMappingRefused("STAGED_PATH_REQUIRED")
    if source_path.suffix.lower() != ".csv":
        raise SyntheticCsvMappingRefused("CSV_EXTENSION_REQUIRED")
    try:
        path, size = _copy_path(source_path, staging_root, True)
        start = path.stat()
        before = (start.st_dev, start.st_ino, start.st_size, start.st_mtime_ns)
        digest = _hash(path)
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.reader(stream, dialect="excel", strict=True)
            columns = next(reader, None)
        if not columns or len(columns) > _MAX_HEADERS:
            raise SyntheticCsvMappingRefused("UNSUPPORTED_CSV_HEADER")
        if any(not _HEADER.fullmatch(h) or _is_secret(h) for h in columns):
            raise SyntheticCsvMappingRefused("UNSAFE_CSV_HEADER")
        if len({h.casefold() for h in columns}) != len(columns):
            raise SyntheticCsvMappingRefused("DUPLICATE_CSV_HEADER")
        end = path.stat()
        after = (end.st_dev, end.st_ino, end.st_size, end.st_mtime_ns)
        if before != after or size != end.st_size or digest != _hash(path):
            raise SyntheticCsvMappingRefused("SOURCE_CHANGED_DURING_INSPECTION")
        report = InspectionReport(
            dialect_declared="synthetic-csv",
            source_format="synthetic-csv-patient-admin-v1",
            sha256=digest,
            file_size_bytes=size,
            tables=(TableInventory("csv_patients", tuple(
                ColumnInventory(column, "TEXT") for column in columns
            )),),
            warnings=("LAB_FAKE_ONLY", "SCHEMA_NOT_VENDOR_VERIFIED"),
        )
        return path, report, tuple(columns)
    except SyntheticCsvMappingRefused:
        raise
    except UnsafeSource as exc:
        raise SyntheticCsvMappingRefused(str(exc)) from None
    except (OSError, UnicodeError, csv.Error):
        raise SyntheticCsvMappingRefused("INVALID_CSV_SOURCE") from None


def draft_synthetic_patient_mapping(
    source_path: Path,
    staging_root: Path,
    *,
    decisions: tuple[ColumnDecision, ...],
    source_software: str,
    source_version: str,
    lab_only_synthetic_fixture: bool = False,
    attested_offline_copy: bool = False,
) -> MappingDraft:
    """Require explicit operator choices for EVERY source column, including UNMAPPED.

    The return is a 05.2 unapproved MappingDraft, not a human approval record.
    """
    _, source, _ = _source_schema(
        source_path, staging_root, lab_only_synthetic_fixture=lab_only_synthetic_fixture,
        attested_offline_copy=attested_offline_copy,
    )
    if not isinstance(decisions, tuple):
        raise SyntheticCsvMappingRefused("MAPPING_DECISIONS_REQUIRED")
    try:
        draft = build_mapping_draft(
            source, _TARGET, (TableDecision("csv_patients", "patients", decisions),),
            source_software=source_software, source_version=source_version,
            profile_version=1,
        )
    except MappingRejected:
        raise SyntheticCsvMappingRefused("MAPPING_DECISIONS_INVALID") from None
    destinations = {
        choice.target_column for choice in draft.decisions[0].columns
        if choice.target_column is not None
    }
    if not _REQUIRED.issubset(destinations):
        raise SyntheticCsvMappingRefused("REQUIRED_PATIENT_MAPPING_INCOMPLETE")
    return draft


def simulate_synthetic_patient_csv(
    source_path: Path,
    staging_root: Path,
    draft: MappingDraft,
    *,
    lab_only_synthetic_fixture: bool = False,
    attested_offline_copy: bool = False,
) -> SyntheticCsvDryRun:
    """Zero-write, non-PHI aggregate simulation; NEVER promotes an approval."""
    path, source, headers = _source_schema(
        source_path, staging_root, lab_only_synthetic_fixture=lab_only_synthetic_fixture,
        attested_offline_copy=attested_offline_copy,
    )
    if not isinstance(draft, MappingDraft):
        raise SyntheticCsvMappingRefused("MAPPING_DRAFT_REQUIRED")
    try:
        result = revalidate_mapping_draft(draft, source, _TARGET)
    except MappingRejected:
        raise SyntheticCsvMappingRefused("MAPPING_DRAFT_INVALID") from None
    if not result.exact_source_and_target:
        raise SyntheticCsvMappingRefused("MAPPING_SOURCE_OR_TARGET_CHANGED")
    if len(draft.decisions) != 1 or draft.decisions[0].source_table != "csv_patients":
        raise SyntheticCsvMappingRefused("INVALID_CSV_MAPPING_TABLE")
    choices = draft.decisions[0].columns
    source_to_target = {d.source_column: d.target_column for d in choices}
    targets = {d.target_column: d.source_column for d in choices if d.target_column is not None}
    if not _REQUIRED.issubset(targets) or set(source_to_target) != set(headers):
        raise SyntheticCsvMappingRefused("MAPPING_COVERAGE_INCOMPLETE")

    original_stat = path.stat()
    original_id = (
        original_stat.st_dev, original_stat.st_ino, original_stat.st_size,
        original_stat.st_mtime_ns,
    )
    row_count = 0
    duplicates = 0
    invalid_ids = 0
    invalid_names = 0
    ambiguous_dates = 0
    critical_rows = 0
    seen_ids: set[str] = set()
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.reader(stream, dialect="excel", strict=True)
            observed = next(reader, None)
            if tuple(observed or ()) != headers:
                raise SyntheticCsvMappingRefused("SOURCE_HEADER_CHANGED")
            for fields in reader:
                row_count += 1
                if row_count > _MAX_ROWS:
                    raise SyntheticCsvMappingRefused("CSV_ROW_LIMIT_EXCEEDED")
                if len(fields) != len(headers):
                    raise SyntheticCsvMappingRefused("INVALID_CSV_ROW_LENGTH")
                # Unmapped columns are STILL inspected for unsafe content.
                if not all(_safe_cell(cell) for cell in fields):
                    raise SyntheticCsvMappingRefused("UNSAFE_CSV_CELL")
                row = dict(zip(headers, fields))
                old_id = row[targets["legacy_id"]]
                bad_id = _ID.fullmatch(old_id) is None
                duplicate = False
                if not bad_id:
                    normalized = old_id.casefold()
                    duplicate = normalized in seen_ids
                    seen_ids.add(normalized)
                bad_name = any(
                    not row[targets[key]] or row[targets[key]].strip() != row[targets[key]]
                    for key in ("given_name", "family_name")
                )
                bad_date = False
                if "birth_date" in targets:
                    raw = row[targets["birth_date"]]
                    if raw and not _ISO_DATE.fullmatch(raw):
                        bad_date = True
                    elif raw:
                        try:
                            date.fromisoformat(raw)
                        except ValueError:
                            bad_date = True
                invalid_ids += int(bad_id)
                invalid_names += int(bad_name)
                duplicates += int(duplicate)
                ambiguous_dates += int(bad_date)
                critical_rows += int(bad_id or bad_name or duplicate or bad_date)
        if row_count == 0:
            raise SyntheticCsvMappingRefused("EMPTY_PATIENT_CSV")
        final_stat = path.stat()
        final_id = (
            final_stat.st_dev, final_stat.st_ino, final_stat.st_size,
            final_stat.st_mtime_ns,
        )
        if original_id != final_id or _hash(path) != draft.source_file_sha256:
            raise SyntheticCsvMappingRefused("SOURCE_CHANGED_DURING_SIMULATION")
    except SyntheticCsvMappingRefused:
        raise
    except (OSError, UnicodeError, csv.Error):
        raise SyntheticCsvMappingRefused("INVALID_OR_CHANGED_CSV") from None

    return SyntheticCsvDryRun(
        input_sha256=source.sha256,
        mapping_profile_sha256=draft.profile_sha256,
        counts_by_entity={"patients": row_count},
        accepted_candidate_rows=row_count - critical_rows,
        anomalies={
            "invalid_source_id": invalid_ids,
            "invalid_name": invalid_names,
            "duplicate_source_id": duplicates,
            "ambiguous_birth_date": ambiguous_dates,
        },
        duplicates=duplicates,
        ignored=0,
        collisions=0,  # Target DB not inspected; NOT a claim of no target collisions.
        unmapped_columns=sum(choice.target_column is None for choice in choices),
        ambiguous_dates=ambiguous_dates,
        critical_count=critical_rows,
    )
