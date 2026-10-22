"""Deterministic synthetic positive/negative tests; no patient images or weights."""
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
import tempfile
import numpy as np

from lot05_j10d_oralguard_offline_probe import (
    OralGuardProbeError, verify_class_order, verify_session, verify_artifact,
    decode_onnx, letterbox, run_probe,
)


class ContractTests(TestCase):
    def test_expected_class_mapping(self):
        self.assertEqual(verify_class_order("{0: 'caries', 1: 'deep_caries', 2: 'periapical_lesion', 3: 'impacted_tooth'}"),
                         ("caries", "deep_caries", "periapical_lesion", "impacted_tooth"))

    def test_swapped_indices_must_fail(self):
        with self.assertRaisesRegex(OralGuardProbeError, "unsafe_class_order"):
            verify_class_order({0:"caries", 1:"deep_caries", 2:"impacted_tooth", 3:"periapical_lesion"})

    def test_duplicate_indices_and_bad_metadata_must_fail(self):
        for value in [None, {}, {0:"caries"}, {"0":"caries", "1":"caries", "2":"periapical_lesion", "3":"impacted_tooth"}, "DROP TABLE"]:
            with self.subTest(value=value), self.assertRaises(OralGuardProbeError):
                verify_class_order(value)

    def test_hash_missing_and_mismatch_fail(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t)/"model.onnx"
            p.write_bytes(b"bad")
            with self.assertRaisesRegex(OralGuardProbeError,"model_sha256_mismatch"):
                verify_artifact(p)
            with self.assertRaisesRegex(OralGuardProbeError,"pinned_model_not_found"):
                verify_artifact(Path(t)/"absent.onnx")

    def test_session_fail_closed_on_swapped_names(self):
        session=SimpleNamespace(get_providers=lambda:["CPUExecutionProvider"],
             get_inputs=lambda:[SimpleNamespace(shape=[1,3,1024,1024])],
             get_outputs=lambda:[SimpleNamespace(shape=[1,8,21504])],
             get_modelmeta=lambda:SimpleNamespace(custom_metadata_map={"names":"{0:'caries',1:'deep_caries',2:'impacted_tooth',3:'periapical_lesion'}"}))
        with self.assertRaisesRegex(OralGuardProbeError,"unsafe_class_order"):
            verify_session(session)

    def test_synthetic_preprocess_shape(self):
        img=np.zeros((512,1024,3),dtype=np.uint8)
        tensor, ratio, padding=letterbox(img)
        self.assertEqual(tensor.shape,(1,3,1024,1024))
        self.assertEqual(ratio,1)
        self.assertEqual(padding,(0,256))

    def test_decode_periapical_does_not_become_impacted(self):
        raw=np.zeros((1,8,21504),dtype=np.float32)
        raw[0,:4,0]=[400,400,100,100]
        raw[0,6,0]=0.91
        raw[0,:4,1]=[800,800,50,50]
        raw[0,7,1]=0.88
        out=decode_onnx(raw,image_shape=(1024,1024),scale=1,padding=(0,0))
        self.assertEqual([v['finding_candidate'] for v in out],["periapical_lesion","impacted_tooth"])
        self.assertNotIn("tooth",out[0])

    def test_nms_suppresses_same_class_not_other_class(self):
        raw=np.zeros((1,8,21504),dtype=np.float32)
        raw[0,:4,0]=[200,200,90,90];raw[0,4,0]=0.9
        raw[0,:4,1]=[201,200,90,90];raw[0,4,1]=0.8
        raw[0,:4,2]=[200,200,90,90];raw[0,5,2]=0.75
        out=decode_onnx(raw,image_shape=(1024,1024),scale=1,padding=(0,0))
        self.assertEqual(len(out),2)

    def test_nonfinite_and_malformed_outputs_fail_closed(self):
        arr=np.zeros((1,8,21504),dtype=np.float32)
        bad=arr.copy();bad[0,0,0]=float("nan")
        for value in [bad, np.zeros((1,8,200),dtype=np.float32)]:
            with self.subTest(shape=value.shape),self.assertRaisesRegex(OralGuardProbeError,"invalid_or_nonfinite_output"):
                decode_onnx(value,image_shape=(1024,1024),scale=1,padding=(0,0))

    def test_verify_artifact_guard_precedes_session(self):
        with self.assertRaisesRegex(OralGuardProbeError,"pinned_model_not_found"):
            run_probe(Path("/not-a-real-model.onnx"), np.zeros((5,5,3),dtype=np.uint8))
