"""LOT05.7C-G — offline header-only probe for *official demo* export review.

This is an evidence acquisition aid, not a vendor compatibility attestation,
patient importer, or a validation of record contents. Intended only for a
locally installed Open Dental trial's fictional demo database, in isolation.
Open Dental documents the demo with fictional patients and the configurable
Patients-Raw / User Query comma-CSV export, NOT fixed header order/format.
https://opendental.com/site/trial.html
https://www.opendental.com/manual/reportpatientraw.html
https://www.opendental.com/manual/queryoverview.html

NO API, credentials, network, SQL execution, row parsing, target DB, runtime
integration, file mutation, patient values, or actual clinical import.
"""
from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
import hashlib
from pathlib import Path
import re

# Direct script mode avoids importing backend/__init__.py (ORM model registration).
# Package mode is retained for the isolated standalone FUE harness.
if __package__:
    from .legacy_sql_inspector_v15 import UnsafeSource, _copy_path, _hash
else:
    from legacy_sql_inspector_v15 import UnsafeSource, _copy_path, _hash


class DemoExportHeaderRefused(ValueError):
    """Stable refusal code; never echo input paths, names or row content."""


_PROJECTION = frozenset(("PatNum", "FName", "LName"))
_VERSION = re.compile(r"[0-9]{2}\.[0-9]{1,2}(?:\.[0-9]{1,4})?\Z")
_MAX_HEADER_BYTES = 512
_DOMAIN = b"DIGITAL-CROWN-LOT05-7C-G-DEMO-HEADER-V1\x00"


@dataclass(frozen=True)
class DemoExportHeaderEvidence:
    """Metadata only: does not establish vendor version or record semantics."""

    file_sha256: str
    file_size_bytes: int
    header_schema_sha256: str
    operator_declared_demo_version: str
    matched_project_projection: bool = True
    observed_header_field_count: int = 3
    patient_row_count: None = None
    warnings: tuple[str, ...] = (
        "OFFICIAL_TRIAL_EXPORT_NOT_INDEPENDENTLY_OBSERVED",
        "OPERATOR_DECLARATION_IS_NOT_SOURCE_PROVENANCE",
        "NO_ROWS_PARSED_OR_PATIENT_CONTENT_VALIDATED",
        "NOT_A_FIXED_VENDOR_EXPORT_SCHEMA",
    )
    actual_demo_source_verified: bool = False
    source_provenance_verified: bool = False
    vendor_format_compatible: bool = False
    mapping_human_approved: bool = False
    target_collisions: None = None
    target_rows_written: int = 0
    import_permitted: bool = False

    def public_dict(self) -> dict:
        """Never include source columns, paths or row contents."""
        return asdict(self)


def probe_offline_demo_csv_header(
    source_path: Path,
    staging_root: Path,
    *,
    operator_declared_demo_version: str,
    lab_only_synthetic_fixture: bool = False,
    attested_offline_copy: bool = False,
    operator_declared_official_demo: bool = False,
) -> DemoExportHeaderEvidence:
    """Match one exact selected CSV header, without decoding any patient rows.

    Version is reported as *operator-declared* only. It is not compared with a
    vendor-signed manifest; human version/screenshot verification is required.
    Hashing the file processes bytes, but does not decode or publish row data.
    """
    if lab_only_synthetic_fixture is not True:
        raise DemoExportHeaderRefused("LAB_SYNTHETIC_ONLY")
    if attested_offline_copy is not True:
        raise DemoExportHeaderRefused("OFFLINE_COPY_ATTESTATION_REQUIRED")
    if operator_declared_official_demo is not True:
        raise DemoExportHeaderRefused("OFFICIAL_DEMO_DECLARATION_REQUIRED")
    if not isinstance(source_path, Path) or not isinstance(staging_root, Path):
        raise DemoExportHeaderRefused("STAGED_PATH_REQUIRED")
    if (not isinstance(operator_declared_demo_version, str)
            or not _VERSION.fullmatch(operator_declared_demo_version)):
        raise DemoExportHeaderRefused("INVALID_DECLARED_DEMO_VERSION")
    if source_path.suffix.lower() != ".csv":
        raise DemoExportHeaderRefused("CSV_EXTENSION_REQUIRED")
    try:
        source, size = _copy_path(source_path, staging_root, True)
        first_stat = source.stat()
        identity_before = (
            first_stat.st_dev, first_stat.st_ino,
            first_stat.st_size, first_stat.st_mtime_ns,
        )
        sha_before = _hash(source)
        # Read only the first physical line. Do not parse or count patient rows.
        with source.open("rb") as stream:
            raw_header = stream.readline(_MAX_HEADER_BYTES + 1)
        if len(raw_header) > _MAX_HEADER_BYTES:
            raise DemoExportHeaderRefused("HEADER_TOO_LARGE")
        if not raw_header.endswith(b"\n"):
            raise DemoExportHeaderRefused("UNTERMINATED_OR_MULTILINE_HEADER")
        try:
            text = raw_header.decode("utf-8-sig")
            fields = next(csv.reader([text], dialect="excel", strict=True))
        except (UnicodeError, csv.Error, StopIteration):
            raise DemoExportHeaderRefused("INVALID_CSV_HEADER") from None
        if len(fields) != 3 or set(fields) != _PROJECTION:
            raise DemoExportHeaderRefused("SELECTED_PROJECTION_HEADER_MISMATCH")

        end_stat = source.stat()
        identity_after = (
            end_stat.st_dev, end_stat.st_ino,
            end_stat.st_size, end_stat.st_mtime_ns,
        )
        if (identity_before != identity_after or size != end_stat.st_size
                or _hash(source) != sha_before):
            raise DemoExportHeaderRefused("SOURCE_CHANGED_DURING_PROBE")
        digest = hashlib.sha256(
            _DOMAIN + b"\x00".join(k.encode("ascii") for k in sorted(_PROJECTION))
        ).hexdigest()
        return DemoExportHeaderEvidence(
            file_sha256=sha_before,
            file_size_bytes=size,
            header_schema_sha256=digest,
            operator_declared_demo_version=operator_declared_demo_version,
        )
    except DemoExportHeaderRefused:
        raise
    except UnsafeSource as exc:
        raise DemoExportHeaderRefused(str(exc)) from None
    except (OSError, ValueError):
        raise DemoExportHeaderRefused("INVALID_OR_CHANGED_DEMO_COPY") from None


def _main() -> int:
    """One-shot local QA only. No file uploads or network calls."""
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="LAB demo-only CSV header evidence (no row inspection or import)"
    )
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--staging-root", type=Path, required=True)
    parser.add_argument("--demo-version", required=True)
    parser.add_argument("--synthetic-only", action="store_true")
    parser.add_argument("--offline-copy", action="store_true")
    parser.add_argument("--official-demo-only", action="store_true")
    args = parser.parse_args()
    try:
        evidence = probe_offline_demo_csv_header(
            args.source,
            args.staging_root,
            operator_declared_demo_version=args.demo_version,
            lab_only_synthetic_fixture=args.synthetic_only,
            attested_offline_copy=args.offline_copy,
            operator_declared_official_demo=args.official_demo_only,
        )
    except DemoExportHeaderRefused as exc:
        print("REFUSED: " + str(exc))
        return 2
    print(json.dumps(evidence.public_dict(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
