"""LOT05.7C-B — synthetic-only vendor-neutral patient CSV inventory.

This is NOT an importer. No database, ORM, application runtime, patient
record output, credentials, API route, or clinical target write.
Only disposable, operator-attested OFFLINE lab fixtures are accepted.
"""
from __future__ import annotations

import csv
import re
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

from .legacy_sql_inspector_v15 import UnsafeSource, _copy_path, _hash


class CsvPatientPreviewRefused(ValueError):
    """Stable non-PHI refusal code. Never include raw cells or file paths."""


@dataclass(frozen=True)
class CsvPatientPreview:
    source_sha256: str
    source_size_bytes: int
    source_format: str
    row_count: int
    column_count: int
    date_field_present: bool
    warnings: tuple[str, ...] = (
        "LAB_SYNTHETIC_PATIENT_IDENTITY_PREVIEW_ONLY",
        "NO_VENDOR_EXPORT_COMPATIBILITY_ATTESTED",
        "NO_TARGET_RECONCILIATION",
    )
    lab_only: bool = True
    vendor_adapter_implemented: bool = False
    schema_semantics_certified: bool = False
    mapping_approved: bool = False
    dry_run_completed: bool = False
    target_rows_written: int = 0
    full_schema_certified: bool = False
    import_permitted: bool = False

    def to_public_dict(self) -> dict:
        """Counts and source hash only; no row, legacy ID, name or date."""
        return asdict(self)


_REQUIRED = frozenset(("legacy_id", "given_name", "family_name"))
_ALLOWED = _REQUIRED | {"birth_date"}
_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")
_ISO_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}\Z")
_MAX_ROWS = 10_000
_MAX_COLS = 4
_MAX_FIELD = 256


def _safe_cell(value: str) -> bool:
    if not isinstance(value, str) or len(value) > _MAX_FIELD:
        return False
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in value):
        return False
    # Reject spreadsheet formula execution even after whitespace padding.
    if value.lstrip(" ").startswith(("=", "+", "-", "@")):
        return False
    return True


def preview_synthetic_patient_csv(
    source_path: Path,
    staging_root: Path,
    *,
    lab_only_synthetic_fixture: bool = False,
    attested_offline_copy: bool = False,
) -> CsvPatientPreview:
    """Check a small FAKE CSV export without exposing any cell or writing rows.

    Format v1 has exact case-sensitive headers:
    legacy_id,given_name,family_name[,birth_date] (any order).
    The standardized format is a contract for lab fixtures, not proof that
    any dental vendor can export this format directly.
    """
    if lab_only_synthetic_fixture is not True:
        raise CsvPatientPreviewRefused("LAB_SYNTHETIC_ONLY")
    if attested_offline_copy is not True:
        raise CsvPatientPreviewRefused("OFFLINE_COPY_ATTESTATION_REQUIRED")
    if not isinstance(source_path, Path) or not isinstance(staging_root, Path):
        raise CsvPatientPreviewRefused("STAGED_PATH_REQUIRED")
    if source_path.suffix.lower() != ".csv":
        raise CsvPatientPreviewRefused("CSV_EXTENSION_REQUIRED")
    try:
        source, size = _copy_path(source_path, staging_root, True)
    except UnsafeSource as exc:
        raise CsvPatientPreviewRefused(str(exc)) from None

    try:
        before_stat = source.stat()
        before_identity = (
            before_stat.st_dev, before_stat.st_ino, before_stat.st_size,
            before_stat.st_mtime_ns,
        )
        digest_before = _hash(source)
        seen_ids: set[str] = set()
        count = 0
        with source.open("r", encoding="utf-8-sig", newline="") as stream:
            rows = csv.reader(stream, dialect="excel", strict=True)
            header = next(rows, None)
            if header is None or not header or len(header) > _MAX_COLS:
                raise CsvPatientPreviewRefused("INVALID_CSV_HEADER")
            if len(header) != len(set(header)):
                raise CsvPatientPreviewRefused("DUPLICATE_CSV_COLUMN")
            if not _REQUIRED.issubset(header) or not set(header).issubset(_ALLOWED):
                raise CsvPatientPreviewRefused("UNSUPPORTED_CSV_COLUMNS")
            has_date = "birth_date" in header
            for values in rows:
                count += 1
                if count > _MAX_ROWS:
                    raise CsvPatientPreviewRefused("CSV_ROW_LIMIT_EXCEEDED")
                if len(values) != len(header):
                    raise CsvPatientPreviewRefused("CSV_COLUMN_COUNT_MISMATCH")
                if not all(_safe_cell(value) for value in values):
                    raise CsvPatientPreviewRefused("UNSAFE_CSV_CELL")
                record = dict(zip(header, values))
                source_id = record["legacy_id"]
                if not _ID.fullmatch(source_id):
                    raise CsvPatientPreviewRefused("INVALID_SOURCE_PATIENT_ID")
                if source_id in seen_ids:
                    raise CsvPatientPreviewRefused("DUPLICATE_SOURCE_PATIENT_ID")
                seen_ids.add(source_id)
                for field in ("given_name", "family_name"):
                    if not record[field] or record[field].strip() != record[field]:
                        raise CsvPatientPreviewRefused("INVALID_ADMIN_PATIENT_NAME")
                if has_date and record["birth_date"]:
                    value = record["birth_date"]
                    if not _ISO_DATE.fullmatch(value):
                        raise CsvPatientPreviewRefused("AMBIGUOUS_PATIENT_BIRTH_DATE")
                    try:
                        date.fromisoformat(value)
                    except ValueError:
                        raise CsvPatientPreviewRefused("INVALID_PATIENT_BIRTH_DATE") from None
        if count == 0:
            raise CsvPatientPreviewRefused("EMPTY_PATIENT_CSV")
        after_stat = source.stat()
        after_identity = (
            after_stat.st_dev, after_stat.st_ino, after_stat.st_size,
            after_stat.st_mtime_ns,
        )
        if before_identity != after_identity or size != after_stat.st_size or _hash(source) != digest_before:
            raise CsvPatientPreviewRefused("SOURCE_CHANGED_DURING_PREVIEW")
        return CsvPatientPreview(
            source_sha256=digest_before,
            source_size_bytes=size,
            source_format="synthetic-patient-csv-v1",
            row_count=count,
            column_count=len(header),
            date_field_present=has_date,
        )
    except CsvPatientPreviewRefused:
        raise
    except (OSError, UnicodeError, csv.Error) as exc:
        raise CsvPatientPreviewRefused("INVALID_OR_CHANGED_CSV") from None
