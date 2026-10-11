"""FUE-G04 native Windows PDF contract tests (stdlib; no patient data)."""
import ast
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "backend" / "windows_native_pdf_bundle.py"
SPEC = ROOT / "DigitalCrown.spec"
HOOK = ROOT / "backend" / "scripts" / "pyi_rth_windows_native_pdf.py"

source = importlib.util.spec_from_file_location("fue_g04_native_pdf_contract", MODULE)
contract = importlib.util.module_from_spec(source)
source.loader.exec_module(contract)


class WindowsNativePdfBundleTest(unittest.TestCase):
    def test_real_spec_requires_verified_inputs(self):
        tree = ast.parse(SPEC.read_text(encoding="utf-8"))
        names = {
            n.func.id for n in ast.walk(tree)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
        }
        self.assertIn("verify_installable_release_directory", names)
        self.assertIn("verified_windows_pdf_spec_assets", names)
        self.assertIn("Analysis", names)
        self.assertIn("COLLECT", names)
        spec = SPEC.read_text(encoding="utf-8")
        self.assertIn("binaries=_PDF_NATIVE_BINARIES", spec)
        self.assertIn("runtime_hooks=['backend/scripts/pyi_rth_windows_native_pdf.py']", spec)

    def test_unapproved_source_is_always_rejected(self):
        self.assertIsNone(contract.RELEASE_APPROVED_PROVENANCE_SHA256)
        with mock.patch.dict(os.environ, {
            "DIGITALCROWN_WINDOWS_PDF_MSYS2_ROOT": "C:/untrusted",
            "DIGITALCROWN_WINDOWS_PDF_PROVENANCE": "C:/untrusted/provenance.json",
            "DIGITALCROWN_WINDOWS_NATIVE_APPROVED": "1",
        }):
            with self.assertRaisesRegex(contract.WindowsNativePdfError, "not release-approved"):
                contract.verify_windows_pdf_sources(
                    ROOT, ROOT / "untrusted-provenance.json", lab_only=False
                )

    def test_lab_manifest_must_match_exact_sha_before_parsing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "provenance.json"
            evidence.write_text('{"Status":"EXPERIMENTAL_NOT_RELEASE_APPROVED"}', encoding="utf-8")
            with self.assertRaisesRegex(contract.WindowsNativePdfError, "SHA256 mismatch"):
                contract.verify_windows_pdf_sources(root, evidence, lab_only=True)

    def test_duplicate_and_traversal_rejected(self):
        for rows in (
            [{"Name": "../evil.dll"}],
            [{"Name": "a.dll"}, {"Name": "A.DLL"}],
        ):
            with self.assertRaises(contract.WindowsNativePdfError):
                contract._unique_rows(rows, len(rows), "test")

    def test_native_file_tampering_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            item = Path(tmp) / "native.dll"
            item.write_bytes(b"official")
            import hashlib
            sha = hashlib.sha256(b"official").hexdigest()
            self.assertEqual(contract._verified_file(item, sha), item)
            item.write_bytes(b"malicious")
            with self.assertRaisesRegex(contract.WindowsNativePdfError, "SHA256 mismatch"):
                contract._verified_file(item, sha)

    def test_runtime_hook_is_stdlib_only_and_explicit_no_go(self):
        text = HOOK.read_text(encoding="utf-8")
        ast.parse(text)
        self.assertIn("RELEASE_APPROVED_PROVENANCE_SHA256 = None", text)
        self.assertIn("WEASYPRINT_DLL_DIRECTORIES", text)
        self.assertIn("FONTCONFIG_FILE", text)
        self.assertNotIn("from backend", text)

    @unittest.skipUnless(os.name == "nt" and os.environ.get("FUE_G04_RUN_NATIVE_LAB") == "1",
                         "Windows UCRT64 lab files not supplied")
    def test_official_lab_sources_exact_manifest(self):
        base = os.environ.get("FUE_G04_MSYS2_ROOT")
        evidence = os.environ.get("FUE_G04_PROVENANCE_JSON")
        self.assertTrue(base and evidence)
        binaries, datas = contract.verify_windows_pdf_sources(
            Path(base), Path(evidence), lab_only=True
        )
        self.assertEqual(len(binaries), 64)
        self.assertEqual(len(datas), 5)
        self.assertTrue(any("DejaVuSans.ttf" in source for source, _ in datas))
        self.assertTrue(all(destination == "pdf_native/bin" for _, destination in binaries))


if __name__ == "__main__":
    unittest.main()
