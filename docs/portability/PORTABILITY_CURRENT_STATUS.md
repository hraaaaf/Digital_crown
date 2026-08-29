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
- P7 — 13 EP — CLOSED
- P8 — 21 EP — CLOSED
- P9 — 8 EP — CLOSED; off-runner cross-OS frozen DR certified
- P10 — 13 EP — CLOSED; authenticated cross-platform update lifecycle certified
- P11 — 8 EP — CLOSED
- P12 — 13 EP — CLOSED; technical Windows/macOS evidence matrix certified

## P9 proof
Final technical candidate `4590e2975e71ca89fc404e96e717646155b8fc14`; P9 #11 `33276520623`: **5/5 SUCCESS**; closeout repeat P9 #12 `33277838848`: **5/5 SUCCESS**.
- macOS → Windows proof artifact `9721759555`, digest `sha256:18d897632b8ee9381b9eec4ca865cdf419164b1950cf83294f06c86075f0830f`.
- Windows → macOS proof artifact `9721742568`, digest `sha256:d62d1e0e6d69fbff7b5e3e58d877e932fd53ea2b5ee04c42d05cd98199ddfc09`.

## P12 closure proof
Exact closeout HEAD `c70f1b4eef7a0246e2a899e8789a440fe5b44e3b` passed all six final PR-triggered gates:
- P12 #75 — SUCCESS;
- P9 #14 — SUCCESS;
- CI #2191 — SUCCESS;
- T2 #1308 — SUCCESS;
- Patient #607 — SUCCESS;
- Catalog #581 — SUCCESS.

PR #298 merged into `portability/p9-backup-recovery-dr` as `34a8f4247a883754a1aa4a59c17fe12796103333`. The target branch was verified at that exact merge SHA and GitHub reported the merge commit signature as valid.

The P12 matrix covers:
1. runtime/readiness/single-instance — P2 + Runtime regression;
2. frozen package self-test / forbidden content — P6/P7/P9;
3. native scientific fail-closed — P5 + frozen self-tests;
4. install/upgrade/uninstall/data preservation — P6/P7;
5. cross-OS DR + failure paths — P9;
6. authenticated update + rollback — P10;
7. launcher/recovery — P11;
8. artifact identity/checksum/platform trust truth — P6/P7/P10;
9. clean-machine technical execution — P6/P7/P9/P10;
10. conservative hardware support truth — P8.

## Canonical EP arithmetic
The 15 listed lots total **167 EP**, not 162. The stale 162 denominator was introduced with the effort table itself on 2026-08-24. No lot value was reduced to preserve it.

## Active / remaining
- P13: ACTIVE — **0/13 EP**; protocol prepared in `docs/portability/P13_REAL_CABINET_CERTIFICATION.md`.
- P14: PLANNED — 5 EP, final closeout.

P13 is deliberately outside the GitHub-hosted technical certification boundary. It requires one physical Windows x64 target, one physical Apple Silicon Mac, administrator-controlled macOS first launch, synthetic cabinet continuity and a real independently stored off-machine recovery medium. CI evidence cannot substitute for those physical/human gates.

## Progress
Verified credited progress: **149 / 167 EP = 89.2%**.
No partial EP is credited for P13.

## Next
1. execute the P13 protocol on both physical cabinet targets;
2. prove real off-machine backup + cross-OS recovery without real patient data;
3. record first-launch, health, single-instance, update/rollback and controlled failure evidence;
4. close P13 only if every mandatory physical gate passes;
5. P14 final closeout.

No Vercel.
