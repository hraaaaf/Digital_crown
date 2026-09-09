# Digital Crown — Portability & Launcher — current verified state

Last verified: 2026-09-09.

## Closed
- P0 — Baseline & portability contract — 5 EP — CLOSED
- P1 — OS abstraction layer — 13 EP — CLOSED
- P2 — Runtime Supervisor / Launcher V2 — 13 EP — CLOSED
- P3 — Cabinet data portability — 13 EP — CLOSED
- P4 — Licence & local secrets cross-platform — 8 EP — CLOSED
- P5 — Native/scientific runtime portability — 13 EP — CLOSED
- P6 — Industrialized Windows packaging — 8 EP — CLOSED
- P7 — Native macOS packaging — 13 EP — CLOSED
- P8 — Hardware & peripherals — 21 EP — CLOSED
- P9 — Backup / Recovery / DR — 8 EP — CLOSED
- P10 — Cross-platform Update Engine — 13 EP — CLOSED
- P11 — Launcher & Recovery UX — 8 EP — CLOSED
- P12 — CI & certification matrix — 13 EP — CLOSED

## Consolidation proof now on master
PR `#382` merged into `master` at `cd47035c19bb9c87ac0c9272808c171f632a7f1d`.

Exact product candidate before docs-only closeout: `b149412edc0dce605b8b5bcda49145320ee673df`.

SUCCESS on that product candidate:
- CI #2925 (`34353472792`)
- P5 #354 (`34353472891`)
- P6 Windows Packaging #169 (`34353472901`)
- P6 Authenticode Probe #31 (`34353472897`)
- P7 macOS Private Distribution #40 (`34353472850`)
- P7/P10 Clean Hosted #23 (`34353472883`)
- P8 #93 (`34353472784`)
- P9 #26 (`34353472906`)
- P10 #155 (`34353472814`)
- P10 macOS #73 (`34353472811`)
- P11 #132 (`34353472785`)
- P12 #87 (`34353472866`)
- Runtime #466 (`34353472932`)
- T2 #1953 (`34353472837`)
- Guided Restore AFTER #219 (`34353472913`)
- Settings Security #242, RBAC #294, Onboarding #275, R11 #422.

Visual AFTER artifact: `guided-restore-after`, id `10104796866`, digest `sha256:160180829e139e0562da3a75e25c56efcc7cf351108c7d43a50ab2d387da31dd`.

Historical stacked PRs `#237` and `#299` are CLOSED without merge as superseded by `#382`.

## Active
P13 — Real cabinet certification — ACTIVE — **0/13 EP**.

Current branch: `portability/p13-physical-certification`, created from verified master `cd47035c19bb9c87ac0c9272808c171f632a7f1d`.

Execution runbook: `docs/portability/P13_PHYSICAL_EXECUTION_RUNBOOK.md`.

P13 remains a real physical/human gate:
- real Windows 11 cabinet-local target;
- genuine off-machine USB/removable/NAS;
- operator attestation;
- same release candidate across Windows/macOS;
- real Apple Silicon macOS evidence, with remote `.metal` allowed only under the closure-guard restrictions;
- final `scripts/p13_real_cabinet_closure_guard.py validate-closure` PASS.

CI or remote rehearsal alone cannot credit P13. No partial EP.

## Planned
P14 — Closeout — 5 EP — PLANNED after P13.

## Progress accounting
Roadmap total corrected: **167 EP**.
Credited: **149 EP**.
Global technical progress: **89.2%**.

## Real blocker
Physical execution and operator-observed evidence on the required Windows/macOS targets.

## Next exact
1. choose one immutable P13 `release_id` and preserve exact Windows/macOS packages;
2. execute Windows 11 cabinet-local run with a real off-machine destination;
3. execute macOS Apple Silicon run using the same `release_id`;
4. record all 15 gates using `scripts/p13_real_cabinet_evidence.py`;
5. validate each evidence file and the pair;
6. run the final closure guard;
7. only if it prints `P13_CLOSURE_GUARD_VALID=PASS_ATTESTED`, credit P13 and execute P14.

## Deployment rule
No Vercel deployment without explicit product authorization.

## Canonical
`PORTABILITY_LAUNCHER_ROADMAP.md`.
