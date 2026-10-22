"""Pure unit tests for FDI ONNX offline bridge, no models or radiographs."""
import json
from pathlib import Path
import tempfile
import unittest

from lot05_j10e_fdi_onnx_bridge import (
    FDIIntegrationError, REVIEW_SCHEMA, format_predictions, verify_model_file,
    hash_file,
)
from lot05_j10e_fdi_onnx_parity_ci import box_iou, compare_predictions


class FakeTensor:
    def __init__(self, values): self.values=values
    def cpu(self): return self
    def numpy(self): return self
    def tolist(self): return self.values


class FakeBoxes:
    def __init__(self, cls, boxes, confidence):
        self.cls=FakeTensor(cls); self.xyxy=FakeTensor(boxes); self.conf=FakeTensor(confidence)


class FakeResult:
    def __init__(self, cls, boxes, confidence): self.boxes=FakeBoxes(cls,boxes,confidence)


class TestFdiBridge(unittest.TestCase):
    def test_metadata_and_real_normalized_geometry(self):
        data = format_predictions(2000,1000,[{"cls":21,"box":[200,300,400,900],"conf":.90}])
        self.assertEqual(data["schema"],REVIEW_SCHEMA)
        self.assertEqual(data["proposals"][0]["fdi"],"36")
        self.assertEqual(data["proposals"][0]["bbox"],[.1,.3,.2,.9])

    def test_empty_film_yields_empty_proposals_not_fake_teeth(self):
        self.assertEqual(format_predictions(300,200,[])["proposals"],[])

    def test_primary_and_out_of_range_fdi_rejected(self):
        for cls in [-1,32,55,True]:
            with self.subTest(cls=cls),self.assertRaises(FDIIntegrationError):
                format_predictions(100,100,[{"cls":cls,"box":[1,1,10,10],"conf":.6}])

    def test_boxes_outside_image_and_non_finite_rejected(self):
        for box in [[0,0,999,5],[1,2,2,2],[1,float("nan"),3,4],[-1,0,3,4]]:
            with self.subTest(box=box),self.assertRaises(FDIIntegrationError):
                format_predictions(100,100,[{"cls":0,"box":box,"conf":.5}])

    def test_confidence_boolean_nan_and_above_one_rejected(self):
        for value in [True,float("nan"),-0.3,1.2]:
            with self.subTest(value=value),self.assertRaises(FDIIntegrationError):
                format_predictions(100,100,[{"cls":0,"box":[1,2,3,4],"conf":value}])

    def test_local_model_hash_rejects_mutated_bytes_and_symlinks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            model=root/"tested.onnx"
            model.write_bytes(b"research fake model")
            digest=hash_file(model)
            self.assertEqual(verify_model_file(model,digest,".onnx"),model)
            model.write_bytes(b"mutated")
            with self.assertRaisesRegex(FDIIntegrationError,"model_hash_mismatch"):
                verify_model_file(model,digest,".onnx")
            ref=root/"link.onnx";ref.symlink_to(model)
            with self.assertRaisesRegex(FDIIntegrationError,"model_must_be_local_regular_file"):
                verify_model_file(ref,hash_file(model),".onnx")

    def test_iou(self):
        self.assertAlmostEqual(box_iou([1,1,11,11],[1,1,11,11]),1)
        self.assertEqual(box_iou([1,1,11,11],[20,20,30,30]),0)

    def test_perfect_same_class_cpu_parity(self):
        a=FakeResult([0,21],[[1,2,11,12],[20,20,30,30]],[.9,.8])
        b=FakeResult([0,21],[[1,2,11,12],[20,20,30,30]],[.9,.8])
        result=compare_predictions(a,b)
        self.assertEqual(result["matching"],2)
        self.assertEqual(result["fdi_mismatch_or_missing"],0)

    def test_geometrically_identical_but_wrong_fdi_fails_parity(self):
        a=FakeResult([21],[[10,10,20,20]],[.8])
        b=FakeResult([22],[[10,10,20,20]],[.8])
        self.assertEqual(compare_predictions(a,b)["fdi_mismatch_or_missing"],1)

    def test_missing_one_proposal_fails_parity(self):
        a=FakeResult([0,1],[[1,1,8,8],[10,10,20,20]],[.8,.8])
        b=FakeResult([0],[[1,1,8,8]],[.8])
        self.assertEqual(compare_predictions(a,b)["fdi_mismatch_or_missing"],1)


if __name__=="__main__":
    unittest.main()
