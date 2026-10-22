"""J10L: provenance cannot be self-certified; synthetics check 32 class wiring.

No patient images, downloaded datasets, or model training in this test suite.
"""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]
READINESS = Path(__file__).with_name("lot05_j10l_fdi_training_readiness.py")
TRAINING = Path(__file__).with_name("lot05_j10l_dfine_synthetic_fdi_training.py")
WORKFLOW = ROOT / ".github/workflows/lot05-j10l-fdi-provenance-synthetic-train.yml"

spec = importlib.util.spec_from_file_location("j10l_gate", READINESS)
assert spec and spec.loader
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def source():
    return json.loads(gate.AUDIT.read_text(encoding="utf-8"))


class DatasetGateUnitTests(unittest.TestCase):
    def test_provenance_gate_fails_closed_on_all_eight_sources(self):
        out = gate.audit_dataset_manifest(source())
        self.assertEqual(out["status"], "REAL_DATA_TRAINING_BLOCKED_SYNTHETIC_ONLY")
        self.assertEqual(out["dataset_candidates"], 8)
        self.assertEqual(out["permanent_fdi_classes"], list(gate.FDI_32))
        self.assertFalse(out["cloud_image_processing_go"])

    def test_research_dataset_license_badge_never_grants_commercial_use(self):
        manifest = source()
        row = manifest["candidates"][0]
        self.assertEqual(row["published_license"], "CC BY 4.0")
        row["decision"] = "COMMERCIAL_APPROVED"
        with self.assertRaises(gate.FDITrainingBlock):
            gate.audit_dataset_manifest(manifest)

    def test_genuine_noncommercial_restriction_is_not_ignorable(self):
        manifest = source()
        for target in ("tl-pano-zenodo", "akudental", "sts-2024"):
            x = copy.deepcopy(manifest)
            row = next(r for r in x["candidates"] if r["id"] == target)
            row["decision"] = "HOLD_PROVENANCE"
            with self.subTest(id=target), self.assertRaises(gate.FDITrainingBlock):
                gate.audit_dataset_manifest(x)

    def test_global_cloud_approval_cannot_be_edited_in_json(self):
        for key in ("cloud_processing_approval", "commercial_dataset_go",
                    "independent_patient_rights_review"):
            x = source()
            x[key] = True
            with self.subTest(key=key), self.assertRaises(gate.FDITrainingBlock):
                gate.audit_dataset_manifest(x)

    def test_source_origin_does_not_imply_full_fdi_labels(self):
        x = source()
        tunis = next(row for row in x["candidates"] if row["id"] == "tunisia-brahmi-v3")
        self.assertTrue(tunis["clinical_origin_documented"])
        self.assertFalse(tunis["complete_32_fdi_labels_confirmed"])
        self.assertFalse(tunis["cloud_training_processing_rights_verified"])
        self.assertEqual(tunis["decision"], "HOLD_FDI_LABELS_AND_CLINICAL_RIGHTS")

    def test_32_fdi_order_is_fixed_and_invalid_numbering_fails(self):
        correct = [q*10+i for q in (1,2,3,4) for i in range(1,9)]
        self.assertEqual(gate.validated_fdi_classes(correct), correct)
        for wrong in (correct[:-1], list(reversed(correct)), [0]+correct[1:],
                      list(range(32)), tuple(correct)):
            with self.subTest(wrong=str(wrong)[:50]), self.assertRaises(gate.FDITrainingBlock):
                gate.validated_fdi_classes(wrong)

    def test_missing_or_fabricated_evidence_rejected(self):
        for mutation in ("remove", "duplicate", "file_url", "empty_evidence"):
            x = source()
            if mutation == "remove":
                x["candidates"].pop()
            elif mutation == "duplicate":
                x["candidates"][1]["id"] = x["candidates"][0]["id"]
            elif mutation == "file_url":
                x["candidates"][0]["url"] = "file:///secret/patient.png"
            else:
                x["candidates"][0]["evidence"] = "MIT"
            with self.subTest(mutation=mutation), self.assertRaises(gate.FDITrainingBlock):
                gate.audit_dataset_manifest(x)

    def test_all_verified_flags_cannot_self_authorize(self):
        x = source()
        item = x["candidates"][0]
        for field in gate.PROVENANCE_FIELDS:
            item[field] = True
        with self.assertRaises(gate.FDITrainingBlock):
            gate.audit_dataset_manifest(x)

    def test_user_supplied_real_dataset_path_is_always_blocked(self):
        for mode,path in (("actual_radiographs",""),("synthetic_geometry","/data/panorama"),
                          ("commercial_fdi","/anything")):
            with self.subTest(mode=mode), self.assertRaises(gate.FDITrainingBlock):
                gate.check_research_only_mode(mode, path)
        gate.check_research_only_mode("synthetic_geometry", "")

    def test_synthetic_boxes_cover_all_adult_fdi_ids(self):
        # PIL in the test suite is a generic illustration library, no x-rays.
        sp = importlib.util.spec_from_file_location("j10l_train", TRAINING)
        assert sp and sp.loader
        import sys
        sys.path.insert(0, str(TRAINING.parent))
        try:
            module = importlib.util.module_from_spec(sp)
            sp.loader.exec_module(module)
            image, rows = module.make_synthetic_fdi_grid()
            module.validate_synthetic_rows(rows)
            self.assertEqual(image.size, (640,320))
            self.assertEqual(len(rows), 32)
            self.assertEqual(set(r["fdi"] for r in rows), set(gate.FDI_32))
            rows[-1]["class_index"] = 0
            with self.assertRaises(module.FDITrainingBlock):
                module.validate_synthetic_rows(rows)
        finally:
            sys.path.remove(str(TRAINING.parent))

    def test_actions_never_publish_weights_or_radiographs(self):
        s = WORKFLOW.read_text(encoding="utf-8")
        for text in ("windows-2025", "ubuntu-24.04", "rights-before-training",
                     "synthetic_geometry", "actions/upload-artifact@",
                     "reports/j10l-", "commercial_release_approved"):
            self.assertIn(text,s)
        for bad in ("roboflow download", "gh release create",
                    "vercel deploy", "huggingface-cli upload",
                    "dataset/images", "static/patients"):
            self.assertNotIn(bad,s.lower())
        train = TRAINING.read_text(encoding="utf-8")
        for fragment in ("optimizer.step()", "outputs.loss.backward()",
                         "ignore_mismatched_sizes=True",
                         "model_checkpoint_saved", "commercial_release_approved"):
            self.assertIn(fragment,train)
        self.assertNotIn("model.save_pretrained(",train)
        self.assertNotIn("Image.open(",train)


if __name__ == "__main__":
    unittest.main()
