# CI runner backpressure — 24 October 2026

## Observed incident

The Digital Crown repo has 314 workflow YAML definitions. A sequence of rapid
updates on a single long-lived pull request generated hundreds of queued runs,
including many exact-HEAD historical duplications. The queue exceeded 700
workflows while GitHub-hosted runners still started jobs. This was not a general
runner outage.

A pull_request paths filter inspects the **whole PR diff**, not only the latest
individual commit. Once a broad file appears in the PR diff, every synchronize
event retriggers all matching workflows.

## Targeted remediation (draft; no production activation)

This PR adds workflow-level concurrency to 38 high-frequency pull_request
certifications (Céphalo/ODF, Cabinet, patient, SQL/Alembic, FUE, migration,
settings, UX, PC08). Group keys are unique to **workflow + PR number**.
Incoming PR runs replace/cancel older ones for the same workflow and PR,
allowing a single latest-HEAD candidate to progress instead of a pile of
obsolete matrix jobs.

The group uses github.run_id when there is no pull_request, and cancellation
is PR-only. Therefore manual workflow_dispatch and push executions remain
independent. No path filters, job steps, assertions, clinical guards, release
conditions, or frozen baselines were changed.

The privileged pull_request_target human visual approval workflow is untouched.
Existing workflows that already have concurrency are untouched.

## Non-goals / limitations

- This does **not retroactively cancel** runs created with earlier workflow versions.
  Historical runs remain available as evidence; existing backlog must be
  independently triaged with exact-HEAD/evidence checks.
- This does **not automatically change other legacy workflows** not in the 38-file
  scope. Do not claim complete elimination of backpressure from this partial fix.
- Successful checks still certify only their tested exact SHA; no CI green
  constitutes clinical approval or automatic merge.
- Expanding the policy to remaining PR-triggered workflows needs change review,
  especially where strict manual or release evidence retention is required.

## Regression guard and acceptance

A lightweight CI PR Concurrency Contract checks modified PR-triggered workflow
files for a unique concurrency group and cancellation policy. Manual/push
triggers must not be automatically canceled.

Before merging, require: clean YAML/Actions parsing for the 38 modified files
and the new guard; green CI PR Concurrency Contract on the PR HEAD; confirmation
that each latest relevant workflow reaches a runner and finishes; human review
of cancellation policy; no master merge or production activation without owner
approval. Monitor queued counts on new PR synchronizations to verify impact.
