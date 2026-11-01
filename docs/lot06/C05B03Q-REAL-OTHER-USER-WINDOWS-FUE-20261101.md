# Digital Crown — LOT06 C05B-03Q: real other-account, other-process Win32 denial

**Date:** 2026-11-01. **Parent:** [DRAFT #1186](https://github.com/hraaaaf/Digital_crown/pull/1186) exact HEAD `6105b4d584a7d2a32ccaac221eacc56e6dc67182`. Canonical Notion: https://app.notion.com/p/3e677c66336281639beae2a946df1483.

## Proof sought — stronger than P

03P demonstrably received native `ERROR_ACCESS_DENIED=5` for a real alternate Windows user token, but this token was impersonated **in the server test process**. 03Q closes that *specific* evidentiary gap by requiring a separate Windows child process actually started under the alternate user.

- Native `CreateNamedPipeW` protected SDDL from 03P (only original local user and SYSTEM full access), `PIPE_REJECT_REMOTE_CLIENTS` flag and `FILE_FLAG_FIRST_PIPE_INSTANCE` plus two instance slots. Keep 03P negative test and permitted-user positive control unchanged.
- Create a disposable local unprivileged Windows account with a random password; call `Start-Process -Credential` to create a *distinct* PowerShell host under that account. The password remains in a PowerShell SecureString credential object and is **never** passed to the child command line, logged, committed or saved in a file.
- Child script `windows_other_process_child_c05b03q.ps1`: compare its own actual Windows access token SID with exact newly created user SID; verify child PID differs from parent; independently use Win32 `CreateFileW(GENERIC_READ|GENERIC_WRITE)` on exact protected pipe; require OS `ERROR_ACCESS_DENIED=5`. Return nonzero if identity or denial differs, with a deterministic non-PHI failure marker. Parent requires completed real child + exit code 0; applies a 12-second bound/forced kill and finally disposes process handle and temporary user/pipe.
- 58 Windows synthetic N policy tests, 03O same-user **separate-process positive** connection/SID impersonation, 03P same-process alternate-token negative, native CNG P-256 software-KSP control with hosted TPM status, plus 80 Linux N/M/L/K/G/J actual SQLCipher/JWT LAB regression on same SHA and Scope Gate.
- Runner is a disposable Windows test VM. NO install of Windows service, changes to product routes, actual scanner, persistent keys, clinic users or real patient records.

## What successful CI would and would not prove

**Proves only on this runner:** an actual separate child process running as an actual different local unprivileged Windows user could **not** open the exact SDDL-protected pipe while original account could, independent of synthetic model checks. The service impersonation test from 03O remains a different same-account fixture.

**Does not prove:** a running SCM Windows service SID, correct `SERVICE_SID_TYPE_RESTRICTED`, production least-privilege DACL with distinct server `FILE_CREATE_PIPE_INSTANCE` and client read/write rights, real remote host denial despite flag `PIPE_REJECT_REMOTE_CLIENTS` being set, Windows restart/installer ACL persistence, physically backed TPM/CNG key provisioning or rotation, staff explicit UI confirmation and patient assignment, power-cut recovery and orphan ciphertext repair, actual imaging devices, or external security sign-off.

A service SID string or `sc showsid` alone **is not proof of a live SCM service**; none is installed in this lot. If hosted runner refuses alternate-user process creation for lack of Windows secondary logon rights, mark FUE **BLOCKED / RED**; do not count the older impersonated-token result as proof of separate-process denial.

## Later gates (03R, pending owner decision)

Actual test-only service SID in a separately approved disposable VM with installer DACL, restricted service access and negative unauthorized process; isolated, authenticated remote-host negative for `PIPE_REJECT_REMOTE_CLIENTS`; TPM/CNG tested on target physical workstation, human review UI FUE (including 200% scaling and patient mismatch), powercut/SQLCipher + filesystem reconciliation, independent security audit, explicit owner GO. No clinical activation by inference.

`READY_TO_MERGE=false`
`PRODUCT_READY=false`
`CLINICAL_GO=false`
