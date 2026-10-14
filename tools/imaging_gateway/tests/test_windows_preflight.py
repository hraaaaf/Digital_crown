"""LOT06-G: read-only NTFS/ACL Windows gate; no installation or key access."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "windows" / "preflight.ps1"
POWERSHELL = shutil.which("powershell.exe") or shutil.which("pwsh")


def run_gate(*args):
    cmd = [POWERSHELL, "-NoProfile", "-NonInteractive", "-File", str(SCRIPT), *map(str, args)]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False,
                            timeout=45)
    return result, json.loads(result.stdout)


class WindowsPreflightPortableContract(unittest.TestCase):
    def test_gate_script_is_read_only_and_no_key_export(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("Get-Acl", source)
        self.assertIn("Get-Volume", source)
        self.assertIn("Test-AncestorReparse", source)
        self.assertIn("DPAPI_DEVICE_KEY_AND_RECOVERY_VERIFIED", source)
        self.assertIn("clinical_activation_permitted=$false", source)
        self.assertNotIn("Set-Acl ", source)
        self.assertNotIn("ConvertFrom-SecureString", source)
        self.assertNotIn("CryptUnprotectData", source)
        self.assertNotIn("Start-Service ", source)
        self.assertNotIn("Set-ItemProperty ", source)
        self.assertNotIn("New-Item ", source)
        self.assertNotIn("Remove-Item ", source)


@unittest.skipUnless(os.name == "nt" and POWERSHELL, "Windows PowerShell required")
class WindowsPreflightNativeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="dc06g-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.watch = self.root / "watch with spaces"
        self.state = self.root / "private"
        self.watch.mkdir()
        self.state.mkdir()
        (self.state / "spool").mkdir()

    def test_powershell_acl_fixtures_cover_broad_write_and_deny(self):
        result, report = run_gate("-SelfTest")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(report["contract"], "DC06G-WINDOWS-PREFLIGHT-SELFTEST-V1")
        self.assertEqual(report["passed"], 6, report)
        self.assertEqual(report["count"], 6)
        self.assertTrue(report["ok"])

    def test_real_windows_paths_never_pass_installation_or_clinical_gate(self):
        files_before = set(str(p.relative_to(self.root)) for p in self.root.rglob("*"))
        result, report = run_gate("-WatchDir", self.watch, "-StateDir", self.state)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(report["contract"], "DC06G-WINDOWS-PREFLIGHT-V1")
        self.assertEqual(report["status"], "BLOCKED")
        self.assertFalse(report["ready_for_install"])
        self.assertFalse(report["clinical_activation_permitted"])
        self.assertEqual(report["key_strategy"], "ENV_ONLY_UNCERTIFIED")
        codes = [item["code"] for item in report["checks"]]
        self.assertIn("WATCH_STATE_DISJOINT", codes)
        self.assertIn("STATE_VOLUME_NTFS", codes)
        self.assertIn("STATE_ACL_BROAD_WRITE_DENIED", codes)
        self.assertIn("DATABASE_NOT_INITIALIZED", codes)
        self.assertNotIn("INSPECTION_FAILED", codes,
                         "Native ACL/volume preflight must really inspect files")
        self.assertIn("DPAPI_DEVICE_KEY_AND_RECOVERY_VERIFIED", codes)
        self.assertIn("PHYSICAL_NTFS_ACL_FIELD_CERTIFIED", codes)
        self.assertFalse(next(item["ok"] for item in report["checks"]
                              if item["code"] == "DPAPI_DEVICE_KEY_AND_RECOVERY_VERIFIED"))
        self.assertNotIn(str(self.watch), result.stdout)
        self.assertNotIn(str(self.state), result.stdout)
        self.assertNotIn("61626364", result.stdout)  # never echo example hex key
        self.assertEqual(files_before, set(str(p.relative_to(self.root))
                                           for p in self.root.rglob("*")))

    def test_missing_paths_fail_closed_and_do_not_echo_paths(self):
        result, report = run_gate("-WatchDir", self.watch,
                                  "-StateDir", self.root / "missing-private")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("INSPECTION_FAILED",
                      [item["code"] for item in report["checks"]])
        self.assertNotIn("missing-private", result.stdout)

    def test_nested_state_cannot_pass_separation_gate(self):
        nested = self.watch / "private"
        nested.mkdir()
        (nested / "spool").mkdir()
        result, report = run_gate("-WatchDir", self.watch, "-StateDir", nested)
        self.assertEqual(result.returncode, 0, result.stderr)
        statuses = [x["ok"] for x in report["checks"]
                    if x["code"] == "WATCH_STATE_DISJOINT"]
        self.assertEqual(statuses, [False], report)
        self.assertFalse(report["ready_for_install"])

    def test_omitted_paths_fail_closed(self):
        result, report = run_gate()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("REQUIRED_PATHS_MISSING",
                      [x["code"] for x in report["checks"]])

    def test_state_missing_spool_cannot_be_declared_ready(self):
        (self.state / "spool").rmdir()
        result, report = run_gate("-WatchDir", self.watch, "-StateDir", self.state)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("INSPECTION_FAILED",
                      [x["code"] for x in report["checks"]])

    def test_preflight_does_not_need_spool_key(self):
        old = os.environ.pop("DC_IMAGING_SPOOL_KEY_HEX", None)
        try:
            result, report = run_gate("-WatchDir", self.watch, "-StateDir", self.state)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(report["clinical_activation_permitted"])
            self.assertEqual(report["key_strategy"], "ENV_ONLY_UNCERTIFIED")
        finally:
            if old is not None:
                os.environ["DC_IMAGING_SPOOL_KEY_HEX"] = old


if __name__ == "__main__":
    unittest.main()
