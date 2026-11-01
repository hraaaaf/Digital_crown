# LOT06 Phase2 B05-A — Real Windows SCM package and key file DACL FUE (LAB)

Parent: [B04 PR #1199](https://github.com/hraaaaf/Digital_crown/pull/1199) exact SHA `cf37fa8d679289b0c966b887141ed08a003ca677` **GREEN LAB**. Single [LOT06 canonical Notion](https://app.notion.com/p/3e677c66336281639beae2a946df1483); this file is only a subordinate technical runbook.

**Candidate status: exact SHA Windows tests pending, do NOT call B05-A green until runs complete SUCCESS.**

## Scope and adversarial FUE
The service is disposable and uses Windows SCM **LocalService with a restricted service SID** and a synthetic 2×2 PNG, AES-GCM and SQLite queue. Before starting the service, lock the **published DLL/package directory** to LocalService RX, exact restricted service SID RX, SYSTEM/Admin Full, without grants to Users/Everyone. The synthetic key file already has LocalService R and service SID R; real clinic keys must not use this mechanism.

A real **other Windows account**, distinct from the LocalService service and allowed to query the protected native Named Pipe, must be denied at kernel ACL enforcement when it attempts:
1. To read the actual fixture key file.
2. To open the published service DLL for writing.
3. To create a file under the service binary directory.

Each rejection must be the genuine Win32 **ACCESS_DENIED**; sharing violations, missing files and a swallowed error **do not count**. Check DLL SHA-256 is unchanged before and after attempts, and then ask the real restricted service for `S1` on the real AES-GCM spool. Inherit all **B04** FUE in the *same* B05 run: SCM STOPPED/RUNNING, ciphertext unchanged and S1, wrong AES key exact E2, restored key S1, changed ciphertext exact E2, second unauthorized account cannot access pipe; fixture completely deleted. Parent B03/B02, Linux 86 and React 8 plus Scope must remain green on candidate SHA.

## Critical non-claims
**B05-A is not B05 complete.** This proves only package ACL and key-file ACL **on a GitHub-hosted disposable Windows runner**. The .NET runtime and Python helper reside outside the protected package (GitHub runner tools/checkout) and are NOT pinned/protected by this test: a production installer must ship controlled immutable runtime/helpers and verify signed hashes. The key is a test file, not TPM/CNG non-exportable material. A real install/uninstall/upgrade, service recovery, machine reboot, file owner policy, privilege escalation, independently attested hardware-backed key enrollment, key rotation/revocation and backup remain unverified. No real scanner, clinical connection, patient data, visual workflow or signed clinical ACK. Tests must never assert production readiness.

`READY_TO_MERGE=false`
`PRODUCT_READY=false`
`CLINICAL_GO=false`
No merge, no deployment, no clinic installation.
