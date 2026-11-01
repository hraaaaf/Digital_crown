# Digital Crown LOT06 — Phase2 B04 · SCM restart and key continuity (LAB only)

**Status: Candidate, pending exact SHA GitHub FUE.** Parent: [B03 PR #1195](https://github.com/hraaaaf/Digital_crown/pull/1195) at `6d06348520b16686de23f8ef0d22e7f74b052fe0`, verified GREEN LAB. One [Notion LOT06 canonical](https://app.notion.com/p/3e677c66336281639beae2a946df1483); this is a technical runbook, not an alternate roadmap.

## Goal and FUE oracle
A real disposable SCM service runs as **LocalService** with restricted service SID, reading **real encrypted AES-GCM/SQLite** HotFolder spool created from a **2×2 synthetic PNG**. A separate approved Windows account queries native OS Named Pipe; another real Windows account is refused.

1. Initial encrypted synthetic queue must return **S1**.
2. `sc stop` → SCM STOPPED, then `sc start` → SCM RUNNING, with **no reseed, no new key or database and unchanged ciphertext SHA-256**. Native S query must still return **S1**.
3. Replace fixture's 32-byte key with a **distinct 32-byte synthetic key**: next read must return exactly **E2 (authenticated-read rejection)**, never `S0`, `S1`, a transport error or an arbitrary failure.
4. Restore the original synthetic key. Without reseed, native S query must return **S1** again.
5. Flip a ciphertext byte: the authenticated read must return exactly **E2**, not `S0` or another unexplained error.
6. Actual unauthorized OS account must remain unable to open the pipe; service/users/test key/media must be removed at teardown. Existing B03 security regressions still required at candidate SHA.

## Execution constraints
Use disposable GitHub-hosted Windows runners only; env `ENVIRONMENT=test`, `DIGITALCROWN_ISOLATED_RUNTIME=true`, `DC06C05B03R_TEST_ONLY=1`, `DC06B03_SERVICE_SPOOL=1`, `DC06B04_RESTART_KEY_TEST=1`; no code paths in backend product or patient UI. Encryption uses an ephemeral file ACL key **only for the fixture**, not a production key vault. No filenames, media, keys, patient IDs or exception text through IPC. No `Users`/`Everyone` ACL grants.

**Important limitations**: controlled SCM restart is **not** abrupt process kill, real power cut or durable clinical crash certification. No true cabinet Windows installation, real TPM, physical scanner, second host, human double-ID review, production key enrollment/rotation or clinical signed ACK. Product currently remains `NATIVE_IPC_NOT_CONNECTED` and cannot infer patient identity from the synthetic queue.

`READY_TO_MERGE=false`
`PRODUCT_READY=false`
`CLINICAL_GO=false`

No merge, no Vercel deploy, no clinic installation, no real patient information.
