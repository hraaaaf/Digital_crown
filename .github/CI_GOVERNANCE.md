# GitHub Actions governance

## Politique after-merge approuvée — 2026-10-27

Les certifications lourdes migrées ne s'exécutent automatiquement que sur `push master` après une fusion autorisée et si leurs `paths` changent. Concurrency par `github.workflow` + `github.ref`, avec `cancel-in-progress: true`. Garder les preuves critiques ciblées avant merge et les gates humains. Voir `docs/quality/CI_POSTMERGE_HEAVY_POLICY_20261027.md` pour le périmètre et les exclusions. Aucune autorisation de fusion ou de déploiement implicite.

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

Target state: `.github/workflows/ci-scope-gate.yml` becomes the only pull-request workflow intended to run automatically by default. Until the migration of legacy workflows is completed and reviewed, existing automatic triggers remain authoritative.

Reusable workflows may keep `workflow_call` because it does not execute independently.

## Heavy workflow contract

Target contract for migrated certification workflows: preserve any runtime context they require, expose an explicit targeted invocation path, and stop consuming runners automatically unless an exception is separately justified, reviewed, and documented. Do not convert a workflow to manual-only if it depends on `github.event.pull_request` without first providing an equivalent explicit PR context.

## Human gate

Before running a heavy workflow, record:

- Goal;
- exact HEAD;
- reason the workflow is relevant;
- expected proof;
- whether a cheaper targeted test can answer the same question.

If relevance is not demonstrated, do not run it.
