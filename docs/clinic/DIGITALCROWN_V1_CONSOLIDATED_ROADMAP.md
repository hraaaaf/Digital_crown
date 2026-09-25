# Digital Crown — V1 Consolidated Roadmap

Status: **CANONICAL / EXECUTION LOCKED / NOT OPERATIONAL**

Effective date: 17 September 2026

## 1. Authority — single roadmap

This file is the **sole execution roadmap for Digital Crown until `V1_OPERATIONAL`**.

Until `V1_OPERATIONAL` is explicitly recorded here:

- only the current unlocked lot may advance;
- fixes/tests/docs strictly required to pass that lot are allowed;
- later-lot PRs remain parked and cannot authorize work or merge;
- every other ROADMAP/PLAN/HANDOVER/BACKLOG/OBJECTIVE is evidence/context only;
- no competing V1 roadmap may be created or used;
- no Vercel deployment is authorized;
- no real cabinet/production mutation is authorized before the final cabinet-update lot and explicit human authorization.

## 1A. Mandatory visual merge evidence

Before confirming that any product PR is ready to merge, visual proof is mandatory even when the implementation is backend-only or claims no UI delta.

Required sequence: **BEFORE → written visual Goal → implementation → AFTER at the same viewports → side-by-side comparison → visual tests → severe visual score → human review before merge authorization**.

Canonical viewports unless a lot proves another surface is more appropriate: **390×844 / 768×1024 / 1280×900**.

The BEFORE and AFTER captures must represent the actual impacted user workflow/screen, use deterministic fixtures/state when practical, and be retained as CI artifacts or another reproducible evidence source. A generic “UI Human Visual Approval” status alone is insufficient: the closeout must identify the BEFORE and AFTER artifact/run and the captures must be inspectable before merge confirmation.

For backend-only changes, capture the nearest product workflow whose behavior depends on that backend contract. If no user-visible workflow exists, document why and capture an appropriate operational/runtime evidence surface instead; never waive evidence merely because no frontend file changed.

No lot may be presented as **merge-ready** until this visual evidence is available and reviewed.


## 1B. Mandatory lot-end user recap

At the end of every lot, before moving to the next lot, provide the product owner with a short, concrete recap together with the retained visual evidence:
- BEFORE: what existed / what was missing or faulty before the lot;
- DURING: what was added, modified or removed in the lot;
- AFTER: the observable resulting behavior and the exact validation evidence;
- CAPTURES: show the retained BEFORE and AFTER captures for the same canonical viewports when the lot has UI/UX impact;
- NO-UI EXCEPTION: when the lot truly has no user-visible UI impact, explicitly say so and show the closest inspectable operational/runtime evidence instead; never fabricate screenshots;
- keep the recap short and decision-oriented, and distinguish verified facts from remaining uncertainty.

This recap is a mandatory closeout deliverable in addition to tests, severe scoring, merge evidence and canonical roadmap updates.

## 2. Global Goal / Success / Proof

**Goal:** produce the first operational V1 cabinet release from canonical V0 while preserving real cabinet data, historical integrity and rollback capability.

**Canonical V0 SHA:** `76547ed178b98b4d8cf14c0fdc691ff3f787076e`

**V1 candidate SHA:** **NOT SELECTED**

**Success:** all mandatory lots below close in order; one exact candidate is frozen; that exact candidate reaches `INSTALLABLE_CERTIFIED` on a fresh isolated restore of real PREUPDATE cabinet data; the same SHA is installed only after explicit human authorization; post-update integrity/startup/smokes pass; rollback remains verified.

**Proof:** exact SHAs + run IDs + tests/runtime evidence + migration/integrity evidence + lot closeouts recorded in this file.

## 3. Verified starting baseline — 17 September 2026

Master before this roadmap refresh: `0483883445d432ce6c7887dfab800a559c99dec4`.

Already acquired on master and therefore **not future V1 lots**:

- Connect Hub: PR `#557` integrated; canonical closeout: `docs/audits/CONNECT_HUB_E_CLOSEOUT.md`.
- Céphalo injected legacy fallback repair: PR `#579` merged.
- FAR / Mutuelles: PR `#559` merged at `20d2e01aa1f097ca93dd0a5a6699a596a392d7d8`; FAR global closeout then reached master `0483883445d432ce6c7887dfab800a559c99dec4`.
- obsolete/superseded PRs `#279`, `#401`, `#407`, `#505`, `#563`, `#578` are closed and are not future execution lots.

Important correction: the previous draft roadmap incorrectly listed already-integrated Connect Hub and FAR as future mandatory lots and referenced closed PRs as future work. This consolidated roadmap removes those contradictions.

Security/physical historical programs `#288`, `#289`, `#383` are **not promoted into the mandatory V1 path by default**. They remain parked unless a concrete requirement from a mandatory lot proves a bounded delta necessary for V1 installability/safety. They must not be resurrected wholesale.

The stale documentation PR `#577` is a competing pre-consolidation roadmap and is to be closed without merge.

## 4. Mandatory execution sequence

### LOT V1-00 — Foundation: CI / Windows / dependency contract

Status: **CLOSED — POST-MERGE MASTER CERTIFIED**

Goal: establish one coherent, reproducible runtime/build dependency contract on the actual current master, including clean Windows Python 3.12 validation and stable Linux CI consumers.

Certified foundation product HEAD: `cc34fdf42874f06d4ac3ec45073e1cbb012c6007`.

Foundation evidence:
- Windows Build Dependency Contract `35261174495` — **SUCCESS** on Windows Server 2025 / CPython 3.12.10; exact 140-package runtime lock; `pip check` green; cabinet import smoke green;
- CI `35261174409` — **SUCCESS**;
- P5 Native `35261174502`, Media C4 `35261174469`, Patient UX1-C `35261174611`, Patient P7 `35261174478`, T2 `35261174525`, Catalog `35261174529`, Marketplace `35261174526` — **SUCCESS**;
- foundation docs commit `41978064008deab3f7e91866d2a858ec21100e7e`;
- PR `#582` merged as `15b5c2084b890c8375558c80b6bd7a44f577c016`.

Post-merge repair evidence:
- first master CI `35267802853` exposed Linux dependency/Connect Hub contract drift; PostgreSQL certification `35267803004` remained **SUCCESS**;
- PR `#583` repaired Linux torch/httpx/Connect Hub/T2 contracts; exact repair HEAD `7b3d89248405296b8503d5eb16d4e54059057dee`;
- exact-head CI `35282100416`, T2 `35282100475`, Connect Hub E `35282100413`, PR Merge Summary `35282100436` — **SUCCESS**;
- PR `#583` merged as `bc7e1e1f1762431a048661ad9495a3430774f6e0`;
- subsequent master CI `35282593094` exposed one stale insurance-validator assertion while PostgreSQL certification `35282593275` remained **SUCCESS**;
- PR `#585` aligned that assertion and repaired file-backed SQLite/SQLCipher pooling after T2 `35283365207` exposed `SingletonThreadPool` detached-connection failures;
- final PR `#585` HEAD `244b452bde8eacdd873b87ef80f31a38b297af8a`: CI `35283989343`, T2 `35283989391`, FAR `35283989308`, CNOPS `35283989425`, PR Merge Summary `35283989374`, UI Human Visual Approval `35283987548` — **SUCCESS**; M6-I `35283989353` skipped by workflow conditions;
- PR `#585` merged as master `9b448dea18b1943f8b15beebf7cada1a75e96af9`.

Remaining Success criterion:
- Cabinet Upgrade PostgreSQL Certification `35284854114` — **SUCCESS** on current master `9b448dea18b1943f8b15beebf7cada1a75e96af9`;
- master CI `35284853774` — **FAILURE** after `2055 passed, 5 skipped`; the only failure was `test_zeroconf_runtime_dependency_is_declared`, whose static assertion still required the obsolete range `zeroconf>=0.131.0,<1.0` while the canonical mirrored runtime lock pins `zeroconf==0.150.0`;
- repair PR `#587`, HEAD `330994e4454a30074e8ee4e1c7e301f071cb060b`, changes only that stale test assertion; exact-head CI `35286042393`, T2 `35286042275`, PR Merge Summary `35286042260`, UI Human Visual Approval `35286041958` — **SUCCESS**; M6-I `35286042180` skipped by workflow conditions.

Remaining Success criterion:
- PR `#587` merged under expected-head guard as master `1edd440bf69ca4a79c5e265b20957148297adb3f`;
- final master CI `35286577382` — **SUCCESS**;
- final Cabinet Upgrade PostgreSQL Certification `35286577467` — **SUCCESS**.

V1-00 Success criterion is satisfied on exact master `1edd440bf69ca4a79c5e265b20957148297adb3f`. V1-01 is unlocked after this canonical closeout is merged.

Next exact: merge this canonical closeout PR after its exact-head checks/coherence are green, then start V1-01 against the resulting current master.

### LOT V1-01 — Agenda A4: physical resources and capacity

Status: **IMPLEMENTED — EXACT-HEAD CERTIFIED; MERGE GATE PENDING**

Working reference: stale PR `#575` was revalidated against certified master and used only as extraction evidence; V1-01 was rebuilt on clean branch `feat/v1-01-agenda-a4-rebuild`, PR `#588`.

Implementation candidate: `0354bdcba7d7c7390e96a94ec5e3f0e778cf28d0`.

Verified scope: tenant-scoped physical resources; canonical nullable `Appointment.resource_id` with `ON DELETE SET NULL`; resource CRUD; deterministic capacity-1 resource conflicts wired through create/update/bulk/check-conflicts; Alembic head advanced from A3 to `a4rs0000004`; A3 certification now verifies ancestry instead of incorrectly requiring A3 to remain the terminal head. No product frontend/UI files were changed.

Exact-head proof:
- CI `35316680604` — SUCCESS.
- PostgreSQL Alembic Schema Certification `35316680541` — SUCCESS.
- Agenda A3 Certification `35316680555` — SUCCESS.
- T2 Runtime Browser Certification `35316680538` — SUCCESS.
- Portability Runtime Certification `35316680511` — SUCCESS.
- Settings TemplateEngine Reachability `35316680524` — SUCCESS.
- Settings R11 TemplateBuilder Dependency `35316680605` — SUCCESS.
- Settings R11 TemplateBuilder Reachability `35316680465` — SUCCESS.
- UI Human Visual Approval `35316678700` — SUCCESS; no V1-01 product UI delta.
- M6-I `35316680502` — SKIPPED by workflow conditions.

Next exact: human merge authorization for PR `#588`; after merge, certify exact master CI/PostgreSQL before unlocking V1-02.

Goal: complete Agenda physical-resource scheduling.

Success: resource persistence/API/runtime wiring complete; create/update/bulk/check-conflicts enforce deterministic practitioner/resource capacity rules; migrations have one coherent head; targeted/global regressions green; any UI change has mandatory BEFORE → Goal → implementation → AFTER at 390×844 / 768×1024 / 1280×900 → comparison/tests/visual score.

Proof: current-master reconciliation + PostgreSQL migration rehearsal from scratch + second upgrade no-op + tests/runtime + UI evidence when applicable + exact-head CI + closeout.

### LOT V1-02 — Agenda A5: temporal/history finalization

Status: **CLOSED — MERGED AND POST-MERGE MASTER CERTIFIED**

Merged: PR `#589`; final PR HEAD `5fcf127e5d660d2ca7a4a8c84edc93da58cca83c`; merge SHA `66bc45b6c88bdefa9dc29a2bded055a3c8ff40ab`.

Verified scope: appointment history uses soft-delete markers (`deleted_at`, `deleted_by`) instead of destructive deletion; deleted appointments are excluded from active agenda reads and practitioner/resource capacity checks; cabinet wall-clock normalization remains explicit; Alembic advances coherently to `a5th0000005`; A4 bulk creation now persists the already-validated `resource_id`. No product frontend/UI files changed.

Exact-head proof:
- CI `35317837168` — SUCCESS.
- PostgreSQL Alembic Schema Certification `35317837149` — SUCCESS.
- Agenda A3 Certification `35317837110` — SUCCESS.
- T2 Runtime Browser Certification `35317837156` — SUCCESS.
- Settings TemplateEngine Reachability `35317837232` — SUCCESS.
- Settings R11 TemplateBuilder Reachability `35317837090` — SUCCESS.
- Settings R11 TemplateBuilder Dependency `35317837089` — SUCCESS.
- UI Human Visual Approval `35317834933` — SUCCESS; no V1-02 product UI delta.
- M6-I `35317837179` — SKIPPED by workflow conditions.

Final visual proof: Agenda A5 Visual Evidence `35320330136` — SUCCESS; artifact `agenda-a5-before-after` contains six deterministic BEFORE/AFTER captures at 390×844 / 768×1024 / 1280×900, with zero horizontal overflow. Human visual review completed before merge; severe visual score 9.2/10.

Post-merge master proof at `66bc45b6c88bdefa9dc29a2bded055a3c8ff40ab`: CI `35324967441` — SUCCESS; Cabinet Upgrade PostgreSQL Certification `35324967435` — SUCCESS.

Next exact: start LOT V1-03 from certified master; reconstruct accepted Morocco pharmacology evidence from stale PRs #565/#572 without merging either branch as-is.

Goal: finish Agenda V1 hardening.

Scope: explicit cabinet timezone behavior, soft-delete/history policy, legacy treatment/migration strategy, transversal regressions and final Agenda certification.

Success/Proof: deterministic temporal/history behavior + no Agenda regression + required tests/runtime/CI + closeout.

### LOT V1-03 — Pharmacology Morocco evidence reconstruction

Status: **CLOSED — MERGED AND POST-MERGE MASTER CERTIFIED**

Working references: stale PR `#565` and divergent evidence PR `#572`; neither is merge-as-is. Clean reconstruction branch: `feat/v1-03-pharmacology-reconstruction` from certified master.

Current reconstruction scope: machine-verifiable inventory/mapping/projection assets, fail-closed validators and deterministic gap audit only. Core8 clinical triage and any clinical activation remain explicitly deferred pending qualified independent scientific review.

Exact-head candidate: `f4940771fc00adb35fc81690bd635aeb861cae40` on PR `#590`. Pharmacology Deterministic Scientific Safety Gate `35327749998` — SUCCESS with 43 targeted tests, including runtime-isolation proof; reference validator proves 170 historical + 8 addenda, 20 structural gaps, and activation=NO; medicine projection proves 68/68 clinical_activation=NO. CI `35327749969` — SUCCESS; T2 Runtime Browser Certification `35327749953` — SUCCESS; Agenda A5 Visual Evidence `35327750115` — SUCCESS; UI Human Visual Approval `35327745996` — SUCCESS. No frontend or product runtime implementation is changed by V1-03; the visual doctrine is satisfied operationally by unchanged runtime/browser certification plus the explicit audit-only isolation test, rather than fabricated pharmacology UI screenshots.

Final merge: PR `#590` merged as `667e9e15ac22c9cc982415e7b662df5f34dd6bb5`. Post-merge master certification: CI `35331628877` — SUCCESS; Cabinet Upgrade PostgreSQL Certification `35331628834` — SUCCESS on rerun attempt 2 after the first attempt was cancelled during setup-python before PostgreSQL assertions executed. V1-03 is closed. Next exact: start V1-04 Cephalometry scientific re-baseline from certified master.

Residual Core-5 closeout on 18 September 2026: PR `#594` merged as `2304003a4757ed8442f0b3f2ec121aa3dce6dac2` after exact-head Pharmacology gate `35358582607` SUCCESS, CI `35358582688` SUCCESS, T2 `35358582593` SUCCESS, Agenda A5 Visual Evidence `35358582692` SUCCESS and UI Human Visual Approval `35358579137` SUCCESS. Adversarial scientific pre-review `35359075923` completed SUCCESS with decision `approve_for_human_review_with_reservations`, zero blocking findings, and explicit `clinical_activation_authorized=false`. The five Core-5 medicines remain fail-closed (`clinical_activation=NO`); exact Morocco product/form/strength/presentation closure is not a V1 merge blocker while activation stays disabled. Stale PRs `#565` and `#572` were closed without merge after evidence extraction. This residual package does not reopen V1-03 and does not authorize automatic prescribing.

Goal: reconstruct only accepted Morocco pharmacology assets/tests on a clean then-current-master branch while preserving fail-closed clinical activation.

Rules:
- regulatory/catalogue presence != dental clinical suitability;
- no unsourced indication/dose/duration/pediatric/contraindication/interaction/renal-hepatic claim;
- malformed/duplicate/boundary mappings remain fail-closed;
- `clinical_activation=NO` remains default unless qualified independent clinical/scientific review explicitly clears activation.

Success: accepted evidence extracted from #565/#572; contradictions resolved/documented; negative tests green; automatic prescribing remains disabled unless the human scientific gate is satisfied; stale evidence PRs closed after extraction.

Proof: source evidence + validators + negative tests + qualified review if activation is requested + exact-head CI + closeout.

### LOT V1-04 — Céphalométrie scientific re-baseline

Status: **IMPLEMENTED — EXACT-HEAD TECHNICAL + VISUAL EVIDENCE GREEN; HUMAN MERGE AUTHORIZATION PENDING**

Goal: inspect current master after all preceding integrations and identify only genuine remaining V1-relevant scientific/runtime gaps; do not manufacture work or reopen already certified lots.

Success: canonical scientific inventory/provenance rebaselined; BLOCKED/TODO/legacy gaps classified; only evidence-backed V1 blockers corrected; no diagnostic/treatment inference introduced without required evidence/review.

Proof: code + scientific tests + provenance + runtime evidence + mandatory UI BEFORE/AFTER if visual changes + review + exact-head CI + closeout. If no genuine V1 blocker remains, record that finding and close the lot without invented implementation.

Verified V1-04 result:
- certified base: `master@7454215274032898d1a50659d624a5cb32aab494`, CI `35335941911` SUCCESS and PostgreSQL `35335941919` SUCCESS;
- selected blocker: R18 concordance omitted COM `Surplomb` / `Recouvrement`; proof run `35338035397` exposed one deterministic Surplomb divergence on `clinical_orientation_reference`: frontend `+2.6 mm` vs backend `-2.6 mm`, delta `5.2 mm`; Recouvrement was concordant;
- correction: Step 3 now preserves signed overjet instead of converting it to an absolute magnitude; positive/reverse overjet and signed overbite regressions are locked; `M_OVERBITE_V1` unit is `mm`, while overjet/overbite construction provenance remains `LEGACY_TO_AUDIT`;
- scientific boundary: reverse overjet is preserved as a signed negative measurement when mandibular incisors are anterior to maxillary incisors; no norm, diagnostic classification, severity, indication or treatment rule was activated; R20 remains closed;
- current exact HEAD before this canonical closeout commit: `46aed2c9758b82f3ee67ffa268859e7d75232a44`;
- exact-head proof on `46aed2c9758b82f3ee67ffa268859e7d75232a44`: CI `35343025885` SUCCESS; T2 `35343025880` SUCCESS; Cephalo R15 AFTER `35343025883` SUCCESS; Cephalo R15bis AFTER `35343025868` SUCCESS; Cephalo R18 Scientific Concordance `35343025882` SUCCESS with zero divergence; Agenda A5 Visual Evidence `35343025861` SUCCESS;
- mandatory V1-04 visual artifact on that exact HEAD: artifact `10545955945`, digest `sha256:b26de23b83fd5e484d84a5d07ee922fbebe5d9f8c4e9ab82e9b6c64bb7b98fee`; BEFORE shows `+2.6 mm`, AFTER shows `-2.6 mm`, at `390x844`, `768x1024`, `1280x900`; all six captures have zero horizontal overflow, zero page errors and zero console errors;
- severe visual review: `9.4/10`; second severe expert-style review: `9.3/10`;
- Achraf explicitly approved the six retained BEFORE/AFTER captures on 2026-09-18; the `visual-approved-by-achraf` label was applied to PR #592;
- prior generic UI Human Visual Approval failure `35340553905` was diagnosed as intentional stale-approval invalidation after a HEAD change, not a product or harness defect; failed jobs were re-run after explicit approval.

Remaining scientific inventory is not promoted into invented V1 work:
- `BLOCKED_LANDMARK`: exact required landmarks are absent/non-certified;
- `BLOCKED_MODALITY_PA`: true PA/frontal acquisition is absent;
- serial displacement/change measures: paired-study/superposition authority is absent;
- `SOURCE_LOCK_REQUIRED` measures remain inactive until their exact construction/provenance is locked;
- Steiner U1-NA/L1-NB linear measures remain unavailable until the required crown landmark exists.

Next exact: certify this documentation-only closeout HEAD, re-materialize visual approval if the generic workflow invalidates it solely because of this documentation commit, then present PR #592 for explicit human merge authorization. V1-05 remains blocked until V1-04 is merged and post-merge certified.

### LOT V1-05 — Orthalis benchmark reconciliation + Ortho Journey

Status: **CLOSED — MERGED AND POST-MERGE CERTIFIED (F5 ENGINEERING PREVIEW ONLY)**

Goal: reconcile the historical competitive roadmap with current master and resume the already-defined **Lot F — Ortho Journey** instead of restarting a generic Orthalis benchmark from zero.

Historical competitive canonical:
- `docs/audits/COMPETITIVE_ROADMAP_POST_MEDIA.md`
- Competitive / Media Lot C: CLOSED.
- Patient Companion Lot D: implemented through D0/D1/D2 with final continuation handover merged.
- Connect Hub Lot E: **CLOSED**; merged via PR #557, merge commit `7c175bdd37b2f53afb7b05fd8cf21aaf4bda2164`; canonical closeout: `docs/audits/CONNECT_HUB_E_CLOSEOUT.md`.
- Therefore the next historical competitive lot is **Lot F — Ortho Journey**.

V1-05 principle:
- do not duplicate Patient Journey, Patient Companion, Connect Hub, Media Core or Céphalométrie;
- use current Orthalis claims only as an external comparison input, not as the roadmap source of truth;
- reopen an old competitive gap only if current master proves the capability is still absent or materially insufficient;
- preserve local/on-prem architecture, tenant isolation, provenance and fail-closed clinical behavior.

#### F0 — Current-state audit + Ortho Case model

Goal: map the current orthodontic, Patient Journey, Media Core, Céphalo, TreatmentPlanStep and JourneyMilestone contracts on current master and define the minimum additive Ortho Case boundary without duplication.

Success:
- exact current capability map;
- explicit reuse boundaries;
- no second patient timeline, no second media store, no duplicate cephalo engine;
- additive data model only where the current schema cannot represent longitudinal orthodontic state safely.

Proof:
- code/model audit;
- anti-duplication matrix;
- schema/migration proof if needed;
- exact-head CI before implementation proceeds.

#### F1 — Orthodontic phases + structured controls

Goal: represent orthodontic treatment longitudinally as a real clinical chronology rather than another generic patient timeline.

Target flow:
`T0 Diagnostic → Préparation → Appareillage → Alignement → Finition → Contention → Clôture`

In scope:
- treatment start date;
- current phase + phase history;
- structured orthodontic controls;
- control date, phase, observations, appliance/device context, notable event, next planned step;
- interruption/abandon/closure documented explicitly;
- each control becomes a traceable event in the existing Patient Journey.

Out of scope:
- automatic diagnosis;
- automatic treatment prescription;
- rebuilding cephalometric analysis;
- unsourced normative inference.

#### F2 — T0 / T1 / T2 / Tn + certified Media Core

Goal: bind each meaningful orthodontic study timepoint to canonical evidence.

Each timepoint may reference:
- panoramic imaging;
- cephalometric analysis;
- clinical photographs;
- scans/impressions where an existing canonical source exists;
- source-locked measurements;
- dates and provenance.

Rules:
- all media remain in certified Media Core;
- Ortho Journey stores references/relationships, not duplicate files;
- no derived clinical conclusion without source-backed rules.

#### F3 — Longitudinal Compare

Goal: provide an evidence-backed comparison over time.

In scope:
- side-by-side T0/T1/T2/Tn;
- before/after visual comparison;
- longitudinal evolution of already-certified measurements;
- exact date/provenance for every compared value;
- representative examples such as `ANB: T0 → T1 → T2` only when the underlying measurement is valid and available.

Safety boundary:
- never convert a numeric change into “improvement”, “success”, severity, diagnosis or treatment recommendation unless separately source-locked and clinically reviewed.

#### F4 — Ortho Cockpit

Goal: give the practitioner one compact orthodontic control surface.

Target summary:
- treatment start;
- current phase;
- control count;
- last control;
- next appointment;
- latest cephalometric study/timepoint;
- number of progress photo series;
- outstanding longitudinal items/events.

UX rule:
- extend/reuse existing patient/ortho navigation patterns;
- mandatory BEFORE → written Goal → implementation → AFTER at 390×844 / 768×1024 / 1280×900 → comparison/tests → severe visual score;
- do not create a competing Patient Journey surface.

#### F5 — Scientific Superimposition (separate scientific gate)

Status at V1-05 start: **NOT AUTHORIZED FOR IMPLEMENTATION WITHOUT SCIENTIFIC SOURCE-LOCK**

Goal: evaluate whether a clinically defensible cephalometric superimposition method can be implemented.

Required before code:
- dedicated scientific benchmark;
- exact method/source provenance;
- landmark/reference stability requirements;
- reproducibility/error analysis;
- explicit boundary between visualization and clinical inference.

Until that gate is satisfied:
- no homemade geometric superimposition;
- no claims of treatment success based on overlay;
- no automatic diagnostic/treatment interpretation.

#### V1-05 Success

V1-05 is successful when:
- historical competitive roadmap and current master are reconciled;
- D/E are not rebuilt;
- F0 establishes the exact non-duplicative architecture;
- only evidence-backed F1–F4 gaps required for V1 are implemented;
- any F5 scientific work remains separately gated unless fully source-locked;
- all applicable migrations/tests/security/tenant-isolation/runtime/UI evidence are green;
- exact-head CI, merge and post-merge certification are complete.

#### V1-05 Proof

Required evidence:
- current-master anti-duplication audit;
- competitive reconciliation against `docs/audits/COMPETITIVE_ROADMAP_POST_MEDIA.md`;
- current primary Orthalis sources for external claims used in the comparison;
- code + tests + behavior evidence for accepted F1–F4 changes;
- Media Core integration proof;
- longitudinal ordering/integrity proof;
- mandatory visual BEFORE/AFTER evidence for UI changes;
- severe dual review;
- canonical closeout with exact PR/HEAD/run/artifact/digest/merge/post-merge evidence.

Final V1-05 result — 2026-09-19:
- F1A OrthoCase lifecycle: PR #596 merged as `c41f47d2eb7708d6494fd32c97814d7a968ed5e0`.
- F1B structured controls: PR #598 merged as `81535364e4f98f3f9b53fac179f2fbfd2ec261f5`.
- F2 canonical timepoints/evidence references: PR #610 merged as `35ccdf5ad73b403279e129c7affe2d9364c6d4cc`, post-merge certified.
- F3 longitudinal compare: PR #613 merged as `413af20093367e43bc3c59efbaa1ad156b668ef4`, post-merge CI/T2/A5 certified; final severe visual score 9.5/10 with explicit owner visual approval.
- F4 Ortho Cockpit: PR #617 merged as `20bfe3349399bf49a2f5ece14c5f70526e9d4a1b`; post-merge certification PR #619 closed without merge after required checks were green.
- F5 Scientific Superimposition engineering preview: PR #620 merged as `2cfb0dc53b71daa9f8cbb63e966a5cab4481fc10`; exact-head CI `35430755915`, T2 `35430755873`, BEFORE `35430755892`, AFTER `35430755887` — SUCCESS.
- F5 post-merge certification PR #622, base exact product merge above, closed without merge after CI `35432362856`, T2 `35432362901`, Agenda A5 `35432362881`, PR Merge Summary `35432362857` — SUCCESS.
- F5 canonical closeout PR #621 merged as `455cff05de35166eed62ae58eb1ae9d9014503dd`.
- Scite external evidence audit added at `docs/clinic/audits/V1_05_F5_SCITE_EVIDENCE_AUDIT.md`; no rollback signal found. Danz 2024 and Vasileiou 2026 were added as validation-relevant sources.
- F5 remains OFF by default, `ENGINE_ESTIMATE_ONLY`, `clinically_validated=false`, `acquisition_protocol_status=UNVERIFIED`; independent named scientific review + human clinical validation remain required before any clinical activation.
- No F6 exists inside V1-05. The next canonical lot is V1-06.

V1-05 Goal/Success/Proof are satisfied for the engineering V1 path. This does not authorize F5 clinical activation.

### LOT V1-06 — Pre-freeze repository reconciliation

Status: **CLOSED — MERGED AND RECONCILED**

Goal: ensure no stale PR or undocumented branch can silently contaminate the V1 freeze.

Scope: fresh open-PR inventory; classify every remaining PR as required-for-V1, parked-post-V1, or superseded/closed. Security/physical PRs #288/#289/#383 remain outside the mandatory path unless a proven V1 blocker requires a bounded delta.

Success: every open PR classified against current master; no half-integrated mandatory feature; no competing roadmap PR remains open; no stale branch is blindly merged.

Proof: inventory + compare/tests where needed + canonical closeout.

V1-06 final result — 2026-09-19:
- canonical reconciliation PR #623 merged as `f05b9dc7c176a5752448793c8a0a585dfb728679`;
- exact-head #623 checks: CI `35435256394` SUCCESS; T2 `35435256380` SUCCESS; Agenda A5 `35435256377` SUCCESS; PR Merge Summary `35435256371` SUCCESS;
- stale/superseded PRs #593, #607 and #575 closed without merge after preservation of their unique evidence;
- remaining open PR set re-proven after merge: #618, #383, #289, #288 only;
- #618 classified PARKED_POST_V1;
- #288/#289 classified PARKED_POST_V1;
- #383 classified HUMAN_GATE_PARKED;
- branch census recorded 404 refs; no destructive mass deletion performed;
- freeze rule: only reconciled `master` and the later exact candidate SHA are canonical; historical branches cannot enter V1 without a fresh compare + explicit classified PR.

Canonical evidence:
- `docs/clinic/audits/V1_06_PREFREEZE_PR_INVENTORY.md`
- `docs/clinic/audits/V1_06_PREFREEZE_BRANCH_CENSUS.md`

V1-06 Success criterion is satisfied. V1-07 is unlocked.

### LOT V1-07 — Master stabilization

Status: **IN_PROGRESS — PRE-FREEZE TRIPLE-CHECK / V1-08 BLOCKED**

Goal: establish a stable pre-candidate master.

Success: required global CI/regressions green; migrations coherent; no known unresolved mandatory V1 blocker; canonical docs coherent; open PR inventory reconciled.

Proof: exact master SHA + required global run IDs + regression evidence + final pre-freeze audit.

Additional mandatory gate approved 2026-09-19:
- Pass 1 broad audit;
- Pass 2 evidence double-check;
- Pass 3 adversarial re-audit;
- every finding classified BLOCKER / MUST-FIX / ACCEPTED-RISK / POST-V1;
- every V1 BLOCKER and MUST-FIX resolved and re-certified before V1-08.

Canonical audit: `docs/clinic/audits/V1_07_PREFREEZE_TRIPLE_CHECK.md`.

Product Owner approved pre-G9 UI/UX integration — 25 September 2026:
- the V1-07 pre-G9 master is intentionally held before G9 so the final semantic reconciliation can include the Document Studio polish below;
- authorized bounded scope: shared odontogram renderer + Patient Clinical odontogram presentation + Devis + Note d'honoraires UX/UI, including the existing read-only PDF preview surface;
- this is a presentation/interaction integration only: FDI contracts, patient odontogram persistence/revision, accounting price/phase/payment policies, archive/rehydration, PDF generation semantics and tenant/data boundaries remain authoritative and must not be weakened;
- existing useful capabilities must be preserved: adult/pediatric dentitions, per-tooth and grouped selection, treatment selector, quick/catalog acts, phase organization, editable accounting rows, total, Preview, Save/Archive, Print, honoraires payment status/modes/installments;
- required sequence before G9: fresh pre-G9 baseline → shared renderer → Clinical → Devis → Honoraires → targeted/transversal regression + BEFORE/AFTER visual evidence → severe scoring/human visual review;
- G9 semantic reconciliation MUST run on the exact resulting product HEAD, not on the prior pre-polish HEAD;
- G10 closeout and V1-08 freeze remain blocked until this bounded scope and all other V1-07 gates are reconciled and certified;
- no Vercel deployment and no real-cabinet mutation are authorized by this amendment.

### LOT V1-08 — Freeze exact V1 candidate

Status: **BLOCKED BY V1-07**

Goal: intentionally select one immutable exact 40-character SHA as V1 candidate.

Success: candidate SHA recorded here and in `docs/clinic/DIGITALCROWN_V1_OBJECTIVE.md`; moving branch names are not install identity.

Rule: any code change after freeze creates a new candidate SHA and restarts candidate certification.

### LOT V1-09 — V0 → V1 installability certification

Status: **BLOCKED BY V1-08**

Goal: certify the locked candidate against a fresh isolated restore of the real cabinet PREUPDATE state.

Success:
- fresh PREUPDATE fingerprints;
- verified PostgreSQL + media/document backups;
- isolated restore;
- exact candidate migrations succeed;
- historical rows/PK/FK preserved, no new orphans;
- document archives resolve;
- media/file manifest preserved;
- second migration no-op;
- app startup + `/api/health` + critical cabinet smokes pass;
- rollback point verified;
- exact candidate reaches `INSTALLABLE_CERTIFIED`.

Proof: complete rehearsal/certification report tied to the exact candidate SHA.

### LOT V1-10 — Real cabinet update + V1 operational closure

Status: **BLOCKED BY V1-09 + EXPLICIT HUMAN AUTHORIZATION**

Goal: install the exact `INSTALLABLE_CERTIFIED` candidate on the real cabinet and prove operational integrity.

Success: explicit authorization immediately before mutation; writes frozen as required; backups revalidated; same locked SHA installed; post-update integrity/startup/critical smokes pass; rollback remains executable; `V1_OPERATIONAL` recorded here.

Proof: installed SHA + POSTUPDATE integrity + health/smoke evidence + rollback identity.

## 5. Unlock / closeout rule

Only one lot may be `IN_PROGRESS` at a time. Lot N+1 unlocks only when lot N has Goal met, observable Success met, Proof captured, impacted tests/CI green, canonical closeout written here, and merge/post-merge completed when applicable.

Pending CI does not unlock the next lot. Independent work is permitted only inside the same unlocked lot.

## 6. Current canonical state

- active lot: **V1-07 — Master stabilization / PRE-FREEZE TRIPLE-CHECK IN PROGRESS**
- previous lot: **V1-06 — Pre-freeze repository reconciliation — CLOSED**
- audit base master: `ceae1624c5f1311eb7ffcf512785b8a30fe438fc`
- V1-07 ordinary stabilization certification was green, but the product owner added a mandatory adversarial triple-check before freeze.
- prior closeout PR #627 was closed without merge as premature.
- canonical objective: `docs/clinic/DIGITALCROWN_V1_OBJECTIVE.md`
- V1-08 freeze: **BLOCKED**
- V1 candidate SHA: **NOT SELECTED**
- installability status: **NOT CERTIFIED**
- V1 state: **EXECUTION LOCKED / NOT OPERATIONAL**
- production/cabinet mutation: **NOT AUTHORIZED**
- Vercel deployment: **NOT AUTHORIZED**
- Next exact: remediate Pass 1 BLOCKER/MUST-FIX findings, then Pass 2 + Pass 3 and exact-head re-certification.

## 7. Maintenance rule

At every lot closeout update this file with exact result, exact evidence/run IDs, relevant PR/merge/master SHA, remaining blocker, newly unlocked lot, and V1 state. Never claim COMPLETE / VERIFIED / INSTALLABLE_CERTIFIED / V1_OPERATIONAL without the corresponding proof.
