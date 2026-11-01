# LOT06 B03 — Real encrypted spool read under Windows SCM LocalService (ISOLATED)

Parent PR #1193 HEAD `b59a46027bce09ec2588710bbb68117536c1014d`.
[Single canonical Notion](https://app.notion.com/p/3e677c66336281639beae2a946df1483).

## Actual testable implementation
The existing disposable Win32 SCM restricted LocalService fixture executes the repo-owned Python read helper **under its own Windows security token**, opening the actual AES-GCM/SQLite HotFolder spool and verifying every pending unassigned item via existing `read_unassigned`. Its restricted native Named Pipe returns only `S<digit>` (0..9), with no patient ID, digest, filename, image, key, receipt or write operation. An error is distinct (`E?`) from an empty queue (`S0`). No HTTP LAB endpoints become product routes.

Windows FUE: synthetic 2x2 PNG seeded into real HotFolder encrypted spool; ACLs scoped to the ephemeral service LocalService SID AND restricted service SID; separate authorized local Windows-account process queries native pipe and sees `S1`; separate unapproved account is denied; ciphertext is modified on disk and same authorized process must receive `E?`, never `S0` or `S1`. 58 Windows policy tests and previous Q/U continue. Service, users, files removed in runner teardown.

## HARD STOP / remaining
This proves a **service-owned read in a disposable isolated fixture**, not an installable clinical service. The helper uses a synthetic fixture-only 256-bit AES key in ephemeral ACL-restricted file; no TPM, no production key lifecycle or clinical device enrollment. It spawns a Python subprocess on query; runtime packaging, least-privilege production installer, service binary pinning, process environment hardening and machine-wide ACL review remain unverified. No patient UI attachment, no capture bytes leave IPC, no staff approval challenge, no clinical storage writes or ACK. Real remote Windows host, hardware TPM CNG, powercut/ACK/crash recovery, human review, physical scanner and independent security audit remain OPEN. B01 product status remains `NATIVE_IPC_NOT_CONNECTED`.

`READY_TO_MERGE=false`
`PRODUCT_READY=false`
`CLINICAL_GO=false`
No merge, deployment, clinic installation or real patient data.
