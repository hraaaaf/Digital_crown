"""Synthetic NEGATIVE and staging-contract tests; NEVER real FACAD or parity proof."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from audit.cephalo_facad_robert_evidence_stage import (
    MENUS, ROBERT_SHA256, TARGETS, VERSION, stage,
)
from audit.cephalo_lot08_facad_parity_validate import validate_manifest


class PrivateFacadStageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="synthetic-facad-no-patient-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.intake = self.root / "intake"
        self.intake.mkdir()
        self.output = self.root / "PRIVATE-OUTPUT"
        self.config = {
            "official_robert_sha256": ROBERT_SHA256,
            "facad_version": VERSION,
            "same_trace_case_id": "SYNTHETIC_TRACE_ONLY",
            "authorized_facad_use_confirmed": True,
            "same_lateral_tracing_confirmed": True,
            "exports": [],
        }
        for profile, prefix in TARGETS.items():
            for kind, menu in MENUS.items():
                name = f"SYNTHETIC_{prefix}_{kind}.txt"
                (self.intake / name).write_bytes(
                    f"FAKE_FIXTURE_{prefix}_{kind}_NOT_FACAD\n".encode()
                )
                self.config["exports"].append({
                    "profile_target_id": profile,
                    "artifact_kind": kind,
                    "file": name,
                    "observed_at": "2026-10-19T12:00:00+01:00",
                    "vendor_menu": menu,
                    "marker_positions_content_verified": kind == "MARKER_POSITIONS",
                })
        self.input_file = self.intake / "SYNTHETIC_INTAKE.json"

    def _attempt(self) -> Path:
        self.input_file.write_text(json.dumps(self.config), encoding="utf-8")
        return stage(self.input_file, self.output)

    def _rejected(self) -> None:
        with self.assertRaises((ValueError, OSError)):
            self._attempt()
        self.assertFalse(self.output.exists(), "failed staging must not leave evidence")

    def test_positive_synthetic_does_not_claim_numeric_parity(self) -> None:
        path = self._attempt()
        self.assertTrue(path.is_file())
        manifest = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["status"], "DIRECT_EVIDENCE_PARTIAL")
        self.assertEqual(len(manifest["evidence_records"]), 6)
        self.assertEqual(manifest["parity_rows"], [])
        self.assertEqual(
            {p["observation_status"] for p in manifest["profiles"]}, {"PARTIAL"}
        )
        self.assertEqual(validate_manifest(manifest, self.output), [])
        self.assertEqual(
            {r["same_trace_case_id"] for r in manifest["evidence_records"]},
            {"SYNTHETIC_TRACE_ONLY"},
        )

    def test_empty_or_missing_file_fails_closed(self) -> None:
        (self.intake / self.config["exports"][0]["file"]).write_bytes(b"")
        self._rejected()

    def test_missing_one_export_fails_closed(self) -> None:
        self.config["exports"].pop()
        self._rejected()

    def test_duplicate_export_pair_fails_closed(self) -> None:
        self.config["exports"][1]["profile_target_id"] = self.config["exports"][0]["profile_target_id"]
        self.config["exports"][1]["artifact_kind"] = self.config["exports"][0]["artifact_kind"]
        self._rejected()

    def test_incorrect_vendor_menu_fails_closed(self) -> None:
        self.config["exports"][2]["vendor_menu"] = "Marker Positions"
        self._rejected()

    def test_unverified_object_values_marker_coverage_fails_closed(self) -> None:
        self.config["exports"][2]["marker_positions_content_verified"] = False
        self._rejected()

    def test_unverified_license_fails_closed(self) -> None:
        self.config["authorized_facad_use_confirmed"] = False
        self._rejected()

    def test_unverified_same_tracing_fails_closed(self) -> None:
        self.config["same_lateral_tracing_confirmed"] = False
        self._rejected()

    def test_wrong_original_robert_hash_fails_closed(self) -> None:
        self.config["official_robert_sha256"] = "0" * 64
        self._rejected()

    def test_wrong_version_fails_closed(self) -> None:
        self.config["facad_version"] = "3.13"
        self._rejected()

    def test_no_timezone_fails_closed(self) -> None:
        self.config["exports"][0]["observed_at"] = "2026-10-19T12:00:00"
        self._rejected()

    def test_parent_path_traversal_fails_closed(self) -> None:
        self.config["exports"][0]["file"] = "../outside.txt"
        self._rejected()

    def test_duplicate_same_file_fails_closed(self) -> None:
        self.config["exports"][1]["file"] = self.config["exports"][0]["file"]
        self._rejected()

    def test_secret_extra_field_fails_closed(self) -> None:
        self.config["license_secret"] = "never-save-this"
        self._rejected()

    def test_symlink_source_fails_closed(self) -> None:
        target = self.intake / self.config["exports"][0]["file"]
        link = self.intake / "symlink-export.txt"
        try:
            link.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("Symlink privileges unavailable on this platform")
        self.config["exports"][0]["file"] = link.name
        self._rejected()

    def test_existing_private_output_must_not_be_overwritten(self) -> None:
        self.output.mkdir()
        sentinel = self.output / "DO_NOT_OVERWRITE.txt"
        sentinel.write_text("ORIGINAL PRIVATE FILE", encoding="utf-8")
        with self.assertRaises(ValueError):
            self._attempt()
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "ORIGINAL PRIVATE FILE")
        self.assertEqual(list(self.output.iterdir()), [sentinel])


if __name__ == "__main__":
    unittest.main()
