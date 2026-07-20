---
name: scientific-source-research
description: Research and register authoritative scientific sources when a task needs evidence, terminology, formulas, norms, product information, or licensing verification.
context: fork
allowed-tools: Read, Grep, Glob, WebSearch, WebFetch
---
# Scientific source research

## Trigger
Use for an exact scientific question or when another workflow is blocked by missing, contradictory, outdated, population-mismatched, or license-uncertain evidence. Do not trigger for cosmetic UI work that merely names a clinical module.

## Workflow
1. State one answerable question and intended implementation target.
2. Search official authority/standard, then scientific society, then primary publication or systematic review.
3. Open the source itself; a search snippet is not evidence.
4. Record date/version, jurisdiction, population, exact supported claims, limitations, contradictions, and license.
5. Add a candidate registry record with a stable ID. Never assign human approval.

## Blocking conditions
Return `insufficient-evidence`, `conflicting-sources`, or `license-blocked` when the claim cannot be supported safely. Do not select a convenient source to break a tie.

## Output contract
Return question, source records, rejected sources with reasons, conflicts, implementation limits, and recommended reviewer.

## Handoff
Return evidence to the invoking domain agent. Research never activates a rule.
