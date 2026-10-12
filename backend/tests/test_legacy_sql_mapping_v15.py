"""V1.5-05.2-A: synthetic-only Mapping Studio contracts, no database."""
import importlib.util
import pathlib
import sys
import unittest
from dataclasses import replace
from types import SimpleNamespace


def load(name):
    path = pathlib.Path(__file__).resolve().parents[1] / "services" / (name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


m = load("legacy_sql_mapping_v15")
I = m.MappingRejected


def src(*tables, digest="a" * 64):
    return SimpleNamespace(
        sha256=digest, import_permitted=False,
        tables=tuple(SimpleNamespace(
            source_name=table,
            columns=tuple(SimpleNamespace(name=name, declared_type="TEXT") for name in columns),
        ) for table, columns in tables),
    )


def target(*tables, revision="neo000000027"):
    return m.TargetSnapshot(revision, tuple(m.TargetTable(name, tuple(cols)) for name, cols in tables))


def setup():
    s = src(("patients", ("id", "name", "legacy_no", "password_hash")),
            ("appointments", ("id", "patient_id")),
            ("legacy_extras", ("misc",)))
    t = target(("patients", ("id", "name", "legacy_no")),
               ("appointments", ("id", "patient_id")),
               ("users", ("id", "name")))
    decisions = (
        m.TableDecision("patients", "patients", (
            m.ColumnDecision("id", "id"),
            m.ColumnDecision("name", "name"),
            m.ColumnDecision("legacy_no", "legacy_no"),
            m.ColumnDecision("password_hash", None),
        )),
        m.TableDecision("appointments", "appointments", (
            m.ColumnDecision("id", "id"),
            m.ColumnDecision("patient_id", "patient_id"),
        )),
        m.TableDecision("legacy_extras", None, (m.ColumnDecision("misc", None),)),
    )
    return s, t, decisions


def draft(s=None, t=None, decisions=None):
    a, b, c = setup()
    return m.build_mapping_draft(s or a, t or b, c if decisions is None else decisions,
                                  source_software="LegacyCabinet", source_version="1.7",
                                  profile_version=1)


class TestMappingDraft(unittest.TestCase):
    def test_proposals_are_case_insensitive_exact_names_only(self):
        s = src(("PATIENTS", ("ID", "name", "unknown")))
        p = m.propose_mapping(s, target(("patients", ("id", "name", "other"))))
        self.assertEqual(p.tables[0].suggested_target_table, "patients")
        self.assertEqual([x.suggested_target_column for x in p.tables[0].columns],
                         ["id", "name", None])

    def test_no_semantic_or_fuzzy_mapping_guesses(self):
        p = m.propose_mapping(src(("personne", ("full_name",))),
                              target(("patients", ("name",))))
        self.assertIsNone(p.tables[0].suggested_target_table)
        self.assertIsNone(p.tables[0].columns[0].suggested_target_column)

    def test_schema_qualified_table_not_silently_collapsed(self):
        p = m.propose_mapping(src(("public.patients", ("id",))),
                              target(("patients", ("id",))))
        self.assertIsNone(p.tables[0].suggested_target_table)

    def test_proposal_never_signals_approval(self):
        s, t, _ = setup()
        p = m.propose_mapping(s, t)
        self.assertIs(p.mapping_approved, False)
        self.assertIs(p.import_permitted, False)
        self.assertIsNone(p.tables[0].suggested_target_table)
        self.assertIsNone(next(c for c in p.tables[1].columns
                               if c.source_column == "password_hash").suggested_target_column)

    def test_explicit_complete_draft_still_forbids_import(self):
        d = draft()
        self.assertEqual(len(d.decisions), 3)
        self.assertIs(d.admin_approved, False)
        self.assertIs(d.dry_run_completed, False)
        self.assertIs(d.import_permitted, False)
        self.assertEqual(len(d.profile_sha256), 64)

    def test_draft_deterministic_independent_of_decision_order(self):
        s, t, d = setup()
        self.assertEqual(draft().profile_sha256, draft(decisions=tuple(reversed(d))).profile_sha256)

    def test_missing_table_review_refused(self):
        s, t, d = setup()
        with self.assertRaisesRegex(I, "TABLE_REVIEW_INCOMPLETE"):
            draft(decisions=d[:-1])

    def test_missing_column_review_refused(self):
        s, t, d = setup()
        changed = (replace(d[0], columns=d[0].columns[:-1]),) + d[1:]
        with self.assertRaisesRegex(I, "COLUMN_REVIEW_INCOMPLETE"):
            draft(decisions=changed)

    def test_unknown_target_column_refused(self):
        s, t, d = setup()
        cols = (replace(d[0].columns[0], target_column="synthetic_not_real"),) + d[0].columns[1:]
        with self.assertRaisesRegex(I, "UNKNOWN_TARGET_COLUMN"):
            draft(decisions=(replace(d[0], columns=cols),) + d[1:])

    def test_unknown_source_column_refused(self):
        _, _, d = setup()
        cols = d[0].columns + (m.ColumnDecision("not_in_dump", None),)
        with self.assertRaisesRegex(I, "UNKNOWN_SOURCE_COLUMN"):
            draft(decisions=(replace(d[0], columns=cols),) + d[1:])

    def test_unknown_target_table_refused(self):
        _, _, d = setup()
        with self.assertRaisesRegex(I, "UNKNOWN_TARGET_TABLE"):
            draft(decisions=(replace(d[0], target_table="unknown"),) + d[1:])

    def test_duplicate_target_table_refused(self):
        s = src(("one", ("id",)), ("two", ("id",)))
        t = target(("patients", ("id",)))
        ds = (m.TableDecision("one", "patients", (m.ColumnDecision("id", "id"),)),
              m.TableDecision("two", "patients", (m.ColumnDecision("id", "id"),)))
        with self.assertRaisesRegex(I, "TARGET_TABLE_COLLISION"):
            draft(s, t, ds)

    def test_duplicate_target_column_refused(self):
        s = src(("people", ("x", "y")))
        t = target(("patients", ("id",)))
        ds = (m.TableDecision("people", "patients",
               (m.ColumnDecision("x", "id"), m.ColumnDecision("y", "id"))),)
        with self.assertRaisesRegex(I, "TARGET_COLUMN_COLLISION"):
            draft(s, t, ds)

    def test_orphan_column_mapping_refused(self):
        _, _, ds = setup()
        altered = replace(ds[-1], columns=(m.ColumnDecision("misc", "id"),))
        with self.assertRaisesRegex(I, "ORPHAN_COLUMN_MAPPING"):
            draft(decisions=ds[:-1] + (altered,))

    def test_sensitive_password_mapping_refused_even_explicitly(self):
        s = src(("legacy_users", ("password_hash",)))
        t = target(("users", ("hashed_password",)))
        ds = (m.TableDecision("legacy_users", "users",
              (m.ColumnDecision("password_hash", "hashed_password"),)),)
        with self.assertRaisesRegex(I, "CREDENTIAL_MAPPING_FORBIDDEN"):
            draft(s, t, ds)

    def test_duplicate_casefold_identifier_is_ambiguous(self):
        s = src(("patients", ("ID", "id")))
        with self.assertRaisesRegex(I, "DUPLICATE_OR_AMBIGUOUS_IDENTIFIER"):
            m.propose_mapping(s, target(("patients", ("id",))))

    def test_target_manifest_duplicate_identifier_refused(self):
        with self.assertRaisesRegex(I, "DUPLICATE_OR_AMBIGUOUS_IDENTIFIER"):
            m.propose_mapping(src(("patients", ("id",))),
                              target(("patients", ("ID", "id"))))

    def test_new_dump_same_schema_still_requires_new_review(self):
        s, t, _ = setup()
        original = draft()
        altered = src(*(("patients", ("id", "name", "legacy_no", "password_hash")),
                        ("appointments", ("id", "patient_id")),
                        ("legacy_extras", ("misc",))), digest="b" * 64)
        result = m.revalidate_mapping_draft(original, altered, t)
        self.assertFalse(result.exact_source_and_target)
        self.assertIn("SOURCE_DUMP_CHANGED", result.mismatches)
        self.assertTrue(result.requires_human_review)

    def test_exact_same_dump_still_requires_review(self):
        s, t, _ = setup()
        result = m.revalidate_mapping_draft(draft(), s, t)
        self.assertTrue(result.exact_source_and_target)
        self.assertTrue(result.requires_human_review)
        self.assertIs(result.import_permitted, False)
        self.assertIs(result.admin_approved, False)

    def test_changed_target_schema_fails_revalidation(self):
        s, t, _ = setup()
        changed = replace(t, tables=t.tables + (m.TargetTable("invoices", ("id",)),))
        result = m.revalidate_mapping_draft(draft(), s, changed)
        self.assertIn("TARGET_SCHEMA_CHANGED", result.mismatches)

    def test_profile_tampering_refused(self):
        s, t, _ = setup()
        altered = replace(draft(), source_software="Modified")
        with self.assertRaisesRegex(I, "DRAFT_TAMPERED"):
            m.revalidate_mapping_draft(altered, s, t)

    def test_invalid_profile_version_refused(self):
        s, t, ds = setup()
        with self.assertRaisesRegex(I, "INVALID_PROFILE_VERSION"):
            m.build_mapping_draft(s, t, ds, source_software="Demo",
                                  source_version=None, profile_version=0)

    def test_invalid_source_checksum_refused(self):
        s, t, _ = setup()
        with self.assertRaisesRegex(I, "INVALID_SOURCE_SHA256"):
            m.propose_mapping(replace_simple(s, sha256="not-a-checksum"), t)

    def test_real_inspector_contract_integration_with_synthetic_copy(self):
        inspector = load("legacy_sql_inspector_v15")
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            staging = pathlib.Path(temp)
            fixture = staging / "synthetic.sql"
            fixture.write_text("CREATE TABLE patients (id INT, full_name TEXT);"
                               "INSERT INTO patients VALUES (1, 'SYNTHETIC_PRIVATE');")
            inspected = inspector.inspect_staged_copy(
                fixture, staging, dialect="postgresql", attested_offline_copy=True
            )
            proposal = m.propose_mapping(inspected, target(("patients", ("id", "name"))))
            self.assertEqual(proposal.tables[0].suggested_target_table, "patients")
            self.assertEqual(proposal.tables[0].columns[0].suggested_target_column, "id")
            self.assertIsNone(proposal.tables[0].columns[1].suggested_target_column)
            self.assertNotIn("SYNTHETIC_PRIVATE", str(proposal))
            self.assertFalse(proposal.import_permitted)


def replace_simple(obj, **fields):
    return SimpleNamespace(**{**vars(obj), **fields})


if __name__ == "__main__":
    unittest.main()
