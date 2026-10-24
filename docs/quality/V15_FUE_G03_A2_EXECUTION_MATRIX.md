# FUE-G03 — Phase A2 — station fallback / secure identity (synthetic lab)

**State:** CANDIDATE / NO CI EVIDENCE / NOT CERTIFIED. No merge and no deployment.

## Proven parent and strict isolation

- Parent: [A1 PR #1066](https://github.com/hraaaaf/Digital_crown/pull/1066), immutable approved `0664393ec36fbecf7d3dd5108d80b6aebf1b5e75`, real E2E [#40119490249](https://github.com/hraaaaf/Digital_crown/actions/runs/40119490249) SUCCESS and owner visual gate [#40121173110](https://github.com/hraaaaf/Digital_crown/actions/runs/40121173110) SUCCESS.
- A2 is deliberately stacked on A1; neither PR may be merged automatically. Base is NOT asserted to be current master.
- Only synthetic patients in freshly created, encrypted `t2-runtime-cert.db`. Strict runtime: `ENVIRONMENT=test`, `T2_G03_A2=1`, `T2_STATION_FUE=1`, `DIGITALCROWN_ISOLATED_RUNTIME=1`, exact `DATABASE_URL=sqlite:///./t2-runtime-cert.db`.
- Lab browser talks to genuine Vite/React `/station` and real FastAPI on localhost; no mocked response, no real phone/camera/NFC/Windows/physical LAN or clinic records.

## Proposed executable matrix (not PASS before actual CI)

| Case | Oracle | Proof candidate |
| --- | --- | --- |
| A2-01 Owner setup | owner enrollment/PIN, real Station lock, wrong PIN 403 | Browser harness real API |
| A2-02 Phone and birth date | actual fallback form, punctuation-normalized phone, 200; rendered unique identity | Chromium AFTER + HTTP + independent SQL AuditLog |
| A2-03 Name and birth date | accent/case/space-normalized names, 200 | second Chromium AFTER + API + AuditLog |
| A2-04 Disabled | no public fallback button and real API 403 | Chromium 768 + HTTP |
| A2-05 Collision | 2 fictional patients share phone+DOB; 403×4 then 429, no names shown | Chromium BEFORE/AFTER, 5 real requests |
| A2-06 Restart/reset | refreshed session still 429; independent station remains 200 | actual backend + station-scoped SQL counter |
| A2-07 Boundaries | wrong workstation 404 and test-only expired session 409 | distinct workstation cookie + injected disposable SQL expiry |
| A2-08 Data minimization | sanitized HTTP path+status, no query/body/cookie/token/clinical data | evidence-after.json inspection |
| A2-09 Independent readback | persisted 5 failed attempts, successful identity audits, 3 intact fictitious patients, 0 clinical appointment mutation | separate SQLCipher process |
| A2-10 Regression | previous Station API pytest and React Station identity Vitest unchanged | exact HEAD run required |

**Pre-existing code:** `backend/routers/station_patient_session.py` implements `phone_dob`, `name_dob`, `disabled`, mode set with owner PIN, station-scoped five failures in 15 minutes, normalized identifiers and generic collision refusal. A2 does NOT replace this production logic.

## Proof entry points

- `scripts/seed_v15_station_fallback_a2.py` seeds exactly three fictitious patients; `--verify` reads SQLCipher independently and `--expire-session` injects only isolated expiry.
- `frontend/scripts/certify-v15-03-a2-real-fallback.mjs` runs real Chromium-to-FastAPI cases and writes 8+ PNGs plus sanitized `evidence-after.json` (must be executed before any PASS).
- **CI blocker at creation:** editing the dedicated `.github/workflows/v15-fue-g03-a2-fallback.yml` was blocked by the GitHub tool security controls. Do not bypass the block, and do not claim executable certification until an authorized CI workflow is committed and an exact-HEAD run + artifacts are independently checked.

## Closure / exclusions

A2 requires completed exact-SHA CI, jobs and step logs, actual negative responses, all genuine screenshots inspected, independent SQL oracle PASS, and human visual sign-off if UI/visual changes justify it. Failing any required case = A2 OPEN. No merge, Vercel, Production, patient real data or physical certification. A3 (deep 0/1/N RDV and public Wall) is a separate next step, not implicitly started.
