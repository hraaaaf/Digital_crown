# LOT06-P / P2 — ADR Windows SCM identity, NTFS DACL, SQLite WAL, migration (DESIGN ONLY)

Date: 2026-10-18. Status: **PROPOSED / P2-A+B DESIGN / SCM NOT TESTED / HUMAN GATE REQUIRED**. No installer, SCM registration, identity or data modification is authorized by this ADR.

Repository: hraaaaf/Digital_crown. Audited PR #909 HEAD **0e98237774bcd7d299335826b12c39a2cabc9393**, base **373ced67385a444996ba290755bdfcdd255440bf**, parent PR #901. Source locations below refer to the audited HEAD; revalidate if it changes. Original F01 design: LOT06_P_F01_WINDOWS_PRINCIPAL_DACL_ADR.md; storage contract: LOT06_P_SQLITE_WAL_WINDOWS_ACL_CONTRACT.md. Current F01 multi-standard-user laboratory is **EXPERIMENTAL**, not a real SCM token proof. The user has authorized investigation, not installation or clinical migration.

## 1. Goal, adversary and decision

Goal: **a normal interactive Windows user and arbitrary process running with that user's SID cannot directly read/write/replace the service-private acquisition DB, live WAL/SHM/journal, spool or secrets, while the actual SCM-hosted acquisition backend CAN create/commit/checkpoint/recover and expose only authenticated application operations**. This is a Windows local-host boundary, not protection from a local Administrator, SYSTEM, privileged backup operator, service-token compromise or malicious authorized API client.

Current same-SID peer can write DB/WAL/SHM in place; sharing flags that block some renames cannot deny such writes. No amount of filtering the child environment or locking the path changes its inherited primary token. The commercial F01 gate remains **OPEN**.

**Decision candidate B (CONDITIONAL):** ONE signed installed Digital Crown product and TWO modes: (1) dedicated headless SCM backend with a separate verified identity, which owns all privileged acquisition I/O, and (2) normal-user launcher that verifies backend health and opens/connects to the React UI. Do not put Tk/browser/provisioning into Session 0. Preserve API, auth/authorization, mobile/LAN compatibility, existing clinical data and packaging identity. This adds a *Windows service deployment mode*, even though it is not a second dentist-facing app; activation is separately gated.

Do not interpret this design decision as an instruction to change run.py or the installer. If clinical path/secret and restore compatibility cannot be proven for a full-backend service, return to the owner with **Option C** (separate imaging-only service + rigorously authenticated IPC) rather than silently grant interactive users access to private acquisition files.

## 2. P2-A — actual source inventory (at audited HEAD)

| Asset/process | Observed code, identity, path/source | Unknown or migration consequence |
| --- | --- | --- |
| Frozen launcher and HTTP server | run.py:5-15 verifies INSTALLABLE identity; 17-71 creates explicit cabinet .env and data/config/runtime/log paths ONLY in first-boot path; 74-94 Tk provisioning; 97-120 rotates log; 123-137 invokes guided restore subprocess; 186-224 claims RuntimeSupervisor and launches Uvicorn plus browser; DigitalCrown.spec: PyInstaller Analysis run.py / console=False | Existing interactive user token; no verified SCM mode, ServiceMain or service control handler. Need split and signed exact artifact |
| Interactive instance lock | backend/core/runtime_supervisor.py:30, 51-55, 80-111; platform.py:175-206 | Runtime directory, browser focus and loopback health assume interactive session; not an SCM watchdog |
| Startup/autostart | backend/core/platform.py:82-86 Windows task_scheduler | Scheduler is not SCM and confers no service SID |
| Clinical user data | backend/core/platform.py:93-135 defaults Windows APPDATA (or explicit DIGITALCROWN_* paths); backend/core/paths.py:17-44 maps clinical_vault.db; run.py:34-64 explicit profile/environment path and media root | Actual customer paths/owners/volume not enumerated; no assumption a running service can read per-user APPDATA |
| Cabinet encryption | run.py:55-64 creates SECRET_KEY, PAIRING_CODE_PEPPER, CABINET_MASTER_KEY_HEX, SQLCIPHER_KEY_HEX, MOBILE_PAIRING_KEY_HEX; backend/env_loader.py:84-106 loads .env; backend/core/key_material.py:21-33 preserves legacy SQLCipher key/passphrase fallback | No key rotation, automatic env recreation or blind DPAPI rewrap; migration requires controlled escrow and restoration |
| Clinical DB + sidecars | backend/database.py:21-35 resolves DATABASE_URL; :35-114 SQLite SQLCipher handling; :115-137 configures QueuePool and journal_mode WAL | Different persistence domain from imaging acquisition store. Must test SQLCipher, schema, key access, busy locks and live data preservation |
| Patient media | run.py:61-64 MEDIA_ROOT; backend/core/media_paths.py (location referenced from backend/main.py:41 and guided restore worker:14) | Actual rooted path and inherited DACL per installation must be measured; do not blindly relocate |
| Background jobs | backend/main.py:220-316 schema, sync_manager, Firebase, panoramic_engine, FTS background thread, daily_scheduler, relay, TTL cleanup and TEST-only bridge | Potential profile, network, scheduler or device dependency; validate each headless, no duplicate ownership |
| LAB bridge child | backend/main.py:309-316 TEST gate; tools/imaging_gateway/bridge_background_lab.py:173-240 subprocess.Popen([sys.executable, -m process_lab]), child environment filtering, GO/READY/Job assignment | Child inherits backend token; LAB remains disabled in cabinet, no real device producer or patient association |
| LAB SQLite | tools/imaging_gateway/gateway.py:150-177 creates private/spool/main DB; :245-334 opens sqlite3.connect by path and enforces WAL/FULL; sqlite_boundary_lab.py:75-146 pins verified Windows paths/handle | Current fixture is under specially marked TEMP; no SCM service principal, live sidecars remain path-based |
| Guided restore | backend/services/guided_restore_worker.py:40-96 copies main DB/WAL; :190-299 waits for parent, replaces DB/media, launches executable and probes /health | Existing relaunch is an *interactive executable*, not SCM StartService; rescue/rollback under new principal must be redesigned |
| API/mobile/LAN | backend/core/cabinet_topology.py:121-166 resolves host/port/TLS; backend/main.py:143-160 checks mobile license | User-facing auth + transport must remain functional; do not presume localhost = trusted |
| Logs, runtime, backups, certificates | run.py:97-120; platform.py:116-135; topology.py:138-148; guided restore; repository README/AGENTS | Actual roots, certificate private keys, backup staging, licensed vault and services that mutate them require installer preflight census |

**Scope honesty:** This is a source inventory, NOT a complete dynamic process/file-access trace from a packaged Windows installation. Installation-specific paths, vendor drivers and discretionary ACLs remain UNKNOWN. The referenced current code never proves a distinct SID for the bridge.

## 3. P2-B — alternatives and selected security principal

| Candidate | Security | Operational cost | Disposition |
| --- | --- | --- | --- |
| Interactive backend with same user SID | Same-SID file writes remain allowed | Low | REJECT F01 |
| LocalSystem + service SID | Admin-scale local privileges can bypass file boundary | Low account provisioning | REJECT default |
| LocalService + per-service SID | Least local privileges, but user SID shared by unrelated services; DACL MUST allow only service SID, not LocalService | Network anonymous, profile/secret compatibility | FALLBACK only with native oracle |
| Dedicated ordinary local account | Distinct SID; password/service-logon management and account recovery | Medium/high | FALLBACK if virtual account incompatible |
| **Virtual service account NT SERVICE\<stable SCM name> + configured service SID** | Per-service account/token without managed password; service name is an install identity and must not be casually renamed | Requires tested Windows versions, network machine-account exposure review, exact SCM packaging | **PREFERRED POC TARGET**, not implemented |

For the isolated Windows POC, propose a stable installer-owned per-install SCM name such as **DigitalCrownBackend_<opaque_install_id>** (name NOT final), running under its **own virtual service account**. The service SID must be resolved with Windows APIs; verify token user SID, service SID group attributes, disabled/restricted groups, integrity level, enabled privileges, SessionId=0, child-process token, service configuration and process executable path. Choose **SERVICE_SID_TYPE_UNRESTRICTED provisionally for compatibility testing only**; evaluate RESTRICTED as a separate, stronger candidate after a positive API/storage/profile proof. RESTRICTED affects restricted-token access checking and can break legitimate writes; choosing it from an icacls command is not a proof. Never treat configured SID without process token evidence as sufficient.

A separately launched child that opens protected files must itself run with the service token or another reviewed principal. No UI-user Popen bridge with direct private-store access.

## 4. Proposed resource map and effective permissions — NOT installed

**Illustrative only**, not the currently installed path: %ProgramData%\DigitalCrown\<install_id>\acquisition-private\ with private sqlite3 (plus -wal/-shm/-journal), encrypted-spool\, keys\, state\, diagnostic logs\. A distinct incoming\ producer exchange and separate clinical data/config/media roots are needed. The actual per-install root is an installer decision. The executable and updater binaries belong in a **non-user-writable, signature-verified protected installation root**, not under producer incoming or TEMP. Do not use a shared ProgramData root without per-install scoping.

| Resource | Virtual-service token | Interactive user / other service / producer | Trusted installer / admin / SYSTEM |
| --- | --- | --- | --- |
| Acquisition private directory | traverse/list and required create/delete-child only **within** private root | NO read/list/write/create/delete-child/WRITE_DAC/WRITE_OWNER | recovery/ACL maintenance only |
| Main DB, WAL, SHM, rollback journal | read/write/append/lock/delete as SQLite actually requires, **not** WRITE_DAC or WRITE_OWNER | NO read, write, append, delete, replace, rename, link or ACL change | authorized restore/backup |
| Encrypted spool and state | necessary read/create/rename/delete | NO private access | audited recovery |
| Key material | service decrypt/use through approved protected store; least privilege | NO raw key export, no decrypt | controlled escrow/recovery |
| Incoming producer drop | read/consume by service under strict path/format/provenance rules | producer only minimal creation/write (no private inheritance) | install/maintenance |
| Executable/SCM service object | read/execute and minimal service query | users may only query status if needed, **NO** CHANGE_CONFIG, STOP, DELETE, WRITE_DAC, WRITE_OWNER or binary replacement | limited trusted operations |
| Clinical DB/media/env/logs | required headless rights TBD only after compatibility and explicit migration gate | existing authorized semantics retained until migration | recovery |

Implement **protected non-NULL DACL** on private root, with explicit OI/CI inheritance and no inherited Everyone, Users, Authenticated Users, ALL SERVICES, CREATOR OWNER broad grants, machine-local generic writable principals or unrelated services. New SQLite-created sidecars must have safe inherited ACEs, no unanticipated explicit/inherited ACE and no reparse/hardlink escape. DACL inheritance need not be disabled on EVERY child if the protected private root is the approved inheritance source; inspect each child and reparse ancestry, never only parent icacls output.

**Subtle Windows blocker:** a new sidecar created by the service may be **owned by the service**, and owner status can confer implicit READ_CONTROL/WRITE_DAC. Evaluate inherited **OWNER RIGHTS (S-1-3-4)** ACE to constrain those implicit rights, with real positive SQLite operations and denial of WRITE_DAC even for the service token. Do not claim a sidecar owner is installer-owned just because the parent is. A service that may change its own DACL can relax the boundary after compromise; if OWNER RIGHTS cannot be enforced compatibly, document accepted service-compromise scope and reconsider the stronger hardening requirement. Test actual creator, owner, ACL and effective access immediately after sidecar creation and after reopen/restart. Never fix service-access failures by granting generic write to BUILTIN\Users or LocalService.

**Access oracle:** use Win32 GetNamedSecurityInfo/GetSecurityInfo to read DACL + owner + protected flag and per-ACE mask and inheritance; token introspection GetTokenInformation; AuthzAccessCheck/AccessCheck for diagnostic predictions; and **actual CreateFileW / ACL/rename/link/replace operations** under real tokens for decisive outcomes. Explicit rights: FILE_WRITE_DATA, APPEND_DATA, FILE_ADD_FILE, ADD_SUBDIRECTORY, FILE_DELETE_CHILD, DELETE, WRITE_DAC, WRITE_OWNER, READ_CONTROL, SYNCHRONIZE, FILE_READ_DATA, FILE_WRITE_ATTRIBUTES, ACCESS_SYSTEM_SECURITY/privileges as appropriate. Check token group and owner effective rights, NULL/empty DACL, privileges, MIC/integrity, reparse point/volume type. No expected denial can be satisfied by FileNotFound or broken fixture.

**Secrets:** LAB hex env key never becomes production credential. Provision a service-readable encrypted store with scoped wrapping, explicit offline recovery package/key-escrow under owner-controlled authentication, versioned key IDs and tested restore/rebind. User-scope DPAPI re-encryption or machine-scope DPAPI must be threat-modelled; machine scope alone is not equivalent to isolation against local users. Preserve the original SQLCipher and cabinet keys byte-for-byte in a protected recovery path until an approved rekey is demonstrated. Do not store secrets in command line, plaintext global env, repo, logs or writable config.

**API channel:** launcher (interactive SID) never opens private store; React ↔ backend uses authenticated API with per-user/per-cabinet object-level authorization and explicit CSRF/CORS/origin/session policy. Loopback port is not an auth boundary. LAN/mobile uses TLS and credential/certificate validation where required by existing topology. Keep bound address, certificate/key readability by service and firewall scope explicit; disable unauthenticated admin/maintenance/restore endpoints. Disable local privilege escalation through service IPC, path arguments or user-supplied imports. Service STOP/config permission is separate from HTTP authorization.

**Limits:** administrator/SYSTEM/elevated processes can bypass OS discretionary protections; attacks in the actual service token are in the trusted computing base; machine compromise, arbitrary privileged DLL injection, physical drive offline access, malicious authorized user actions, and device-firmware trust need distinct controls.

## 5. P2-C — REQUIRED Windows native synthetic test matrix (none asserts current SCM success)

All scenarios require an isolated disposable NTFS Windows VM, an approved *real SCM service installation gate*, no patient data, no clinical device. Record full image SHA, executable/signature, token user/group/service SID, privileges, DACL owner and masks, UAC elevation, file/volume IDs, service exit status, database hashes, integrity_check, ledger counts and restored rows. Use two identities: true SCM token **positive** and ordinary interactive SID **negative**; include other service using shared LocalService SID if fallback chosen.

| ID | Positive authorized operation and oracle | Unauthorized/negative oracle | Current P2 disposition |
| --- | --- | --- | --- |
| W01 | SCM creates WAL database and real -wal/-shm/journal under private root; inspect actual owner/inheritance/ACE of each | Interactive SID cannot read/write/create/append any current or recreated leaf | NOT TESTED SCM |
| W02 | BEGIN/COMMIT and ROLLBACK yield correct rows, FULL synchronous, foreign key/integrity checks | Interactive SID cannot r+b identical-byte DB/WAL/SHM; attempt must get access denied, not content hash alone | NOT TESTED SCM |
| W03 | checkpoint PASSIVE/FULL/TRUNCATE with active readers; WAL replay consistent | other SID cannot force checkpoint, swap/replace sidecar, unlink or rename | NOT TESTED SCM |
| W04 | competing authorized connections: busy_timeout, read isolation, no duplicate writers | other SID cannot open in place while authorized connection open or closed | NOT TESTED SCM |
| W05 | kill service process mid-transaction, SCM recovery, committed set stable, uncommitted set absent | substitute WAL/SHM before recovery fails closed | NOT TESTED SCM |
| W06 | online SQLite backup API or reviewed SQLCipher equivalent; restore to fresh isolated root verifies rows and keys | ad-hoc live main-db-only copy is rejected as invalid backup proof | NOT TESTED SCM |
| W07 | after sidecar delete/recreate/restart, correct owner/DACL/OWNER RIGHTS and normal SQLite writes | hostile SID cannot WRITE_DAC, WRITE_OWNER, DELETE_CHILD, hardlink, symlink/junction, reparse swap, replace or rename | NOT TESTED SCM |
| W08 | installer fresh install and idempotent upgrade preserve exact identity, keys, data counts, integrity and ACL | wrong SID, stale SID, permissive ACE, NULL DACL or wrong volume aborts before DB opens | NOT TESTED SCM |
| W09 | rollback/reinstall/restore under approved rebind principal preserves data and decryptability | failed migration/restore leaves old data and service OFF; no silent blank database | NOT TESTED SCM |
| W10 | SCM StartService/StopService, service handler, delayed/retry recovery, headless UI/login/mobile parity | wrong token, SessionId, service binary writable by user or unauthorized SCM change fails gate | NOT TESTED SCM |
| W11 | spool ciphertext read/decrypt/replay once, no PHI in logs, producer may deposit only incoming | producer and UI cannot access spool/key or bypass API authorization | NOT TESTED SCM |
| W12 | disk-full, access denied, partial staged migration, unavailable secrets, restore/network loss fail closed and recover | unexpected sidecar paths/temp files and user-writable install directories fail gate | NOT TESTED SCM |

Existing experimental two-standard-user F01 harness tests *some* filesystem denials; it is **NOT equivalent** to any Wxx test with actual SCM. Existing LAB sqlite3 tests exercise selected synthetic transactions, not this full Windows security/recovery contract. Linux/Windows stdlib-only smoke tests, if added, must be labeled **synthetic SQLite semantics**, not native security evidence.

Acceptance invariant: **(service token CAN commit + checkpoint + restore) AND (interactive/other forbidden token CANNOT read/alter any protected file nor retake ownership/change DACL)**; an access-denied positive path is a FAIL, and a successful unauthorized identical-byte write is a security FAIL regardless of unchanged hash.

## 6. P2-D — installation/upgrade/migration and rollback protocol (FUTURE; HUMAN_GATE_REQUIRED)

**PRE-FLIGHT before any change:** verify human authorization, local administrative support, signed artifact/checksum, supported Windows build and NTFS local volume (no SMB/WAL network drive), current service/launcher/install identities, SCM DACL, antivirus locks, running writers/jobs, real cabinet config, DATABASE_URL/clinical schema/SQLCipher driver and passphrase, media/TLS/license vaults, backup/restore staging, Windows startup strategy, version migration graph, free space, permission census and independent reversible restore media. Capture machine-independent manifest with *redacted* path identifiers/hashes, not keys.

**Phase 1 — baseline rescue (no mutation of existing clinical state):** quiesce existing writers via agreed maintenance window; consistent SQLCipher-aware online backup/checkpoint if supported by current driver; include all media/config, authorized keys and licensing state with encrypted recovery escrow. Verify detached restore in disposable profile with complete schema, rows and decryptability; rollback gate fails if backup alone exists without proven restore. Preserve original untouched until owner sign-off.

**Phase 2 — shadow isolation:** create fresh per-install ProgramData root under trusted installer, validate NTFS and protected DACL/owner/OWNER RIGHTS; store temporary synthetic DB and service-private key *without reusing clinical secrets*. Apply ACL before service first opens any DB. Re-check effective rights with actual test tokens and dynamically generated leaves. No temporary Users/Everyone/LocalService broad grants.

**Phase 3 — service POC (requires separate explicit approval even in lab):** register service via protected installer transaction, fixed signed ImagePath + explicit headless mode, stable unique name, virtual account, chosen SID type, minimum required privileges, secure service object DACL, SCM status callbacks/shutdown timeout/recovery. Verify token from inside service and positive + negative W01-W12. No attempt to pop UI in Session 0 or to rely on Task Scheduler as equivalent.

**Phase 4 — compatibility rehearsal:** launch existing React UI through a user-session launcher, reuse certified API/object authorization, check login/licensing, clinical SQLCipher, TLS/LAN/mobile if implemented, FTS/scheduler/panorama dependencies, backup/restore and crash recovery. This is an isolated exact-version rehearsal; clinical DB identity must not switch to a blank database. Only then request *new* approval for any real clinical profile/ACL/key/data migration and installer entrypoint change.

**Commit/rollback transaction:** stage target config and ACLs separately; keep original executable/profile/data and encryption keys intact; fail before activation on any deny/allow mismatch. On failure, stop/reap test service, disable new backend, restore previous autostart/launcher/profile mapping using previously checked artifacts, **restore a transactionally consistent snapshot** only if actual data rollback is needed, validate encrypted DB/media/keys, and attest full API operation; never downgrade a schema without a rehearsed backward-compatible path. If irreversibility occurs, fail to MANUAL_RECOVERY, no auto activation or unapproved restoration.

**Upgrade/reinstall/uninstall:** maintain service name/SID lifecycle intentionally; rename changes service SID and can orphan data. Version manifest tracks installer/package SHA, existing SID, DACL, schema, encryption key IDs and restore compatibility. Uninstall stops/removes *service binaries* only on separate authorization; patient/clinical media, private acquisition, backup and recovery keys remain retained unless separately approved for disposal. Reinstall must prove matching identity or authorized ACL/key rebind, never create empty replacement cabinet.

## 7. P2-E — adversarial and authorization gates

BLOCKER: SEC-A01 inherited child token; SEC-A02 same-SID DB/WAL/SHM writes; no real SCM process token; ownership of dynamic sidecar/OWNER RIGHTS is unproven. BLOCKER at commercial activation: any private-store write by ordinary interactive SID; service denied legitimate WAL; unverified restore; unattended clinical data/key switch.

MAJOR: SEC-A03 incomplete owner/ACE/effective mask oracle; SEC-A04 rename/replace/hardlink/reparse/new sidecar gaps; SEC-A05 SQLite VFS path-based TOCTOU; Windows packaged entrypoint and Session 0 behavior not implemented; clinical SQLCipher key/profiles/restore under new service token not inventoried dynamically; SCM DACL and API LAN/mobile/endpoint auth parity not exercised; upgrade/change SID/rollback unrehearsed.

**Two internal adversarial perspectives, no independence claim (DESIGN ONLY):**
- DC03 security: **6/10**. An actual per-service token is the correct architectural direction; the root still has no real SCM effective-rights proof, and owner-rights, IPC and secret compromise threats are open. NOT CONVERGED.
- DC04/DC05/DC07 reliability: **5/10**. The design makes migration rollback explicit, but cannot show that real SQLCipher, guided restore, scheduler, and frozen startup survive a switch. NOT CONVERGED.
Neither perspective executed W01-W12, and neither is a genuinely independent external reviewer. Scores are P2 design-readiness indicators, not certification scores.

**Required current-source CI:** exact-HEAD Windows/Ubuntu 06-A, 06-B, Scope Gate, Portability and security guards. **Experimental:** cross-SID F01 and future native SCM simulation. **HORS SCOPE:** clinical devices, real patients, production imaging, LOT10 physical PC, Vercel, clinical release.

**Gate decision:** GO for additional read-only audit, ADR review, and new synthetic-only unit tests. **NO-GO for SCM installation, altered runtime identity, clinical migration, merge, release or deployment** until owner separately authorizes the exact POC host, name/account/SID type, installer and rollback boundaries. Next after approved synthetic POC: real Windows native W01-W12 under service token, then two genuinely independent clean reviews on final exact SHA and confirmation.

## 8. Official technical references (checked 2026-10-18)

- Microsoft SERVICE_SID_INFO: https://learn.microsoft.com/en-us/windows/win32/api/winsvc/ns-winsvc-service_sid_info
- Microsoft Service Accounts: https://learn.microsoft.com/en-us/windows/win32/services/service-user-accounts
- Microsoft Virtual Service Accounts: https://learn.microsoft.com/en-us/windows/security/identity-protection/access-control/service-accounts
- Microsoft CreateService virtual accounts: https://learn.microsoft.com/en-us/windows/win32/api/winsvc/nf-winsvc-createservicea
- Microsoft SCM Service Security: https://learn.microsoft.com/en-us/windows/win32/services/service-security-and-access-rights
- Microsoft Session 0: https://learn.microsoft.com/en-us/windows/win32/services/service-changes-for-windows-vista
- Microsoft Owner Rights S-1-3-4: https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/understand-security-identifiers
- SQLite WAL: https://www.sqlite.org/wal.html
- Existing repository ADR/contract: docs/quality/LOT06_P_F01_WINDOWS_PRINCIPAL_DACL_ADR.md and docs/quality/LOT06_P_SQLITE_WAL_WINDOWS_ACL_CONTRACT.md.
