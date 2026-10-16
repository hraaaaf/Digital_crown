# CB-00 — Crown Bot PRODUCT_TRUTH (baseline 2026-10-16)

**STATUS: OPEN — B selected as TARGET; isolated synthetic CI HTTP/DOM measurements and cross-tenant 404 now obtained, but real cabinet UX evidence and B implementation are incomplete.**
**Reference (not to mutate):** [PR #894](https://github.com/hraaaaf/Digital_crown/pull/894), source HEAD `9cf19e68026fa92d31fb704f5b81b9cd667e5254`, DRAFT / unmerged. Source canonical plan: [Crown Bot 2.0 Notion roadmap](https://app.notion.com/p/3fb77c66336281dda0a3d295c5625d95). This doc branch is **separate**, not an amendment to certified #894.

## Truth matrix — source HEAD

| Capability | Backend exists? | Currently usable in Cabinet UI? | Flagged preview | Proof / limitation |
|---|---|---|---|---|
| Ghost Brain contextual alerts, mark-read, patient link | yes | yes when alerts exist | n/a | React ack tests; actual alert quality not measured |
| Patient by name, dossier, agenda, finances, lab, stats, alerts | classic `/api/bot/chat` and dispatcher yes | **NO**: Chat tab disabled flag OFF | `/patient` **numeric ID only** | code paths exist ≠ shipped UX |
| Real booking/status mutation with confirm, CAS, audit | yes | **NO** accessible Chat pathway | **NON-EXECUTABLE** | real PostgreSQL+SQLCipher HTTP E2E in [gate #38883675681](https://github.com/hraaaaf/Digital_crown/actions/runs/38883675681) |
| Prescription/devis editor suggestions | classic bot code yes | **NO** accessible Chat pathway | `/devis` proposal only; no prescription | explicit human confirmation, no autonomous clinical decision |
| Conversation history/streaming | classic bot yes | current Chat control disabled | ephemeral 8-turn deterministic preview | streamed response not token-by-token generative |
| Free-form multilingual/Darija, voice, autonomous diagnosis | **not demonstrated** | NO | NO | outside baseline |
| Pocket Assistant | placeholder | **« En cours de construction »** | NO | Pocket is distinct device-paired JWT /mobile surface |

**Flags remain OFF by default:** `VITE_CROWN_BOT_WORKFLOW_PREVIEW_ENABLED` and `CROWN_BOT_DETERMINISTIC_WORKFLOWS_ENABLED`. Preview commands exact `/patient`, `/rdv`, `/devis`; returns only read-only proposal, no pending action ID, no `/bot/execute`.

## Twelve synthetic product tasks — protocol, not claimed executed as human UX

| ID | Persona / task | Expected user outcome | Existing evidence / gap | Risk |
|---|---|---|---|---|
| S01 | Dentiste: « agenda demain » | accurate schedule in ≤2 interactions | dispatcher CODE, current Chat unreachable | MEDIUM |
| S02 | Dentiste: search Mme Benali, two matching identities | clear disambiguation, no wrong patient | backend search CODE, no selection in preview | HIGH |
| S03 | Dentiste: `/patient` + synthetic ID | scoped patient read, no writes | **Synthetic CI PASS** for complete authorized read + 30 HTTP warm and 30 DOM warm at 1280/1440/1920, no executable proposal; not staff workflow | HIGH |
| S04 | Dentiste: natural-language patient name in preview | results by name | **UNSUPPORTED** in preview | MEDIUM |
| S05 | Accueil: propose tomorrow 10am 30min | recap and no write until confirmation | **Synthetic HTTP preview PASS**: separate Accueil role with patients+agenda rights, confirmation-required without proposal, then non-executable 10:00 / 30min consultation proposal; no appointment/pending action count change, [run #38942585020](https://github.com/hraaaaf/Digital_crown/actions/runs/38942585020). Availability and staff UX **not tested** | HIGH |
| S06 | Accueil without agenda permission: `/rdv` | fail 403, no patient data | **Synthetic HTTP PASS**: Accueil patients=true, agenda=false; `/rdv` short AND full patient/slot/CONFIRMER transcript return generic 403 with no leak, [run #38942585020](https://github.com/hraaaaf/Digital_crown/actions/runs/38942585020). Human UX **not tested** | CRITICAL |
| S07 | Dentiste: consecutive 08:00–08:20 / 08:20–08:40 | accept both, real overlap 409 | real PG+SQLCipher synthetic HTTP PASS #38883675681 | HIGH |
| S08 | Dentiste: crown quote tooth 46 | proposal/editor only on explicit confirm | **Partial synthetic HTTP PASS**: owner `/devis` + patient ID + `couronne` requires confirmation, returns `OPEN_DEVIS_EDITOR` / `draft_only=true` without executable action ID, [run #38942585020](https://github.com/hraaaaf/Digital_crown/actions/runs/38942585020). **Tooth 46 unsupported in preview schema**; no real quote editor or staff UX tested | HIGH |
| S09 | Dentiste: stale pending status ABA | reject 409 and unchanged real booking | real PG+SQLCipher HTTP PASS #38883675681 | CRITICAL |
| S10 | Accueil: 409 during workflow | clear reconciliation, no automatic replay | Vitest 409, human recovery NOT TESTED | HIGH |
| S11 | Another cabinet: request patient ID | deny without patient leak | **Synthetic HTTP PASS** on a DB-existing foreign patient + unknown ID, identical 404 response, [run #38930309390](https://github.com/hraaaaf/Digital_crown/actions/runs/38930309390); full staff/UI matrix missing | CRITICAL |
| S12 | Dentiste: mark a relevant Ghost Brain alert read | ack only after server success | React tests PASS; actual clinical usefulness unmeasured | MEDIUM |

All cases use fictitious fixture values. **0/12 complete end-to-end human-UX repetitions measured**, not « 0/12 feature works ».

### Latest exact-HEAD CB-00 synthetic evidence (2026-10-16)
**Source:** [PR #902](https://github.com/hraaaaf/Digital_crown/pull/902), tested SHA `dcc0709aaef96c5f926217fd16447115b986d713`; [Scope #38942584883](https://github.com/hraaaaf/Digital_crown/actions/runs/38942584883), [Probe Guard #38942584960](https://github.com/hraaaaf/Digital_crown/actions/runs/38942584960) (**36 pytest PASSED**) and [isolated synthetic Desktop/API #38942585020](https://github.com/hraaaaf/Digital_crown/actions/runs/38942585020) all SUCCESS. **None of these is human staff E2E or an implemented B UI**.

- Live isolated preview route checks: `s05_reception_rdv_proposal_only=PASS`, `s08_crown_draft_proposal_only=PASS`, `s06_no_agenda_403=PASS`, `s06_full_proposal_denied_403=PASS`, `foreign_patient_404=PASS`, `foreign_unknown_same_404=PASS`.
- Synthetic API completed useful patient read **30 warm**, p50/p95 **3.83/3.97 ms**. Existing *flagged* preview click→useful DOM, 30 warm per width: **1280×900 110.34/166.53 ms**, **1440×900 112.48/147.09 ms**, **1920×900 142.64/154.99 ms** (p50/p95). Results are CI-only, not clinic performance or B.
- Counts for Appointment and BotPendingAction unchanged after preview; **not** a full DB-delta proof. CI artifact `cb00-synthetic-desktop-evidence` ID `12064176618`, available on [run #38942585020](https://github.com/hraaaaf/Digital_crown/actions/runs/38942585020), reported expiry **2026-10-30**.
- Outstanding: real user/baseline BEFORE→implemented B AFTER at same desktop widths, browser zoom 200% / keyboard, 12 complete staff scenarios, clinical slot availability, quote tooth-number context, cold-start, exhaustive DB diff, distinct adversarial reviews, final owner exit decision.


## BEFORE status (actual current app)
- Earlier genuine **Cabinet Web 1280×900** before/after *interaction-state* screenshots are in [synthetic browser visual #38883675591](https://github.com/hraaaaf/Digital_crown/actions/runs/38883675591), artifact `12039871284`. This is NOT a before/after release-change comparison.
- **New synthetic CI** captured the existing **flagged preview interaction** at **1280×900, 1440×900 and 1920×900**, [run #38930309390](https://github.com/hraaaaf/Digital_crown/actions/runs/38930309390), artifact `12058073801`. This is **not** the actual cabinet flag-OFF BEFORE, nor an AFTER for the chosen B sidecar. Never relabel it as such.
- On actual 1280 image the panel is ~396px wide, blue identity consistent; user sees « Simulation ZERO-LLM — aucune écriture » and exact slash commands, then asks for numeric patient ID. Technical language and multi-step flow precede useful clinical result.
- **Synthetic preview only**, p50/p95 now measured for **authorized useful read**: HTTP **3.09 / 3.27 ms** (30 warm), click→useful-DOM **1280: 89.87 / 130.97 ms**, **1440: 103.04 / 136.39 ms**, **1920: 110.27 / 124.45 ms** (30 warm each), [run #38930309390](https://github.com/hraaaaf/Digital_crown/actions/runs/38930309390). This is not product release / real clinic latency. Previously measured 0.7–2.1ms are synthetic **appointment SQL conflict queries**, not Crown Bot.

## Measurement contract — REQUIRED to close CB-00
Use **authorized synthetic localhost T2 only**, never patients or live server. Record CPU/RAM/OS/browser, PR SHA, fixture ID, cold first-request, 30 warm repetitions, p50/p95 by `performance.now` or monotonic clock for **HTTP full response** and **click-to-useful-DOM**, load/panel open, retries/errors, and interaction counts. Target desktop **1280/1440/1920**, keyboard and 200% browser zoom in scope. 390/430 are safety smoke of web fallback only, not Pocket UX acceptance. Deny any /bot/execute or appointment write during preview.

| Metric | State | Initial proposed goal (NOT measured) |
|---|---|---|
| Preview API first / 30 warm p50,p95 | **MEASURED synthetic CI** first useful 3.99 ms; warm p50/p95 **3.09 / 3.27 ms**, n=30 at HEAD `c398ba2` | synthetic baseline only |
| Browser click → useful DOM p50,p95 | **MEASURED synthetic CI** 30 warm at each 1280/1440/1920; p95 **130.97 / 136.39 / 124.45 ms** | read p95 ≤2 sec (synthetic target; not human usability) |
| Initial assistant open p50,p95 | **SINGLE open samples only** 206.80 / 150.22 / 192.74 ms at 1280/1440/1920; **p50/p95 NOT MEASURED** | warm p95 ≤1 sec |
| Proposed booking (once actionable) | **NOT MEASURED** | p95 ≤3 sec; clinical integrity first |
| 12 synthetic staff journeys | **NOT EXECUTED** end-to-end | ≥90% pilot success after implementation |

## Three UI TARGET directions — concepts only, not shipped
Scored heuristically on common rubric: time-to-value 30%, identity/error clarity 25%, readability/keyboard 20%, action safety 15%, reversibility 10%. **Owner explicitly selected B on 2026-10-16**; these scores are not usability or implementation validation.

| Direction | Shape | Benefit | Trade-off | Preliminary /10 |
|---|---|---|---|---|
| A Quick Panel | compact contextual floating ~420px | shortest transition from current popover | complex booking may not fit | 8.1 |
| **B Associate Sidecar (recommended for review)** | stable 480px right pane, patient identity, step progress, explicit confirmation | continuous context, visible review + errors | reduces clinical workspace width | **8.8** |
| C Task-first Workspace | full task view with 3 columns and confirmations | best density for complex multi-step tasks | larger navigation change | 8.5 |

**Owner decision DONE (2026-10-16): B — Associate Sidecar is the Cabinet Web Desktop TARGET.** This is not permission to merge/activate; Pocket remains separate and en cours de construction. [CB-00 B handover](CB00_B_GO_EXECUTION_HANDOVER_20261016.md).

## CB-00 status / gates
**Completed:** HEAD inventory, source-traceable 12 scenarios, chosen B TARGET, synthetic CI HTTP useful-read p50/p95, synthetic DOM p50/p95 and screenshot interaction states at three desktop widths, genuine existing 1280 earlier reference, and **DB-existing cross-tenant 404 identical to unknown 404** ([run #38930309390](https://github.com/hraaaaf/Digital_crown/actions/runs/38930309390)). 19 guard tests passed on [run #38930309404](https://github.com/hraaaaf/Digital_crown/actions/runs/38930309404); synthetic Appointment/BotPendingAction row counts unchanged. **OPEN / BLOCKED:** true process cold-start; real product flag-OFF BEFORE 1440/1920; full DB diff; all 12 staff E2E journeys and role-agenda S06; keyboard/200% zoom; B UI implementation/AFTER; 2 distinct adversarial reviews and real workstation T2.

**NEXT exact / HIGH:** preserve [PR #902](https://github.com/hraaaaf/Digital_crown/pull/902) DRAFT and [PR #894](https://github.com/hraaaaf/Digital_crown/pull/894) separate; run remaining 12 staff E2E scenarios with real user result/role evidence, 200% zoom/keyboard, real cabinet flag-OFF BEFORE and B AFTER at 1280/1440/1920, true startup and DB diff on authorized isolated workstation, then adversarial review before considering CB-00 closure. No release, merge, production flag, deployment or Pocket code.
