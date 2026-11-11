# Digital Crown — Design Reference

**Document:** `design.md` · **Edition:** 0.1 · **Snapshot:** 2026-11-11 (UTC)  
**Decision:** DESIGN-BASELINE-01 · **Nature:** documentation / FUE-0 · **Status:** DRAFT, not merged  
**Repository:** [hraaaaf/Digital_crown](https://github.com/hraaaaf/Digital_crown) · **Observed master at drafting:** `17e4dc381db823cd6a95b1b695dab7700a219faa`

> **Purpose.** Establish a single, navigable design reference for the product, clinical UX, visual language, authorized boundaries and currently active design dependencies. This is a **design map**, not a new execution roadmap, a code certificate, a clinical validation, an installation authorization or a release claim.

## 1. Authorities and interpretation

Consult, in this order, the current runtime/repository and exact HEAD, then [V1.5 canonical roadmap in Notion](https://app.notion.com/p/3e677c66336281d88c82d2fbe43835fb), [AGENTS.md](AGENTS.md), [STATE.md](STATE.md), the domain-specific specification, and the relevant evidence. The [V1 consolidated roadmap](docs/clinic/DIGITALCROWN_V1_CONSOLIDATED_ROADMAP.md) records **V1_OPERATIONAL** and remains historical V1 authority; V1.5+ uses its active canonical roadmap. This document cannot unlock, re-order or certify a lot.

Evidence labels throughout this reference:
- **LOCKED**: explicit project/product decision; verify if superseded.
- **INTEGRATED**: observed on master for the identified scope, not necessarily installed or clinically active.
- **LAB PROVED**: a bounded, synthetic executable test with inspectable evidence; not proof of clinical fitness or cabinet installability.
- **DRAFT / PROPOSED**: isolated PR or design candidate; not merged, delivered or activated.
- **HOLD / UNKNOWN**: the necessary evidence, human gate or implementation is absent.

A PR, screenshot, green CI badge, mockup, stale Notion entry or generated text must never silently promote a feature to an implemented or validated claim.

## 2. Product north star — what Digital Crown is

Digital Crown is a **desktop-first, local-first dental clinic operating system**, with the clinic's local backend as the source of truth. The objective is to reduce clerical friction while preserving patient safety, accurate records, clinician authority and recoverability.

Users and contexts:
- **Practitioner**: chart, clinical chronology, imaging, decisions, documents and follow-up. Clinical interpretation and approval stay with a qualified practitioner.
- **Reception / assistant**: schedule, authorized patient intake, waiting-room progress, payments and operational handoffs. Work interruptions and role permissions matter.
- **Clinic administrator**: staff, configuration, access, local operations, audit, backup/restore and release control.
- **Patient or staff mobile companion**: distinct, narrowly authorized experiences. A mobile route or a screenshot does not imply equivalence to the full desktop product.

**Priority order:** patient safety → confidentiality and data integrity → factual/clinical accuracy → auditable evidence → workflow efficiency → bounded autonomy.

**Design test:** on every significant screen, the user should immediately understand (1) *which patient/context* they are acting on, (2) *which information is authoritative*, (3) *what can safely happen next*, and (4) *why an action is blocked*.

## 3. Approved product boundaries

### Architecture — LOCKED

- On-premise backend and clinic-controlled local/LAN patient data and media. No unapproved remote patient hosting.
- FastAPI/Python backend owns tenant, role, permission, validation, transaction, document and persistence decisions. React/TypeScript is an **untrusted client**.
- Firebase is restricted to the project's authorized identity/licence functions; it is **not** the clinic database.
- V1 has **ZERO LLM clinical/runtime logic**. Crown Bot behaviour is deterministic. ONNX/PyTorch may be used only for explicitly scoped, sourced, validated model functions; model output is never a clinician-approved diagnosis by default.
- Digital Crown Desktop, Pocket/PWA, patient companion, kiosk, wall and Queue are **distinct surfaces and trust boundaries**. Do not equate a synthetic lab facade with a shipped patient-visible feature.
- No Vercel deployment, on-prem release, patient migration, clinical model activation or irreversible operation without the appropriate explicit owner/human gate.

The current technical baseline is described by [ARCHITECTURE.md](ARCHITECTURE.md); for actual behaviour, inspect the code at the exact SHA.

### Desktop vs Pocket — product direction

**Desktop-first**: full clinical and imaging workflow, calibrated cephalometric editing and analysis, advanced scheduling, finance, documents, administration and recovery.  
**Pocket/PWA**: short contextual, role-bound actions, limited authorized reading/capture and explicit offline freshness or pending-state indicators.  
**Patient companion**: separate patient-facing scope, identity, privacy and publishing gate.

The October desktop/PWA functional matrix contains proposals rather than blanket implementation proof: [Notion arbitration](https://app.notion.com/p/3f677c663362817d9155d9bf6145f724). Do not present a proposed Pocket navigation as currently deployed.

### MultiView — approved direction, scope-limited implementation

The owner selected **MultiView across authorized Cabinet Desktop modules**, not a simultaneous two-patient workspace and not a Pocket redesign. Maintain a **single active patient** per workspace. Switching patients requires safe handling of unsaved drafts, pending async work and protected context. Personal layout preferences are per account **and** workstation, without patient/media/credential content.

Source: [LOT07 canonical closeout](https://app.notion.com/p/40277c66336281b6b7ffeeecae6baff9) and [MultiView decision history](https://app.notion.com/p/3f977c66336281648581cad81ea058e9). LOT07's delivered, bounded desktop scope is closed; historical proposals and unmerged specialities are **not** automatically integrated. Physical dual-monitor acceptance belongs to a separate gate.

## 4. Information hierarchy and primary workflows

Use **patient identity and clinical context first**, then next action, then secondary information. Avoid duplicate competing CTAs or falsely authoritative indicators.

| Workflow | On-screen truth | Key safety/design rule |
|---|---|---|
| Open a patient file | Identity, current encounter, allergies/alerts where present, recent activity, active practitioner | Never silently transfer one patient's context into another |
| Consult chronology / clinical record | Observations, findings, hypotheses, confirmed diagnoses and recorded decisions **distinguished** | Missing evidence must remain visible as missing |
| Agenda / reception / Queue | Time, authorised state, resource, arrival evidence, next permissible operation | EN_ROUTE ≠ ARRIVED; no automatic clinical prioritisation |
| Imaging / Céphalo | Source media, calibration, landmarks, construction, measurement, source/norm, uncertainty, clinical validation state | Non-detection ≠ absence; computed measure ≠ diagnosis |
| Documents / prescription | Source of each field, validity, preview, signature/approval and archive status | A generated PDF or archived document ≠ approved clinical decision |
| Honoraires / payments | Amount, status, audit/reconciliation, pending action | Never imply balance or payment settled without authoritative ledger logic |
| Backup / restore / administration | Target, scope, last verified proof, impact, rollback and permissions | A backup command alone ≠ restorable backup |

Workflow transitions must preserve context and bring the **next required interaction into view** without users hunting or scrolling. Confirmation overlays remain usable on small laptop screens and return keyboard focus. Reference: [UX Continuity Goal](docs/ux/DIGITAL_CROWN_UX_CONTINUITY_GOAL_UI.md).

## 5. Interface behaviour contracts

1. **Visible status with words, not colour alone.** Distinguish loading, empty, incomplete, stale, pending, failed, blocked, saved and approved. A request that failed must never appear saved.
2. **Patient and practitioner context always explicit** on sensitive screens. Context changes invalidate stale in-flight responses and prevent cross-patient draft leakage.
3. **Role-bound actions.** Hide or disable only with a truthful reason; the backend independently enforces every permission and tenant boundary.
4. **Reversible where feasible.** Confirm destructive actions with object identity and impact, safe cancel and focus return. Never imply a rollback path unless actually available.
5. **Information density without ambiguity.** Desktop should optimize clinical scanning, not reduce usable space through decorative chrome, excess spacing or repeated panels.
6. **No fake assistance.** No autonomous diagnosis, suggested prescription, treatment or clinical norm without an approved scientific contract and human activation.
7. **Provenance at point of use.** Distinguish observed data, imported/legacy content, computed values, suggested interpretations and clinician-approved decisions.
8. **Failures fail closed.** Contradictory, missing, unauthorized or uncalibrated clinical inputs block only the dependent claim, not unrelated verified data.
9. **Do not expose PHI in screenshots, logs, CI fixtures, URLs, analytics or external services.** Synthetic fixtures and scrubbed evidence only.
10. **Respect the task, not the theme.** Visual sophistication is subordinate to clarity, accessibility and real workflow completion.

The clinical R11→R14 studio explicitly distinguishes calculability, evidence, interpretation, actions and archiving: [Céphalo R15 Studio UX](docs/CEPHALO_R15_STUDIO_UX_UI.md).

## 6. Existing visual system — verified source, not an invented redesign

**Current implementation source:** [frontend/src/index.css](frontend/src/index.css), theme-related CSS and domain theme modules. Use semantic CSS tokens, not hardcoded palette-specific component colours.

Observed default-theme token examples on the 2026-11-11 master:

| Design meaning | Implemented token | Current default value |
|---|---|---|
| Primary action | `--primary` | `#003380` |
| Primary background | `--bg-medical-pearl` | `#f8fafc` |
| Main text | `--text-main` | `#0f172a` |
| Muted text | `--text-muted` | `#475569` |
| Card surface | `--card-bg` | `white` |
| Border | `--border-color` | `#e2e8f0` |
| Success / danger / warning | `--status-success`, `--status-danger`, `--status-warning` | `#047857`, `#be123c`, `#b45309` |
| Sans / display | `--font-sans`, `--font-outfit` | Inter / Outfit |
| Radius primitives | `--radius-elite-sm`, `--radius-elite`, `--radius-elite-lg` | 16 / 24 / 32 px |

Styles define named theme variants including emerald, rose, prestige, ocean, graphite and dark, in addition to the default root. Their **presence is not universal contrast or visual certification**. Prefer existing variables for foreground/background, borders, inputs, alerts, focus and glass effects; reduce visual noise on dense clinical surfaces.

**Accessibility:** readable hierarchy, robust keyboard/focus behaviour, high-contrast actionable states, no colour-only clinical semantics, proper errors and reflow, respect for reduced motion. Validate 200% text scaling where relevant. WCAG 2.2 is an engineering benchmark; do not claim blanket legal certification.

**Visual evidence:** BEFORE → written Goal → reference/target → implementation → AFTER at identical relevant viewports → functional/accessibility tests → comparison → score/decision. Typical widths: 390, 430, 768, 1280 px; for workstation-dense flows also inspect 1366×700 and 1440×900 when applicable. A documentation-only FUE-0 does **not** need fabricated UI captures.

## 7. Céphalo and orthodontic evidence contract

**Intent:** a supervised clinical **workspace**, not an AI dentist. Preserve the chain:
source image → acquisition/calibration → anatomical points → geometric constructions → calculations → validated reference profile → interpretation limits → practitioner decision → consistent UI/API/DB/PDF.

Mandatory distinctions:
- A mapped SRPose38 channel label does **not** prove an anatomical landmark.
- A model's localisation score is not proof that a clinical measurement is interchangeable with human tracing.
- A non-calibrated image cannot silently yield reliable linear millimetres.
- Contradictory landmark conventions, source definitions or norms remain explicit.
- Manual correction triggers recalculation of all **dependent** values and outputs.
- A missing/non-computable value is **never** replaced with zero.
- The proposed orthodontic objectives checklist is documentation only until implemented and clinically approved.

Canonical domain references: [Céphalo diagnostic specification](docs/CEPHALO_DIAGNOSTIC_SPEC.md), [SRPose38 landmark contract](docs/SRPOSE38_LANDMARK_CONTRACT.md), [scientific concordance R18](docs/CEPHALO_R18_SCIENTIFIC_CONCORDANCE.md), [Céphalo roadmap](https://app.notion.com/p/3ec77c663362811db11ec59dbd9eb7d3), [Orthodontiste agent contract](.claude/agents/Orthodontiste.md) where present on the checked ref.

**Design debt, independently noted 2026-11-11:** draft #1284's 9 synthetic screenshots are dark-theme-only; light-theme evidence is missing; the desktop lexicon panel is narrow and the mobile expanded panel displaces radiography. Do **not** promote the historic 8.7/10 lexicon review to light/dark or installed-workstation UX validation. [Notion clinical roadmap](https://app.notion.com/p/3ec77c663362811db11ec59dbd9eb7d3).

## 8. Queue / arrival / waiting-room design contract

The stand-alone Queue domain distinguishes `PLANNED`, `EN_ROUTE`, `WAITING`, `CALLED`, `CHAIR`, `DONE`, `CANCELLED`, `NO_SHOW`; `ARRIVED` is an audited **event**, not a visit status. Clinic staff control exceptional actions with recorded actor, permission and reason. No autonomous clinical prioritisation, no client-authoritative ranking and no patient identity broadcast on a wall/kiosk by default.

A queue call must be based on the server's **complete tenant-authorized queue snapshot** under transaction control. For a given visit, accepted transition + relevant event must be atomic; rejected command must not alter persisted visit or event state. Current candidate SQLite event immutability guards only prevent ordinary SQL UPDATE/DELETE on protected fresh databases; they do not defend against a privileged OS/DDL adversary.

Source: [Queue core domain contract](docs/v1.5/V15_08_1_QUEUE_CORE_DOMAIN_CONTRACT.md) and [V1.5-08 Notion](https://app.notion.com/p/3ec77c66336281d59cdcffe610561f86). The standalone Queue runtime, genuine installable, retention/purge and cabinet-facing integration remain separately gated.

## 9. Live portfolio snapshot (not an execution-order override)

**As checked 2026-11-11 around 13:00 UTC:** GitHub `master@17e4dc381db823cd6a95b1b695dab7700a219faa`; open PRs below remain DRAFT/unmerged unless explicitly indicated. Re-check their HEAD, CI and merge gate before action.

| Stream | Observed state and evidence boundary | Next gate, not automatically authorized |
|---|---|---|
| V1 / cabinet baseline | Historical `V1_OPERATIONAL` in consolidated V1 roadmap. Not a certificate of the current V1.5 experimental features. | Cabinet release proof on exact target package |
| V1.5 LOT07 / MultiView | Bounded delivery closed, source integrated, documented exclusions (speciality R3 / physical monitor). [Closeout](https://app.notion.com/p/40277c66336281b6b7ffeeecae6baff9) | Separate scope + real FUE/physical evidence for excluded work |
| V1.5 LOT08.2 / Queue | Source and synthetic lab integration merged via [#1292](https://github.com/hraaaaf/Digital_crown/pull/1292), handover via [#1289](https://github.com/hraaaaf/Digital_crown/pull/1289); **not installed-product certification**. | Genuine installable Windows FUE and product gate |
| V1.5 LOT08.3-A / immutable event log | [#1294](https://github.com/hraaaaf/Digital_crown/pull/1294) DRAFT on `34e38ebb9840cd0b990ad32187d632ede725ac6f`. Linux 219 passed / 3 skipped; Windows 3 passed / 15 deselected, and scope checks green on exact PR HEAD. Broader 08.3 **OPEN**. | Full applicable CI, owner merge GO, then independent 08.3-B retention/migration/recovery lot |
| LOT05 / legacy interoperability | 2A synthetic source inventory [#1254](https://github.com/hraaaaf/Digital_crown/pull/1254) merged; 2B **direct synthetic MariaDB CSV** [#1269](https://github.com/hraaaaf/Digital_crown/pull/1269) merged and postmerge tested. Neither is native Open Dental GUI CSV or patient migration. | Native permissions/provenance and migration-specific gates |
| LOT05 / 2C fictional mapping | [#1293](https://github.com/hraaaaf/Digital_crown/pull/1293) DRAFT on `42326121cc40c2e9d9a17e068b7b2d74a37f36ab`; 9 FUE-0 tests each on Linux/Windows succeeded according to current Notion POST. A transverse candidate regression [#43021912091](https://github.com/hraaaaf/Digital_crown/actions/runs/43021912091) was still IN_PROGRESS at observation. `import_permitted=false`. | Resolve required CI, distinct owner merge GO, later semantic/collision/restore validation before real migration |
| Céphalo J1.B1 / SRPose38 lexicon | [#1284](https://github.com/hraaaaf/Digital_crown/pull/1284) DRAFT; branches #1276–#1283 have dependencies; 38 channels + 2 constructions **informative**, no automatic anatomical/clinical certification. [#1290](https://github.com/hraaaaf/Digital_crown/pull/1290) orthodontic objectives: DRAFT documentation only. | Evidence on light/dark and desktop; owner visual gate, source/clinical approval; integration decision |
| Pocket V2 / CPV2-02C | Isolated draft PRs [#1201](https://github.com/hraaaaf/Digital_crown/pull/1201), [#1224](https://github.com/hraaaaf/Digital_crown/pull/1224); integration/production not established by these drafts. | Security/integrity regression, exact-head evidence, explicit merge/release gates |
| LOT09 and beyond / V2 modules | External integration, clinical automation expansion and later modules are **not activated by this document**. | Follow canonical dependency order and explicit product/human gate |

**Portfolio risk:** many historical and parallel open DRAFT PRs create a high risk of stale-base assumptions and accidental promotion of lab code. Prefer **one decision and one exact source-of-truth HEAD per execution**, reconcile dependencies before any merge, and archive superseded exploratory PRs only with exact evidence.

## 10. Design decision rules for a new feature

Every significant UI/workflow proposal should have one compact decision record:
1. **Decision ID + name;** canonical roadmap lot and owner-approved scope.
2. **Problem and target user;** actual observed BEFORE and task frequency/criticality.
3. **Goal / SUCCESS / PROOF;** meaningful positive and negative journey, independent oracle.
4. **Authority boundary;** source data, patient/tenant identity, RBAC, clinical vs operational authority, local/offline state.
5. **Alternatives;** keep/simplify/rework/move/delete, plus a defensible reason for choosing.
6. **Design contract;** states, permissions, errors, destructive actions, drafts, keyboard/focus, empty/loading/failed/stale data, themes and relevant viewports.
7. **Build and verification;** minimal delta on isolated branch, exact-HEAD tests, required FUE-0/I/G and risk-specific proofs, observed AFTER if UI.
8. **Human gate and closeout;** what remains unverified, explicit GO before merge/release/clinical action, final status and Notion/STATE linkage.

A feature is not DONE because its interface looks attractive; it is DONE only when the **authorized scope** reaches an observable outcome without unresolved required safety, data, clinical, permissions or evidence blockers.

## 11. Current design follow-ups (candidates, not a competing roadmap)

- **P0 — truthfulness and integration discipline:** no lab-only claim on patient surfaces; consolidate dependent PR/CI status into the active lot, preserve exact-SHA proof and protect patient boundaries.
- **P1 — Céphalo legibility:** verify the informational landmark panel in *real light and dark* across relevant desktop widths, with 200% scaling, before owner visual acceptance; keep clinical activation separately gated.
- **P1 — Queue clarity:** only after server/retention and installable gates, design human-readable arrivals, exceptions, privacy-safe kiosk/wall behaviour and the right permissions with an actual end-to-end FUE.
- **P1 — practical desktop efficiency:** favor scan-friendly layout, fewer duplicate actions, visible next steps and one-patient MultiView context. Validate on real constrained workstation viewports.
- **P2 — Pocket refinement:** only for explicitly authorized mobile tasks. Do not transplant the entire desktop cephalometry or advanced administration surface.

These are **design recommendations**, not permission to start later lots or change the canonical sequence.

## 12. Definition of ready, done and maintenance

**DESIGN READY:** owner-scope and roadmap dependency known, real target route/workflow identified, authority and clinical risk mapped, test oracle and user-visible success defined.

**IMPLEMENTED:** code exists on an exact reviewed SHA and the behavior is reachable under the intended auth/state; a DRAFT branch by itself is not integration.

**VERIFIED for evaluated scope:** applicable FUE evidence really executed, assertions and negative cases inspected, final HEAD identified, required specialty controls green, actual UI AFTER observed if claimed. Passing tests never certifies legal or clinical safety alone.

**RELEASED / CABINET-READY:** separately needs a traceable signed/integrity-checked artifact, applicable Windows install/upgrade/recovery evidence, a real restore drill where required, required physical/human acceptance and explicit deployment/installation approval.

**Maintenance rule:** update this document **only** for a new supported design decision or verified state transition. Preserve the date, source link, exact scope and evidence; do not turn it into a running PR micro-log. For changing PR/CI facts prefer the linked canonical Notion roadmap and `STATE.md`; refresh the snapshot here when a material design dependency changes.

### Source index

- [AGENTS.md](AGENTS.md), [STATE.md](STATE.md), [ARCHITECTURE.md](ARCHITECTURE.md)
- [V1 consolidated roadmap](docs/clinic/DIGITALCROWN_V1_CONSOLIDATED_ROADMAP.md), [V1.5 canonical roadmap](https://app.notion.com/p/3e677c66336281d88c82d2fbe43835fb)
- [Product & Design Compass](https://app.notion.com/p/3df77c66336281f9a130d15b13320ab9)
- [LOT07 / MultiView](https://app.notion.com/p/40277c66336281b6b7ffeeecae6baff9), [Queue LOT08](https://app.notion.com/p/3ec77c66336281d59cdcffe610561f86)
- [Céphalo PREMIUM](https://app.notion.com/p/3ec77c663362811db11ec59dbd9eb7d3)
- [frontend CSS tokens](frontend/src/index.css), [UX continuity goal](docs/ux/DIGITAL_CROWN_UX_CONTINUITY_GOAL_UI.md)
