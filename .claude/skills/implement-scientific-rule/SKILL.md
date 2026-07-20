---
name: implement-scientific-rule
description: Implement a deterministic scientific rule only after its sources, units, population, prerequisites, missing-data behavior, and approval status are explicit.
allowed-tools: Read, Grep, Glob, Edit, Write, Bash
---
# Implement scientific rule

## Trigger
Use for deterministic clinical/scientific logic. Do not use for pure terminology, styling, documentation-only research, or model-generated narrative.

## Hard gate
Before editing, verify every claim source exists in the registry and is `approved-by-clinician` with named human reviewer and date. Otherwise stop with `blocked_missing_approved_source`. Also stop on conflicting sources, unknown unit/population, ambiguous formula, or license uncertainty.

## Workflow
Define stable ID/version, inputs and units, applicability population, prerequisites, exclusions, deterministic logic, explicit missing-data behavior, outputs, limitations, provenance, activation state, and tests. Keep rule data outside prompts. Increment version for logic changes.

## Output contract
Return gate result, contract path, source IDs, code/tests changed, version change, and unresolved risks.

## Handoff
Scientific-test-engineer then independent scientific-reviewer.
