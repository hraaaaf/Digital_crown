"""LOT05.7C-F — documented Open Dental Patients-Raw *projection*, FAKE only.

Official docs describe configurable Patients-Raw fields and User Query comma CSV
export, NOT a fixed vendor-issued schema/version. This checks an explicitly
configured synthetic PatNum/FName/LName projection, not a real export.
Sources:
https://www.opendental.com/manual/reportpatientraw.html
https://www.opendental.com/manual/queryoverview.html
https://www.opendental.com/site/apipatients.html
NO import, target read/write, runtime route, patient data or vendor attestation.
"""
from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path
import re

from .legacy_migration_csv_envelope_lab_v15 import (
    SyntheticExportEnvelopeRefused, inspect_synthetic_csv_envelope,
)
from .legacy_migration_csv_mapping_lab_v15 import (
    SyntheticCsvMappingRefused, draft_synthetic_patient_mapping,
    simulate_synthetic_patient_csv,
)
from .legacy_sql_inspector_v15 import UnsafeSource, _copy_path, _hash
from .legacy_sql_mapping_v15 import ColumnDecision


class DocumentedDentalProjectionRefused(ValueError):
    """Input-independent, non-PHI failure codes only."""


# Open Dental *fields* are documented, but this three-column output projection
# is a Digital Crown test contract; no Open Dental export has been inspected.
_FIELD_MAP = {
    "PatNum": "legacy_id",
    "FName": "given_name",
    "LName": "family_name",
}
_PATNUM = re.compile(r"[1-9][0-9]{0,14}\Z")
_FAKE_FIRST = re.compile(r"FAKE_GIVEN_[0-9]{4,6}\Z")
_FAKE_LAST = re.compile(r"FAKE_FAMILY_[0-9]{4,6}\Z")


@dataclass(frozen=True)
class DocumentedDentalProjectionLab:
    source_sha256: str
    header_schema_sha256: str
    mapping_profile_sha256: str
    candidate_patient_count: int
    critical_count: int = 0
    warnings: tuple[str, ...] = (
        "OFFICIAL_EXPORT_MECHANISM_DOCUMENTED_NOT_FILE_ATTESTED",
        "OPERATOR_SELECTED_COLUMNS_NOT_FIXED_VENDOR_EXPORT",
        "FAKE_PATIENTS_ONLY_NO_IDENTITY_COLLISION_RECONCILIATION",
        "FNAME_LNAME_PATNUM_SEMANTIC_CANDIDATES_NOT_CLINICAL_APPROVAL",
    )
    lab_only: bool = True
    source_provenance_verified: bool = False
    vendor_format_compatible: bool = False
    mapping_human_approved: bool = False
    real_target_verified: bool = False
    backup_restore_verified: bool = False
    target_collisions: None = None
    target_rows_written: int = 0
    import_permitted: bool = False

    def public_dict(self) -> dict:
        """Only counts, hashes and fixed warning codes. Never expose rows."""
        return asdict(self)


def assess_synthetic_open_dental_patient_projection(
    source_path: Path,
    staging_root: Path,
    *,
    lab_only_synthetic_fixture: bool = False,
    attested_offline_copy: bool = False,
) -> DocumentedDentalProjectionLab:
    """Assess a controlled three-column project fixture, NEVER real PHI.

    Test-only mapping: PatNum -> legacy_id, FName -> given_name,
    LName -> family_name. No vendor-export guarantee or clinical approval.
    Require FAKE_ names even when lab flags are asserted, to limit accidental
    processing of identifiable real patient data.
    """
    if lab_only_synthetic_fixture is not True:
        raise DocumentedDentalProjectionRefused("LAB_SYNTHETIC_ONLY")
    if attested_offline_copy is not True:
        raise DocumentedDentalProjectionRefused("OFFLINE_COPY_ATTESTATION_REQUIRED")
    if not isinstance(source_path, Path) or not isinstance(staging_root, Path):
        raise DocumentedDentalProjectionRefused("STAGED_PATH_REQUIRED")

    try:
        envelope = inspect_synthetic_csv_envelope(
            source_path,
            staging_root,
            syntax_profile="csv-comma-utf8",
            lab_only_synthetic_fixture=True,
            attested_offline_copy=True,
        )
        path, _ = _copy_path(source_path, staging_root, True)
        before_stat = path.stat()
        before = (before_stat.st_dev, before_stat.st_ino,
                  before_stat.st_size, before_stat.st_mtime_ns)
        if _hash(path) != envelope.source_sha256:
            raise DocumentedDentalProjectionRefused("SOURCE_CHANGED_SINCE_ENVELOPE")

        seen: set[str] = set()
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.reader(stream, dialect="excel", strict=True)
            header = next(reader, None)
            if (not header or len(header) != len(_FIELD_MAP)
                    or set(header) != set(_FIELD_MAP)):
                raise DocumentedDentalProjectionRefused(
                    "DOCUMENTED_PROJECTION_FIELDS_MISMATCH"
                )
            for values in reader:
                row = dict(zip(header, values))
                # 05.7C-E already checks column count, size and unsafe cells.
                raw_id = row["PatNum"]
                if not _PATNUM.fullmatch(raw_id):
                    raise DocumentedDentalProjectionRefused(
                        "PATNUM_NOT_NUMERIC_RAW"
                    )
                if raw_id in seen:
                    raise DocumentedDentalProjectionRefused(
                        "DUPLICATE_SOURCE_PATNUM"
                    )
                seen.add(raw_id)
                if (not _FAKE_FIRST.fullmatch(row["FName"])
                        or not _FAKE_LAST.fullmatch(row["LName"])):
                    raise DocumentedDentalProjectionRefused(
                        "NON_FAKE_PATIENT_VALUES_FORBIDDEN"
                    )
        after_stat = path.stat()
        after = (after_stat.st_dev, after_stat.st_ino,
                 after_stat.st_size, after_stat.st_mtime_ns)
        if (before != after or _hash(path) != envelope.source_sha256
                or len(seen) != envelope.row_count):
            raise DocumentedDentalProjectionRefused("SOURCE_CHANGED_DURING_ASSESSMENT")

        # Existing 05.2 MappingDraft and 05.7C-C dry-run are reused, rather
        # than creating an alternate mapping approval or simulation engine.
        choices = tuple(ColumnDecision(h, _FIELD_MAP[h]) for h in header)
        draft = draft_synthetic_patient_mapping(
            path, staging_root,
            decisions=choices,
            source_software="DOCUMENTED_OPENDENTAL_PATIENTS_RAW_LAB_NOT_VERIFIED",
            source_version="PUBLIC_MANUAL_UNVERSIONED_PROJECTION_1",
            lab_only_synthetic_fixture=True,
            attested_offline_copy=True,
        )
        report = simulate_synthetic_patient_csv(
            path, staging_root, draft,
            lab_only_synthetic_fixture=True,
            attested_offline_copy=True,
        )
        if (report.critical_count != 0
                or report.accepted_candidate_rows != envelope.row_count
                or report.input_sha256 != envelope.source_sha256
                or report.mapping_approved is not False
                or report.import_permitted is not False
                or report.target_rows_written != 0
                or report.collisions is not None
                or _hash(path) != envelope.source_sha256):
            raise DocumentedDentalProjectionRefused("SYNTHETIC_RECONCILIATION_FAILED")
        return DocumentedDentalProjectionLab(
            source_sha256=envelope.source_sha256,
            header_schema_sha256=envelope.header_schema_sha256,
            mapping_profile_sha256=draft.profile_sha256,
            candidate_patient_count=envelope.row_count,
        )
    except DocumentedDentalProjectionRefused:
        raise
    except (SyntheticExportEnvelopeRefused, SyntheticCsvMappingRefused,
            UnsafeSource):
        # Never include input-derived text, paths or row fragments.
        raise DocumentedDentalProjectionRefused("UNSAFE_OR_UNSUPPORTED_FAKE_EXPORT") from None
    except (OSError, UnicodeError, csv.Error, ValueError, KeyError):
        raise DocumentedDentalProjectionRefused("INVALID_OR_CHANGED_FAKE_EXPORT") from None
