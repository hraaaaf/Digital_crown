# Digital Crown — Portability & Launcher — current verified state

Last verified: 2026-08-29.

## Closed
- P0 — 5 EP — CLOSED
- P1 — 13 EP — CLOSED
- P2 — 13 EP — CLOSED
- P3 — 13 EP — CLOSED
- P4 — 8 EP — CLOSED
- P5 — 13 EP — CLOSED
- P6 — 8 EP — CLOSED
- P7 — 13 EP — CLOSED; private macOS packaging and lifecycle certified
- P8 — 21 EP — CLOSED
- P10 — 13 EP — CLOSED; authenticated cross-platform update lifecycle certified
- P11 — 8 EP — CLOSED

## P7 / P10 closeout proof
PR #274 merged into `portability/p10-update-engine` as `04d286041fe85743920d633aea4f6a24f3ceae3f`.
Post-merge exact HEAD `3bc4f781e9ad496b86c72b4cade56da9241555c7` verified with 18/19 PR-triggered workflows SUCCESS and 0 failures; the only non-completed workflow is redundant P6 Windows Packaging #149, still pending, while P6 Authenticode #16, P10 #139, P10 macOS #57, P7 #25, Clean Hosted #7, P12 #69 and general CI #2183 are all SUCCESS.

Clean Hosted #7 `33272768876` — SUCCESS on both fresh platforms.
P7 macOS #25 `33272768846` — SUCCESS.
P10 #139 `33272768851` — SUCCESS.
P10 macOS #57 `33272768868` — SUCCESS.
P12 Prep #69 `33272768866` — SUCCESS.
CI #2183 `33272768872` — SUCCESS.

## Active / remaining
- P9: ACTIVE; off-machine independently persisted DR proof + clean packaged restore + cross-OS evidence where applicable remain open.
- P12: PREPARED, 0 EP until final matrix closes after P9.
- P13: PLANNED; real-cabinet certification including human macOS first launch.
- P14: PLANNED.

## Progress
Credited progress: **128 / 162 EP = 79.0%**.
No partial EP is credited for open lots.

## Next
1. execute P9 off-machine independent clean packaged restore proof;
2. close P9 if its real gates pass;
3. finalize P12 matrix;
4. execute P13 real-cabinet certification;
5. P14 closeout.

No Vercel.
