"""LOT05.7C-A: vendor-neutral source inventory over attested OFFLINE copies.

No vendor data-row adapter, no target DB handle, no API, no credentials, no
clinical import. This narrow gate reuses the existing 05.1 schema-only
inspector and exports only non-PHI aggregate metadata. Vendor name/version
are OPERATOR DECLARATIONS, not verified software identity.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

# Package use is unchanged. Standalone direct-script use is LAB/CLI only.
if __package__:
    from .legacy_sql_inspector_v15 import UnsafeSource, inspect_staged_copy
else:
    from legacy_sql_inspector_v15 import UnsafeSource, inspect_staged_copy


class VendorInventoryRefused(ValueError):
    """Stable refusal code only; never format a path, source value or SQL."""


@dataclass(frozen=True)
class ReadOnlySourceSummary:
    """Safe-to-display aggregates; raw table and column names stay local."""

    source_sha256: str
    file_size_bytes: int
    dialect_declared: str
    source_format: str
    table_count: int
    column_count: int
    warnings: tuple[str, ...] = (
        "SOURCE_VENDOR_DECLARATION_NOT_VERIFIED",
        "SOURCE_SCHEMA_ONLY_NO_SEMANTIC_MAPPING",
    )
    source_vendor_verified: bool = False
    vendor_adapter_implemented: bool = False
    human_mapping_approved: bool = False
    target_backup_verified: bool = False
    target_rows_written: int = 0
    full_schema_certified: bool = False
    import_permitted: bool = False

    def to_public_dict(self) -> dict:
        """No file paths, SQL, schema identifiers, rows or vendor labels."""
        return asdict(self)


_ALLOWED_DIALECTS = frozenset(("sqlite", "postgresql", "mysql", "mariadb"))
_SQLITE_EXTENSIONS = frozenset((".sqlite", ".sqlite3", ".db"))
_EXPORT_FORMATS = frozenset(("sqlite-copy", "sql-text-ddl"))


def _operator_label(value: object, error_code: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 80:
        raise VendorInventoryRefused(error_code)
    if value.strip() != value or any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise VendorInventoryRefused(error_code)
    return value


def inventory_declared_legacy_copy(
    source_path: Path,
    staging_root: Path,
    *,
    source_software: str,
    source_version: str,
    dialect: str,
    export_format: str,
    attested_offline_copy: bool = False,
) -> ReadOnlySourceSummary:
    """Inventory strictly a cold, operator-attested copy; never authenticate a vendor.

    The current source vendor and version must be explicitly declared by the
    operator. Declaring them does NOT select or certify a vendor-specific
    parser; supported formats are limited to what 05.1 can inspect.
    """
    _operator_label(source_software, "SOURCE_SOFTWARE_REQUIRED")
    _operator_label(source_version, "SOURCE_VERSION_REQUIRED")
    if attested_offline_copy is not True:
        raise VendorInventoryRefused("OFFLINE_COPY_ATTESTATION_REQUIRED")
    if not isinstance(dialect, str) or dialect not in _ALLOWED_DIALECTS:
        raise VendorInventoryRefused("DIALECT_UNSUPPORTED")
    if not isinstance(export_format, str) or export_format not in _EXPORT_FORMATS:
        raise VendorInventoryRefused("EXPORT_FORMAT_UNSUPPORTED")
    if not isinstance(source_path, Path) or not isinstance(staging_root, Path):
        raise VendorInventoryRefused("OFFLINE_PATH_REQUIRED")

    suffix = source_path.suffix.lower()
    if export_format == "sqlite-copy":
        if dialect != "sqlite":
            raise VendorInventoryRefused("SQLITE_REQUIRES_SQLITE_DIALECT")
        if suffix not in _SQLITE_EXTENSIONS:
            raise VendorInventoryRefused("EXPORT_FORMAT_MISMATCH")
    elif suffix != ".sql":
        raise VendorInventoryRefused("EXPORT_FORMAT_MISMATCH")

    try:
        # 05.1 handles symlinks/hardlinks, staging containment, byte limit,
        # checksum before+after, SQLite cold/WAL gate and non-executing DDL.
        report = inspect_staged_copy(
            source_path, staging_root,
            dialect=dialect,
            attested_offline_copy=True,
            encoding="utf-8",
        )
    except UnsafeSource as exc:
        # 05.1 exceptions contain only stable non-PHI codes by contract.
        raise VendorInventoryRefused(str(exc)) from None

    if report.source_format != export_format:
        raise VendorInventoryRefused("EXPORT_FORMAT_MISMATCH")
    if export_format == "sql-text-ddl" and "OTHER_SQL_NOT_PARSED" in report.warnings:
        # 05.1 may inventory DDL alongside INSERT/COPY; 05.7C-A deliberately
        # refuses any other statement rather than interpreting a data dump.
        raise VendorInventoryRefused("NON_DDL_SQL_FORBIDDEN")

    return ReadOnlySourceSummary(
        source_sha256=report.sha256,
        file_size_bytes=report.file_size_bytes,
        dialect_declared=report.dialect_declared,
        source_format=report.source_format,
        table_count=len(report.tables),
        column_count=sum(len(table.columns) for table in report.tables),
    )



def _main(argv: list[str] | None = None) -> int:
    """Offline non-PHI source inventory CLI; no clinical application imports.

    The two lab/attestation switches are explicit operator declarations, NOT
    technical proof that a file belongs to a vendor or is actually synthetic.
    A success never authorizes a target migration or record-level parsing.
    """
    import argparse
    import json

    class _SafeParser(argparse.ArgumentParser):
        def error(self, message: str) -> None:
            # argparse's default error text can contain a sensitive path/value.
            raise VendorInventoryRefused("INVALID_CLI_ARGUMENTS")

    parser = _SafeParser(
        description="LAB metadata-only offline source inventory; NO PATIENT IMPORT"
    )
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--staging-root", type=Path, required=True)
    parser.add_argument("--source-software", required=True)
    parser.add_argument("--source-version", required=True)
    parser.add_argument("--dialect", required=True)
    parser.add_argument("--export-format", required=True)
    parser.add_argument("--attest-offline-copy", action="store_true")
    parser.add_argument("--lab-synthetic-fixture", action="store_true")

    try:
        args = parser.parse_args(argv)
        if args.lab_synthetic_fixture is not True:
            raise VendorInventoryRefused("LAB_SYNTHETIC_ONLY")
        if args.attest_offline_copy is not True:
            raise VendorInventoryRefused("OFFLINE_COPY_ATTESTATION_REQUIRED")
        result = inventory_declared_legacy_copy(
            args.source, args.staging_root,
            source_software=args.source_software,
            source_version=args.source_version,
            dialect=args.dialect,
            export_format=args.export_format,
            attested_offline_copy=True,
        )
    except VendorInventoryRefused as exc:
        print("REFUSED: " + str(exc))
        return 2
    except (OSError, UnicodeError, ValueError):
        # Stable refusal; no traceback, paths, SQL, schema or patient values.
        print("REFUSED: LAB_INSPECTION_FAILED")
        return 2

    print(json.dumps({
        "lab_synthetic_operator_attestation_not_verified": True,
        "source_summary": result.to_public_dict(),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
