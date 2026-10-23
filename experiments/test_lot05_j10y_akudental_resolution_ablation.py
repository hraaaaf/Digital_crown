"""J10Y metric scope tests: no network, model, external images or torch."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import unittest

p=Path(__file__).with_name("lot05_j10y_akudental_resolution_ablation.py")
s=importlib.util.spec_from_file_location("j10y",p)
assert s and s.loader
m=importlib.util.module_from_spec(s)
s.loader.exec_module(m)

def one_prediction(gt_id, pred_id, score=.8):
    box=[.1,.2,.5,.6]
    return ({"boxes":[box],"labels":[pred_id],"scores":[score]},
            {"boxes":[box],"labels":[gt_id]})

class TestValidationOnlyAblation(unittest.TestCase):
    def test_fixed_focal_classes(self):
        self.assertEqual(m.FOCUS,("31","32","41","42","24","25","23","33"))

    def test_perfect_fdi32_is_separated_from_restoration(self):
        r=m._small_report([one_prediction(17,17)],resolution=320,
                          loss=2.0,train_images=96,val_images=1)
        self.assertEqual(r["fdi32"]["tp"],1)
        self.assertEqual(r["restorations3"]["tp"],0)
        self.assertEqual(r["focus_teeth"]["31"]["gt"],1)

    def test_wrong_fdi_number_is_not_true_positive(self):
        r=m._small_report([one_prediction(17,18)],resolution=640,
                          loss=2.0,train_images=96,val_images=1)
        self.assertEqual(r["fdi32"]["tp"],0)
        self.assertEqual(r["wrong_spatial_fdi_numbers"],1)
        self.assertEqual(r["focus_teeth"]["31"]["tp"],0)

    def test_restoration_separate(self):
        r=m._small_report([one_prediction(33,33)],resolution=320,
                          loss=3.0,train_images=96,val_images=1)
        self.assertEqual(r["fdi32"]["tp"],0)
        self.assertEqual(r["restorations3"]["tp"],1)
        self.assertEqual(r["validation_images"],1)

    def test_low_score_fails_fixed_threshold(self):
        r=m._small_report([one_prediction(17,17,.1)],resolution=640,
                          loss=2.0,train_images=96,val_images=1)
        self.assertEqual(r["fdi32"]["tp"],0)
        self.assertEqual(r["fdi32"]["fn"],1)

if __name__=="__main__":
    unittest.main()
