# Agent handoff protocol V2

## Payload

```yaml
task: ""
domain: ""
change_kind: audit | research | contract | implementation | test | review
agent: ""
rule_owner: ""
files_read: []
files_changed: []
source_ids_used: []
source_claims_used: []
assumptions: []
unknowns: []
contradictions: []
decisions: []
blocked_items: []
risks: []
tests_run: []
test_oracle_provenance: []
review_required: true
human_clinical_approval_required: true
next_agent: ""
```

## Routing

- Established domain-local change: domain engineer -> test engineer -> reviewer.
- New shared contract, multi-domain dependency, or migration: architect -> domain engineer -> test engineer -> reviewer.
- Missing/conflicting/licence-uncertain evidence: source research -> domain engineer only after gate resolution.
- Audit request: audit skill -> report only; a separate implementation task is required.
- Database change: architect -> user-invoked migration skill -> test engineer -> reviewer.

The main Claude Code session performs sequencing because subagents cannot spawn subagents. The reviewer must not be the authoring agent.

## Stop states

blocked_missing_approved_source, blocked_conflicting_sources, blocked_unknown_unit, blocked_unknown_population, blocked_ambiguous_formula, blocked_license_uncertain, blocked_patient_data, blocked_production_migration.

