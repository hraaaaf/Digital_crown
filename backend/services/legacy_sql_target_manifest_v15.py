"""V1.5-05.2-B2a: build a NON-AUTHORITATIVE target mapping manifest from ORM declarations.

Reads SQLAlchemy MetaData only. Never imports backend.database, makes a DB
connection, reflects a live database or claims a physical Alembic version.
Not an API; callers must still authenticate staff and verify the physical
schema/tenant before any draft can become eligible for a real dry-run.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Iterable

from sqlalchemy import MetaData

from backend.services.legacy_sql_mapping_v15 import TargetSnapshot, TargetTable
from backend.core.schema_runtime import CURRENT_ALEMBIC_HEAD


class TargetManifestRefused(ValueError):
    """Generic metadata-only rejection code; no source values in errors."""


@dataclass(frozen=True)
class DeclaredTargetManifest:
    """Deliberately untrusted preview, never an authorization record."""

    declared_revision: str
    schema_fingerprint: str
    tables: tuple[TargetTable, ...]
    filtered_column_count: int
    provenance: str = "SQLALCHEMY_DECLARED_METADATA_ONLY"
    physical_schema_verified: bool = False
    tenant_verified: bool = False
    admin_approved: bool = False
    dry_run_completed: bool = False
    import_permitted: bool = False

    def as_mapping_target(self) -> TargetSnapshot:
        return TargetSnapshot(
            schema_revision="orm-declared:" + self.declared_revision,
            tables=self.tables,
        )

    def as_ui_json(self) -> dict[str, Any]:
        """Only the two keys accepted by the *untrusted* B1 JSON parser.

        This payload MUST NOT be served as a certified physical DB snapshot.
        """
        return {
            "schema_revision": "orm-declared:" + self.declared_revision,
            "tables": [
                {
                    "name": table.name,
                    "columns": [{"name": column} for column in table.columns],
                }
                for table in self.tables
            ],
        }


_REVISION = re.compile(r"^[a-z0-9][a-z0-9_-]{1,63}$")
_MAX_TABLES = 512
_MAX_COLUMNS_PER_TABLE = 512
_MAX_BYTES = 1024 * 1024

# Conservative hard deny list. Not a substitute for an explicit field-level
# authorization policy when importing real practitioner / clinical records.
# Privilege flags must NEVER be automatically mapped from an untrusted source.
_RESTRICTED_FRAGMENTS = (
    "password", "passwd", "passphrase", "secret", "credential",
    "token", "privatekey", "apikey", "hash", "salt", "oauth",
    "session", "authentication", "authorization", "superadmin",
    "permission", "privilege", "userrole", "accessrole", "isadmin",
    "islicensed", "approvalstatus", "refresh", "recoverycode",
    "mfacode", "totp", "otpsecret", "securityquestion",
    "devicepair", "nonce", "challenge", "revokedtoken",
    "userrole", "role", "isactive", "issuspended", "isarchived",
)
_RESTRICTED_TABLES = {
    "alembic_version", "users", "revoked_tokens", "auth_sessions",
    "user_sessions", "api_tokens", "oauth_tokens", "refresh_tokens",
}


def _identifier(value: Any) -> str:
    if not isinstance(value, str) or not value or len(value) > 255:
        raise TargetManifestRefused("INVALID_METADATA_IDENTIFIER")
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in value):
        raise TargetManifestRefused("INVALID_METADATA_IDENTIFIER")
    return value


def _restricted(value: str) -> bool:
    normalized = "".join(ch for ch in value.casefold() if ch.isalnum())
    return any(fragment in normalized for fragment in _RESTRICTED_FRAGMENTS)


def _unique_casefold(names: Iterable[str]) -> None:
    normalized = [_identifier(name).casefold() for name in names]
    if len(set(normalized)) != len(normalized):
        raise TargetManifestRefused("AMBIGUOUS_METADATA_IDENTIFIER")


def _table_name(table: Any) -> str:
    name = _identifier(table.name)
    schema = getattr(table, "schema", None)
    if schema:
        return _identifier(schema) + "." + name
    return name


def build_declared_target_manifest(
    metadata: MetaData,
    *,
    requested_tables: tuple[str, ...],
    declared_revision: str,
) -> DeclaredTargetManifest:
    """Extract a bounded, explicitly requested ORM subset without touching a DB.

    'requested_tables' must be a reviewed *business scope*, not a tenant ID.
    Raises when the scope is absent/ambiguous or cannot be fully represented.
    """
    if not isinstance(metadata, MetaData):
        raise TargetManifestRefused("DECLARATIVE_METADATA_REQUIRED")
    if not isinstance(declared_revision, str) or not _REVISION.fullmatch(declared_revision):
        raise TargetManifestRefused("INVALID_DECLARED_REVISION")
    if declared_revision != CURRENT_ALEMBIC_HEAD:
        raise TargetManifestRefused("DECLARED_ALEMBIC_REVISION_MISMATCH")
    if (not isinstance(requested_tables, tuple)
            or not 0 < len(requested_tables) <= _MAX_TABLES):
        raise TargetManifestRefused("EXPLICIT_TABLE_SCOPE_REQUIRED")
    _unique_casefold(requested_tables)
    if any(name.rsplit(".", 1)[-1].casefold() in _RESTRICTED_TABLES
           or _restricted(name) for name in requested_tables):
        raise TargetManifestRefused("SENSITIVE_TARGET_TABLE_FORBIDDEN")

    declared_tables = tuple(metadata.tables.values())
    if not declared_tables:
        raise TargetManifestRefused("EMPTY_ORM_METADATA")
    # Explicit schema-qualified names prevent 'public.patients' from silently
    # collapsing onto a same-name table of another schema.
    all_names = [_table_name(table) for table in declared_tables]
    _unique_casefold(all_names)
    lookup = dict(zip(all_names, declared_tables))
    if any(name not in lookup for name in requested_tables):
        raise TargetManifestRefused("REQUESTED_TARGET_TABLE_MISSING")

    preview_tables: list[TargetTable] = []
    excluded_columns = 0
    for name in sorted(requested_tables):
        table = lookup[name]
        raw_columns = tuple(_identifier(col.name) for col in table.columns)
        if not 0 < len(raw_columns) <= _MAX_COLUMNS_PER_TABLE:
            raise TargetManifestRefused("TARGET_COLUMN_COUNT_UNSUPPORTED")
        _unique_casefold(raw_columns)
        allowed = []
        for col in raw_columns:
            if _restricted(col):
                excluded_columns += 1
            else:
                allowed.append(col)
        if not allowed:
            # Never silently omit an entire table because all columns are secrets.
            raise TargetManifestRefused("NO_SAFE_COLUMNS_IN_TARGET_TABLE")
        preview_tables.append(TargetTable(name, tuple(sorted(allowed))))

    tables = tuple(preview_tables)
    metadata_digest = {
        "provenance": "SQLALCHEMY_DECLARED_METADATA_ONLY",
        "revision": declared_revision,
        "tables": [{"name": t.name, "columns": list(t.columns)} for t in tables],
        "filtered_column_count": excluded_columns,
    }
    rendered = json.dumps(metadata_digest, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ui_report = {
        "schema_revision": "orm-declared:" + declared_revision,
        "tables": [{"name": t.name, "columns": [{"name": c} for c in t.columns]} for t in tables],
    }
    if len(json.dumps(ui_report, ensure_ascii=False).encode("utf-8")) > _MAX_BYTES:
        raise TargetManifestRefused("UI_MANIFEST_TOO_LARGE")

    return DeclaredTargetManifest(
        declared_revision=declared_revision,
        schema_fingerprint=hashlib.sha256(rendered).hexdigest(),
        tables=tables,
        filtered_column_count=excluded_columns,
    )
