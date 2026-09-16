"""Deterministic, fail-closed rehearsal of a cabinet PostgreSQL upgrade.

Safety contract
---------------
* The source/live database is touched only by ``pg_dump``.
* The same dump is restored into two new databases whose names start with
  ``dc_rehearsal_``.  Existing databases are never dropped or overwritten.
* BEFORE is the immutable control clone.  AFTER alone receives Alembic and the
  backend smoke boot.
* Source media are copied to an isolated directory and hashed before/after the
  copy.  Any concurrent source-media mutation blocks the proof.
* On failure the clones/work directory are intentionally kept for inspection.

This is an operator tool, not a cabinet startup path.  It never changes the live
schema and never silently stamps a non-empty existing database.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
import uuid
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import unquote, urlsplit, urlunsplit

import sqlalchemy as sa
from sqlalchemy.engine import Engine, URL, make_url


REPO_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_VERSION_TABLE = "alembic_version"
SAFE_DB_NAME = re.compile(r"^dc_rehearsal_[a-z0-9_]{1,48}$")
ARCHIVE_PREFIXES = (("static",), ("media",), ("backend", "static"), ("backend", "media"))


@dataclass(frozen=True)
class PostgresTarget:
    url: URL
    host: str
    port: int
    user: str
    password: str
    database: str


def _json_default(value: Any) -> Any:
    if isinstance(value, (dt.datetime, dt.date, dt.time)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, bytes):
        return {"__bytes_sha256__": hashlib.sha256(value).hexdigest(), "length": len(value)}
    if isinstance(value, uuid.UUID):
        return str(value)
    return str(value)


def _stable_hash(value: Any) -> str:
    payload = json.dumps(
        value,
        default=_json_default,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _find_pg_binary(name: str) -> str:
    found = shutil.which(name)
    if found:
        return found
    if os.name == "nt":
        import glob

        candidates = sorted(
            glob.glob(f"C:/Program Files/PostgreSQL/*/bin/{name}.exe"), reverse=True
        )
        if candidates:
            return candidates[0]
    return name


def _canonical_database_target(database_url: str) -> str:
    """Mirror the runtime PostgreSQL isolation identity without importing backend."""
    parsed = urlsplit(str(database_url or "").strip())
    if not parsed.scheme:
        return str(database_url or "").strip().lower()
    scheme = parsed.scheme.lower().split("+", 1)[0]
    if scheme not in {"postgres", "postgresql"}:
        raise RuntimeError("Le rehearsal cabinet exige une cible PostgreSQL.")
    hostname = (parsed.hostname or "").lower()
    if hostname in {"localhost", "127.0.0.1", "::1", "0.0.0.0"}:
        hostname = "loopback"
    elif ":" in hostname and not hostname.startswith("["):
        hostname = f"[{hostname}]"
    username = unquote(parsed.username or "")
    netloc = f"{username}@" if username else ""
    netloc += f"{hostname}:{parsed.port or 5432}"
    return urlunsplit(("postgresql", netloc, unquote(parsed.path), "", ""))


def _database_fingerprint(database_url: str) -> str:
    return hashlib.sha256(_canonical_database_target(database_url).encode("utf-8")).hexdigest()


def _media_manifest(root: Path) -> dict[str, Any]:
    root = root.resolve()
    if not root.is_dir():
        raise RuntimeError(f"MEDIA_ROOT introuvable: {root}")
    files: list[tuple[str, int, str]] = []
    for path in sorted((p for p in root.rglob("*") if p.is_file()), key=lambda p: p.as_posix()):
        rel = path.relative_to(root).as_posix()
        files.append((rel, path.stat().st_size, _sha256_file(path)))
    return {
        "file_count": len(files),
        "total_bytes": sum(item[1] for item in files),
        "manifest_sha256": _stable_hash(files),
    }


def _parse_postgres_target(raw_url: str) -> PostgresTarget:
    url = make_url(raw_url)
    if url.get_backend_name() != "postgresql" or not url.database:
        raise RuntimeError("SOURCE_DATABASE_URL doit cibler PostgreSQL avec un nom de base.")
    return PostgresTarget(
        url=url,
        host=url.host or "localhost",
        port=int(url.port or 5432),
        user=url.username or "",
        password=url.password or "",
        database=url.database,
    )


def _clone_url(source: PostgresTarget, database: str) -> str:
    if not SAFE_DB_NAME.fullmatch(database):
        raise RuntimeError(f"Nom de DB rehearsal refusé: {database!r}")
    return source.url.set(database=database).render_as_string(hide_password=False)


def _masked_target(source: PostgresTarget) -> str:
    return f"postgresql://{source.user or '<default>'}:***@{source.host}:{source.port}/{source.database}"


def _admin_engine(source: PostgresTarget) -> Engine:
    return sa.create_engine(
        source.url.set(database="postgres"), isolation_level="AUTOCOMMIT", pool_pre_ping=True
    )


def _database_exists(admin: Engine, name: str) -> bool:
    with admin.connect() as connection:
        return bool(connection.execute(sa.text("SELECT 1 FROM pg_database WHERE datname=:name"), {"name": name}).scalar())


def _create_database(admin: Engine, name: str) -> None:
    if not SAFE_DB_NAME.fullmatch(name):
        raise RuntimeError(f"Nom de DB rehearsal refusé: {name!r}")
    if _database_exists(admin, name):
        raise RuntimeError(f"DB rehearsal déjà existante: {name}; aucun écrasement implicite.")
    quoted = admin.dialect.identifier_preparer.quote(name)
    with admin.connect() as connection:
        connection.exec_driver_sql(f"CREATE DATABASE {quoted}")


def _drop_database(admin: Engine, name: str) -> None:
    if not SAFE_DB_NAME.fullmatch(name):
        raise RuntimeError(f"Refus cleanup DB non-rehearsal: {name!r}")
    quoted = admin.dialect.identifier_preparer.quote(name)
    with admin.connect() as connection:
        connection.execute(
            sa.text("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname=:name AND pid<>pg_backend_pid()"),
            {"name": name},
        )
        connection.exec_driver_sql(f"DROP DATABASE IF EXISTS {quoted}")


def _pg_env(source: PostgresTarget) -> dict[str, str]:
    env = os.environ.copy()
    if source.password:
        env["PGPASSWORD"] = source.password
    return env


def _connection_args(source: PostgresTarget) -> list[str]:
    args = ["-h", source.host, "-p", str(source.port)]
    if source.user:
        args += ["-U", source.user]
    return args


def _dump_source(source: PostgresTarget, output: Path) -> None:
    cmd = [
        _find_pg_binary("pg_dump"),
        *_connection_args(source),
        "-d",
        source.database,
        "--format=custom",
        "--no-owner",
        "--no-privileges",
        "--file",
        str(output),
    ]
    result = subprocess.run(cmd, env=_pg_env(source), capture_output=True, check=False)
    if result.returncode != 0:
        raise RuntimeError("pg_dump a échoué: " + result.stderr.decode(errors="replace")[-2000:])
    if not output.is_file() or output.stat().st_size == 0:
        raise RuntimeError("pg_dump n'a produit aucun dump exploitable.")


def _restore_dump(source: PostgresTarget, database: str, dump_path: Path) -> None:
    cmd = [
        _find_pg_binary("pg_restore"),
        *_connection_args(source),
        "-d",
        database,
        "--no-owner",
        "--no-privileges",
        "--exit-on-error",
        str(dump_path),
    ]
    result = subprocess.run(cmd, env=_pg_env(source), capture_output=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(
            f"pg_restore vers {database} a échoué: " + result.stderr.decode(errors="replace")[-2000:]
        )


def _table_rows(engine: Engine, table: str, columns: Iterable[str]) -> list[list[Any]]:
    columns = list(columns)
    if not columns:
        return []
    preparer = engine.dialect.identifier_preparer
    quoted_table = preparer.quote(table)
    quoted_columns = ",".join(preparer.quote(column) for column in columns)
    with engine.connect() as connection:
        return [list(row) for row in connection.execute(sa.text(f"SELECT {quoted_columns} FROM {quoted_table}"))]


def _table_snapshot(engine: Engine, table: str, expected_columns: list[str] | None = None) -> dict[str, Any]:
    inspector = sa.inspect(engine)
    if not inspector.has_table(table):
        raise RuntimeError(f"Table historique absente: {table}")
    actual = [item["name"] for item in inspector.get_columns(table)]
    columns = expected_columns or actual
    missing = set(columns) - set(actual)
    if missing:
        raise RuntimeError(f"Colonnes historiques supprimées de {table}: {sorted(missing)}")
    pk_columns = list((inspector.get_pk_constraint(table) or {}).get("constrained_columns") or [])
    rows = _table_rows(engine, table, columns)
    row_hashes = sorted(_stable_hash(dict(zip(columns, row, strict=True))) for row in rows)
    pk_hashes: list[str] = []
    if pk_columns and set(pk_columns) <= set(columns):
        indexes = [columns.index(name) for name in pk_columns]
        pk_hashes = sorted(
            _stable_hash({name: row[index] for name, index in zip(pk_columns, indexes, strict=True)})
            for row in rows
        )
    return {
        "columns": columns,
        "pk_columns": pk_columns,
        "count": len(rows),
        "rows_sha256": _stable_hash(row_hashes),
        "pk_sha256": _stable_hash(pk_hashes),
    }


def _database_snapshot(engine: Engine) -> dict[str, dict[str, Any]]:
    tables = sorted(t for t in sa.inspect(engine).get_table_names(schema="public") if t != ALEMBIC_VERSION_TABLE)
    return {table: _table_snapshot(engine, table) for table in tables}


def _database_snapshot_after(engine: Engine, before: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        table: _table_snapshot(engine, table, list(snapshot["columns"]))
        for table, snapshot in before.items()
    }


def _assert_data_preserved(before: dict[str, dict[str, Any]], after: dict[str, dict[str, Any]]) -> None:
    failures: list[str] = []
    for table, snapshot in before.items():
        for key in ("count", "rows_sha256", "pk_sha256"):
            if snapshot[key] != after[table][key]:
                failures.append(f"{table}.{key}: {snapshot[key]} != {after[table][key]}")
    if failures:
        raise RuntimeError("Régression de données historiques: " + "; ".join(failures[:20]))


def _relation_snapshot(engine: Engine, tables: Iterable[str]) -> dict[str, int]:
    inspector = sa.inspect(engine)
    prep = engine.dialect.identifier_preparer
    output: dict[str, int] = {}
    for table in tables:
        for fk in inspector.get_foreign_keys(table):
            source_cols = list(fk.get("constrained_columns") or [])
            target_cols = list(fk.get("referred_columns") or [])
            target_table = fk.get("referred_table")
            if not source_cols or len(source_cols) != len(target_cols) or not target_table:
                continue
            join = " AND ".join(
                f"src.{prep.quote(src)}=dst.{prep.quote(dst)}"
                for src, dst in zip(source_cols, target_cols, strict=True)
            )
            present = " AND ".join(f"src.{prep.quote(src)} IS NOT NULL" for src in source_cols)
            missing = f"dst.{prep.quote(target_cols[0])} IS NULL"
            sql = (
                f"SELECT COUNT(*) FROM {prep.quote(table)} src "
                f"LEFT JOIN {prep.quote(target_table)} dst ON {join} WHERE {present} AND {missing}"
            )
            key = f"{table}({','.join(source_cols)})->{target_table}({','.join(target_cols)})"
            with engine.connect() as connection:
                output[key] = int(connection.execute(sa.text(sql)).scalar_one())
    return dict(sorted(output.items()))


def _schema_fingerprint(engine: Engine) -> dict[str, Any]:
    inspector = sa.inspect(engine)
    tables = sorted(inspector.get_table_names(schema="public"))
    payload: list[Any] = []
    for table in tables:
        columns = sorted((c["name"], str(c["type"]), bool(c["nullable"])) for c in inspector.get_columns(table))
        indexes = sorted((i.get("name"), tuple(i.get("column_names") or ()), bool(i.get("unique"))) for i in inspector.get_indexes(table))
        uniques = sorted((u.get("name"), tuple(u.get("column_names") or ())) for u in inspector.get_unique_constraints(table))
        fks = sorted((tuple(f.get("constrained_columns") or ()), f.get("referred_table"), tuple(f.get("referred_columns") or ())) for f in inspector.get_foreign_keys(table))
        payload.append((table, columns, indexes, uniques, fks))
    return {"table_count": len(tables), "schema_sha256": _stable_hash(payload), "tables": tables}


def _archive_relative_path(raw_path: str, source_media: Path) -> Path:
    """Map historical archive paths onto MEDIA_ROOT without duplicating static/media."""
    raw = str(raw_path or "").strip().replace("\\", "/")
    if not raw:
        raise ValueError("empty archive path")
    candidate = Path(raw)
    source_root = source_media.resolve()
    if candidate.is_absolute():
        resolved = candidate.resolve()
        try:
            return resolved.relative_to(source_root)
        except ValueError as exc:
            raise ValueError("absolute archive path outside MEDIA_ROOT") from exc
    parts = tuple(part for part in candidate.parts if part not in {"", "."})
    if ".." in parts:
        raise ValueError("parent traversal")
    for prefix in ARCHIVE_PREFIXES:
        if parts[: len(prefix)] == prefix:
            parts = parts[len(prefix) :]
            break
    if not parts:
        raise ValueError("archive path resolves to MEDIA_ROOT")
    return Path(*parts)


def _archive_file_proof(engine: Engine, media_root: Path, source_media: Path) -> dict[str, Any]:
    inspector = sa.inspect(engine)
    if not inspector.has_table("document_archives"):
        raise RuntimeError("document_archives absente.")
    columns = {item["name"] for item in inspector.get_columns("document_archives")}
    if "file_path" not in columns:
        raise RuntimeError("document_archives.file_path absent.")
    select = ["id", "file_path"] + (["file_hash"] if "file_hash" in columns else [])
    rows = _table_rows(engine, "document_archives", select)
    proof_rows: list[tuple[Any, str, str]] = []
    missing: list[Any] = []
    hash_mismatches: list[Any] = []
    for row in rows:
        data = dict(zip(select, row, strict=True))
        try:
            rel = _archive_relative_path(str(data.get("file_path") or ""), source_media)
        except ValueError:
            missing.append(data.get("id"))
            continue
        path = (media_root.resolve() / rel).resolve()
        try:
            path.relative_to(media_root.resolve())
        except ValueError:
            missing.append(data.get("id"))
            continue
        if not path.is_file():
            missing.append(data.get("id"))
            continue
        digest = _sha256_file(path)
        expected = str(data.get("file_hash") or "").strip().lower()
        if expected and re.fullmatch(r"[0-9a-f]{64}", expected) and expected != digest:
            hash_mismatches.append(data.get("id"))
        proof_rows.append((data.get("id"), rel.as_posix(), digest))
    if missing or hash_mismatches:
        raise RuntimeError(
            f"Archives non prouvées: missing={missing[:20]} hash_mismatch={hash_mismatches[:20]}"
        )
    return {"archive_count": len(rows), "proved_files": len(proof_rows), "proof_sha256": _stable_hash(sorted(proof_rows))}


def _alembic_revision(engine: Engine) -> str | None:
    inspector = sa.inspect(engine)
    if not inspector.has_table(ALEMBIC_VERSION_TABLE):
        return None
    with engine.connect() as connection:
        return connection.execute(sa.text("SELECT version_num FROM alembic_version")).scalar_one_or_none()


def _run_alembic(after_url: str) -> None:
    env = os.environ.copy()
    env.update(
        {
            "DATABASE_URL": after_url,
            "ENVIRONMENT": "rehearsal",
            "DIGITALCROWN_ISOLATED_RUNTIME": "1",
            "DIGITALCROWN_ISOLATION_DB_FINGERPRINT": _database_fingerprint(after_url),
        }
    )
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError("alembic upgrade head a échoué:\n" + (result.stderr or result.stdout)[-4000:])


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _smoke_backend(after_url: str, media_root: Path) -> dict[str, Any]:
    port = _free_port()
    env = os.environ.copy()
    env.update(
        {
            "DATABASE_URL": after_url,
            "MEDIA_ROOT": str(media_root.resolve()),
            "ENVIRONMENT": "rehearsal",
            "DIGITALCROWN_ISOLATED_RUNTIME": "1",
            "DIGITALCROWN_ISOLATION_DB_FINGERPRINT": _database_fingerprint(after_url),
        }
    )
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=REPO_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    deadline = time.time() + 35
    last_error = ""
    try:
        while time.time() < deadline:
            if process.poll() is not None:
                break
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=2) as response:
                    body = response.read().decode("utf-8", errors="replace")
                    if response.status == 200:
                        return {"status": response.status, "body_sha256": hashlib.sha256(body.encode()).hexdigest()}
            except Exception as exc:  # noqa: BLE001 - bounded local health probe
                last_error = str(exc)
            time.sleep(0.5)
        output = ""
        if process.stdout:
            output = process.stdout.read()[-4000:]
        raise RuntimeError(f"backend smoke /api/health failed: {last_error}\n{output}")
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


def _clone_name(run_id: str, suffix: str) -> str:
    name = f"dc_rehearsal_{run_id}_{suffix}"
    if not SAFE_DB_NAME.fullmatch(name):
        raise RuntimeError(f"Nom clone invalide: {name}")
    return name


def run(source_url: str, source_media: Path, work_dir: Path, *, cleanup: bool) -> dict[str, Any]:
    source = _parse_postgres_target(source_url)
    source_media = source_media.resolve()
    work_dir = work_dir.resolve()
    work_dir.mkdir(parents=True, exist_ok=False)
    run_id = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:6]
    before_db = _clone_name(run_id, "before")
    after_db = _clone_name(run_id, "after")
    before_url = _clone_url(source, before_db)
    after_url = _clone_url(source, after_db)
    dump_path = work_dir / "source.dump"
    copied_media = work_dir / "media"
    report_path = work_dir / "report.json"
    admin = _admin_engine(source)
    created: list[str] = []
    report: dict[str, Any] = {
        "status": "IN_PROGRESS",
        "source": _masked_target(source),
        "source_database_fingerprint": _database_fingerprint(source_url),
        "work_dir": str(work_dir),
        "before_db": before_db,
        "after_db": after_db,
    }
    try:
        media_source_before = _media_manifest(source_media)
        _dump_source(source, dump_path)
        report["dump_sha256"] = _sha256_file(dump_path)
        shutil.copytree(source_media, copied_media)
        media_source_after = _media_manifest(source_media)
        media_copy = _media_manifest(copied_media)
        if media_source_before != media_source_after:
            raise RuntimeError("MEDIA_ROOT source a changé pendant la copie; rehearsal non déterministe.")
        if media_source_before != media_copy:
            raise RuntimeError("Copie média différente de la source.")
        report["media_before"] = media_source_before

        _create_database(admin, before_db)
        created.append(before_db)
        _create_database(admin, after_db)
        created.append(after_db)
        _restore_dump(source, before_db, dump_path)
        _restore_dump(source, after_db, dump_path)

        before_engine = sa.create_engine(before_url, pool_pre_ping=True)
        after_engine = sa.create_engine(after_url, pool_pre_ping=True)
        before_data = _database_snapshot(before_engine)
        before_relations = _relation_snapshot(before_engine, before_data)
        before_archive = _archive_file_proof(before_engine, source_media, source_media)
        report["before"] = {
            "alembic_revision": _alembic_revision(before_engine),
            "schema": _schema_fingerprint(before_engine),
            "table_data_sha256": _stable_hash(before_data),
            "relations_sha256": _stable_hash(before_relations),
            "archive": before_archive,
        }

        _run_alembic(after_url)
        after_data = _database_snapshot_after(after_engine, before_data)
        _assert_data_preserved(before_data, after_data)
        after_relations = _relation_snapshot(after_engine, before_data)
        if before_relations != after_relations:
            raise RuntimeError("Régression des relations/FK historiques après migration.")
        after_archive = _archive_file_proof(after_engine, copied_media, source_media)
        if before_archive != after_archive:
            raise RuntimeError("Preuve archive différente BEFORE/AFTER.")

        schema_after_first = _schema_fingerprint(after_engine)
        _run_alembic(after_url)
        schema_after_second = _schema_fingerprint(after_engine)
        if schema_after_first != schema_after_second:
            raise RuntimeError("Second alembic upgrade head non idempotent.")

        media_pre_boot = _media_manifest(copied_media)
        smoke = _smoke_backend(after_url, copied_media)
        media_post_boot = _media_manifest(copied_media)
        if media_pre_boot != media_post_boot:
            raise RuntimeError("Le boot rehearsal a modifié les médias.")
        data_post_boot = _database_snapshot_after(after_engine, before_data)
        _assert_data_preserved(before_data, data_post_boot)
        if _relation_snapshot(after_engine, before_data) != before_relations:
            raise RuntimeError("Le boot rehearsal a modifié l'intégrité relationnelle historique.")
        if _schema_fingerprint(after_engine) != schema_after_second:
            raise RuntimeError("Le boot rehearsal a modifié le schéma.")

        report["after"] = {
            "alembic_revision": _alembic_revision(after_engine),
            "schema": schema_after_second,
            "table_data_sha256": _stable_hash(data_post_boot),
            "relations_sha256": _stable_hash(before_relations),
            "archive": after_archive,
            "health": smoke,
            "media": media_post_boot,
        }
        report["status"] = "PASS"
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        if cleanup:
            before_engine.dispose()
            after_engine.dispose()
            for name in reversed(created):
                _drop_database(admin, name)
            report["cleanup"] = "databases_dropped"
            report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        return report
    except Exception:
        report["status"] = "BLOCKED"
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        raise
    finally:
        admin.dispose()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Rehearse Digital Crown cabinet upgrade on isolated clones.")
    parser.add_argument(
        "--source-database-url",
        default=os.environ.get("DIGITALCROWN_REHEARSAL_SOURCE_DATABASE_URL", ""),
        help="Live/source PostgreSQL URL. It is used only by pg_dump and for creating isolated clone DBs.",
    )
    parser.add_argument("--media-root", required=True, type=Path, help="Current cabinet MEDIA_ROOT (read-only source).")
    parser.add_argument("--work-dir", type=Path, default=None, help="New evidence directory; must not already exist.")
    parser.add_argument("--cleanup", action="store_true", help="Drop only this run's clone DBs after a PASS.")
    parser.add_argument(
        "--confirm-source-dump-only",
        action="store_true",
        help="Required acknowledgement that the source DB must only be read by pg_dump.",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    if not args.confirm_source_dump_only:
        print("REHEARSAL BLOCKED: --confirm-source-dump-only est obligatoire.", file=sys.stderr)
        return 2
    if not args.source_database_url:
        print("REHEARSAL BLOCKED: source database URL manquante.", file=sys.stderr)
        return 2
    work_dir = args.work_dir or Path(tempfile.gettempdir()) / (
        "digitalcrown_rehearsal_" + dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d_%H%M%S")
    )
    try:
        report = run(args.source_database_url, args.media_root, work_dir, cleanup=args.cleanup)
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print(f"REHEARSAL BLOCKED: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
