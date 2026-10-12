"""V1.5-05.1: inspect explicitly staged OFFLINE SQL copies, never import data.

The .sql adapter only inventories common CREATE TABLE DDL; it never executes SQL.
A successful inventory is NOT a migration dry-run, mapping or import approval.
"""
from __future__ import annotations

import hashlib
import re
import sqlite3
from contextlib import closing
from dataclasses import asdict, dataclass
from pathlib import Path



class UnsafeSource(ValueError):
    """Non-PHI error code for refused inputs."""


@dataclass(frozen=True)
class ColumnInventory:
    name: str
    declared_type: str
    not_null: bool | None = None
    primary_key: bool | None = None


@dataclass(frozen=True)
class TableInventory:
    source_name: str
    columns: tuple[ColumnInventory, ...]


@dataclass(frozen=True)
class InspectionReport:
    dialect_declared: str
    source_format: str
    sha256: str
    file_size_bytes: int
    tables: tuple[TableInventory, ...]
    warnings: tuple[str, ...]
    row_counts: None = None
    mapping_approved: bool = False
    dry_run_completed: bool = False
    import_permitted: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


_DIALECTS = {"postgresql", "mysql", "mariadb", "sqlite"}
_ENCODINGS = {"utf-8", "utf-8-sig", "latin-1", "cp1252"}
_MAX_BYTES = 32 * 1024 * 1024
_MAX_TABLES = 512
_MAX_COLUMNS = 512
_SQLITE_EXT = {".db", ".sqlite", ".sqlite3"}
_IDENT = r'(?:"(?:[^"]|"")*"|__BACKTICK__(?:[^__BACKTICK__]|__BACKTICK____BACKTICK__)*__BACKTICK__|[A-Za-z_][\w$]*)'
_IDENT = _IDENT.replace("__BACKTICK__", chr(96))
_CREATE = re.compile(r"^CREATE\s+(?:TEMPORARY\s+|UNLOGGED\s+)?TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?", re.I)
_NAME = re.compile(rf"^({_IDENT})(?:\s*\.\s*({_IDENT}))?")
_COL = re.compile(rf"^({_IDENT})\s+(.+)$", re.S)
_CONSTRAINT = re.compile(r"^(?:CONSTRAINT\s+\S+\s+)?(?:PRIMARY\s+KEY|FOREIGN\s+KEY|UNIQUE|CHECK|KEY|INDEX|EXCLUDE)\b", re.I)


# Only a bounded, non-sensitive type token is exported. Full DDL may include
# patient-identifying DEFAULT strings and MUST NOT leave the offline staging area.
# Unknown/vendor types are refused until an explicit dialect adapter is built.
_TYPE = re.compile(
    r"^(?:DOUBLE\s+PRECISION|TIMESTAMP(?:\s+WITH(?:OUT)?\s+TIME\s+ZONE)?|"
    r"CHARACTER(?:\s+VARYING)?|VARCHAR|CHAR|DECIMAL|NUMERIC|"
    r"SMALLINT|BIGINT|INTEGER|INT|TINYINT|MEDIUMINT|SERIAL|BIGSERIAL|"
    r"BOOLEAN|BOOL|TEXT|TINYTEXT|MEDIUMTEXT|LONGTEXT|"
    r"REAL|FLOAT|DATE|DATETIME|TIMESTAMPTZ|BLOB|BYTEA|UUID|"
    r"JSONB|JSON|VARBINARY|BINARY)"
    r"\b(?:\s*\(\s*\d{1,5}(?:\s*,\s*\d{1,5})?\s*\))?",
    re.I,
)


def _copy_path(path: Path, root: Path, attested_offline_copy: bool) -> tuple[Path, int]:
    if attested_offline_copy is not True:
        raise UnsafeSource("OFFLINE_COPY_ATTESTATION_REQUIRED")
    # Reject symlinks in every provided path component, not only the final file.
    for component in (root, *root.parents, path, *path.parents):
        if component.is_symlink():
            raise UnsafeSource("SYMLINK_FORBIDDEN")
    try:
        base, resolved = root.resolve(strict=True), path.resolve(strict=True)
    except OSError as exc:
        raise UnsafeSource("STAGED_FILE_UNAVAILABLE") from exc
    if resolved == base or base not in resolved.parents or not resolved.is_file():
        raise UnsafeSource("OUTSIDE_STAGING_ROOT")
    # An intermediate symlink is unsafe, even when it happens to resolve inside staging.
    relative = resolved.relative_to(base)
    cursor = base
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise UnsafeSource("SYMLINK_FORBIDDEN")
    metadata = resolved.stat()
    # A hardlink inside staging can alias an original living outside staging.
    if metadata.st_nlink != 1:
        raise UnsafeSource("HARDLINK_SOURCE_FORBIDDEN")
    size = metadata.st_size
    if not 0 < size <= _MAX_BYTES:
        raise UnsafeSource("INPUT_SIZE_UNSUPPORTED")
    return resolved, size


def _hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sqlite(path: Path) -> tuple[TableInventory, ...]:
    try:
        with closing(sqlite3.connect(path.as_uri() + "?mode=ro&immutable=1", uri=True, timeout=1)) as connection:
            connection.execute("PRAGMA query_only=ON")
            connection.execute("PRAGMA trusted_schema=OFF")
            names = connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            ).fetchall()
            if len(names) > _MAX_TABLES:
                raise UnsafeSource("TOO_MANY_TABLES")
            tables = []
            for (name,) in names:
                # Quote every identifier obtained from sqlite_master, never interpolate input SQL.
                quoted = '"' + name.replace('"', '""') + '"'
                columns = connection.execute("PRAGMA table_xinfo(" + quoted + ")").fetchall()
                if len(columns) > _MAX_COLUMNS:
                    raise UnsafeSource("TOO_MANY_COLUMNS")
                tables.append(TableInventory(name, tuple(
                    ColumnInventory(str(c[1]), str(c[2]), bool(c[3]), bool(c[5]))
                    for c in columns
                )))
            return tuple(tables)
    except sqlite3.DatabaseError as exc:
        raise UnsafeSource("INVALID_SQLITE_COPY") from exc


def _unquote(s: str) -> str:
    if s.startswith('"'):
        return s[1:-1].replace('""', '"')
    if s.startswith(chr(96)):
        return s[1:-1].replace(chr(96) * 2, chr(96))
    return s


def _split(text: str, delimiter: str) -> list[str]:
    """Non-executing lexical separator honoring quotes/comments/nested parentheses."""
    output, current = [], []
    depth = 0
    quote = None
    mode = "plain"
    i = 0
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if mode == "line":
            if ch == "\n":
                mode = "plain"
                current.append(" ")
            i += 1
            continue
        if mode == "block":
            if ch == "*" and nxt == "/":
                mode = "plain"
                i += 2
            else:
                i += 1
            continue
        if quote:
            current.append(ch)
            if ch == quote:
                if nxt == ch:
                    current.append(nxt)
                    i += 2
                    continue
                quote = None
            elif quote == "'" and ch == "\\" and nxt:
                current.append(nxt)
                i += 2
                continue
            i += 1
            continue
        if ch == "-" and nxt == "-" and (i + 2 == len(text) or text[i + 2].isspace()):
            mode = "line"
            i += 2
            continue
        if ch == "/" and nxt == "*":
            mode = "block"
            i += 2
            continue
        if ch == "#" and delimiter == ";":
            mode = "line"
            i += 1
            continue
        if ch in ("'", '"', chr(96)):
            quote = ch
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth < 0:
                raise UnsafeSource("AMBIGUOUS_PARENS")
        elif ch == delimiter and depth == 0:
            piece = "".join(current).strip()
            if piece:
                output.append(piece)
            current = []
            i += 1
            continue
        current.append(ch)
        i += 1
    if quote or mode == "block" or depth != 0:
        raise UnsafeSource("AMBIGUOUS_SQL_LEXING")
    tail = "".join(current).strip()
    if tail:
        output.append(tail)
    return output


def _table_body(ddl: str) -> tuple[str, str]:
    name = _NAME.match(ddl)
    if not name:
        raise UnsafeSource("UNSUPPORTED_TABLE_IDENTIFIER")
    table = ".".join(_unquote(p) for p in name.groups() if p is not None)
    remainder = ddl[name.end():].lstrip()
    if not remainder.startswith("("):
        raise UnsafeSource("UNSUPPORTED_TABLE_DDL")
    # Obtain balanced body without treating delimiters inside nested type args as columns.
    # A malformed or complex quoted expression is refused, not guessed.
    depth, quote = 0, None
    for idx, ch in enumerate(remainder):
        if quote:
            if ch == quote and (idx == 0 or remainder[idx - 1] != "\\"):
                quote = None
        elif ch in ("'", '"', chr(96)):
            quote = ch
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                if remainder[idx + 1:].strip():
                    raise UnsafeSource("UNSUPPORTED_TABLE_OPTIONS")
                return table, remainder[1:idx]
    raise UnsafeSource("UNSUPPORTED_TABLE_DDL")


def _sql(text: str) -> tuple[tuple[TableInventory, ...], tuple[str, ...]]:
    tables: list[TableInventory] = []
    used: set[str] = set()
    unrelated = False
    for statement in _split(text, ";"):
        create = _CREATE.match(statement)
        if not create:
            if re.search(r"\bCREATE\s+(?:TEMPORARY\s+|UNLOGGED\s+)?TABLE\b", statement, re.I):
                raise UnsafeSource("UNSUPPORTED_CREATE_TABLE")
            unrelated = True
            continue
        table, body = _table_body(statement[create.end():].lstrip())
        columns: list[ColumnInventory] = []
        for item in _split(body, ","):
            if _CONSTRAINT.match(item):
                continue
            col = _COL.match(item)
            if not col:
                raise UnsafeSource("UNSUPPORTED_COLUMN")
            declaration = col.group(2).strip()
            type_match = _TYPE.match(declaration)
            if type_match is None:
                raise UnsafeSource("UNSUPPORTED_COLUMN_TYPE")
            suffix = declaration[type_match.end():]
            if re.match(r"^\s+UNSIGNED\b", suffix, re.I):
                declared_type = type_match.group(0) + " UNSIGNED"
            else:
                declared_type = type_match.group(0)
            # Never export defaults, comments, CHECK text or source row values.
            columns.append(ColumnInventory(_unquote(col.group(1)), declared_type))
        if not columns:
            raise UnsafeSource("EMPTY_OR_UNSUPPORTED_TABLE")
        if len(columns) > _MAX_COLUMNS or len(tables) >= _MAX_TABLES:
            raise UnsafeSource("SCHEMA_SIZE_UNSUPPORTED")
        if table in used or len({c.name for c in columns}) != len(columns):
            raise UnsafeSource("DUPLICATE_SCHEMA_IDENTITY")
        used.add(table)
        tables.append(TableInventory(table, tuple(columns)))
    if not tables:
        raise UnsafeSource("NO_SUPPORTED_TABLE_DDL")
    warnings = ("DDL_ONLY_NO_ROWS_OR_RELATIONS_VALIDATED", "SQL_NOT_EXECUTED")
    if unrelated:
        warnings += ("OTHER_SQL_NOT_PARSED",)
    return tuple(tables), warnings


def inspect_staged_copy(
    source_path: Path, staging_root: Path, *, dialect: str,
    attested_offline_copy: bool = False, encoding: str = "utf-8",
) -> InspectionReport:
    """No live connections, credentials, target DB or data writes."""
    if dialect not in _DIALECTS:
        raise UnsafeSource("DIALECT_MUST_BE_EXPLICIT")
    source, size = _copy_path(Path(source_path), Path(staging_root), attested_offline_copy)
    before_stat = source.stat()
    before = (before_stat.st_dev, before_stat.st_ino, before_stat.st_size, before_stat.st_mtime_ns)
    before_digest = _hash(source)
    with source.open("rb") as stream:
        magic = stream.read(32)
    if source.suffix.lower() in _SQLITE_EXT and dialect == "sqlite":
        if not magic.startswith(b"SQLite format 3\x00"):
            raise UnsafeSource("SQLITE_MAGIC_MISMATCH")
        if any(source.with_name(source.name + suffix).exists()
               for suffix in ("-wal", "-shm", "-journal")):
            raise UnsafeSource("SQLITE_SIDECAR_REQUIRES_COLD_COPY")
        tables = _sqlite(source)
        warnings = ("SCHEMA_ONLY_NO_ROW_COUNTS",)
        fmt = "sqlite-copy"
    elif source.suffix.lower() == ".sql":
        if magic.startswith((b"PGDMP", b"SQLite format 3\x00")):
            raise UnsafeSource("FORMAT_MISMATCH")
        if encoding not in _ENCODINGS:
            raise UnsafeSource("ENCODING_UNSUPPORTED")
        try:
            sql_text = source.read_bytes().decode(encoding, errors="strict")
        except UnicodeError as exc:
            raise UnsafeSource("ENCODING_INVALID") from exc
        if "\x00" in sql_text:
            raise UnsafeSource("BINARY_INPUT_FORBIDDEN")
        tables, warnings = _sql(sql_text)
        fmt = "sql-text-ddl"
    else:
        raise UnsafeSource("NATIVE_ADAPTER_NOT_IMPLEMENTED")
    checksum = _hash(source)
    after_stat = source.stat()
    after = (after_stat.st_dev, after_stat.st_ino, after_stat.st_size, after_stat.st_mtime_ns)
    if before != after or checksum != before_digest or size != after_stat.st_size:
        raise UnsafeSource("SOURCE_CHANGED_DURING_INSPECTION")
    return InspectionReport(dialect, fmt, checksum, size, tables, warnings)
