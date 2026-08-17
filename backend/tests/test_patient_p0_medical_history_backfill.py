"""P0-G — prove the medical-history backfill preserves canonical Patient truth."""
import importlib.util
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / "alembic/versions/c3d4e5f6a7b8_backfill_patient_medical_history.py"


def _load_backfill_sql() -> str:
    spec = importlib.util.spec_from_file_location("patient_p0_medical_history_migration", MIGRATION)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.BACKFILL_SQL


def _db():
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE patients (
            id INTEGER PRIMARY KEY,
            antecedents_medicaux TEXT NULL
        );
        CREATE TABLE dossiers_cliniques (
            id INTEGER PRIMARY KEY,
            patient_id INTEGER NOT NULL UNIQUE,
            antecedents_medicaux TEXT NULL
        );
        """
    )
    return conn


def test_backfill_copies_legacy_value_only_when_patient_value_is_missing():
    conn = _db()
    conn.execute("INSERT INTO patients(id, antecedents_medicaux) VALUES (1, NULL)")
    conn.execute("INSERT INTO dossiers_cliniques(id, patient_id, antecedents_medicaux) VALUES (1, 1, 'Diabète type 2')")

    conn.execute(_load_backfill_sql())

    value = conn.execute("SELECT antecedents_medicaux FROM patients WHERE id = 1").fetchone()[0]
    assert value == "Diabète type 2"


def test_backfill_never_overwrites_existing_patient_value():
    conn = _db()
    conn.execute("INSERT INTO patients(id, antecedents_medicaux) VALUES (1, 'Allergie pénicilline')")
    conn.execute("INSERT INTO dossiers_cliniques(id, patient_id, antecedents_medicaux) VALUES (1, 1, 'Ancienne valeur')")

    conn.execute(_load_backfill_sql())

    value = conn.execute("SELECT antecedents_medicaux FROM patients WHERE id = 1").fetchone()[0]
    assert value == "Allergie pénicilline"


def test_backfill_ignores_blank_legacy_values():
    conn = _db()
    conn.execute("INSERT INTO patients(id, antecedents_medicaux) VALUES (1, NULL)")
    conn.execute("INSERT INTO dossiers_cliniques(id, patient_id, antecedents_medicaux) VALUES (1, 1, '   ')")

    conn.execute(_load_backfill_sql())

    value = conn.execute("SELECT antecedents_medicaux FROM patients WHERE id = 1").fetchone()[0]
    assert value is None


def test_backfill_fills_blank_patient_value_from_non_blank_legacy_value():
    conn = _db()
    conn.execute("INSERT INTO patients(id, antecedents_medicaux) VALUES (1, '  ')")
    conn.execute("INSERT INTO dossiers_cliniques(id, patient_id, antecedents_medicaux) VALUES (1, 1, 'AVK')")

    conn.execute(_load_backfill_sql())

    value = conn.execute("SELECT antecedents_medicaux FROM patients WHERE id = 1").fetchone()[0]
    assert value == "AVK"
