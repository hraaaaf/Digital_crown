# LOT06 Phase2 B05-C1 — signed candidate before real Windows SCM activation (LAB)

This is subordinate technical evidence; the single canonical lot file remains [Notion LOT06](https://app.notion.com/p/3e677c66336281639beae2a946df1483). Parent [B05-B PR #1202](https://github.com/hraaaaf/Digital_crown/pull/1202), exact green HEAD `0466c790af9ed9a3e5eef489144742da0e4236aa`.

## Goal

A disposable Windows runner builds the actual `win-x64 --self-contained` service executable, copies the existing B03 Python spool helper and imaging gateway sources, signs the closed inventory with disposable in-memory Ed25519 and places the **public trust pin outside the package stage**. Only after verifying that signed inventory and minimum generation does the test launcher issue `sc.exe start` on a **real LocalService restricted-SID SCM service** whose `binPath` points to the **same staged executable**. Check SCM RUNNING, native pipe response and running process executable path. After `sc.exe stop`, tampering with executable or Python helper, injecting a new file, or increasing the minimum trusted generation MUST fail admission while the SCM service remains STOPPED. Restore bytes and show genuine SCM restart. File/directory ACLs must grant only LocalService RX, the exact restricted service SID RX, SYSTEM/Admin F; never grant broad Users/Everyone. Dispose service, test Windows accounts, package and test key.

## FUE and reservations

The **LAB launcher** calls the admission verifier directly before `sc start`; this is **not a built-in Windows SCM policy** and an administrator with direct SCM control could bypass the launcher. No measured boot, TPM/CNG hardware binding, independently provisioned publisher identity, Authenticode, production installer, durable generation ledger or rollback-proof release counter. The Python helper is **sealed** but is **not executed by this SCM C1 test**, and the Python runtime and dependencies are not bundled. The manifest verifier/launcher itself is part of the checked-out CI source, not an independently trusted installer binary. The stage has a test-only admin maintenance grant, and no guarantee of atomic byte identity against a malicious administrator between validation and process execution (TOCTOU). No real scanner, patient data, clinical identity, Media Core receipt, ACK, clinic deployment or machine power-cut testing. Do **not** claim that this test produces an installable or clinically authorized release.

`READY_TO_MERGE=false`
`PRODUCT_READY=false`
`CLINICAL_GO=false`

No merge, Vercel deploy, clinic installation or clinical use.
