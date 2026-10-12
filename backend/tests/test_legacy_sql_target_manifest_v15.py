"""LOT05.2-B2a: SQLAlchemy MetaData adapter on synthetic and *declared* live models only.

No database URLs, connections, source dumps, migrations or patient rows used.
"""
import dataclasses
import hashlib
import importlib
import json
import unittest

from sqlalchemy import Column, Integer, MetaData, String, Table

from backend.services.legacy_sql_target_manifest_v15 import (
    TargetManifestRefused,
    build_declared_target_manifest,
)
from backend.services.legacy_sql_mapping_v15 import propose_mapping


def clinical_metadata():
    md = MetaData()
    Table(
        "patients", md,
        Column("id", Integer, primary_key=True),
        Column("nom", String(100)),
        Column("prenom", String(100)),
        Column("password_hash", String(255)),
        Column("is_superadmin", Integer),
        Column("patient_ref", String(16)),
    )
    Table("appointments", md,
          Column("id", Integer), Column("patient_id", Integer),
          Column("session_token", String(255)))
    Table("payments", md, Column("id", Integer), Column("amount", Integer))
    Table("users", md, Column("id", Integer), Column("hashed_password", String(255)))
    return md


def build(metadata=None, scope=("appointments", "patients")):
    return build_declared_target_manifest(
        metadata if metadata is not None else clinical_metadata(),
        requested_tables=scope,
        declared_revision="neo000000027",
    )


class TargetManifestAdapterTest(unittest.TestCase):
    def test_exact_requested_orm_names_and_version_provenance(self):
        out = build()
        self.assertEqual([t.name for t in out.tables], ["appointments", "patients"])
        self.assertEqual(out.provenance, "SQLALCHEMY_DECLARED_METADATA_ONLY")
        self.assertEqual(out.as_ui_json()["schema_revision"], "orm-declared:neo000000027")
        self.assertEqual(
            [t.name for t in out.as_mapping_target().tables], ["appointments", "patients"]
        )

    def test_filters_credentials_and_privilege_flags(self):
        out = build(scope=("patients",))
        self.assertNotIn("password_hash", out.tables[0].columns)
        self.assertNotIn("is_superadmin", out.tables[0].columns)
        self.assertIn("nom", out.tables[0].columns)
        self.assertIn("prenom", out.tables[0].columns)
        self.assertEqual(out.filtered_column_count, 2)

    def test_rejects_credentials_and_user_account_table_even_if_requested(self):
        with self.assertRaisesRegex(TargetManifestRefused, "SENSITIVE_TARGET_TABLE_FORBIDDEN"):
            build(scope=("users",))

    def test_never_claims_physical_schema_or_admin(self):
        out = build()
        self.assertFalse(out.physical_schema_verified)
        self.assertFalse(out.tenant_verified)
        self.assertFalse(out.admin_approved)
        self.assertFalse(out.dry_run_completed)
        self.assertFalse(out.import_permitted)

    def test_rejects_missing_table_no_silent_omission(self):
        with self.assertRaisesRegex(TargetManifestRefused, "REQUESTED_TARGET_TABLE_MISSING"):
            build(scope=("patients", "fake_table"))

    def test_requires_non_empty_explicit_scoped_selection(self):
        with self.assertRaisesRegex(TargetManifestRefused, "EXPLICIT_TABLE_SCOPE_REQUIRED"):
            build(scope=())
        with self.assertRaisesRegex(TargetManifestRefused, "EXPLICIT_TABLE_SCOPE_REQUIRED"):
            build(scope=["patients"])

    def test_rejects_duplicate_casefold_table_scope(self):
        with self.assertRaisesRegex(TargetManifestRefused, "AMBIGUOUS_METADATA_IDENTIFIER"):
            build(scope=("patients", "PATIENTS"))

    def test_rejects_duplicate_casefold_column_names(self):
        md = MetaData()
        Table("patients", md, Column("NAME", Integer), Column("name", Integer))
        with self.assertRaisesRegex(TargetManifestRefused, "AMBIGUOUS_METADATA_IDENTIFIER"):
            build(md, ("patients",))

    def test_rejects_invalid_requested_metadata_type(self):
        with self.assertRaisesRegex(TargetManifestRefused, "DECLARATIVE_METADATA_REQUIRED"):
            build(metadata={})

    def test_rejects_revision_injection(self):
        with self.assertRaisesRegex(TargetManifestRefused, "INVALID_DECLARED_REVISION"):
            build_declared_target_manifest(
                clinical_metadata(), requested_tables=("patients",),
                declared_revision="neo000000027; DROP TABLE patients",
            )

    def test_deterministic_fingerprint_ignores_table_declaration_order(self):
        first = build().schema_fingerprint
        self.assertEqual(first, build(scope=("patients", "appointments")).schema_fingerprint)
        self.assertEqual(len(first), 64)
        self.assertEqual(first, first.lower())

    def test_content_change_invalidates_fingerprint(self):
        a = build()
        md = clinical_metadata()
        md.tables["patients"].append_column(Column("legacy_id", Integer))
        b = build(md)
        self.assertNotEqual(a.schema_fingerprint, b.schema_fingerprint)

    def test_schema_qualified_tables_are_never_silently_collapsed(self):
        md = MetaData()
        Table("patients", md, Column("id", Integer), schema="public")
        Table("patients", md, Column("id", Integer), schema="archive")
        out = build(md, ("public.patients",))
        self.assertEqual(out.tables[0].name, "public.patients")
        with self.assertRaisesRegex(TargetManifestRefused, "REQUESTED_TARGET_TABLE_MISSING"):
            build(md, ("patients",))

    def test_untrusted_ui_payload_has_no_patient_values_or_authority_flags(self):
        out = build()
        raw = json.dumps(out.as_ui_json(), sort_keys=True)
        self.assertNotIn("password_hash", raw)
        self.assertNotIn("patient-full-name", raw)
        self.assertNotIn("admin_approved", raw)
        self.assertNotIn("import_permitted", raw)
        self.assertEqual(set(out.as_ui_json()), {"schema_revision", "tables"})

    def test_empty_orm_is_rejected(self):
        with self.assertRaisesRegex(TargetManifestRefused, "EMPTY_ORM_METADATA"):
            build(MetaData(), ("patients",))

    def test_fully_secret_table_is_rejected(self):
        md = MetaData()
        Table("clinic", md, Column("password_hash", String(40)), Column("session_token", String(40)))
        with self.assertRaisesRegex(TargetManifestRefused, "NO_SAFE_COLUMNS_IN_TARGET_TABLE"):
            build(md, ("clinic",))

    def test_does_not_call_engine_or_reflect_tables(self):
        import sqlalchemy
        old = sqlalchemy.create_engine

        def forbidden(*args, **kwargs):
            raise AssertionError("database connection forbidden in ORM adapter")

        try:
            sqlalchemy.create_engine = forbidden
            manifest = build()
            self.assertEqual(len(manifest.tables), 2)
        finally:
            sqlalchemy.create_engine = old

    def test_real_backend_models_declarations_exist_without_database_import(self):
        # Import code-defined ORM declarations, *not* database.py or any live URL.
        from backend.models_base import Base
        importlib.import_module("backend.models")
        manifest = build(Base.metadata, ("patients", "appointments", "payments"))
        self.assertIn("patients", [t.name for t in manifest.tables])
        self.assertIn("numero_dossier", next(t for t in manifest.tables if t.name == "patients").columns)
        self.assertNotIn("hashed_password", json.dumps(manifest.as_ui_json()))
        self.assertTrue(manifest.as_ui_json()["schema_revision"].startswith("orm-declared:"))

    def test_interoperates_with_non_approving_mapping_engine(self):
        from types import SimpleNamespace
        declared = build(scope=("patients",)).as_mapping_target()
        source = SimpleNamespace(
            sha256="a" * 64, import_permitted=False,
            tables=(SimpleNamespace(
                source_name="patients",
                columns=(SimpleNamespace(name="id", declared_type="INTEGER"),),
            ),),
        )
        proposal = propose_mapping(source, declared)
        self.assertEqual(proposal.tables[0].suggested_target_table, "patients")
        self.assertFalse(proposal.import_permitted)
        self.assertFalse(proposal.mapping_approved)

    def test_sensitive_credentials_not_exported_from_real_users_even_if_requested(self):
        from backend.models_base import Base
        importlib.import_module("backend.models")
        with self.assertRaisesRegex(TargetManifestRefused, "SENSITIVE_TARGET_TABLE_FORBIDDEN"):
            build(Base.metadata, ("users",))

    def test_mutating_orm_columns_does_not_change_previous_manifest(self):
        md = clinical_metadata()
        m = build(md)
        md.tables["patients"].append_column(Column("new_field", String(20)))
        self.assertNotIn("new_field", next(t for t in m.tables if t.name == "patients").columns)


if __name__ == "__main__":
    unittest.main()
