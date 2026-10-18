"""LOT05.7-A negative-only, synthetic metadata gates. No clinic DB involved."""
from __future__ import annotations

import ast
from dataclasses import replace
import importlib.util
from pathlib import Path
import sys
import unittest

BACKEND = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "lot05_7a_evidence_gate", BACKEND / "services" / "legacy_import_certification_gate_v15.py"
)
gate = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = gate
SPEC.loader.exec_module(gate)


def fake_claims(**kwargs):
    defaults = dict(
        tenant_id=777, authenticated_owner_id=777, asserted_tenant_owner_id=777,
        staged_source_sha256="a" * 64, inspector_source_sha256="a" * 64,
        mapping_source_sha256="a" * 64, dryrun_source_sha256="a" * 64,
        mapping_profile_sha256="b" * 64, dryrun_mapping_sha256="b" * 64,
        mapping_target_revision="neo000000031",
        dryrun_target_revision="neo000000031",
        observed_target_revision="neo000000031",
        critical_count=0, unresolved_duplicate_count=0, unmapped_required_count=0,
        cross_tenant_link_count=0, undocumented_media_count=0,
        source_offline_copy_attested=True, source_provenance_claimed=True,
        mapping_owner_review_claimed=True, dryrun_zero_target_writes_claimed=True,
        restore_rehearsal_claimed=True, replay_rehearsal_claimed=True,
        tenant_isolation_rehearsal_claimed=True,
    )
    defaults.update(kwargs)
    return gate.UntrustedImportEvidence(**defaults)


class GateFailClosedTests(unittest.TestCase):
    def evaluate(self, **changes):
        return gate.check_untrusted_import_evidence(fake_claims(**changes))

    def test_even_coherent_claims_never_enable_import(self):
        result = self.evaluate()
        self.assertTrue(result.claims_coherent)
        self.assertEqual(result.status, "CONSTRUCTION_CLAIMS_COHERENT")
        self.assertFalse(result.import_permitted)
        self.assertFalse(result.full_schema_certified)
        self.assertFalse(result.real_restore_certified)
        self.assertFalse(result.human_authorization_verified)
        self.assertIn("REAL_IMPORT_NOT_IMPLEMENTED", result.blockers)
        self.assertIn("HUMAN_SIGNOFF_NOT_VERIFIED", result.blockers)
        self.assertFalse(result.to_dict()["import_permitted"])

    def test_non_evidence_never_crashes_or_passes(self):
        for invalid in (None, {}, [], object(), "fake", 777, True):
            with self.subTest(invalid=type(invalid).__name__):
                report = gate.check_untrusted_import_evidence(invalid)
                self.assertFalse(report.claims_coherent)
                self.assertIn("INVALID_EVIDENCE_SHAPE", report.blockers)

    def test_source_digest_change_detected_at_every_boundary(self):
        for key in ("inspector_source_sha256", "mapping_source_sha256", "dryrun_source_sha256"):
            with self.subTest(key=key):
                report = self.evaluate(**{key: "c" * 64})
                self.assertIn("SOURCE_DIGEST_BINDING_MISMATCH", report.blockers)
                self.assertFalse(report.claims_coherent)

    def test_mapping_digest_binding_detects_change(self):
        report = self.evaluate(dryrun_mapping_sha256="c" * 64)
        self.assertIn("MAPPING_DIGEST_BINDING_MISMATCH", report.blockers)

    def test_all_revision_boundaries_are_exactly_pinned(self):
        for key in ("mapping_target_revision", "dryrun_target_revision", "observed_target_revision"):
            for value in ("neo000000030", "orm-declared:neo000000031", "", None):
                with self.subTest(key=key, value=value):
                    report = self.evaluate(**{key: value})
                    self.assertIn("TARGET_REVISION_UNVERIFIED_OR_STALE", report.blockers)

    def test_sha256_not_a_guessable_label_or_uppercase(self):
        for value in ("a" * 63, "A" * 64, "a" * 64 + "\n", "../../file", None, True):
            with self.subTest(value=str(value)[:8]):
                self.assertIn("INVALID_SHA256_CLAIM", self.evaluate(staged_source_sha256=value).blockers)

    def test_mapping_hash_rejects_unknown_values(self):
        self.assertIn("INVALID_SHA256_CLAIM", self.evaluate(mapping_profile_sha256={}).blockers)

    def test_owner_claim_must_match(self):
        self.assertIn("OWNER_SCOPE_CLAIM_MISMATCH", self.evaluate(asserted_tenant_owner_id=778).blockers)

    def test_numeric_tenant_owner_ids_are_strict(self):
        for key in ("tenant_id", "authenticated_owner_id", "asserted_tenant_owner_id"):
            for value in (0, -1, True, 1.0, "777", None):
                with self.subTest(key=key, value=value):
                    self.assertIn("INVALID_TENANT_OR_OWNER_CLAIM", self.evaluate(**{key: value}).blockers)

    def test_each_anomaly_category_blocks(self):
        for key in ("critical_count", "unresolved_duplicate_count", "unmapped_required_count",
                    "cross_tenant_link_count", "undocumented_media_count"):
            with self.subTest(key=key):
                self.assertIn("UNRESOLVED_IMPORT_ANOMALIES", self.evaluate(**{key: 1}).blockers)

    def test_invalid_anomaly_counter_values_fail_closed(self):
        for key in ("critical_count", "unresolved_duplicate_count", "unmapped_required_count",
                    "cross_tenant_link_count", "undocumented_media_count"):
            for value in (-1, True, "0", 0.0, None):
                with self.subTest(key=key, value=value):
                    self.assertIn("INVALID_ANOMALY_COUNT", self.evaluate(**{key: value}).blockers)

    def test_every_missing_untrusted_control_blocks(self):
        fields = (
            "source_offline_copy_attested", "source_provenance_claimed",
            "mapping_owner_review_claimed", "dryrun_zero_target_writes_claimed",
            "restore_rehearsal_claimed", "replay_rehearsal_claimed",
            "tenant_isolation_rehearsal_claimed",
        )
        for field in fields:
            for value in (False, None, 1, "true"):
                with self.subTest(field=field, value=value):
                    self.assertIn("MISSING_OR_INVALID_CONTROL_CLAIM", self.evaluate(**{field: value}).blockers)

    def test_all_injected_metadata_is_absent_from_public_report(self):
        report = self.evaluate()
        payload = str(report.to_dict())
        for value in ("777", "a" * 64, "b" * 64):
            self.assertNotIn(value, payload)
        self.assertEqual(set(report.to_dict()), {
            "status", "claims_coherent", "blockers", "import_permitted",
            "full_schema_certified", "real_restore_certified", "human_authorization_verified",
        })

    def test_report_authorization_is_literal_false_even_when_dataclass_modified(self):
        # Non-authorization properties are not mutable fields, even via replace.
        with self.assertRaises(TypeError):
            replace(self.evaluate(), import_permitted=True)
        with self.assertRaises((AttributeError, TypeError)):
            self.evaluate().import_permitted = True

    def test_no_runtime_dependency_or_side_effect_import(self):
        tree = ast.parse((BACKEND / "services" / "legacy_import_certification_gate_v15.py").read_text())
        modules = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
        roots = [a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names]
        self.assertNotIn("backend", modules)
        self.assertEqual(sorted(roots), ["re"])
        self.assertTrue(all(m in ("__future__", "dataclasses", "typing") for m in modules))
        self.assertFalse(any(
            isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
            and n.func.id in {"open", "exec", "eval", "compile", "__import__"}
            for n in ast.walk(tree)
        ))

    def test_existing_import_api_has_no_clinical_write_route(self):
        tree = ast.parse((BACKEND / "routers" / "legacy_migration_v15.py").read_text())
        route_paths = []
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for dec in node.decorator_list:
                if (isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute)
                        and isinstance(dec.func.value, ast.Name)
                        and dec.func.value.id == "router"
                        and dec.func.attr in ("get", "post", "put", "patch", "delete", "api_route", "options")):
                    route_paths.append((dec.func.attr, dec.args[0].value))
        self.assertEqual(sorted(route_paths), sorted([
            ("get", "/preflight"), ("post", "/synthetic-rehearsal"),
            ("get", "/synthetic-fixture"), ("post", "/synthetic-file-dryrun"),
        ]))


if __name__ == "__main__":
    unittest.main()
