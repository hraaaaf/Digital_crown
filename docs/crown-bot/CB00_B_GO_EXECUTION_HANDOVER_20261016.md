# Crown Bot 2.0 — CB-00 GO / Direction B (2026-10-16)

**STATE: CB-00 OPEN / CB-01 NOT STARTED.** Owner explicitly chose B — Associate Sidecar as the Cabinet Web Desktop UX TARGET. This does not approve merging, activating, deploying or expanding into Pocket.

## Source and proof boundary

- Technical base: PR #894, HEAD 9cf19e68026fa92d31fb704f5b81b9cd667e5254, draft/unmerged. This separate documentation branch does not change PR #894.
- Actual existing UI: frontend/src/components/CrownBot/CrownBotChat.tsx, CrownBotWorkflowPreview.tsx.
- Backend: backend/routers/bot_workflows.py, POST /api/bot/workflows/preview, exact slash commands, at most 8 turns, patient by numeric ID. No executable pending action ID; flags default OFF.
- Pocket: separate mobile JWT/device trust boundary, assistant “En cours de construction”, out of scope.

## Completed vs not proven

- DONE: product truth matrix, 12 specified synthetic business tasks, 9 concept mockups at 1280/1440/1920, existing 1280 interaction-state capture, owner direction B approval.
- DONE, narrow: new scripts/ci/crownbot_cb00_t2_read_evidence.py to measure a **useful authenticated /patient + ID HTTP read** across 30 warm repetitions, alongside anonymous 401 and optional synthetic 403/404 checks. Syntax and local guard/contract assertions checked; no T2 execution.
- NOT MEASURED: actual T2 HTTP results, click-to-useful-DOM p50/p95, genuine process cold start, actual BEFORE 1440/1920, 12 full staff E2E journeys, full DB write delta, 200% zoom and staff UX.
- BLOCKED: authorized remote Desktop Commander device DESKTOP-3MAJEEH was OFFLINE when inspected. Never label SQL conflict query timings (0.7–2.1ms) as Crown Bot response time.

## Required T2 evidence procedure (not yet run)

1. On an authorized **isolated localhost T2**, confirm exact running source SHA, permitted local server, synthetic patients, test users, permissions, and separate disposable preview flags. No genuine cabinet data.
2. Snapshot synthetic DB, appointment counts, audit entries, before any UI requests; freeze unrelated background jobs if necessary, and compare afterwards. A request trace alone is insufficient evidence that there were zero writes.
3. Provide T2_USER (starts with t2-), T2_PASSWORD, T2_PATIENT_ID (known test record), DIGITALCROWN_ISOLATED_RUNTIME=1. For negatives also T2_DENIED_USER/T2_DENIED_PASSWORD with revoked agenda permission and T2_FOREIGN_PATIENT_ID for another synthetic cabinet. Never log these values.
4. Run: python scripts/ci/crownbot_cb00_t2_read_evidence.py --api http://127.0.0.1:8005 --n 30 --out /tmp/cb00-t2-useful-read.json. The 401/403/404 controls fail closed; omitted optional fixtures show NOT_RUN, never PASS. An auth 423 or flag OFF is a blocker, not an acceptable latency result. Source SHA in output is operator-entered and must be checked against running binary separately.
5. Run a real authorized browser at 1280x900, 1440x900 and 1920x900. Capture actual existing UI **BEFORE** at each width, then click-to-useful-DOM timing 30 warm samples per scenario/width, page load, first result, errors, keyboard navigation and 200% browser zoom. Store screenshots from fictional test data only.
6. Execute all 12 scenarios S01–S12 with test IDs, role, expected vs observed outcome, screenshots/trace, 403/404/409 and DB delta. Unsupported name search is UNSUPPORTED in current preview, not a successful E2E task.
7. Only after evidence, compare same-viewport approved B TARGET with real AFTER implementation and run security/UX independent adversarial perspectives + confirmation before claiming convergence.

## B — Approved UX target, not implementation

**Intent:** persistent right-side assistant that keeps the current agenda or patient record visible and does not force page navigation for common tasks.

Information architecture:
- Header: current cabinet, Crown Bot, close/collapse, clear access and offline state.
- Patient identity: selected patient name **plus scoped identifier**, with mandatory disambiguation if homonyms. No selection by guess.
- Shortcuts: “Mon programme”, “Trouver un patient”, “Préparer un rendez-vous”. Label non-wired functions in prototype as future TARGET, not live capabilities.
- Guided steps: one missing datum at a time, correction without restart, patient and permissions visible, source/freshness and specific recovery for 401/403/404/409/423/500.
- Review: visible proposal vs actual confirmation, no clinical write in CB-01, never show “saved” from a read-only proposal. Treat unknown post-submit outcome as “vérifier l'état”, not success.

**Desktop layout constraint:** initial sidecar concept about 440–480 CSS px at 1440/1920, adapt near 400–440px or collapse at 1280 **only if real layout evidence confirms core clinical workspace remains usable**. The ~480px mockup is not a fixed final rule. Keyboard/focus/zoom/reflow; no clipping, overlay obstructing patient data, or horizontal overflow.

**Boundaries:** CB-01 read-only first value; CB-02 deterministic guided natural French only after specific corpus of 60 formulations; CB-03 secure executable actions only after confirmed permissions, idempotence, CAS and independent test gates. No clinical LLM inference, autonomous prescription, Pocket token reuse or data export.

**Acceptance gates:** three useful tasks (agenda, patient homonyms, preparing non-executable appointment), observable useful result and interaction count, role/tenant isolation, explicit 403/404/409 recovery, 1280/1440/1920 BEFORE/TARGET/AFTER and keyboard + 200% zoom; at least two genuinely distinct adversarial review perspectives on exact HEAD plus clean confirmation pass. Green CI alone is not a visual or clinical validation.

## Next exact

HIGH effort: reconnect a permissioned isolated T2 → real HTTP and browser p50/p95, snapshots, synthetic S01–S12, desktop baseline → validate B at 1280 → CB-00 exit only if evidence complete → CB-01 proposal separately. No merge, activation or deployment from this handover.
