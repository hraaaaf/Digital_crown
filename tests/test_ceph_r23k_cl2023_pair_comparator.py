"""R23-K synthetic parser/anti-mismatch tests. NO real patient image or fake ML."""
from __future__ import annotations
import json
import math
from pathlib import Path
import tempfile
import unittest
import zipfile

import numpy as np
from scripts.compare_srpose38_cl2023_38 import (
    PairEvidenceError, inference, load_organizer_gt, read_original_mha_slice,
    run, score_channels,
)


def synthetic_sources(tmp: Path, *, corrupt_case=False, duplicate=False, zero_scale=False):
    w,h,depth = 90, 100, 2
    # Identifiable two differently bright synthetic films, no patient pixels.
    film1 = np.full((h,w,3), 20, dtype=np.uint8)
    film2 = np.full((h,w,3), 220, dtype=np.uint8)
    film2[90:,:,:] = 0
    film2[:,80:,:] = 0
    mha=tmp/'train_stack.mha'
    header=(f"ObjectType = Image\nNDims = 3\nBinaryData = True\n"
            f"BinaryDataByteOrderMSB = False\nCompressedData = False\n"
            f"DimSize = {w} {h} {depth}\nElementNumberOfChannels = 3\n"
            f"ElementType = MET_UCHAR\nElementDataFile = LOCAL\n").encode()
    mha.write_bytes(header+film1.tobytes()+film2.tobytes())
    points=[]
    for z in range(1,3):
        for index in range(1,39):
            points.append({"name":index,"point":[index,20+(index%20),
                3 if corrupt_case and z==2 else z],
                 "scale":"0" if zero_scale and z==2 else "0.1"})
    if duplicate:points[-1]["name"]=1
    gt=tmp/'train-gt.json'
    gt.write_text(json.dumps({"name":"Orthodontic landmarks","type":"Multiple points","points":points}))
    zipped=tmp/'train-gt.json.zip'
    with zipfile.ZipFile(zipped,"w") as z:z.write(gt,arcname="train-gt.json")
    return mha,gt,zipped


class PairedComparatorTests(unittest.TestCase):
    def test_correct_one_based_slice_and_cropped_coordinates(self):
        with tempfile.TemporaryDirectory() as d:
            mha,gt,_=synthetic_sources(Path(d))
            a=read_original_mha_slice(mha,1)
            b=read_original_mha_slice(mha,2)
            self.assertEqual(a.shape,(100,90,3))
            self.assertEqual(b.shape,(90,80,3))
            self.assertEqual(int(a[0,0,0]),20)
            self.assertEqual(int(b[0,0,0]),220)
            pts,mm=load_organizer_gt(gt,2)
            self.assertEqual((len(pts),mm),(38,0.1))
            self.assertEqual(pts[0],(1,21))
            rows=score_channels(pts,pts,mm,80,90)
            self.assertTrue(all(x["error_mm"]==0 for x in rows))
            self.assertEqual([r["index_1_based"] for r in rows],list(range(1,39)))

    def test_original_zip_support_no_other_file_substitution(self):
        with tempfile.TemporaryDirectory() as d:
            mha,gt,zipped=synthetic_sources(Path(d))
            pts,scale=load_organizer_gt(zipped,2)
            self.assertEqual(len(pts),38)
            self.assertEqual(scale,0.1)
            with zipfile.ZipFile(zipped,"a") as z:
                z.writestr("fake/train-gt.json","{}")
            with self.assertRaisesRegex(PairEvidenceError,"Exactly one"):
                load_organizer_gt(zipped,2)

    def test_no_wrong_slice_unpaired_or_duplicate(self):
        with tempfile.TemporaryDirectory() as d:
            mha,gt,_=synthetic_sources(Path(d),corrupt_case=True)
            with self.assertRaisesRegex(PairEvidenceError,"38 ground truth"):
                load_organizer_gt(gt,2)
            with self.assertRaisesRegex(PairEvidenceError,"film ID"):
                read_original_mha_slice(mha,3)
        with tempfile.TemporaryDirectory() as d:
            _,gt,_=synthetic_sources(Path(d),duplicate=True)
            with self.assertRaisesRegex(PairEvidenceError,"Duplicate"):
                load_organizer_gt(gt,2)
        with tempfile.TemporaryDirectory() as d:
            _,gt,_=synthetic_sources(Path(d),zero_scale=True)
            with self.assertRaisesRegex(PairEvidenceError,"zero"):
                load_organizer_gt(gt,2)

    def test_no_channel_name_guess_and_no_fabricated_validity(self):
        pts=[(i+10.,20.) for i in range(38)]
        pred=list(pts)
        pred[0]=(20.,20.)
        pred[1]=(math.nan,20.)
        rows=score_channels(pred,pts,0.1,100,100)
        self.assertEqual(rows[0]["index_1_based"],1)
        self.assertAlmostEqual(rows[0]["error_mm"],1.0)
        self.assertIsNone(rows[1]["error_mm"])
        self.assertFalse(rows[1]["valid_in_frame"])
        with self.assertRaisesRegex(PairEvidenceError,"38"):
            score_channels(pred[:-1],pts,0.1,100,100)
        with self.assertRaisesRegex(PairEvidenceError,"outside"):
            score_channels(pts,[(1000,10)]+pts[1:],0.1,100,100)

    def test_no_model_weights_does_not_fake_predictions(self):
        with tempfile.TemporaryDirectory() as d:
            _,_,_=synthetic_sources(Path(d))
            with self.assertRaisesRegex(PairEvidenceError,"mismatched"):
                inference(np.zeros((100,90,3),dtype=np.uint8),Path(d)/"missing-model.onnx")

    def test_pair_only_remains_explicitly_no_inference_and_nonclinical(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);mha,gt,_=synthetic_sources(root)
            args=type("Args",(),dict(confirm_dataset_rights=True,case_id=2,mha=mha,gt=gt,
                model=root/"not-installed.onnx",output=root/"private-output",check_pair_only=True))
            self.assertEqual(run(args),0)
            r=json.loads((root/"private-output"/"report.json").read_text())
            self.assertEqual(r["status"],"PAIR_VERIFIED_MODEL_NOT_RUN")
            self.assertFalse(r["model_ran"])
            self.assertFalse(r["clinical_release"])
            self.assertEqual(r["gt_points"],38)
            self.assertFalse((root/"private-output"/"overlay_local_only.png").exists())

    def test_rejects_missing_authorization_before_accessing_image(self):
        args=type("Args",(),dict(confirm_dataset_rights=False,case_id=1,
            mha=Path("/does/not/exist"),gt=Path("/also/missing")))
        with self.assertRaisesRegex(PairEvidenceError,"RESTRICTED"):
            run(args)


if __name__=="__main__":
    unittest.main()
