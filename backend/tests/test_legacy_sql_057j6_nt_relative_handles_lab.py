"""LOT05.7-J6 relative NtCreateFile on disposable fake paths, real Windows."""
from __future__ import annotations
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from backend.tests.fixtures import lot05j6_root_relative_nt_lab as nt


class NativeAnchoredWindows(unittest.TestCase):
    def setUp(self):
        if os.name != "nt":
            self.fail("J6_WIN32_REQUIRED")
        self.before = os.environ.get(nt.FLAG)
        os.environ[nt.FLAG] = "1"
        self.addCleanup(self.restore)
        self.temp = tempfile.TemporaryDirectory(prefix="lot05j6_fake_")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.folder = self.root / "inputs"
        self.folder.mkdir()
        self.file = self.folder / "payload.fake"
        self.file.write_bytes(nt.PAYLOAD)

    def restore(self):
        if self.before is None:
            os.environ.pop(nt.FLAG, None)
        else:
            os.environ[nt.FLAG] = self.before

    def deny(self, operation):
        with self.assertRaises(nt.NativeRefused):
            operation()

    def test_01_native_relative_handle_reads_good_fake(self):
        self.assertEqual(nt.anchored_fake_read(self.root), nt.PAYLOAD)

    def test_02_disabled_lab_never_opens_path(self):
        os.environ[nt.FLAG] = "0"
        self.deny(lambda: nt.anchored_fake_read(self.root))

    def test_03_wrong_root_refused(self):
        self.deny(lambda: nt.anchored_fake_read(self.folder))

    def test_04_missing_leaf_refused(self):
        self.file.unlink()
        self.deny(lambda: nt.anchored_fake_read(self.root))

    def test_05_changed_data_refused(self):
        self.file.write_bytes(b"NOT_AUTHORIZED_FAKE")
        self.deny(lambda: nt.anchored_fake_read(self.root))

    def test_06_real_hardlink_refused_by_opened_handle(self):
        os.link(self.file, self.root / "another.fake")
        self.assertEqual(self.file.stat().st_nlink, 2)
        self.deny(lambda: nt.anchored_fake_read(self.root))

    def test_07_leaf_symlink_refused_by_nt_handle(self):
        other = self.root / "alternate.fake"
        other.write_bytes(nt.PAYLOAD)
        self.file.unlink()
        self.file.symlink_to(other)
        self.deny(lambda: nt.anchored_fake_read(self.root))

    def test_08_parent_junction_refused_by_nt_handle(self):
        alternate = self.root / "alternate-inputs"
        alternate.mkdir()
        (alternate / "payload.fake").write_bytes(nt.PAYLOAD)
        self.file.unlink()
        self.folder.rmdir()
        cmd = subprocess.run(["cmd.exe", "/c", "mklink", "/J",
                              str(self.folder), str(alternate)],
                             capture_output=True, text=True)
        self.assertEqual(cmd.returncode, 0, cmd.stderr)
        try:
            self.assertTrue(self.folder.is_junction())
            self.deny(lambda: nt.anchored_fake_read(self.root))
        finally:
            self.folder.rmdir()

    def test_09_synthetic_rename_of_parent_after_handle_open(self):
        # If Windows permits this synthetic rename while an anchored handle
        # remains open, read must still come from the original directory.
        # If the OS refuses to rename (sharing semantics), it fails closed.
        def mutate():
            try:
                self.folder.rename(self.root / "inputs-original")
                self.folder.mkdir()
                (self.folder / "payload.fake").write_bytes(b"ATTACKER_FAKE")
            except PermissionError:
                pass
        try:
            self.assertEqual(nt.anchored_fake_read(self.root, before_leaf=mutate),
                             nt.PAYLOAD)
        finally:
            if (self.root / "inputs-original").is_dir():
                pass

    def test_10_noop_does_not_break_anchored_handle(self):
        self.assertEqual(nt.anchored_fake_read(self.root, before_leaf=lambda: None),
                         nt.PAYLOAD)


if __name__ == "__main__":
    unittest.main(verbosity=2)
