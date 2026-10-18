"""LOT05.7-H real SQLCipher fixture + FAKE-only authority/multicomponent lab.

17 isolated cases, no actual worker, HTTP endpoint or SCM permission changes.
This test deliberately documents the existing _assert_owner(None) gap.
"""
from __future__ import annotations

import copy
import os
import secrets
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from backend.tests import test_legacy_sql_057e_real_backupservice_sqlcipher_head as e
from backend.services import legacy_migration_recovery_authority_lab_v15 as h
from backend.services.legacy_migration_restore_policy_v15 import require_clinical_apply


class SyntheticAuthorityBundleLab(unittest.TestCase):
    @classmethod
    def _seed_fake_orm(cls):
        e.RealEncryptedBackupServiceLab._seed_fake_orm.__func__(cls)

    @classmethod
    def setUpClass(cls):
        if os.environ.get(h.FAKE_FLAG) != "1":
            raise h.AuthorityHandoffDenied("FAKE_ONLY_DISABLED")
        e.RealEncryptedBackupServiceLab.setUpClass.__func__(cls)
        from sqlalchemy import text
        with cls.engine.connect() as c:
            cls.owners = tuple(c.execute(text(
                "SELECT id FROM users WHERE employer_id IS NULL ORDER BY id"
            )).scalars())
        if len(cls.owners) != 2:
            raise h.AuthorityHandoffDenied("FAKE_OWNERS_REQUIRED")
        cls.principal = SimpleNamespace(id=cls.owners[0], role="DENTISTE",
                                         is_active=True, employer_id=None,
                                         approval_status="approved")

    @classmethod
    def tearDownClass(cls):
        e.RealEncryptedBackupServiceLab.tearDownClass.__func__(cls)

    def setUp(self):
        e.RealEncryptedBackupServiceLab.setUp(self)
        self.bundle = tempfile.TemporaryDirectory(prefix="lot05e_fake_sqlcipher_")
        self.root_bundle = Path(self.bundle.name)
        (self.root_bundle / "media-fake").mkdir()
        # Real SQLCipher bytes from the genuine E operator/ORM fixture, no
        # synthetic SQLite metadata.create_all or manual Alembic stamp.
        (self.root_bundle / "database.db").write_bytes(self.source.read_bytes())
        (self.root_bundle / "license_fake.bin").write_bytes(b"FAKE_VAULT_NO_KEYS")
        (self.root_bundle / "media-fake" / "image.fake").write_bytes(b"FAKE_IMG")
        (self.root_bundle / "media-fake" / "receipt.fake").write_bytes(b"FAKE_RECEIPT")
        self.manifest = h.fake_manifest(self.root_bundle)
        self.manifest_sha = h.fake_manifest_sha(self.manifest)
        self.key = secrets.token_bytes(32)
        self.job_id = "fakejob_" + secrets.token_hex(8)
        self.now = 1760000000
        self.job = {"job_id": self.job_id,
                    "owner_employer_id": self.owners[0],
                    "manifest_sha256": self.manifest_sha,
                    "state": "prepared_fake"}

    def tearDown(self):
        self.bundle.cleanup()
        e.RealEncryptedBackupServiceLab.tearDown(self)

    def ticket(self, **overrides):
        options = dict(expected_owners=self.owners, job_id=self.job_id,
                       manifest_sha=self.manifest_sha, now=self.now,
                       signing_key=self.key, bundle_root=self.root_bundle,
                       manifest=self.manifest)
        options.update(overrides)
        with self.engine.connect() as c:
            return h.fake_issue_request_ticket(c, self.principal, **options)

    def verify(self, ticket, *, job=None, **overrides):
        options = dict(expected_owner=self.owners[0],
                       manifest_sha=self.manifest_sha, now=self.now + 1,
                       signing_key=self.key, used_nonces=set(),
                       bundle_root=self.root_bundle, manifest=self.manifest)
        options.update(overrides)
        return h.fake_worker_verify_ticket(
            ticket, self.job if job is None else job, **options)

    def test_01_real_backupservice_and_multicomponent_manifest(self):
        from backend.services.backup_service import BackupService
        from backend.core.schema_runtime import assert_database_at_current_head
        from backend.tests.test_legacy_sql_057e_real_backupservice_sqlcipher_head import rows_digest
        original = rows_digest(self.engine)
        backup = e.RealEncryptedBackupServiceLab.backup(self)
        (self.root_bundle / "database.db").unlink()
        BackupService.restore_backup(
            backup, self.root_bundle / "database.db",
            verify_sqlcipher=True, passphrase=self.fake_key,
        )
        engine = e.RealEncryptedBackupServiceLab.restored_engine(
            self, self.root_bundle / "database.db")
        try:
            assert_database_at_current_head(engine)
            self.assertEqual(rows_digest(engine), original)
        finally:
            engine.dispose()
        manifest = h.fake_manifest(self.root_bundle)
        self.assertEqual(h.verify_fake_manifest(self.root_bundle, manifest),
                         h.fake_manifest_sha(manifest))
        self.assertEqual([x["name"] for x in manifest["components"]],
                         list(h.NAMES))

    def test_02_actual_owner_helper_and_fake_worker_handoff(self):
        token = self.ticket()
        verdict = self.verify(token)
        self.assertIs(verdict["fake_handoff_verified"], True)
        self.assertIs(verdict["clinical_restore_permitted"], False)
        self.assertIs(verdict["clinical_import_permitted"], False)
        self.assertEqual(h.verify_fake_manifest(self.root_bundle, self.manifest),
                         self.manifest_sha)

    def test_03_no_clinical_apply_even_with_valid_signed_ticket(self):
        token = self.ticket()
        self.assertTrue(self.verify(token)["fake_handoff_verified"])
        for name in ("RESTORE_ENABLED", "LOT05H_ENABLE_CLINICAL"):
            with self.subTest(name=name), patch.dict(os.environ, {name:"1"}):
                with self.assertRaisesRegex(PermissionError, "CLINICAL_APPLY_DISABLED"):
                    require_clinical_apply(token, self.principal)

    def test_04_missing_or_forged_request_owner_denied(self):
        from backend.services.legacy_migration_gateway_v15 import require_cabinet_owner
        with self.engine.connect() as c:
            with self.assertRaisesRegex(h.AuthorityHandoffDenied,
                                        "REQUEST_OWNER_OR_TENANT_DENIED"):
                h.fake_issue_request_ticket(
                    c, None, expected_owners=self.owners, job_id=self.job_id,
                    manifest_sha=self.manifest_sha, now=self.now,
                    signing_key=self.key, bundle_root=self.root_bundle,
                    manifest=self.manifest)
            for change in (
                {"role":"SECRETAIRE"}, {"is_active":False},
                {"employer_id":self.owners[1]}, {"approval_status":"pending"},
                {"id":0}, {"id":self.owners[1],"employer_id":self.owners[0]}
            ):
                principal = SimpleNamespace(**{**vars(self.principal), **change})
                with self.subTest(change=change):
                    with self.assertRaises((h.AuthorityHandoffDenied, PermissionError)):
                        h.fake_issue_request_ticket(
                            c, principal, expected_owners=self.owners,
                            job_id=self.job_id, manifest_sha=self.manifest_sha,
                            now=self.now, signing_key=self.key,
                            bundle_root=self.root_bundle, manifest=self.manifest)

    def test_05_ticket_claim_and_signature_mutations_denied(self):
        token = self.ticket()
        for key, value in (("owner",self.owners[1]),("job","fakejob_"+"0"*16),
                           ("manifest","0"*64),("expires",self.now+500),
                           ("purpose","CLINICAL_RESTORE")):
            candidate = copy.deepcopy(token)
            candidate["claims"][key] = value
            with self.subTest(key=key), self.assertRaisesRegex(
                    h.AuthorityHandoffDenied, "TICKET_SIGNATURE_DENIED"):
                self.verify(candidate)
        candidate = copy.deepcopy(token)
        candidate["mac"] = "f"*64
        with self.assertRaisesRegex(h.AuthorityHandoffDenied, "TICKET_SIGNATURE_DENIED"):
            self.verify(candidate)

    def test_06_wrong_worker_signing_key_denied(self):
        with self.assertRaisesRegex(h.AuthorityHandoffDenied, "TICKET_SIGNATURE_DENIED"):
            self.verify(self.ticket(), signing_key=secrets.token_bytes(32))

    def test_07_worker_missing_owner_is_not_optional(self):
        token = self.ticket()
        candidate = dict(self.job, owner_employer_id=None)
        with self.assertRaisesRegex(h.AuthorityHandoffDenied,
                                    "JOB_OWNER_OR_CONTENT_MISMATCH"):
            self.verify(token, job=candidate)
        with self.assertRaisesRegex(h.AuthorityHandoffDenied,
                                    "WORKER_BOUNDARY_INVALID"):
            self.verify(token, expected_owner=None)

    def test_08_worker_job_id_or_manifest_changed_denied(self):
        token = self.ticket()
        for delta in ({"job_id":"fakejob_"+"1"*16},
                      {"manifest_sha256":"a"*64},
                      {"state":"applying"},
                      {"owner_employer_id":self.owners[1]}):
            with self.subTest(delta=delta), self.assertRaisesRegex(
                    h.AuthorityHandoffDenied, "JOB_OWNER_OR_CONTENT_MISMATCH"):
                self.verify(token, job={**self.job, **delta})

    def test_09_expired_or_not_yet_issued_ticket_denied(self):
        token = self.ticket()
        for clock in (self.now-1, self.now+300, self.now+3600):
            with self.subTest(clock=clock), self.assertRaisesRegex(
                    h.AuthorityHandoffDenied, "SIGNED_CLAIMS_OUT_OF_SCOPE"):
                self.verify(token, now=clock)

    def test_10_valid_ticket_is_one_time_in_lab(self):
        ticket = self.ticket()
        used = set()
        self.assertTrue(self.verify(ticket, used_nonces=used)["fake_handoff_verified"])
        with self.assertRaisesRegex(h.AuthorityHandoffDenied, "REPLAY_DENIED"):
            self.verify(ticket, used_nonces=used)

    def test_11_malformed_ticket_and_job_denied(self):
        token = self.ticket()
        for wrong in ({}, {"claims":token["claims"]}, {"claims":{}, "mac":token["mac"]}):
            with self.assertRaises(h.AuthorityHandoffDenied):
                self.verify(wrong)
        with self.assertRaisesRegex(h.AuthorityHandoffDenied, "JOB_ATTESTATION_MISSING"):
            self.verify(token, job={**self.job, "extra_auth":True})

    def test_12_mutated_fake_encrypted_db_is_refused_by_manifest(self):
        path = self.root_bundle / "database.db"
        with path.open("ab") as stream:
            stream.write(b"FAKE_APPEND")
        with self.assertRaisesRegex(h.AuthorityHandoffDenied,
                                    "MULTICOMPONENT_INTEGRITY_DENIED"):
            h.verify_fake_manifest(self.root_bundle, self.manifest)

    def test_13_mutated_media_or_license_vault_is_refused(self):
        for filename in ("media-fake/image.fake", "media-fake/receipt.fake",
                         "license_fake.bin"):
            path = self.root_bundle / filename
            before = path.read_bytes()
            path.write_bytes(before + b"BAD")
            with self.subTest(name=filename), self.assertRaisesRegex(
                    h.AuthorityHandoffDenied, "MULTICOMPONENT_INTEGRITY_DENIED"):
                h.verify_fake_manifest(self.root_bundle, self.manifest)
            path.write_bytes(before)

    def test_14_missing_or_extra_fake_media_refused(self):
        path = self.root_bundle / "media-fake" / "receipt.fake"
        original = path.read_bytes()
        path.unlink()
        with self.assertRaisesRegex(h.AuthorityHandoffDenied,
                                    "FAKE_COMPONENT_SET_MISMATCH"):
            h.fake_manifest(self.root_bundle)
        path.write_bytes(original)
        extra = self.root_bundle / "media-fake" / "rogue.fake"
        extra.write_bytes(b"EXTRA")
        with self.assertRaisesRegex(h.AuthorityHandoffDenied,
                                    "FAKE_COMPONENT_SET_MISMATCH"):
            h.fake_manifest(self.root_bundle)

    def test_15_symlinked_component_or_directory_denied(self):
        path = self.root_bundle / "license_fake.bin"
        with patch.object(Path, "is_symlink",
                          autospec=True,
                          side_effect=lambda instance: instance == path):
            with self.assertRaisesRegex(h.AuthorityHandoffDenied,
                                        "UNEXPECTED_OR_LINKED_COMPONENT"):
                h.fake_manifest(self.root_bundle)

    def test_16_manifest_forgery_or_changed_component_size_denied(self):
        invalid = copy.deepcopy(self.manifest)
        invalid["components"][0]["size"] += 1
        with self.assertRaisesRegex(h.AuthorityHandoffDenied,
                                    "MULTICOMPONENT_INTEGRITY_DENIED"):
            h.verify_fake_manifest(self.root_bundle, invalid)
        invalid = copy.deepcopy(self.manifest)
        invalid["admin"] = "allow_restore"
        with self.assertRaisesRegex(h.AuthorityHandoffDenied, "MANIFEST_MALFORMED"):
            h.verify_fake_manifest(self.root_bundle, invalid)

    def test_17_guided_restore_current_owner_none_gap_does_not_bypass_h(self):
        from backend.services.guided_restore import GuidedRestoreService
        observed = {"owner_employer_id":self.owners[0]}
        # Existing production helper currently skips when owner=None.
        self.assertIsNone(GuidedRestoreService._assert_owner(observed, None))
        # H deliberately does not trust that helper, and requires numeric owner.
        with self.assertRaisesRegex(h.AuthorityHandoffDenied,
                                    "WORKER_BOUNDARY_INVALID"):
            self.verify(self.ticket(), expected_owner=None)
        with self.assertRaises(PermissionError):
            GuidedRestoreService._assert_owner(observed, self.owners[1])

    def test_18_fake_flag_missing_denies_issue_verify_and_components(self):
        token = self.ticket()
        with patch.dict(os.environ, {h.FAKE_FLAG:"0"}):
            for call in (
                lambda: h.fake_manifest(self.root_bundle),
                lambda: self.ticket(),
                lambda: self.verify(token),
            ):
                with self.subTest(operation=str(call)), self.assertRaisesRegex(
                        h.AuthorityHandoffDenied, "FAKE_ONLY_DISABLED"):
                    call()


    def test_19_signed_ticket_cannot_hide_bundle_changed_before_worker(self):
        ticket = self.ticket()
        media = self.root_bundle / "media-fake" / "image.fake"
        before = media.read_bytes()
        used = set()
        media.write_bytes(before + b"AFTER_ISSUE_TAMPER")
        with self.assertRaisesRegex(h.AuthorityHandoffDenied,
                                    "MULTICOMPONENT_INTEGRITY_DENIED"):
            self.verify(ticket, used_nonces=used)
        self.assertEqual(used, set(), "a rejected ticket must not burn its nonce")
        media.write_bytes(before)
        self.assertTrue(self.verify(ticket, used_nonces=used)["fake_handoff_verified"])

    def test_20_request_cannot_issue_ticket_for_unverified_fake_bundle(self):
        media = self.root_bundle / "media-fake" / "receipt.fake"
        media.write_bytes(b"FICTITIOUS_TAMPER_BEFORE_ISSUANCE")
        with self.assertRaisesRegex(h.AuthorityHandoffDenied,
                                    "MULTICOMPONENT_INTEGRITY_DENIED"):
            self.ticket()
        # An arbitrary mismatching digest is never silently signed either.
        media.write_bytes(b"FAKE_RECEIPT")
        with self.assertRaisesRegex(h.AuthorityHandoffDenied,
                                    "REQUEST_MANIFEST_CONTENT_MISMATCH"):
            self.ticket(manifest_sha="0"*64)



if __name__ == "__main__":
    unittest.main()
