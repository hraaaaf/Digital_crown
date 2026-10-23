"""J11B tests: synthetic fingerprints only; no actual academic case IDs or images."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import tempfile
import unittest

p=Path(__file__).with_name("lot05_j11b_private_candidate_pair_roster.py")
spec=importlib.util.spec_from_file_location("j11b_unit",p)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def fake(split, token, dh, mirror):
    return (split, token, mod.J11A.Fingerprint(split, "byte_"+token,
        "pixel_"+token, dh, mirror))


class TestPrivateCandidateRoster(unittest.TestCase):
    def test_aggregate_pair_selection_does_not_count_same_split(self):
        items=[fake("train","1",0,255),fake("train","2",0,255),
               fake("val","3",0,255)]
        pairs=mod.candidates(items)
        self.assertEqual(len(pairs),2)
        self.assertTrue(all(x["source_split_a"]!=x["source_split_b"] for x in pairs))

    def test_mirror_pair_and_all_records_unreviewed(self):
        items=[fake("train","111",0,255),
               fake("test","222",255,0)]
        selected=mod.candidates(items)
        self.assertEqual(len(selected),1)
        self.assertEqual(selected[0]["dhash_hamming_mirrored"],0)
        self.assertEqual(selected[0]["expert_decision"],"UNREVIEWED")
        self.assertFalse(selected[0]["same_patient_or_exam_proven"])

    def test_disparate_pair_not_candidate(self):
        items=[fake("train","111",0,0),fake("val","222",(1<<64)-1,(1<<64)-1)]
        self.assertEqual(mod.candidates(items),[])

    def test_existing_manifest_refused(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            p=root/"manifest.json"
            p.write_text("{}")
            with self.assertRaisesRegex(mod.LocalReviewError,"must_be_new_json"):
                mod._safe_output(p,(root/"images",root/"labels"))

    def test_review_json_inside_git_refused(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            (root/".git").mkdir()
            output=root/"my_review.json"
            with self.assertRaisesRegex(mod.LocalReviewError,"git_checkout"):
                mod._safe_output(output,(root/"images",root/"labels"))

    def test_review_within_source_refused(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            source=root/"source"
            source.mkdir()
            with self.assertRaisesRegex(mod.LocalReviewError,"overlaps_source"):
                mod._safe_output(source/"review.json",(source,root/"other"))


if __name__=="__main__":
    unittest.main()
