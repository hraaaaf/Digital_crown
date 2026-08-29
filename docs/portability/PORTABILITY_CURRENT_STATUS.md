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
- P12 — 13 EP — CLOSED candidate; technical Windows/macOS evidence matrix complete

## P9 proof
Final technical candidate `4590e2975e71ca89fc404e96e717646155b8fc14`; P9 #11 `33276520623`: **5/5 SUCCESS**.
- macOS → Windows proof artifact `9721759555`, digest `sha256:18d897632b8ee9381b9eec4ca865cdf419164b1950cf83294f06c86075f0830f`.
- Windows → macOS proof artifact `9721742568`, digest `sha256:d62d1e0e6d69fbff7b5e3e58d877e932fd53ea2b5ee04c42d05cd98199ddfc09`.

## P12 evidence matrix
All ten technical requirements have an independently verified upstream proof:
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

P13 remains separate for physical cabinet machines, human macOS first launch, operational USB/NAS setup and real-device evidence where required.

## Canonical EP arithmetic
The 15 listed lots total **167 EP**, not 162. The stale 162 denominator was introduced with the effort table itself on 2026-08-24. No lot value was reduced to preserve it.

## Active / remaining
- P13: PLANNED — 13 EP, real-cabinet certification.
- P14: PLANNED — 5 EP, final closeout.

## Progress
Candidate credited progress after P12 exact-head validation: **149 / 167 EP = 89.2%**.
Until the P12 closeout candidate passes its own exact-head checks, the last fully validated credited state remains P9-level **136 / 167 EP = 81.4%**.

## Next
1. exact-head validate P9/P12 closeout candidate;
2. merge PR #298 if green;
3. define and execute P13 real-cabinet certification;
4. P14 closeout.

No Vercel.
