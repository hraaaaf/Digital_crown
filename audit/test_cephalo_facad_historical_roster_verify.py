"""Synthetic-only archive-verifier regression tests; never downloads FACAD files."""
from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from audit import cephalo_facad_historical_roster_verify as v


def dummy_capture(profile: str, rows: list[str], heading_count: int) -> bytes:
    items = [
        "ControlType.Window|Edit Cephalometric Analysis|AUTOID=|ENABLED=True|OFFSCREEN=False|B=1,1,1,1",
        f"ControlType.Edit|{profile}|AUTOID=1022|ENABLED=True|OFFSCREEN=False|B=1,1,1,1",
        "ControlType.DataGrid||AUTOID=1317|ENABLED=True|OFFSCREEN=False|B=1,1,1,1",
        "ControlType.Header|Header|AUTOID=Header",
    ]
    cells = [("SECTION_" + str(i), "Heading") for i in range(heading_count)]
    cells += [(name, "Angle4p") for name in rows]
    for name, kind in cells:
        items.append(f"ControlType.DataItem|{name}|AUTOID=|ENABLED=True|OFFSCREEN=False|B=1,1,1,1")
        for val in [name, kind, "N", "A", "B", "Pog", "1±1", "", ""]:
            items.append(f"ControlType.Text|{val}|AUTOID=|ENABLED=True|OFFSCREEN=False|B=1,1,1,1")
    items.append("ControlType.DataGrid||AUTOID=999|ENABLED=True|OFFSCREEN=False|B=1,1,1,1")
    return ("\r\n".join(items) + "\r\n").encode()


class HistoricalRosterArchiveTests(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.TemporaryDirectory(prefix="synthetic-facad-historic-")
        self.addCleanup(self.work.cleanup)
        self.folder = Path(self.work.name)
        self.real_roster = json.loads(v.SCHEMA.read_text(encoding="utf-8"))
        self.roster = copy.deepcopy(self.real_roster)
        self.sources = {}
        for p in self.roster["profile_rosters"]:
            target = p["profile_target_id"]
            name = "Ricketts (32 F)" if "32F" in target else "Ricketts (13 F)"
            raw = dummy_capture(name, [q["facad_label"] for q in p["ordered_factor_labels"]],
                                6 if "32F" in target else 4)
            with ZipFile(self.folder / (("32F" if "32F" in target else "13F") + ".zip"), "w") as z:
                z.writestr(p["source_uia_member_name"], raw)
            path = self.folder / (("32F" if "32F" in target else "13F") + ".zip")
            p["source_artifact_zip_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            p["source_uia_member_sha256"] = hashlib.sha256(raw).hexdigest()
            p["source_uia_member_byte_count"] = len(raw)
            self.sources[target] = path

    def test_pair_verifies_only_gui_roster(self):
        result = v.verify_pair(self.roster, self.sources)
        self.assertEqual(result["total_ordered_factor_definitions"], 45)
        self.assertEqual(result["numeric_parity_observed"], 0)
        self.assertEqual(result["authentic_vendor_numeric_exports_checked"], 0)
        self.assertEqual([x["vendor_gui_definitions_verified"] for x in result["records"]], [32, 13])
        self.assertTrue(result["clinical_no_go"])

    def test_baseline_45_not_numeric_exports(self):
        self.assertEqual(sum(x["observed_factor_count"] for x in self.real_roster["profile_rosters"]), 45)
        self.assertEqual(sum(len(x["ordered_factor_labels"]) for x in self.real_roster["profile_rosters"]), 45)
        self.assertFalse(self.real_roster["scientific_authority"])

    def test_refuses_wrong_archive_sha(self):
        first = self.roster["profile_rosters"][0]
        first["source_artifact_zip_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "ZIP SHA256"):
            v.verify_pair(self.roster, self.sources)

    def test_refuses_wrong_uia_sha(self):
        self.roster["profile_rosters"][0]["source_uia_member_sha256"] = "1" * 64
        with self.assertRaisesRegex(ValueError, "UIA member SHA256"):
            v.verify_pair(self.roster, self.sources)

    def test_refuses_swapped_archive_profile(self):
        a, b = list(self.sources)
        self.sources[a], self.sources[b] = self.sources[b], self.sources[a]
        with self.assertRaisesRegex(ValueError, "ZIP SHA256"):
            v.verify_pair(self.roster, self.sources)

    def test_refuses_modified_order_even_if_count_same(self):
        rows = self.roster["profile_rosters"][0]["ordered_factor_labels"]
        rows[0], rows[1] = rows[1], rows[0]
        with self.assertRaisesRegex(ValueError, "factor name/order"):
            v.verify_pair(self.roster, self.sources)

    def test_refuses_header_only_fake_data(self):
        text = dummy_capture("Ricketts (13 F)", [], 4).decode()
        row, count = v.parse_editor(text, "Ricketts (13 F)")
        self.assertEqual(count, 4)
        self.assertEqual(row, [])

    def test_first_grid_only_not_landmark_grid(self):
        text = dummy_capture("Ricketts (13 F)", ["Facial axis"], 1).decode()
        text += "ControlType.DataItem|Injected|AUTOID=|ENABLED=True|OFFSCREEN=False|B=1,1,1,1\n"
        row, count = v.parse_editor(text, "Ricketts (13 F)")
        self.assertEqual(row, [{"order": 1, "facad_label": "Facial axis"}])
        self.assertEqual(count, 1)

    def test_exact_editor_profile_identity(self):
        text = dummy_capture("Ricketts (13 F)", ["Facial axis"], 0).decode()
        with self.assertRaisesRegex(ValueError, "profile identity"):
            v.parse_editor(text, "Ricketts (32 F)")

    def test_bad_status_or_false_claim_fails(self):
        self.roster["status"] = "DIRECT_PARITY_OBSERVED"
        with self.assertRaisesRegex(ValueError, "historical source-lock"):
            v.verify_pair(self.roster, self.sources)

    def test_missing_profile_or_wrong_name_in_zip_fails(self):
        del self.sources[next(iter(self.sources))]
        with self.assertRaisesRegex(ValueError, "pairing mismatch"):
            v.verify_pair(self.roster, self.sources)

    def test_real_zip_not_embedded_in_repository(self):
        tree = v.ROOT
        self.assertFalse((tree / "facad-history-11586908104.zip").exists())
        self.assertFalse((tree / "facad-history-11587723671.zip").exists())


if __name__ == "__main__":
    unittest.main()
