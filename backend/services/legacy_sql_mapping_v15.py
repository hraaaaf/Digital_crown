"""V1.5-05.2-A metadata-only mapping drafts. No DB, auth or imports.

Proposals are never decisions. A structurally complete draft is never approved.
Input schemas must be supplied by a *future trusted adapter* before real use.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from typing import Any


class MappingRejected(ValueError):
    """Stable non-PHI code for refused mapping metadata."""


@dataclass(frozen=True)
class TargetTable:
    name: str
    columns: tuple[str, ...]


@dataclass(frozen=True)
class TargetSnapshot:
    schema_revision: str
    tables: tuple[TargetTable, ...]


@dataclass(frozen=True)
class ColumnSuggestion:
    source_column: str
    suggested_target_column: str | None


@dataclass(frozen=True)
class TableSuggestion:
    source_table: str
    suggested_target_table: str | None
    columns: tuple[ColumnSuggestion, ...]


@dataclass(frozen=True)
class MappingProposal:
    source_file_sha256: str
    source_schema_sha256: str
    target_schema_sha256: str
    tables: tuple[TableSuggestion, ...]
    mapping_approved: bool = False
    import_permitted: bool = False


@dataclass(frozen=True)
class ColumnDecision:
    source_column: str
    target_column: str | None  # Explicit None = UNMAPPED


@dataclass(frozen=True)
class TableDecision:
    source_table: str
    target_table: str | None  # Explicit None = UNMAPPED
    columns: tuple[ColumnDecision, ...]


@dataclass(frozen=True)
class MappingDraft:
    profile_version: int
    source_software: str
    source_version: str | None
    source_file_sha256: str
    source_schema_sha256: str
    target_schema_sha256: str
    target_schema_revision: str
    decisions: tuple[TableDecision, ...]
    profile_sha256: str
    admin_approved: bool = False
    dry_run_completed: bool = False
    import_permitted: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Revalidation:
    exact_source_and_target: bool
    mismatches: tuple[str, ...]
    requires_human_review: bool = True
    admin_approved: bool = False
    import_permitted: bool = False


_SHA256 = re.compile(r"^[a-f0-9]{64}$")
# Credential-derived legacy values must not become live authentication material.
_SECRET_FRAGMENTS = (
    "password", "passwd", "pwd", "secret", "token", "credential",
    "apikey", "api_key", "privatekey", "private_key", "hashed",
    "salt", "oauth", "session_key", "otp", "authentication",
)


def _name(value: Any) -> str:
    if not isinstance(value, str) or not value or len(value) > 255:
        raise MappingRejected("INVALID_IDENTIFIER")
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in value):
        raise MappingRejected("INVALID_IDENTIFIER")
    return value


def _label(value: Any, *, allow_none: bool = False) -> str | None:
    if value is None and allow_none:
        return None
    if not isinstance(value, str) or not value or len(value) > 128:
        raise MappingRejected("INVALID_PROFILE_LABEL")
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in value):
        raise MappingRejected("INVALID_PROFILE_LABEL")
    return value


def _digest(payload: Any) -> str:
    # Metadata and explicit mapping names ONLY; never source rows or SQL DEFAULT.
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _unique(items: tuple[str, ...]) -> dict[str, str]:
    found: dict[str, str] = {}
    for item in items:
        value = _name(item)
        key = value.casefold()
        if key in found:
            raise MappingRejected("DUPLICATE_OR_AMBIGUOUS_IDENTIFIER")
        found[key] = value
    return found


def _source(source: Any) -> tuple[tuple[tuple[str, tuple[tuple[str, str], ...]], ...], str]:
    checksum = getattr(source, "sha256", None)
    if not isinstance(checksum, str) or not _SHA256.fullmatch(checksum):
        raise MappingRejected("INVALID_SOURCE_SHA256")
    if getattr(source, "import_permitted", False) is not False:
        raise MappingRejected("SOURCE_INSPECTION_MUST_NOT_APPROVE_IMPORT")
    try:
        tables = tuple(source.tables)
        normalized = []
        for table in tables:
            columns = tuple((_name(c.name), _name(c.declared_type)) for c in table.columns)
            _unique(tuple(name for name, _ in columns))
            normalized.append((_name(table.source_name), columns))
    except (AttributeError, TypeError, ValueError) as exc:
        if isinstance(exc, MappingRejected):
            raise
        raise MappingRejected("INVALID_SOURCE_SCHEMA") from exc
    if not normalized:
        raise MappingRejected("EMPTY_SOURCE_SCHEMA")
    _unique(tuple(name for name, _ in normalized))
    return tuple(normalized), checksum


def _target(snapshot: TargetSnapshot) -> tuple[tuple[tuple[str, tuple[str, ...]], ...], str]:
    if not isinstance(snapshot, TargetSnapshot):
        raise MappingRejected("TARGET_SNAPSHOT_REQUIRED")
    revision = _label(snapshot.schema_revision)
    try:
        tables = tuple((_name(t.name), tuple(_name(c) for c in t.columns)) for t in snapshot.tables)
    except (AttributeError, TypeError) as exc:
        raise MappingRejected("INVALID_TARGET_SCHEMA") from exc
    if not tables:
        raise MappingRejected("EMPTY_TARGET_SCHEMA")
    _unique(tuple(name for name, _ in tables))
    for _, columns in tables:
        if not columns:
            raise MappingRejected("EMPTY_TARGET_TABLE")
        _unique(columns)
    return tables, revision


def _metadata(source: Any, snapshot: TargetSnapshot) -> tuple:
    src, file_sha = _source(source)
    dst, revision = _target(snapshot)
    return src, file_sha, _digest(src), dst, revision, _digest((revision, dst))


def _is_secret(name: str) -> bool:
    lowered = name.casefold().replace("-", "_").replace(" ", "_")
    return any(fragment in lowered for fragment in _SECRET_FRAGMENTS)


def propose_mapping(source: Any, snapshot: TargetSnapshot) -> MappingProposal:
    """Exact-name suggestions only. No approval, no automatic binding."""
    src, file_sha, src_sha, dst, _, dst_sha = _metadata(source, snapshot)
    target_by_name = {name.casefold(): (name, columns) for name, columns in dst}
    suggestions = []
    for table, columns in src:
        match = target_by_name.get(table.casefold())
        if match and not _is_secret(table):
            destination, target_columns = match
            by_column = {name.casefold(): name for name in target_columns}
        else:
            destination, by_column = None, {}
        suggestions.append(TableSuggestion(
            table,
            destination,
            tuple(ColumnSuggestion(
                column,
                by_column.get(column.casefold())
                if not _is_secret(column) and not _is_secret(by_column.get(column.casefold(), ""))
                else None,
            ) for column, _ in columns),
        ))
    return MappingProposal(file_sha, src_sha, dst_sha, tuple(suggestions))


def _payload(
    *, profile_version: int, source_software: str, source_version: str | None,
    file_sha: str, source_sha: str, target_sha: str, target_revision: str,
    decisions: tuple[TableDecision, ...],
) -> dict[str, Any]:
    return {
        "profile_version": profile_version, "source_software": source_software,
        "source_version": source_version, "source_file_sha256": file_sha,
        "source_schema_sha256": source_sha, "target_schema_sha256": target_sha,
        "target_schema_revision": target_revision, "decisions": [asdict(d) for d in decisions],
    }


def build_mapping_draft(
    source: Any,
    target: TargetSnapshot,
    decisions: tuple[TableDecision, ...],
    *, source_software: str, source_version: str | None, profile_version: int,
) -> MappingDraft:
    """Validate *human decisions* structurally; this is NOT proof of human identity."""
    src, file_sha, src_sha, dst, revision, dst_sha = _metadata(source, target)
    if type(profile_version) is not int or profile_version < 1:
        raise MappingRejected("INVALID_PROFILE_VERSION")
    source_software = _label(source_software)
    source_version = _label(source_version, allow_none=True)
    if not isinstance(decisions, tuple):
        raise MappingRejected("DECISIONS_MUST_BE_EXPLICIT")
    source_table_columns = {name: tuple(c for c, _ in cols) for name, cols in src}
    target_table_columns = dict(dst)
    seen_source: set[str] = set()
    seen_destinations: set[str] = set()
    normalized: list[TableDecision] = []
    for choice in decisions:
        if not isinstance(choice, TableDecision) or choice.source_table not in source_table_columns:
            raise MappingRejected("UNKNOWN_SOURCE_TABLE")
        if choice.source_table in seen_source:
            raise MappingRejected("DUPLICATE_SOURCE_TABLE_DECISION")
        seen_source.add(choice.source_table)
        if choice.target_table is not None:
            if choice.target_table not in target_table_columns:
                raise MappingRejected("UNKNOWN_TARGET_TABLE")
            if _is_secret(choice.source_table) or _is_secret(choice.target_table):
                raise MappingRejected("CREDENTIAL_MAPPING_FORBIDDEN")
            if choice.target_table in seen_destinations:
                raise MappingRejected("TARGET_TABLE_COLLISION")
            seen_destinations.add(choice.target_table)
        seen_columns: set[str] = set()
        seen_targets: set[str] = set()
        normalized_columns: list[ColumnDecision] = []
        if not isinstance(choice.columns, tuple):
            raise MappingRejected("DECISIONS_MUST_BE_EXPLICIT")
        for column in choice.columns:
            if not isinstance(column, ColumnDecision) or column.source_column not in source_table_columns[choice.source_table]:
                raise MappingRejected("UNKNOWN_SOURCE_COLUMN")
            if column.source_column in seen_columns:
                raise MappingRejected("DUPLICATE_SOURCE_COLUMN_DECISION")
            seen_columns.add(column.source_column)
            dest = column.target_column
            if dest is not None:
                if choice.target_table is None:
                    raise MappingRejected("ORPHAN_COLUMN_MAPPING")
                if dest not in target_table_columns[choice.target_table]:
                    raise MappingRejected("UNKNOWN_TARGET_COLUMN")
                if _is_secret(column.source_column) or _is_secret(dest):
                    raise MappingRejected("CREDENTIAL_MAPPING_FORBIDDEN")
                if dest in seen_targets:
                    raise MappingRejected("TARGET_COLUMN_COLLISION")
                seen_targets.add(dest)
            normalized_columns.append(column)
        if set(source_table_columns[choice.source_table]) != seen_columns:
            raise MappingRejected("COLUMN_REVIEW_INCOMPLETE")
        normalized.append(TableDecision(
            choice.source_table, choice.target_table,
            tuple(sorted(normalized_columns, key=lambda c: c.source_column)),
        ))
    if set(source_table_columns) != seen_source:
        raise MappingRejected("TABLE_REVIEW_INCOMPLETE")
    ordered = tuple(sorted(normalized, key=lambda t: t.source_table))
    payload = _payload(
        profile_version=profile_version, source_software=source_software,
        source_version=source_version, file_sha=file_sha, source_sha=src_sha,
        target_sha=dst_sha, target_revision=revision, decisions=ordered,
    )
    return MappingDraft(profile_version, source_software, source_version,
                        file_sha, src_sha, dst_sha, revision, ordered, _digest(payload))


def revalidate_mapping_draft(draft: MappingDraft, source: Any, target: TargetSnapshot) -> Revalidation:
    """A match only means same fingerprints, never automatic profile approval."""
    if not isinstance(draft, MappingDraft):
        raise MappingRejected("MAPPING_DRAFT_REQUIRED")
    # An offline draft cannot become an authorization by flipping flags.
    if draft.admin_approved or draft.import_permitted or draft.dry_run_completed:
        raise MappingRejected("DRAFT_CANNOT_AUTHORIZE")
    src, file_sha, src_sha, dst, revision, dst_sha = _metadata(source, target)
    payload = _payload(profile_version=draft.profile_version,
                       source_software=draft.source_software, source_version=draft.source_version,
                       file_sha=draft.source_file_sha256, source_sha=draft.source_schema_sha256,
                       target_sha=draft.target_schema_sha256, target_revision=draft.target_schema_revision,
                       decisions=draft.decisions)
    if _digest(payload) != draft.profile_sha256:
        raise MappingRejected("DRAFT_TAMPERED")
    mismatches = []
    if file_sha != draft.source_file_sha256:
        mismatches.append("SOURCE_DUMP_CHANGED")
    if src_sha != draft.source_schema_sha256:
        mismatches.append("SOURCE_SCHEMA_CHANGED")
    if dst_sha != draft.target_schema_sha256 or revision != draft.target_schema_revision:
        mismatches.append("TARGET_SCHEMA_CHANGED")
    return Revalidation(not mismatches, tuple(mismatches))
