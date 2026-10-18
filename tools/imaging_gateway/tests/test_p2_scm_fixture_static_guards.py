"""LOT06-P/P2-F01: text-only regression tripwires for UNEXECUTED SCM fixtures.

NOT a Windows SCM, token, DACL, security, or product certification.
Uses only repository text; never runs PowerShell, compiles the C# service,
changes Windows accounts, registers services, or touches cabinet data.
"""
from pathlib import Path
import unittest


LAB_DIR = Path(__file__).resolve().parents[1] / "windows"
PS1 = LAB_DIR / "p2_scm_virtual_account_wal_lab.ps1"
CS = LAB_DIR / "p2_scm_synthetic_service.cs"


class P2ScmFixtureStaticGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ps = PS1.read_text(encoding="utf-8")
        cls.cs = CS.read_text(encoding="utf-8")

    def test_both_modes_have_a_single_guard_before_peer_dispatch(self):
        guard = "'DISPOSABLE_RUNNER_AND_OWNER_SCOPE'"
        self.assertEqual(self.ps.count(guard), 1)
        self.assertLess(self.ps.index(guard), self.ps.index("if($Mode -eq 'Peer')"))
        for marker in ("P2_RUNNER_ENVIRONMENT", "GITHUB_REPOSITORY",
                       "P2_SCM_OWNER_GO", "GITHUB_ACTIONS"):
            self.assertIn(marker, self.ps)

    def test_peer_path_guard_precedes_any_peer_file_probe(self):
        mode = self.ps.split("if($Mode -eq 'Peer'){", 1)[1].split(
            "\n$runner=", 1
        )[0]
        self.assertIn("PEER_ROOT_NOT_DISPOSABLE_FIXTURE", mode)
        self.assertIn("PEER_ROOT_REQUIRED", mode)
        self.assertIn("^dc-p2-scm-ci-[0-9a-f]{8}$", mode)
        self.assertLess(mode.index("PEER_ROOT_NOT_DISPOSABLE_FIXTURE"),
                        mode.index("$private=Join-Path $WorkRoot 'private'"))
        self.assertLess(mode.index("PEER_ROOT_NOT_DISPOSABLE_FIXTURE"),
                        mode.index("Deny {"))

    def test_harness_uses_fresh_lab_root_and_explicit_cleanup_oracles(self):
        for marker in (
            "NONFRESH_ROOT", "NTFS_REQUIRED", "RUNNER_ADMIN_REQUIRED",
            "SERVICE_LEFTOVER", "WORKSPACE_LEFTOVER", "PEER_LEFTOVER",
            "P2_SCM_DISPOSABLE_SERVICE_ACCOUNT_WORKSPACE_CLEANUP=PASS",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.ps)
        self.assertIn("}catch{$mainError=$_}finally{", self.ps)

    def test_csharp_rejects_non_synthetic_executable_paths(self):
        for marker in (
            "LAB_FIXTURE_LAYOUT_REQUIRED",
            "CommonApplicationData",
            "^dc-p2-scm-ci-[0-9a-f]{8}$",
            "^DCP2S[0-9a-f]{8}$",
            "rootName.Substring",
            "serviceName.Substring",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.cs)
        # Fixture layout is evaluated in Work before constructing the DB path.
        self.assertIn("string dir = PrivateDir, dbpath =", self.cs)

    def test_positive_and_negative_markers_remain_separate(self):
        for marker in (
            "SERVICE_NOT_SESSION0", "SERVICE_RUNTIME_SID_MISMATCH",
            "SQLITE_SIDECAR_MISSING", "SERVICE_AFTER_DENIAL_FAILED",
            "PEER_DENIAL_COUNT",
        ):
            # Peer denial counter is currently named DENIAL_COUNT_WRONG.
            if marker == "PEER_DENIAL_COUNT":
                marker = "DENIAL_COUNT_WRONG"
            with self.subTest(marker=marker):
                self.assertIn(marker, self.ps)
        self.assertIn("SCM_COMMITTED", self.cs)
        self.assertIn("SCM_ROLLED_BACK", self.cs)
        self.assertIn("SCM_AFTER_DENIAL", self.cs)

    def test_peer_requests_dac_and_owner_rights_without_mutation(self):
        peer = self.ps.split("if($Mode -eq 'Peer'){", 1)[1].split(
            "\n$runner=", 1
        )[0]
        for marker in (
            "FileSystemRights]::ChangePermissions",
            "FileSystemRights]::TakeOwnership",
            "'WRITE_DAC';$n++;$dac++",
            "'WRITE_OWNER';$n++;$owner++",
            "$n -eq 17", "$dac -eq 3", "$owner -eq 3",
            "WRITE_DAC_DENIED=", "WRITE_OWNER_DENIED=",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, peer)
        for mutator in ("Set-Acl", "SetAccessControl(", "SetOwner("):
            self.assertNotIn(mutator, peer)
        for marker in (
            "DENIALS=17", "WRITE_DAC_DENIED=3",
            "WRITE_OWNER_DENIED=3", "P2_SCM_PEER_WRITE_DAC_DENIED=3/3",
            "P2_SCM_PEER_WRITE_OWNER_DENIED=3/3",
        ):
            self.assertIn(marker, self.ps)
        self.assertNotIn("P2_SCM_INTERACTIVE_PEER_DENIED=11/11", self.ps)

    def test_native_sqlite_wal_full_fail_closed_readback(self):
        # Source-only oracle: compiled by the separate experimental Windows gate,
        # never a claim of a real SCM token, backup or crash recovery.
        for marker in (
            'EntryPoint="sqlite3_prepare_v2"',
            'EntryPoint="sqlite3_step"',
            'EntryPoint="sqlite3_column_text"',
            'EntryPoint="sqlite3_finalize"',
            "SQLITE_PRAGMA_PREPARE_FAILED",
            "SQLITE_PRAGMA_ROW_MISSING",
            "SQLITE_PRAGMA_VALUE_MISMATCH",
            "SQLITE_PRAGMA_EXTRA_ROW",
            "SQLITE_PRAGMA_FINALIZE_FAILED",
            'ExpectScalar(db, "PRAGMA journal_mode=WAL;", "wal")',
            'Sql(db, "PRAGMA synchronous=FULL;")',
            'ExpectScalar(db, "PRAGMA synchronous;", "2")',
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.cs)
        wal = self.cs.index('ExpectScalar(db, "PRAGMA journal_mode=WAL;", "wal")')
        full = self.cs.index('ExpectScalar(db, "PRAGMA synchronous;", "2")')
        commit = self.cs.index("SCM_COMMITTED")
        proof = self.cs.index("SQLITE_COMMIT=PASS")
        self.assertLess(wal, full)
        self.assertLess(full, commit)
        self.assertLess(commit, proof)
        self.assertNotIn('PRAGMA journal_mode=WAL; PRAGMA synchronous=FULL;', self.cs)

    def test_native_wal_checkpoint_fails_closed_on_partial_result(self):
        # Source only; behavioral partial-checkpoint test is separate in
        # test_p2_sqlite_recovery_semantics.py; neither executes native SCM.
        for marker in (
            'EntryPoint="sqlite3_column_int"',
            'Prepare(db, "PRAGMA wal_checkpoint(PASSIVE);"',
            "int busy = ColumnInt(statement, 0);",
            "int logFrames = ColumnInt(statement, 1);",
            "int checkpointedFrames = ColumnInt(statement, 2);",
            "busy != 0", "logFrames < 0", "checkpointedFrames < 0",
            "checkpointedFrames != logFrames",
            "SQLITE_CHECKPOINT_INCOMPLETE", "SQLITE_CHECKPOINT_PREPARE_FAILED",
            "SQLITE_CHECKPOINT_ROW_MISSING", "SQLITE_CHECKPOINT_EXTRA_ROW",
            "SQLITE_CHECKPOINT_FINALIZE_FAILED",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.cs)
        self.assertEqual(self.cs.count("RequireCompleteCheckpoint(db);"), 2)
        self.assertNotIn('Sql(db, "PRAGMA wal_checkpoint(PASSIVE);")', self.cs)
        self.assertLess(
            self.cs.index("RequireCompleteCheckpoint(db);"),
            self.cs.index('"TOKEN_USER_SID="'),
        )
        self.assertLess(
            self.cs.rindex("RequireCompleteCheckpoint(db);"),
            self.cs.index('"AFTER_DENIAL_COMMIT=PASS'),
        )

    def test_native_worker_shutdown_and_close_fail_closed(self):
        # Source assertion only; no SCM stop/kill/restart has executed.
        for marker in (
            "if (db != IntPtr.Zero && Close(db) != 0)",
            '"SQLITE_CLOSE_FAILED"',
            "if (worker != null && !worker.Join(7000))",
            '"SERVICE_WORKER_STOP_TIMEOUT"',
            'workerFailed = true;',
            'workerFailed = false;',
            'workerFailed || File.Exists(Path.Combine(PrivateDir, "service.error"))',
            '"SERVICE_WORKER_OR_CLOSE_FAILED"',
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.cs)
        self.assertEqual(self.cs.count('workerFailed = true;'), 2)
        self.assertLess(self.cs.index('workerFailed = true;'),
                        self.cs.index('workerFailed = false;'))
        self.assertLess(self.cs.index('Close(db) != 0'),
                        self.cs.index('protected override void OnStop()'))
        self.assertLess(self.cs.index('worker.Join(7000)'),
                        self.cs.rindex('File.Exists(Path.Combine(PrivateDir, "service.error"))'))
        self.assertNotIn('finally { if (db != IntPtr.Zero) Close(db); }', self.cs)

    def test_no_production_storage_paths_or_device_calls(self):
        together = self.ps + "\n" + self.cs
        for forbidden in (
            "clinical_vault.db", "SQLCIPHER_KEY_HEX", "CABINET_MASTER_KEY_HEX",
            "C:\\Program Files\\Digital Crown", "patient_id", "pacs_client",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, together)


if __name__ == "__main__":
    unittest.main()
