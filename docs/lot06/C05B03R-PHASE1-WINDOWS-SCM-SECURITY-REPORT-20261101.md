# LOT06 — PHASE 1 one-shot — C05B-03R Windows local acquisition security

**Date:** 2026-11-01. **Parent:** [DRAFT PR #1187](https://github.com/hraaaaf/Digital_crown/pull/1187) at `85f3e7531d36d58d76cc5b16349568b5ae493083`. **Canonical:** https://app.notion.com/p/3e677c66336281639beae2a946df1483.

## Scope: complete every feasible hosted-Windows security proof in one PR

This PR extends prior N/O/P/Q test-only security artifacts, without importing test code into the production backend. A new disposable .NET 8 Windows executable is compiled **at CI runtime**, is invoked only by the real Windows Service Control Manager under **NT AUTHORITY/LocalService**, is granted `SERVICE_SID_TYPE_RESTRICTED` and explicitly checks its own live Windows process-token **S-1-5-19** identity and presence of its *service-specific SID* before setting `SERVICE_RUNNING`. It opens one Win32 named pipe with versioned random name, protected SDDL and native `PIPE_REJECT_REMOTE_CLIENTS` and `FILE_FLAG_FIRST_PIPE_INSTANCE` flags. The service runs with a hard lab deadline and receives STOP via SCM.

**Explicit access policy (test fixture, not product installer)**:
- Service SID: `GA` on pipe — sole own-service permission to create server instances and read/write.
- A specific separate ordinary Windows client SID: **only `0x00100003`** (`SYNCHRONIZE | FILE_READ_DATA | FILE_WRITE_DATA`), **no `FILE_CREATE_PIPE_INSTANCE` (0x4)**.
- SYSTEM: `GA`; all other accounts, Everyone and Anonymous excluded from explicit DACL.
- Two disposable local user accounts, authorized and unauthorized, each starts an independent real child PowerShell process under its respective real OS Windows user. Each child validates its own SID, independently calls Win32 `CreateFileW` and `CreateNamedPipeW` and confirms the expected real kernel outcomes. **Allowed:** read/write possible but server-instance creation gets `ACCESS_DENIED=5`; **unauthorized:** both connection and instance creation get 5. Parent demands child exit code 0 and bounded completion; all artifacts removed in finally.
- Installed test service is demand-start, **never** auto-start, runs only inside disposable hosted Windows CI machine with `GITHUB_ACTIONS`, `RUNNER_OS=Windows`, `ENVIRONMENT=test`, `DIGITALCROWN_ISOLATED_RUNTIME=true`, `DC06C05B03R_TEST_ONLY=1`. **No service installed on a clinic or ordinary workstation.**

## Test and verdict checklist

- [ ] C05B-03R Windows true SCM LocalService + restricted SID recognized from live service token
- [ ] C05B-03R client allowed to read/write but denied server instance creation (avoid GENERIC_WRITE, since that includes FILE_CREATE_PIPE_INSTANCE)
- [ ] C05B-03R different ordinary account denied both data connection and server instance creation
- [ ] C05B-03R full cleanup: stop/delete service, delete two users and generated code/binaries
- [ ] Prior C05B-03Q actual separate-user process rejection, C05B-03P custom DACL and C05B-03O IPC + CNG software LAB probe
- [ ] 58 Windows negative contracts and 80 Linux N/M/L/K/G/J SQLCipher tests on EXACT final SHA
- [ ] GitHub CI Scope Gate SUCCESS on EXACT final SHA
- [ ] Distinguish hardware TPM availability from software provider laboratory only

## Inescapable limits and stop

**Remote denial:** passing `PIPE_REJECT_REMOTE_CLIENTS` to actual Win32 native CreateNamedPipe is code-path verified, but a GitHub-hosted isolated Windows runner **does not supply a controlled second host/SMB peer**. An actual remote rejection requires an explicitly provisioned isolated second-host test, then FUE; this is OPEN and must NOT be marked GREEN by a loopback workaround.

**Physical TPM:** hosted Windows runner had no working Microsoft Platform Crypto Provider TPM in 03O–03Q; physical cabinet CNG TPM enrollment/rotation/revocation and nonexportable key attestation remain OPEN. The software-CNG test never authorizes automatic product fallback.

**Product hardening still OPEN:** service fixture is *not* the Windows installer; production SDDL also needs client logon-session SID and impersonation/revert per request, stronger service hardening including dedicated SID only minimal rights, fixed audit and request framing; genuine UI human choice with dual patient identifiers and staff authenticated confirmation, lost ACK recovery/crash/power cut, real scanner hardware, independent security audit. The clinical integration phase has not started. Running Windows SCM in CI does **not** certify actual cabinet service installation.

The next action after Windows-phase laboratory gate is a separate **Phase 2: product gateway integration**, with a physical hardware validation prerequisite for eventual production deployment; this avoids an endless chain of security-model PRs.

`READY_TO_MERGE=false`
`PRODUCT_READY=false`
`CLINICAL_GO=false`
