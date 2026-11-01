# Digital Crown LOT06 C05B-03P — Win32 named-pipe SDDL and real other-account denial (LAB)

**Date:** 2026-11-01. **Parent:** [DRAFT #1185](https://github.com/hraaaaf/Digital_crown/pull/1185), exact SHA `951729b931ee443031101ab789d615802c85d2ce`. **Canonique:** https://app.notion.com/p/3e677c66336281639beae2a946df1483

## Evidence sought

The 03O lab established that **two distinct processes under the same Windows account** can exchange bytes via `CurrentUserOnly`, and the server can impersonate that client to inspect its Windows SID. This did **not** test a user from another account or a caller-restricted native SDDL. The 03P test seeks the next tighter proof.

**Disposable Windows runner fixture** `isolated_fue_lot06c/windows_sddl_crossaccount_c05b03p.ps1`:
1. Assert `ENVIRONMENT=test` and `DIGITALCROWN_ISOLATED_RUNTIME=true`; generate a random unique pipe name and a **temporary unprivileged local Windows user** using non-logged secret material. In all control-flow exits, dispose native handles/tokens and delete the Windows test user. No installer, Windows service or standing account remains.
2. Real `ConvertStringSecurityDescriptorToSecurityDescriptorW` on protected SDDL `D:P(A;;GA;;;<server current-user SID>)(A;;GA;;;SY)`. Unlike `NamedPipeServerStreamAcl.Create(...CurrentUserOnly...)`, this native DACL is actually supplied as `SECURITY_ATTRIBUTES` to `CreateNamedPipeW`.
3. Explicit flags: `PIPE_ACCESS_DUPLEX | FILE_FLAG_FIRST_PIPE_INSTANCE | FILE_FLAG_OVERLAPPED`; pipe mode `PIPE_REJECT_REMOTE_CLIENTS`, max instances=1, bounded buffers. Reopening with FIRST_PIPE_INSTANCE must get Windows `ERROR_ACCESS_DENIED = 5`.
4. Authenticate real distinct local account with native `LogonUserW`, impersonate its OS token through .NET `WindowsIdentity.RunImpersonated`, verify Windows actual SID matches the created identity, and attempt native `CreateFileW(GENERIC_READ|GENERIC_WRITE)` on the *same* pipe. Must receive genuine `ERROR_ACCESS_DENIED = 5`, rather than `ERROR_PIPE_BUSY` or a synthetic string comparison.
5. Finally under the authorized original Windows account, native `CreateFileW` on that pipe must succeed. This proves positive path and negative token ACL behavior. The 03O independent-process same-user roundtrip and native SID impersonation run again in the same workflow.
6. The workflow also replays the 58 Windows N contract cases, previous Windows native CNG-P256 lab control with its explicit TPM-unavailable hard-stop, and 80 Linux N/M/L/K/G/J SQLCipher/JWT FUE on one exact SHA. Scope Gate required.

### Constraints and security truth

This negative proves **distinct OS account token access control on a Win32 pipe** but its alternate identity is impersonated *in the test process*. It **does not prove** a hostile unprivileged **separate process** cannot connect, nor custom Windows SCM **service SID** binding, installer ACLs, actual remote client denial over a controlled second host, Windows ACL changes under reboot, secure request framing, or CNG hardware TPM on the clinic PC. `PIPE_REJECT_REMOTE_CLIENTS` and `FILE_FLAG_FIRST_PIPE_INSTANCE` are exercised as native creation flags but the former needs a real LAN peer for empirical remote denial. The lab DACL grants full access to the test service account because a dedicated service SID/client SID has **not** yet been provisioned; a production pipe must separate service `FILE_CREATE_PIPE_INSTANCE` capability from client read/write rights. No account is created on any clinic PC.

**Residual P0:** actual distinct-account separate process denial, real service SID & installation SDDL least privilege with client CREATE_PIPE_INSTANCE denied, remote peer denial, Windows service execution / ACL recovery, physical machine TPM-based nonexportable CNG lifecycle/rotation, human UI click and session-bound patient confirmation, independent security review. **P1:** filesystem/SQLCipher power-cut recovery and orphan cleanup with immutable receipt ACK reconciliation. Real scanner remains later LOT10.4.

References: [Microsoft CreateNamedPipeW](https://learn.microsoft.com/en-us/windows/win32/api/namedpipeapi/nf-namedpipeapi-createnamedpipew), [Microsoft NamedPipeServerStreamAcl.Create](https://learn.microsoft.com/en-us/dotnet/api/system.io.pipes.namedpipeserverstreamacl.create). CurrentUserOnly overrides the supplied PipeSecurity, so the SDDL is created with the native API.

`READY_TO_MERGE=false`
`PRODUCT_READY=false`
`CLINICAL_GO=false`

**Next C05B-03Q:** if 03P true native token ACL deny succeeds, run an explicitly bounded same-machine **separate-process** low-priv account attempt and service SID/privilege separation; proceed only after exact-run proof and owner authorization. No clinical GO.
