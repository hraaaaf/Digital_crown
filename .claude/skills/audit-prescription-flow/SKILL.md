---
name: audit-prescription-flow
description: Read-only audit of the prescription path from examination and diagnosis through medication selection, validation, persistence, and PDF.
context: fork
allowed-tools: Read, Grep, Glob, Bash
---
# Audit prescription flow

## Trigger
Use for prescription safety/consistency audits. Do not trigger for button colors, typography, or layout-only changes.

## Read-only workflow
Trace examination -> diagnosis -> medication identity -> dose expression -> validation -> persistence -> PDF. Inspect age, weight, allergies, interactions, contraindications, pregnancy, renal/hepatic context, units, concentration, route, frequency, duration, maximum, stewardship, hardcoded values, duplicates, prompts, and UI/API/DB/PDF parity.

## Forbidden
Do not modify code, data, rules, tests, or fixtures during the audit. Report even trivial findings; a separate task may fix them.

## Output contract
Return route map, findings by severity, evidence gaps, duplicate rules, missing tests, and recommended next skill.

## Handoff
Research gaps to scientific-source-research; approved fixes to pharmacology-engineer; then test and review.
