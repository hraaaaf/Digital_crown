# Digital Crown V1.5 — Independent Reviewer Routing (canonical lot matrix)

Version: 1.0 · 2026-11-04 · **DOCUMENTARY CANDIDATE** · No clinical activation, merge or deployment permission.

## 0. Scope and authority

Canonical lot definitions: [Digital Crown V1.5 ROADMAP UNIQUE](https://app.notion.com/p/3e677c66336281d88c82d2fbe43835fb), lots V1.5-00 through V1.5-10. Read actual HEAD, current lot handover and `AGENTS.md` before use. The historically closed V1 roadmap is NOT the operative V1.5 plan. This file is the **single reviewer-routing matrix**; do not replicate lot-level lists in AGENTS/CLAUDE.

Seven specialized reviewer agents are read-only and independent of the implementing agent. **They are not independent human reviewers just because distinct names exist**: use a separate invocation/personnel with actual evidence; disclose same-model/self-review limits. Reviewers have neither clinical authority nor permission to mutate records, production, CI gating policies, deployment or merge. Their output is advisory/risk-evidence only.

Existing scientific specialists are reused when relevant: `scientific-reviewer`, `scientific-test-engineer`, `orthodontiste` (candidate on draft PR #1209, **not yet on master**), `radiology-engineer`, `cephalometry-engineer`, `clinical-diagnosis-engineer`, `pharmacology-engineer`. The new `reviewer-imaging-acquisition` audits device ingestion rather than performing radiological diagnosis.

## 1. Reviewer registry

| ID | Agent file | Boundary |
|---|---|---|
| SEC | `.claude/agents/reviewer-access-privacy.md` | RBAC, object/tenant isolation, sessions, QR/NFC, PHI exposure |
| DATA | `.claude/agents/reviewer-migration-integrity.md` | migration, reconciliation, idempotence, patient/media/financial integrity |
| OPS | `.claude/agents/reviewer-workstation-recovery.md` | on-prem roles, Windows/LAN, install, backup/restore, recovery |
| IMG | `.claude/agents/reviewer-imaging-acquisition.md` | photo/radio ingestion, modality metadata, DICOM, patient association |
| DOC | `.claude/agents/reviewer-patient-documents.md` | eligibility, approved content, PDF, printing, delivery/purge |
| QUEUE | `.claude/agents/reviewer-queue-consistency.md` | queue transitions, events, retries, idempotence, integrations |
| UX | `.claude/agents/reviewer-ux-accessibility.md` | real workflow usability, FR/AR/EN, theme tokens, 200%, accessibility |

These are **available reviewers**, not seven mandatory approvals per pull request. The reviewer must not author the change under review. Invoke the minimal set **triggered by changed risk surface** and annotate `REQUIRED / CONDITIONAL / OUT_OF_SCOPE`. An independent reviewer is required only when the applicable lot/human/clinical/security gate explicitly requires one; never replace actual executable tests or certified field acceptance with a simulated second persona.

## 2. Canonical lot-to-risk matrix

| Lot V1.5 | Canonical feature scope | Primary reviewer | Add on actual risk trigger | Non-negotiable validation |
|---|---|---|---|---|
| **00 Hub & Dispatcher** | Hub shell, roles/workstation routes, device mode | SEC | UX, OPS | RBAC, denied routes, Hub navigation, appropriate FUE-I/G visual |
| **01 Cabinet topology** | Server, annex PCs, LAN discovery/restart | OPS | SEC | 2-PC+server real topology when required; reconnect/restart/latency; simulated != field |
| **02 Patient photo & identity** | Canonical photo source, capture/crop, UI propagation | SEC | IMG, UX, DATA | Correct patient association, tenant/RBAC, cache/delete and image fallback |
| **03 Station / kiosk foundation** | Locked kiosk, pairing, QR/NFC, arrival, wall calls | SEC | QUEUE, UX, OPS | Anti-replay, public/private boundary, short sessions, no autonomous queue engine in LOT03 |
| **04 Self-service documents** | Whitelist, staff-presence proof, pre-approved care sheet, print/Pocket | DOC | SEC, UX, OPS | Never edit clinical content in station; short token, purge, print, exact PDF |
| **05 SQL Migration Wizard** | Inspector, source mappings, dry run, patients, finance, documents, rollback | DATA | OPS, SEC; clinical specialist if clinical semantics imported | Independent record/financial reconciliation, double run idempotence, tested isolated restore |
| **06 Imaging Acquisition Gateway** | Local hot-folder, camera, TWAIN/DICOM, patient linking, retries | IMG | SEC, OPS, DATA; radiology specialist if clinical reading affected | Correct patient / acquisition metadata, malformed files, duplicates, device trial for LOT10 |
| **07 Theme Packs & Motion** | Semantic tokens, theme switch/persistence and accessibility | UX | SEC only if persistence/auth changes | Theme token inheritance (no palette hardcode); BEFORE/AFTER, contrast, 200%, reduced motion |
| **08 Autonomous Queue Core** | Standalone state machine, operators, event log, idempotent API | QUEUE | SEC, DATA, UX | Concurrency, duplicate arrival, offline replay, tenant isolation, real events |
| **09 Queue Integrations** | Digital Crown / Pocket / station / wall integration | QUEUE | SEC, DOC, UX, DATA | Patient/RDV source authority, webhook retries, anti-replay, wall minimization |
| **10 Field certification** | Installation, standalone queue, SQL migration, acquisition device, docs, integrations, security | OPS | SEC + domain reviewer matching each actual test: DATA/IMG/DOC/QUEUE/UX | **Physical witnessed test** with authorized real devices, complete evidence, actual rollback/restore, owner human gate; CI alone cannot PASS |

**Current roadmap warning:** canonical Notion historical paragraphs sometimes retain `CURRENT` labels from earlier dates, so inspect recent LOT07/handover and live PR/HEAD before describing *present* product progress. This routing document is not an execution-unlock decision, does not imply previous lots are reopened, and does not change existing required gates.

## 3. Role allocation and collision policy

1. **Reviewer is not implementer**: reviewer outputs findings/evidence; authors patch on a distinct assignment. A language model running two prompts on the same uninspected evidence is an internal adversarial method, not independent external review.
2. **Scientific meaning routes to existing specialists**; new reviewers review engineering safety boundary. Never silently promote `Orthodontiste.md` from PR #1209 into master or claim it installed there.
3. **SEC is a conditional cross-cutting reviewer** on privacy/authorization changes, not an automatic extra reviewer for a pure visual label edit. **UX is conditional** where actual user flows and perceptible states change.
4. **High-risk patients/data/security** require targeted negative tests and authorized human decisions even if no reviewer is invoked. An independent reviewer alone is insufficient. Tests and reviews are orthogonal.
5. **No medical device, compliance or safety certification claim** from these docs. Human clinical sign-off, CNDP/legal assessment and physical gate must be demonstrated separately when applicable.
6. No patient identifiers in GitHub, Notion, prompts, logs, fixtures or external services. Local-first and V1 ZERO-LLM clinical runtime unchanged. No Vercel without explicit user GO.
7. For UI, only use theme semantic tokens from `frontend/src/index.css`; avoid theme-specific palette literals. The reviewers may flag violations but cannot implement fixes.
8. A reviewer says `PASS_TECHNICAL` only for an inspected exact-HEAD scoped claim; `NOT_RUN` / `UNKNOWN` for missing evidence; `CHANGES_REQUIRED` / `BLOCKED` for unresolved MAJOR/BLOCKER. No score overrides missing proof.

## 4. Per-lot reviewer call contract (copy, do not invent)

`LOT / SUBLOT / CHANTIER / SHA / DIFF / ACCEPTANCE CLAIM / INPUT EVIDENCE / HUMAN GATES / FUE LEVEL`

Reviewer returns `FINDING_ID / SEVERITY / EVIDENCE FILE+LINE OR ARTIFACT / IMPACT / REPRODUCTION / REFUSAL CASE / REMEDY / REQUIRED RETEST / STATUS`.

After correction, compare actual new HEAD, retest affected evidence and have the distinct reviewer recheck only invalidated claims. Do not silently reclassify `UNKNOWN` as `PASS`.

## 5. FUE and evidence gates

- FUE-0: Markdown/contract/validator and independent static-oracle verification only. Do not fake UI screenshots.
- FUE-I: actual isolated intermediate workflow with synthetic actors and APIs; negative permissions and meaningful interaction.
- FUE-G: actual end-to-end UI/API/auth/persistence pathway when the lot affects it. Capture BEFORE → ACTION → AFTER plus inspectable artifacts as appropriate.
- LOT10: hardware/Windows/LAN/printer/camera/QR/NFC and field witness **NOT_RUN until physically exercised**, irrespective of prior lab/CI success.
- Report actual GitHub Actions runs with run URLs, final exact HEAD, executed/skipped tests and what each run covers. Do not turn a scope classifier into a scientific gate.

## 6. Maintenance

Update this **one matrix** when the Notion roadmap's lot scope or canonical owner changes; keep `AGENTS.md` and `CLAUDE.md` as short router pointers. Re-check all existing specialist names and schema contracts before adjusting the scientific validator. For each significant mission, Notion PRE → execute → FUE/negative evidence → Notion POST, no micro-journal. Any new agent defaults to read-only unless explicitly authorized otherwise.
