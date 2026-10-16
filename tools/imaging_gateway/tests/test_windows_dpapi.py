"""LOT06-H DPAPI lifecycle laboratory; synthetic keys and temporary files only."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools.imaging_gateway.windows import dpapi_lab as vault


class PortableDPAPIContract(unittest.TestCase):
    def test_bad_device_scope_is_rejected(self):
        for args in [("", "ws"), ("cab", "../ws"), ("cab", "é"), (None, "ws")]:
            with self.subTest(args=args), self.assertRaises(vault.KeyCustodyError):
                vault._binding(*args)

    def test_rotation_explicitly_refuses_unversioned_spool(self):
        with self.assertRaisesRegex(vault.KeyCustodyError, "^ROTATION_REQUIRES_"):
            vault.rotate_existing_spool()
        with self.assertRaisesRegex(vault.KeyCustodyError, "^ROTATION_REQUIRES_"):
            vault.rotate_existing_spool("old", "new")

    def test_foreign_machine_scope_never_accepted(self):
        binding = vault._binding("cab", "ws")
        raw = json.dumps({"version": 1, "scope": "LOCAL_MACHINE",
                          "binding": binding.hex(), "sealed": "YWJjZA=="}).encode()
        with self.assertRaisesRegex(vault.KeyCustodyError, "KEY_SCOPE_MISMATCH"):
            vault._open_record(raw, binding)

    def test_record_parser_rejects_unexpected_fields_before_dpapi(self):
        binding = vault._binding("cab", "ws")
        raw = json.dumps({"version": 1, "scope": "CURRENT_USER",
                          "binding": binding.hex(), "sealed": "AAAA",
                          "patient_id": "forbidden"}).encode()
        with patch.object(vault, "_dpapi", side_effect=AssertionError("must not run")):
            with self.assertRaisesRegex(vault.KeyCustodyError, "KEY_RECORD_INVALID"):
                vault._open_record(raw, binding)

    def test_revocation_appearing_during_unlock_stops_return(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "key.json"
            with patch.object(vault, "_read", return_value=b"synthetic"):
                def add_tombstone(*args):
                    vault._revocation_path(path).write_bytes(b"blocked")
                    return b"k" * 32
                with patch.object(vault, "_open_record", side_effect=add_tombstone):
                    with self.assertRaisesRegex(vault.KeyCustodyError, "KEY_LOCALLY_REVOKED"):
                        vault.unlock(path, "cab", "ws")

    def test_os_error_never_leaks_path_in_key_error(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "key.json"
            path.write_bytes(b"synthetic")
            with patch.object(vault.os, "open", side_effect=OSError("SECRET_PATIENT_FILE_PATH")):
                with self.assertRaises(vault.KeyCustodyError) as raised:
                    vault._read(path)
            self.assertEqual(str(raised.exception), "KEY_RECORD_UNREADABLE")

    @unittest.skipUnless(os.name != "nt", "Windows uses the real native DPAPI suite")
    def test_linux_fails_closed_without_native_dpapi(self):
        with self.assertRaisesRegex(vault.KeyCustodyError, "WINDOWS_DPAPI_REQUIRED"):
            vault._dpapi(b"k" * 32, b"e" * 32, unprotect=False)


@unittest.skipUnless(os.name == "nt", "Native Windows DPAPI required")
class NativeWindowsDPAPITests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="dc06h-synthetic-")
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.record = self.root / "sealed.json"
        self.backup = self.root / "backup.json"

    def provision(self):
        vault.provision(self.record, "cab1", "ws1")

    def test_native_dpapi_roundtrip_and_no_cleartext_at_rest(self):
        self.provision()
        key = vault.unlock(self.record, "cab1", "ws1")
        self.assertEqual(len(key), 32)
        self.assertNotIn(key, self.record.read_bytes())
        self.assertEqual(key, vault.unlock(self.record, "cab1", "ws1"))
        self.assertEqual(json.loads(self.record.read_text())["scope"], "CURRENT_USER")

    def test_another_process_same_profile_can_recover(self):
        self.provision()
        script = ("from pathlib import Path; from tools.imaging_gateway.windows "
                  "import dpapi_lab as v; k=v.unlock(Path(__import__('sys').argv[1]),"
                  "'cab1','ws1'); assert len(k)==32")
        proc = subprocess.run([sys.executable, "-c", script, str(self.record)],
                              cwd=Path(__file__).resolve().parents[3],
                              capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout, "")

    def test_wrong_workstation_or_cabinet_cannot_unseal(self):
        self.provision()
        for cabinet, device in [("cab2", "ws1"), ("cab1", "ws2")]:
            with self.subTest(cabinet=cabinet, device=device):
                with self.assertRaisesRegex(vault.KeyCustodyError, "KEY_SCOPE_MISMATCH"):
                    vault.unlock(self.record, cabinet, device)

    def test_tampering_or_missing_record_blocks_access(self):
        with self.assertRaisesRegex(vault.KeyCustodyError, "KEY_RECORD_MISSING"):
            vault.unlock(self.record, "cab1", "ws1")
        self.provision()
        obj = json.loads(self.record.read_text())
        obj["sealed"] = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        self.record.write_text(json.dumps(obj))
        with self.assertRaises(vault.KeyCustodyError):
            vault.unlock(self.record, "cab1", "ws1")

    def test_interrupted_write_does_not_autoregenerate_key(self):
        self.record.write_bytes(b'{"version":1')
        with self.assertRaises(vault.KeyCustodyError):
            vault.unlock(self.record, "cab1", "ws1")
        with self.assertRaisesRegex(vault.KeyCustodyError, "KEY_RECORD_ALREADY_EXISTS"):
            self.provision()

    def test_backup_restores_only_on_same_user_profile(self):
        self.provision()
        expected = vault.unlock(self.record, "cab1", "ws1")
        vault.backup_sealed(self.record, self.backup, "cab1", "ws1")
        self.assertEqual(self.backup.read_bytes(), self.record.read_bytes())
        self.record.unlink()
        vault.restore_same_user(self.backup, self.record, "cab1", "ws1")
        self.assertEqual(expected, vault.unlock(self.record, "cab1", "ws1"))

    def test_restore_rejects_wrong_identity_and_existing_record(self):
        self.provision()
        vault.backup_sealed(self.record, self.backup, "cab1", "ws1")
        with self.assertRaisesRegex(vault.KeyCustodyError, "KEY_RECORD_ALREADY_EXISTS"):
            vault.restore_same_user(self.backup, self.record, "cab1", "ws1")
        self.record.unlink()
        with self.assertRaisesRegex(vault.KeyCustodyError, "KEY_SCOPE_MISMATCH"):
            vault.restore_same_user(self.backup, self.record, "cab1", "ws-other")
        self.assertFalse(self.record.exists())

    def test_local_revocation_blocks_unlock_and_backup_restore(self):
        self.provision()
        vault.backup_sealed(self.record, self.backup, "cab1", "ws1")
        vault.revoke_locally(self.record, "cab1", "ws1")
        with self.assertRaisesRegex(vault.KeyCustodyError, "KEY_LOCALLY_REVOKED"):
            vault.unlock(self.record, "cab1", "ws1")
        self.record.unlink()
        with self.assertRaisesRegex(vault.KeyCustodyError, "KEY_LOCALLY_REVOKED"):
            vault.restore_same_user(self.backup, self.record, "cab1", "ws1")
        self.assertFalse(self.record.exists())

    def test_failed_dpapi_unprotect_does_not_unlock(self):
        self.provision()
        with patch.object(vault, "_dpapi", side_effect=vault.KeyCustodyError("DPAPI_UNPROTECT_FAILED")):
            with self.assertRaisesRegex(vault.KeyCustodyError, "DPAPI_UNPROTECT_FAILED"):
                vault.unlock(self.record, "cab1", "ws1")

    def test_provision_does_not_overwrite_or_rotate_live_key(self):
        self.provision()
        first = self.record.read_bytes()
        with self.assertRaisesRegex(vault.KeyCustodyError, "KEY_RECORD_ALREADY_EXISTS"):
            self.provision()
        self.assertEqual(first, self.record.read_bytes())


if __name__ == "__main__":
    unittest.main()
