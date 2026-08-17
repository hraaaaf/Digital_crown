# Document Studio — T2 Integration Status

Date: 2026-08-17
State: **CLOSED — TECHNICAL INTEGRATION CERTIFICATION PASS ON MASTER**
Canonical integration PR: #135.
Canonical master merge commit: `36567642db299508275419a6782f4ea1c556eabe`.

## Proof contract

- **CODE VÉRIFIÉ**: demonstrated by inspected source/diff.
- **TEST EXÉCUTÉ**: demonstrated by a real repository run.
- **RUNTIME / VISUEL**: only authenticated/browser evidence counts.
- **CERTIFICATION**: separate final gate; never inferred from code presence alone.

## Canonical integration history

T2 was developed as a stacked series (#98 → #99 → #103 → #104 → #105), then consolidated safely against current `master` through isolated integration work before final PR #135.

The pre-integration exact-certified T2 HEAD was `c3ba76b3d68c55243da04c3348195b2f694a9c6a`.

The integrated candidate HEAD was `5625647aea51cb8816ab21c906c06964eb968e9c` and passed:
- T2 Runtime Browser Certification #43 / run `32005383525`: **SUCCESS**;
- CI #745 / run `32005383515`: **SUCCESS**.

PR #135 then merged this integrated tree into `master` as:
- merge commit `36567642db299508275419a6782f4ea1c556eabe`.

## Exact post-merge proof on master

The exact merged `master` commit `36567642db299508275419a6782f4ea1c556eabe` passed all required technical gates:

- CI push #753 / run `32007070096`: **SUCCESS**;
- T2 Runtime Browser Certification #44 / run `32007115783`: **SUCCESS**;
- CI PR #754 / run `32007115747`: **SUCCESS**.

Post-merge runtime artifact:
- name: `t2-browser-evidence`;
- artifact id: `9280493037`;
- digest: `sha256:5c12bf830b1bdbdd8f2e99c1b6ea439cc66bb9f7d5c065418654f8a501297828`.

Artifact inspection confirms:
- authenticated browser matrix: **7/7 pages green**;
- light responsive viewports: **390x844, 430x932, 768x1024, 1280x900**;
- dark-mode verification: **1280x900**;
- all seven automated page scorecards: **10/10**;
- rapid-navigation dirty-state stress: **PASS**, 10/10 transitions completed;
- strict runtime PDF: generate HTTP 200, fetch HTTP 200, `application/pdf`, `%PDF` signature;
- persisted P3/P4/P5 financial reconciliation: **PASS**;
- browser print runtime callback path: **PASS**;
- rapid-edit PDF freshness: **PASS**.

## Financial evidence

Post-merge exact-head evidence:
- P4 paid exact payment: **888 MAD**;
- P5 installment plan total: **1,200 MAD**;
- installment rows: **500 + 700 MAD**;
- collected: **500 MAD**.

## Print boundary

The automated browser gate certifies this application runtime chain:

`PDF blob → hidden iframe → onload → contentWindow.focus() → contentWindow.print()`.

Post-merge exact trace:
- iframe created: 1;
- blob source observed: 1;
- iframe appended: 1;
- onload assigned: 1;
- focus calls: 1;
- print calls: 1;
- fallback `window.open`: 0.

Chromium headless requires a controlled PDF iframe load signal because its PDF plugin does not reliably emit the normal iframe load event. Therefore this certifies the application print callback path and real PDF generation/retrieval, **not observation of the native operating-system print dialog**.

## PDF freshness evidence

Post-merge exact runtime verified two successive PDFs:
- first payload: `T2 Freshness A` / `Version PDF A`;
- second payload: `T2 Freshness C` / `Version PDF C`;
- both fetched as `application/pdf`;
- SHA-256 hashes differ;
- latest payload observed: **true**.

## T2 lot states

- **T2-A — Information architecture:** TECHNICAL RUNTIME PASS.
- **T2-B — Preview truth / freshness:** TECHNICAL RUNTIME PASS.
- **T2-C — Shell decomposition:** TECHNICAL PASS.
- **T2-D — Accessibility residual closeout:** TECHNICAL BROWSER PASS.
- **T2-E — Product polish:** TECHNICAL VISUAL PASS.
- **T2-F — Global recertification:** TECHNICAL INTEGRATION CERTIFICATION PASS ON MASTER.

## Dashboard preservation

The integration branch first absorbed current `master` before PR #135. Dashboard files were not part of the final #135 diff against `master`, so the current Dashboard tree was preserved while T2 was added. The integrated frontend test/build gate passed in #745 and again post-merge in #753/#754.

## Independent anomalies

These remain separate from the closed T2 technical integration gate:
- CI force-pins `httpx==0.27.2` although newer Firebase/Ultralytics packages require 0.28.x;
- npm install reports dependency vulnerabilities; no security certification is claimed;
- GitHub Actions reports Node 20 action-runtime deprecation warnings.

## External / human boundaries

This closeout does **not** claim:
- native OS print-dialog observation;
- security certification;
- clinical/regulatory human certification;
- production-ready status.

No Vercel deployment was performed.

No percentage is assigned because the canonical roadmap has no validated weighting model.
