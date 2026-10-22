"""LOT05/J10J — static and synthetic tests; never download models or patient data."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

PATH = Path(__file__).with_name("lot05_j10j_dfine_coco_actions_smoke.py")
spec = importlib.util.spec_from_file_location("j10j_smoke", PATH)
assert spec and spec.loader
smoke = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smoke)
REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = REPO_ROOT / ".github/workflows/lot05-j10j-dfine-cpu-smoke.yml"


class DfineSmokeContracts(unittest.TestCase):
    def test_model_revision_and_weights_are_immutable(self):
        self.assertEqual(smoke.MODEL_REPO, "ustc-community/dfine-nano-coco")
        self.assertEqual(
            smoke.MODEL_REVISION,
            "066438d3d8f0da137a37b38fdf3368fd4afceced",
        )
        self.assertEqual(
            smoke.MODEL_WEIGHTS_SHA256,
            "19e06bdc873da819920a8d373b879721a5b9759d822f8213220bb09abbdab58b",
        )
        self.assertEqual(
            smoke.FILES, ("model.safetensors", "config.json", "preprocessor_config.json")
        )

    def test_missing_model_fails_closed(self):
        with TemporaryDirectory() as tmp:
            with self.assertRaises(smoke.FoundationSmokeError):
                smoke.verify_downloaded_snapshot(Path(tmp))

    def test_sha_mismatch_fails_closed(self):
        with TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p / "model.safetensors").write_bytes(b"wrong")
            (p / "config.json").write_text('{"model_type":"d_fine","id2label":{}}')
            (p / "preprocessor_config.json").write_text("{}")
            with self.assertRaisesRegex(smoke.FoundationSmokeError, "digest"):
                smoke.verify_downloaded_snapshot(p)

    def test_non_fdi_coco_head_is_not_32(self):
        with TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p / "model.safetensors").write_bytes(b"fake weights ONLY in test fixture")
            (p / "config.json").write_text(json.dumps({
                "model_type": "d_fine",
                "id2label": {str(i): f"COCO-{i}" for i in range(80)},
            }))
            (p / "preprocessor_config.json").write_text("{}")
            original = smoke.MODEL_WEIGHTS_SHA256
            try:
                smoke.MODEL_WEIGHTS_SHA256 = smoke.sha256(p / "model.safetensors")
                check = smoke.verify_downloaded_snapshot(p)
            finally:
                smoke.MODEL_WEIGHTS_SHA256 = original
            self.assertEqual(check["coco_class_count"], 80)
            self.assertEqual(check["checkpoint_bytes"], len(b"fake weights ONLY in test fixture"))

    def test_unchanged_license_gate_must_block_release(self):
        from importlib.util import spec_from_file_location, module_from_spec
        f = REPO_ROOT / "experiments/lot05_j10i_fdi_commercial_rights_gate.py"
        sp = spec_from_file_location("j10i_gate", f)
        assert sp and sp.loader
        gate = module_from_spec(sp)
        sp.loader.exec_module(gate)
        report = gate.review_catalog(json.loads(gate.CATALOG_PATH.read_text(encoding="utf-8")))
        self.assertEqual(report["status"], "COMMERCIAL_AND_CLINICAL_RELEASE_BLOCKED")

    def test_gha_workflow_restricts_artifact_to_json_reports_and_never_deploys(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("ubuntu-24.04", text)
        self.assertIn("windows-2025", text)
        self.assertIn("actions/upload-artifact@", text)
        self.assertIn("reports/j10j-", text)
        for forbidden in (
            "deploy-production", "aws s3", "netlify deploy",
            "vercel deploy", "gh release create", "huggingface-cli upload",
            "model.safetensors\n", "backend/static/patients",
        ):
            self.assertNotIn(forbidden, text)
        self.assertIn("commercial_release_approval", WORKFLOW.read_text())

    def test_script_is_strictly_coco_and_synthetic(self):
        code = PATH.read_text(encoding="utf-8")
        for must in (
            "training_performed", "fdi_detections_validated",
            "commercial_release_approval", "clinical_approval",
            "torch.inference_mode()", "verify_downloaded_snapshot",
            "Image.new(", "snapshot_download(", "trust_remote_code=False",
        ):
            self.assertIn(must, code)
        self.assertNotIn("Roboflow", code)
        self.assertNotIn("DENTEX", code)


if __name__ == "__main__":
    unittest.main()
