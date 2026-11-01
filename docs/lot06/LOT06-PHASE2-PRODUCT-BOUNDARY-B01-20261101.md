# Digital Crown LOT06 Phase2 B01 — Product boundary, read-only status

Base PR #1190, SHA `ec65c6c7564f81d36f19d893c0f764bc5f4c99a5`.
[Canonique Notion](https://app.notion.com/p/3e677c66336281639beae2a946df1483).

## Delivered within this software tranche
- One actual product GET endpoint `/api/patients/{patient_id}/acquisition/status`, behind normal JWT + workstation guard, patients permission, patient scope and read-only preflight. Response deliberately signals **native IPC unavailable** and `pending_captures=null`, not an empty inbox or device enrollment.
- Real patient Imagerie → Médiathèque shows the server status, with a denial on errors or contradictory responses. No capture preview, selection, confirm, media POST or device receipt is exposed through this UI.
- Existing manual media import untouched. Existing isolated Phase2 LAB HTTP routes NOT mounted in backend.main. No clinical file/DB change, no new schema or migration.
- Narrow CI executes live synthetic localhost SQLCipher/JWT/station negative test and React contract tests, plus parent Linux/Windows LAB regressions.

## Unfinished; HARD STOP before enabling clinical capture
1. Real local Windows Named Pipe adapter and service install with bound user/SCM Service SID, ACL, impersonation and *physical second Windows host* denial.
2. Hardware-bound CNG P-256 TPM keys with independent receipt pin, admin enrollment/rotation/revocation; no software fallback.
3. Unassigned encrypted capture queue, authenticated preview, real clinician identity verification, one-time server challenge and Win32 IPC-to-MediaCore transaction. The LAB challenge is NOT promoted.
4. Crash/powercut SQLCipher/AES/ACK staging/orphan reconciliation, read-only signed receipt recovery and no duplicate.
5. Observed UI FUE (390/430/768/1280, 200% zoom, keyboard), actual human confirmation, physical scanner LOT10.4, independent security review + owner GO.

The GET-only product UI is an intermediate FUE-I, **not complete Phase2 acquisition**. Neither GREEN LAB nor this status screen certifies clinical readiness.

`READY_TO_MERGE=false`
`PRODUCT_READY=false`
`CLINICAL_GO=false`
No merge, no deployment, no clinic installation, no real patient data.
