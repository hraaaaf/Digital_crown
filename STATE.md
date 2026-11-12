## DECISION CANONIQUE DE GOUVERNANCE — 2026-11-09 — FUE À LA PLACE DE REVUE INDEPENDANTE DE CODE

**Décision propriétaire 2026-11-09 — FUE remplace la revue indépendante de code comme gate standard.** La preuve requise est une FUE-0/I/G réellement exécutée, proportionnée au risque, avec scénarios négatifs/sécurité et oracles explicites, résultats inspectables, artefacts et SHA/HEAD exacts. Aucun reviewer indépendant, double review A/B, agent externe ou validation fictive n'est requis **en plus** de cette FUE pour un merge logiciel. Une FUE verte ne vaut pas automatiquement autorisation de merge, acte médical, restauration réelle, installation, validation humaine clinique/réglementaire/physique ou déploiement ; ces gates explicites restent inchangés. Les sections historiques qui imposent une revue indépendante de code sont supersédées prospectivement ; leurs constats et preuves restent archivés.

**Effet immédiat pour LOT05 / J7 et les lots V1.5 à venir :** un reviewer indépendant absent ne bloque plus une PR lorsque la FUE et les contrôles spécialisés applicables sont exécutés avec preuves exact-HEAD ; un backend CI encore en cours/rouge, une faille prouvée, ou une autorisation humaine requise continue à bloquer. Les anciennes mentions « fresh independent review », « separate reviewer », « two reviewers » ci-dessous conservent leur valeur d'historique et **ne sont plus un gate prospectif**. La roadmap/Notion et `AGENTS.md` sont autorités.

# STATE — DigitalCrown

## LOT08.3-B3 — 2026-11-12 — NEVER-CONSUMED EXPIRED QR G3 RETENTION (SYNTHETIC LAB CANDIDATE)

**Owner GO / one bounded decision:** 2026-11-12 explicit owner "Go" after disclosure of HIGH effort. Complete a **LAB-only software** G3 gap: tenant-scoped expiration of unconsumed kiosk QR at the exact kiosk denial boundary, and fail-closed encrypted restore of snapshots that would reintroduce expired tokens. Physical custody, real devices, actual loss of workstation and installed Windows certification belong **exclusively to LOT10**, not a software closeout dependency for LOT08. No installable, prod scheduler, clinic data, migration, merge, release or deployment authorization.

**Baseline and branch:** started from `master@5582ca44da563da4b28c4f64e2bf539ff7bcd285`, after B2-F source merge and postmerge [#43227058578](https://github.com/hraaaaf/Digital_crown/actions/runs/43227058578) SUCCESS. Isolated branch `feat/lot08-3-b3-unconsumed-expired-qr-retention-lab-20261112`. All changes must remain DRAFT pending independent owner merge GO.

**Contract and safety proof target:**
- `queue_core/service/retention_expired_qr_08_3_b3_lab.py` accepts ONLY marked, tempdir synthetic Queue SQLite and a specific tenant with authenticated G2 QR schema, event immutable triggers, FK/integrity and UTC aware clock. Dry-run by default. `execute=True` uses BEGIN IMMEDIATE and 1–100 limited rows. Deletes only `consumed_epoch IS NULL AND expires_epoch <= now_epoch`, exactly matching the existing kiosk `redeem` rejection boundary `now >= expires_epoch`. No change to consumed QR retry grace (7 days, B2-A separate), no deletion of Queue event audit or visits, no other-tenant mutation. Append-only count-only G3 receipts have immutable UPDATE/DELETE guards. Fault after first DELETE rolls back the whole operation, including receipt/table DDL.
- `queue_core/service/backup_restore_clone_08_3_b2_lab.py` now rejects an encrypted snapshot containing any **expired or structurally invalid never-consumed QR** BEFORE publishing a clone, with `RESTORE_EXPIRED_UNCONSUMED_QR_DENIED`. New B3 aggregate receipt table is explicitly allowlisted and validated read-only for required triggers and schema, not automatically repaired. The existing B2-C/D/E/F encrypted restore chains transitively use the same B2-B fail-closed guard. A fresh encrypted archive after valid purge may restore only to a NEW synthetic SQLite clone; old snapshots must not resurrect expired unconsumed tokens.
- `queue_core/tests/test_retention_expired_qr_08_3_b3_lab.py` adds adversarial fixtures: just-before/at-exact-expiry boundary, two tenants, batch, dry-run, preservation of 7-day consumed receipt and event audit, crash rollback, receipt immutability and corrupt schema refusal, unsafe paths/time/input, no replay via stale Fernet archive, post-purge archive restore, and B2-C vault chain. Workflow `.github/workflows/v15-08-3-b2b-restore-clone-lab.yml` includes B3 in native Windows 2022 + Ubuntu 24.04 FUE.

**FUE / proof status at authoring:** NOT YET CERTIFIED on final candidate HEAD; require real complete native Actions/JUnit on Windows and Ubuntu, full Queue Core and CI scope, exact matching PR head before claiming PASS or merge. No physical test is in LOT08.3.

**Remaining software G3 criteria after B3 (NOT CLOSED by this candidate):** minimized audit retention/rotation at 12 months where applicable; real technical logs/ledgers 7-day management where tables exist; bounded software scheduling/orchestration and non-physical RPO/RTO lab fidelity, schema/upgrade edge cases, and a deliberate full LOT08.3 software closeout. No fabricated tables, no clinical restore, and no claim that B3 closes whole LOT08.3. LOT08.4 API, 08.5 UX and 08.6 resilience remain separate dependencies. See [Notion LOT08](https://app.notion.com/p/3ec77c66336281d59cdcffe610561f86?pvs=204).

## LOT08.3-B2-F — 2026-11-12 — IMMUTABLE OFFLINE CUSTODY HANDOFF (SYNTHETIC CANDIDATE; NOT PHYSICAL PROOF)

**Owner GO / Decision:** explicit 2026-11-12 after earlier HIGH effort disclosure. One bounded risk decision: avoid relying on a mutable B2-E sealed kit during the gap between kit overwrite and retention of the latest independent witness. Implement an isolated laboratory export that packages a VERIFIED immutable snapshot and returns a separate external descriptor digest for a custodian to retain. The success of the interface does NOT mean the fingerprint was stored on another physical device. No changes to B2-E production or app integration, no cabinet install, migration, real patient data or deployment.

**Pre-branch baseline:** latest confirmed master `4038ad11e5931bdf31162e582305c8639461e922` (unrelated LOT05.1 commit already integrated); branch `feat/lot08-3-b2f-custody-handoff-synthetic-lab-20261112`. Candidate PR to remain DRAFT until native FUE proof and owner separate merge GO.

**Protocol:** `queue_core/service/custody_handoff_08_3_b2f_lab.py` admits only tempdir-prefixed synthetic vault, sealed kit, and custody root disjoint from both inputs; verifies existing B2-E AES-GCM/Scrypt encrypted kit against caller-held latest SHA-256 witness, authenticates B2-C manifest/HMAC and every Fernet archive, refuses B2-D unresolved journals, unknown files and symlinks. Creates a RANDOM immutable generation-specific bundle with copied encrypted kit + manifest + archive ciphertext only, rechecks copied and original catalog, writes a canonical no-secret JSON descriptor containing generation, predecessor fingerprint and per-file hashes, then renames a verified pending folder to a published bundle. Returns the descriptor SHA-256 independently to the caller. Restore refuses a missing or incorrect **caller-supplied latest trusted external digest** before decryption or clone creation, checks canonical descriptor and each copied file, reauthenticates encrypted kit and B2-C catalog, delegates to the original B2-E/B2-B G3 clone gate for a NEW synthetic SQLite clone. B2-F never performs an implicit fallback to an older generation. Interruption before publication removes pending staging; neither an unsigned directory nor a previous fingerprint authorizes the new bundle.

**Risk boundaries / no false claims:** all test directories may reside on the SAME GitHub runner and disk, not independent physical media; no actual offsite escrow, TPM/DPAPI, immutable monotonic trust device, off-host acknowledged witness, human distribution, durable fsync of directory trees, true Windows device-loss/power-failure test, simultaneous rollback/compromised custodian defense or atomic cross-medium acknowledgement. A complete rollback of bundle PLUS externally held digest remains outside this model. The caller must guarantee that only the latest independently trusted external digest is used, and the app must not expose a route that bypasses this gate. Earlier authenticated snapshots cannot prove clinical RPO/RTO or full patient SQLCipher/media recovery. LOT08.3 OPEN, next physical custodian/media exercise is separate owner/human gate 🔴 HIGH.

**FUE / exact-HEAD evidence, first hardened candidate before final negative-test addition:** on `3287ca2daaa94a5ec8970ea056d4868b4e6ec976`, [real native Windows 2022 + Ubuntu 24.04 #43224072799](https://github.com/hraaaaf/Digital_crown/actions/runs/43224072799) COMPLETED SUCCESS, Ubuntu **97 PASS**, Windows **95 PASS / 2 SKIP** (POSIX permission-mode checks not applicable on Windows). JUnit artifacts: Ubuntu `13947650677`, Windows `13946439768`. [Full Queue Core #43224072791](https://github.com/hraaaaf/Digital_crown/actions/runs/43224072791) COMPLETED SUCCESS with **316 PASS / 3 SKIP / 4 subtests PASS**. Scope Gate #43224072750 SUCCESS. Source module uses POSIX explicit 0600 creation and rejects non-private custody root, but Windows ACL and physical media remain unverified. Two ADDITIONAL fail-closed negative tests (unfinished B2-D journal and source vault symlink) were added AFTER the above proven SHA; therefore all evidence MUST BE RECHECKED at the final updated PR HEAD before merge, no carried-over green claim. Current PR #1322 DRAFT / not merged; exact SHA and full workflow matrix must be read back.

## LOT08.3-B2-E — 2026-11-12 — POSTMERGE SOURCE/LAB VERIFIED (CURRENT READBACK)

**Decision / scope:** distinct owner "Go" for [PR #1314](https://github.com/hraaaaf/Digital_crown/pull/1314) authorized a **squash merge of the synthetic-only source and tests**, not a clinical restore, installation, patient migration or deployment. Candidate tested HEAD `37d96f266b1e0fd9d6d5e1506467472291522950`; historical base master `12dc65e8ee517897e76b7d2e37af58236c6b771f`. GitHub reports PR #1314 **CLOSED / MERGED / not draft** on 2026-11-12. [Squash master commit `6adf3e0ba07df057cf909ff0eace5a44387d0e36`](https://github.com/hraaaaf/Digital_crown/commit/6adf3e0ba07df057cf909ff0eace5a44387d0e36) was independently read back as exact master HEAD at the postmerge check.

**PROOF on candidate / merge:** all nine candidate workflows completed **8 SUCCESS, 1 SKIPPED M6-I out of scope, 0 FAILED / 0 ACTIVE**; [native Windows 2022 + Ubuntu 24.04 run #43201237861](https://github.com/hraaaaf/Digital_crown/actions/runs/43201237861) **79 PASS per OS**; [Queue Core #43201238025](https://github.com/hraaaaf/Digital_crown/actions/runs/43201238025) **298 PASS, 3 SKIP, 4 subtests PASS**; [Scope Gate #43201238041](https://github.com/hraaaaf/Digital_crown/actions/runs/43201238041) SUCCESS. Postmerge compare old master→squash commit **ahead 1, behind 0, four files only**: this `STATE.md`, `.github/workflows/v15-08-3-b2b-restore-clone-lab.yml`, `queue_core/service/recovery_kit_08_3_b2e_lab.py`, `queue_core/tests/test_recovery_kit_08_3_b2e_lab.py`. [Master push CI #43205609337](https://github.com/hraaaaf/Digital_crown/actions/runs/43205609337) **COMPLETED / SUCCESS** at exact squash SHA; both jobs **PostgreSQL 18 + immutable release invariants** and **Windows PowerShell 5.1 release guards** SUCCESS.

**Scope / residual risks:** B2-B, B2-C, B2-D and B2-E are merged within the bounded **synthetic SQLite encrypted vault / restoration clone LAB** scope. This is NOT proof of independent physical storage, lost-machine TPM/DPAPI key custody, off-host durable latest SHA witness, atomic kit/witness rollover, real power loss, authentic clinic SQLCipher and media restore, RPO/RTO, security/privacy compliance or clinical recovery. **LOT08.3 remains OPEN**; LOT08.4–08.6 deferred. No Vercel, installer, cabinet deployment, patient data, clinical restore, or migration.

**Next exact:** keep B2-E merged result and postmerge CI proof; this documentation-only addendum is a separate candidate pending its own PR merge gate. Next engineering decision **physical key/witness custody after loss of workstation** is **HIGH** and separately gated; define independent media, custody, recovery witness trust and fail-closed recovery under synthetic test before any cabinet integration. Canonical [Notion LOT08](https://app.notion.com/p/3ec77c66336281d59cdcffe610561f86?pvs=204). Earlier B2-E DRAFT content below is **historical premerge evidence**, not current status.

## LOT08.3-B2-E — 2026-11-12 — ENCRYPTED SEPARATELY WITNESSED RECOVERY KIT, SYNTHETIC ONLY (HISTORICAL PREMERGE)

**Owner GO:** explicit 2026-11-12 after HIGH effort warning for the next B2-E security scope (not a merge or clinical deployment GO). Exactly ONE decision: show loss of synthetic workstation source while retaining an encrypted Queue vault and separately handled recovery kit, then authenticate and restore only a NEW fake SQLite clone. Latest master baseline was `12dc65e8ee517897e76b7d2e37af58236c6b771f` after unrelated LOT05-2E merge; separate branch `feat/lot08-3-b2e-external-recovery-kit-lab-20261112`. No real patient data or cabinet media.

**Lab custody model:** NEW `queue_core/service/recovery_kit_08_3_b2e_lab.py` stores the Fernet Queue archive key, HMAC catalog key, exact latest catalog anchor, generation and clock ONLY inside a password-encrypted AES-256-GCM envelope (Scrypt derived from a synthetic high-entropy test passphrase; fresh random salt + nonce). The vault and the separate purpose-named kit folder both live in ephemeral system temporary directories for tests; same physical storage is possible and **NO offsite/TPM/DPAPI escrow is proven**. The API returns a SHA-256 witness fingerprint which MUST be retained independently by the caller outside BOTH vault and kit. Never put this external fingerprint inside either directory. SHA-256 witness detects stale/tampered kits only if the independently trusted LATEST witness was not rolled back itself. A password of 24 bytes is NOT proof of password entropy; the production secret and recovery procedure remain separate gates.

**Operations:** initial seal requires an existing authenticated B2-C clean nonempty vault manifest (journal B2-D cannot be pending) and both test keys; no overwrite. Updating an already sealed kit requires previous external fingerprint and previous passphrase, proves same archive/signing keys and strictly later catalog generation, and publishes an updated authenticated blob atomically within the same ephemeral directory. Crash between updating kit and independently preserving the new fingerprint is NOT solved atomically; fail-closed may render a valid archive unrecoverable. Restore takes only kit path, vault path, candidate clone path, passphrase, exact external witness, desired slot/date and clock: authenticate witness before password, decrypt in process without writing plaintext secrets, revalidate latest manifest and B2-C/B2-B G3 30-day closed visit and >7-day consumed QR anti-resurrection gates, and create only a NEW SQLite clone. No production runtime connections, no installer, no scheduler, no real secret storage. If a signed rotation journal is unresolved, restore is refused pending distinct B2-D recovery.

**FUE PROVEN on technical HEAD `95e31d03c21146ba93f9c56c0d283795a4b05b8d` (before this handover update):** [native real Windows 2022 + Ubuntu 24.04 #43200767523](https://github.com/hraaaaf/Digital_crown/actions/runs/43200767523) **79 PASS on each OS** (20 new B2-E adversarial cases + 59 previous Queue B2-B/C/D fixtures); JUnit [Windows #13934114690](https://github.com/hraaaaf/Digital_crown/actions/runs/43200767523/artifacts/13934114690) and [Ubuntu #13934249925](https://github.com/hraaaaf/Digital_crown/actions/runs/43200767523/artifacts/13934249925). [Full Queue Core Linux #43200767510](https://github.com/hraaaaf/Digital_crown/actions/runs/43200767510) **298 PASS / 3 SKIP / 4 subtests PASS**, [JUnit #13934578619](https://github.com/hraaaaf/Digital_crown/actions/runs/43200767510/artifacts/13934578619). [Scope Gate #43200768065](https://github.com/hraaaaf/Digital_crown/actions/runs/43200768065) SUCCESS. Tests prove encrypted on-disk AES-GCM envelope + Scrypt, raw key/anchor/passphrase absent from kit blob, only clone creation after copying kit and vault and deleting original synthetic Windows source, wrong passphrase, missing/wrong/stale SHA witness, altered AEAD tag even with attacker-recomputed fingerprint, wrong Fernet/HMAC key, stale catalog + stale recovery kit, signed but unresolved B2-D journal, destination collision, non-LAB path, interrupted key package publish preserving old ciphertext, and old weekly 30-day visit / 7-day consumed QR anti-resurrection. No tests disabled.

**History RED→GREEN:** initial native [#43200376280](https://github.com/hraaaaf/Digital_crown/actions/runs/43200376280) Ubuntu 77 PASS, Windows failed on a genuine Windows WinError32 when test removed fake source SQLite while its setup connection was still open. Corrected **fixture resource cleanup** by explicitly closing `sqlite3.Connection` after setting LAB marker (context manager commits but does not close); preserved loss-of-source scenario, no test relaxed. Added 2 more G3 QR/AEAD falsification negative tests, then native 79 PASS each OS. The documentary edit creates a NEW PR HEAD: **repeat exact-HEAD verification before declaring final CI completed.**

**Scope limits / risk gates:** no hard independent media, hardware-backed monotonic counter, physical escrow key vault, Windows ACL protection, DPAPI/TPM, secure human key distribution, machine loss with simultaneous loss of vault+kit+witness, online password cracking resistance against weak phrases, antirollback if vault+kit+witness collectively rolled back, bounded concurrency/Windows fsync and real power failure, real clinic SQLCipher/media restore, RPO<=1h/RTO<=2h evidence, or CNDP/09-08 approvals. All remain OPEN and HIGH effort. No production/clinical changes, migration, deployment, Vercel, or PR merge without separate owner GO.

**Historical candidate status (superseded by current readback above):** [PR #1314 DRAFT](https://github.com/hraaaaf/Digital_crown/pull/1314), OPEN, NO MERGE, NO DEPLOY. **Next exact:** check native 79/79 on both OS, Queue 298 PASS and all required GitHub workflows on the FINAL post-handover SHA, write Notion POST, then HOLD for distinct owner merge GO. Durable physical custody/atomic external witness rollover, actual Windows full-device restore, authentic SQLCipher/media/clinical data and RPO/RTO remain separate HIGH-risk gates.


## LOT08.3-B2-D — 2026-11-12 — AUTHENTICATED ROTATION INTERRUPT RECOVERY, SYNTHETIC LAB

**GO owner 2026-11-12** after B2-C merged, HIGH risk already surfaced. Single bounded decision: explicit **signed** recovery of a temp Queue encrypted 7D/4W backup rotation interrupted after journal preparation or after manifest commit, without silent deletion. Baseline `master@744ec07288bc9b36dfb5e7d4f7d1f0e395f919b1`. Branch `feat/lot08-3-b2d-journaled-recovery-lab-20261112`, PR DRAFT pending.

**BUG in B2-C prior state:** manifests are atomically replaced before retirement of previous ciphertexts. If interrupted post-commit, those old files become orphaned (correctly fail-closed), but there is no safe reconciliation. The opposite gap is newly sealed archives awaiting manifest commit. The external anchor handed back to the caller after successful rotation is also not automatically adopted on interrupted commits. Existing source refused unknown orphan data; B2-D must preserve that security property.

**Protocol:** `queue_core/service/backup_rotation_08_3_b2c_lab.py` signs a HMAC-SHA256 **transaction journal** with a distinct manifest key, binding complete pre- and post- catalog anchors, generations, predecessor latest UTC epoch, execution clock and exact new and retired archive names/digests. Journal is written and fsynced before publishing manifest; previous fault-injection hook remains before intent publication. If interrupted after signing, ordinary rotate and restore remain **BLOCKED** until explicit recovery. New `queue_core/service/backup_rotation_recovery_08_3_b2d_lab.py` requires latest caller-held anchor (separate from vault), checks HMAC journal, valid Queue/Fernet manifest, source/next anchors rederived from exact entry sets, every unchanged/new archive digest, and the 7/4 calendar retirement plan. **Before commit:** delete only signed *new* files, retain old manifest and all old archives; **after commit:** delete only signed *retired* archives, return authenticated next anchor for independent custody; missing files listed in the authenticated intent support retry after partial cleanup. Unlisted/orphan, symlink, modified bytes or wrong keys/anchor fail closed. No guesswork or unrestricted delete. Only synthetic temp vault/SQLite and encrypted ciphertext.

**FUE PROVEN on source/test SHA `20cb6c7c2fdc238d60d856f877ae7299edb6cded` (before this documentary update):** [native Windows+Ubuntu #43194394379](https://github.com/hraaaaf/Digital_crown/actions/runs/43194394379) **59 PASS on each OS** (15 new B2-D crash/recovery security tests + 44 B2-C/B2-B regressions); JUnit [Windows #13932621048](https://github.com/hraaaaf/Digital_crown/actions/runs/43194394379/artifacts/13932621048) and [Ubuntu #13932456607](https://github.com/hraaaaf/Digital_crown/actions/runs/43194394379/artifacts/13932456607). [Full Queue Core Linux #43194394446](https://github.com/hraaaaf/Digital_crown/actions/runs/43194394446) **278 PASS / 3 SKIP / 4 subtests PASS**, [JUnit #13931962901](https://github.com/hraaaaf/Digital_crown/actions/runs/43194394446/artifacts/13931962901). [Scope Gate #43194394334](https://github.com/hraaaaf/Digital_crown/actions/runs/43194394334) SUCCESS. Native fake SQLite tests exercise signed pre/post journal, safe rollback before commit, safe finalization after commit, partial ciphertext retirement, corrupted journal/ciphertext, wrong caller anchor/key, unknown orphan, clock/scope guards, and a recovered real clone; no test was disabled. Remaining LOT07 visual/browser checks were still active as of the source SHA read. **This STATE.md-only update changes PR HEAD; re-verify exact final commit checks before claiming full CI closure.**

**HUMAN HOLD / not proven:** physical independent media, Windows secret/anchor external durability, interprocess locking & race safety, actual crash/power-loss fsync/atomicity across independent devices, backup installer/scheduler, old offsite copies cleanup, SQLCipher/media real cabinet recovery, CNDP/09-08, measured RPO ≤1 h / RTO ≤2 h. No app runtime integration or actual patient files, Vercel deployment, migration or merge without distinct GO.

**Current:** [DRAFT PR #1313](https://github.com/hraaaaf/Digital_crown/pull/1313), no merge/no deploy. **Next exact:** all GitHub checks on exact updated SHA (native 59/59 on each OS and Queue 278 PASS), inspect artifacts, update Notion POST, then STOP before merge pending a distinct explicit owner GO. Physical power-loss resilience and durable Windows anchor custody are still unmet HIGH-effort gates.


## LOT08.3-B2-C — 2026-11-12 — SYNTHETIC 7 DAILY + 4 WEEKLY SEALED VAULT (DRAFT, NO DEPLOY)

**Owner GO:** 2026-11-12 after HIGH effort notification; one decision, source + GitHub Actions synthetic LAB only, separate merge gate. Initial master exactly `ac3d2a74ddfd5f27d112fc136b3aff09ba401e67`. Branch `feat/lot08-3-b2c-rotating-7d4w-synthetic-vault-20261112`. No changes to clinical runtime, key store, scheduler, patient data, migrations, real cabinet, or Vercel.

**Goal:** use the already-merged 08.3-B2-B sealed SQLite synthetic snapshot and restore-clone functions, simulate a bounded offline vault with at most 7 UTC daily calendar buckets and 4 ISO-week buckets. New archives must be genuinely encrypted/authenticated Fernet and validated via a disposable restored clone **before** publishing a new authenticated manifest. Overage is deleted **only after** new manifest publication, never before an authenticated successor. Do not fabricate slots on missed days. Test over month/year boundaries and non-running periods. No automatic scheduling is activated.

**Threat model and anti-rollback boundary:** HMAC-SHA256 manifest catalog with a dedicated 32-byte signing key separate from the Fernet archive key, plus the **latest manifest anchor held independently by the caller** (not saved to the vault). Every rotation and restore requires the exact external latest anchor. Stale or modified manifest, missing/extra/tampered ciphertext, unexpected archive path, non-LAB source, clock regression, wrong key, old G3 visit/QR records and overwrite all fail closed. An archive from before a justified purge must not restore a 30-day-overdue closed visit or consumed expired QR >7 days. Only publish a **new temp clone**, never overwrite an active database. The prototype cannot protect a caller that loses/rolls back its external anchor, nor resist a privileged attacker with both keys and anchor. Primary/backup directories on GitHub runners DO NOT prove independent physical media.

**FUE PROVEN on source/test SHA `ebf5fd6ce954c1fa9e5aedca53dec10b0ae3ada5` (before this documentary update):** [native Windows+Ubuntu #43187697490](https://github.com/hraaaaf/Digital_crown/actions/runs/43187697490) **44 PASS each OS** (15 new B2-C oracles + 29 B2-B/B2-A/B1 regressions); JUnit [Windows #13929012273](https://github.com/hraaaaf/Digital_crown/actions/runs/43187697490/artifacts/13929012273) and [Ubuntu #13928463207](https://github.com/hraaaaf/Digital_crown/actions/runs/43187697490/artifacts/13928463207). [Full Queue Linux #43187697745](https://github.com/hraaaaf/Digital_crown/actions/runs/43187697745): **263 PASS, 3 SKIP, 4 subtests PASS**, [JUnit #13928857518](https://github.com/hraaaaf/Digital_crown/actions/runs/43187697745/artifacts/13928857518). [CI Scope Gate #43187697731](https://github.com/hraaaaf/Digital_crown/actions/runs/43187697731): SUCCESS. At this point 2 unrelated LOT07 visual/browser workflows are still running, and merged/prerelease status must not be overstated. **This STATE.md edit changes PR HEAD, so evidence on the NEW exact HEAD must be reread before claiming final CI completion.**

**Real negative-oracle coverage:** 43-day sequence with at most 7 daily calendar + 4 weekly ISO buckets, no stale daily after 44-day scheduler outage on next rotation, reject restoring stale daily or weekly even BEFORE the next rotation, ISO week rollover, immutable audit, scoped synthetic SQLite marker, separate Fernet/HMAC keys and consistent backup key across generations, ciphertext/manifest corruption, missing/orphan archives, stale external anchor and manifest rollback, duplicate daily slot, injected crash before manifest publication with full cleanup, cross-tenant restoration, old weekly QR receipt after verified 7-day purge, and old weekly visit after verified 30-day purge; old snapshots refused without exposing new clinic database.

**History RED→GREEN:** initial Queue run [#43186163809](https://github.com/hraaaaf/Digital_crown/actions/runs/43186163809) failed on an invalid synthetic Queue event type `CHECK_IN`, corrected to `WAITING_ENTERED` with method `STAFF` (real schema guard preserved). New workflow file did not register on the draft PR, so CI was incorporated into the proven existing two-OS B2-B workflow; redundant new workflow deleted from PR. After addition of calendar age restriction, an old test expecting `RESTORE_OVERDUE_VISIT_DENIED` for a daily archive aged 29 days failed [#43187471403](https://github.com/hraaaaf/Digital_crown/actions/runs/43187471403) as it was already properly rejected earlier by `ROTATION_ARCHIVE_OUTSIDE_RETENTION_DENIED`. Test now exercises a still-retained weekly snapshot and requires the actual `RESTORE_OVERDUE_VISIT_DENIED` guard; both guards remain active. No test disabled, ignored or marked xfail.

**Still open / human gate:** daily/weekly backed-up data on genuinely independent physical supports, Windows protected recovery keys, durable external rollback anchor custody, interrupted multi-file rotation/recovery semantics, archival policy over outages, legal CNDP/09-08 review, genuine SQLCipher/media restore, measured RPO <=1h and RTO <=2h. Both are *targets*, not certified. No patient data, real restore, installable activation, deployment, destructive clinical purge or merge without separate owner authorization.

**Current PR:** [#1309 DRAFT](https://github.com/hraaaaf/Digital_crown/pull/1309), head after this handover update requires new check. **Next:** verify exact HEAD two OS + full Queue + 2 remaining LOT07 runs and no failures, record Notion POST, keep DRAFT and STOP before merge pending separate explicit owner GO. The full G3 7+4 production-ready goal is NOT claimed; physical media separation, robust interrupted multi-file rotation recovery, windows key custody, RPO/RTO and legal gates remain OPEN.


## LOT08.3-B2-B — 2026-11-11 — ENCRYPTED SYNTHETIC QUEUE RESTORE CLONE (NO INSTALLABLE)

**User GO:** 2026-11-11 after 08.3-B2-A merged, risk/effort HIGH explicitly announced. One bounded decision: prove encrypted online SQLite Queue snapshot, authenticated decrypt, and **create-only restore CLONE** against fake Queue LAB. Master baseline `ca533b7d04432b85553cf97e18df216cceb85a38`, separate draft branch `feat/lot08-3-b2b-encrypted-restore-clone-lab-20261111`.

**Scope:** NEW `queue_core/service/backup_restore_clone_08_3_b2_lab.py`, `queue_core/tests/test_backup_restore_clone_08_3_b2_lab.py`, native 2-OS workflow `.github/workflows/v15-08-3-b2b-restore-clone-lab.yml`, and this handover ONLY. No changes to actual clinical backend, existing `backend/services/backup_service.py`, Queue HTTP/authorized services, installer, scheduling, or real cabinet. The actual LOT05 SQLCipher/Guided Restore already has separate runbooks/tests; this Queue clone lab is **not** that product or a validation of its real-key/SQLCipher/media restoration.

**Security oracles:** only system-temp, `lot08_3_b_lab_*.sqlite` source with explicit `application_id=LOT8`, immutable event triggers and FK/integrity, allowlisted Queue tables only, exact QR schema if present, no patient/clinical tables. Read-only source + native SQLite online backup (committed WAL included) into in-memory image; Fernet authenticated encryption with caller-generated **separate test key**, no plaintext source on backup medium, no overwrite of existing archive. Restore authenticates ciphertext, verifies authenticated created time/size/digest, memory-deserializes and revalidates schema; **refuses** if *any* tenant has closed visits eligible for 30-day purge or consumed QR retry receipts strictly over 7 days and expired. It DOES NOT silently purge/replay or rewrite append-only audit. Only after gates: stage a *new* clone in the isolated temp directory, verify then create-only publish with hard-link; no replacement of existing target. Injection failure cleans stage and leaves original source untouched. No active DB publication.

**FUE / proofs on candidate code SHA `9f2e8e008df12b46df84c3972e6d531d72067751` (before this documentary handover update):** actual Windows 2022 and Ubuntu native SQLite/cryptography [native FUE #43069973594](https://github.com/hraaaaf/Digital_crown/actions/runs/43069973594) **29 passed on each OS** (12 B2-B + 9 B2-A + 8 B1); [Queue Linux #43069973798](https://github.com/hraaaaf/Digital_crown/actions/runs/43069973798) **248 passed / 3 skipped / 4 subtests passed**; [Scope gate #43069973732](https://github.com/hraaaaf/Digital_crown/actions/runs/43069973732) SUCCESS. JUnit native Windows [artifact #13877745845](https://github.com/hraaaaf/Digital_crown/actions/runs/43069562229/artifacts/13877745845) and Ubuntu [artifact #13876573649](https://github.com/hraaaaf/Digital_crown/actions/runs/43069562229/artifacts/13876573649) are from earlier functional code SHA `edb1e304dc9d2a5ce20e5c15d7837523f2f4ff01`; the new `9f2e8e0` native run also succeeded. Queue full failed once because its 3.11 minimal dependency list omitted `cryptography` (unmodified code), fixed by explicitly pinning `cryptography==49.0.0` in `.github/workflows/v15-08-1-queue-domain-fue0.yml`; no skip, full rerun PASS. Native WAL test originally failed on BOTH OS because a native SQLite backup of a WAL database retained a WAL-mode file header that cannot be deserialized alone. Fixed safely via `VACUUM` **on the in-memory clone only**, then actual SQLite deserialize/clone FUE GREEN. The original source file remains untouched. Prior red artifacts are historical, not green.

**Tested negative oracles:** real committed WAL snapshot, verified cloned tenants and immutable audit, both overdue retention deadlines on all tenants, backup after verified purge restores without resurrecting, wrong encryption key and ciphertext tamper, missing event guard/unexpected clinical table, ordinary file and invalid SQLite synthetic marker, archive/destination collision without overwrite, injected failure cleans transient clone without any destination, future timestamp and naive clock denied. Actual clone may be formed only after SQLite integrity/retention guards. No test was removed or marked xfail.

**New SHA after this STATE.md update requires fresh check on final exact HEAD before claiming CI-complete or mergeable-ready; keep DRAFT.**

**Critical unsatisfied gates:** 7 daily + 4 weekly encrypted backups on independent media with separated recovery keys, old-backup garbage collection and anti-rollback across offsite copies, physical crash/power-off and multi-component DB/media snapshots, RPO <=1 h/RTO <=2 h measured, legal CNDP/09-08 approval, actual installable and real patient data. Restore clone cannot become active cabinet DB. **NO_DEPLOY / NO_MERGE without new owner GO**. 08.3 global remains OPEN, 08.4–08.6 deferred.

**Next exact:** draft PR, exact-head Win+Linux real tests, negative-oracle review, Notion POST and distinct owner merge gate. 


## LOT08.3-B2-A — 2026-11-11 — 7-DAY CONSUMED QR RETRY RECEIPT RETENTION, SYNTHETIC LAB ONLY

**Decision:** owner « Go » after #1301 integrated. One 08.3-B2 subdecision only: the **existing** synthetic QR receipt ledger `queue_presence_qr_lab` from LOT08.2-D, not imaginary generic webhook/log tables or legal-audit purge. Master baseline `8a9db931d153f7d20edc5d6ea70faab2f12feee3`. [Draft PR #1303](https://github.com/hraaaaf/Digital_crown/pull/1303), branch `feat/v15-08-3-b2-qr-ledger-retention-lab-20261111`.

**G3 threshold invariant:** Queue QR redeem permits retries for exactly 7 elapsed days (`now <= consumed_epoch + 7*86400`), therefore cleanup must retain the QR receipt at the exact boundary and only purge **strictly later**, when expiry is past and the original transaction was fully consumed. Do not delete pending/unconsumed receipts or the event audit. Query by tenant and eligible age, batch max 100, default dry-run; temporary-path AND explicit SQLite synthetic marker; SQLite event UPDATE/DELETE guards, foreign-key integrity and exact QR columns required. Immutable aggregate retention receipt only after successful atomic commit, rollback on exception; zero-match run nonmutating.

**FUE proof (candidate before canonical change):** original negative Windows run [#43059196552](https://github.com/hraaaaf/Digital_crown/actions/runs/43059196552) FAILED on an accidental Python newline serialization error: NameError `cutoff` before any purge. Fixed without removing tests. Latest substantive code/test SHA `804be45bfa137d58e4b5bdacfd8bad0dd3610cde`: [Windows #43059391283](https://github.com/hraaaaf/Digital_crown/actions/runs/43059391283) **15 passed** (7 QR new + 8 B1 regression), JUnit [#13873036685](https://github.com/hraaaaf/Digital_crown/actions/runs/43059391283/artifacts/13873036685). Linux Queue full workflow [#43059391699](https://github.com/hraaaaf/Digital_crown/actions/runs/43059391699) pending at documentation time; do not assert completion without a final readback. Subsequent hardening adds two negative cases against preexisting mutable or schema-incompatible QR purge receipts (9 B2 tests). Final PR candidate SHA after this handover and hardening requires revalidation and exact-head traceability.

**Limitations:** prototype source/LAB, no runtime background scheduler, no clinic installable, no real patient file, no migration or production purge. Technical logs/webhook deliveries seven days have no identified Queue tables in examined code, unconsumed expired QR token verifier cleanup is separately gated under G2, append-only audit 12 months and backup/restore with RPO/RTO remain **NOT IMPLEMENTED**. Strict 7d TTL on consumed retry receipts does not imply all G3 lifecycle goals complete. Old audit identifier `visit_ref` minimization/legal review still required.

**Next exact:** verify final PR head Linux Queue + native Windows + scope gate, inspect negative oracles and JUnit, Notion POST, leave PR DRAFT until distinct merge GO. Begin a separate G3 backup/restore decision only after this sublot closes.


## LOT08.3-A/B1 — 2026-11-11 — VERIFIED INTEGRATION CANDIDATE (LAB ONLY)

**Owner GO** (2026-11-11): reconcile tested Queue retention LAB against latest master, rerun applicable FUE and merge if green, never deploy/install/migrate real DBs. **Baseline** `master@5a51be7483b661c95852c5a3a53109c9c2bf9f15` (two intervening design documentation commits #1296/#1298 after #1294; no Queue files changed).

**08.3-A merged**: [#1294](https://github.com/hraaaaf/Digital_crown/pull/1294) squash at `2e52e63b8142614fe5a4fa38582f69dd8aa8410b`, SQLite event UPDATE/DELETE denied on fresh LAB files and old unguarded SQLite rejected (not OS/DDL tamper-proof); [Linux FUE 219 passed](https://github.com/hraaaaf/Digital_crown/actions/runs/43024876988), [Windows 3 passed](https://github.com/hraaaaf/Digital_crown/actions/runs/43024877122).

**08.3-B1:** [Original #1297](https://github.com/hraaaaf/Digital_crown/pull/1297) candidate `47b6028da0231df56e10aae73aa4bc7d54a02ef8` passed [Queue 227 PASS/3 SKIP/4 subtests](https://github.com/hraaaaf/Digital_crown/actions/runs/43027852470) and [Windows 8 PASS](https://github.com/hraaaaf/Digital_crown/actions/runs/43027852099), all 9 PR CI (8 success, 1 irrelevant skipped). Reconciliation branch `integrate/v15-08-3-b1-retention-rebase-20261111` forks latest master and carries exact content blobs of original 3 LAB module/test/workflow files; adds this canonical checkpoint only. **Requires new exact-head CI** before controlled merge. Original draft to be superseded/closed only after successful verified merge.

**Boundary:** synthetic temporary `lot08_3_b_lab_*.sqlite` with explicit SQLite LAB marker; dry-run by default, at most 100 tenant-authorized eligible DONE/CANCELLED/NO_SHOW visits after 30 days, rollback on injected fault, no QR orphan, SQLite/FK integrity checks; externally linked references and resource bindings cascaded, 12-month append-only event history preserved, aggregate immutable LAB receipt. No clinic DB, installer, migration, release or real data. 08.3-B2 / 7-day ledger and logs, 12-month audit rotation, secure backups (7 daily/4 weekly), RPO<=1h/RTO<=2h restore, legal CNDP and cabinet safety gates remain **OPEN**. No PRODUCT CLOSEOUT.

**Next exact:** verify reconciliation branch diff and final GitHub Queue/Windows FUE, merge only if ALL applicable gates green; read back final master, update Notion, close superseded #1297 without deleting historical proof. `NO_INSTALLABLE_GO`, `NO_DEPLOY`.


## LOT08.2-D/E/F/G — INTEGRATED SOURCE/LAB MERGED, PRODUCT INSTALLABLE HOLD — 2026-11-11

- **GO:** utilisateur « Go » le 11/11/2026 pour intégrer les PR 08.2, exécuter la FUE, fusion contrôlée ; aucune permission de déployer ni d'installer en cabinet.
- **Master verified after squash merge:** `d89dd77831970b3c1ba23c95e7e12884b47afd47`, [PR #1292 merged](https://github.com/hraaaaf/Digital_crown/pull/1292). Candidate source head `0c5ae67e33ab3eec614bdfbd3921714adf273f85` on former master `093e89390d0e4b934d478485ea1ef28a7ce95de4`. 17 changed paths = 16 LAB added + 1 QR regression test modified; 0 patient/clinical runtime changes.
- **FUE exact candidate head:** [Queue #43018994172](https://github.com/hraaaaf/Digital_crown/actions/runs/43018994172) **216 passed / 3 skipped / 4 subtests passed**; [Windows E #43018994438](https://github.com/hraaaaf/Digital_crown/actions/runs/43018994438) 2/2 SUCCESS; [Windows F #43018994111](https://github.com/hraaaaf/Digital_crown/actions/runs/43018994111) 2/2 SUCCESS; [native SQLCipher and Windows G #43018994567](https://github.com/hraaaaf/Digital_crown/actions/runs/43018994567) 3/3 SUCCESS; [Scope #43018994142](https://github.com/hraaaaf/Digital_crown/actions/runs/43018994142) SUCCESS. Final 11 PR-triggered workflows = 10 SUCCESS + 1 biometric SKIPPED, 0 FAILED/ACTIVE. Two initial E/G CI source-gate failures were repaired by exact 17-file allowlist, not by disabling security tests.
- **Master postmerge SHA verified** by connector. The available workflow-run lookup filters PR-triggered runs; a master push postmerge run has **not yet been independently proven**. Do not relabel the candidate tests as a master build certificate.
- **Verdict:** LOT08.2 identity/RBAC/pairing/QR and Windows LAB safety regression **source-integrated & synthetic FUE proven**. **PRODUCT/INSTALLABLE CLOSEOUT HOLD** until authentic INSTALLABLE_CERTIFIED on current exact master and Windows installed FUE-G (real EXE, QR/surfaces where in scope). No cabinet install, clinic activation, human-facing patient data, migration, deploy or Vercel. 08.3–08.6 remain OPEN.
- **Canonical detail:** [V15_08_2_CLOSEOUT_GATE_20261111.md](docs/v1.5/V15_08_2_CLOSEOUT_GATE_20261111.md), Notion [V1.5-08](https://app.notion.com/p/3ec77c66336281d59cdcffe610561f86).
- **NEXT EXACT:** finish doc closeout PR #1289; preserve history while closing superseded DRAFT PR #1273/#1274/#1275/#1287 only after validating master coverage, then start LOT08.3 Queue engine as distinct decision. No actual installable proof may be inferred from the lab's negative release checks.


## LOT08.2-B / B-7d — RED CONFLICTS RECONCILED / LAB FUE-I PASS — 2026-11-09

- **Décision autorisée** : utilisateur « Go then », tests frontend B-7d sur le merge simulé et, après preuves de sécurité, réconciliation contrôlée de la **branche PR DRAFT #1239 uniquement**. Ne jamais merger la PR vers master, installer, créer une release, utiliser de vrais dossiers patient ou approuver automatiquement le visuel.
- **SOURCE** : branche `feat/v15-08-2-b-rbac-isolation-20261109` HEAD avant lot `c6954e6ec0c775c245754840ad532e6ed147640e`, master actuel confirmé `d4d2d144393fc884e01ca8734c1efa9fb0e0f2e3` (master antérieur `edbc24ed...` avait avancé de six commits LOT05 sans chevauchement des cinq conflits). Exact **5 fichiers / 6 blocs** résolus dans worktree Git détaché sans modification de master, conservant tests de provenance/identité patient, tests blob/PDF authentifié, audit AST et garde Hub Windows, gouvernance FUE. Hash SHA256 des cinq résolutions identique entre simulations master anciennes et actuelles, 0 unmerged, git diff --cached --check PASS.
- **FUE frontend** : 5 suites chacune dans un processus indépendant avec **1 worker**, toutes **exit 0** : audit ClientFacingCopy 13/13, Documents M4-C 6/6, Hub 8/8, PrescriptionForm 7/7, PatientDraft 8/8 ; total **42/42 PASS**, zéro erreur worker. L'ancienne exécution combinée 42 assertions mais erreur onTaskUpdate/exit1 reste RED dans l'historique.
- **FUE backend** : Céphalo/Ortho **15/15 PASS / exit0** sur le merge précédent, contenus des cinq fichiers conflictuels inchangés après intégration master d4d2 ; aucune donnée patient réelle. Premier essai Queue Core sur l'arbre actuel **124 PASS / 3 FAIL / exit1** dû exclusivement au checkout sparse omettant le fichier Git suivi `installer/DigitalCrown.iss`. Après `git sparse-checkout add installer`, préflight **5/5 PASS / exit0** ; puis **régression complète Queue Core 127/127 PASS / exit0 / 158,86 s**, sur le même arbre fusionné. Les trois échecs initiaux restent conservés dans l'historique, mais le run complet final est maintenant réellement vert.
- **TypeScript final** : `tsc --noEmit -p tsconfig.app.json` **PASS / exit0** sur le master d4d2 fusionné, machine Windows 8 Go. Dossier de preuve [B-7d](docs/v1.5/V15_08_2_B_B7D_CONFLICT_RECONCILIATION_20261109.md) et manifeste 5 logs SHA-256 `docs/v1.5/evidence/lot08_2_b7d_master_conflict_sequential_20261109.json`, logs bruts hors dépôt.
- **GATES** : certification `CODE_CERTIFIED` master et `INSTALLABLE_CERTIFIED`, migration `/appointments`, tests Windows natifs installés/LOT10 physique **NOT_RUN / NOT_AUTHORIZED** ; B-6 `NO_INSTALLABLE_GO` demeure. [UI Human Visual Approval](https://github.com/hraaaaf/Digital_crown/actions/runs/42697010891) rouge attendu après changement HEAD et requiert de nouvelles preuves/screenshots et approbation **explicite** par propriétaire GitHub.
- **NEXT exact** : commit de réconciliation dans worktree isolé en respectant parent SHA exact, push uniquement vers branche DRAFT après vérification des références distantes, puis recontrôler PR/CI et documenter Notion. Aucune fusion vers master autorisée.



## LOT08.2-B / B-7c — 2026-11-09 — 388/388 FRONTEND FILES / 2035 TESTS WINDOWS SHARDED PASS · CI NOT VERIFIED

- **Décision GO utilisateur :** finir les lots 7–9 de Vitest Windows sous contrainte de 8 Go RAM, revalider les preuves machine et vérifier la CI GitHub du HEAD exact `66c2f3d4fb0efc6fa5d99a2d15211a5b02c4203f`. PR #1239 OPEN/DRAFT/NON MERGÉE, branch `feat/v15-08-2-b-rbac-isolation-20261109`, base master `324afd13487acf7ff29223f077451927b54b8178`.
- **RÉSULTAT OBSERVÉ (exhaustif sous plan de tests sharded)** : `frontend/src` contient **388 fichiers de tests**, répartis en **9 exécutions Vitest** de 48/48/48/48/48/48/48/48/4 fichiers, avec au maximum **2 workers**. **9/9 shards EXIT 0**, **388/388 fichiers PASS**, **2 035/2 035 tests PASS**, aucun FAIL dans les neuf groupes. Détail par shard : `271 + 264 + 215 + 263 + 274 + 237 + 268 + 224 + 19 = 2035`. Contrôle indépendant des neuf logs `ALL_VERIFIED=True FILES=388 TESTS=2035` / exit 0 ; par shard test/file count exact et SHA-256 des journaux enregistrés.
- **PREUVE CANONIQUE** : `docs/v1.5/evidence/lot08_2_b7c_windows_vitest_shards_20261109.json`, 9 empreintes SHA-256 de logs bruts non commités restant sur le PC de test `DigitalCrown-B7C-Shard-Evidence` ; rapport `docs/v1.5/V15_08_2_B_B7C_PRESCRIPTION_TIMEOUT_STABILITY_20261109.md`. Le code testé est le SHA `66c2f3d` avant commit documentaire. **Les exécutions Vitest globales non plafonnées antérieures restent RED**, ce PASS est une **validation exhaustive découpée**, pas un PASS d'un `npm test` monolithique.
- **Frontières** : tests ciblés B-7c plus anciens 34/34 PASS ; prescription plus forte (quatre presets, label, payload et ordre) et audit des libellés exhaustif par 48 sources, garde-brouillon patient intact. Aucune mutation de code clinique, patients, documents réels, installateur ou migration.
- **CI/GITHUB** : connecteur GitHub `fetch_commit_workflow_runs` limité à la première page des runs `pull_request` a retourné **0** ; un GET **public en lecture seule avec filtre exact `head_sha=66c2f3d`** a vérifié **1 run réel** : [UI Human Visual Approval #42686757746](https://github.com/hraaaaf/Digital_crown/actions/runs/42686757746), évènement `pull_request_target`, **FAILURE attendu** car `PR HEAD changed: approval revoked; new screenshots and explicit approval required`. Ce run ne prouve **aucune** CI Queue Core / Scope / CODE_CERT candidate au SHA testé ; elles restent **NON VÉRIFIÉES**. La PR est **mergeable_state=dirty** (conflits contre master) au contrôle public. Le CLI `gh` local est non authentifié, sans accès de dispatch CI. **Ne jamais contourner la gate visuelle humaine**. Politique `SOURCE_GATE_PRESENT_NO_INSTALLABLE_GO` : tests natifs installés, `CODE_CERTIFIED` exact master, assets certifiés, LOT10 physique, vrai `/appointments` et humains **NOT_RUN/NOT_AUTHORIZED**.
- **BUILD + MÉNAGE** : `tsc --noEmit -p tsconfig.app.json` **PASS**, `npm run build:test` **PASS**, Vite PWA créé sous `dist-test`, manifeste `environment=test`, `commit=66c2f3d`, `mode=test`, **exit 0** ; jamais de build cabinet. La sortie de test `audit/out/frontend.json` et `frontend/dist-test` ont été vérifiées synthétiques puis supprimées ; seuls les logs de preuve externes au dépôt sont conservés.
- **NEXT EXACT** : committer rapport + manifeste dans PR DRAFT, vérifier nouveau HEAD et GitHub CI avec accès paginé, puis traiter les conflits `mergeable_state=dirty` et renouveler la preuve/approbation visuelle via décision séparée. Aucune fusion ou installation pour forcer un workflow.



## LOT08.2-B / B-7c — REAL PRESCRIPTION TEST TIMEOUT & EXHAUSTIVE AUDIT BATCHING — 2026-11-09

- **User GO:** continue the exact last RED: full frontend Vitest 2022 PASS / 1 FAIL (test-only PrescriptionForm quick-preset **5000ms timeout**), not a proven clinical prescription bug. PR #1239 DRAFT, starting SHA `82248e25c9eecc12c4b63052d40a9aee1c22a6f1`, no merge/install/deploy/clinical migration.
- **Oracle repair, NO clinical production code changes:** `frontend/src/features/admin/DocumentStudio/PrescriptionForm.g4Interactive.test.tsx` checks all four quick-preset names, order, payload drug name and exact 4 calls to `onApplyPreset`, with explicit 20s load budget. BEFORE the same isolated unchanged PrescriptionForm file passed **7/7**, actual test time **2.77s**; the RED was runner timeout only, not a callback assertion.
- **Second load failure discovered:** monolithic AST `ClientFacingCopyCandidateAudit.test.ts` timed out even at 20s during a four-suite focused run. Converted to exhaustive **48-file** source batches using identical source discovery filter, same per-file AST/technical-copy rules; new positive source count/unique/flatten coverage assertion, no exclusions and no weaker language scanning.
- **FUE-I Windows focused actual:** the four sensitive suites (copy audit, PrescriptionForm, patient draft-guard, M4-C documents) **34/34 PASS** across **4/4 files**, process exit 0; previous patient draft active-identity+empty editor test retained. Further TypeScript and full default frontend Vitest run currently in progress. `frontend/src/ClientFacingCopyCandidateAudit.test.ts`, `frontend/src/features/patients/PatientDraftRouteGuard.test.tsx` were previously local-uncommitted at `82248e2`.
- **Clinical safety boundaries:** no actual medication instructions altered, no prescribing algorithm clinically certified, no real patient data. `CODE_CERTIFIED`, `INSTALLABLE_CERTIFIED`, physical LOT10 and real `/appointments` migration **NOT_RUN/NOT_AUTHORIZED**; LOT08.2-B OPEN. Repro/report `docs/v1.5/V15_08_2_B_B7C_PRESCRIPTION_TIMEOUT_STABILITY_20261109.md`.
- **NEXT EXACT:** read full Vitest/TypeScript verdict; fix proven residual failures without dropping tests, compile/build if relevant, push safe verified changes only to DRAFT PR #1239, verify GitHub exact HEAD workflows and Notion. GitHub CLI local PC is not authenticated, so do not invent run IDs or CI state.



## LOT08.2-B / B-7 — RED / 3 FAILED CODE_CERT CANDIDATE ASSERTIONS — 2026-11-09

- **Décision :** GO « Red » : traiter les **trois échecs** du workflow GitHub candidat `Cabinet CODE_CERTIFIED candidate regression (no package)` [#42644548911](https://github.com/hraaaaf/Digital_crown/actions/runs/42644548911) au HEAD `c64d9e94077fb63bb6c37e3b80cf24d477dab3dc`. PR #1239 `feat/v15-08-2-b-rbac-isolation-20261109` OPEN/DRAFT/non mergée. Ne pas fusionner, déployer, créer d'installable ni migrer des patients.
- **CAUSE PROUVÉE logs :** frontend Vitest **2022 PASSED/1 FAILED** sur signature `handleView(doc.id)` qui ne correspond plus à l'appel réel sécurisé `handleView(doc.id, doc.name)`. Backend **5918 PASSED/2 FAILED/30 SKIPPED** : `test_cephalo_v1_l3_a4_document` simule un média sans `patient_id`, T0, provenance/date conformes et se heurte au **refus sécuritaire légitime** du lecteur ; `test_ortho_frontend_fail_closed_contract` exige un avertissement clinique littéral manquant dans le composant PDF Step4. Contrôle PostgreSQL/JWT candidat indépendant SUCCESS.
- **CHANGEMENTS MINIMAUX :** mise à jour de l'assertion frontend vers la vraie signature à deux arguments, renforcée par assertions du rattachement patient du blob ; correction de la fixture positive Céphalo avec T0 / patient 42 / upload / slot / version / date réels, **trois nouveaux cas négatifs** patient étranger, mauvais timepoint et image sans provenance pour vérifier l'absence de lecture des bytes ; ajout de l'avertissement clinique visible près des actions PDF dans Step4. Aucun garde de sécurité de production retiré ; le lecteur Céphalo et le module patient Documents restent inchangés.
- **Preuves locales initiales :** process isolé `ENVIRONMENT=test`, `sqlite:///:memory:` avec données fictives ; tests backend Céphalo+Ortho **14/14 PASS**, Vitest M4-C **6/6 PASS**. Premier **Vitest complet Windows 2019 PASS / 3 FAIL + 1 suite en erreur**, isolés en 2 fixtures Git absentes du sparse-checkout local, 1 assertion LF-only sous Windows CRLF et 1 test avec timeout 5 s. Après ajout des fixtures suivies Git **sans changement de code** et correction d'un seul test de portabilité CRLF en conservant l'assertion de garde exacte, les 4 suites ciblées **16/16 PASS**, y compris le timeout en isolation. Il ne s'agit pas d'un nouveau run complet vert. **TypeScript tsc PASS**, **build gardé npm run build:test PASS** vers `frontend/dist-test` avec manifest `mode=test`, sans installation. Nouveau Vitest Windows complet en cours dans checkout élargi ; CI Github sur SHA final à vérifier ; ne pas déclarer le candidat CODE_CERTIFIED tant que la CI complète n'est pas verte.
- **Dossier :** `docs/v1.5/V15_08_2_B_B7_CANDIDATE_RED_REPAIR_20261109.md`. Dernier **B-6** source-only maintient `SOURCE_GATE_PRESENT_NO_INSTALLABLE_GO`, LOT08.2-B OPEN, tests natifs/physiques LOT10 NOT_RUN, aucune donnée patient réelle.
- **Next exact :** finir les régressions, pousser uniquement sur la même PR DRAFT, contrôler les runs de certification candidate au SHA exact, documenter Notion. CEPH experimental et Mobile Pocket restent des workflows séparés non clos sans preuve.



## LOT08.2-B / B-6 — DESKTOP INSTALLABLE ACCEPTANCE CONTRACT — 2026-11-09 — SOURCE PREFLIGHT PASS / NO GO

- **GO utilisateur :** « Go » pour définir et tester les conditions d'acceptation du véritable Desktop installable ; aucune autorisation de merge, de certification master, de build EXE, d'installation ni de migration clinique. PR #1239 DRAFT/OPEN, HEAD source avant ce sous-lot `b003528a744f78ad4a9375e7de0eb70762f38b34`.
- **Décision unique :** le LAB Queue Core et sa CI ne constituent pas `CODE_CERTIFIED` ni `INSTALLABLE_CERTIFIED`. Le vrai binaire installable exige les gates de `docs/CABINET_CERTIFIED_RELEASE_POLICY.md` : SHA exact master → CODE_CERTIFIED+Sigstore → assets scientifiques certifiés au même SHA → INSTALLABLE_CERTIFIED+7 manifestes → packaging natif fail-closed → FUE installable sur PC fictif → GO distinct de migration patients et LOT10 physique.
- **Livré :** matrice de décision exhaustive `docs/v1.5/V15_08_2_B_B6_DESKTOP_INSTALLABLE_ACCEPTANCE_20261109.md` avec Success/Proof/STOP et états PRESENT/NOT_RUN/NOT_AUTHORIZED. Nouveau préflight source **READ-ONLY** `scripts/v15_08_2_b_desktop_installable_preflight.py` : SHA 40 hex exact, dix garde-fous source inspectés, détection de couplage entre `WaitingRoomPage` et Queue Core LAB, rapport permanent `installable_ready=false` / `clinical_go=false`; aucun accès cabinet, installation ou package. `queue_core/tests/test_installable_source_preflight_08_2_b.py` injecte source altérée, mauvais SHA, refus de sortie dans repo, état NO GO.
- **Preuves source Windows Python 3.12 :** `SOURCE_GATE_PRESENT_NO_INSTALLABLE_GO`, **10/10 contrôles statiques PRESENT** ; **5/5 tests ciblés de préflight PASS** ; suite globale Queue Core finale **127/127 PASS / 95,37 s**, compilation et diff-check PASS. Préflight désormais **strictement lecture seule** (stdout simple ou `--json`, aucune option de fichier de sortie). Les protections doivent encore être exercées sur un vrai artefact certifié avant acceptation native ; CI au nouveau SHA à relever après push.
- **Source canonique existante :** `docs/CABINET_CERTIFIED_RELEASE_POLICY.md`, `docs/quality/REALITY_PROOF_GATE.md`, `installer/DigitalCrown.iss`, `DigitalCrown.spec`, `run.py`, `docs/handovers/2026-11-07-restore03-installable-candidate-preflight.md`. La preuve B-5b sur le SHA `b003528` est Queue Core Linux **119 PASSED / 3 SKIPPED** et Scope Gate SUCCESS ; `Cabinet CODE_CERTIFIED candidate regression (no package)` était QUEUED au contrôle et **n'est pas une certification master**.
- **STOP / NEXT EXACT :** LOT08.2-B reste OPEN. Finaliser régression, exact-head PR/CI, mettre Notion à jour ; toute promotion vers master/installable et tout test sur clinique nécessitent un GO humain séparé. Ne pas créer de pourcentage non prouvé.



## LOT08.2-B / B-5b — RED CI DEPENDENCY ISOLATION — 2026-11-09 — WINDOWS PASS / LINUX CI PENDING

- **GO utilisateur :** « Red », traiter le blocage critique suivant de la PR #1239, sans fusion, installation, déploiement ou migration patient. HEAD avant fix `10ff5f55b4ec43709ad23e7f1b7a4e90f31283b9`. BRANCHE `feat/v15-08-2-b-rbac-isolation-20261109`, PR OPEN/DRAFT.
- **Cause constatée dans les logs GitHub :** [Queue Core #42634986803](https://github.com/hraaaaf/Digital_crown/actions/runs/42634986803) FAIL au SHA 10ff5f5 pendant **pytest collection, 0 tests exécutés**, `ModuleNotFoundError: email_validator`. La suite isolée Queue Core importait `backend.queue_core_desktop_lab`, ce qui importait d'abord `backend/__init__` et des schémas médicaux nécessitant `pydantic.EmailStr`. [Scope #42634986969](https://github.com/hraaaaf/Digital_crown/actions/runs/42634986969) SUCCESS. Ce n'était PAS un échec d'autorisation Queue Core.
- **Correction sécurité/architecture :** le module LAB existant, inchangé, est maintenant `queue_core/service/desktop_lab_bridge.py` ; `backend/queue_core_desktop_lab.py` est un shim de compatibilité vers cette implémentation, afin que l'authentique `backend.main` conserve sa composition. Tests Queue Core importent directement le module isolé ; nouveau test sur interpréteur vierge interdit l'import implicite de `backend`. Aucune dépendance clinique ajoutée, aucun skip de test ni affaiblissement de la CI ; aucun changement aux données, aux rendez-vous ni à la sécurité de production.
- **Proof Windows locale vérifiée :** `BACKEND_LOADED=False` import du module LAB depuis processus Python vierge ; suite ciblée Desktop 8/8 PASS ; suite globale `py -3.12 -m pytest -q queue_core/tests` **122/122 PASS / 82,28 s**, `compileall` et `git diff --check` exit 0. **Véritable `backend.main` ASGI synthetic** après shim : autorisation 403/401/200/CHECK_IN/logout/401, **exit 0**, sans démarrer `lifespan` clinique, et SQLite temporaire supprimée.
- **Document :** `docs/v1.5/V15_08_2_B_B5B_CI_ISOLATION_FIX_20261109.md`. CI au prochain SHA final à attester et Notion à synchroniser. **LOT08.2-B OPEN**, logiciel cabinet certifié/installer, essais physiques LOT10, données patients et migration `/appointments` NOT_RUN.
- **NEXT EXACT :** push contrôlé du correctif sur PR #1239 DRAFT, lire jobs/logs Linux et Scope Gate du nouveau SHA ; si échec changer de stratégie sans prétendre PASS, sinon actualiser Notion/PR. Aucune fusion ou déploiement non autorisé.



## LOT08.2-B / B-5a — REAL BACKEND.MAIN ASGI LAB FUE-I — 2026-11-09 — PASS / NO DEPLOY

- **Décision & périmètre :** GO « Green next » après B-5 Chromium LAB ; vérifier le véritable point d'entrée `backend.main:app` et ses middlewares via ASGI local synthétique. Aucun runtime clinique/lifespan, aucun installable ni migration patient ou de cabinet. Base git `3203eff850b081261ec7959cb81cc8f4a2bda782` PR #1239 DRAFT et non fusionnée.
- **Test autonome :** `queue_core/tests/desktop_main_lab_probe.py` : flag explicite `DIGITALCROWN_QUEUE_MAIN_FUE_RUN=1`, `ENVIRONMENT=test`, clinique `sqlite:///:memory:` et attestation runtime isolé, deux vraies SQLite temporaires B-2 + Queue Core avec comptes/visites fictifs, import réel `backend.main` **sans lancer clinical lifespan**, réseau absent ; test HTTP ASGI loopback réel sur la composition globale et les middlewares (synthetic `testclient` 403, 127.0.0.1 → 401 sans auth, 200 login/snapshot/check-in, 200 logout, 401 session révoquée). `backend.main` garde `WaitingRoomPage` clinique historique intacte. Commande : `$env:DIGITALCROWN_QUEUE_MAIN_FUE_RUN='1'; py -3.12 -m queue_core.tests.desktop_main_lab_probe` → **exit 0 / ACTUAL_BACKEND_MAIN_ROUTING_AND_RBAC_PASS_NO_CLINICAL_LIFESPAN**. Fermeture explicite moteurs SQLAlchemy pour suppression des fichiers Windows.
- **Écarts rencontrés et résolus :** `relay` absent seulement du sparse-checkout local, ajouté sans changement source ; testclient ASGI synthétique 403 attendu car seul loopback réel est autorisé ; SQLite test verrouillée pendant nettoyage initial, puis `engine.dispose` et rerun code 0. Warnings imports modèle Pydantic / ONNX absent dans sparse checkout non bloquants pour ce test.
- **Preuve :** `docs/v1.5/V15_08_2_B_MAIN_ENTRYPOINT_FUE_I_20261109.md`. B-5 précédent : FUE-G navigateur Chromium 19/19 PASS + captures 7, suite locale Windows 121/121 PASS, build:test isolé PASS. Le présent FUE-I **n'est pas** un test du cycle de vie de l'application clinique, du paquet installable, du contenu patient ou des machines cabinet. LOT08.2-B OPEN / LOT10 PHYSICAL NOT_RUN.
- **CI :** Scope Gate sur HEAD B-5 3203eff SUCCESS ; Queue Core #42632131539 encore QUEUED au relevé ; le prochain commit B-5a nécessite une vérification CI sur son SHA propre avant tout jugement. Aucun merge / déploiement / Vercel.
- **Next exact :** attester CI exact-SHA, documenter Notion + PR, puis isoler les critères d'acceptation d'un candidat Desktop installable avant tout test patient réel.



## LOT08.2-B / B-5 — DESKTOP LOCAL LAB FUE-G — 2026-11-09 — PREUVE BROWSER PASS / B OPEN

- **GO utilisateur :** raccorder B-4 HTTP/SSE au runtime Desktop local en laboratoire, FUE-G navigateur, sans fusion/déploiement/installation ni patient réel. PR #1239 DRAFT, HEAD avant B-5 `16bf642d2558380326e89fea3ac049308048de0f`, base master `324afd13487acf7ff29223f077451927b54b8178`.
- **Reality check :** Desktop réel `run.py → backend.main:app` + React ; `WaitingRoomPage.tsx` existante utilise les vrais `/appointments`. Aucune mutation de ce workflow ni de données cliniques. Montage `backend.queue_core_desktop_lab.attach_queue_core_lab` derrière flag + environnement `test` uniquement, deux fichiers SQLite synthétiques préexistants, marqueur explicite ; le montage dans `backend/main.py` est opt-in et exclut cabinet/production. Login opérateur B-2 tenant résolu serveur, rôles/grants seulement comme indices UI, RBAC toujours côté serveur.
- **Client LAB :** `frontend/src/features/queue-core/QueueCoreLabPane.tsx`, route React dév protégée `/queue-core-lab` plus entrée Vite de test isolée `/queue-core-fue.html`. Un navigateur réel utilise token Bearer volatile (pas URL/cookie/storage), fait check-in→call→chair→done, affiche les événements SSE, cache les actions non autorisées, et efface les visites immédiatement si le flux est clos/révoqué.
- **FUE-I :** montage Desktop 8/8 PASS, tests ciblés montage+HTTP/SSE 21/21 PASS, Python 3.12 Windows. **FUE-G navigateur :** Chromium + Python FastAPI et Vite sur processus loopback distincts, deux SQLite temporaires, 19/19 checks PASS, 7 captures 390/768/1280 et JSON hashes SHA256 ; aucune erreur navigateur inattendue ; vérification du 401 après révocation externe. Preuve : `docs/v1.5/V15_08_2_B_DESKTOP_LAB_FUE_G_20261109.md` et `docs/v1.5/evidence/lot08_2_b5_fue_g_20261109/`.
- **CI et gates :** re-tests complets Windows Python 3.12 **121/121 PASS (89,32 s)**, compilation Python PASS, TypeScript `tsc --noEmit -p tsconfig.app.json` PASS, build gardé `npm run build:test` PASS dans `frontend/dist-test` sans toucher au dist cabinet ; GitHub CI au SHA final à vérifier après push. FUE-G est **LAB navigateur synthétique**, PAS une session clinique native installée ; aucune preuve USB/Windows installer/TLS LAN, ni intégration aux rendez-vous cliniques ; LOT10 physique NOT_RUN. **LOT08.2-B OPEN, PR DRAFT, aucun merge/déploiement.**
- **Next exact :** relever résultats locaux et Actions exact SHA, POST Notion, puis définir gate distinct pour intégration dans candidat Desktop certifiable, sans exposer de vrais patients.



## LOT08.2-B / B-4 — HTTP/SSE LOCAL ASGI — 2026-11-09 — FUE-I PASS LAB, B OPEN / NO MERGE

- **GO user :** développer la vraie interface HTTP/SSE du Queue Core depuis le B-3 in-process, sans fusion, installation, déploiement ni patient réel. PR #1239 DRAFT, base master 324afd13487acf7ff29223f077451927b54b8178 ; HEAD avant B-4 a94343a12f6045db5595e108763fe6cfd7d3068d.
- **Implémenté :** queue_core/service/http_transport.py, factory FastAPI ASGI locale (aucun socket démarré), POST commandes, GET snapshot, GET replay paginé, GET SSE streaming (text/event-stream). B-2 session Bearer obligatoire depuis Authorization header, local loopback peer+Host, pas de credentials URL/cookie, Docs/OpenAPI/CORS fermés, refus 401/403, schéma HTTP fermé à l'injection de tenant/actor, SSE recontrôle droit B-2 avant ouverture et avant chaque frame / heartbeat, reprise Last-Event-ID tenant/queue, évents minimisés sans secret et IDs validés. Ajout queue_core/service/authorized_queue.py require_queue_read() à validation fraîche.
- **FUE-I transport local réel (sans réseau) :** queue_core/tests/test_http_sse_08_2_b.py, FastAPI TestClient + httpx.ASGITransport, 13 scénarios HTTP/SSE réels / négatifs avec deux vraies SQLite isolées et données synthétiques : commandes 0→2→3→5→7, IDOR, token, non-loopback, host, corps malformé, paginated replay, cursor, SSE révocation au milieu d'un lot d'événements et anti-injection de champs SSE. Suite Windows Python 3.12 après modifications : **113/113 PASS / 46,20 s** ; compileall et git diff --check exit 0.
- **CI GitHub vérifiée sur commit transport f75bc8dc6acab24720c89fadfafceb72741b6e76 :** workflow .github/workflows/v15-08-1-queue-domain-fue0.yml avec dépendances isolées FastAPI/httpx/anyio/pydantic/starlette ; run #42620845974 COMPLETED/SUCCESS, job #129172271703, logs Linux Python 3.11 : **110 PASSED / 3 SKIPPED / 31,19s** ; Scope Gate run #42620845954 SUCCESS. Les skips ne sont pas des passes. Le commit final de documentation/STATE appelle sa propre CI, dont le verdict doit être consigné dans Notion. Preuve : docs/v1.5/V15_08_2_B_HTTP_SSE_FUEI_20261109.md.
- **LIMITES :** aucun serveur écoutant, TLS, Windows packaging, client navigateur/UI ni expérience opérateur physique ; FUE-G non exécuté, LOT10 PHYSICAL NOT_RUN. Un octet déjà envoyé ne peut pas être retiré après révocation. Architecture non déployée/non activée en cabinet. LOT08.2-B OPEN, pas de merge ni production.
- **Next exact :** vérifier la CI Linux et Scope Gate au SHA poussé, enregistrer Notion, puis réconcilier l'interface vers le périmètre 08.3 et effectuer FUE-G/browser quand un vrai client est disponible. Pas de pourcentage inventé.



## LOT08.2-B — LOCAL COMMAND/REPLAY ADAPTER FUE-I — 2026-11-09 — CANDIDATE / NO MERGE

- **GO utilisateur :** après B-2 FUE-0, intégrer le contrôle humain aux vraies commandes/lectures événementielles du Queue Core, FUE proportionné ; aucune revue indépendante obligatoire par défaut, mais contrôles SEC/IDOR/intégrité systématiquement négatifs. Pas de GO fusion ou mise en production.
- **Source réelle vérifiée :** PR #1239 DRAFT sur base master 324afd13487acf7ff29223f077451927b54b8178 ; HEAD avant travaux a642bb38d26c5b6420456fc02867e2da8ea5d6b7. Domaine et tables Queue Core existants ; aucun HTTP/SSE runtime existant.
- **Implémentation :** queue_core/service/authorized_queue.py : adaptateur local in-process sur le vrai domaine Queue Core et la base SQLAlchemy séparée de la SQLite auth B-2 ; RECEPTION check-in, STAFF call/recall, CHAIR/DONE grants séparés, NO_SHOW/override explicites, verrou de transaction auth→queue, scope tenant/visite/ressource résolu depuis le serveur, événements minimisés, pagination/replay et queue snapshot réautorisés à chaque appel. Aucun listener, create_all, migration, données patient ni identité Device.
- **FUE-I local :** 11 tests sur 2 SQLite temporaires avec commandes/vrais événements, IDOR, annulation/révocation, cursor cross-tenant, concurrence command→revoke et pagination. FUE-I ciblé 11/11 PASS ; suite globale Windows Python 3.12 finale 100/100 PASS (33,65s), compileall et git diff --check PASS ; CI GitHub au SHA final à relever après push. Preuve : docs/v1.5/V15_08_2_B_LOCAL_SERVICE_FUEI_20261109.md.
- **Limite critique :** ce FUE-I concerne l'adaptateur local **sans transport HTTP/SSE**. Aucune preuve FUE-G/browser/SSE live ni physique (LOT10 NOT_RUN). Le prochain vrai endpoint/service devra revalider les autorisations par requête, souscription, replay et événement émis. B RESTE OPEN ; ne pas fusionner, déployer ou créer de comptes cabinet.
- **NEXT EXACT :** terminer re-test Windows + CI GitHub exact-SHA, consigner Notion, puis poursuivre l'intégration transport uniquement sur périmètre autorisé quand 08.3 expose un vrai service. Ne pas revendiquer de service HTTP déjà livré.



## LOT08.2-B — FUE-FIRST remplacement gate reviewer — 2026-11-09 — B-2 FUE-0 PASS / B OPEN

- **Décision utilisateur :** la revue indépendante systématique est substituée par le FUE approprié, conformément à SKILLS.md FUE-first ; les contrôles SEC/data/révocation restent obligatoires selon les risques. Pas de revue artificielle ni de sign-off humain inventé.
- **Base vérifiée :** PR #1239 DRAFT au SHA de départ `43581796b4c57223ddd734f8b2d35bc68ab2be72`; base master `324afd13487acf7ff29223f077451927b54b8178`.
- **FUE-0 exécuté sur Windows Python 3.12 :** nouveau `queue_core/tests/test_fue_08_2_b.py` : 3/3 PASS (SQLite réel isolé : reprise, revoke/A recovery, concurrence sérialisée, fail-closed rôle corrompu). Suite complète `py -3.12 -m pytest -q queue_core/tests` : **89 PASSED**, compileall et diff-check PASS.
- **Protocole et limites :** `docs/v1.5/V15_08_2_B_FUE0_20261109.md` ; données fictives, pas de clinique, FUE-I/G indisponible (routes/API/SSE pas encore implémentés). Tests physiques exclusif LOT10. Aucune fusion/déploiement accordé.
- **Next exact :** confirmer la CI au HEAD final de ce checkpoint FUE puis traiter l'intégration des contrôles d'autorisation aux vraies commandes/flux dans un sous-lot distinct ; le lot B reste OPEN. Aucune validation FUE-G ou produit affirmée.



## LOT08.2-B — B-2 persistance opérateurs candidate — 2026-11-09 — OPEN / NO MERGE

- **GO owner 2026-11-09 :** poursuivre B-2 exclusivement après B-1 au HEAD `e0363e055fd4b31b3903b105229445e7252e1078` de PR #1239 DRAFT. Aucun GO de merge, déploiement, installation ou activation clinique.
- **B-2 implémenté en LAB isolé :** `queue_core/security/operator_store.py`, extension additive au fichier SQLite local de 08.2-A (distinct de toute DB clinique), premier Admin bind tenant contrôlé par garde local, opérateurs nominatifs, scrypt, sessions opaques, rôle unique, attributions file/ressource, grants explicites, audit append-only, last-admin et bootstrap immuable par API + trigger SQL. `local_auth.recover_admin` invalide désormais les sessions A et B atomiquement.
- **Preuve directe Windows Python 3.12 :** `py -3.12 -m pytest -q queue_core/tests` → **86 PASSED / 0 FAILED** (fixtures synthétiques SQLite temporaires uniquement) ; `compileall` et `git diff --check` exit 0. Ne pas assimiler cette preuve à une validation physique ou sécurité complète ; le SHA final et CI GitHub sont à consigner après commit.
- **Contrat :** `docs/v1.5/V15_08_2_B_RBAC_ISOLATION_CONTRACT.md`, nouvelle section B-2 avec limites. `test_operator_store_08_2_b.py` fournit tests persistés, tenant/IDOR, droits, expiration, lockout, transactions, audit refus, rollback et récupération.
- **OPEN :** revue SEC ciblée sur SHA final et CI Linux/Windows applicable ; résolution serveur fiable des tenants/visites/ressources et couplage auth→commande/flux futurs non implémentés ; aucune route/API, service SSE ou installation. Scope mono-tenant local de B-2. Essais physiques exclusivement LOT10 NOT_RUN.
- **Next exact :** commit/push candidat sur PR #1239 DRAFT, inspecter CI exacte et revue SEC indépendante, corriger tout défaut critique et demander décision de fusion distincte une fois tous les gates logiciels requis satisfaits. Aucun merge automatique.



## LOT08.2-B — RBAC tenant-scopé / isolation — 2026-11-09 — B-1 EN COURS

- **08.2-A** : [PR #1238](https://github.com/hraaaaf/Digital_crown/pull/1238) MERGED sur master commit `324afd13487acf7ff29223f077451927b54b8178`; Windows CI 53/53 PASS au SHA source `1b4380735932896b8b7a38485b2af709182c796c`, physique `NOT_RUN / LOT10`. Un workflow transversal postmerge #42599749810 était IN_PROGRESS au premier relevé.
- **Décision propriétaire** : séquence 08.2-A → **08.2-B**, pas 08.3. G2 validé : Admin configuration/audit sans droits opérationnels ; accueil check-in/QR ; staff call/recall ; CHAIR/DONE distincts, NO_SHOW et queue.override OFF par défaut, permissions par tenant/file/visite/ressource.
- **B-1 candidat (PR DRAFT, non fusionné)** : policy pure `queue_core/security/rbac.py`, oracles synthétiques d'isolation/refus/révocation via resolver de session live, contrat `docs/v1.5/V15_08_2_B_RBAC_ISOLATION_CONTRACT.md`. La présence de code + tests ne constitue PAS une preuve d'auth multi-opérateurs persistante ni une certification des flux.
- **B reste OPEN** : persistance isolée des opérateurs nominaux, rattachements/permissions et authentification par compte, révocation immédiate de sessions, preuve last-admin et contrôle réellement appliqué sur chaque future commande/flux, revue SEC indépendante et CI au SHA avant GO de merge. C/D/E, 08.3, déploiement, cabinet et données patients hors périmètre.
- **Next exact** : CI Python/tests existants + nouveaux tests RBAC, examiner SEC et compléter durable store/transactions ; aucune validation physique avant LOT10.

## DÉCISION PROPRIÉTAIRE — 2026-11-09 — LOT08 logiciel/LAB ≠ LOT10 physique

**Cette décision prime sur les anciens checkpoints « NO-GO merge car tests physiques non exécutés » contenus plus bas.** La roadmap officielle [V1.5-10 — Tests physiques exclusivement](https://app.notion.com/p/3e677c66336281fcbe65f8889baf8c6a) réserve la validation matérielle/terrain au **LOT10** : 10.1 (installation postes), 10.2 (Queue Core réel), 10.7 (incidents/sécurité terrain), 10.8 (réception humaine). Le premier enrôlement physique Admin `issue→enroll→recover`, les ACL sur installation réelle, la récupération offline et le refus d'autres profils sont **PHYSICAL NOT_RUN / LOT10**. Ils ne sont **pas un préalable de clôture logicielle/merge du LOT08.2-A** ; l'utilisation clinique reste interdite jusqu'aux gates terrain applicables.

**Preuves 08.2-A :** [Windows Actions #42596486051](https://github.com/hraaaaf/Digital_crown/actions/runs/42596486051) SUCCESS sur SHA exécutable `1b4380735932896b8b7a38485b2af709182c796c`, **53/53 tests PASS**, création Win32 et vérification ACL réelles uniquement sous RUNNER_TEMP, refus CLI non interactive sans modification ProgramData, refus ACL non conforme ; [Ubuntu FUE-0 #42596493320](https://github.com/hraaaaf/Digital_crown/actions/runs/42596493320) SUCCESS. Une **décision de clôture du logiciel** doit considérer revue SEC, CI, risques et périmètre, sans exiger le terrain physique.

**PR #1238 :** reste DRAFT/non fusionnée **en attente d'une décision d'intégration distincte du propriétaire et des contrôles logiciels applicables, pas d'une preuve physique LOT10**. Pas de déploiement, d'installation cabinet ou de passage automatique à 08.2-B–E. **Next exact :** revoir les preuves et le diff logiciel A, proposer décision de merge ; si approuvée, merge + contrôles post-merge, puis poursuivre roadmap logicielle. Les précédentes mentions contradictoires documentent le gate erroné désormais supersédé.

## LOT08.2-A — Windows GitHub Actions ACL complémentaire — 2026-11-09 — CI PROUVÉ / PHYSIQUE OPEN

- **PR #1238 : OPEN/DRAFT/NOT MERGED**, [preuve Windows Actions #42596486051](https://github.com/hraaaaf/Digital_crown/actions/runs/42596486051) **SUCCESS** sur SHA exact testé `1b4380735932896b8b7a38485b2af709182c796c`, Windows hosted runner et Python 3.12. La suite `queue_core/tests` **53/53 PASS** ; non-interactive `status` refusé `INTERACTIVE_CONSOLE_REQUIRED` sans effet sur ProgramData ; **vraie création Win32 d'un dossier et fichier temporaires** sous RUNNER_TEMP avec validation owner/ACE réelle Get-Acl + refus ACL non conforme. Artifact JUnit non médical. Aucun accès cabinet ni donnée patient.
- **Linux FUE-0 existant** [#42596493320](https://github.com/hraaaaf/Digital_crown/actions/runs/42596493320) **SUCCESS** sur ce SHA ; correctif de l'oracle du test de refus sous non-Windows (attendre LOCAL_WINDOWS_CONSOLE_REQUIRED) inclus. Le code sécurité runtime est resté inchangé depuis le SHA source sécurité revu `44bc6fc639332796f064dbf18a59a4f8b5c3333f`.
- **Diagnostic des premiers FAIL :** Powershell 7 runner -> sous-processus Windows PowerShell 5.1 incapable d'auto-charger `Microsoft.PowerShell.Security` pour `Get-Acl`. La même vérification exécutée directement sous Windows PowerShell 5.1 (shell natif dans Actions) est PASS. Ce n'était pas une preuve de permissions correctes tant que la vraie vérification n'était pas PASS.
- **STOP MAINTENU :** runner hébergé ≠ console physique locale élevée. Aucun `issue→enroll→recover` réel à la console LAB, aucune vérification d'identité utilisateur non privilégié par second profil humain, aucune restauration hors ligne réelle sur poste LAB : **NOT_RUN**. Aucun merge, déploiement, installation cabinet, 08.2-B/C/D/E ni certification clinique autorisés. **Next exact :** Windows LAB physiquement isolé, Admin élevé local, recette première inscription + ACL + récupération offline, preuves expurgées, puis gate humain GO/NO-GO.
- **Fichier canonique :** ce checkpoint documentaire est ajouté après la CI ; le SHA testé `1b438073...` reste la preuve exécutable. Toute différence de SHA ultérieure doit être réconciliée par comparaison du delta, sans déclarer une nouvelle CI PASS si elle n'a pas tourné.

## LOT08.2-A — Local Windows identity/bootstrap — IN PROGRESS / DRAFT (2026-11-09)

- **2026-11-09 SEC review current source `44bc6fc639332796f064dbf18a59a4f8b5c3333f`**: independent read-only Codex delta review from `09f3d40e` reports **no actionable defect**. Prior full review found P2 stale expired session rows; corrected within serialized login transactions, including denied logins, with negative retention test. **53/53 direct Windows Python 3.12 PASS postcommit**, compileall exit 0, git clean. Directory/file SDDL accepted by Windows API without writes, remote CLI rejected with `INTERACTIVE_CONSOLE_REQUIRED` exit 2 and no real auth-store file created. [SEC review report](docs/v1.5/V15_08_2_A_SECURITY_REVIEW_20261109.md). **Physical elevated Windows console positive bootstrap/ACL NOT RUN; PR #1238 remains DRAFT / NO-GO merge or clinic install pending physical LAB proof**. No 08.2-B GO.

- **2026-11-09 independent Codex review on SHA 09f3d40e:** found P2 unbounded expired sessions retained in SQLite. Fixed under the login transaction by pruning `expires_epoch <= now` even on denied logins; added negative synthetic retention test. **53/53 direct Windows Python 3.12 PASS**, compileall and diff check PASS. New exact SHA and separate final review still required. Physical Windows local elevated console enrollment/ACL positive **NOT_RUN**; no clinical use, merge, 08.2-B or deploy.

- **2026-11-09 separate Codex review on e3513ac9:** no P1/P2 findings; one P3: read-only `status` unexpectedly created an auth directory before first enrollment. Fixed `windows_cli._database_path(initialize=False)` to inspect without creating, with a regression test. **52/52 direct Windows Python 3.12 PASS**, compileall and diff-check PASS. Fresh reviewer required on the *new* commit; physical elevated Windows-console positive enrollment/ACL still NOT_RUN, no real auth store created and no merge under this checkpoint.

- **SEC critical review #1, initial SHA 58e3b5e7:** independent targeted Codex SEC/OPS review identified P1 directory-owner ACL spoof and P2 dangling reparse bypass. Corrected with atomic Windows SDDL protected CreateDirectoryW/CreateFileW, trusted SID owner and both distinct required ACEs, non-following `lstat()` and `FILE_FLAG_OPEN_REPARSE_POINT`, with synthetic negative/static Win32/PowerShell tests. **51/51 direct Windows Python 3.12 PASS on preceding e3513ac9.** Subsequent 2026-11-09 review P3 correction now **52/52 PASS**. Real elevated physical console creation/ACL remains NOT_RUN. New SHA needs another independent security review before merge.

- **GOAL:** standalone Queue Core first Admin enrollment on a physically local elevated Windows console, no Internet, Firebase, patient records or clinical database access.
- **Owner GO:** « Play 8-2 A go ». This authorizes implementation of A only, not merge/release or 08.2-B–E.
- **BASE:** `edf26bb7ff70904b802069891f31ef3b4dc7691d` master (LOT08.1 CLOSED 29/29). Worktree `feat/v15-08-2-a-local-admin-bootstrap-20261108`, isolated branch.
- **DELIVERABLE CANDIDATE:** `queue_core/security/local_auth.py` (SQLite local auth + bootstrapping), `windows_console.py` OS privilege/console gate, `windows_cli.py` ProgramData ACL-controlled offline CLI, synthetic negative unit tests and `docs/v1.5/V15_08_2_A_LOCAL_ADMIN_BOOTSTRAP_CONTRACT.md`.
- **PRELIMINARY DIRECT WINDOWS EVIDENCE:** Python 3.12 `pytest -q queue_core/tests` **52/52 passed** (29 08.1 + 23 08.2-A incl. Windows ACL/symlink hardening and read-only status); compileall PASS. Real Remote Desktop Commander shell `python -m queue_core.security.windows_cli status` denied with `INTERACTIVE_CONSOLE_REQUIRED` exit 2; `ProgramData\DigitalCrownQueueCore\local_auth.sqlite` absent before/after. NO real admin account or recovery secret generated; tests use temp SQLite synthetic fixtures and injected guard.
- **SECURITY CONTRACT:** 256-bit random bootstrap (10min), single use/5-attempt cap; scrypt salted passwords, opaque SHA-256 session verifier and lockout, 8h sessions; separate 256-bit offline recovery secret, one-time rotation and all-session revocation. Restricted Windows physical console and ACL verification; no public route. No default admin.
- **UNVERIFIED / BLOCKED FOR REAL USE:** actual elevated physical Windows-console onboarding, DirectorySecurity Set-Acl success on target PC, backup/restore/installed service, session-cookie/network auth, multi-tenant RBAC, kiosk/QR, standalone runtime and legal G3. Risk-critical source needs independent SEC/OPS review on exact SHA before any merge, with negative tests and correction loops. No automation GitHub Actions requested.
- **NEXT:** commit & push DRAFT PR, direct Windows proof exact SHA, separate reviewer, POST Notion. Do NOT merge, install or begin 08.2-B without distinct GO.

## LOT08.1 — Queue Core domain contracts — CLOSED / POST-MERGE VERIFIED (2026-11-08)

- **GOAL:** isolated standalone Queue Core domain state machine, dynamic ranking, auditable event plans, dedicated SQLAlchemy schema and synthetic FUE-0. **Delivered:** G1 transitions/rank oracles, manual NO_SHOW and queue.override, tenant/resource constraints, active chair occupancy, provenance and SQL integrity checks. No clinical DB coupling, migration, patient data or runtime deployment.
- **RESULT:** [PR #1234](https://github.com/hraaaaf/Digital_crown/pull/1234) **MERGED**; final contributor SHA `1df36d79a694f713cb19b112ae26831501cf1678`; squash master SHA `a5c47f5efcc7b9843a9fea13799bae073ca541e7` (based on parent master `16f531f04eb7daff3bf5d75017717e12927f47ab`). Owner GO "Green" captured.
- **PROOF POST-MERGE Windows:** authorized device DESKTOP-3MAJEEH, isolated worktree checked out on the exact master merge SHA; Python 3.12 `pytest -q queue_core/tests` **29/29 PASS**, `compileall -q queue_core` **PASS**, clean git tree. No GitHub Actions tests deliberately launched; older green runs belong to earlier contributor SHAs and are not evidence for this one.
- **INDEPENDENT CODE REVIEW:** fresh Codex CLI read-only agent on final contributor SHA against updated `origin/master`: no definite actionable defects reported. Its default Python 3.14 lacked pytest; only separate Windows 3.12 tests substantiate FUE. Earlier distinct reviews identified P1/P2 defects corrected and re-tested. This is **AI code review, not medical or human signoff**.
- **CLOSEOUT SCORES (08.1 scope ONLY):** EXECUTION 9.0/10, FUE_EVIDENCE 9.0/10, RETAINED 9.0/10 (minimum). FUE-0 applicable and demonstrated, no UI exists in 08.1; FUE-I/G and installed runtime remain later sublots. Final independent review + postmerge tests serve as scoped Perfection Pass.
- **LIMITS:** `call_visit` cannot prove candidate completeness; future 08.3 MUST load authoritative candidates under DB transaction lock and atomically commit resource state, audit and versions. No durable append-only, encryption, RBAC, kiosk/QR, API/SSE, webhooks, UI, backups/restore or real patient enablement is claimed.
- **HANDOVER:** `docs/v1.5/V15_08_1_QUEUE_CORE_CLOSEOUT_20261108.md`; contract `docs/v1.5/V15_08_1_QUEUE_CORE_DOMAIN_CONTRACT.md`; historical detailed review trail in `techdoubt.md` and [canonical Notion LOT08](https://app.notion.com/p/3ec77c66336281d59cdcffe610561f86).
- **NEXT EXACT:** 08.2 local identity/RBAC/device/QR requires separate GO and fresh preflight; no 08.2 start, merge beyond closeout documentation, clinic release or Vercel deployment under this approval.

# LOT07 V1.5 Desktop Experience & MultiView — 2026-11-08 — INTEGRATED DELIVERY CLOSED (LIMITED SCOPE)

- **Scope closed:** R8.3 + POLISH-01 + POLISH-02 (historical merge and postmerge CI success 2026-10-31), plus Windows B10 true NVDA certification workflow fix PR #1228, source head `68279047d9d73a501f18a1e5c7fb235f241deae7` merged at `1131f117254894d208490b2b6916fd2a4799d18b`.
- **Proof B10 source:** Windows actual NVDA, native zoom and synthetic authenticated FastAPI/React [run #42481818872](https://github.com/hraaaaf/Digital_crown/actions/runs/42481818872) SUCCESS (18 screenshots, 104 checks), owner Human Visual Approval [#42504061075](https://github.com/hraaaaf/Digital_crown/actions/runs/42504061075) SUCCESS.
- **Proof postmerge:** [Cabinet Upgrade PostgreSQL Certification #42504229531](https://github.com/hraaaaf/Digital_crown/actions/runs/42504229531), **2/2 SUCCESS** on the B10 merge commit. Merge diff is exactly one CI workflow and one synthetic browser test script, no patient/clinical runtime changes.
- **Historical DRAFT disposition:** #1131 (R5) CLOSED/NOT MERGED, core R5 API/preferences modules present on master; #1109 (R3) CLOSED/NOT MERGED, historical 3-pane DEV pilot NOT SHIPPED. The nine declared layout starting points on master are **not nine independently certified clinical UIs**. Numerous historical DRAFTs remain outside this verified closure and are not silently certified. No clinical or patient data imported.
- **Future scope:** R3 prototype and missing 3-pane specialist views are **unshipped/deferred**, preserved in [Notion backlog](https://app.notion.com/p/41277c66336281cc9654e5e69fe4e2d4), with branch/PR history intact; if deemed REQUIRED by owner, reopen LOT07 scope before treating it as completed. No blanket clearance for unimplemented clinical interfaces.
- **Roadmap:** [LOT07 canonical closeout](https://app.notion.com/p/40277c66336281b6b7ffeeecae6baff9) and [V1.5 roadmap](https://app.notion.com/p/3e677c66336281d88c82d2fbe43835fb). LOT08 G6 is cleared only for this delivered, bounded LOT07 scope. Resume LOT08 preflight against current master, and still lock G1-G5 before 08.1. 35 SP LOT08 re-estimate remains tentative, not approved baseline.
- **No release:** no Vercel, no cabinet PROD deployment, no physical multi-monitor / OS DPI200 field certification; physical tests at LOT10.

**NEXT EXACT:** Re-check current master SHA/CI, confirm relevant LOT07 closure and any REQUIRED scope exception; re-run LOT08 PRE / domain/tenant/visits before any LOT08 implementation. No implicit permission for real patient data, migration, merge of future features or production.

---


> Fichier de reprise canonique. Historique pré-audit : `docs/archive/STATE_2026-07-21.md`.

# Etat canonique scientifique — 2026-10-07

## LOT08 — Facad Ricketts 32F compatibility disposition — MERGED / POST-MERGE CLOSEOUT PENDING

- Repository: `hraaaaf/Digital_crown`
- PR: `#775` — MERGED / CLOSED
- Branch: `feat/ortho-studio-lot08-ricketts-protocol-v2`
- exact evidence HEAD before docs closeout: `575fc9e2ad21133763bdacbe512e7591a39b9f59`
- Facad source: official 3.14.1.1111 `Ricketts (32 F).cph`
- pinned profile SHA-256: `d0b442b39ac7db3dc9c46d807cb3c20bd937c69783b096b484872017f9376518`
- originally unmapped compatibility rows: **26**
- explicitly dispositioned compatibility rows: **26/26**
- remaining `unmapped`: **0**
- important boundary: **26/26 dispositioned does not mean 26 runtime aliases**. Vendor variants, landmark-authority differences, signed/presentation parity gates and non-authoritative Facad norms remain fail-closed.
- final targeted workflow: `Facad Ricketts 32F final seven contract #2` — **SUCCESS** on `575fc9e...`
- explicit adversarial review A (science/provenance): **15/15 PASS**, 0 BLOCKER / 0 MAJOR
- explicit adversarial review B (CI/reproducibility): **14/14 PASS**, 0 BLOCKER / 0 MAJOR
- additional confirmation pass: **10/10 PASS**
- final Perfection Pass: **16/16 PASS**
- final scores on evidence HEAD: EXECUTION **9.4/10**, ADVERSARIAL **9.4/10**, RETAINED **9.4/10**
- no frontend product delta; no clinical runtime activation in the final compatibility-disposition clusters
- Vercel: **NOT AUTHORIZED / NOT USED**
- merge commit: `c7209e9d35f0a85a12ee1725589bca2863aa6607` — **MERGED**

Canonical closeout source:
- `docs/handovers/2026-10-07-ricketts32-compatibility-closeout.md`

**Next exact:** merge the docs-only post-merge reconciliation PR after its exact-head documentary checks are green; then perform a read-only master coherence check and mark the LOT08 Ricketts 32F compatibility closeout fully closed.

# Etat canonique manuel - 2026-10-01

## V1.5-01 — Cabinet topology & workstation roles — CLOSED

- PR topology/workstation harness: #734 — MERGED
- merge commit #734: `a37367dcc3283ef2cb89fd79f736b387171ed89d`
- follow-up deterministic Honoraires harness: PR #738 — MERGED
- exact candidate head #738: `5de868634a2335bce13a306b70124a58d33f99d9`
- final merge commit: `b7c6d25b99e1de2b5a8e937f0909ba02b040f99e`
- T2 PR certification #5948 / run `36894203496`: **SUCCESS** end-to-end
- PR CI #7129 / run `36894203439`: **SUCCESS**
- post-merge master CI #7132 / run `36912825476`: **SUCCESS**
- post-merge Cabinet Upgrade PostgreSQL #1091 / run `36912825240`: **SUCCESS**
- deterministic Honoraires period: fixed September 2026 fixture + explicit Accounting UI period selection; no UTC/local month rollover dependency
- WorkstationModeGate/auth: unchanged by the hardening follow-up
- production runtime: unchanged by PR #738
- double-check internal review: **9.7/10**
- triple-check adversarial internal review: **9.6/10**
- Vercel: **NOT AUTHORIZED / NOT REQUIRED**

**Next exact:** open **V1.5-02 — Patient Identity & Photo**.

# Etat canonique manuel - 2026-09-30

## V1.5-00 — Hub & Dispatcher — CLOSED

- PR closeout: #724 — MERGED
- merge commit: `2f0fdeb4583e633e479627a275d7da2d6bc1375e`
- exact candidate head: `f406ae767f2585e468a15cbc65ce5d106573e9f1`
- targeted Hub/Gate/Station/Admin tests: **17/17 PASS**
- Hub Visual Proof run `36788607154`: **SUCCESS**
- Human Visual Approval run `36790450196`: **SUCCESS**
- double-check exact-head: **9.3/10**
- triple-check adversarial exact-head: **9.0/10**
- post-merge code identity: the four touched Hub/Gate runtime+test blobs are byte-identical between candidate HEAD and merge commit
- V1.5-00 residual gap closed: Control Center remains fail-soft as a local recovery surface while clinical routes remain fail-closed; Station remains restrictive
- CI doctrine: only directly impacted tests/builds/workflows are proof-relevant; broad unrelated frontend/browser matrices are not rerun or treated as blockers unless a transverse dependency or invariant requires it
- Vercel: **NOT AUTHORIZED / NOT REQUIRED**

**Next exact after closeout docs merge:** open **V1.5-01 — Cabinet topology & workstation roles**.

# Etat canonique manuel - 2026-09-29

## V1 — CLOSED / V1_OPERATIONAL

- Repository: `hraaaaf/Digital_crown`
- V1-08 initial freeze: **CLOSED** - `3c86e72bf0e132e6f79bc336d4ff9eb121d08fab`
- V1-09 installability: **CLOSED / INSTALLABLE_CERTIFIED**
- V1-10 real cabinet activation: **CLOSED / VERIFIED**
- Final certified/installed V1 SHA: `bce60b26059054ba43cf8ec13cd210098e648ea4`
- Installed release: `dc-cabinet-bce60b260590-run36628947897`
- `INSTALLABLE_CERTIFIED`: **OUI**
- `V1_OPERATIONAL`: **OUI**
- Evidence-carrying master before docs closeout: `6966ebf2656f78dd6674d435bc806bd659248d0f`
- Master CI `36638379136`: **SUCCESS**
- PostgreSQL certification `36638379156`: **SUCCESS**
- Live cabinet: health/db/storage HTTP 200; normal launcher restart OK
- Preservation: 434/434 document archives and 2915 media files; integrity PASS
- Rollback: fresh encrypted DB/media backup retained; isolated historical rollback rehearsal documented
- Limitation: V1-10 does not claim comparative visual UX certification
- Vercel: **NOT AUTHORIZED / NOT REQUIRED**

## Continuite

V1 is **CLOSED** and operational on the real cabinet. No V1 execution lot remains. After this final canonical documentation closeout is merged and re-read on `master`, execution authority transfers to the canonical POST-V1 / V1.5 roadmap. Next exact: **V1.5-00 — Hub & Dispatcher**.

# Historique canonique — 2026-08-14

## Baseline vérifiée

- Repository : `hraaaaf/Digital_crown`
- `master` après merge P0-6 : `412ab81cc5c47b7220865881f83836b539458a69`
- PR P0-6 : `#12` — MERGED
- Head candidat P0-6 certifié : `8dfe6bcfd866f62a1b41aca08554246411ad67e4`
- CI P0-6 : run `31810762297` — SUCCESS
- Backend tests/durcissement : **SUCCESS**
- Frontend tests/build : **SUCCESS**
- Garde production négative : **SUCCESS**

## Doctrine produit confirmée

- Application **on-premise / local-first**.
- Firebase : identité/licence, jamais source de vérité des dossiers patients.
- Architecture courante : modèles locaux + moteurs déterministes ; aucun LLM requis.
- Donnée patient requise mais absente = inconnue/non-évaluable ; jamais inventée.
- `tests green != validation scientifique`.
- Dans ce projet, `review` signifie par défaut **double-check complet par l’agent**, sauf demande explicite d’un reviewer externe.

## P0 — Safety & Integrity — CLOSED ✅

### P0-1 — PRESCRIPTION-MISSING-DATA-FAIL-CLOSED — CLOSED ✅

Objectif : empêcher toute valeur patient synthétique/estimée de déclencher un calcul patient-spécifique lorsqu’une donnée requise manque.

Implémentation intégrée :
- garde backend explicite `evaluable/non_evaluable` ;
- âge absent reste `None` ;
- poids absent n’est jamais synthétisé ;
- antécédents absents restent explicitement incomplets ;
- enfant sans contexte sûr ne passe pas dans le chemin pédiatrique legacy ;
- plan non évaluable = zéro ligne automatique ;
- `PrescriptionGuideModal` exige un poids explicite pour l’automatisme pédiatrique ;
- `estimateWeightFromAge()` est neutralisé ;
- top-level `assessment.age` est masqué lorsque le contexte n’est pas évaluable ;
- tests backend/frontend missing-data ajoutés.

Double-check final avant merge :
- restauration de tests `clinical_rules_engine` + `habits_engine` supprimés accidentellement ;
- test honoraires rendu déterministe, sans assertion permissive `409 ou 422` ;
- diff final : 16 fichiers, aucun fichier parasite ;
- couverture backend finale : **2459 passed, 7 skipped, 0 failed**.

Limite explicite :
- ce lot **ne valide pas scientifiquement** les constantes thérapeutiques/doses historiques du moteur legacy ;
- ces constantes restent une dette scientifique distincte.

Dette CI non bloquante :
- la CI force `httpx==0.27.2` pour compatibilité Starlette/TestClient ;
- cela entre en conflit déclaré avec `firebase-admin 7.5.0` et `ultralytics-platform 0.1.4`, qui demandent `httpx>=0.28` ;
- correction durable à traiter séparément : upgrade FastAPI/Starlette ou isolation des dépendances de test.

### P0-2 — CMO-NON-PRESCRIPTIVE-BOUNDARY — CLOSED ✅

Objectif : empêcher la synthèse CMO de transformer des mentions textuelles documentaires en diagnostic, pronostic ou décision thérapeutique autonome.

Implémentation intégrée :
- synthèse CMO convertie en signaux documentaires uniquement ;
- conservation des clés de réponse historiques nécessaires à la compatibilité ;
- ajout explicite de `evidence`, `uncertainty`, `practitioner_validation_required=True` et `automation_scope="signal_only"` ;
- pronostic autonome neutralisé en `Non déterminé automatiquement` ;
- aucune décision automatique d'initier, reporter ou modifier un traitement orthodontique ;
- mémoire Ghost CMO reclassée en `SIGNAL_CLINIQUE` ;
- tests ciblés couvrant les signaux textuels et le cas de texte négatif traité comme mention à valider, jamais comme diagnostic.

Certification :
- PR `#6` — MERGED ;
- head candidat certifié : `84c14bb54068d21a9d7c668b5d041fdac7d93e01` ;
- CI : run `31758201657` — SUCCESS ;
- backend : **2462 passed, 7 skipped, 4 warnings, 0 failed** ;
- frontend tests/build et garde production négative : **SUCCESS** ;
- merge commit : `6def2a2501cd687f5fa9be03741206b77b02643f`.

Limite explicite :
- la détection reste lexicale et peut relever une mention négative ou hors contexte ; elle est exposée comme **signal incertain à valider**, jamais comme conclusion clinique.

### P0-3 — SQLCIPHER-FAIL-CLOSED — CLOSED ✅

Objectif : empêcher un cabinet on-premise configuré sur SQLite disque de démarrer en clair si SQLCipher est indisponible ou si la migration de chiffrement échoue.

Implémentation intégrée :
- `ENVIRONMENT=cabinet` + SQLite disque impose désormais SQLCipher ;
- driver `sqlcipher3` absent = `RuntimeError` bloquant avant ouverture d'une SQLite non chiffrée ;
- migration plaintext → SQLCipher échouée = restauration du fichier d'origine puis démarrage refusé ;
- `development` et SQLite `:memory:` restent compatibles avec la CI/tests ;
- tests subprocess forcent l'absence de `sqlcipher3`, couvrent le refus de démarrage, la restauration du fichier plaintext et la non-régression development.

Certification :
- PR `#8` — MERGED ;
- head candidat certifié : `bf01fc9b66848c64ba159924ceb900da90d886fe` ;
- CI : run `31785414095` — SUCCESS ;
- backend : **2465 passed, 7 skipped, 4 warnings, 0 failed** ;
- frontend tests/build et garde production négative : **SUCCESS** ;
- merge commit : `c4adedb6528d586e3a8ec8fa5c52e33069cfb9f3`.

### P0-4 — PARTIAL-PAYMENT-NO-INFERENCE — CLOSED ✅

Objectif : empêcher `documents/generate` de créer un véritable `Payment` partiel à partir d'un montant inventé lorsque le contrat ne transporte aucun montant encaissé explicite.

Implémentation intégrée :
- `DocumentRequest` refuse `payment_status=PARTIEL` sans montant encaissé explicite ;
- le flux dédié `/accounting/payments` reste le chemin autorisé pour un paiement partiel car `PaymentCreate.amount` y est obligatoire ;
- `EN_ATTENTE` et `PAYE` restent valides ;
- tests dédiés couvrent le refus fail-closed et l'absence d'écriture partielle inférée ;
- le test financier legacy a été réaligné sur `PAYE` afin de ne plus codifier l'ancien comportement dangereux.

Certification :
- PR `#9` — MERGED ;
- head candidat certifié : `7e5066d1dd53abfde33ad5e8043cd1c5d14c4d37` ;
- CI : run `31805059079` — SUCCESS ;
- frontend tests/build et garde production négative : **SUCCESS** ;
- merge commit : `a99025d67a5470219369c633570a617e19f6f557`.

Limite UX connue :
- le bouton `PARTIEL` du Document Studio reste fail-closed jusqu'à ajout d'un vrai champ montant encaissé ; aucune valeur financière ne doit être devinée entre-temps.

### P0-5 — PRESCRIPTION-SAFETY-TENANT-GUARD — CLOSED ✅

Objectif : empêcher `POST /api/prescriptions/safety/check` de lire ou évaluer un patient hors tenant avant l'appel au service clinique.

Implémentation intégrée :
- `assert_patient_access(patient_id, current_user, db)` s'exécute avant `prescription_service.check_safety(...)` ;
- un patient d'un autre tenant produit `403 Accès refusé` ;
- le service de sécurité n'est jamais appelé pour ce patient ;
- test cross-tenant dédié ajouté.

Certification :
- PR `#11` — MERGED ;
- head candidat certifié : `d579750ce5897f86e902cf70b4e5003d188f1762` ;
- CI : run `31807332356` — SUCCESS ;
- frontend tests/build et garde production négative : **SUCCESS** ;
- merge commit : `67dc6620f5667ad4060592ef5662379fc720b6f9`.

### P0-6 — PREVIEW-MUST-BE-READ-ONLY — CLOSED ✅

Objectif : garantir qu'une preview documentaire ne persiste aucun état comptable ou archive en base.

Implémentation intégrée :
- les previews d'échéancier à données directes utilisent `flush()` puis `rollback()` au lieu de commits durables ;
- `DocumentFactory.create_installment_plan(..., archive=False)` désactive la création de `DocumentArchive` en preview ;
- le chemin preview avec `plan_id` existant désactive lui aussi l'archivage ;
- le log d'audit `GENERATE` n'est pas persisté en preview ;
- `DocumentRequest` accepte explicitement `echeancier`, alignant le contrat avec le routeur ;
- test dédié vérifie que `InstallmentPlan`, `Installment` et `AuditLog` restent inchangés et que la factory reçoit `archive=False`.

Certification :
- PR `#12` — MERGED ;
- head candidat certifié : `8dfe6bcfd866f62a1b41aca08554246411ad67e4` ;
- CI : run `31810762297` — SUCCESS ;
- backend tests/durcissement, frontend tests/build et garde production négative : **SUCCESS** ;
- merge commit : `412ab81cc5c47b7220865881f83836b539458a69`.

## P1 — Hardening — ACTIVE

### P1-1 — NATIVE-SECURE-STORAGE — CLOSED ✅ (N/A runtime courant)

Constat vérifié : le client actuel est une PWA React/Vite et le dépôt ne contient aucun runtime natif Capacitor/Tauri/Electron ni dépendance Keychain/Keystore/SecureStore à câbler.

Décision :
- ne pas introduire un wrapper natif artificiel uniquement pour satisfaire la roadmap ;
- le runtime web courant ne doit pas persister de bearer secret longue durée dans `localStorage`, `sessionStorage` ou IndexedDB ;
- tout futur client natif devra stocker les credentials longue durée exclusivement dans le Keychain/Keystore du système.

### P1-2 — MOBILE-CREDENTIAL-LIFETIME-REVOCATION — ACTIVE

Objectif : réduire l'exposition des credentials mobiles longue durée et vérifier une révocation réellement fail-closed.

Constats initiaux :
- le flux mobile/ZKA émet actuellement un bearer JWT avec une durée de vie de 365 jours ;
- une infrastructure `jti`/blacklist existe déjà et doit être conservée puis testée, pas réinventée ;
- le flux de claim one-shot doit être vérifié pour ne pas consommer définitivement le token avant validation complète du handshake.

### P1-3 — CABINET-SETTINGS-STRICT-WHITELIST

Whitelist Pydantic stricte pour les paramètres cabinet ; pas de mass assignment générique.

### P1-4 — PATIENT-SCOPED-TENANT-AUDIT

Audit tenant exhaustif des routes patient-scopées.

### P1-5 — UPLOAD-MIME-MAGIC-BYTES

MIME + magic bytes systématiques sur uploads sensibles.

### P1-6 — FRONTEND-HASACCESS-CENTRALIZATION

Centraliser `hasAccess()` frontend.

### P1-7 — LEGACY-ENGINE-QUARANTINE

Quarantainer/supprimer les anciens moteurs non utilisés.

## P2 — Certification

- CI sur le head réellement candidat.
- Backend + frontend + build.
- Smoke live/rehearsal ciblé selon le risque.
- Audit visuel 390 / 768 / 1280 pour les lots UI concernés.
- Accessibilité clavier/ARIA sur contrôles custom.
- Validation scientifique céphalométrique source par source avant toute revendication autoritative.

## Skills scientifiques applicables

- `.claude/skills/audit-prescription-flow/SKILL.md`
- `.claude/skills/audit-clinical-diagnosis-flow/SKILL.md`
- `.claude/skills/audit-panoramic-report-pipeline/SKILL.md`
- `.claude/skills/validate-cephalo-pipeline/SKILL.md`
- `.claude/rules/scientific-engineering.md`

## Lot actif

### LOT P1-2 — MOBILE CREDENTIAL LIFETIME + REVOCATION — ACTIVE

---

## Document Studio — chantier actif — 2026-08-15

Roadmap canonique : `DOCUMENT_STUDIO_ROADMAP.md`.

### R1 — P0 Cohérence médicament / Maroc-first — CLOSED ✅
- PR `#17` — MERGED.
- Head certifié : `8063b11b061ea6d1912e1b4e1a0ab8ef1fcb649a`.
- CI : run `31852032393` — SUCCESS.
- Merge : `e32ab311f72980e0797b93a306c3616a4ff66042`.

### R2 — P0 Persistance protocoles/habitudes — CLOSED ✅
- PR `#19` — MERGED.
- Head certifié : `ba66457e5f65917f71670e151826062442525200`.
- CI : run `31852827218` — SUCCESS.
- Merge : `432a95eca05d1d7b9781d2d8e81077f0dcb589f2`.

### R3 — P0 Safety orchestration — CLOSED ✅
- PR `#20` — MERGED.
- Head certifié : `becadcafb4ba0e6a5f4fda10a0053bb92c96fe1e`.
- CI : run `31853962025` — SUCCESS.
- Frontend tests/build : SUCCESS.
- Backend tests/durcissement : SUCCESS.
- Garde production négative : SUCCESS.
- Merge squash : `75e4693dc983ba1708914d16432504bea8f0cd8c`.
- Le Studio n'affiche plus d'état safety vérifié avant succès réel du backend ; états explicites `unchecked/checking/verified/error`.
- Dette R3 non bloquante : appel safety read-only parallèle encore présent dans `DocumentHub`, à dédupliquer lors du prochain lot pertinent.
- Aucune certification clinique/scientifique humaine revendiquée.

### R4 — P0 Dirty-state & actions — CLOSED ✅
- PR `#21` — MERGED.
- Head certifié : `cdaf28874bc9155d115108bba7548470300c5ca1`.
- CI : run `31855874418` — SUCCESS.
- Frontend tests/build : SUCCESS.
- Backend tests/durcissement : SUCCESS.
- Garde production négative : SUCCESS.
- Merge : `6a4debe01cf0e0ea78e49ed787cae5e26c4976b8`.
- Dirty-state dérivé du fingerprint ordonnance complet ; garde onglet/navigateur ; reset après archivage ; actualisation contexte explicite.
- Le fallback source `forme: d.forme || 'Sachets'` existe encore dans le legacy, mais son effet caché est neutralisé à la frontière transport et la forme manquante est explicitée dans l’UI.
- Aucune certification UX runtime ni clinique/scientifique humaine revendiquée.

### R5 — P1 Fast Prescription UX — CLOSED ✅
- PR `#22` — MERGED.
- Head certifié : `6de453962668e66be9e26978ec07fc9082afacb7`.
- CI : run `31878337816` — SUCCESS.
- Frontend tests/build : SUCCESS.
- Backend tests/durcissement : SUCCESS.
- Garde production négative : SUCCESS.
- Merge : `8957635e1bd50d8f44fbcef38c529b3c27f8fb32`.
- Quick-picks praticien issus des habitudes réelles : récents + fréquents. Aucun favori étoilé explicite inventé.
- Aucune certification UX runtime ni clinique/scientifique humaine revendiquée.

### R6 — P1 Protocoles + Référentiel — CLOSED ✅
- PR `#23` — MERGED.
- Head certifié : `10751078601c3aa5be728bc263e25a58e856c676`.
- CI : run `31879112143` — SUCCESS.
- Frontend tests/build : SUCCESS.
- Backend tests/durcissement : SUCCESS.
- Garde production négative : SUCCESS.
- Merge : `6f2b8a22f9cdca25cafe228f266ed46deee8281b`.
- Référentiel search-first, ajout manuel replié, contexte âge/poids visible, `Mes protocoles` réversible après masquage.
- Aucune certification UX runtime ni clinique/scientifique humaine revendiquée.

### R7 — P1 Contexte + Preview premium — CLOSED ✅
- PR finale `#26` — MERGED.
- Head certifié : `9a39ecc4d415e59c5457a58638a48ba0c22f81fd`.
- CI : run `31879649826` — SUCCESS.
- Frontend tests/build : SUCCESS.
- Backend tests/durcissement : SUCCESS.
- Garde production négative : SUCCESS.
- Merge squash : `2596da527fdd1bee5c6746f645e995f682ca3189`.
- PR intermédiaires `#24` et `#25` fermées sans merge car remplacées par le candidat consolidé sur baseline post-R6.
- Contexte patient et preview utilisent une terminologie déterministe ; preview responsive ; test backend prouve qu’une ordonnance `preview=true&archive=true` ne crée ni archive, ni audit, ni paiement, ni acte.
- Aucune certification UX runtime ni clinique/scientifique humaine revendiquée.

### P1 Ordonnance — ENGINEERING CLOSED ✅
- R1→R7 fermés et fusionnés.
- Roadmap canonique synchronisée.
- Interaction runtime et recertification UX/clinique restent des gates séparés et ne sont pas revendiqués.

### P2 Devis + Honoraires — ACTIVE 🟡
- Audit canonique : `docs/audits/DOCUMENT_STUDIO_P2_DEVIS_HONORAIRES_AUDIT.md`.

#### P2-A — Prix catalogue local conservé — CLOSED ✅
- PR `#27` — MERGED.
- Head certifié : `7289d0bf64c8139838470923622f8c0b588206e1`.
- CI : run `31882328096` — SUCCESS.
- Frontend tests/build : SUCCESS.
- Backend tests/durcissement : SUCCESS.
- Garde production négative : SUCCESS.
- Merge squash : `a8ce1f8143fd58f20aee5cb4ebb9b8827128c4cc`.
- Le wrapper répare uniquement les suggestions locales dont le prix catalogue existe ; aucun prix absent n’est inventé.

#### P2-B — PARTIEL fail-closed cohérent UI/backend — CLOSED ✅
- PR `#29` — MERGED.
- Head certifié : `d60a99c290e0e27c84d73fb95d947fa111461f7a`.
- CI finale : run `31884437013` — SUCCESS.
- Frontend tests/build : SUCCESS.
- Backend tests/durcissement : SUCCESS.
- Garde production négative : SUCCESS.
- Merge squash : `6543c3dad146bdbe055117fe0302b3fbe9cbda07`.
- Premier head `1005f2281868f435b8fb2f56066bc920b3151df5` : frontend/build + garde production verts, backend rouge uniquement parce qu’un `ValueError` Pydantic restait non sérialisable dans le contexte du handler JSON ; corrigé avec `PydanticCustomError`.
- `PARTIEL` ne peut plus devenir l’état du document dans ce flux ; aucun montant partiel n’est inféré.
- `PaymentCreate.amount` est strictement positif et les méthodes connues sont normalisées explicitement.

#### P2-E — Échéances/réconciliation financière exacte — ACTIVE 🟡
- Défaut confirmé : Honoraires global peut créer un plan dont la somme des échéances diffère du total facturé.
- Préparation P2-E : réconciliation exacte au centime frontend/backend + tests ; PR draft `#30` 3/3 verte sur ancienne baseline.
- #30 ne doit pas être mergée : reconstruction obligatoire sur baseline post-P2-B.

#### P2-F — Allocation PAYE exacte par Acte — PREPARED
- Défaut confirmé : Honoraires PAYE crée des Acte marqués PAYE mais un Payment global sans `acte_id`, ce qui peut diverger de la vue `actes-billing`.
- Helper/test d’allocation exacte préparés sur PR draft `#31`; intégration route à faire après P2-E.

#### Préparation UX suivante
- P2-C : quick actions tactiles + phases déterministes sans durée clinique estimée, PR draft `#32`.
- P2-D : handler legacy de déduplication odontogramme confirmé orphelin ; policy `dent::traitement`, PR draft `#33`.

#### Pré-audits isolés pendant les CI
- P3 : `work-20260815-p3-static-audit` — non fusionné.
- P4 : `work-20260815-p4-static-audit` — non fusionné.
- P5 : `work-20260815-p5-static-audit` — non fusionné.
- P6 : `work-20260815-p6-static-audit` — non fusionné.

#### P5-P0 clinique découvert — NON CORRIGÉ 🔴
- `HouseWizard` est atteignable via `Mode Expert`.
- `DiagnosticEngine` produit diagnostic/protocole/plan de traitement et substitue actuellement automatiquement des classes thérapeutiques à partir d’une détection textuelle d’allergie.
- Exemple source vérifié : pénicilline → remplacement `AMOXICILLINE` par `CLINDAMYCINE/MACROLIDE`; AINS → remplacement par `CORTICOSTÉROÏDES`.
- `Appliquer` transforme le résultat en insight `DETERMINISTIC` et positionne le score d’intelligence à 100 ; il ne persiste pas directement le treatment plan dans la DB au point inspecté.
- Branche de sécurité `work-20260815-p5p0-no-auto-substitution` : test de frontière ajouté, correctif applicatif non encore fusionné.
- Priorité : aucune substitution thérapeutique automatique ; exposer une alerte à validation praticien.

Aucune certification financière production, UX runtime ou clinique/scientifique humaine n’est revendiquée pour les lots actifs/pré-audits.
