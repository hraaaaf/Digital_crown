# PC-06 — Patient Finance — HANDOVER

Status: MACHINE-CERTIFIED — HUMAN VISUAL APPROVAL REQUIRED
Branch: feature/patient-companion-pc06-finance
PR: #645 (DRAFT)
Product evidence head: ded90193ce5cd65484f56b5dbb4bba1388e701fa
Master dependency baseline: 70c3dea8fc30b4babe54fe230cfd902f822cf2a7
Deployment: none

## Goal
Expose patient finance as a read-through projection of canonical cabinet financial truth, without a second ledger or optimistic payment state.

## Implemented
- finance summary from active/accounted cabinet truth;
- visible payment history;
- existing installment schedules;
- shared active Note d'honoraires retrieval/download;
- exact tenant + patient boundary;
- live-only finance display;
- explicit cabinet-offline fail-closed behavior;
- no online payment CTA without a verified provider.

## Honoraires reconciliation dependency
PR #644 was merged to master as `70c3dea8fc30b4babe54fe230cfd902f822cf2a7`.
PC-06 was reconstructed on this master baseline before final certification.

## Visual correction
The first AFTER run was green but manual inspection found MAD totals wrapping on mobile.
Correction:
- integer MAD values no longer force useless decimal display;
- summary values are kept on one line with responsive type;
- browser evidence now fails if any summary total spans more than one rendered line.

## Exact-head machine proof
On `ded90193ce5cd65484f56b5dbb4bba1388e701fa`:
- PC-06 Certification `35577425192` ✅
- BEFORE `35577425233` ✅
- AFTER `35577425151` ✅
- CI `35577425226` ✅
- T2 `35577425300` ✅
- P7 `35577425258` ✅
- Remote Transport `35577425256` ✅

AFTER artifact:
- id `10628975176`
- digest `sha256:d86bb4752d6de762cd3f156684f8302b9a7ce3b814cfdde6865815d614758dec`

BEFORE artifact:
- id `10627698972`
- digest `sha256:4821cf8294d963b15cd126b602911e8d7197f68d9d9d22e1d80414504dba7549`

## Visual inspection
Inspected manually:
- Chromium 360x800 / 390x844
- WebKit 360x800 / 390x844

Result:
- no finance overlap;
- no horizontal overflow;
- totals stay on one line;
- 44px minimum finance action;
- no payment CTA;
- cross-browser presentation coherent.

Conservative visual score: 9.2 / 10.

## Remaining
True human gate:
1. human visual approval;
2. if approved: mark PR ready, final exact-head verification if HEAD unchanged, merge #645;
3. post-merge verification;
4. close PC-06 and prepare PC-07 handover.

No Vercel deployment without explicit authorization.
