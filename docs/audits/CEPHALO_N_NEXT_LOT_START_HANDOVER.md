# CÉPHALO-N — NEXT LOT START HANDOVER

Last verified: 2026-09-17.

## PURPOSE

This file is the handover for a new conversation after the verified R20 closeout.

Do not assume the next Ortho/Céphalo implementation lot in advance. First re-baseline the live scientific inventory on current `master`, then select the highest-priority still-open lot from evidence.

## READ FIRST — IN THIS ORDER

1. `docs/CEPHALO_N_CANONICAL.md`
2. `docs/CEPHALO_N_ROADMAP.md`
3. `docs/SCIENTIFIC_CORE_REBUILD_ROADMAP.md`
4. `docs/audits/CEPHALO_N_R20_CLOSEOUT_HANDOVER.md`
5. This file

Then verify live GitHub state before any conclusion or write: repo, `master` HEAD, open/merged Céphalo/Ortho PRs, exact-head CI and any newer commits.

Historical runs never override live GitHub state.

## VERIFIED BASELINE

Repository: `hraaaaf/Digital_crown`.

R20 closeout documentation PR: `#569`.

PR `#569` head: `d9d36133310bf48ba34e2e4429ba574924b96044`.

PR `#569` merge SHA / verified `master` baseline: `7d936cc76257911d03e98f7788f25056399783d3`.

PR checks before merge:

- CI `35206163538`: SUCCESS.
- T2 Runtime Browser Certification `35206163520`: SUCCESS.
- PR Merge Summary `35206163571`: SUCCESS.
- M6-I `35206163543`: SKIPPED as expected.

Post-merge verification confirmed `docs/CEPHALO_N_CANONICAL.md` is present on `master` and records `CEPHALO_N_CLOSEOUT_VERIFIED`.

No Vercel deployment is authorized by this handover.

## LOCKED INVARIANTS

Preserve all of the following unless new evidence explicitly justifies a change:

- `measurement != diagnosis != indication != treatment`.
- Missing scientific evidence means BLOCKED, not inferred.
- No autonomous diagnostic, indication or treatment generation from raw cephalometric measurements.
- `backend/services/cephalo_measure_registry.py` remains the single canonical measure registry.
- Normative registry remains separate from the measure registry.
- Unknown canonical unit fails closed.
- `M_OVERBITE_V1` remains without a locked unit and therefore `None` until evidenced.
- Lateral and PA/frontal are distinct acquisition/analysis domains.
- New measurements require source, landmarks, construction, unit, calibration contract, canonical ID, centralized calculation, and deterministic positive/negative tests.
- No Vercel deployment without explicit user authorization.

## GOAL — FIRST LOT OF THE NEW CONVERSATION

Re-baseline the Ortho/Céphalo scientific inventory on live `master`, identify the most critical genuinely open lot, then define and execute that lot without reopening R20 unless a new regression is evidenced.

## SUCCESS

The start phase is complete only when all of the following are observable:

1. Live `master` HEAD is verified.
2. Canonical Céphalo files are read and internally coherent with live GitHub state.
3. Open Ortho/Céphalo scientific gaps are inventoried from repository evidence, not memory.
4. One next lot is selected because it is the highest-priority open gap on the critical path.
5. That lot has an explicit Goal / Success / Proof contract before implementation starts.
6. Scope is bounded and does not silently reopen R20.
7. No unsupported scientific inference is introduced.
8. No Vercel deployment occurs without explicit authorization.

## PROOF REQUIRED

Before implementing the selected lot, capture:

- exact `master` SHA;
- relevant files/functions/endpoints/tests discovered;
- current behavior observed from code/tests where applicable;
- open-gap inventory;
- rationale for selecting the next lot;
- the lot's Goal / Success / Proof contract.

After implementation, proof must be proportional to risk and normally include code diff, deterministic tests, observed behavior, relevant CI on the exact candidate SHA, documentation closeout, and post-merge verification.

## FIRST ACTIONS IN THE NEW CONVERSATION

1. Fetch current `master` and confirm whether it still equals `7d936cc76257911d03e98f7788f25056399783d3`; if not, record the new live SHA and inspect the delta relevant to Ortho/Céphalo.
2. Read the four canonical files listed above.
3. Search the repo for remaining Ortho/Céphalo TODO/BLOCKED/legacy/scientific-gap markers plus active services, routers, frontend flows, tests, and documentation touching cephalometry/orthodontics.
4. Build a compact inventory of genuinely open scientific/technical gaps.
5. Rank only by critical-path impact, scientific risk, user impact, dependency order, and testability; do not invent a lot name before evidence.
6. Select one lot and write its Goal / Success / Proof.
7. Execute the lot if the scope is sufficiently determined and no human gate is required.

## DO NOT DO

- Do not reopen R20 because of historical TODOs already closed by the canonical chain.
- Do not use historical CI as proof of current `master` without checking the live delta.
- Do not conflate presence of a value with scientific validation of that value.
- Do not add normative interpretation, diagnosis, indication or treatment merely because a measurement exists.
- Do not modify `docs/ROADMAP_DIGITAL_CROWN_V2.md`; it is historically locked/read-only.
- Do not deploy Vercel without explicit authorization.

## NEXT EXACT

In the new conversation: verify live `master` -> read canonical files -> re-baseline remaining Ortho/Céphalo scientific gaps -> select the highest-priority open lot -> define Goal / Success / Proof -> execute if no human gate exists.

## REMAINING SEQUENCE

`live master verification -> canonical read -> repo inventory -> gap triage -> next-lot selection -> Goal/Success/Proof -> implementation -> targeted tests -> exact-head CI -> closeout docs -> merge -> post-merge verification`
