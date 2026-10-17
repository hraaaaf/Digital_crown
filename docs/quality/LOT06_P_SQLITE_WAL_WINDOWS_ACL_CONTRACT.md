# LOT06-P — SQLite/WAL and Windows installer isolation contract

Status: **REQUIRED commercial design gate — NOT INSTALLED / NOT CERTIFIED**.
User decision 2026-10-17: remote PC offline; local Codex/physical hardware
tests intentionally DEFERRED TO LOT10. Do not attempt any installation now.

## Code scope and evidence

On PR #909 the **disabled-by-default synthetic LAB** uses a local SQLite
database `private/acquisitions.sqlite3` plus SQLite-created `-wal`,
`-shm` and possible `-journal` files. The imaging source and encrypted
spool read/create/rename flows are native root-relative on Windows. The
**Python sqlite3 default VFS still opens its database and sidecars by path**.
There is no documented stdlib parameter to attach the SQLite VFS to a
directory HANDLE. The path-based boundary can race after inspection.

The LAB mitigates this by:
- checking `private` is the original directory (including native volume/file
  ID on Windows) before and after opening SQLite and around each commit;
- checking DB, WAL, SHM and rollback journal leaves are regular files, not
  symlinks/NTFS reparse points, not hardlinks, with stable main-DB identity;
- requiring `PRAGMA journal_mode=WAL` to actually return `wal`;
- requiring synchronous FULL, trusted_schema OFF and memory temp-store;
- verifying SQLite reports exactly the expected main DB and no attachment;
- aborting before SQLite operations if an existing sidecar or root is unsafe.

### Additional Windows handle-sharing protections in the synthetic LAB

On native Windows, the LAB now holds `CreateFileW` handles on the verified
SQLite private **directory ancestry** and the existing **main DB leaf**,
with `FILE_SHARE_DELETE` deliberately omitted, until the database connection
has closed. These narrow OS sharing protections are more than path observations:
native negative tests prove directory/main-DB rename denial while the handles
are held, release after connection close, and main-DB rename refusal when
attempted by a **second disposable Python process** (CI 06-A Windows).
The database identity and observed sidecar safety guards remain necessary.

**Limitations still MAJOR:** the stdlib SQLite VFS itself remains path-based.
The held main-DB handle does not prevent **in-place content writes by a process
with sufficient access**, the creation/replacement of unpinned
`acquisitions.sqlite3-wal`, `-shm` or `-journal` names, or all filesystem
races during initial database creation. Directory sharing is not equivalent
to a per-service protected NTFS ACL. No installed Windows service SID,
hostile-effective-user access matrix, real-PC trial or physical device testing
has been performed. Do not classify F01 as closed because the synthetic
interprocess rename test passes.

Other checks remain fail-closed **observations**, not a race-free Windows
sandbox. F01 remains **MAJOR OPEN** until a demonstrably protected native
Windows process/ACL boundary or a proven, comprehensively handle-anchored
SQLite VFS covers the threat model and every relevant database I/O.

## Commercial installer / Windows DACL CONTRACT (future, not executed)

**Installer prerequisites (REQUIRED):**
1. Install Imaging Bridge as part of the Digital Crown package, as an
   internal background component without a second app in the dentist UI.
   The installer must identify the actual service/security principal. Do
   not hardcode an account name or assume SYSTEM-only is enough.
2. Use a private per-cabinet/workstation data root **separate from the
   install binaries and separate from the incoming device drop-folder**,
   e.g. an installer-owned subdirectory of `%ProgramData%`. Never
   create or move the clinical spool under TEMP, Public, user Downloads,
   or a device-writable directory.
3. Protect that root and every descendant (`acquisitions.sqlite3`,
   `-wal`, `-shm`, `-journal`, encrypted `spool`, key material) with
   an explicit protected NTFS DACL: full necessary access only to
   the dedicated service/security SID and authorized administrators/system
   according to the installer threat model. No write/modify/append/delete
   inherited for Everyone, Users, Authenticated Users, Guests, or another
   cabinet's workstation principal. Validate effective access as both
   service SID and ordinary interactive user. The owner/backup/restore
   permissions must not silently expand after an upgrade.
4. Only device-specific `incoming` has separately minimized producer
   write permissions; never grant that producer an ACL on the SQLite or
   encrypted spool root. The Bridge may read authorized incoming images
   but cannot use another patient's open UI tab as an attachment claim.
5. Encrypt the spool key at rest using an approved per-installation
   mechanism (e.g. service-scoped Windows DPAPI or equivalent secret
   store); the ephemeral `DC_V15_06_BRIDGE_LAB_KEY_HEX` test variable
   **must never become a commercial installation credential**.
6. Retain a process lifetime contract for the internal Job Object and
   prove ownership with the actual packaged executable/process tree.
   Multi-worker FastAPI must have an exclusive single acquisition owner
   per workstation; no competing writers or duplicate scans.
7. The installer must stop if the NTFS filesystem, SID creation,
   protected DACL, integrity verification or key access cannot be
   established. **Fail closed, no partial clinical activation**.
   Installer uninstall must not delete patient/media data without a
   specific, verified data-preservation procedure.

**Installer validation / evidence (REQUIRED, DEFERRED TO LOT10 Windows):**
- exact signed package hash, authenticated publisher, OS version, path,
  service principal/SIDs and NTFS volume type;
- DACL before and after creation, normal-user negative modify tests on
  main DB, WAL, SHM, spool and key, and service SID positive tests;
- junction, hardlink, reparse swap, open-file rename races while SQLite
  uses WAL with concurrent connect/checkpoint/rollback, no external writes;
- abrupt process parent death, Windows Job Object kill/reap, service restart,
  power interruption, WAL replay, corruption/disk-full/reserve, backup/restore;
- two cabinets, two workstations, multiple workers, backpressure;
- source/target trace showing **only** synthetic data in test environments;
- install/upgrade/uninstall preservation and rollback.

**Never claim F01/F04 commercially CLOSED before those checks succeed and
two genuinely independent reviewer assessments of the exact final HEAD.**

## CI classification

REQUIRED for current LAB source: Windows/Ubuntu 06-A, backend 06-B, Scope,
Portability, storage boundary negative tests and no patient link.
EXPERIMENTAL: isolated process/ACL engineering experiments on CI Windows,
not an installer and not standalone clinical certification.
HORS SCOPE in this batch: interactive/mobile UI, vendor drivers, hardware,
patient mapping, real cabinet operation, all local PC testing (LOT10).

Roadmap: LOT06-P synthetic protection and independent review OPEN →
installer/ACL Windows physical trial deferred LOT10 → patient acquisition
session UI and choice manual/automatic, each separately safety reviewed.
