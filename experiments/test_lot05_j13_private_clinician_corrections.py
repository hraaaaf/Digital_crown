"""LOT05 J13: synthetic-only tests; never contains clinical cases or media."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

P = Path(__file__).with_name("lot05_j13_private_clinician_corrections.py")
SPEC = importlib.util.spec_from_file_location("j13_unit", P)
assert SPEC and SPEC.loader
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def fixture(root):
    records = []
    for split, expected in M.SPLITS.items():
        folder = root / split
        folder.mkdir()
        for n in range(expected):
            stem = str({"train":1000,"val":3000,"test":4000}[split] + n)
            (folder/(stem+".txt")).write_text(
                "0 0.20 0.30 0.04 0.12\n16 0.55 0.70 0.04 0.12\n",
                encoding="utf8")
            records.append((split,stem))
    flagged = records[:25] + records[266:269]
    for i,(split,stem) in enumerate(flagged):
        p = root/split/(stem+".txt")
        repeated = ("4 0.41 0.40 0.04 0.15\n4 0.41 0.40 0.04 0.15\n"
                    if i==27 else
                    "4 0.41 0.40 0.04 0.15\n4 0.48 0.41 0.04 0.15\n")
        p.write_text(p.read_text()+repeated)
        if i<3:
            p.write_text(p.read_text()+
                         "6 0.58 0.40 0.04 0.15\n6 0.65 0.41 0.04 0.15\n")
    changes = []
    for i,(split,stem) in enumerate(flagged[:17]):
        changes.append({"case":i+1,"split":split,"stem":stem,
            "from_fdi":"15","to_fdi":"16",
            "expected_bbox":[.41,.40,.04,.15]})
        if i<2:
            changes.append({"case":i+1,"split":split,"stem":stem,
                "from_fdi":"17","to_fdi":"18",
                "expected_bbox":[.58,.40,.04,.15]})
    manifest = {"schema":M.MANIFEST_SCHEMA, "source_commit":M.PIN,
        "reviewed_cases":28,"reviewed_pairs":6,"relabels":changes,
        "exact_duplicate_deletions":[{
            "case":28,"split":flagged[27][0],"stem":flagged[27][1],
            "fdi":"15","expected_bbox":[.41,.40,.04,.15]}],
        "unresolved":[{"case":k,"reason":"class_unknown"}
                      for k in range(18,28)]}
    return manifest,flagged


class J13SyntheticTest(unittest.TestCase):
    def test_standard_fdi_indices(self):
        self.assertEqual(len(M.FDI),32)
        self.assertEqual([M.FDI[x] for x in ("11","18","21","38","48")],
                         [0,7,8,23,31])

    def test_box_match_tolerance(self):
        self.assertTrue(M.closebox([.5,.6,.04,.1],[.5,.6,.04,.1]))
        self.assertFalse(M.closebox([.5,.6,.04,.1],[.6,.6,.04,.1]))

    def test_missing_source_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(M.J13Error):
                M.inventory_preflight(Path(d))

    def test_synthetic_whole_corpus_census(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            fixture(root)
            result=M.inventory_preflight(root)
            self.assertEqual((result["source_label_files"],
                             result["flagged_images"],
                             result["extra_same_fdi_labels"],
                             result["exact_duplicate_pairs"]), (333,28,31,1))
            self.assertEqual(result["by_split"]["train"]["flagged_images"],25)

    def test_manifest_exact_count_validation(self):
        with tempfile.TemporaryDirectory() as d:
            manifest,_=fixture(Path(d))
            M.validate_manifest(manifest)
            self.assertEqual(len(manifest["relabels"]),19)

    def test_specific_row_only_relabels_and_original_unchanged(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);manifest,flagged=fixture(root)
            sample=root/flagged[0][0]/(flagged[0][1]+".txt")
            before=sample.read_text()
            result,replacements=M.evaluate_private(root,manifest)
            self.assertEqual(result["clinician_relabels_safe"],19)
            self.assertEqual(result["case_files_with_target_collision"],0)
            self.assertEqual(before,sample.read_text())
            self.assertIn("5 0.41 0.40 0.04 0.15",replacements[flagged[0]])
            self.assertIn("7 0.58 0.40 0.04 0.15",replacements[flagged[0]])

    def test_exact_dedupe_one_and_only_one(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);manifest,flagged=fixture(root)
            _,changed=M.evaluate_private(root,manifest)
            before=(root/flagged[27][0]/(flagged[27][1]+".txt")).read_text()
            after=changed[flagged[27]]
            self.assertEqual(before.count("4 0.41 0.40 0.04 0.15"),2)
            self.assertEqual(after.count("4 0.41 0.40 0.04 0.15"),1)

    def test_wrong_expected_box_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);manifest,_=fixture(root)
            manifest["relabels"][0]["expected_bbox"]=[.45,.4,.04,.15]
            with self.assertRaises(M.J13Error):
                M.evaluate_private(root,manifest)

    def test_existing_destination_class_blocks_relabel(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);manifest,flagged=fixture(root)
            first=root/flagged[0][0]/(flagged[0][1]+".txt")
            first.write_text(first.read_text()+"5 0.75 0.40 0.04 0.15\n")
            result,changed=M.evaluate_private(root,manifest)
            self.assertGreater(result["clinician_relabels_blocked_by_existing_target_class"],0)
            self.assertNotIn(flagged[0],changed)

    def test_preexisting_private_destination_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/"source";source.mkdir()
            manifest,_=fixture(source)
            _,changes=M.evaluate_private(source,manifest)
            output=Path(d)/"private";output.mkdir()
            with self.assertRaises(M.J13Error):
                M.stage_private(source,output,changes)

    def test_local_private_staging_all_333_preserves_source(self):
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/"source";source.mkdir()
            manifest,flagged=fixture(source)
            before=(source/flagged[0][0]/(flagged[0][1]+".txt")).read_text()
            _,changed=M.evaluate_private(source,manifest)
            target=Path(d)/"stage"
            M.stage_private(source,target,changed)
            self.assertEqual(len(list(target.glob("*/*.txt"))),333)
            self.assertEqual(before,(source/flagged[0][0]/(flagged[0][1]+".txt")).read_text())
            self.assertNotEqual(before,(target/flagged[0][0]/(flagged[0][1]+".txt")).read_text())
            self.assertEqual(target.stat().st_mode & 0o777,0o700)
            self.assertEqual(next(target.glob("*/*.txt")).stat().st_mode & 0o777,0o600)

    def test_staging_under_source_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            source=Path(d);manifest,_=fixture(source)
            _,changed=M.evaluate_private(source,manifest)
            with self.assertRaises(M.J13Error):
                M.stage_private(source,source/"new",changed)

    def test_invalid_cli_emits_only_safe_json(self):
        with tempfile.TemporaryDirectory() as d:
            r=subprocess.run([sys.executable,str(P),"--labels-dir",d,
                              "--stage-private",str(Path(d)/"private")],
                              capture_output=True,text=True)
            self.assertEqual(r.returncode,1)
            self.assertEqual(json.loads(r.stdout),
                {"schema":M.SCHEMA,"status":"FAIL_CLOSED_NO_MEDIA_OR_IDENTIFIERS"})
            self.assertEqual(r.stderr,"")

    def test_read_only_preflight_preserves_source(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);_,flagged=fixture(root)
            file=root/flagged[0][0]/(flagged[0][1]+".txt")
            before=file.read_bytes()
            self.assertFalse(M.inventory_preflight(root)["source_modified"])
            self.assertEqual(file.read_bytes(),before)


if __name__=="__main__":
    unittest.main()
