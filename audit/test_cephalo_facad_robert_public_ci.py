"""Synthetic-only tests: no actual Robert coordinates/values in public CI."""
from __future__ import annotations
import copy
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from audit import cephalo_facad_robert_public_ci as run


def fake_case():
    points = {
        "Ii": [0, 0], "Iia": [1, 2], "Is": [2, -1], "Isa": [1, -3],
        "A": [0, -1], "Pog": [1, 3], "Go": [-4, 0], "Me": [4, 0],
        "N": [0, -5],
    }
    points.update({f"FAKE_{i}": [i + 1, i + 2] for i in range(21)})
    linear = {"Convexity", "Ii to A-Pog", "Is to A-Pog", "Li-EL", "Upper lip len"}
    values32 = {
        label: {"value": 0.0, "unit": "mm" if label in linear else "°"}
        for label in run.dc.FACTOR_32
    }
    return {
        "schema_version": "FACAD_ROBERT_PUBLIC_EDUCATIONAL_GEOMETRY_V1",
        "source_proof_level": "OPERATOR_ONLY_GUI_NOT_INDEPENDENTLY_VERIFIED",
        "coordinate_system": "FACAD_EXPORTED_ORIGINAL_SAGITTAL_VERTICAL_MM_UNSPECIFIED_ORIENTATION",
        "coordinate_rounding_mm": 0.1,
        "clinical_authority": False,
        "clinical_parity_proven": False,
        "signed_measurements_may_not_be_compared_without_FH": True,
        "points_mm": points,
        "facad_values": {
            "32F": values32,
            "13F": {k: copy.deepcopy(values32[k]) for k in run.dc.FACTOR_13},
        },
    }


class PublicExampleContractTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fake_case()

    def test_still_calls_real_dc_math_only_and_abstains_clinically(self):
        result = run.validate_fixture(self.fixture)
        self.assertEqual(result["dc_geometry_helpers_executed"], 4)
        self.assertEqual(result["clinical_numeric_parities_verified"], 0)
        self.assertFalse(result["dc_full_runtime_adapter_executed"])
        self.assertTrue(result["clinical_no_go"])

    def test_absent_fixture_is_explicitly_not_executed(self):
        with tempfile.TemporaryDirectory() as folder:
            absent = Path(folder) / "not-uploaded.json"
            with patch.object(run, "FIXTURE", absent):
                with patch("sys.argv", ["public-demo"]), redirect_stdout(io.StringIO()) as out:
                    self.assertEqual(run.main(), 0)
            self.assertIn("NOT_EXECUTED_FIXTURE_MISSING", out.getvalue())

    def test_required_fixture_absent_fails_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            absent = Path(folder) / "not-uploaded.json"
            with patch.object(run, "FIXTURE", absent):
                with patch("sys.argv", ["public-demo", "--require-fixture"]), redirect_stdout(io.StringIO()) as out:
                    self.assertEqual(run.main(), 2)
            self.assertIn("FAIL_CLOSED_", out.getvalue())

    def test_clinical_promotion_disallowed(self):
        self.fixture["clinical_authority"] = True
        with self.assertRaisesRegex(ValueError, "unsafe"):
            run.validate_fixture(self.fixture)

    def test_sign_gates_disallowed_to_remove(self):
        self.fixture["signed_measurements_may_not_be_compared_without_FH"] = False
        with self.assertRaisesRegex(ValueError, "unsafe"):
            run.validate_fixture(self.fixture)

    def test_bad_point_or_count_disallowed(self):
        del self.fixture["points_mm"]["Ii"]
        with self.assertRaises(ValueError):
            run.validate_fixture(self.fixture)

    def test_wrong_shared_vendor_number_disallowed(self):
        self.fixture["facad_values"]["13F"]["ILi/A-Pog"]["value"] = 1
        with self.assertRaisesRegex(ValueError, "shared vendor values disagree"):
            run.validate_fixture(self.fixture)

    def test_changed_unit_disallowed(self):
        self.fixture["facad_values"]["32F"]["Li-EL"]["unit"] = "px"
        with self.assertRaisesRegex(ValueError, "unit"):
            run.validate_fixture(self.fixture)

    def test_wrong_reference_frame_disallowed(self):
        self.fixture["coordinate_system"] = "CONFIRMED_DC_FRAME"
        with self.assertRaisesRegex(ValueError, "unverified frame"):
            run.validate_fixture(self.fixture)

    def test_synthetic_file_cannot_impersonate_pinned_public_case(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "fake.json"
            path.write_text(json.dumps(self.fixture), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "hash"):
                run.read_checked_fixture(path)


if __name__ == "__main__":
    unittest.main()
