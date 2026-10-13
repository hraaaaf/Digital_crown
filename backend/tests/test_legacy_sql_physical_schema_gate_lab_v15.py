"""LOT05-B TEST-ONLY physical-schema discrepancy gate.

Reads injected SQLAlchemy Connection only. Never obtains an engine, external URL
or clinic credentials. A fake Alembic marker proves revision *matching*, NOT
migrations were applied or a tenant was authenticated.
"""
from __future__ import annotations

from dataclasses import dataclass
import unittest

from sqlalchemy import inspect, text

from test_legacy_sql_real_orm_scratch_v15 import _physical_scratch


class SchemaAttestationRefused(ValueError):
    pass


@dataclass(frozen=True)
class SyntheticAttestation:
    revision: str
    checked_tables: tuple[str, ...]
    physical_columns_checked: int
    revision_string_matches: bool
    migrated_with_alembic: bool = False
    tenant_authenticated: bool = False
    import_permitted: bool = False


_TABLES = ("appointments", "patients", "agenda_resources", "users")
_REVISION = "neo000000027"


def check_lab_physical_schema(*, connection, declared_metadata, expected_revision):
    """Read-only verifier, deliberately injectable only from synthetic fixtures."""
    if expected_revision != _REVISION:
        raise SchemaAttestationRefused("UNSUPPORTED_EXPECTED_REVISION")
    inspector = inspect(connection)
    if set(inspector.get_table_names()) != set(_TABLES) | {"alembic_version"}:
        raise SchemaAttestationRefused("UNEXPECTED_PHYSICAL_TABLES")
    versions = tuple(connection.execute(text("SELECT version_num FROM alembic_version")).scalars())
    if versions != (expected_revision,):
        raise SchemaAttestationRefused("ALEMBIC_VERSION_MISMATCH")
    total_columns = 0
    for name in _TABLES:
        declared = declared_metadata.tables[name]
        expected = {c.name: bool(c.nullable) for c in declared.columns}
        actual = {c["name"]: bool(c["nullable"]) for c in inspector.get_columns(name)}
        if expected != actual:
            raise SchemaAttestationRefused("COLUMN_OR_NULLABILITY_DRIFT")
        total_columns += len(actual)
        def fks_declared():
            return sorted((tuple(c.parent.name for c in fk.constraint.elements),
                           fk.column.table.name,
                           tuple(c.name for c in fk.constraint.referred_table.primary_key.columns))
                          for fk in declared.foreign_keys
                          if False)
        # Multi-column constraints are compared as sets; no auto-trust of strings.
        expected_fk = sorted(
            (tuple(col.name for col in fk.columns),
             next(iter(fk.elements)).column.table.name,
             tuple(el.column.name for el in fk.elements))
            for fk in declared.foreign_key_constraints
        )
        physical_fk = sorted(
            (tuple(fk["constrained_columns"]),
             fk["referred_table"],
             tuple(fk["referred_columns"]))
            for fk in inspector.get_foreign_keys(name)
        )
        if expected_fk != physical_fk:
            raise SchemaAttestationRefused("FOREIGN_KEY_DRIFT")
        expected_uniques = sorted(
            tuple(c.name for c in unique.columns)
            for unique in declared.constraints
            if unique.__class__.__name__ == "UniqueConstraint"
        )
        physical_uniques = sorted(
            tuple(x["column_names"])
            for x in inspector.get_unique_constraints(name)
        )
        if expected_uniques != physical_uniques:
            raise SchemaAttestationRefused("UNIQUE_CONSTRAINT_DRIFT")
    return SyntheticAttestation(expected_revision, _TABLES, total_columns, True)


def _fake_version(con, version):
    con.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"))
    if version is not None:
        con.execute(text("INSERT INTO alembic_version(version_num) VALUES (:v)"), {"v":version})


class SyntheticPhysicalSchemaTests(unittest.TestCase):
    def test_01_exact_revision_columns_fks_unique_passes(self):
        with _physical_scratch() as (md, con):
            _fake_version(con, _REVISION)
            result=check_lab_physical_schema(connection=con, declared_metadata=md,
                expected_revision=_REVISION)
            self.assertGreater(result.physical_columns_checked, 40)
            self.assertFalse(result.migrated_with_alembic)
            self.assertFalse(result.tenant_authenticated)
            self.assertFalse(result.import_permitted)

    def test_02_stale_revision_refused(self):
        with _physical_scratch() as (md, con):
            _fake_version(con, "neo000000026")
            with self.assertRaisesRegex(SchemaAttestationRefused, "ALEMBIC_VERSION_MISMATCH"):
                check_lab_physical_schema(connection=con, declared_metadata=md, expected_revision=_REVISION)

    def test_03_missing_alembic_version_refused(self):
        with _physical_scratch() as (md, con):
            with self.assertRaisesRegex(SchemaAttestationRefused, "UNEXPECTED_PHYSICAL_TABLES"):
                check_lab_physical_schema(connection=con, declared_metadata=md, expected_revision=_REVISION)

    def test_04_extra_unexpected_table_refused(self):
        with _physical_scratch() as (md, con):
            _fake_version(con, _REVISION)
            con.execute(text("CREATE TABLE extra_privileged (id INTEGER)"))
            with self.assertRaisesRegex(SchemaAttestationRefused, "UNEXPECTED_PHYSICAL_TABLES"):
                check_lab_physical_schema(connection=con, declared_metadata=md, expected_revision=_REVISION)

    def test_05_dropped_fk_detected_even_if_columns_same(self):
        # An adversary can remove one FK while keeping column names/nullable.
        from sqlalchemy import Column, ForeignKey, Integer, MetaData, Table
        with _physical_scratch() as (md, con):
            _fake_version(con, _REVISION)
            clone = MetaData()
            for t in md.tables.values():
                t.to_metadata(clone)
            cloned = clone.tables["appointments"]
            # Tamper source metadata only; compare to the *physical* original.
            fkc = next(f for f in cloned.foreign_key_constraints
                       if any(col.name == "patient_id" for col in f.columns))
            cloned.constraints.remove(fkc)
            with self.assertRaisesRegex(SchemaAttestationRefused, "FOREIGN_KEY_DRIFT"):
                check_lab_physical_schema(connection=con, declared_metadata=clone, expected_revision=_REVISION)

    def test_06_no_auto_approval_when_version_matches(self):
        with _physical_scratch() as (md, con):
            _fake_version(con, _REVISION)
            result=check_lab_physical_schema(connection=con, declared_metadata=md, expected_revision=_REVISION)
            self.assertFalse(result.import_permitted)
            self.assertFalse(result.migrated_with_alembic)
            self.assertFalse(result.tenant_authenticated)

if __name__ == "__main__":
    unittest.main()
