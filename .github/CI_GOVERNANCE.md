# GitHub Actions governance

## Principle

A code change must not automatically start expensive browser, visual, scientific, runtime, release, or certification workflows.

The default path is:

1. A lightweight **CI Scope Gate** runs on pull requests.
2. It lists changed files and classifies the affected surfaces.
3. No heavy workflow is dispatched by that gate.
4. A heavy workflow is started manually only when its relevance to the current Goal is demonstrated.
5. New commits invalidate unfinished certification evidence for the previous HEAD.
6. Use concurrency with `cancel-in-progress: true` for workflows that can supersede older HEADs.
7. Run full matrices only for an explicit closeout/release gate.

## Allowed automatic trigger

`.github/workflows/ci-scope-gate.yml` is the only pull-request workflow intended to run automatically by default.

Reusable workflows may keep `workflow_call` because it does not execute independently.

## Heavy workflow contract

Existing certification workflows must expose `workflow_dispatch`. They may additionally expose `workflow_call` when another explicitly selected workflow reuses them. They must not independently run on `pull_request`, `push`, `schedule`, `workflow_run`, or similar automatic events unless a future exception is separately justified, reviewed, and documented.

## Human gate

Before running a heavy workflow, record:

- Goal;
- exact HEAD;
- reason the workflow is relevant;
- expected proof;
- whether a cheaper targeted test can answer the same question.

If relevance is not demonstrated, do not run it.
