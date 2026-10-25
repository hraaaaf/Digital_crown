"""P8 tests: only generated pixel data and synthetic 13F/32F exports."""
import hashlib
import json
import struct
import unittest
import zlib

from audit.cephalo_facad_p8_source_gate import SCHEMA, verify

def png():
    def chunk(kind, payload):
        return (struct.pack(">I", len(payload)) + kind + payload +
                struct.pack(">I", zlib.crc32(kind + payload) & 0xffffffff))
    pixels = (bytes(1201)) * 900
    return (bytes.fromhex("89504e470d0a1a0a")
            + chunk(b"IHDR", struct.pack(">IIBBBBB", 1200, 900, 8, 0, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(pixels))
            + chunk(b"IEND", b""))

def bundle():
    profiles = [
        ("FACAD_RICKETTS_32F_COMPATIBILITY_TARGET", 32),
        ("FACAD_RICKETTS_13F_COMPATIBILITY_TARGET", 13),
    ]
    records = [
        {"evidence_id": "SYNTHETIC_" + str(count) + "_" + kind,
         "profile_target_id": profile, "artifact_kind": kind,
         "sha256": hashlib.sha256((profile+kind).encode()).hexdigest(),
         "facad_version": "3.14.1.1111", "same_trace_case_id": "SYNTHETIC_ONLY"}
        for profile, count in profiles
        for kind in ("ANALYSIS_VALUES", "ANALYSIS_PROPERTIES", "MARKER_POSITIONS")
    ]
    return json.dumps({
        "schema_version": "ORTHO_LOT08_FACAD_RICKETTS_DIRECT_PARITY_EVIDENCE_V1",
        "scientific_authority": False, "compatibility_only": True,
        "status": "DIRECT_EVIDENCE_PARTIAL", "parity_rows": [],
        "profiles": [{"target_id": p, "expected_facad_factor_count": n}
                     for p, n in profiles],
        "evidence_records": records
    }, sort_keys=True).encode()

def case():
    image, manifest = png(), bundle()
    claim = {"schema": SCHEMA,
             "image_hash": hashlib.sha256(image).hexdigest(),
             "export_bundle_hash": hashlib.sha256(manifest).hexdigest(),
             "source_width": 1200, "source_height": 900,
             "facad_version": "3.14.1.1111", "native_source": True,
             "no_overlay": True, "same_case": True, "same_trace": True,
             "rights": True, "screen_capture": False}
    return image, manifest, claim

class P8Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image, cls.manifest, cls.claim = case()

    def run_case(self, image=None, manifest=None, **changes):
        a = dict(self.claim)
        a.update(changes)
        return verify(self.image if image is None else image,
                      self.manifest if manifest is None else manifest, a)

    def test_complete_synthetic_png_is_not_clinical_authority(self):
        result = self.run_case()
        self.assertTrue(result["intake_candidate_only"])
        self.assertTrue(result["png_structural_integrity"])
        self.assertTrue(result["facad_manifest_structure_verified"])
        self.assertFalse(result["original_image_authenticated"])
        self.assertFalse(result["six_private_exports_verified_by_bytes"])
        self.assertFalse(result["same_trace_independently_verified"])
        self.assertEqual(result["clinical_parities"], 0)
        self.assertTrue(result["clinical_no_go"])

    def test_hash_mismatch_blocks_intake(self):
        self.assertFalse(self.run_case(image_hash="0"*64)["intake_candidate_only"])
        self.assertFalse(self.run_case(export_bundle_hash="f"*64)["intake_candidate_only"])

    def test_screenshot_or_rights_declared_false_blocks_intake(self):
        self.assertFalse(self.run_case(screen_capture=True)["intake_candidate_only"])
        self.assertFalse(self.run_case(rights=False)["intake_candidate_only"])

    def test_truncated_png_rejected_even_with_matching_claim_hash(self):
        truncated = self.image[:-12]
        with self.assertRaises(ValueError):
            self.run_case(image=truncated, image_hash=hashlib.sha256(truncated).hexdigest())

    def test_png_bad_crc_rejected_even_with_matching_claim_hash(self):
        broken = bytearray(self.image)
        broken[29] ^= 1
        modified = bytes(broken)
        with self.assertRaises(ValueError):
            self.run_case(image=modified, image_hash=hashlib.sha256(modified).hexdigest())

    def test_old_p8_fake_header_no_longer_accepted(self):
        fake = (bytes.fromhex("89504e470d0a1a0a0000000d49484452") +
                (1200).to_bytes(4,"big") + (900).to_bytes(4,"big") + bytes(9))
        with self.assertRaises(ValueError):
            self.run_case(image=fake, image_hash=hashlib.sha256(fake).hexdigest())

    def test_mismatched_png_dimensions_rejected(self):
        with self.assertRaises(ValueError):
            self.run_case(source_width=1500)

    def test_broken_manifest_triplet_rejected(self):
        m = json.loads(self.manifest)
        m["evidence_records"].pop()
        bad = json.dumps(m).encode()
        with self.assertRaises(ValueError):
            self.run_case(manifest=bad,
                          export_bundle_hash=hashlib.sha256(bad).hexdigest())

    def test_manifest_cross_case_rejected(self):
        m = json.loads(self.manifest)
        m["evidence_records"][0]["same_trace_case_id"] = "DIFFERENT_SYNTHETIC_CASE"
        bad = json.dumps(m).encode()
        with self.assertRaises(ValueError):
            self.run_case(manifest=bad,
                          export_bundle_hash=hashlib.sha256(bad).hexdigest())

    def test_unsigned_or_out_of_scope_claim_rejected(self):
        with self.assertRaises(ValueError):
            self.run_case(native_source="yes")
        with self.assertRaises(ValueError):
            self.run_case(schema="WRONG")
        a = dict(self.claim)
        a["extra_private_field"] = "not allowed"
        with self.assertRaises(ValueError):
            verify(self.image, self.manifest, a)

if __name__ == "__main__":
    unittest.main()
