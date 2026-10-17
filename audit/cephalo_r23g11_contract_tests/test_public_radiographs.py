"""Source-only synthetic unit tests; original JPEG bytes are tested in CI's smoke step."""
import copy
import unittest
from pathlib import Path

from scripts.cephalo_r23g11_public_radiograph_smoke import (
    G4_CAPTURE, REGISTRY, jpeg_dimensions, load, validate_registry,
)

ROOT = Path(__file__).resolve().parents[2]

def fixtures():
    return load(ROOT / REGISTRY), (ROOT / G4_CAPTURE).read_text(encoding="utf-8")

def synthetic_sof(width=320, height=240):
    # Minimal SOI + SOF0 header for a parser unit test; NOT radiographic pixels.
    return (b"\xff\xd8\xff\xc0\x00\x11\x08" +
            height.to_bytes(2, "big") + width.to_bytes(2, "big") +
            b"\x03\x01\x11\x00\x02\x11\x00\x03\x11\x00")

class PublicRadiographs(unittest.TestCase):
    def test_exact_two_public_sources_match_g4_contract(self):
        registry, capture = fixtures()
        rows = validate_registry(registry, capture)
        self.assertEqual([x["id"] for x in rows], ["anug", "challiyan"])
        self.assertTrue(all(x["license"] == "CC BY-SA 4.0" for x in rows))

    def test_source_hash_must_not_change(self):
        registry, capture = fixtures()
        registry["cases"][0]["sha1"] = "0"*40
        with self.assertRaises(ValueError):
            validate_registry(registry, capture)

    def test_source_url_must_not_change(self):
        registry, capture = fixtures()
        registry["cases"][0]["url"] = "https://example.invalid/fake.jpg"
        with self.assertRaises(ValueError):
            validate_registry(registry, capture)

    def test_license_cannot_be_widened(self):
        registry, capture = fixtures()
        registry["cases"][1]["license"] = "CC0"
        with self.assertRaises(ValueError):
            validate_registry(registry, capture)

    def test_unknown_third_radiograph_is_not_silent_acceptance(self):
        registry, capture = fixtures()
        registry["cases"].append(copy.deepcopy(registry["cases"][0]))
        with self.assertRaises(ValueError):
            validate_registry(registry, capture)

    def test_forged_clinical_release_rejected(self):
        registry, capture = fixtures()
        registry["clinical_release"] = True
        with self.assertRaises(ValueError):
            validate_registry(registry, capture)

    def test_forged_orientation_or_calibration_rejected(self):
        for flag in ("calibration_verified", "orientation_verified", "manual_landmarks_verified"):
            registry, capture = fixtures()
            registry["cases"][1][flag] = True
            with self.assertRaises(ValueError):
                validate_registry(registry, capture)

    def test_valid_header_dimensions(self):
        self.assertEqual(jpeg_dimensions(synthetic_sof()), (320, 240))

    def test_malformed_jpeg_header_fails_closed(self):
        with self.assertRaises(ValueError):
            jpeg_dimensions(b"not jpeg")
        with self.assertRaises(ValueError):
            jpeg_dimensions(b"\xff\xd8\xff\xc0\x00\x11")
        with self.assertRaises(ValueError):
            jpeg_dimensions(synthetic_sof(width=0))
        with self.assertRaises(ValueError):
            jpeg_dimensions(b"\xff\xd8\xff\xda\x00\x02")

if __name__ == "__main__":
    unittest.main()
