"""LOT06-J crash-state and adversarial recovery tests; synthetic media only."""
from dataclasses import FrozenInstanceError, replace
import hashlib
from pathlib import Path
import unittest

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from tools.imaging_gateway import migration_lab as m


class MigrationStateMachineTests(unittest.TestCase):
    def setUp(self):
        self.media = b"\x89PNG\r\n\x1a\n" + b"synthetic-06-j-not-patient-data"
        self.digest = hashlib.sha256(self.media).hexdigest()
        self.legacy_key = b"L" * 32
        self.key1 = b"N" * 32
        self.key2 = b"Q" * 32
        self.key_id = "1234567890abcdef" * 2
        self.other_id = "abcdef1234567890" * 2
        self.keys = {self.key_id: self.key1, self.other_id: self.key2}
        self.identity = "d" * 64
        self.scope = dict(
            cabinet="cabinet-test", workstation="workstation-01",
            identity=self.identity, digest=self.digest
        )
        self.legacy = self.old_blob(self.identity)
        self.original = bytes(self.legacy)
        self.s0 = m.begin(self.legacy, legacy_key=self.legacy_key, **self.scope)

    def old_blob(self, identity):
        nonce = b"synthetic123"  # 12 bytes
        aad = ("DC06A|cabinet-test|workstation-01|" + identity).encode("ascii")
        return b"DC6A" + nonce + AESGCM(self.legacy_key).encrypt(
            nonce, self.media, aad
        )

    def prepare(self, state=None):
        state = self.s0 if state is None else state
        return m.prepare(state, expected_revision=state.revision,
                         legacy_key=self.legacy_key,
                         target_key_id=self.key_id, keys=self.keys)

    def verify(self, state):
        return m.verify(state, expected_revision=state.revision,
                        legacy_key=self.legacy_key, keys=self.keys)

    def commit(self, state):
        return m.commit(state, expected_revision=state.revision,
                        legacy_key=self.legacy_key, keys=self.keys)

    def active(self, state, keys=None):
        return m.read_active(state, legacy_key=self.legacy_key,
                             keys=self.keys if keys is None else keys)

    def rollback(self, state, operator_confirmed=True):
        return m.rollback(state, expected_revision=state.revision,
                          legacy_key=self.legacy_key,
                          operator_confirmed=operator_confirmed)

    def test_full_prepare_verify_commit_and_restart(self):
        p = self.prepare()
        v = self.verify(p)
        c = self.commit(v)
        self.assertEqual((p.phase, v.phase, c.phase),
                         ("PREPARED", "VERIFIED", "COMMITTED"))
        self.assertEqual([p.revision, v.revision, c.revision], [1, 2, 3])
        for state in (self.s0, p, v, c):
            self.assertIs(m.restart(state, legacy_key=self.legacy_key,
                                    keys=self.keys), state)
            self.assertEqual(self.active(state), self.media)
            self.assertEqual(state.source, self.original)
            self.assertEqual(state.source_sha256, hashlib.sha256(self.original).hexdigest())
        self.assertTrue(c.candidate.startswith(b"DC6B"))
        self.assertEqual(c.candidate[4:20].hex(), self.key_id)
        self.assertNotEqual(c.candidate, self.original)

    def test_crash_after_each_checkpoint_no_implicit_promotion(self):
        for checkpoint, expected_phase, revision in (
            ("source", "SOURCE", 0), ("prepare", "PREPARED", 1),
            ("verify", "VERIFIED", 2), ("commit", "COMMITTED", 3)
        ):
            with self.subTest(checkpoint=checkpoint):
                with self.assertRaises(m.SimulatedCrash) as caught:
                    m.exercise(self.s0, legacy_key=self.legacy_key,
                               target_key_id=self.key_id, keys=self.keys,
                               crash_after=checkpoint)
                saved = caught.exception.checkpoint
                self.assertEqual((saved.phase, saved.revision),
                                 (expected_phase, revision))
                self.assertEqual(self.active(m.restart(
                    saved, legacy_key=self.legacy_key, keys=self.keys
                )), self.media)
                self.assertEqual(saved.source, self.original)
                if checkpoint in ("prepare", "verify"):
                    self.assertNotEqual(saved.phase, "COMMITTED")

    def test_verified_crash_can_resume_explicit_commit(self):
        with self.assertRaises(m.SimulatedCrash) as error:
            m.exercise(self.s0, legacy_key=self.legacy_key,
                       target_key_id=self.key_id, keys=self.keys,
                       crash_after="verify")
        saved = m.restart(error.exception.checkpoint,
                          legacy_key=self.legacy_key, keys=self.keys)
        self.assertEqual(self.commit(saved).phase, "COMMITTED")

    def test_unprepared_commit_and_repeated_transitions_rejected(self):
        with self.assertRaisesRegex(m.MigrationLabError, "VERIFY_REQUIRED"):
            self.commit(self.s0)
        with self.assertRaisesRegex(m.MigrationLabError, "INVALID_TRANSITION"):
            self.verify(self.s0)
        prepared = self.prepare()
        with self.assertRaisesRegex(m.MigrationLabError, "VERIFY_REQUIRED"):
            self.commit(prepared)
        with self.assertRaisesRegex(m.MigrationLabError, "INVALID_TRANSITION"):
            self.prepare(prepared)
        done = self.commit(self.verify(prepared))
        with self.assertRaisesRegex(m.MigrationLabError, "VERIFY_REQUIRED"):
            self.commit(done)

    def test_stale_revision_and_boolean_revision_refused(self):
        state = self.prepare()
        for revision in (0, True, 9, None):
            with self.subTest(revision=revision):
                with self.assertRaisesRegex(m.MigrationLabError, "STALE_CHECKPOINT"):
                    m.verify(state, expected_revision=revision,
                             legacy_key=self.legacy_key, keys=self.keys)
                with self.assertRaisesRegex(m.MigrationLabError, "STALE_CHECKPOINT"):
                    m.rollback(state, expected_revision=revision,
                               legacy_key=self.legacy_key, operator_confirmed=True)

    def test_frozen_snapshot_cannot_in_place_change(self):
        with self.assertRaises(FrozenInstanceError):
            self.s0.phase = "COMMITTED"

    def test_corrupt_legacy_source_or_seal_never_promotes_or_rolls_back(self):
        prepared = self.prepare()
        for corrupt in (
            replace(prepared, source=prepared.source[:-1] + b"x"),
            replace(prepared, source_sha256="0" * 64),
            replace(prepared, digest="b" * 64),
            replace(prepared, identity="e" * 64),
        ):
            with self.subTest():
                with self.assertRaises(m.MigrationLabError):
                    m.restart(corrupt, legacy_key=self.legacy_key, keys=self.keys)
                with self.assertRaises(m.MigrationLabError):
                    self.rollback(corrupt)

    def test_mutated_candidate_blocks_verify_commit_restart(self):
        p = self.prepare()
        broken = replace(p, candidate=p.candidate[:-1] + b"x")
        with self.assertRaisesRegex(m.MigrationLabError, "CANDIDATE_CHECKPOINT_INVALID"):
            self.verify(broken)
        with self.assertRaises(m.MigrationLabError):
            m.restart(broken, legacy_key=self.legacy_key, keys=self.keys)
        v = self.verify(p)
        with self.assertRaises(m.MigrationLabError):
            self.commit(replace(v, candidate_sha256="1" * 64))

    def test_explicit_rollback_restores_from_corrupted_committed_candidate(self):
        committed = self.commit(self.verify(self.prepare()))
        corrupted = replace(committed, candidate=committed.candidate[:-1] + b"x")
        with self.assertRaises(m.MigrationLabError):
            self.active(corrupted)
        restored = self.rollback(corrupted)
        self.assertEqual(restored.phase, "ROLLED_BACK")
        self.assertEqual(restored.revision, 4)
        self.assertIsNone(restored.candidate)
        self.assertEqual(restored.source, self.original)
        self.assertEqual(self.active(restored), self.media)

    def test_missing_new_key_blocks_restart_and_explicit_rollback_still_works(self):
        c = self.commit(self.verify(self.prepare()))
        with self.assertRaisesRegex(m.MigrationLabError, "CANDIDATE_UNAVAILABLE"):
            m.restart(c, legacy_key=self.legacy_key, keys={self.other_id: self.key2})
        r = self.rollback(c)
        self.assertEqual(self.active(r, keys={}), self.media)

    def test_missing_legacy_key_blocks_even_committed_recovery(self):
        c = self.commit(self.verify(self.prepare()))
        with self.assertRaisesRegex(m.MigrationLabError, "LEGACY_SOURCE_UNAVAILABLE"):
            m.restart(c, legacy_key=b"X" * 32, keys=self.keys)
        with self.assertRaisesRegex(m.MigrationLabError, "LEGACY_SOURCE_UNAVAILABLE"):
            m.rollback(c, expected_revision=c.revision,
                       legacy_key=b"X" * 32, operator_confirmed=True)

    def test_operator_gate_required_even_if_candidate_corrupt(self):
        c = self.commit(self.verify(self.prepare()))
        with self.assertRaisesRegex(m.MigrationLabError, "OPERATOR_GATE_REQUIRED"):
            self.rollback(c, operator_confirmed=False)
        with self.assertRaisesRegex(m.MigrationLabError, "OPERATOR_GATE_REQUIRED"):
            self.rollback(c, operator_confirmed=1)
        r = self.rollback(c)
        with self.assertRaisesRegex(m.MigrationLabError, "INVALID_TRANSITION"):
            self.rollback(r)

    def test_rollback_before_commit_and_retry_keeps_monotonic_local_revision(self):
        prepared = self.prepare()
        rolled = self.rollback(prepared)
        self.assertEqual(rolled.revision, 2)
        self.assertEqual(self.active(rolled), self.media)
        retried = self.prepare(rolled)
        self.assertEqual(retried.revision, 3)
        self.assertEqual(self.commit(self.verify(retried)).revision, 5)

    def test_unknown_target_reused_key_and_invalid_failpoint(self):
        with self.assertRaisesRegex(m.MigrationLabError, "PREPARE_REFUSED"):
            m.prepare(self.s0, expected_revision=0, legacy_key=self.legacy_key,
                      target_key_id=self.key_id, keys={})
        with self.assertRaisesRegex(m.MigrationLabError, "PREPARE_REFUSED"):
            m.prepare(self.s0, expected_revision=0, legacy_key=self.legacy_key,
                      target_key_id=self.key_id, keys={self.key_id: self.legacy_key})
        with self.assertRaisesRegex(m.MigrationLabError, "INVALID_FAILPOINT"):
            m.exercise(self.s0, legacy_key=self.legacy_key, target_key_id=self.key_id,
                       keys=self.keys, crash_after="after-delete")

    def test_candidate_header_key_id_replay_and_scope_mismatch(self):
        p = self.prepare()
        tampered = replace(p, target_key_id=self.other_id)
        with self.assertRaises(m.MigrationLabError):
            self.verify(tampered)
        copied = replace(
            p, candidate=p.candidate[:4] + bytes.fromhex(self.other_id) + p.candidate[20:]
        )
        copied = replace(copied, target_key_id=self.other_id,
                         candidate_sha256=hashlib.sha256(copied.candidate).hexdigest())
        with self.assertRaisesRegex(m.MigrationLabError, "CANDIDATE_UNAVAILABLE"):
            self.verify(copied)
        with self.assertRaises(m.MigrationLabError):
            self.active(replace(p, workstation="another-station"))

    def test_checkpoint_invalid_shapes_and_phase_forgery(self):
        for invalid in (
            replace(self.s0, phase="UNRECOGNIZED"),
            replace(self.s0, phase="COMMITTED"),
            replace(self.s0, revision=True),
            replace(self.s0, revision=-1),
            replace(self.s0, candidate=b"fake"),
            replace(self.s0, source_sha256="X" * 64),
        ):
            with self.subTest(invalid=invalid.phase):
                with self.assertRaises(m.MigrationLabError):
                    m.restart(invalid, legacy_key=self.legacy_key, keys=self.keys)

    def test_no_filesystem_sql_or_live_wiring(self):
        folder = Path(__file__).resolve().parents[1]
        code = (folder / "migration_lab.py").read_text(encoding="utf-8")
        for forbidden in ("sqlite3", "os.replace", "os.unlink", "open(", "Path(",
                          "HotFolder(", "os.fsync", "sqlalchemy"):
            self.assertNotIn(forbidden, code)
        for active in ("gateway.py", "cli.py"):
            self.assertNotIn("migration_lab", (folder / active).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
