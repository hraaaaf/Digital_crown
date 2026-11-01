# LOT06 C05B-03O — Native Windows inter-process IPC and CNG proof (lab only)

Date 2026-11-01. Child of [PR #1184](https://github.com/hraaaaf/Digital_crown/pull/1184) pinned at `18058e65cc568b76f6fa3f238763bfee883c9f27`. Canonical [Notion V1.5-06](https://app.notion.com/p/3e677c66336281639beae2a946df1483).

## Scope and critical distinction

03N created a CurrentUserOnly Windows Named Pipe only and **did not** prove IPC. 03O tests in a disposable Windows CI runner:
- An actual Windows Named Pipe server and a **separate PowerShell Job process** as client; rejects same PID; roundtrip synthetic bytes with deadlines. Server invokes real Win32 `ImpersonateNamedPipeClient`, reads the impersonated OS principal SID and compares it with expected Windows user SID, checks API result, and calls `RevertToSelf` in finally. The pipe is `PipeOptions.CurrentUserOnly`, not a custom SCM service pipe.
- Real Windows CNG `CngKey.Create(ECDsaP256)` in Microsoft Platform Crypto Provider (TPM **if available**), or an explicitly differentiated Microsoft Software Key Storage Provider **laboratory control only**. Test creates uniquely named ephemeral test-lifetime persisted keys, SHA-256 signs and verifies a synthetic string, rejects modified payload, attempts forbidden private key export, then deletes keys in finally. **Software KSP success is NOT product fallback or TPM certification.** On a hosted VM with no Platform KSP, show explicit `TPM_UNAVAILABLE_CABINET_HARD_STOP`, not false hardware GREEN.
- The existing C05B-03N matrix of 58 synthetic negative-policy checks runs on Windows, while Linux executes the full 80-case N/M/L/K/G/J chain on exactly the same candidate SHA. CI Scope Gate must pass.

This is a more concrete Windows lab probe, **not** a native service/clinical integration or independent security review.

## What remains OPEN, regardless of CI

- **P0**: Win32 `CreateNamedPipeW` with explicit SDDL DACL / `PIPE_REJECT_REMOTE_CLIENTS` and `FILE_FLAG_FIRST_PIPE_INSTANCE` implementation and **negative client test from another unprivileged Windows account**. CurrentUserOnly alone is insufficient to prove the production principal boundary. The test is an isolated same-user job, not a Windows SCM service SID with installer-specific ACL.
- **P0**: Genuine Windows service SID, service account boundary, restart policy, broker/collector privilege split, scoped paths and DACL under an installation. No real Windows installer or SCM activation is authorized.
- **P0**: Hardware-backed CNG on *target physical cabinet PC*, persistent key enrollment, admin approval, pinning and key rotation/revocation. Windows hosted VM TPM probe is only capability telemetry; it does not prove actual deployed key security. Never silently promote software provider.
- **P0**: Actual clinical UI showing two independent patient identifiers and media digest plus explicit authenticated staff confirmation, keyboard + 200% scaling and negative user journey FUE. 03M generated synthetic staff-review events, never a real operator click.
- **P1**: Real power-cut / filesystem fsync / AES ciphertext orphan GC / SQLCipher receipt+audit+outbox / client ACK reconciliation, full restore/recovery evidence, and matching signed read-only receipt lookup after lost ACK. 03N state machine tests are synthetic.
- **P0 review gate**: Independent security review and explicit owner approval BEFORE product route, merge or installation. No automatic patient association by file metadata, appointment inference, or raw scanner name.

## Requested future go/no-go evidence for 03P

Real Windows test with physically separate unprivileged identity and custom SDDL, protected service SID, explicit native remote rejection; real CNG KSP + nonexportability and revocation on the cabinet machine; manual human approval UI at 200%, power-loss and crash matrix. Keep a single immutable screenshot/log/trace index tied to exact SHA and independent reviewer signoff. If hardware provider is absent, fail closed, do not select software KSP implicitly.

`READY_TO_MERGE=false`
`PRODUCT_READY=false`
`CLINICAL_GO=false`
