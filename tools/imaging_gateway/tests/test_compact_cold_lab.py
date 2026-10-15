"""Adversarial LAB-only compact cold ciphertext archival tests."""
from dataclasses import replace
import hashlib
import unittest

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from tools.imaging_gateway import compact_cold_lab as c
from tools.imaging_gateway import migration_lab as m
from tools.imaging_gateway import journal_lab as j


class CompactColdTests(unittest.TestCase):
    def setUp(self):
        self.legacy = b"L" * 32
        self.jkey = b"J" * 32
        self.akey = b"A" * 32
        self.target = {"ab" * 16: b"T" * 32}
        self.clear = b"synthetic-cold-archive-only"
        self.identity = "e" * 64

    def history(self, clear=None):
        clear = self.clear if clear is None else clear
        digest = hashlib.sha256(clear).hexdigest()
        nonce = b"synthetic123"
        aad = ("DC06A|lab_m|workstation_m|" + self.identity).encode("ascii")
        source = b"DC6A" + nonce + AESGCM(self.legacy).encrypt(nonce, clear, aad)
        state = m.begin(source, cabinet="lab_m", workstation="workstation_m",
                        identity=self.identity, digest=digest,
                        legacy_key=self.legacy)
        records, anchor = j.initialize(
            state, journal_key=self.jkey,
            legacy_key=self.legacy, keys=self.target)
        prepared = m.prepare(state, expected_revision=0,
                             legacy_key=self.legacy,
                             target_key_id="ab" * 16, keys=self.target)
        records, anchor = j.append(
            records, anchor, prepared,
            journal_key=self.jkey, legacy_key=self.legacy, keys=self.target)
        verified = m.verify(prepared, expected_revision=1,
                            legacy_key=self.legacy, keys=self.target)
        records, anchor = j.append(
            records, anchor, verified,
            journal_key=self.jkey, legacy_key=self.legacy, keys=self.target)
        return records, anchor

    def packed(self, history=None, anchor=None, store=None):
        if history is None:
            history, anchor = self.history()
        store = c.VolatileBlobStore() if store is None else store
        bundle = c.pack_verified(
            history, anchor, store=store, archive_key=self.akey,
            journal_key=self.jkey, legacy_key=self.legacy, keys=self.target)
        return history, anchor, store, bundle

    def read(self, bundle, anchor, store, *, key=None):
        return c.reassemble_verified(
            bundle, anchor, store=store, archive_key=key or self.akey,
            journal_key=self.jkey, legacy_key=self.legacy, keys=self.target)

    def test_tiny_history_roundtrip_and_dedup(self):
        history, anchor, store, bundle = self.packed()
        self.assertEqual(len(history.records), 3)
        self.assertEqual(len(store._blobs), 2)
        self.assertEqual(len(bundle.records), 3)
        self.assertNotIn(self.clear, repr(bundle).encode("utf-8"))
        self.assertEqual(self.read(bundle, anchor, store), history)

    def test_wrong_key_tampered_seal_and_trusted_head_refuse(self):
        history, anchor, store, bundle = self.packed()
        with self.assertRaisesRegex(c.CompactColdLabError,
                                    "ARCHIVE_SEAL_REFUSE"):
            self.read(bundle, anchor, store, key=b"Z" * 32)
        with self.assertRaisesRegex(c.CompactColdLabError,
                                    "ARCHIVE_SEAL_REFUSE"):
            self.read(replace(bundle, seal="0"*64), anchor, store)
        stale = replace(anchor, sequence=anchor.sequence - 1)
        with self.assertRaisesRegex(c.CompactColdLabError,
                                    "INDEPENDENT_HEAD_MISMATCH"):
            self.read(bundle, stale, store)
        altered = replace(bundle.records[-1], mac="0"*64)
        bad = replace(bundle, records=bundle.records[:-1] + (altered,))
        with self.assertRaisesRegex(c.CompactColdLabError,
                                    "ARCHIVE_SEAL_REFUSE"):
            self.read(bad, anchor, store)

    def test_missing_and_mutated_ciphertext_fail_closed(self):
        history, anchor, store, bundle = self.packed()
        key = bundle.records[-1].snapshot.candidate.sha256
        original = store._blobs.pop(key)
        with self.assertRaisesRegex(c.CompactColdLabError,
                                    "BLOB_MISSING_REFUSE"):
            self.read(bundle, anchor, store)
        store._blobs[key] = original[:-1] + bytes([original[-1] ^ 1])
        with self.assertRaisesRegex(c.CompactColdLabError,
                                    "BLOB_INTEGRITY_REFUSE"):
            self.read(bundle, anchor, store)
        store._blobs[key] = original
        self.assertEqual(self.read(bundle, anchor, store), history)

    def test_rollback_head_cannot_be_inferred_from_archive_alone(self):
        records, head, store, bundle = self.packed()
        older = j.Journal(records.records[:-1])
        rec = older.records[-1]
        old_head = j.TrustedAnchor(rec.sequence, rec.mac)
        older_store = c.VolatileBlobStore()
        old_pack = c.pack_verified(
            older, old_head, store=older_store, archive_key=self.akey,
            journal_key=self.jkey, legacy_key=self.legacy, keys=self.target)
        with self.assertRaisesRegex(c.CompactColdLabError,
                                    "INDEPENDENT_HEAD_MISMATCH"):
            self.read(old_pack, head, older_store)
        # NEGATIVE: caller can roll back BOTH archive and fake anchor.
        # This is why an independently maintained monotonic witness is required.
        self.assertEqual(self.read(old_pack, old_head, older_store), older)

    def test_true_50mib_encrypted_media_three_step_roundtrip(self):
        """Actual AES-GCM codec maximum, not a simulated size field."""
        clear = b"x" * (50 * 1024 * 1024)
        history, anchor = self.history(clear)
        expanded = sum(
            len(r.snapshot.source) +
            (len(r.snapshot.candidate) if r.snapshot.candidate else 0)
            for r in history.records)
        self.assertGreater(expanded, 128 * 1024 * 1024)
        store = c.VolatileBlobStore()
        _, _, store, bundle = self.packed(history, anchor, store)
        self.assertEqual(len(store._blobs), 2)
        self.assertLessEqual(store.distinct_bytes(), 101 * 1024 * 1024)
        self.assertEqual(self.read(bundle, anchor, store), history)

    def test_invalid_record_or_bad_archive_key_never_packs(self):
        history, anchor = self.history()
        bad = j.Journal(history.records[:-1] +
                        (replace(history.records[-1], mac="0"*64),))
        with self.assertRaisesRegex(c.CompactColdLabError,
                                    "UNAUTHENTICATED_HISTORY_REFUSE"):
            self.packed(bad, anchor)
        with self.assertRaisesRegex(c.CompactColdLabError,
                                    "ARCHIVE_KEY_DOMAIN_REFUSE"):
            c.pack_verified(history, anchor, store=c.VolatileBlobStore(),
                            archive_key=self.jkey, journal_key=self.jkey,
                            legacy_key=self.legacy, keys=self.target)


if __name__ == "__main__":
    unittest.main()
