"""LOT05.7B — offline SQLite COPY-ONLY assessment; NEVER a clinical importer.

This module deliberately has no target DB connection, clinical write method,
HTTP route, credential, SQL-dump executor or automatic mapping approval.
It inspects a *cold, attested, bounded copy* via the existing LOT05.1 inspector
and revalidates the exact LOT05.2 human-decision draft before reading ONLY
source identity/reference columns. It reports aggregate non-PHI evidence.
"""
from __future__ import annotations

from contextlib import closing
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Mapping

from .legacy_sql_inspector_v15 import (
    UnsafeSource, _copy_path, _hash, inspect_staged_copy,
)
from .legacy_sql_mapping_v15 import (
    MappingDraft, MappingRejected, TargetSnapshot, revalidate_mapping_draft,
)


class OfflinePlanRefused(ValueError):
    """Stable non-PHI error code; never include paths, SQL, identities or rows."""


@dataclass(frozen=True)
class ReferenceRule:
    """An explicitly reviewed legacy foreign-key relationship."""
    child_source_table: str
    reference_column: str
    parent_source_table: str


@dataclass(frozen=True)
class OfflinePlanReport:
    source_sha256: str
    mapping_profile_sha256: str
    plan_sha256: str
    counts_by_entity: dict[str, int]
    unmapped_tables: int
    unmapped_columns: int
    duplicate_legacy_ids: int
    missing_legacy_ids: int
    orphan_references: int
    reference_count: int
    anomalies: tuple[str, ...]
    warnings: tuple[str, ...]
    critical_count: int
    source_unchanged: bool = True
    source_only_copy: bool = True
    target_rows_written: int = 0
    target_schema_physically_certified: bool = False
    target_backup_verified: bool = False
    target_restore_verified: bool = False
    real_auth_verified: bool = False
    human_mapping_approved: bool = False
    clinical_records_reconciled: bool = False
    full_schema_certified: bool = False
    import_permitted: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


_MAX_SOURCE_ROWS = 100_000
_MAX_REFERENCES = 64
_MAX_MAPPED_TABLES = 24
_MAX_ID_LENGTH = 255
_DIALECT = "sqlite"


def _identifier(value: object, available: set[str]) -> str:
    if not isinstance(value, str) or value not in available:
        raise OfflinePlanRefused("EXPLICIT_SOURCE_IDENTIFIER_REQUIRED")
    return value


def _quoted(identifier: str) -> str:
    # Values originate solely from the inspected source inventory.
    return '"' + identifier.replace('"', '""') + '"'


def _legacy_key(value: object) -> str | None:
    if value is None or isinstance(value, (bytes, float, bool)):
        return None
    if not isinstance(value, (str, int)):
        return None
    normalized = str(value)
    if not normalized or len(normalized) > _MAX_ID_LENGTH:
        return None
    return normalized


def _get_keys(connection: sqlite3.Connection, table: str, column: str) -> tuple[set[str], int, int, int]:
    keys: set[str] = set()
    duplicates = missing = count = 0
    sql = "SELECT " + _quoted(column) + " FROM " + _quoted(table)
    try:
        cursor = connection.execute(sql)
        while True:
            batch = cursor.fetchmany(1000)
            if not batch:
                break
            count += len(batch)
            if count > _MAX_SOURCE_ROWS:
                raise OfflinePlanRefused("ROW_LIMIT_EXCEEDED")
            for (raw,) in batch:
                key = _legacy_key(raw)
                if key is None:
                    missing += 1
                elif key in keys:
                    duplicates += 1
                else:
                    keys.add(key)
        return keys, count, duplicates, missing
    except sqlite3.DatabaseError as exc:
        raise OfflinePlanRefused("COLD_SQLITE_SCAN_FAILED") from exc


def _count_orphans(
    connection: sqlite3.Connection, table: str, column: str, parent_ids: set[str],
) -> tuple[int, int]:
    total = orphans = 0
    try:
        cursor = connection.execute(
            "SELECT " + _quoted(column) + " FROM " + _quoted(table)
        )
        while True:
            batch = cursor.fetchmany(1000)
            if not batch:
                break
            total += len(batch)
            if total > _MAX_SOURCE_ROWS:
                raise OfflinePlanRefused("ROW_LIMIT_EXCEEDED")
            for (raw,) in batch:
                key = _legacy_key(raw)
                if key is None or key not in parent_ids:
                    orphans += 1
        return total, orphans
    except sqlite3.DatabaseError as exc:
        raise OfflinePlanRefused("COLD_SQLITE_REFERENCE_SCAN_FAILED") from exc


def assess_cold_sqlite_copy(
    source_path: Path,
    staging_root: Path,
    *,
    draft: MappingDraft,
    target_snapshot: TargetSnapshot,
    source_id_columns: Mapping[str, str],
    reference_rules: tuple[ReferenceRule, ...],
    attested_offline_copy: bool,
    dialect: str = _DIALECT,
) -> OfflinePlanReport:
    """Read identity and reference columns only; NEVER modify source or target.

    Operator assertion that a copy is offline is NOT cryptographic provenance.
    The report is never an admission ticket: even critical_count=0 remains
    NO-GO pending real backups, tenant/issuer authority, consent and review.
    """
    if dialect != _DIALECT:
        raise OfflinePlanRefused("NATIVE_ROW_ADAPTER_NOT_IMPLEMENTED")
    if attested_offline_copy is not True:
        raise OfflinePlanRefused("OFFLINE_COPY_ATTESTATION_REQUIRED")
    if not isinstance(draft, MappingDraft):
        raise OfflinePlanRefused("MAPPING_DRAFT_REQUIRED")
    if type(reference_rules) is not tuple or len(reference_rules) > _MAX_REFERENCES:
        raise OfflinePlanRefused("REFERENCE_RULES_INVALID")
    if not isinstance(source_id_columns, Mapping):
        raise OfflinePlanRefused("SOURCE_IDENTITIES_REQUIRED")

    try:
        inspection = inspect_staged_copy(
            source_path, staging_root,
            dialect=dialect, attested_offline_copy=True,
        )
        if inspection.source_format != "sqlite-copy":
            raise OfflinePlanRefused("NATIVE_ROW_ADAPTER_NOT_IMPLEMENTED")
        validation = revalidate_mapping_draft(draft, inspection, target_snapshot)
    except (UnsafeSource, MappingRejected) as exc:
        # Hide any sensitive file/path/source field details.
        raise OfflinePlanRefused(str(exc)) from exc
    if not validation.exact_source_and_target or validation.import_permitted:
        raise OfflinePlanRefused("SOURCE_OR_TARGET_DRAFT_CHANGED")

    inventory = {t.source_name: {c.name for c in t.columns} for t in inspection.tables}
    chosen = {d.source_table: d for d in draft.decisions if d.target_table is not None}
    if len(chosen) > _MAX_MAPPED_TABLES or not chosen:
        raise OfflinePlanRefused("MAPPED_TABLE_SCOPE_INVALID")
    if "patients" not in {d.target_table for d in chosen.values()}:
        raise OfflinePlanRefused("PATIENT_MAPPING_REQUIRED")
    if set(source_id_columns) != set(chosen):
        raise OfflinePlanRefused("EXPLICIT_ID_FOR_EVERY_MAPPED_TABLE_REQUIRED")
    if not all(isinstance(rule, ReferenceRule) for rule in reference_rules):
        raise OfflinePlanRefused("REFERENCE_RULES_INVALID")
    if len(reference_rules) != len(set(reference_rules)):
        raise OfflinePlanRefused("DUPLICATE_REFERENCE_RULE")
    for table, id_col in source_id_columns.items():
        _identifier(table, set(chosen))
        _identifier(id_col, inventory[table])
    for rule in reference_rules:
        _identifier(rule.child_source_table, set(chosen))
        _identifier(rule.parent_source_table, set(chosen))
        _identifier(rule.reference_column, inventory[rule.child_source_table])
        if rule.child_source_table == rule.parent_source_table:
            raise OfflinePlanRefused("SELF_REFERENCE_REQUIRES_SEPARATE_REVIEW")
    # Appointment-to-patient reference evidence is mandatory if appointments
    # are mapped. Never count appointments as reconciled without that link.
    patient_source = next(t for t, d in chosen.items() if d.target_table == "patients")
    for t, d in chosen.items():
        if d.target_table == "appointments" and not any(
            rule.child_source_table == t and rule.parent_source_table == patient_source
            for rule in reference_rules
        ):
            raise OfflinePlanRefused("PATIENT_APPOINTMENT_REFERENCE_REQUIRED")

    source, size = _copy_path(Path(source_path), Path(staging_root), True)
    stat = source.stat()
    identity = (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns)
    if size != inspection.file_size_bytes or _hash(source) != inspection.sha256:
        raise OfflinePlanRefused("SOURCE_CHANGED_AFTER_INSPECTION")
    counts: dict[str, int] = {}
    keys: dict[str, set[str]] = {}
    duplicate = missing = orphan = reference_count = 0
    try:
        with closing(sqlite3.connect(
            source.as_uri() + "?mode=ro&immutable=1",
            uri=True, timeout=1,
        )) as connection:
            connection.execute("PRAGMA query_only=ON")
            connection.execute("PRAGMA trusted_schema=OFF")
            for source_table, decision in sorted(chosen.items()):
                ids, count, dup, miss = _get_keys(
                    connection, source_table, source_id_columns[source_table]
                )
                keys[source_table] = ids
                counts[decision.target_table] = count
                duplicate += dup
                missing += miss
            for rule in reference_rules:
                count, bad = _count_orphans(
                    connection, rule.child_source_table,
                    rule.reference_column, keys[rule.parent_source_table],
                )
                reference_count += count
                orphan += bad
    except sqlite3.DatabaseError as exc:
        raise OfflinePlanRefused("COLD_SQLITE_READ_FAILED") from exc
    # Compare source bytes and inode after row scan: a changed file is
    # rejected, never presented as a reproducible evidence snapshot.
    after = source.stat()
    if ((after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) != identity
            or _hash(source) != inspection.sha256):
        raise OfflinePlanRefused("SOURCE_CHANGED_DURING_PLAN")

    unmapped_tables = sum(d.target_table is None for d in draft.decisions)
    unmapped_columns = sum(
        c.target_column is None for d in draft.decisions for c in d.columns
    )
    anomalies = []
    if duplicate:
        anomalies.append("DUPLICATE_LEGACY_ID")
    if missing:
        anomalies.append("MISSING_LEGACY_ID")
    if orphan:
        anomalies.append("ORPHAN_REFERENCE")
    if unmapped_tables or unmapped_columns:
        anomalies.append("UNMAPPED_REQUIRES_HUMAN_DISPOSITION")
    critical = int(bool(duplicate)) + int(bool(missing)) + int(bool(orphan)) + int(bool(unmapped_tables or unmapped_columns))
    warnings = (
        "NO_REAL_TARGET_SCHEMA_OR_TENANT_ATTESTATION",
        "NO_TARGET_WRITE_NO_BACKUP_NO_RESTORE",
        "NO_CLINICAL_MEDIA_OR_FINANCE_SEMANTIC_RECONCILIATION",
        "NO_HUMAN_APPROVAL_OR_REAL_IMPORT_AUTHORITY",
    )
    # Deterministic, low-detail digest: only the already-present inspection
    # digest, mapping draft digest and aggregate counts; never patient values.
    body = json.dumps(
        (inspection.sha256, draft.profile_sha256,
         sorted(counts.items()), duplicate, missing, orphan,
         unmapped_tables, unmapped_columns),
        separators=(",", ":"), ensure_ascii=True,
    )
    return OfflinePlanReport(
        source_sha256=inspection.sha256,
        mapping_profile_sha256=draft.profile_sha256,
        plan_sha256=hashlib.sha256(body.encode("ascii")).hexdigest(),
        counts_by_entity=counts,
        unmapped_tables=unmapped_tables,
        unmapped_columns=unmapped_columns,
        duplicate_legacy_ids=duplicate,
        missing_legacy_ids=missing,
        orphan_references=orphan,
        reference_count=reference_count,
        anomalies=tuple(anomalies),
        warnings=warnings,
        critical_count=critical,
    )
