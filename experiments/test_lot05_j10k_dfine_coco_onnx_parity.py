"""J10K synthetic-only independent ONNX CPU parity contract tests."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import numpy as np

MODULE = Path(__file__).with_name("lot05_j10k_dfine_coco_onnx_parity.py")
spec = importlib.util.spec_from_file_location("j10k_parity", MODULE)
assert spec and spec.loader
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/lot05-j10k-dfine-onnx-parity.yml"


class TestOnnxContract(unittest.TestCase):
    def setUp(self):
        self.logits = np.zeros((1, 300, 80), dtype=np.float32)
        self.logits[:, :, 0] = 3
        self.boxes = np.full((1, 300, 4), 0.5, dtype=np.float32)

    def test_upstream_pins_exact_file_hashes(self):
        self.assertEqual(m.SOURCE_REVISION, "066438d3d8f0da137a37b38fdf3368fd4afceced")
        self.assertEqual(m.SOURCE_WEIGHTS_SHA,
                         "19e06bdc873da819920a8d373b879721a5b9759d822f8213220bb09abbdab58b")
        self.assertEqual(m.ONNX_SHA,
                         "b0ec2e5793f3a3cbd07440d098645a0e102cd450fb92f4f35e713f36e35d152e")
        self.assertEqual(m.ONNX_BYTES, 15_434_935)

    def test_byte_tampering_is_rejected(self):
        with TemporaryDirectory() as tmp:
            fake = Path(tmp) / "model.onnx"
            fake.write_bytes(b"fake 0 byte model")
            with self.assertRaises(m.ParityError):
                m.verify_onnx(fake)

    def test_pytorch_model_is_also_pinned(self):
        with TemporaryDirectory() as tmp:
            with self.assertRaises(m.ParityError):
                m.verify_source_model(Path(tmp))

    def test_same_logits_and_boxes_pass(self):
        values = m.compare_tensors(self.logits, self.boxes,
                                   self.logits.copy(), self.boxes.copy())
        self.assertEqual(values["same_argmax_class_queries"], 300)
        self.assertEqual(values["logits_max_abs_delta"], 0.0)

    def test_large_logit_change_fails(self):
        wrong = self.logits.copy()
        wrong[0, 0, 0] += 0.1
        with self.assertRaises(m.ParityError):
            m.compare_tensors(self.logits, self.boxes, wrong, self.boxes)

    def test_large_box_difference_fails(self):
        wrong = self.boxes.copy()
        wrong[0, 10, 3] += 0.03
        with self.assertRaises(m.ParityError):
            m.compare_tensors(self.logits, self.boxes, self.logits, wrong)

    def test_shape_change_fails(self):
        with self.assertRaises(m.ParityError):
            m.compare_tensors(self.logits, self.boxes,
                              np.zeros((1, 300, 32), dtype=np.float32), self.boxes)

    def test_nonfinite_data_fails(self):
        bad = self.logits.copy()
        bad[0, 0, 0] = np.nan
        with self.assertRaises(m.ParityError):
            m.compare_tensors(self.logits, self.boxes, bad, self.boxes)

    def test_permuted_classes_fail(self):
        perm = self.logits.copy()
        perm[:, :, 0] = 0
        perm[:, :, 1] = 3
        with self.assertRaises(m.ParityError):
            m.compare_tensors(self.logits, self.boxes, perm, self.boxes)

    def test_actions_only_metadata_artifacts_and_no_shipping(self):
        content = WORKFLOW.read_text(encoding="utf-8")
        for term in ("ubuntu-24.04", "windows-2025", "actions/upload-artifact@",
                     "reports/j10k-", "commercial_release_approved", "CPUExecutionProvider"):
            self.assertIn(term, content)
        for term in ("deploy-production", "gh release create", "aws s3",
                     "vercel deploy", "huggingface-cli upload", "patient_id"):
            self.assertNotIn(term, content)

    def test_only_public_nonmedical_data_in_script(self):
        content = MODULE.read_text(encoding="utf-8")
        for term in ("Image.new(", "trust_remote_code=False",
                     "SOURCE_WEIGHTS_SHA", "ONNX_SHA",
                     "fdi_class_training_performed", "clinical_use_approved"):
            self.assertIn(term, content)
        self.assertNotIn("Roboflow", content)
        self.assertNotIn("DENTEX", content)


if __name__ == "__main__":
    unittest.main()
