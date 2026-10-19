"""LOT05 J5 — verify native Windows handles on disposable fixtures only."""
from __future__ import annotations
import os
from pathlib import Path
import tempfile
import unittest

from backend.tests.fixtures import lot05j5_native_handles_lab as lab


class NativeHandleTests(unittest.TestCase):
    def setUp(self):
        self.assertEqual(os.name, "nt", "Windows-native test required")
        self.previous = os.environ.get(lab.FLAG)
        os.environ[lab.FLAG] = "1"
        self.addCleanup(self.restore)
        self.temp = tempfile.TemporaryDirectory(prefix="lot05j5_fake_")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.folder = self.root / "inputs"
        self.folder.mkdir()
        self.file = self.folder / "payload.fake"
        self.file.write_bytes(lab.CONTENTS)

    def restore(self):
        if self.previous is None:
            os.environ.pop(lab.FLAG, None)
        else:
            os.environ[lab.FLAG] = self.previous

    def test_01_real_win32_handle_read(self):
        self.assertEqual(lab.inspect_win32_handles(self.root), lab.CONTENTS)

    def test_02_no_flag_denied(self):
        os.environ[lab.FLAG] = "0"
        with self.assertRaises(lab.J5Denied):
            lab.inspect_win32_handles(self.root)

    def test_03_nonmatching_directory_denied(self):
        with self.assertRaises(lab.J5Denied):
            lab.inspect_win32_handles(self.folder)

    def test_04_missing_file_denied(self):
        self.file.unlink()
        with self.assertRaises(lab.J5Denied):
            lab.inspect_win32_handles(self.root)

    def test_05_changed_contents_denied(self):
        self.file.write_bytes(b"NOT_J5_PAYLOAD")
        with self.assertRaises(lab.J5Denied):
            lab.inspect_win32_handles(self.root)

    def test_06_hardlink_identity_denied(self):
        os.link(self.file, self.root / "alternate.fake")
        with self.assertRaises(lab.J5Denied):
            lab.inspect_win32_handles(self.root)

    def test_07_injected_new_file_identity_denied(self):
        def update():
            self.file.rename(self.folder / "original.fake")
            self.file.write_bytes(lab.CONTENTS)
        with self.assertRaises(lab.J5Denied):
            lab.inspect_win32_handles(self.root, attack_hook=update)

    def test_08_unchanged_identity_ok(self):
        self.assertEqual(lab.inspect_win32_handles(self.root, attack_hook=lambda: None),
                         lab.CONTENTS)


if __name__ == "__main__":
    unittest.main(verbosity=2)
