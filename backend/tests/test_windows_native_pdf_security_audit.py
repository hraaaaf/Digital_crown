"""Negative safety tests for the FUE-G04 native security audit (no MSYS2 needed)."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

AUDIT = Path(__file__).resolve().parents[1] / "scripts" / "audit_windows_native_pdf_security.py"
spec = importlib.util.spec_from_file_location("fue_g04_pe_security_audit", AUDIT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class NativeSecurityAuditTest(unittest.TestCase):
    def test_import_name_hardening(self):
        for name in ("", "../evil.dll", "C:\\Windows\\evil.dll", "evil.so", "..\\pango.dll"):
            with self.subTest(name=name), self.assertRaises(RuntimeError):
                mod._basename(name)
        self.assertEqual(mod._basename("KERNEL32.DLL"), "kernel32.dll")

    def test_non_system_fallback_is_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            system32 = Path(root)
            for name in ("libexternal.dll", "libpango-1.0-0.dll"):
                with self.assertRaisesRegex(RuntimeError, "Unresolved"):
                    mod.classify_import(name, set(), system32)

    def test_bundled_binary_precedes_system_resolution(self):
        with tempfile.TemporaryDirectory() as root:
            system32 = Path(root)
            (system32 / "libpango-1.0-0.dll").write_bytes(b"malicious host copy")
            self.assertEqual(mod.classify_import("libpango-1.0-0.dll",
                             {"libpango-1.0-0.dll"}, system32), "pinned_bundle")
            self.assertEqual(mod.classify_import("api-ms-win-core-foo.dll",
                             set(), system32), "windows_api_set")

    def test_system_import_requires_real_system32_file(self):
        with tempfile.TemporaryDirectory() as root:
            system32 = Path(root)
            (system32 / "kernel32.dll").write_bytes(b"fixture")
            self.assertEqual(mod.classify_import("kernel32.dll", set(), system32),
                             "windows_system32")

    def test_missing_pacman_metadata_fails_closed(self):
        with self.assertRaises(RuntimeError):
            mod._field("Name : sample\nVersion : 1-1", "Licenses")
        self.assertEqual(mod._field("Licenses : LGPL-2.1\n", "Licenses"),
                         "LGPL-2.1")


if __name__ == "__main__":
    unittest.main()
