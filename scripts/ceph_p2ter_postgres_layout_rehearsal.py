"""Prove a fresh PostgreSQL baseline and an existing stamped predecessor recover.

This rehearsal is destructive ONLY on the exact disposable CI database below.
No real or hosted database URL is allowed. No real patient data is accessed.
"""
import os
import subprocess
import sys

from sqlalchemy import create_engine, inspect, text

EXPECTED = "postgresql://postgres:postgres@127.0.0.1:5432/dc_atomic_synthetic"
assert os.getenv("GITHUB_ACTIONS") == "true"
assert os.getenv("ENVIRONMENT") == "test"
assert os.getenv("DIGITALCROWN_ISOLATED_RUNTIME") == "1"
assert os.getenv("T2_POSTGRES_ATOMIC_LAB") == "1"
assert os.getenv("DATABASE_URL") == EXPECTED

engine = create_engine(EXPECTED)
with engine.begin() as connection:
    head = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
    assert head == "ceparch0002", head
    cols = {c["name"]: c for c in inspect(connection).get_columns("cabinet_configs")}
    assert "content_offset_y" in cols, "Fresh baseline omitted runtime document layout column"
    assert cols["content_offset_y"]["nullable"] is False
    # Simulate a pre-repair DB already stamped at predecessor. Keep an unrelated
    # persisted marker to show upgrade only adds schema; no data is rewritten.
    connection.execute(text(
        "CREATE TABLE p2ter_schema_rehearsal_sentinel (id integer PRIMARY KEY, marker text NOT NULL)"
    ))
    connection.execute(text(
        "INSERT INTO p2ter_schema_rehearsal_sentinel (id,marker) "
        "VALUES (1,'SYNTHETIC_PREDECESSOR_PRESERVE')"
    ))
    connection.execute(text("ALTER TABLE cabinet_configs DROP COLUMN content_offset_y"))
    connection.execute(text("UPDATE alembic_version SET version_num = 'ceparch0001'"))

subprocess.run(
    [sys.executable, "-m", "alembic", "upgrade", "ceparch0002"],
    check=True, timeout=120, env=os.environ.copy(),
)
with engine.begin() as connection:
    assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "ceparch0002"
    cols = {c["name"]: c for c in inspect(connection).get_columns("cabinet_configs")}
    assert "content_offset_y" in cols
    assert cols["content_offset_y"]["nullable"] is False
    assert connection.execute(text(
        "SELECT marker FROM p2ter_schema_rehearsal_sentinel WHERE id = 1"
    )).scalar_one() == "SYNTHETIC_PREDECESSOR_PRESERVE"
    connection.execute(text("DROP TABLE p2ter_schema_rehearsal_sentinel"))
engine.dispose()
print("P2TER_POSTGRES_LAYOUT_FRESH_AND_PREDECESSOR_UPGRADE_PASS", {
    "fresh_metadata_column": True,
    "predecessor_backfill": True,
    "existing_unrelated_data_preserved": True,
    "cabinet_database_used": False,
})
