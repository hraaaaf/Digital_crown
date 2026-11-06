"""LOT05.7C-D: standalone replay-evidence FUE; generated FAKE CSV only.

No patient records, DB, network, runtime route, installation or clinical import.
"""
from __future__ import annotations

from dataclasses import replace
import csv
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch


BACKEND = Path(__file__).resolve().parents[1]
PACKAGE = "_lot05_7c_d_evidence_lab_only"
package = types.ModuleType(PACKAGE)
package.__path__ = [str(BACKEND / "services")]
sys.modules[PACKAGE] = package


def load(name):
    spec = importlib.util.spec_from_file_location(
        PACKAGE + "." + name, BACKEND / "services" / (name + ".py")
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


load("legacy_sql_inspector_v15")
mapping = load("legacy_sql_mapping_v15")
load("legacy_migration_csv_preview_v15")
lab = load("legacy_migration_csv_mapping_lab_v15")
evidence = load("legacy_migration_csv_evidence_lab_v15")


class SyntheticReplayEvidenceFUE(unittest.TestCase):
    def setUp(self):
        area = tempfile.TemporaryDirectory(prefix="LOT05_7C_D_FAKE_")
        self.addCleanup(area.cleanup)
        self.root = Path(area.name)
        self.stage = self.root / "staging"
        self.stage.mkdir()
        self.source = self.stage / "FAKE_patients.csv"
        self.headers = ["ancien_id", "prenom", "nom", "naissance", "ignore"]
        self.rows = [
            [f"FAKE{i:05d}", f"FAKE_FIRST_{i}", f"FAKE_LAST_{i}",
             "2000-02-29", "FAKE_EXTRA"]
            for i in range(15)
        ]
        self.write()

    def write(self, headers=None, rows=None):
        with self.source.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(self.headers if headers is None else headers)
            writer.writerows(self.rows if rows is None else rows)

    def choices(self, *, swapped=False):
        return (
            mapping.ColumnDecision("ancien_id", "legacy_id"),
            mapping.ColumnDecision("prenom", "family_name" if swapped else "given_name"),
            mapping.ColumnDecision("nom", "given_name" if swapped else "family_name"),
            mapping.ColumnDecision("naissance", "birth_date"),
            mapping.ColumnDecision("ignore", None),
        )

    def draft(self, *, swapped=False):
        return lab.draft_synthetic_patient_mapping(
            self.source, self.stage, decisions=self.choices(swapped=swapped),
            source_software="FAKE_VENDOR_NOT_VERIFIED", source_version="FAKE-1",
            lab_only_synthetic_fixture=True, attested_offline_copy=True,
        )

    def build(self, draft=None, path=None, **overrides):
        params = {
            "lab_only_synthetic_fixture": True,
            "attested_offline_copy": True,
        }
        params.update(overrides)
        return evidence.build_synthetic_csv_evidence(
            self.source if path is None else path, self.stage,
            self.draft() if draft is None else draft, **params
        )

    def replay(self, bundle=None, draft=None, path=None, **overrides):
        if draft is None:
            draft = self.draft()
        if bundle is None:
            bundle = self.build(draft)
        params = {
            "lab_only_synthetic_fixture": True,
            "attested_offline_copy": True,
        }
        params.update(overrides)
        return evidence.verify_synthetic_csv_evidence(
            bundle, self.source if path is None else path, self.stage,
            draft, **params
        )

    def denied(self, code, fn, *args, **kwargs):
        with self.assertRaises(evidence.CsvLabEvidenceRefused) as failure:
            fn(*args, **kwargs)
        self.assertEqual(str(failure.exception), code)
        self.assertNotIn("FAKE_FIRST", str(failure.exception))
        self.assertNotIn(str(self.source), str(failure.exception))

    def test_01_replay_matches_identical_fake_source(self):
        d = self.draft()
        b = self.build(d)
        r = self.replay(b, d)
        self.assertTrue(r.lab_replay_matched)
        self.assertEqual(r.evidence_sha256, b.evidence_sha256)
        self.assertFalse(r.clinical_import_permitted)

    def test_02_count_only_no_phi(self):
        before = self.source.read_bytes()
        b = self.build()
        self.assertEqual(b.patient_row_count, 15)
        self.assertEqual(b.candidate_row_count, 15)
        self.assertEqual(b.critical_row_count, 0)
        self.assertEqual(b.unmapped_column_count, 1)
        self.assertEqual(before, self.source.read_bytes())
        out = str(b.public_dict())
        self.assertNotIn("FAKE_FIRST_", out)
        self.assertNotIn("FAKE_LAST_", out)
        self.assertNotIn("FAKE00001", out)
        self.assertNotIn("ancien_id", out)
        self.assertNotIn(str(self.source), out)

    def test_03_bundle_is_deterministic(self):
        self.assertEqual(self.build(), self.build())

    def test_04_no_vendor_or_clinical_approval(self):
        b = self.build()
        self.assertFalse(b.source_provenance_verified)
        self.assertFalse(b.vendor_format_compatible)
        self.assertFalse(b.real_clinical_target_verified)
        self.assertFalse(b.backup_restore_verified)
        self.assertFalse(b.mapping_human_approved)
        self.assertFalse(b.import_permitted)
        self.assertEqual(b.target_rows_written, 0)
        self.assertIsNone(b.target_collisions)

    def test_05_digest_is_64_lower_hex(self):
        b = self.build()
        self.assertRegex(b.evidence_sha256, r"^[a-f0-9]{64}$")
        self.assertRegex(b.report_sha256, r"^[a-f0-9]{64}$")

    def test_06_different_explicit_mapping_has_distinct_digest(self):
        self.assertNotEqual(
            self.build(self.draft()).evidence_sha256,
            self.build(self.draft(swapped=True)).evidence_sha256,
        )

    def test_07_swapped_mapping_replay_refused(self):
        original = self.build()
        self.denied(
            "EVIDENCE_REPLAY_MISMATCH", self.replay,
            original, self.draft(swapped=True),
        )

    def test_08_mutated_source_fails_closed(self):
        d = self.draft()
        b = self.build(d)
        self.rows[1][1] = "FAKE_REWRITTEN_NAME"
        self.write()
        self.denied("MAPPING_SOURCE_OR_TARGET_CHANGED", self.replay, b, d)

    def test_09_bundle_digest_tamper_rejected(self):
        b = self.build()
        self.denied("EVIDENCE_BUNDLE_TAMPERED", self.replay,
                    replace(b, evidence_sha256="0" * 64))

    def test_10_row_count_tamper_rejected(self):
        b = self.build()
        self.denied("EVIDENCE_BUNDLE_TAMPERED", self.replay,
                    replace(b, patient_row_count=500))

    def test_11_report_hash_tamper_rejected(self):
        b = self.build()
        self.denied("EVIDENCE_BUNDLE_TAMPERED", self.replay,
                    replace(b, report_sha256="0" * 64))

    def test_12_mapping_hash_tamper_rejected(self):
        b = self.build()
        self.denied("EVIDENCE_BUNDLE_TAMPERED", self.replay,
                    replace(b, mapping_profile_sha256="0" * 64))

    def test_13_target_schema_hash_tamper_rejected(self):
        b = self.build()
        self.denied("EVIDENCE_BUNDLE_TAMPERED", self.replay,
                    replace(b, synthetic_target_schema_sha256="0" * 64))

    def test_14_vendor_provenance_claim_denied(self):
        self.denied("CLINICAL_OR_VENDOR_APPROVAL_FORBIDDEN", self.replay,
                    replace(self.build(), source_provenance_verified=True))

    def test_15_vendor_compatibility_claim_denied(self):
        self.denied("CLINICAL_OR_VENDOR_APPROVAL_FORBIDDEN", self.replay,
                    replace(self.build(), vendor_format_compatible=True))

    def test_16_mapping_approval_claim_denied(self):
        self.denied("CLINICAL_OR_VENDOR_APPROVAL_FORBIDDEN", self.replay,
                    replace(self.build(), mapping_human_approved=True))

    def test_17_import_permission_claim_denied(self):
        self.denied("CLINICAL_OR_VENDOR_APPROVAL_FORBIDDEN", self.replay,
                    replace(self.build(), import_permitted=True))

    def test_18_target_write_claim_denied(self):
        self.denied("CLINICAL_OR_VENDOR_APPROVAL_FORBIDDEN", self.replay,
                    replace(self.build(), target_rows_written=1))

    def test_19_target_collision_fake_zero_denied(self):
        self.denied("CLINICAL_OR_VENDOR_APPROVAL_FORBIDDEN", self.replay,
                    replace(self.build(), target_collisions=0))

    def test_20_backup_restore_claim_denied(self):
        self.denied("CLINICAL_OR_VENDOR_APPROVAL_FORBIDDEN", self.replay,
                    replace(self.build(), backup_restore_verified=True))

    def test_21_clinical_target_claim_denied(self):
        self.denied("CLINICAL_OR_VENDOR_APPROVAL_FORBIDDEN", self.replay,
                    replace(self.build(), real_clinical_target_verified=True))

    def test_22_wrong_evidence_type_denied(self):
        self.denied("EVIDENCE_BUNDLE_REQUIRED", self.replay, object())

    def test_23_wrong_evidence_digest_shape_denied(self):
        self.denied("INVALID_EVIDENCE_FINGERPRINT", self.replay,
                    replace(self.build(), evidence_sha256="bad"))

    def test_24_missing_explicit_lab_gate_denied(self):
        self.denied("LAB_SYNTHETIC_ONLY", self.build,
                    lab_only_synthetic_fixture=False)

    def test_25_integer_lab_gate_denied(self):
        self.denied("LAB_SYNTHETIC_ONLY", self.build,
                    lab_only_synthetic_fixture=1)

    def test_26_missing_offline_attestation_denied(self):
        self.denied("OFFLINE_COPY_ATTESTATION_REQUIRED", self.build,
                    attested_offline_copy=False)

    def test_27_outside_staging_denied(self):
        other = self.root / "outside.csv"
        other.write_bytes(self.source.read_bytes())
        self.denied("OUTSIDE_STAGING_ROOT", self.build, path=other)

    def test_28_symlink_denied_if_supported(self):
        link = self.stage / "alias.csv"
        try:
            link.symlink_to(self.source)
        except (OSError, NotImplementedError):
            self.skipTest("OS symlinks disabled")
        self.addCleanup(link.unlink, missing_ok=True)
        self.denied("SYMLINK_FORBIDDEN", self.build, path=link)

    def test_29_formula_in_unmapped_column_refused(self):
        self.rows[0][4] = "=HYPERLINK(1)"
        self.write()
        self.denied("UNSAFE_CSV_CELL", self.build)

    def test_30_ambiguous_date_is_evidence_not_approval(self):
        self.rows[0][3] = "01/02/2010"
        self.write()
        b = self.build()
        self.assertEqual(b.critical_row_count, 1)
        self.assertEqual(b.candidate_row_count, 14)
        self.assertFalse(b.import_permitted)
        self.assertTrue(self.replay(b).lab_replay_matched)

    def test_31_duplicate_source_id_is_counted_not_merged(self):
        self.rows[1][0] = self.rows[0][0]
        self.write()
        b = self.build()
        self.assertEqual(b.critical_row_count, 1)
        self.assertFalse(b.vendor_format_compatible)

    def test_32_empty_csv_denied(self):
        self.write(rows=[])
        self.denied("EMPTY_PATIENT_CSV", self.build)

    def test_33_unrecognized_source_schema_denied(self):
        self.write(headers=["ancien_id", "prenom", "nom", "naissance", "pwd"])
        self.denied("UNSAFE_CSV_HEADER", self.build)

    def test_34_report_mutation_changes_evidence_digest(self):
        d = self.draft()
        real = lab.simulate_synthetic_patient_csv
        normal = real(
            self.source, self.stage, d,
            lab_only_synthetic_fixture=True, attested_offline_copy=True,
        )
        with patch.object(evidence, "simulate_synthetic_patient_csv",
                          return_value=replace(normal, warnings=("OTHER_WARNING",))):
            different = self.build(d)
        self.assertNotEqual(different.report_sha256, self.build(d).report_sha256)

    def test_35_invalid_fake_report_with_write_claim_denied(self):
        d = self.draft()
        normal = lab.simulate_synthetic_patient_csv(
            self.source, self.stage, d, lab_only_synthetic_fixture=True,
            attested_offline_copy=True,
        )
        with patch.object(evidence, "simulate_synthetic_patient_csv",
                          return_value=replace(normal, target_rows_written=1)):
            self.denied("SIMULATION_AUTHORIZATION_FORBIDDEN", self.build, d)

    def test_36_invalid_fake_report_counts_denied(self):
        d = self.draft()
        normal = lab.simulate_synthetic_patient_csv(
            self.source, self.stage, d, lab_only_synthetic_fixture=True,
            attested_offline_copy=True,
        )
        with patch.object(evidence, "simulate_synthetic_patient_csv",
                          return_value=replace(normal, accepted_candidate_rows=400)):
            self.denied("INVALID_SIMULATION_COUNTS", self.build, d)


if __name__ == "__main__":
    unittest.main()
