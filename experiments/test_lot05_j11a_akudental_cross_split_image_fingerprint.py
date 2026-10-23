"""J11A privacy and image fingerprint tests using 100% synthetic data."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import tempfile
import unittest

p=Path(__file__).with_name("lot05_j11a_akudental_cross_split_image_fingerprint.py")
spec=importlib.util.spec_from_file_location("j11a",p)
assert spec and spec.loader
j=importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name]=j
spec.loader.exec_module(j)

def sample(split, byte, pix, dh, mirrored):
    return j.Fingerprint(split, byte, pix, dh, mirrored)


class TestSplitImageFingerprint(unittest.TestCase):
    def test_exact_file_and_decoded_pixel_matches(self):
        items=[sample("train","a","p",123,456),
               sample("val","a","p",123,456)]
        r=j.compare_fingerprints(items)["cross_partition"]["train_vs_val"]
        self.assertEqual(r["identical_jpeg_file_pairs"],1)
        self.assertEqual(r["identical_decoded_pixel_pairs"],1)
        self.assertEqual(r["candidate_pairs_by_dhash_threshold"]["0"],1)

    def test_decoded_pixel_equal_even_different_file_hash(self):
        items=[sample("train","a","pix",12,99),
               sample("test","b","pix",12,99)]
        r=j.compare_fingerprints(items)["cross_partition"]["train_vs_test"]
        self.assertEqual(r["identical_jpeg_file_pairs"],0)
        self.assertEqual(r["identical_decoded_pixel_pairs"],1)

    def test_mirrored_near_match_is_screen_not_proof(self):
        items=[sample("train","a","pix_a",0,~0 & ((1<<64)-1)),
               sample("val","b","pix_b",~0 & ((1<<64)-1),0)]
        r=j.compare_fingerprints(items)["cross_partition"]["train_vs_val"]
        self.assertEqual(r["identical_decoded_pixel_pairs"],0)
        self.assertEqual(r["candidate_normal_pairs_by_threshold"]["0"],0)
        self.assertEqual(r["candidate_mirror_pairs_by_threshold"]["0"],1)
        self.assertTrue(r["similarity_candidates_are_not_confirmed_duplicate_patients"])

    def test_no_paths_or_hashes_ever_in_aggregate(self):
        items=[sample("train","secret_file_hash", "secret_pixel_hash", 3,4),
               sample("val","other_file", "another_pixel", 5,6)]
        r=str(j.compare_fingerprints(items))
        self.assertNotIn("secret_",r)
        self.assertNotIn("path",r.lower())
        self.assertIn("patient_level_independence_established",r)
        self.assertIn("'train_vs_val'",r)

    def test_dhash_is_deterministic_and_orientation_sensitive(self):
        from PIL import Image
        img=Image.new("RGB",(90,80))
        for x in range(90):
            for y in range(80):
                img.putpixel((x,y),(x*2,x*2,x*2))
        normal=j._dhash(img)
        mirror=j._dhash(img,mirrored=True)
        self.assertEqual(j._dhash(img),normal)
        self.assertNotEqual(normal,mirror)
        img.close()

    def test_true_synthetic_jpeg_fingerprint_no_metadata_emitted(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as temp:
            a=Path(temp)/"private.jpg"
            im=Image.new("RGB",(100,80),(40,70,100))
            im.save(a,format="JPEG")
            im.close()
            f=j.fingerprint_jpeg(a,"train")
            self.assertEqual(len(f.jpeg_sha256),64)
            self.assertEqual(len(f.pixels_sha256),64)
            self.assertEqual(f.split,"train")

    def test_symlink_refused(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            a=root/"a.jpg"
            b=root/"b.jpg"
            img=Image.new("RGB",(100,80),(20,40,60))
            img.save(a,format="JPEG")
            img.close()
            b.symlink_to(a)
            with self.assertRaisesRegex(j.AuditError,"unsafe_or_missing_jpeg"):
                j.fingerprint_jpeg(b,"val")

    def test_missing_dataset_fails_closed(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaisesRegex(j.AuditError,"source_layout_missing"):
                j.audit_source(Path(t)/"images", Path(t)/"labels")


if __name__=="__main__":
    unittest.main()
