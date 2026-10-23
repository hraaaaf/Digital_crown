"""Nine synthetic-only tests for J11E ROI comparison."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from PIL import Image,ImageDraw,ImageOps

p=Path(__file__).with_name("lot05_j11e_academic_pair_roi_screen.py")
spec=importlib.util.spec_from_file_location("j11e_unit",p)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class TestROIScreen(unittest.TestCase):
    def image(self):
        im=Image.new("L",(224,128),40)
        d=ImageDraw.Draw(im)
        d.rectangle((0,0,70,127),fill=180)
        d.rectangle((170,30,211,68),fill=245)
        return im

    def test_same_roi_distance_zero(self):
        im=self.image()
        self.assertEqual(mod.distance(im,im),0)
    def test_mirrored_source_recognized(self):
        im=self.image()
        normal,mirror=mod.evaluate(im,ImageOps.mirror(im))
        self.assertGreater(normal,.05)
        self.assertAlmostEqual(mirror,0,places=7)
    def test_difference_returns_unit_interval(self):
        a=Image.new("L",(224,128),0)
        b=Image.new("L",(224,128),255)
        self.assertEqual(mod.distance(a,b),1)
    def test_nonmatching_sizes_rejected(self):
        with self.assertRaises(mod.ScreenError):
            mod.distance(self.image(),Image.new("L",(200,100)))
    def test_synthetic_jpeg_roi_dimensions(self):
        with tempfile.TemporaryDirectory() as root:
            f=Path(root)/"fixture.jpg"
            Image.new("RGB",(600,350),"white").save(f,"JPEG")
            crop=mod.roi(f)
            self.assertEqual(crop.size,(224,128))
            crop.close()
    def test_no_images_exported_on_roi(self):
        with tempfile.TemporaryDirectory() as root:
            f=Path(root)/"fixture.jpg"
            Image.new("RGB",(600,350),"black").save(f,"JPEG")
            mod.roi(f).close()
            self.assertEqual([v.name for v in Path(root).iterdir()],["fixture.jpg"])
    def test_reject_non_jpeg(self):
        with tempfile.TemporaryDirectory() as root:
            f=Path(root)/"fixture.png"
            Image.new("RGB",(600,350),"white").save(f,"PNG")
            with self.assertRaises(mod.ScreenError):
                mod.roi(f)
    def test_missing_labels_fail_closed(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(mod.ScreenError):
                mod.screen(Path(root)/"missing",Path(root)/"missing")
    def test_cli_failure_minimal_json(self):
        with tempfile.TemporaryDirectory() as root:
            r=subprocess.run([sys.executable,str(p),"--images-dir",root,
               "--labels-dir",root],capture_output=True,text=True)
            self.assertEqual(r.returncode,1)
            self.assertEqual(json.loads(r.stdout),
                             {"schema":mod.SCHEMA,"status":"FAIL_CLOSED"})
            self.assertEqual(r.stderr,"")

if __name__=="__main__":
    unittest.main()
