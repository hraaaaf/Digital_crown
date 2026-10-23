"""J10Z research-only fixture tests; no torch, radiographs or external source access."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import unittest

path=Path(__file__).with_name("lot05_j10z_fdi640_epoch_ablation.py")
spec=importlib.util.spec_from_file_location("j10z",path)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def snapshot(precision, recall, fp, tp, focus):
    return {
        "fdi32":{"precision":precision,"recall":recall,"fp":fp,"tp":tp},
        "focus_teeth":{k:{"tp":focus[k]} for k in ("31","32","24")}
    }


class TestPreRegisteredEpochAblation(unittest.TestCase):
    def test_fixed_epochs_and_image_scopes(self):
        self.assertEqual(mod.CHECKPOINTS,(3,6))
        self.assertEqual((mod.RESOLUTION,mod.TRAIN_N,mod.VALID_N),(640,96,33))

    def test_positive_and_negative_deltas_are_signed(self):
        a=snapshot(.4,.3,600,250,{"31":0,"32":5,"24":9})
        b=snapshot(.5,.35,500,290,{"31":4,"32":3,"24":8})
        out=mod._compare(a,b)
        self.assertEqual(out["precision_6_minus_3"],.1)
        self.assertEqual(out["recall_6_minus_3"],.05)
        self.assertEqual(out["false_positives_6_minus_3"],-100)
        self.assertEqual(out["fdi31_tp_6_minus_3"],4)
        self.assertEqual(out["fdi32_tp_6_minus_3"],-2)
        self.assertEqual(out["fdi24_tp_6_minus_3"],-1)

    def test_equal_checkpoints_have_zero_differences(self):
        a=snapshot(.45,.4,400,250,{"31":4,"32":4,"24":5})
        self.assertTrue(all(v==0 for v in mod._compare(a,a).values()))

    def test_metrics_do_not_depend_on_restoration_data(self):
        a=snapshot(.4,.3,600,250,{"31":0,"32":5,"24":9})
        b=snapshot(.5,.35,500,290,{"31":4,"32":3,"24":8})
        a["restorations3"]={"tp":0}
        b["restorations3"]={"tp":999}
        self.assertEqual(mod._compare(a,b)["true_positives_6_minus_3"],40)


if __name__=="__main__":
    unittest.main()
