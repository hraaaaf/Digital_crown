# Portability & Launcher — P0 Baseline & Portability Contract

Status: **CLOSED — AUDIT/DOCS ONLY — NO PRODUCT CODE CHANGE**

Audited baseline: `a25893c7c1c3bb5bbecd6fb8ff54a0d81ab440a0`

Roadmap weight: **5 EP**

## Goal

Map the current Windows/macOS portability boundary before implementation: shared core, OS-specific integration, data/secrets, packaging, native/scientific dependencies, tests/CI and hardware assumptions.

## Success criterion

Every OS-specific dependency identified in the audited product path is either:
- explicitly shared/portable,
- explicitly Windows-specific,
- explicitly missing/unproved on macOS,
- or explicitly deferred to a named later roadmap lot.

Unknown vendor hardware support is treated as an explicit unknown, never as implicit compatibility.

## Proof boundary

This P0 is a source/configuration/dependency audit of exact baseline `a25893c...`. It does **not** claim native macOS execution, installer execution, hardware certification or scientific numerical parity. Those require later lots and real/native test environments.

---

## 1. Current product architecture — BEFORE

Current main packaged path:

`React build → PyInstaller spec → run.py → FastAPI/Uvicorn → bundled frontend → browser`

Windows distribution adds:

`DigitalCrown.exe → Inno Setup → per-user Windows install → Task Scheduler autostart`

A separate Tauri scaffold exists in `frontend/src-tauri`, but it does not currently supervise/start the Python/FastAPI backend and is therefore not the current desktop product architecture.

### Shared product core

| Area | Current implementation | Windows | macOS | P0 verdict | Target lot |
|---|---|---:|---:|---|---|
| Frontend | React/Vite static build | Yes | structurally portable | Shared core | P5/P7/P12 |
| Backend | FastAPI/Uvicorn/Python | Yes | structurally portable, not product-certified | Shared core | P5/P12 |
| API contracts | HTTP local/LAN | Yes | OS-neutral by design | Shared core | P2/P12 |
| Cabinet DB semantics | SQLCipher/SQLite path via `AppPaths` | Yes | native dependency not certified | Shared semantics | P3/P5 |
| Media/docs semantics | filesystem under app data | Yes | concept portable | Shared semantics | P1/P3 |
| Backup logic | encrypted archive + integrity/restore logic | Yes | concept portable | Shared semantics; key contract unresolved | P3/P9 |
| Licence validation | signed server licence + local encrypted store | Yes | concept portable | Shared semantics; storage/migration unresolved | P4 |
| Scientific models | local Python/native dependencies | Yes/current product path | not certified on Apple Silicon | High native risk | P5 |

---

## 2. Filesystem, configuration and user-data paths

Source of truth inspected: `backend/core/paths.py`, `backend/env_loader.py`, `run.py`.

### Current `AppPaths`

- `DIGITALCROWN_USER_DATA_DIR` can override the user-data root.
- Windows uses `%APPDATA%` when available, otherwise `~/AppData/Roaming`.
- Non-Windows currently falls back to `~/.config/DigitalCrown`.
- Database filename: `clinical_vault.db`.
- Logs: `<user-data>/logs`.
- Licence/config are derived from the same user-data root.
- Frozen resources use `sys._MEIPASS`.

### P0 finding

**macOS is not modeled as a native platform yet.** It currently falls into generic non-Windows behavior instead of a deliberate macOS application-data contract such as `~/Library/Application Support/...`.

### Action

P1 owns native OS path abstraction and the removal of direct platform assumptions from shared code.

---

## 3. Environment and secrets

`backend/env_loader.py` resolves environment files in this order:

1. explicit `DIGITALCROWN_ENV_FILE`;
2. repository/backend environment files;
3. user-data/config fallback derived from `AppPaths`.

`run.py` bootstraps a cabinet environment only when frozen and generates local secrets including `SECRET_KEY` and `CABINET_MASTER_KEY_HEX` where required.

### P0 contract

Every secret must later be classified as exactly one of:
- **machine-local**;
- **cabinet-portable**;
- **regenerable**.

No cross-platform migration may simply copy the entire application-data directory and call that portability.

P3 owns cabinet payload. P4 owns licence/local-secret semantics.

---

## 4. Licence implementation — current truth

Source inspected: `backend/services/license_service.py`.

Current implementation stores:
- `license.dat`;
- `license_secret.key`;
under the licence directory derived from `AppPaths`, with local Fernet encryption and signed licence validation.

### Important correction to historical audit

The currently audited implementation does **not** use the old hardware-fingerprint/DPAPI design that had been discussed previously.

Therefore P4 must not introduce a device-identity abstraction merely because an older implementation had one. Device identity is only justified if a concrete licensing requirement proves it necessary.

---

## 5. Backup / restore portability boundary

Source inspected: `backend/services/backup_service.py` plus current backup/recovery architecture already merged before this baseline.

Current backup logic is mostly OS-neutral:
- derives DB/user paths from `AppPaths`;
- produces encrypted backup material;
- validates restore candidates before replacement;
- uses local `backup.key` under user data.

### Open portability contract

A cross-platform Cabinet Bundle must explicitly define:
- what clinical data travels;
- what media/documents travel;
- what configuration travels;
- whether/how backup encryption material travels;
- what secrets must be regenerated/re-activated on the destination machine.

P3 defines Cabinet Bundle semantics. P9 certifies disaster recovery.

---

## 6. Launcher / runtime lifecycle

Source inspected: `run.py`, `backend/main.py`, `backend/tests/test_cabinet_mode.py`.

### Current `run.py`

- cabinet default host: `0.0.0.0`;
- default port: `8005`;
- host/port overridable via environment;
- starts Uvicorn directly;
- opens `http://127.0.0.1:<port>` in the browser;
- browser opening waits using a fixed approximately two-second delay;
- logs to the user-data log directory.

### Current `backend/main.py`

The P0 inspection did not find the historical second frozen browser opener that had previously targeted port 8000. The current architecture should therefore be treated as **one observed browser-opening authority in `run.py`**, subject to later static/runtime certification.

### Current remaining lifecycle gaps

- no proven single-instance lock;
- fixed-delay browser open instead of readiness-based open;
- no cross-platform supervisor contract;
- no native launcher state/recovery UX yet.

P2 owns these gaps. P11 owns user-facing launcher/recovery UX.

---

## 7. Windows-specific launch and operations

### `Start_DigitalCrown.bat`

Development helper:
- Windows `cmd`;
- activates `venv\\Scripts\\activate.bat` if available;
- runs backend with reload on port 8005;
- runs frontend dev server separately.

This is not cross-platform product infrastructure.

### `Start_PROD.bat`

Legacy Windows-only path:
- backend port 8000;
- optional local certs;
- Uvicorn workers;
- starts frontend using `npm run dev` on port 5173.

This differs from the current packaged single-port/product architecture and must not become the portability source of truth.

### PowerShell operations

`backend/scripts` still contains Windows PowerShell release/operations helpers including:
- `create_backup_release.ps1`;
- `create_release.ps1`;
- `run_real_backend.ps1`.

These are explicit Windows operational integrations, not shared-core requirements.

P1/P2/P6 own the future disposition of OS-specific lifecycle tooling.

---

## 8. Windows installer

Source inspected: `installer/DigitalCrown.iss`.

Current installer is explicitly Windows-only:
- Inno Setup;
- fixed `AppVersion=1.0.0`;
- install under `{localappdata}\\Programs\\DigitalCrown`;
- Start Menu/optional desktop shortcuts;
- Task Scheduler `ONLOGON` autostart;
- user data intentionally retained on uninstall.

### Gaps

- no macOS counterpart in current product path;
- no canonical shared version source;
- no cross-platform update engine;
- no clean dual-OS installation certification in current P0 evidence.

P6 owns Windows packaging. P7 owns macOS packaging. P10 owns updates.

---

## 9. Tauri status

Sources inspected:
- `frontend/src-tauri/tauri.conf.json`;
- `frontend/src-tauri/Cargo.toml`;
- `frontend/src-tauri/src/lib.rs`.

Current facts:
- Tauri 2 scaffold exists;
- product config version is `0.1.0`;
- bundle target is configured generically;
- icons include `.icns` and `.ico`;
- Rust code only builds a basic Tauri shell/log plugin;
- no Python/FastAPI sidecar supervisor is implemented there.

### Verdict

Tauri is **not** the current launcher/runtime architecture and must not be counted as macOS support. Any future adoption requires a separate architecture decision backed by proof that it improves the approved supervisor model.

---

## 10. Native/scientific dependency matrix

Source inspected: root `requirements.txt` and reachable product architecture.

| Dependency family | Current evidence | Windows | macOS/Apple Silicon | Risk / owner |
|---|---|---:|---:|---|
| ONNX Runtime | `onnxruntime-directml` on Windows; `onnxruntime` on non-Windows | explicit Windows path | package path exists but runtime/model parity unproved | High — P5 |
| OpenCV | Python package dependency | used/available in current stack | native wheel/runtime unproved here | P5 |
| TensorFlow | dependency present | package-level | Apple Silicon reachability/perf unproved | P5 |
| SQLCipher | cabinet DB architecture | current cabinet path | native build/runtime unproved | P5 |
| Pillow/image stack | dependency present | current product | native/runtime parity unproved | P5 |
| ReportLab/PyMuPDF/WeasyPrint/PDF stack | dependencies present | current product | output/runtime parity unproved | P5 |
| cryptography/Fernet | current backup/licence use | current product | concept portable; native build unproved | P4/P5 |
| frontend `onnxruntime-web` | frontend dependency | browser-runtime dependent | browser-runtime dependent | P5/P12 |

### Rule

Package availability is not certification. P5 must test only reachable dependencies and remove/quarantine dead native baggage rather than spending effort certifying unused libraries.

---

## 11. Version-source drift

Current version declarations are not unified:

- root `package.json`: `1.0.0`;
- frontend `package.json`: `0.0.0`;
- Tauri config/Cargo package: `0.1.0`;
- Inno Setup: `1.0.0`.

### Verdict

There is no proven single canonical application version source in P0 evidence.

P6/P7/P10 must converge packaging/update versioning before production cross-platform distribution.

---

## 12. CI / certification baseline

Current `.github/workflows` contains extensive application/browser/regression gates, but P0 code searches did not find dedicated `macos-latest`, `windows-latest` packaging, PyInstaller packaging or Tauri packaging jobs.

The exact merge baseline `a25893c...` returned no combined commit statuses through the connector, so P0 does **not** manufacture a green CI claim for that SHA.

Existing source-level cabinet tests include Windows-specific assumptions, notably `%APPDATA%` fallback and PyInstaller-secret guards in `backend/tests/test_cabinet_mode.py`.

### P0 conclusion

Current CI is rich at application level but does not yet constitute a Windows/macOS distribution certification matrix.

P12 owns the cross-platform CI/certification matrix.

---

## 13. Hardware/peripheral baseline

Repository searches performed during P0 for direct `RVG` and `DICOM` integration returned no indexed matches. This is **not proof that every possible hardware path is absent**, and it is explicitly insufficient to claim Mac hardware compatibility.

Current portability therefore separates:
- file/image import and pure software workflows, which can be certified in P5/P12/P13;
- direct device acquisition, drivers and vendor SDKs, which require explicit device-by-device evidence in P8.

### Rule

No peripheral is called macOS-compatible merely because Digital Crown itself launches on macOS.

---

## 14. Windows/macOS parity contract

### Must remain functionally equivalent

1. Clinical/business rules.
2. Patient and cabinet data semantics.
3. API contracts.
4. Database schema and migration semantics.
5. Document/PDF clinical content and accepted rendering constraints.
6. Backup/restore integrity semantics.
7. Cabinet Bundle format.
8. Authentication/licence semantics at product level.
9. Error/recovery states and safety behavior.
10. Scientific outputs within predefined numerical/clinical tolerances.
11. LAN/local-server semantics where supported.
12. Security/fail-closed invariants.

### Allowed to differ by OS

1. Application/config/log/cache filesystem locations.
2. Installer format and installation UI.
3. Code-signing/notarization mechanisms.
4. Autostart mechanism.
5. Native application chrome/menu/tray integration.
6. OS permission prompts.
7. Hardware driver/SDK implementation where vendor constraints force it.
8. Architecture-specific native acceleration, provided output tolerances and safety contracts remain satisfied.

### Forbidden divergence

- separate clinical/business implementations per OS;
- separate DB schema semantics per OS;
- undocumented feature loss on one OS;
- silent fallback from a certified hardware mode to an uncertified one;
- copying machine-local secrets as if they were cabinet data.

---

## 15. Initial certification matrix

| Capability | Windows baseline | macOS baseline | Required proof lot |
|---|---|---|---|
| Shared React/FastAPI core | Existing product path | structurally plausible, unproved native product | P5/P12 |
| User-data paths | explicit Windows | generic Unix fallback only | P1 |
| Launcher | `run.py` | not natively certified | P2 |
| Single instance | unproved | unproved | P2 |
| Readiness before UI | fixed delay | same conceptual gap | P2 |
| Cabinet export/import | not yet canonical cross-OS bundle | not yet canonical | P3 |
| Licence/local secrets | current encrypted local store | storage/migration unproved | P4 |
| Scientific runtime | current Windows-oriented product | Apple Silicon unproved | P5 |
| Windows installer | Inno Setup exists | N/A | P6 |
| macOS app/installer | N/A | absent as certified product | P7 |
| Hardware support | must be enumerated | unknown | P8 |
| Disaster recovery | current recovery foundation | cross-OS unproved | P9 |
| Update engine | no canonical dual-OS engine | absent | P10 |
| Launcher UX | browser-based launch | no native product UX | P11 |
| Cross-platform CI | no packaging matrix found | no macOS runner found | P12 |
| Real cabinet certification | not this P0 | not this P0 | P13 |

---

## 16. P0 decisions locked

1. **One product core, never two functional forks.**
2. Windows and macOS differences are isolated behind platform integration.
3. Apple Silicon is a required macOS certification target; Intel Mac support remains a later product decision.
4. Tauri is not assumed to be the solution merely because a scaffold exists.
5. `run.py` is the current launcher authority on the audited baseline; P2 replaces fixed-delay startup semantics with readiness supervision.
6. Current licence architecture is preserved unless threat model/product requirements justify change.
7. Cabinet portability and machine-local secret migration are separate contracts.
8. Hardware parity is independently certified from software parity.
9. Package presence is never treated as native compatibility proof.
10. No Vercel deployment is authorized by this chantier.

---

## 17. Gap → roadmap mapping

- OS paths/commands/autostart → **P1**
- supervisor/readiness/single-instance → **P2**
- Cabinet Bundle/cross-OS data movement → **P3**
- licence/local secrets → **P4**
- Apple Silicon/native/scientific dependencies → **P5**
- Windows packaging → **P6**
- macOS `.app`/DMG/PKG/signing/notarization → **P7**
- direct hardware/peripherals → **P8**
- disaster recovery → **P9**
- updates/rollback/versioning → **P10**
- launcher/recovery UX → **P11**
- dual-OS CI/certification matrix → **P12**
- real cabinet E2E → **P13**
- canonical closeout → **P14**

---

## P0 closeout

### Result
P0 is documentation/audit-only and introduces no product/runtime code change.

### Success
Met within the declared evidence boundary: current OS-specific integration is explicit, unresolved macOS/native/hardware claims are marked unproved, and every identified gap is assigned to a future lot.

### Proof
- exact audited baseline: `a25893c7c1c3bb5bbecd6fb8ff54a0d81ab440a0`;
- this canonical matrix;
- canonical roadmap restored/refined in the same docs-only commit;
- final Git diff must contain documentation only.

### Next
P1 remains **NOT STARTED** until the separate DECOMP-P0 large-file chantier is finished or product explicitly authorizes code work in parallel.
