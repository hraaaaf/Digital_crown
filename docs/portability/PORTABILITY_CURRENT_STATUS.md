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
- P9 — 8 EP — CLOSED; off-runner cross-OS frozen disaster recovery certified
- P10 — 13 EP — CLOSED; authenticated cross-platform update lifecycle certified
- P11 — 8 EP — CLOSED

## P9 closeout proof
Final technical candidate: `4590e2975e71ca89fc404e96e717646155b8fc14`.
P9 Backup Recovery DR #11 / run `33276520623`: **5/5 jobs SUCCESS**.

macOS → Windows:
- source bundle SHA `b1ec767990c3dba5dbd36ecf86fc31610cee7e6b3248e5413070a19d3de9374b`;
- source artifact `9721663479`;
- target proof artifact `9721759555`, digest `sha256:18d897632b8ee9381b9eec4ca865cdf419164b1950cf83294f06c86075f0830f`.

Windows → macOS:
- source bundle SHA `65394c59e3a77e5ea76f36a82c0fe7bb319cc072cc666f9894307ba286e17a58`;
- source artifact `9721671848`;
- target proof artifact `9721742568`, digest `sha256:d62d1e0e6d69fbff7b5e3e58d877e932fd53ea2b5ee04c42d05cd98199ddfc09`.

Both directions used distinct fresh target runners, real frozen packages, Guided Restore, `/health`, SQLCipher DB truth and media verification; wrong secret and tamper paths failed closed.

## Active / remaining
- P12: PREPARED, 0 EP; P7/P9/P10 are AVAILABLE inputs, final matrix still open.
- P13: PLANNED; real-cabinet certification including human macOS first launch and physical/off-machine backup ceremony.
- P14: PLANNED.

## Progress
Credited progress: **136 / 162 EP = 84.0%**.
No partial EP is credited for open lots.

## Next
1. finalize P12 exact matrix using closed upstream evidence;
2. close P12 only if all technical matrix rows are independently proved;
3. execute P13 real-cabinet certification;
4. P14 closeout.

No Vercel.
