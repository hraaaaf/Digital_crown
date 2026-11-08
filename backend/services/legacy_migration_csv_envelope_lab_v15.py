"""LOT05.7C-E: read-only FAKE export syntax envelope, NOT vendor compatibility.

An explicit CSV/TSV syntax choice is checked on an attested *synthetic*
offline copy. No import, mapping approval, live database, vendor assertion,
PHI output, file mutation, API route, network access, or target operation.
"""
from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
import hashlib
from pathlib import Path
import re

from .legacy_migration_csv_preview_v15 import _safe_cell
from .legacy_sql_inspector_v15 import UnsafeSource, _copy_path, _hash
from .legacy_sql_mapping_v15 import _is_secret


class SyntheticExportEnvelopeRefused(ValueError):
    """Refusals are stable non-PHI codes, not input-derived strings."""


# These are wire *syntax* options, not claims about any software vendor.
_FORMATS = {
    "csv-comma-utf8": (".csv", ","),
    "csv-semicolon-utf8": (".csv", ";"),
    "tsv-tab-utf8": (".tsv", "\t"),
}
_HEADER = re.compile(r"[A-Za-z][A-Za-z0-9_]{0,39}\Z")
_MAX_COLS = 16
_MAX_ROWS = 10_000
_DOMAIN = b"DIGITAL-CROWN-LOT05-7C-E-FAKE-HEADERS-V1\x00"


@dataclass(frozen=True)
class SyntheticExportEnvelope:
    source_sha256: str
    source_size_bytes: int
    syntax_profile_declared: str
    header_schema_sha256: str
    column_count: int
    row_count: int
    warnings: tuple[str, ...] = (
        "SYNTAX_LAB_ONLY_NOT_VENDOR_COMPATIBILITY",
        "SOURCE_ENTITY_AND_FIELD_SEMANTICS_UNKNOWN",
        "NO_TARGET_OR_CLINICAL_DRY_RUN",
    )
    source_provenance_verified: bool = False
    vendor_format_compatible: bool = False
    mapping_human_approved: bool = False
    real_target_verified: bool = False
    backup_restore_verified: bool = False
    target_collisions: None = None
    target_rows_written: int = 0
    import_permitted: bool = False

    def public_dict(self) -> dict:
        """Only fixed metadata, digests and counts; no headers or cells."""
        return asdict(self)


def inspect_synthetic_csv_envelope(
    source_path: Path,
    staging_root: Path,
    *,
    syntax_profile: str,
    lab_only_synthetic_fixture: bool = False,
    attested_offline_copy: bool = False,
) -> SyntheticExportEnvelope:
    """Read an explicitly declared FAKE CSV/TSV syntax without target access.

    This is NOT automatic format detection, schema compatibility or mapping.
    A matching syntax does not mean a vendor can export that format.
    """
    if lab_only_synthetic_fixture is not True:
        raise SyntheticExportEnvelopeRefused("LAB_SYNTHETIC_ONLY")
    if attested_offline_copy is not True:
        raise SyntheticExportEnvelopeRefused("OFFLINE_COPY_ATTESTATION_REQUIRED")
    if type(syntax_profile) is not str or syntax_profile not in _FORMATS:
        raise SyntheticExportEnvelopeRefused("UNSUPPORTED_SYNTAX_PROFILE")
    if type(source_path) is not Path or type(staging_root) is not Path:
        raise SyntheticExportEnvelopeRefused("STAGED_PATH_REQUIRED")
    suffix, delimiter = _FORMATS[syntax_profile]
    if source_path.suffix.lower() != suffix:
        raise SyntheticExportEnvelopeRefused("EXPORT_EXTENSION_MISMATCH")
    try:
        source, original_size = _copy_path(source_path, staging_root, True)
        before_stat = source.stat()
        before = (before_stat.st_dev, before_stat.st_ino,
                  before_stat.st_size, before_stat.st_mtime_ns)
        digest_before = _hash(source)
        with source.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.reader(stream, delimiter=delimiter, strict=True)
            headers = next(reader, None)
            if not headers or not (2 <= len(headers) <= _MAX_COLS):
                raise SyntheticExportEnvelopeRefused("UNSUPPORTED_EXPORT_HEADER")
            if any(not _HEADER.fullmatch(h) or _is_secret(h) for h in headers):
                raise SyntheticExportEnvelopeRefused("UNSAFE_EXPORT_HEADER")
            if len({h.casefold() for h in headers}) != len(headers):
                raise SyntheticExportEnvelopeRefused("DUPLICATE_EXPORT_HEADER")
            count = 0
            for values in reader:
                count += 1
                if count > _MAX_ROWS:
                    raise SyntheticExportEnvelopeRefused("EXPORT_ROW_LIMIT_EXCEEDED")
                if len(values) != len(headers):
                    raise SyntheticExportEnvelopeRefused("EXPORT_COLUMN_MISMATCH")
                if not all(_safe_cell(value) for value in values):
                    raise SyntheticExportEnvelopeRefused("UNSAFE_EXPORT_CELL")
        if count == 0:
            raise SyntheticExportEnvelopeRefused("EMPTY_EXPORT")
        after_stat = source.stat()
        after = (after_stat.st_dev, after_stat.st_ino,
                 after_stat.st_size, after_stat.st_mtime_ns)
        if (before != after or after_stat.st_size != original_size
                or _hash(source) != digest_before):
            raise SyntheticExportEnvelopeRefused("SOURCE_CHANGED_DURING_INSPECTION")
        header_bytes = "\x00".join(headers).encode("ascii")
        return SyntheticExportEnvelope(
            source_sha256=digest_before,
            source_size_bytes=original_size,
            syntax_profile_declared=syntax_profile,
            header_schema_sha256=hashlib.sha256(_DOMAIN + header_bytes).hexdigest(),
            column_count=len(headers),
            row_count=count,
        )
    except SyntheticExportEnvelopeRefused:
        raise
    except UnsafeSource as exc:
        raise SyntheticExportEnvelopeRefused(str(exc)) from None
    except (OSError, UnicodeError, csv.Error, ValueError):
        raise SyntheticExportEnvelopeRefused("INVALID_OR_CHANGED_EXPORT") from None
