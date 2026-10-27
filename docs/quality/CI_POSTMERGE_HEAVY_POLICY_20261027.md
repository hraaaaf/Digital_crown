# CI — Post-merge heavy policy — 2026-10-27

## Locked decision
- **PR:** automatic CI Scope Gate and narrow non-heavy checks only. Required human, clinical, security, RBAC and pre-merge FUE evidence remain mandatory, on the exact current candidate SHA. If missing, PR stays OPEN/DRAFT/BLOCKED; do not merge just to run a heavy suite later.
- **After authorized merge to master:** expensive workflows selected by changed code paths run on \`push\` to \`master\`. The evaluated source must be \`github.sha\` (and a comparison base may use \`github.event.before\`, never absent PR context).
- **Concurrency:** use workflow + branch/ref key, \`cancel-in-progress: true\`. A newly triggered master run covers the latest code; historic artifact evidence is retained, not rewritten.
- **No workflow self-path triggers:** CI-policy-only changes must NOT launch all 18 heavy workflows at once on the merge that introduces this governance.
- **Merge and deploy:** no automatic merge, Vercel, real cabinet, feature-flag activation or clinical release is authorized.

## Migrated workflows (Wave 1, 18)
\`cabinet-code-cert-candidate.yml\`, \`ceph-p2ter-master-bridge-preflight.yml\`, \`ceph-p2ter-master-bridge-real-cabinet.yml\`, \`ceph-p2ter-master-bridge-frontend.yml\`, \`patient-companion-d2-visual-cert.yml\`, \`patient-p1-architecture-after.yml\`, \`patient-indicators-cert.yml\`, \`ortho-f3-after.yml\`, \`ortho-f4-after.yml\`, \`ux-continuity-patientdetails-cert.yml\`, \`lot07-r3-1-after-screenshots.yml\`, \`lot07-r2-ux-polish-9plus.yml\`, \`lot07-r2-ronly-dec02-e2e.yml\`, \`clinic-p2-patient-billing-visual-cert.yml\`, \`media-c5-visual-cert.yml\`.

## Explicitly not migrated / risks
- \`lot07-r2-ux-master-integration.yml\` needs both PR HEAD and BASE SHA; cannot replace these with \`github.sha\` without redesigning its purpose.
- \`cb03-g7-sqlcipher-api-e2e.yml\` only exists on the unmerged PR #1119; its SQLCipher transaction safety checks cannot be silently deferred. Its trigger/concurrency requires an independent PR-bound safety decision.
- \`ui-human-visual-approval.yml\` remains a trusted \`pull_request_target\` PRE-MERGE gate, never post-merge.
- \`ci-scope-gate.yml\` remains a cheap PR workflow.
- Theme waves, other unmodified legacy workflows and previous DRAFT PRs [#1085](https://github.com/hraaaaf/Digital_crown/pull/1085), [#1086](https://github.com/hraaaaf/Digital_crown/pull/1086) are outstanding. Their changes must be reconciled, not represented as already merged. These 18 are a bounded first wave, not a claim that all 339 workflow files comply.

## CI proof
Run the tiny \`CI Post-merge Heavy Policy Contract\` on PR: parse YAML, inspect exact 15 triggers/paths/concurrency, ensure no PR context, and assert the trusted human gate and scope gate remain intact. After any authorized merge, inspect the actual master SHA and workflow jobs; never claim SUCCESS before GitHub completes.

## Triage of incidental expensive PR runs
The policy PR itself triggered 10 workflows before this scope correction. The G1 MultiView browser suite and Wave02 token suite now run only on matching postmerge master changes. CEPH native Windows SQLCipher remains a **required PR security exception**, but now restricts paths to real Windows SQLCipher/ceph source impact and serializes by PR. LOT07 R2 disposable premerge integration keeps PR HEAD/BASE semantics but no longer triggers when unrelated CI YAML changes. Never infer this wave covers the remaining legacy workflows.
