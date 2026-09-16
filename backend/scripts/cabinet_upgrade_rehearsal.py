"""Deterministic, fail-closed cabinet upgrade rehearsal.

The live/source PostgreSQL database is *never* migrated, booted, seeded, or used
for comparison queries.  It is touched only by ``pg_dump``.  The same dump is
restored into two isolated databases:

- BEFORE: immutable control clone used for data/relationship fingerprints.
- AFTER:  candidate clone upgraded to the current Alembic head and boot-smoked.

Media are copied into an isolated scratch directory and hashed before/after the
copy.  If the source media changes while copying, the run fails rather than
pretending to have a stable baseline.

This script intentionally keeps its scratch databases/files by default so a
reviewer can inspect them.  ``--cleanup`` drops only database names created by
this exact run after a successful proof.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable

import sqlalchemy as sa
from sqlalchemy.engine import URL, Engine, make_url

from backend.core.runtime_safety import database_target_fingerprint
from backend.scripts.backup_db import find_pg_binary


REPO_ROOT = Path(__file__).resolve().parents[2]
CRITICAL_TABLES = (
    "patients",
    "appointments",
    "actes",
    "payments",
    "document_archives",
)
ALEMBIC_VERSION_TABLE = "alembic_version"
SAFE_DB_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,62}$")


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


def _media_manifest(root: Path) -> dict[str, Any]:
    root = root.resolve()
    files: list[tuple[str, int, str]] = []
    if not root.is_dir():
        raise RuntimeError(f"MEDIA_ROOT introuvable: {root}")
    for path in sorted((item for item in root.rglob("*") if item.is_file()), key=lambda item: item.as_posix()):
        rel = path.relative_to(root).as_posix()
        files.append((rel, path.stat().st_size, _sha256_file(path)))
    return {
        "root": str(root),
        "file_count": len(files),
        "total_bytes": sum(item[1] for item in files),
        "manifest_sha256": _stable_hash(files),
        "files": files,
    }


def _parse_postgres_target(raw_url: str) -> PostgresTarget:
    url = make_url(raw_url)
    if url.get_backend_name() != "postgresql":
        raise RuntimeError("Le rehearsal cabinet exige une source PostgreSQL.")
    if not url.database:
        raise RuntimeError("DATABASE_URL PostgreSQL sans nom de base.")
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
    admin_url = source.url.set(database="postgres")
    return sa.create_engine(admin_url, isolation_level="AUTOCOMMIT", pool_pre_ping=True)


def _database_exists(admin: Engine, name: str) -> bool:
    with admin.connect() as connection:
        return bool(
            connection.execute(
                sa.text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": name}
            ).scalar()
        )


def _create_database(admin: Engine, name: str) -> None:
    if not SAFE_DB_NAME.fullmatch(name):
        raise RuntimeError(f"Nom de DB rehearsal refusé: {name!r}")
    if _database_exists(admin, name):
        raise RuntimeError(
            f"DB rehearsal déjà existante: {name}. Refus de drop/écrasement implicite."
        )
    preparer = admin.dialect.identifier_preparer
    with admin.connect() as connection:
        connection.exec_driver_sql(f"CREATE DATABASE {preparer.quote(name)}")


def _drop_database(admin: Engine, name: str) -> None:
    if not SAFE_DB_NAME.fullmatch(name) or not name.startswith("dc_rehearsal_"):
        raise RuntimeError(f"Refus cleanup DB non reconnue comme rehearsal: {name!r}")
    preparer = admin.dialect.identifier_preparer
    with admin.connect() as connection:
        connection.execute(
            sa.text(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = :name AND pid <> pg_backend_pid()"
            ),
            {"name": name},
        )
        connection.exec_driver_sql(f"DROP DATABASE IF EXISTS {preparer.quote(name)}")


def _pg_env(source: PostgresTarget) -> dict[str, str]:
    env = os.environ.copy()
    if source.password:
        env["PGPASSWORD"] = source.password
    return env


def _dump_source(source: PostgresTarget, output: Path) -> None:
    cmd = [
        find_pg_binary("pg_dump"),
        "-h",
        source.host,
        "-p",
        str(source.port),
        "-U",
        source.user,
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
        raise RuntimeError(
            "pg_dump a échoué: " + result.stderr.decode(errors="replace")[-2000:]
        )
    if not output.is_file() or output.stat().st_size == 0:
        raise RuntimeError("pg_dump n'a produit aucun dump exploitable.")


def _restore_dump(source: PostgresTarget, database: str, dump_path: Path) -> None:
    cmd = [
        find_pg_binary("pg_restore"),
        "-h",
        source.host,
        "-p",
        str(source.port),
        "-U",
        source.user,
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
            f"pg_restore vers {database} a échoué: "
            + result.stderr.decode(errors="replace")[-2000:]
        )


def _table_rows(engine: Engine, table: str, columns: Iterable[str]) -> list[list[Any]]:
    columns = list(columns)
    if not columns:
        return []
    preparer = engine.dialect.identifier_preparer
    quoted_table = preparer.quote(table)
    quoted_columns = ", ".join(preparer.quote(column) for column in columns)
    with engine.connect() as connection:
        rows = connection.execute(sa.text(f"SELECT {quoted_columns} FROM {quoted_table}"))
        return [list(row) for row in rows]


def _table_snapshot(engine: Engine, table: str) -> dict[str, Any]:
    inspector = sa.inspect(engine)
    if not inspector.has_table(table):
        raise RuntimeError(f"Table critique absente du clone BEFORE: {table}")
    columns = [item["name"] for item in inspector.get_columns(table)]
    pk_columns = list((inspector.get_pk_constraint(table) or {}).get("constrained_columns") or [])
    rows = _table_rows(engine, table, columns)
    row_payloads = [dict(zip(columns, row, strict=True)) for row in rows]
    row_hashes = sorted(_stable_hash(item) for item in row_payloads)
    if pk_columns:
        pk_indexes = [columns.index(name) for name in pk_columns]
        pk_values = sorted(
            (_json_default(tuple(row[index] for index in pk_indexes)) for row in rows),
            key=lambda value: json.dumps(value, default=_json_default, sort_keys=True),
        )
    else:
        pk_values = []
    return {
        "columns": columns,
        "pk_columns": pk_columns,
        "count": len(rows),
        "rows_sha256": _stable_hash(row_hashes),
        "pk_sha256": _stable_hash(pk_values),
    }


def _table_snapshot_with_columns(
    engine: Engine,
    table: str,
    columns: list[str],
    pk_columns: list[str],
) -> dict[str, Any]:
    inspector = sa.inspect(engine)
    if not inspector.has_table(table):
        raise RuntimeError(f"Table critique disparue après migration: {table}")
    after_columns = {item["name"] for item in inspector.get_columns(table)}
    missing = set(columns) - after_columns
    if missing:
        raise RuntimeError(f"Colonnes historiques supprimées de {table}: {sorted(missing)}")
    rows = _table_rows(engine, table, columns)
    row_payloads = [dict(zip(columns, row, strict=True)) for row in rows]
    row_hashes = sorted(_stable_hash(item) for item in row_payloads)
    if pk_columns:
        pk_indexes = [columns.index(name) for name in pk_columns]
        pk_values = sorted(
            (_json_default(tuple(row[index] for index in pk_indexes)) for row in rows),
            key=lambda value: json.dumps(value, default=_json_default, sort_keys=True),
        )
    else:
        pk_values = []
    return {
        "columns": columns,
        "pk_columns": pk_columns,
        "count": len(rows),
        "rows_sha256": _stable_hash(row_hashes),
        "pk_sha256": _stable_hash(pk_values),
    }


def _critical_snapshot(engine: Engine) -> dict[str, dict[str, Any]]:
    return {table: _table_snapshot(engine, table) for table in CRITICAL_TABLES}


def _critical_snapshot_after(
    engine: Engine, before: dict[str, dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    return {
        table: _table_snapshot_with_columns(
            engine,
            table,
            list(snapshot["columns"]),
            list(snapshot["pk_columns"]),
        )
        for table, snapshot in before.items()
    }


def _assert_critical_preserved(
    before: dict[str, dict[str, Any]], after: dict[str, dict[str, Any]], label: str
) -> None:
    failures: list[str] = []
    for table in CRITICAL_TABLES:
        for key in ("count", "rows_sha256", "pk_sha256"):
            if before[table][key] != after[table][key]:
                failures.append(
                    f"{table}.{key}: {before[table][key]!r} != {after[table][key]!r}"
                )
    if failures:
        raise RuntimeError(f"Régression données critiques ({label}): " + "; ".join(failures))


def _simple_fk_orphans(engine: Engine, table: str) -> dict[str, int]:
    inspector = sa.inspect(engine)
    preparer = engine.dialect.identifier_preparer
    result: dict[str, int] = {}
    for fk in inspector.get_foreign_keys(table):
        source_columns = list(fk.get("constrained_columns") or [])
        target_columns = list(fk.get("referred_columns") or [])
        target_table = fk.get("referred_table")
        if len(source_columns) != 1 or len(target_columns) != 1 or not target_table:
            continue
        source = source_columns[0]
        target = target_columns[0]
        key = f"{table}.{source}->{target_table}.{target}"
        sql = (
            f"SELECT COUNT(*) FROM {preparer.quote(table)} src "
            f"LEFT JOIN {preparer.quote(target_table)} dst "
            f"ON src.{preparer.quote(source)} = dst.{preparer.quote(target)} "
            f"WHERE src.{preparer.quote(source)} IS NOT NULL "
            f"AND dst.{preparer.quote(target)} IS NULL"
        )
        with engine.connect() as connection:
            result[key] = int(connection.execute(sa.text(sql)).scalar_one())
    return result


def _relation_snapshot(engine: Engine) -> dict[str, int]:
    output: dict[str, int] = {}
    for table in CRITICAL_TABLES:
        output.update(_simple_fk_orphans(engine, table))
    return dict(sorted(output.items()))


def _schema_fingerprint(engine: Engine) -> dict[str, Any]:
    inspector = sa.inspect(engine)
    tables = sorted(inspector.get_table_names(schema="public"))
    payload: list[Any] = []
    for table in tables:
        columns = sorted(
            (item["name"], str(item["type"]), bool(item["nullable"]))
            for item in inspector.get_columns(table, schema="public")
        )
        indexes = sorted(
            (
                item.get("name"),
                tuple(item.get("column_names") or ()),
                bool(item.get("unique")),
            )
            for item in inspector.get_indexes(table, schema="public")
        )
        payload.append((table, columns, indexes))
    return {
        "table_count": len(tables),
        "schema_sha256": _stable_hash(payload),
        "tables": tables,
    }


def _archive_file_proof(engine: Engine, source_media: Path, copied_media: Path) -> dict[str, int]:
    inspector = sa.inspect(engine)
    columns = {item["name"] for item in inspector.get_columns("document_archives")}
    if "file_path" not in columns:
        raise RuntimeError("document_archives.file_path absent; impossible de prouver les médias archivés.")
    select = ["id", "file_path"]
    if "file_hash" in columns:
        select.append("file_hash")
    rows = _table_rows(engine, "document_archives", select)
    source_root = source_media.resolve()
    copied_root = copied_media.resolve()
    checked = matched_hashes = missing = unresolved = 0
    for row in rows:
        data = dict(zip(select, row, strict=True))
        raw_path = str(data.get("file_path") or "").strip()
        if not raw_path:
            missing += 1
            continue
        candidate = Path(raw_path)
        try:
            if candidate.is_absolute():
                rel = candidate.resolve().relative_to(source_root)
            else:
                rel = Path(raw_path.replace("\\", "/"))
                if ".." in rel.parts:
                    raise ValueError("parent traversal")
            copied_path = (copied_root / rel).resolve()
            copied_path.relative_to(copied_root)
        except (OSError, ValueError):
            unresolved += 1
            continue
        if not copied_path.is_file():
            missing += 1
            continue
        checked += 1
        expected = str(data.get("file_hash") or "").strip().lower()
        if re.fullmatch(r"[0-9a-f]{64}", expected):
            if _sha256_file(copied_path) != expected:
                raise RuntimeError(
                    f"Hash document archivé divergent: document_archive id={data['id']}"
                )
            matched_hashes += 1
    if missing or unresolved:
        raise RuntimeError(
            "Archives média non résolues sur la copie: "
            f"checked={checked} missing={missing} unresolved={unresolved}"
        )
    return {
        "archive_rows": len(rows),
        "files_checked": checked,
        "hashes_matched": matched_hashes,
        "missing": missing,
        "unresolved": unresolved,
    }


def _migration_env(after_url: str, media_root: Path) -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "DATABASE_URL": after_url,
            "ENVIRONMENT": "rehearsal",
            "DIGITALCROWN_ISOLATED_RUNTIME": "true",
            "DIGITALCROWN_ISOLATION_DB_FINGERPRINT": database_target_fingerprint(after_url),
            "MEDIA_ROOT": str(media_root.resolve()),
            "TELEMETRY_ENABLED": "false",
            "CLOUD_AI_ENABLED": "false",
            "DEBUG": "false",
        }
    )
    env.setdefault("SECRET_KEY", "cabinet-upgrade-rehearsal-only-secret-key-000001")
    return env


def _run_alembic(after_url: str, media_root: Path) -> None:
    env = _migration_env(after_url, media_root)
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError("alembic upgrade head a échoué:\n" + result.stderr[-4000:])


def _alembic_version(engine: Engine) -> str:
    with engine.connect() as connection:
        return str(connection.execute(sa.text("SELECT version_num FROM alembic_version")).scalar_one())


def _boot_smoke(after_url: str, media_root: Path, port: int, timeout: float) -> dict[str, Any]:
    env = _migration_env(after_url, media_root)
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "backend.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=REPO_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    deadline = time.monotonic() + timeout
    last_error = ""
    try:
        while time.monotonic() < deadline:
            if process.poll() is not None:
                output = process.stdout.read() if process.stdout else ""
                raise RuntimeError("Backend rehearsal arrêté avant healthcheck:\n" + output[-4000:])
            try:
                with urllib.request.urlopen(
                    f"http://127.0.0.1:{port}/api/health", timeout=2
                ) as response:
                    body = response.read().decode("utf-8", errors="replace")
                    if response.status == 200:
                        return {"status": 200, "body_sha256": _stable_hash(body)}
            except Exception as exc:  # noqa: BLE001 - bounded startup retry
                last_error = str(exc)
                time.sleep(0.5)
        raise RuntimeError(f"Healthcheck rehearsal timeout: {last_error}")
    finally:
        process.terminate()
        try:
            process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def _copy_media_stably(source_media: Path, destination: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    before = _media_manifest(source_media)
    shutil.copytree(source_media, destination, copy_function=shutil.copy2)
    source_after = _media_manifest(source_media)
    copied = _media_manifest(destination)
    if (
        before["manifest_sha256"] != source_after["manifest_sha256"]
        or before["manifest_sha256"] != copied["manifest_sha256"]
        or before["file_count"] != copied["file_count"]
        or before["total_bytes"] != copied["total_bytes"]
    ):
        raise RuntimeError(
            "MEDIA_ROOT a changé pendant la copie ou la copie n'est pas bit-à-bit; rehearsal refusé."
        )
    return before, copied


def _build_run_names() -> tuple[str, str, str]:
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d_%H%M%S")
    token = f"{os.getpid() % 100000:05d}"
    base = f"dc_rehearsal_{stamp}_{token}"
    return base, f"{base}_before", f"{base}_after"


def _write_report(path: Path, report: dict[str, Any]) -> None:
    safe = dict(report)
    path.write_text(
        json.dumps(safe, default=_json_default, ensure_ascii=False, sort_keys=True, indent=2),
        encoding="utf-8",
    )


def run(args: argparse.Namespace) -> Path:
    source_url = os.environ.get(args.source_url_env, "").strip()
    if not source_url:
        raise RuntimeError(f"Variable {args.source_url_env} absente; aucune source DB fournie.")
    source = _parse_postgres_target(source_url)
    source_media = Path(args.media_root).expanduser().resolve()
    scratch_parent = Path(args.scratch_root).expanduser().resolve() if args.scratch_root else Path(tempfile.gettempdir())
    base, before_name, after_name = _build_run_names()
    scratch = scratch_parent / base
    scratch.mkdir(parents=True, exist_ok=False)
    dump_path = scratch / "cabinet_source.dump"
    copied_media = scratch / "media"
    report_path = scratch / "rehearsal_report.json"

    admin = _admin_engine(source)
    created: list[str] = []
    report: dict[str, Any] = {
        "status": "IN_PROGRESS",
        "repo_head_env": os.environ.get("GIT_COMMIT", ""),
        "source_target": _masked_target(source),
        "source_database": source.database,
        "scratch": str(scratch),
        "before_database": before_name,
        "after_database": after_name,
        "critical_tables": list(CRITICAL_TABLES),
    }
    _write_report(report_path, report)

    try:
        print(f"[rehearsal] source READ-ONLY dump target: {_masked_target(source)}")
        print(f"[rehearsal] scratch: {scratch}")
        _dump_source(source, dump_path)
        report["dump_bytes"] = dump_path.stat().st_size
        report["dump_sha256"] = _sha256_file(dump_path)

        source_manifest, copied_manifest = _copy_media_stably(source_media, copied_media)
        report["media"] = {
            "source_file_count": source_manifest["file_count"],
            "source_total_bytes": source_manifest["total_bytes"],
            "manifest_sha256": source_manifest["manifest_sha256"],
            "copy_manifest_sha256": copied_manifest["manifest_sha256"],
        }

        for name in (before_name, after_name):
            _create_database(admin, name)
            created.append(name)
            _restore_dump(source, name, dump_path)

        before_url = _clone_url(source, before_name)
        after_url = _clone_url(source, after_name)
        before_engine = sa.create_engine(before_url, pool_pre_ping=True)
        after_engine = sa.create_engine(after_url, pool_pre_ping=True)

        before_version = _alembic_version(before_engine)
        before_critical = _critical_snapshot(before_engine)
        before_relations = _relation_snapshot(before_engine)
        archive_proof = _archive_file_proof(before_engine, source_media, copied_media)
        report["before"] = {
            "alembic_version": before_version,
            "critical": before_critical,
            "relations": before_relations,
            "archive_media": archive_proof,
        }

        _run_alembic(after_url, copied_media)
        after_version = _alembic_version(after_engine)
        schema_first = _schema_fingerprint(after_engine)
        after_critical = _critical_snapshot_after(after_engine, before_critical)
        after_relations = _relation_snapshot(after_engine)
        _assert_critical_preserved(before_critical, after_critical, "après migration")
        if before_relations != after_relations:
            raise RuntimeError(
                "Relations/FK critiques divergentes après migration: "
                f"before={before_relations} after={after_relations}"
            )

        _run_alembic(after_url, copied_media)
        schema_second = _schema_fingerprint(after_engine)
        if schema_first != schema_second:
            raise RuntimeError("Second alembic upgrade head non idempotent sur clone AFTER.")

        media_before_boot = _media_manifest(copied_media)
        smoke = _boot_smoke(after_url, copied_media, args.port, args.boot_timeout)
        schema_after_boot = _schema_fingerprint(after_engine)
        after_boot_critical = _critical_snapshot_after(after_engine, before_critical)
        after_boot_relations = _relation_snapshot(after_engine)
        media_after_boot = _media_manifest(copied_media)

        _assert_critical_preserved(before_critical, after_boot_critical, "après boot")
        if before_relations != after_boot_relations:
            raise RuntimeError("Relations/FK critiques modifiées par le boot rehearsal.")
        if schema_second != schema_after_boot:
            raise RuntimeError("Le boot rehearsal a modifié le schéma.")
        if media_before_boot["manifest_sha256"] != media_after_boot["manifest_sha256"]:
            raise RuntimeError("Le boot rehearsal a modifié les médias copiés.")

        report["after"] = {
            "alembic_version": after_version,
            "critical": after_critical,
            "relations": after_relations,
            "schema_first": schema_first,
            "schema_second": schema_second,
            "schema_after_boot": schema_after_boot,
            "smoke": smoke,
            "media_manifest_after_boot": media_after_boot["manifest_sha256"],
        }
        report["status"] = "PASS"
        report["proof"] = {
            "same_dump_before_after": True,
            "critical_rows_preserved": True,
            "critical_primary_keys_preserved": True,
            "critical_fk_orphans_preserved": True,
            "second_upgrade_noop": True,
            "boot_schema_noop": True,
            "media_copy_bit_identical": True,
            "boot_media_noop": True,
            "historical_archive_files_resolved": True,
            "health_200": True,
        }
        _write_report(report_path, report)

        if args.cleanup:
            for name in reversed(created):
                _drop_database(admin, name)
            created.clear()
            report["cleanup"] = "created rehearsal databases dropped"
            _write_report(report_path, report)

        print(f"[rehearsal] PASS report={report_path}")
        return report_path
    except Exception as exc:
        report["status"] = "FAIL"
        report["error"] = f"{type(exc).__name__}: {exc}"
        report["created_databases_kept_for_review"] = list(created)
        _write_report(report_path, report)
        print(f"[rehearsal] FAIL report={report_path}", file=sys.stderr)
        raise
    finally:
        admin.dispose()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a fail-closed Digital Crown cabinet upgrade rehearsal on isolated PostgreSQL clones."
    )
    parser.add_argument(
        "--source-url-env",
        default="DATABASE_URL",
        help="Environment variable containing the source PostgreSQL URL; the URL is never printed with its password.",
    )
    parser.add_argument(
        "--media-root",
        required=True,
        help="Real cabinet MEDIA_ROOT to copy read-only into the rehearsal scratch directory.",
    )
    parser.add_argument(
        "--scratch-root",
        default="",
        help="Parent directory for dump/media/report; defaults to the OS temp directory.",
    )
    parser.add_argument("--port", type=int, default=8008, help="Isolated backend smoke port.")
    parser.add_argument("--boot-timeout", type=float, default=45.0)
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="After PASS only, drop the two rehearsal databases created by this run. Scratch files are kept.",
    )
    return parser


if __name__ == "__main__":
    try:
        run(build_parser().parse_args())
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print(f"REHEARSAL BLOCKED: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
