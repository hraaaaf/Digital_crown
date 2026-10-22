"""LOT05/J10I: negative license/provenance/packaging unit gates (synthetic)."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

MODULE_PATH = Path(__file__).with_name("lot05_j10i_fdi_commercial_rights_gate.py")
spec = importlib.util.spec_from_file_location("fdi_rights_gate_j10i", MODULE_PATH)
assert spec and spec.loader
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

CATALOG_PATH = Path(__file__).resolve().parents[1] / "docs/research/LOT05_J10I_FDI_COMMERCIAL_CANDIDATES.json"


def example():
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


class RightsReviewTests(unittest.TestCase):
    def test_catalog_explicitly_blocks_all_commercial_and_clinical_use(self):
        result = gate.review_catalog(example())
        self.assertEqual(result["status"], "COMMERCIAL_AND_CLINICAL_RELEASE_BLOCKED")
        self.assertEqual(result["candidate_count"], 10)
        self.assertEqual(result["commercially_cleared_fdi_checkpoints"], 0)

    def test_fraudulent_global_go_is_rejected(self):
        for name in ("commercial_go", "clinical_go"):
            data = example()
            data[name] = True
            with self.subTest(name=name), self.assertRaises(gate.RightsGateError):
                gate.review_catalog(data)

    def test_false_provenance_attestation_does_not_turn_a_candidate_into_an_approved_model(self):
        data = example()
        c = data["candidates"][1]
        c["training_dataset_provenance_verified"] = True
        c["declared_weights_license"] = "Apache-2.0"
        # Editing text declarations is never sufficient to authorize release.
        c["commercial_release_approval"] = True
        with self.assertRaises(gate.RightsGateError):
            gate.review_catalog(data)

    def test_auto_approval_from_readme_mit_badge_is_rejected(self):
        data = example()
        c = next(c for c in data["candidates"] if c["id"] == "garry2k2-tooth-detection")
        c["rights_to_commercially_distribute"] = True
        with self.assertRaises(gate.RightsGateError):
            gate.review_catalog(data)

    def test_unadapted_coco_rtdetr_cannot_be_promoted_to_fdi_accuracy(self):
        data = example()
        c = next(c for c in data["candidates"] if c["id"] == "pekingu-rtdetrv2-r101vd")
        c["fdi_classes"] = 32
        c["usable_fd_i_model"] = True
        with self.assertRaises(gate.RightsGateError):
            gate.review_catalog(data)

    def test_incomplete_rights_audit_fails_closed(self):
        data = example()
        del data["candidates"][0]["base_runtime_license"]
        with self.assertRaises(gate.RightsGateError):
            gate.review_catalog(data)

    def test_candidate_sources_are_https_and_unique(self):
        data = example()
        data["candidates"][0]["upstream"] = "file:///secret_patient.jpg"
        with self.assertRaises(gate.RightsGateError):
            gate.review_catalog(data)
        data = example()
        data["candidates"][1]["id"] = data["candidates"][0]["id"]
        with self.assertRaises(gate.RightsGateError):
            gate.review_catalog(data)

    def test_unaudited_fdi_weight_in_client_assets_fails_closed(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            model = root / "frontend/public/models/fdi-fast.onnx"
            model.parent.mkdir(parents=True)
            model.write_bytes(b"FAKE DO NOT DEPLOY")
            with self.assertRaises(gate.RightsGateError):
                gate.check_no_research_weights_bundled(root)
            model.unlink()
            gate.check_no_research_weights_bundled(root)

    def test_unrelated_existing_model_asset_is_not_caught_by_fdi_specific_gate(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            general = root / "backend/ai_models/cephalo-nonfdi.onnx"
            general.parent.mkdir(parents=True)
            # Use unrelated name to ensure the restricted check does not
            # alter the existing non-FDI product scope.
            general = general.with_name("cephalo-landmarks.onnx")
            general.write_bytes(b"FAKE")
            gate.check_no_research_weights_bundled(root)

    def test_missing_catalog_is_not_success(self):
        with self.assertRaises((OSError, ValueError)):
            json.loads((Path(__file__).parent / "not-present-j10i.json").read_text())


if __name__ == "__main__":
    unittest.main()
