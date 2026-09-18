# HANDOVER — Digital Crown V1 / LOT V1-04 — Céphalométrie scientific re-baseline

Date: 2026-09-18
Repository: hraaaaf/Digital_crown
Canonical roadmap: docs/clinic/DIGITALCROWN_V1_CONSOLIDATED_ROADMAP.md

## Goal

Re-baseline the current cephalometric runtime after V1-03 and correct only evidence-backed V1 blockers, without reopening already-certified R20 work or introducing unsourced diagnosis, indication, severity, treatment or normative inference.

Success = exact-head frontend/backend concordance, targeted regressions, full CI/scientific gates, mandatory visual BEFORE/AFTER evidence, severe dual review, canonical closeout, merge and post-merge certification.
Proof = GitHub tests/runs + retained visual artifacts + canonical docs.

## Start state verified

Certified base:
- master: 7454215274032898d1a50659d624a5cb32aab494
- CI 35335941911 — SUCCESS
- Cabinet Upgrade PostgreSQL Certification 35335941919 — SUCCESS
- no Céphalo/Ortho runtime delta since the prior R20 canonical baseline; R20 remains closed.

Active work:
- branch: feat/v1-04-cephalo-rebaseline
- PR: #592 — OPEN / DRAFT / mergeable
- current HEAD: eb0f114c659d7461f34c0437252a4b8da63bad50
- base: 7454215274032898d1a50659d624a5cb32aab494

## BEFORE / discovered blocker

Existing R18 frontend/backend concordance did not cover COM incisor relations Surplomb and Recouvrement even though both are computed/displayed.

The audit was extended first without changing product behavior.

Deterministic evidence:
- run 35338035397 — expected FAILURE exposing the gap
- same fixture/landmarks/calibration
- frontend Surplomb: +2.6 mm
- backend Surplomb: -2.6 mm
- delta: 5.2 mm
- Recouvrement: concordant

Root cause verified:
frontend computeStep3Data applied Math.abs() to overjet, destroying direction; backend preserved signed geometry.

## Scientific boundary / decision

Peer-reviewed source check supports signed overjet: reverse overjet is negative rather than converted to absolute magnitude. Overjet/overbite are expressed in millimetres.

Important limitation:
the evidence supports signed relation + mm unit. It does NOT independently certify Digital Crown's exact legacy Frankfort-projection construction as a universal orthodontic standard.

Therefore:
- preserve signed patient geometry consistently frontend/backend;
- M_OVERBITE_V1 unit may be locked to mm;
- M_OVERJET_MM_V1 and M_OVERBITE_V1 remain LEGACY_TO_AUDIT for construction/provenance;
- do NOT activate new norms, diagnosis, classification, indication, severity or treatment inference.

Evidence note:
docs/audits/CEPHALO_V1_04_REBASELINE.md

## Implemented

1. Extended frontend R18 audit extraction with overjet/overbite.
2. Extended backend R18 report with the same signed incisor relations.
3. Extended comparator with Surplomb/Recouvrement.
4. Fixed frontend computeStep3Data:
   - removed absolute-value distortion;
   - preserves signed overjet.
5. Added frontend regression for positive and reverse overjet.
6. Added backend runtime regression:
   - signed positive/reverse overjet;
   - signed overbite/open-bite behavior;
   - fail-closed when mm calibration unavailable.
7. Locked M_OVERBITE_V1 canonical unit to mm while keeping LEGACY_TO_AUDIT.
8. Updated measurement audit docs.
9. Added deterministic V1-04 Step 3 signed-overjet visual harness.
10. Attached BEFORE/AFTER evidence generation to the R18 concordance gate.
11. Activated V1-04 state in canonical roadmap.

## Current exact-HEAD evidence

HEAD: eb0f114c659d7461f34c0437252a4b8da63bad50

Green:
- CI 35340555838 — SUCCESS
- Cephalo R18 Scientific Concordance Audit 35340555874 — SUCCESS
- T2 Runtime Browser Certification 35340555942 — SUCCESS
- Cephalo R15 AFTER 35340555983 — SUCCESS
- Cephalo R15bis AFTER 35340555908 — SUCCESS
- Agenda A5 Visual Evidence 35340555862 — SUCCESS

Expected skips:
- PR Merge Summary 35340555973 — SKIPPED
- M6-I Biometric Passkey Certification 35340556025 — SKIPPED

Red:
- UI Human Visual Approval 35340553905 — FAILURE

Do NOT call the lot merge-ready yet. The visual failure must be inspected/fixed and the retained V1-04 BEFORE/AFTER artifact must be downloaded/reviewed before the human merge gate.

## Mandatory visual doctrine

For this lot the corrected value is user-visible, so no no-UI exception.

Required:
- BEFORE and AFTER same fixture/workflow;
- canonical viewports 390x844 / 768x1024 / 1280x900;
- BEFORE must show +2.6 mm;
- AFTER must show -2.6 mm;
- same Step 3 workflow;
- zero horizontal overflow/runtime errors;
- retained inspectable artifact;
- show captures to product owner;
- severe visual score;
- second severe expert/agent-style review before merge.

Never fabricate screenshots or substitute unrelated Agenda/R15 images.

## Mandatory lot-end recap

At lot end send:
- BEFORE: R18 omitted incisor relations; frontend destroyed reverse-overjet sign.
- FAIT: concordance extended, signed overjet fixed, tests + registry/docs + visual harness.
- AFTER: exact measured parity and correct signed value, with run/artifact evidence.
- CAPTURES: show BEFORE/AFTER at all three canonical viewports.
- PREUVES: exact-head gates + severe dual score.
- Remaining uncertainty: legacy projection construction stays LEGACY_TO_AUDIT unless separately source-locked.

## Next exact

1. Inspect UI Human Visual Approval run 35340553905 logs.
2. Fix only the proven harness/product issue.
3. Re-run/obtain exact-head visual evidence.
4. Fetch/download retained V1-04 BEFORE/AFTER artifact and inspect all six captures.
5. Verify R18 report has zero divergence for Surplomb + Recouvrement.
6. Perform severe visual score + independent expert-style severe review.
7. Update canonical roadmap with exact HEAD/run/artifact/digest and lot-end evidence.
8. Only then present PR #592 for explicit human merge authorization.
9. If authorized: mark ready + merge exact HEAD.
10. Certify post-merge master CI/PostgreSQL/scientific gates.
11. Canonical closeout, then unlock/start V1-05.

If any gate is red: diagnose → correct → test → continue. Do not wait passively.

## Safety / operational constraints

- no Vercel deployment without explicit authorization;
- no production/cabinet DB mutation;
- no unsourced clinical inference;
- do not reopen R20 without new evidence;
- merge remains a human gate;
- visual evidence is mandatory before merge.

## Resume protocol in a new window

Read this file first, then verify:
1. PR #592 current state and exact HEAD;
2. compare branch/base;
3. all exact-HEAD Actions runs;
4. UI Human Visual failure status/logs;
5. visual artifact availability.

Then execute Next exact without asking for information already recorded here.
