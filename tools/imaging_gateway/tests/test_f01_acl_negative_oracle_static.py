"""F01 static evidence contract; NEVER executes Windows accounts, ACLs or SCM.

A passing static test is not an effective-token or Windows security proof.
The hosted experimental cross-SID workflow is the actual runtime oracle.
"""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "tools/imaging_gateway/windows/f01_cross_sid_acl_lab.ps1"
WORKFLOW = ROOT / ".github/workflows/v15-06p-f01-cross-sid.yml"


class F01AclNegativeOracleStaticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.script = SCRIPT.read_text(encoding="utf-8")
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")

    def test_distinct_non_admin_tokens_and_no_scm_claim(self):
        for marker in (
            "'OWNER_NOT_STANDARD'", "'PEER_NOT_STANDARD'",
            "'PEER_TOKEN_MISMATCH'", "'F01_SCM_SERVICE_SID=NOT_TESTED'",
            "'F01_COMMERCIAL_CERTIFICATION=NOT_AUTHORIZED'",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.script)

    def test_explicit_direct_rights_requests_are_counted_as_refusals(self):
        peer = self.script.split("if ($Mode -eq 'Peer') {", 1)[1].split(
            "\nAssert-F01 ($env:CI", 1
        )[0]
        for enum, denial in (
            ("[Security.AccessControl.FileSystemRights]::Delete", "'DELETE_RIGHT'"),
            ("[Security.AccessControl.FileSystemRights]::ChangePermissions", "'WRITE_DAC'"),
            ("[Security.AccessControl.FileSystemRights]::TakeOwnership", "'WRITE_OWNER'"),
        ):
            with self.subTest(right=enum):
                self.assertIn(enum, peer)
                self.assertIn(denial, peer)
        self.assertIn("assertions -eq 33", self.script)
        self.assertIn("F01_PEER_NEGATIVE_FILE_IO=33/33", self.script)

    def test_denial_cannot_be_a_missing_file_and_proof_requires_nonmutation(self):
        self.assertIn("UnauthorizedAccessException", self.script)
        self.assertIn("FileNotFoundException is NOT an access-denial proof", self.script)
        self.assertIn("SECURITY_DESCRIPTOR_CHANGED", self.script)
        self.assertIn("HASH_CHANGED", self.script)
        self.assertIn("F01_DISPOSABLE_USER_AND_ROOT_CLEANUP=PASS", self.script)

    def test_ci_requires_actual_windows_oracle_markers_not_syntax_only(self):
        markers = (
            "F01_PEER_NEGATIVE_FILE_IO=33/33",
            "F01_PEER_WRITE_DAC_REQUEST_DENIED=6/6",
            "F01_PEER_WRITE_OWNER_REQUEST_DENIED=6/6",
            "F01_SECURITY_DESCRIPTOR_UNCHANGED=6/6",
            "F01_SCM_SERVICE_SID=NOT_TESTED",
            "F01_EXPERIMENTAL_EVIDENCE_VALIDATED=PASS",
        )
        for marker in markers:
            with self.subTest(marker=marker):
                self.assertIn(marker, self.workflow)
        self.assertIn("F01_EXACT_HEAD_MISMATCH", self.workflow)


if __name__ == "__main__":
    unittest.main()
