# LOT06-P / F01 — Windows process principal + NTFS DACL (ADR, DESIGN ONLY)

Date: 2026-10-17  
Status: **PROPOSED / HUMAN GATE REQUIRED / NOT IMPLEMENTED / F01 MAJOR OPEN**  
Evidence baseline: PR #909 at \`e710ddf12add68f6a4e1339b592ff3552349ebd1\` (head before this ADR).  
Scope: Imaging Bridge **synthetic LAB** and proposed future commercial acquisition-store boundary, **not** existing patient clinical DB migration or Windows installer approval.

## 1. Why the current guard is insufficient (VERIFIED)

The native Windows 06-A run #39052253074, job #117453031824, executed 391 cases (390 PASS, 1 SKIP). \`test_windows_peer_can_write_same_byte_in_place_on_db_wal_shm\` passed: a *different Python process running with the SAME CI user token* opened the existing main acquisition SQLite DB, WAL, and SHM in \`r+b\` during a held connection, rewrote only the identical first byte, and left all three SHA-256 values and the synthetic ledger intact.

**Correct interpretation:** this proves a peer's in-place **write capability** under the same Windows identity. It neither proves deliberate corruption nor a different-user ACL bypass. Holding file/directory HANDLEs without \`FILE_SHARE_DELETE\` prevents certain renames, **not** permitted write opens. The Python sqlite3 VFS still opens DB/WAL/SHM/journal by path. F01 remains **MAJOR OPEN**.

## 2. Actual packaging/runtime conflict (verified from repository)

- \`run.py\`: a single packaged program checks \`INSTALLABLE_CERTIFIED\` identity, selects/loads a cabinet env, optionally runs Tkinter provisioning dialogs, acquires the interactive \`RuntimeSupervisor\` lock, opens the user's browser, and calls Uvicorn. There is **no verified SCM service entrypoint** in this file.
- \`DigitalCrown.spec\`: PyInstaller \`Analysis(['run.py'])\` with \`EXE(..., console=False)\`; no evidenced service-host bootstrap.
- \`backend/core/platform.py\`: Windows default autostart strategy is \`task_scheduler\`; default Windows paths can resolve under per-user \`APPDATA\`. A scheduled task is **not** automatically a Windows service with a service SID.
- \`backend/core/runtime_supervisor.py\`: existing lock/browser readiness/focus assume an interactive launcher. Service Session 0 cannot directly show dialogs or open the user's desktop browser.
- \`tools/imaging_gateway/bridge_background_lab.py\`: LAB opt-in only, TEMP-marked fixture, child process and Windows Job; it does **not** currently run under a separate service token, and its test key is ephemeral. The child normally inherits the launcher token.
- \`backend/main.py\`: LAB Bridge starts only in isolated TEST. Do not silently enable in cabinet/production. The existing clinical database and patient media have separate ownership/continuity requirements; changing the entire backend identity would reach far beyond the Imaging LAB.

**Critical contradiction:** simply adding \`NT SERVICE\DigitalCrown...\` to a filesystem DACL while launching the current interactive EXE will either deny its access or require permissions for the user's actual token, restoring the same-user attack exposure. Never use “service SID configured” as a substitute for proving **the token of the process doing the SQLite I/O**.

## 3. Architectural options — decision gate

| Option | Strength | Blocking cost | Verdict |
| --- | --- | --- | --- |
| A: continue the current interactive Uvicorn EXE and apply path pin / same-user ACL | Smallest change; CI LAB already works | Same-token hostile process can still write; different path spelling/handle pin cannot repair token equivalence | **REJECT as commercial F01 closure** |
| B: run the *backend of the existing DigitalCrown package* through a dedicated SCM service mode with stable per-install service SID; user launches UI/browser separately via the same package | Allows file ACL to grant write only to backend service identity; Imaging Bridge remains an internal backend component, not a second dentist-facing application | Session 0 UI split; SCM bootstrap/stop/health, per-cabinet env, clinical-data paths, backup, permissions, upgrades, startup and rollback must be redesigned and proven; introduces a Windows service even if no second installed product | **PREFERRED CONDITIONAL DESIGN**, **NOT AUTHORIZED TO IMPLEMENT** |
| C: keep interactive backend and add a separately protected imaging service/process or task under a distinct account | Smaller migration of full clinical backend | Requires explicitly sanctioned IPC, auth, lifetime and credential boundary; may violate prior “no extra Windows service/app” constraint; task identity is **not** \`SERVICE_SID\` | **ALTERNATIVE ONLY IF HUMAN APPROVES TOPOLOGY CHANGE** |

**Human product/security gate:** the existing #909 scope explicitly says “no additional Windows service.” Option B **changes that assumption**. Design review can compare it; implementing/registering any service, changing \`run.py\`, installer, release, customer topology, PC ACL, or activation requires a specific **new owner decision**, separate from the current “Go” for design. Without that decision **F01 remains blocked**; no pretend DACL-only fix.

## 4. Conditional target B (if independently approved later)

1. **One package, separate execution modes, no interactive service UI.** Preserve the same signed DigitalCrown distribution. A service entrypoint (not currently present) would host headless backend/Imaging logic under SCM; a user-context entrypoint would only open/connect to the authenticated local/LAN UI. Neither mode may self-create a second clinical database. Define startup ordering, loopback/LAN TLS, health, shutdown, process ownership and fatal errors before any runtime code.
2. **Actual identity.** Select a stable SCM service name per the installer contract and resolve its SID from the SCM/system, never guess the SID string or hardcode a translated account name. Consider \`LocalService\` with a service SID rather than \`LocalSystem\` for privilege minimization, but **do not choose** \`SERVICE_SID_TYPE_RESTRICTED\` vs \`UNRESTRICTED\` without effective-token/compatibility tests. A service SID exists only if the configured service is actually started by SCM with the expected token. Mere process name, parent PID, token user, or Task Scheduler task is insufficient.
3. **Private acquisition root:** proposed location under an installer-controlled per-install/cabinet \`ProgramData\` subtree, distinct from executable/clinical DB and device-writable incoming. Paths and exact SID remain **TBD**, not presumed present. The *containing directory* and every generated child file must inherit a protected, explicit **non-NULL** DACL. Do not “grant users temporarily” on access denied. Owner and \`WRITE_DAC\` remain installer/authorized administrators, not ordinary workstation users or device producers.
4. **Minimal ACL intent (not installable SDDL):** actual service SID may read/write/create/rename/delete acquisition SQLite DB, WAL, SHM, journal and encrypted spool as required; administrators/SYSTEM retain narrowly specified recovery access; ordinary Users, Authenticated Users, Everyone, Guests, device-producer SID and other cabinet/workstation identities get **no write, append, delete-child, rename, \`WRITE_DAC\` or \`WRITE_OWNER\`** to the private subtree. Do not grant broad write to \`LocalService\` itself; another service can share that account SID. Define read restrictions for patient data and encryption key as well.
5. **Incoming separate:** only the authorized device producer has minimal create/write rights to an *incoming* root. No inheritance/propagation of producer write rights into private acquisition files, spool or secrets. Quarantine/copy, source validation and patient-confirmation boundaries remain explicit.
6. **Secrets and profiles:** use an approved per-install key store with service identity scope and restore/rotation story. The LAB hex key environment variable is prohibited commercially. Before switching backend identity, inventory existing \`APPDATA\`/explicit profile paths, certificate/key locations, current clinical DB media/SQLCipher credentials and Firebase privileges. Do not migrate/relocate any patient data in F01. **Failure must not lock the clinician out of reading/recovering existing patient records.**
7. **Install/upgrade/uninstall:** trusted installer creates the protected root and ACL before the service ever starts or SQLite opens. Validate owner, DACL, inheritance and filesystem before enablement; fail closed if any step is uncertain. Upgrade/rollback must preserve existing images/keys and prevent permission regression. Uninstall cannot remove clinical material without separately approved retention/restore.
8. **Service and API access surface:** service-control ACL must prevent ordinary user stop/reconfigure/service-binary replacement. Ordinary-user frontend communicates only via backend authentication/authorization, not raw filesystem or unauthenticated localhost trust. A process compromised **inside the service token**, or an administrator with effective control, remains outside the isolation claim.

### Proposed effective-permission matrix (intended behavior, unverified)

| Actor token | DB / WAL / SHM / journal | Encrypted spool + key | Device incoming |
| --- | --- | --- | --- |
| Exact acquisition service token/SID | Positive open / create / write / checkpoint / close; no need to own DACL | Strictly necessary positive reads/writes; key read only via scoped mechanism | Read only, under explicit producer contract |
| Ordinary interactive user (different SID) | **DENY** file read/change/create/replace/rename/delete/ACL edit | **DENY** read/write/delete/key export | Only what the device workflow requires; not implicit grant |
| Other local service, even sharing \`LocalService\` account | **DENY** by relying on per-service SID and effective token checks | **DENY** | No privilege by default |
| Separate cabinet/workstation/device producer | **DENY** | **DENY** | Limited producer create/write only |
| Installer-authorized administrator/SYSTEM | Audited backup/recovery rights only, never claimed blocked | Audited recovery rights only | Administrator policy-dependent |

**No ACL has been applied.** “DENY” above is an acceptance oracle, not an observed status or a suggestion to insert explicit DENY ACEs indiscriminately. Default-deny from a correct protected allow-list is preferable to incompatible inherited grant/deny mixtures. Null DACL = full access to everyone (fatal), empty DACL = deny everyone (service unusable).

## 5. Independent-oracle verification required BEFORE claiming F01 closure

- **Design/static gate:** trace \`run.py\` startup, \`DigitalCrown.spec\`, Task Scheduler versus SCM, backend lifespan, all source/target paths and authentication/restore workflows. Require human acceptance of topology/migration plan; no silent switch of launch mode.
- **Windows-native negative tests, synthetic fixture:** generate a real separate standard interactive user token and a real SCM service token with recorded user SID, groups and enabled service SID. Test via real \`CreateFileW\`/filesystem operations (not monkeypatch or \`AccessCheck\` alone) file read, \`r+b\` write, append, delete, rename, replace, hardlink/reparse and ACL modifications against main DB / WAL / SHM / journal / spool / key, both open and closed; test **sidecars created after startup** and under checkpoint/rollback/restart.
- **Positive path:** the actual dedicated service token writes WAL normally, checkpoints, closes/reopens, rotates/recovers spool and decrypts scoped secrets; backend remains functional. A deny for legitimate SQLite WAL activity is not success.
- **Filesystem/ACL oracle:** independently inspect volume type, root and child owner, inheritance/protected bit, NULL/empty DACL, explicit and inherited ACE masks, \`READ_CONTROL\`, \`WRITE_DAC\`, \`WRITE_OWNER\`, \`DELETE_CHILD\`, and process effective token. Verify newly created leaf permissions; ACL on a parent alone is insufficient proof.
- **Fault/release gate:** partial installer failure, unexpected parent death, power loss, crash/WAL recovery, disk full, concurrent clients, upgrade/downgrade, rollback, backup *and actual restore*; no leaks to logs. Verify signed packaged executable, exact SHA and service binary path.
- **UI/backend parity:** compare existing interactive open/browser and auth paths with the service-hosted design, plus workstation/mobile consumers *only if functionality exists*. No unobserved visual validation claim.
- **Review:** two genuinely distinct reviewers must inspect a **single final HEAD**, with real code/CI/artifacts and one further clean confirmation pass. Internal reasoning or green LAB tests alone are not independent approval.

## 6. Adversarial design review — INTERNAL only, not convergence

**Perspective DC03 / security — 5/10, MAJOR OPEN.** Proposed service identity is the proper direction *only if its actual process token differs from the user's*. Service SID in an ACL will not defend against service compromise, administrator privilege, broad \`LocalService\` grants, unprotected sidecar inheritance, machine-scope key export or unauthenticated backend IPC. **BLOCK implementation until** explicit principal/token, child-inheritance and key/ACL oracles exist. The same-SID write-capability evidence remains decisive.

**Perspective DC01+DC07 / architecture & operability — 4/10, MAJOR OPEN.** Converting the existing interactive frozen Uvicorn launcher directly into Session 0 is a regression risk: Tk provisioning, browser launch, single-instance lock, per-user profile secrets, clinical data access, restore and upgrades are not service-ready. Existing #909 expressly excludes an extra Windows service. **BLOCK implementation until** the user approves topology and a reviewed headless/interactive split or a demonstrably equivalent alternative is designed.

These are **two internal adversarial perspectives**, NOT external reviewers. No implementation, installer, separate-SID run, ACL test, packaged EXE run, review convergence, security certification or clinical acceptance.

## 7. Delivery decision / next

**Design result:** CONDITIONAL candidate B, **HUMAN_GATE_REQUIRED**. The user approved design investigation, **not** a service/installer/packaging change. The narrow LAB pin remains defense-in-depth only. F01 stays **MAJOR OPEN / NOT MERGE READY**.

**Next Extra High:** get the explicit topology decision *if a new SCM service mode is desired*, then create an **isolated Windows synthetic proof-of-concept** with distinct effective tokens and protected DACL *before touching the clinical backend or installer*. If service addition is refused, investigate a true separate restricted **task/account principal** alternative and prove its effective token rather than incorrectly calling it a service SID. Physical PC, signed installer and hardware acceptance = **LOT10, separately authorized**.

Roadmap: LOT06-P/F01 negative Windows capability verified -> design ADR / HUMAN GATE -> synthetic cross-SID proof -> reviewed integration -> two real independent reviews -> LOT10 -> clinical acquisition UI/patient mapping under separate gate.

## Technical primary sources (checked 2026-10-17)

- Microsoft SERVICE_SID_INFO, including restricted/unrestricted behavior: https://learn.microsoft.com/en-us/windows/win32/api/winsvc/ns-winsvc-service_sid_info
- Microsoft Service Changes / Session 0: https://learn.microsoft.com/en-us/windows/win32/services/service-changes-for-windows-vista
- Microsoft Interactive Services: https://learn.microsoft.com/en-us/windows/win32/services/interactive-services
- Microsoft Service User Accounts: https://learn.microsoft.com/en-us/windows/win32/services/service-user-accounts
- Microsoft How AccessCheck Works: https://learn.microsoft.com/en-us/windows/win32/secauthz/how-dacls-control-access-to-an-object
- Microsoft Null DACLs and Empty DACLs: https://learn.microsoft.com/en-us/windows/win32/secauthz/null-dacls-and-empty-dacls
- Microsoft ACE Inheritance Rules: https://learn.microsoft.com/en-us/windows/win32/secauthz/ace-inheritance-rules
- Microsoft CreateFile (share access vs requested access): https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew
