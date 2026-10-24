"""No vendor runtime/data. Synthetic GUI grids test intra-FACAD source-lock logic."""
from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from audit import cephalo_facad_intravendor_ricketts_validate as d


def synth_grid(profile: str, rows: list[dict], headings: int) -> bytes:
    lines = [
        "ControlType.Window|Edit Cephalometric Analysis|AUTOID=|ENABLED=True|OFFSCREEN=False",
        f"ControlType.Edit|{profile}|AUTOID=1022|ENABLED=True|OFFSCREEN=False",
        "ControlType.DataGrid||AUTOID=1317|ENABLED=True|OFFSCREEN=False",
    ]
    def add(name, kind, args, norm):
        lines.append(f"ControlType.DataItem|{name}|AUTOID=|ENABLED=True|OFFSCREEN=False")
        cols = [name, kind, *args, *([""] * (4 - len(args))), norm, "", ""]
        for c in cols:
            lines.append(f"ControlType.Text|{c}|AUTOID=|ENABLED=True|OFFSCREEN=False")
    for h in range(headings):
        add(f"SECTION_{h}", "Heading", [], "")
    for item in rows:
        add(item["facad_label"], item["calc_type"], item["arg_refs"], item["norm"])
    lines.append("ControlType.DataGrid||AUTOID=1414|ENABLED=True|OFFSCREEN=False")
    return ("\r\n".join(lines) + "\r\n").encode()


class FacadIntraVendorTests(unittest.TestCase):
    def setUp(self):
        self.cross = json.loads(d.CROSSWALK.read_text(encoding="utf-8"))
        self.roster = json.loads(d.ROSTER.read_text(encoding="utf-8"))
        self.temp = tempfile.TemporaryDirectory(prefix="FACAD-SYNTHETIC-NO-VENDOR-")
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)

    def fixtures(self):
        by_label = {row["facad_label"]: row for row in self.cross["pairings"]}
        sources = []
        for profile in self.roster["profile_rosters"]:
            is_13 = "13F" in profile["profile_target_id"]
            n = 13 if is_13 else 32
            rows = []
            for label_row in profile["ordered_factor_labels"]:
                label = label_row["facad_label"]
                item = by_label.get(label)
                rows.append({
                    "facad_label": label,
                    "calc_type": item["calc_type"] if item else "Angle4p",
                    "arg_refs": item["arg_refs"] if item else ["N", "A", "B", "Pog"],
                    "norm": item["norm_13f" if is_13 else "norm_32f"] if item else "1±1",
                })
            contents = synth_grid(f"Ricketts ({n} F)", rows, 4 if is_13 else 6)
            filename = self.folder / f"SYNTHETIC-{n}.zip"
            with ZipFile(filename, "w") as z:
                z.writestr(profile["source_uia_member_name"], contents)
            profile["source_uia_member_sha256"] = hashlib.sha256(contents).hexdigest()
            profile["source_uia_member_byte_count"] = len(contents)
            profile["source_artifact_zip_sha256"] = hashlib.sha256(filename.read_bytes()).hexdigest()
            sources.append(filename)
        return sources

    def test_13_same_vendor_signatures_and_four_distinct_norms(self):
        r = d.validate_schema(self.cross, self.roster)
        self.assertEqual(r["same_displayed_calc_type_and_refs"], 13)
        self.assertEqual(r["different_displayed_norms"], 4)
        self.assertEqual(r["distinct_norm_labels"], ["Facial axis", "ML/FH", "LFH", "Convexity"])
        self.assertEqual(r["numeric_parity_observed"], 0)
        self.assertEqual(r["digital_crown_cross_product_parity_observed"], 0)
        self.assertTrue(r["clinical_no_go"])

    def test_original_archive_checker_accepts_synthetic_matching_signatures(self):
        zip32, zip13 = self.fixtures()
        res = d.verify_original_archives(self.cross, self.roster, zip32, zip13)
        self.assertEqual(res["status"], "HISTORIC_ORIGINAL_ZIP_EDITOR_SIGNATURES_VERIFIED")
        self.assertTrue(res["source_zip_verification_performed"])
        self.assertEqual(res["numeric_parity_observed"], 0)

    def test_original_archive_checker_fails_changed_norm(self):
        zip32, zip13 = self.fixtures()
        self.cross["pairings"][0]["norm_13f"] = "90±99"
        with self.assertRaisesRegex(ValueError, "norm"):
            d.verify_original_archives(self.cross, self.roster, zip32, zip13)

    def test_original_archive_checker_fails_changed_calculation_type(self):
        zip32, zip13 = self.fixtures()
        self.cross["pairings"][0]["calc_type"] = "DistLine"
        with self.assertRaisesRegex(ValueError, "calculation signature mismatch"):
            d.verify_original_archives(self.cross, self.roster, zip32, zip13)

    def test_original_archive_checker_fails_changed_refs(self):
        zip32, zip13 = self.fixtures()
        self.cross["pairings"][0]["arg_refs"] = ["Xi", "Go"]
        with self.assertRaisesRegex(ValueError, "calculation signature mismatch"):
            d.verify_original_archives(self.cross, self.roster, zip32, zip13)

    def test_no_patient_or_vendor_export_data_in_synthetic_ci(self):
        r = d.validate_schema(self.cross, self.roster)
        self.assertFalse(r["source_zip_verification_performed"])
        self.assertTrue(r["clinical_no_go"])

    def test_normalization_crosswalk_cannot_erase_four_differences(self):
        self.cross["pairings"][3]["norm_13f"] = self.cross["pairings"][3]["norm_32f"]
        with self.assertRaisesRegex(ValueError, "norm"):
            d.validate_schema(self.cross, self.roster)

    def test_no_direct_digital_crown_alias_claim(self):
        self.cross["pairings"][5]["digital_crown_geometry_parity_observed"] = True
        with self.assertRaisesRegex(ValueError, "false clinical equivalence"):
            d.validate_schema(self.cross, self.roster)

    def test_no_same_trace_numeric_promotion(self):
        self.cross["pairings"][2]["numeric_same_trace_observed"] = True
        with self.assertRaisesRegex(ValueError, "false clinical equivalence"):
            d.validate_schema(self.cross, self.roster)

    def test_no_silently_unified_norms(self):
        self.cross["safety_rules"]["do_not_unify_norms"] = False
        with self.assertRaisesRegex(ValueError, "safety"):
            d.validate_schema(self.cross, self.roster)

    def test_tampered_13_factor_order_fails(self):
        lines = self.roster["profile_rosters"][1]["ordered_factor_labels"]
        lines[1]["facad_label"], lines[2]["facad_label"] = (
            lines[2]["facad_label"], lines[1]["facad_label"]
        )
        with self.assertRaisesRegex(ValueError, "ordered FACAD 13F"):
            d.validate_schema(self.cross, self.roster)

    def test_wrong_historical_artifact_id_fails(self):
        self.cross["source_artifacts"]["profile_32f"] = 999
        with self.assertRaisesRegex(ValueError, "artifact ID"):
            d.validate_schema(self.cross, self.roster)

    def test_32f_vs_13f_norm_distinct_facial_axis(self):
        x = self.cross["pairings"][0]
        self.assertEqual((x["norm_13f"], x["norm_32f"]), ("90±3.5", "90±3"))
        self.assertEqual((x["calc_type"], x["arg_refs"]), ("Angle4p", ["Pt", "Gn", "N", "Ba"]))

    def test_32f_vs_13f_norm_distinct_lower_facial_height(self):
        x = self.cross["pairings"][3]
        self.assertEqual((x["norm_13f"], x["norm_32f"]), ("45±4", "47±4"))
        self.assertEqual((x["calc_type"], x["arg_refs"]), ("Angle3p", ["Xi", "ANS", "PM"]))


if __name__ == "__main__":
    unittest.main()
