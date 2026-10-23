"""J11C: synthetic image/geometry and fail-closed tests only."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

p=Path(__file__).with_name("lot05_j11c_academic_visual_readiness.py")
spec=importlib.util.spec_from_file_location("j11c_unit",p)
assert spec and spec.loader
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class TestReadiness(unittest.TestCase):
    def test_pixel_extent(self):
        self.assertEqual(m.pixel_extent((1000,500),(.25,.5,.1,.2)),(100,100))
    def test_tiny_usable_region(self):
        self.assertEqual(m.pixel_extent((1000,500),(.5,.5,.01,.02)),(10,10))
    def test_reject_zero_and_nan_bbox(self):
        for box in ((.5,.5,0,.1),(2,.5,.1,.1),(.5,.5,float("nan"),.1)):
            with self.assertRaises(m.ReadinessError):
                m.pixel_extent((1000,500),box)
    def test_reject_zero_image(self):
        with self.assertRaises(m.ReadinessError):
            m.pixel_extent((0,0),(.5,.5,.1,.1))
    def test_image_decode_synthetic_only(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as root:
            image=Path(root)/"synthetic.jpg"
            Image.new("RGB",(320,160),"white").save(image,"JPEG")
            self.assertEqual(m.image_info(image),(320,160,1))
            self.assertEqual(len(list(Path(root).iterdir())),1)
    def test_reject_missing_and_png(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root)/"fake.png"
            p.write_bytes(b"PNG?")
            for path in (p,Path(root)/"missing.jpg"):
                with self.assertRaises(m.ReadinessError):
                    m.image_info(path)
    def test_missing_source_not_certified(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(m.ReadinessError):
                m.run(Path(root)/"images",Path(root)/"labels")
    def test_cli_failure_has_no_identifiers(self):
        with tempfile.TemporaryDirectory() as root:
            r=subprocess.run([sys.executable,str(p),"--images-dir",str(Path(root)/"missing"),
                 "--labels-dir",str(Path(root)/"other")],capture_output=True,text=True)
            self.assertEqual(r.returncode,1)
            self.assertEqual(json.loads(r.stdout),{"schema":m.SCHEMA,"status":"FAIL_CLOSED"})
            self.assertEqual(r.stderr,"")

if __name__=="__main__":
    unittest.main()
