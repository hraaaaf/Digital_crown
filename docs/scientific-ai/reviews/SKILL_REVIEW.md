# Skill review

## Verdict

The original 11 skills and evals were near-identical copies and lacked SKILL.md frontmatter. V2 gives every skill a distinct trigger, scope, workflow, blocker set, output contract, and handoff.

| Skill | Verdict | Routing | V2 correction |
|---|---|---|---|
| scientific-source-research | VALID_AFTER_CHANGE | High | Direct-source and license/conflict workflow |
| implement-scientific-rule | VALID_AFTER_CHANGE | High | Human-approved evidence hard gate |
| audit-prescription-flow | VALID_AFTER_CHANGE | High | Read-only prescription checklist |
| audit-clinical-diagnosis-flow | VALID_AFTER_CHANGE | High | Typed-state audit and diagnosis blockers |
| implement-cephalo-measurement | VALID_AFTER_CHANGE | High | Separate formula/profile gates |
| validate-cephalo-pipeline | VALID_AFTER_CHANGE | High | Read-only numeric/pipeline invariants |
| implement-radiology-finding | VALID_AFTER_CHANGE | High | Observation-to-diagnosis separation |
| audit-panoramic-report-pipeline | VALID_AFTER_CHANGE | High | Auth, metadata, quality and report audit |
| generate-scientific-golden-tests | VALID_AFTER_CHANGE | High | Independent oracle only |
| scientific-database-migration | VALID_AFTER_CHANGE | High | User-only, isolated, additive workflow |
| review-scientific-pull-request | VALID_AFTER_CHANGE | High | Independent read-only blockers |

## Collision routing

New measurement routes to implement-cephalo-measurement; full pipeline evidence adds validate-cephalo-pipeline. New finding routes to implement-radiology-finding; pipeline audit remains read-only. A dose rule starts with source research when evidence is missing. Persistence changes start with architect and require user-invoked migration.

Each eval now has positive, negative, ambiguous, collision, and dangerous under-specified cases. Audit skills never edit. Implementation skills never self-review.

