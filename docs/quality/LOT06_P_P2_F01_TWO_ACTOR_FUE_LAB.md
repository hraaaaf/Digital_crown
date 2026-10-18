# LOT06-P / P2-F01 — Two-actor FUE technical Windows LAB (EXPERIMENTAL)

**Scope**: This is a pair of **first-use technical actor exercises** targeting the P2-F01 storage trust boundary. It is **not** a user-facing/browser FUE, not two independent AI reviewers, and not an SCM service identity test. The current P2-F01 service mode has no legitimate UI to test. Existing FUE-G00 browser scenarios belong to a different work package and are deliberately not imported.

**Run target**: PR #909, exact head read from GitHub, synthetic data on independent GitHub-hosted `windows-latest` runner jobs. Workflow `.github/workflows/v15-06p-p2-f01-two-actor-fue-experimental.yml`. Only workflow/manual PR path scope. No customer PC, no production install, no release or Vercel deployment, no SCM service registration/start.

## FUE-A — first standard Windows user (actual different user SIDs)

**BEFORE**: disposable Windows runner, exact HEAD, no clinical paths; fixture creates genuine different local standard user SIDs and protected NTFS files.

**ACTION**: reexecute existing `f01_cross_sid_acl_lab.ps1`, which proves owner positive I/O and a different standard peer's DB/WAL/SHM read/write/delete/create/ACL requests denied. Require the actual output marker set `F01_OWNER_POSITIVE_FILE_IO=6/6`, `F01_PEER_NEGATIVE_FILE_IO=33/33`, `F01_PEER_WRITE_DAC_REQUEST_DENIED=6/6`, `F01_PEER_WRITE_OWNER_REQUEST_DENIED=6/6`; no marker means FAIL.

**AFTER**: require unmodified six file hashes/NTFS SDDL plus disposable account and fixture cleanup, else FAIL. The harness emits `F01_SCM_SERVICE_SID=NOT_TESTED`.

## FUE-B — first restore operator (separate Windows runner)

**BEFORE**: another fresh disposable Windows runner, exact HEAD, temporary synthetic SQLite acquisition/spool/key fixtures.

**ACTION**: execute the existing `test_p2_backup_lab.py` and `test_p2_sqlite_recovery_semantics.py` against fresh fixtures. Cover quiescent SQLite backup, complete DB+spool+key restore, wrong key refusal, DB-only restore refusal, snapshot interruption, source mutation, ledger mutation, WAL checkpoint/contention and subprocess crash recovery. The runtime result (success/failure) is the oracle, not the wrapper's static labels.

**AFTER**: new fixtures validate restored data and negative fail-closed cases; temporary fixtures self-clean. No Windows service or actual user-facing UI is started. FUE-B does not test packaged installation, SQLCipher or true SCM crash/restart.

## Evidence and acceptance

Each job must be **COMPLETED/SUCCESS on the same exact head**, with distinct runner/job IDs and matching BEFORE/ACTION/AFTER logs and short evidence artifacts. Any ERROR/FAIL/skip of an entire job => OPEN; negative tests must reject unsafe operations, not silently skip. CI source tests on the new head are independently required. Read actual logs; do not infer PASS from YAML.

**Strict scope boundaries:** A/B are two executions in separate OS jobs, **not** two agents performing BLIND first-time source reviews. Neither fulfills mandatory native SCM W01–W12. Gate P2 stays OPEN/NOT CONVERGED even if both FUE technical jobs succeed. Windows F01 uses standard users but its existing hosted runner setup is privileged; no prohibited SCM service operation is performed.

**Adversarial risk:** A verifies a tested set of 33 denials and unchanged SDDL, not arbitrary attacks; B runs the existing recovery test cases under the runner identity, not an operator product UI. Run statuses on a previous HEAD are invalid after a code change. Never label these as clinical certification.
