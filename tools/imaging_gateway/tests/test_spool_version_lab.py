"""LOT06-I isolated versioned envelope, failure/replay abuse fixtures."""
import hashlib
from pathlib import Path
import secrets
import unittest
from unittest.mock import patch

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from tools.imaging_gateway import spool_version_lab as v


class VersionedEnvelopeTests(unittest.TestCase):
    def setUp(self):
        self.clear = b"\x89PNG\r\n\x1a\n" + b"synthetic-only-test-payload"
        self.digest = hashlib.sha256(self.clear).hexdigest()
        self.identity = "a" * 64
        self.kid1 = "0123456789abcdef" * 2
        self.kid2 = "fedcba9876543210" * 2
        self.key1 = b"x" * 32
        self.key2 = b"y" * 32
        self.keys = {self.kid1: self.key1, self.kid2: self.key2}
        self.a = dict(cabinet="cabinet-test", workstation="station1",
                      identity=self.identity, digest=self.digest)

    def encode(self, **kwargs):
        return v.encode_v2(self.clear, key_id=self.kid1, keys=self.keys, **(self.a | kwargs))

    def decode(self, blob, **kwargs):
        return v.decode_v2(blob, keys=self.keys, **(self.a | kwargs))

    def old(self):
        nonce = b"n" * 12
        aad = b"DC06A|cabinet-test|station1|" + self.identity.encode()
        return b"DC6A" + nonce + AESGCM(self.key1).encrypt(nonce, self.clear, aad)

    def test_v2_roundtrip_key_version_nonce_and_sha(self):
        first, second = self.encode(), self.encode()
        self.assertNotEqual(first, second)
        self.assertEqual(first[:4], b"DC6B")
        self.assertEqual(first[4:20].hex(), self.kid1)
        self.assertEqual(self.decode(first), self.clear)
        self.assertEqual(self.decode(second), self.clear)
        self.assertNotIn(self.clear, first)
        self.assertNotIn(self.key1, first)

    def test_new_key_can_be_selected_explicitly_and_old_key_kept(self):
        old = self.encode()
        newer = v.encode_v2(self.clear, key_id=self.kid2, keys=self.keys, **self.a)
        self.assertEqual(self.decode(newer), self.clear)
        self.assertEqual(self.decode(old), self.clear)
        with self.assertRaisesRegex(v.SpoolCodecError, "^KEY_ID_UNAVAILABLE$"):
            v.decode_v2(old, keys={self.kid2: self.key2}, **self.a)

    def test_different_cabinet_station_capture_and_digest_block(self):
        blob = self.encode()
        for kwargs in ({"cabinet": "else"}, {"workstation": "else"},
                       {"identity": "b" * 64}, {"digest": "b" * 64}):
            with self.subTest(kwargs=kwargs), self.assertRaises(v.SpoolCodecError):
                self.decode(blob, **kwargs)

    def test_mutated_authenticated_header_nonce_tag_ciphertext_block(self):
        blob = self.encode()
        for index in (0, 5, 21, len(blob) - 1, 40):
            broken = bytearray(blob)
            broken[index] ^= 1
            with self.subTest(index=index), self.assertRaises(v.SpoolCodecError):
                self.decode(bytes(broken))

    def test_invalid_ciphertext_sizes_and_wrong_magic_rejected(self):
        blob = self.encode()
        for bad in (b"", b"DC6A" + blob[4:], b"DC6B", blob[:48],
                    blob[:8], blob + (b"z" * 17)):
            if bad.startswith(b"DC6B") and len(bad) > 48:
                # Oversized extension breaks AEAD, not the bounded allocation gate.
                pass
            with self.subTest(length=len(bad)), self.assertRaises(v.SpoolCodecError):
                self.decode(bad)

    def test_size_rejection_before_unbounded_decrypt(self):
        blob = self.encode()
        with patch.object(v, "MAX_CLEAR_BYTES", 4):
            with self.assertRaisesRegex(v.SpoolCodecError, "SPOOL_ENVELOPE_SIZE_INVALID"):
                self.decode(blob)
            with self.assertRaisesRegex(v.SpoolCodecError, "SPOOL_CLEAR_SIZE_INVALID"):
                self.encode()

    def test_bad_keyring_key_id_and_key_length_fail_closed(self):
        for keys in ({}, {self.kid1: b"short"}, {self.kid1.upper(): self.key1},
                     {self.kid1: "not-bytes"}):
            with self.subTest(keys=keys), self.assertRaises(v.SpoolCodecError):
                v.encode_v2(self.clear, key_id=self.kid1, keys=keys, **self.a)
        with self.assertRaisesRegex(v.SpoolCodecError, "KEY_ID_UNAVAILABLE"):
            v.encode_v2(self.clear, key_id=self.kid1,
                        keys={self.kid2: self.key2}, **self.a)
        with self.assertRaisesRegex(v.SpoolCodecError, "INVALID_KEY_ID"):
            v.encode_v2(self.clear, key_id="legacy", keys=self.keys, **self.a)

    def test_invalid_scope_and_digest_forbid_encrypt(self):
        for kwargs in ({"cabinet": ""}, {"workstation": "bad/path"},
                       {"identity": "broken"}, {"digest": "a" * 64}):
            with self.subTest(kwargs=kwargs), self.assertRaises(v.SpoolCodecError):
                self.encode(**kwargs)

    def test_explicit_legacy_decode_and_rewrap_preserve_source(self):
        legacy = self.old()
        snapshot = bytes(legacy)
        self.assertEqual(v.decode_legacy_v1(legacy, legacy_key=self.key1, **self.a),
                         self.clear)
        candidate = v.rewrap_legacy_v1(
            legacy, legacy_key=self.key1, target_key_id=self.kid2,
            keys=self.keys, **self.a
        )
        self.assertEqual(legacy, snapshot)
        self.assertTrue(candidate.startswith(b"DC6B"))
        self.assertEqual(candidate[4:20].hex(), self.kid2)
        self.assertEqual(self.decode(candidate), self.clear)
        with self.assertRaisesRegex(v.SpoolCodecError, "V2_ENVELOPE_REQUIRED"):
            self.decode(legacy)
        with self.assertRaisesRegex(v.SpoolCodecError, "V1_ENVELOPE_REQUIRED"):
            v.decode_legacy_v1(candidate, legacy_key=self.key1, **self.a)

    def test_legacy_bad_key_scope_digest_and_corruption_never_rewrap(self):
        legacy = self.old()
        for kwargs in ({"legacy_key": self.key2},
                       {"legacy_key": self.key1, "identity": "f" * 64},
                       {"legacy_key": self.key1, "digest": "f" * 64}):
            with self.subTest(kwargs=kwargs), self.assertRaises(v.SpoolCodecError):
                v.rewrap_legacy_v1(legacy, target_key_id=self.kid2,
                                   keys=self.keys, **(self.a | kwargs))
        tampered = legacy[:-1] + bytes([legacy[-1] ^ 1])
        with self.assertRaises(v.SpoolCodecError):
            v.rewrap_legacy_v1(tampered, target_key_id=self.kid2,
                               legacy_key=self.key1, keys=self.keys, **self.a)

    def test_no_fallback_to_legacy_when_target_key_absent(self):
        legacy = self.old()
        with self.assertRaisesRegex(v.SpoolCodecError, "KEY_ID_UNAVAILABLE"):
            v.rewrap_legacy_v1(legacy, legacy_key=self.key1,
                               target_key_id=self.kid2,
                               keys={self.kid1: self.key1}, **self.a)
        self.assertEqual(v.decode_legacy_v1(legacy, legacy_key=self.key1, **self.a),
                         self.clear)

    def test_rewrap_verification_failure_does_not_succeed(self):
        legacy = self.old()
        with patch.object(v, "decode_v2", return_value=b"wrong"):
            with self.assertRaisesRegex(v.SpoolCodecError, "REWRAP_VERIFICATION_FAILED"):
                v.rewrap_legacy_v1(legacy, legacy_key=self.key1,
                                   target_key_id=self.kid2, keys=self.keys, **self.a)

    def test_no_production_wiring_or_sql_mutation(self):
        folder = Path(__file__).resolve().parents[1]
        self.assertNotIn("spool_version_lab", (folder / "cli.py").read_text())
        self.assertNotIn("spool_version_lab", (folder / "gateway.py").read_text())
        code = (folder / "spool_version_lab.py").read_text()
        self.assertNotIn("sqlite3", code)
        self.assertNotIn("os.replace", code)
        self.assertNotIn("unlink(", code)


if __name__ == "__main__":
    unittest.main()
