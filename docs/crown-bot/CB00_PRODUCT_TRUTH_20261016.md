# CB-00 — Crown Bot PRODUCT_TRUTH (baseline 2026-10-16)

**STATUS: OPEN — inventory and target alternatives completed; actual performance/desktop evidence incomplete.**
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
| S03 | Dentiste: `/patient` + synthetic ID 7 | scoped patient read, no writes | preview Vitest + real browser proof, no p95 | HIGH |
| S04 | Dentiste: natural-language patient name in preview | results by name | **UNSUPPORTED** in preview | MEDIUM |
| S05 | Accueil: propose tomorrow 10am 30min | recap and no write until confirmation | preview CODE; real action path not UI-integrated | HIGH |
| S06 | Accueil without agenda permission: `/rdv` | fail 403, no patient data | server permission CODE; re-run role-specific HTTP | CRITICAL |
| S07 | Dentiste: consecutive 08:00–08:20 / 08:20–08:40 | accept both, real overlap 409 | real PG+SQLCipher synthetic HTTP PASS #38883675681 | HIGH |
| S08 | Dentiste: crown quote tooth 46 | proposal/editor only on explicit confirm | classic backend CODE; preview draft only | HIGH |
| S09 | Dentiste: stale pending status ABA | reject 409 and unchanged real booking | real PG+SQLCipher HTTP PASS #38883675681 | CRITICAL |
| S10 | Accueil: 409 during workflow | clear reconciliation, no automatic replay | Vitest 409, human recovery NOT TESTED | HIGH |
| S11 | Another cabinet: request patient ID | deny without patient leak | tenant/auth CODE + security CI; full UI matrix missing | CRITICAL |
| S12 | Dentiste: mark a relevant Ghost Brain alert read | ack only after server success | React tests PASS; actual clinical usefulness unmeasured | MEDIUM |

All cases use fictitious fixture values. **0/12 complete end-to-end human-UX repetitions measured**, not « 0/12 feature works ».

## BEFORE status (actual current app)
- Only genuine existing **Cabinet web 1280×900** before/after *interaction state* screenshots available in [synthetic browser visual #38883675591](https://github.com/hraaaaf/Digital_crown/actions/runs/38883675591), artifact `12039871284`. This is NOT a before/after release-change comparison.
- `1440` and `1920` baseline **NOT CAPTURED**; do not upscale 1280 and call it proof.
- On actual 1280 image the panel is ~396px wide, blue identity consistent; user sees « Simulation ZERO-LLM — aucune écriture » and exact slash commands, then asks for numeric patient ID. Technical language and multi-step flow precede useful clinical result.
- Current end-to-end bot latency **NOT MEASURED**. Previously measured 0.7–2.1ms are synthetic **appointment SQL conflict queries**, not bot/browser p50/p95.

## Measurement contract — REQUIRED to close CB-00
Use **authorized synthetic localhost T2 only**, never patients or live server. Record CPU/RAM/OS/browser, PR SHA, fixture ID, cold first-request, 30 warm repetitions, p50/p95 by `performance.now` or monotonic clock for **HTTP full response** and **click-to-useful-DOM**, load/panel open, retries/errors, and interaction counts. Target desktop **1280/1440/1920**, keyboard and 200% browser zoom in scope. 390/430 are safety smoke of web fallback only, not Pocket UX acceptance. Deny any /bot/execute or appointment write during preview.

| Metric | State | Initial proposed goal (NOT measured) |
|---|---|---|
| Preview API first / 30 warm p50,p95 | **NOT MEASURED** | baseline first |
| Browser click → useful DOM p50,p95 | **NOT MEASURED** | read p95 ≤2 sec |
| Initial assistant open p50,p95 | **NOT MEASURED** | warm p95 ≤1 sec |
| Proposed booking (once actionable) | **NOT MEASURED** | p95 ≤3 sec; clinical integrity first |
| 12 synthetic staff journeys | **NOT EXECUTED** end-to-end | ≥90% pilot success after implementation |

## Three UI TARGET directions — concepts only, not shipped
Scored heuristically on common rubric: time-to-value 30%, identity/error clarity 25%, readability/keyboard 20%, action safety 15%, reversibility 10%. Not a usability test or owner choice.

| Direction | Shape | Benefit | Trade-off | Preliminary /10 |
|---|---|---|---|---|
| A Quick Panel | compact contextual floating ~420px | shortest transition from current popover | complex booking may not fit | 8.1 |
| **B Associate Sidecar (recommended for review)** | stable 480px right pane, patient identity, step progress, explicit confirmation | continuous context, visible review + errors | reduces clinical workspace width | **8.8** |
| C Task-first Workspace | full task view with 3 columns and confirmations | best density for complex multi-step tasks | larger navigation change | 8.5 |

**Owner decision still needed:** choose A/B/C after viewing non-functional concept mockups. Their scores do not establish a 9/10 production UI.

## CB-00 status / gates
**Completed:** HEAD inventory, source-traceable 12 scripts/scenarios, code + test truth labels, genuine 1280 reference audited, measurement plan, 3 concept alternatives. **OPEN / BLOCKED:** actual T2 p50/p95 cold/warm, fresh 1440/1920 *real product* BEFORE captures, 12 executed staff flows with evidence, owner TARGET approval.

**NEXT exact:** gain permission/runner access to synthetic isolated T2, execute read-only benchmark and real screenshots, then show owner A/B/C for selection. No release, merge, production flag, deployment or Pocket code.
