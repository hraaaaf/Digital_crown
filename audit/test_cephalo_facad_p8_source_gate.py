"""P8 source declaration and byte-integrity checks with synthetic data only."""
import hashlib
import unittest
from audit.cephalo_facad_p8_source_gate import SCHEMA, verify

def case():
    image = bytes.fromhex("89504e470d0a1a0a0000000d49484452") + (1200).to_bytes(4,"big") + (900).to_bytes(4,"big") + bytes(9)
    bundle = b"SYNTHETIC TEST MANIFEST - NO REAL EXPORTS"
    a = {
        "schema": SCHEMA,
        "image_hash": hashlib.sha256(image).hexdigest(),
        "export_bundle_hash": hashlib.sha256(bundle).hexdigest(),
        "source_width": 1200, "source_height": 900,
        "facad_version": "3.14.1.1111",
        "native_source": True, "no_overlay": True,
        "same_case": True, "same_trace": True,
        "rights": True, "screen_capture": False,
    }
    return image, bundle, a

class P8Tests(unittest.TestCase):
    def test_hash_consistency_is_not_clinical_certification(self):
        img, bundle, a = case()
        result = verify(img, bundle, a)
        self.assertTrue(result["byte_integrity_matches"])
        self.assertTrue(result["intake_candidate_only"])
        self.assertFalse(result["anatomical_validation"])
        self.assertFalse(result["same_trace_independently_verified"])
        self.assertEqual(result["clinical_parities"], 0)
        self.assertTrue(result["clinical_no_go"])

    def test_image_hash_mismatch(self):
        img, bundle, a = case()
        a["image_hash"] = "0" * 64
        self.assertFalse(verify(img, bundle, a)["intake_candidate_only"])

    def test_bundle_hash_mismatch(self):
        img, bundle, a = case()
        a["export_bundle_hash"] = "f" * 64
        self.assertFalse(verify(img, bundle, a)["intake_candidate_only"])

    def test_operator_screenshot_blocks_candidate(self):
        img, bundle, a = case()
        a["screen_capture"] = True
        self.assertFalse(verify(img, bundle, a)["intake_candidate_only"])

    def test_rights_missing_blocks_candidate(self):
        img, bundle, a = case()
        a["rights"] = False
        self.assertFalse(verify(img, bundle, a)["intake_candidate_only"])

    def test_unknown_fields_rejected(self):
        img, bundle, a = case()
        a["patient_name"] = "not_allowed"
        with self.assertRaises(ValueError):
            verify(img, bundle, a)

    def test_nonboolean_flags_rejected(self):
        img, bundle, a = case()
        a["native_source"] = "yes"
        with self.assertRaises(ValueError):
            verify(img, bundle, a)

if __name__ == "__main__":
    unittest.main()
