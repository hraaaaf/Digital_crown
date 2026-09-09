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

## Exact-head consolidation proof
Product candidate before docs closeout: `b149412edc0dce605b8b5bcda49145320ee673df`.

SUCCESS on this candidate:
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

## Active next
P13 — Real cabinet certification — ACTIVE — **0/13 EP**.

P13 remains a real physical/human gate: Windows 11 cabinet-local target, genuine off-machine USB/removable/NAS, operator attestation, same release candidate across Windows/macOS, and final closure guard. CI and P13-R remote bare-metal do not credit P13 by themselves.

## Planned
P14 — Closeout — 5 EP — PLANNED after P13.

## Progress accounting
Roadmap total corrected: **167 EP**.
Credited: **149 EP**.
Global technical progress: **89.2%**.

No partial EP are credited for an open lot.

## Consolidation state
Branch: `refactor/portability-master-consolidation`.
PR: `#382`.
The old divergent P9/P13 stack must not be merged directly. After #382 is merged and master is verified, PRs #237 and #299 are to be closed as superseded without merge; P13 then restarts from the new master.

## Deployment rule
No Vercel deployment without explicit product authorization.

## Canonical
`PORTABILITY_LAUNCHER_ROADMAP.md`.
