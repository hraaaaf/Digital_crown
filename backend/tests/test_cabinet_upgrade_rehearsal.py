from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
import sqlalchemy as sa

from backend.scripts import cabinet_upgrade_rehearsal as rehearsal


def test_archive_relative_path_strips_static_prefix(tmp_path: Path) -> None:
    media = tmp_path / "media"
    media.mkdir()
    assert rehearsal._archive_relative_path("static/archives/12/doc.pdf", media) == Path(
        "archives/12/doc.pdf"
    )
    assert rehearsal._archive_relative_path("static/documents/2026/09/doc.pdf", media) == Path(
        "documents/2026/09/doc.pdf"
    )


def test_archive_relative_path_strips_backend_media_prefixes(tmp_path: Path) -> None:
    media = tmp_path / "media"
    media.mkdir()
    assert rehearsal._archive_relative_path("backend/static/archives/a.pdf", media) == Path(
        "archives/a.pdf"
    )
    assert rehearsal._archive_relative_path("media/archives/a.pdf", media) == Path("archives/a.pdf")


def test_archive_relative_path_accepts_absolute_path_only_inside_media(tmp_path: Path) -> None:
    media = tmp_path / "media"
    inside = media / "archives" / "a.pdf"
    inside.parent.mkdir(parents=True)
    inside.write_bytes(b"a")
    assert rehearsal._archive_relative_path(str(inside), media) == Path("archives/a.pdf")

    outside = tmp_path / "outside.pdf"
    outside.write_bytes(b"x")
    with pytest.raises(ValueError, match="outside MEDIA_ROOT"):
        rehearsal._archive_relative_path(str(outside), media)


def test_archive_relative_path_rejects_parent_traversal(tmp_path: Path) -> None:
    media = tmp_path / "media"
    media.mkdir()
    with pytest.raises(ValueError, match="parent traversal"):
        rehearsal._archive_relative_path("static/archives/../../secret", media)


def test_archive_file_proof_resolves_static_archive_paths(tmp_path: Path) -> None:
    media = tmp_path / "media"
    archive = media / "archives" / "1" / "doc.pdf"
    archive.parent.mkdir(parents=True)
    payload = b"historical-pdf"
    archive.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()

    engine = sa.create_engine("sqlite+pysqlite:///:memory:")
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "CREATE TABLE document_archives (id INTEGER PRIMARY KEY, file_path TEXT NOT NULL, file_hash TEXT)"
        )
        connection.execute(
            sa.text(
                "INSERT INTO document_archives(id, file_path, file_hash) "
                "VALUES (1, 'static/archives/1/doc.pdf', :digest)"
            ),
            {"digest": digest},
        )

    proof = rehearsal._archive_file_proof(engine, media, media)
    assert proof["archive_count"] == 1
    assert proof["proved_files"] == 1


def test_archive_file_proof_fails_on_missing_or_hash_mismatch(tmp_path: Path) -> None:
    media = tmp_path / "media"
    (media / "archives").mkdir(parents=True)
    (media / "archives" / "bad.pdf").write_bytes(b"wrong")

    engine = sa.create_engine("sqlite+pysqlite:///:memory:")
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "CREATE TABLE document_archives (id INTEGER PRIMARY KEY, file_path TEXT NOT NULL, file_hash TEXT)"
        )
        connection.execute(
            sa.text(
                "INSERT INTO document_archives(id, file_path, file_hash) VALUES "
                "(1, 'static/archives/missing.pdf', NULL), "
                "(2, 'static/archives/bad.pdf', :digest)"
            ),
            {"digest": hashlib.sha256(b"expected").hexdigest()},
        )

    with pytest.raises(RuntimeError, match="Archives non prouvées"):
        rehearsal._archive_file_proof(engine, media, media)


def test_snapshot_preserves_historical_rows_when_additive_column_is_added() -> None:
    engine = sa.create_engine("sqlite+pysqlite:///:memory:")
    with engine.begin() as connection:
        connection.exec_driver_sql("CREATE TABLE patients (id INTEGER PRIMARY KEY, nom TEXT NOT NULL)")
        connection.exec_driver_sql("INSERT INTO patients(id, nom) VALUES (1, 'A'), (2, 'B')")

    before = rehearsal._database_snapshot(engine)
    with engine.begin() as connection:
        connection.exec_driver_sql("ALTER TABLE patients ADD COLUMN new_nullable TEXT")
    after = rehearsal._database_snapshot_after(engine, before)
    rehearsal._assert_data_preserved(before, after)
    assert before["patients"]["pk_sha256"] == after["patients"]["pk_sha256"]


def test_snapshot_rejects_primary_key_drift() -> None:
    before_engine = sa.create_engine("sqlite+pysqlite:///:memory:")
    with before_engine.begin() as connection:
        connection.exec_driver_sql(
            "CREATE TABLE patients (id INTEGER PRIMARY KEY, external_id INTEGER, nom TEXT)"
        )
        connection.exec_driver_sql("INSERT INTO patients(id, external_id, nom) VALUES (1, 10, 'A')")
    before = rehearsal._database_snapshot(before_engine)

    after_engine = sa.create_engine("sqlite+pysqlite:///:memory:")
    with after_engine.begin() as connection:
        connection.exec_driver_sql(
            "CREATE TABLE patients (id INTEGER, external_id INTEGER PRIMARY KEY, nom TEXT)"
        )
        connection.exec_driver_sql("INSERT INTO patients(id, external_id, nom) VALUES (1, 10, 'A')")

    with pytest.raises(RuntimeError, match="Clé primaire historique modifiée"):
        rehearsal._database_snapshot_after(after_engine, before)


def test_relation_preservation_allows_additive_foreign_keys() -> None:
    historical = {"patients(employer_id)->users(id)": 0}
    after = {
        "patients(employer_id)->users(id)": 0,
        "actes(catalog_act_id)->catalog_acts(id)": 0,
    }
    rehearsal._assert_relations_preserved(historical, after, "migration")


def test_relation_preservation_rejects_removed_or_degraded_historical_fk() -> None:
    historical = {"patients(employer_id)->users(id)": 0}
    with pytest.raises(RuntimeError, match="FK historique supprimée"):
        rehearsal._assert_relations_preserved(historical, {}, "migration")
    with pytest.raises(RuntimeError, match="orphans 0 -> 1"):
        rehearsal._assert_relations_preserved(
            historical, {"patients(employer_id)->users(id)": 1}, "migration"
        )


def test_connection_args_omit_empty_user() -> None:
    target = rehearsal._parse_postgres_target("postgresql://localhost/example")
    args = rehearsal._connection_args(target)
    assert "-U" not in args


def test_isolation_fingerprint_normalizes_loopback_driver_password_and_query() -> None:
    first = rehearsal._database_fingerprint(
        "postgresql+psycopg2://user:secret@localhost:5432/dc_rehearsal_x_after?sslmode=disable"
    )
    second = rehearsal._database_fingerprint(
        "postgresql://user:other@127.0.0.1/dc_rehearsal_x_after"
    )
    assert first == second


def test_clone_name_is_strictly_rehearsal_scoped() -> None:
    name = rehearsal._clone_name("20260916_120000_abc123", "after")
    assert name.startswith("dc_rehearsal_")
    assert rehearsal.SAFE_DB_NAME.fullmatch(name)
