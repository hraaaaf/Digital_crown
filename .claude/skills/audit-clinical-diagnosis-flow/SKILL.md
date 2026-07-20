---
name: audit-clinical-diagnosis-flow
description: Read-only audit of history, examination, tests, imaging, findings, hypotheses, diagnosis, certainty, odontogram, and treatment-plan transitions.
context: fork
allowed-tools: Read, Grep, Glob, Bash
---
# Audit clinical diagnosis flow

## Trigger
Use for clinical-data or diagnostic-state audits, not cosmetic changes containing words like diagnosis or examination.

## Read-only workflow
Trace motive -> history -> symptom -> sign -> test result -> imaging observation -> finding -> hypothesis -> differential -> diagnosis -> treatment plan. Check missing fields, certainty, clinician confirmation, FDI numbering, absent-tooth contradictions, odontogram parity, hidden assumptions, prompt logic, and coherence bypasses.

## Blocking findings
Automatic confirmed diagnosis, one-finding shortcuts, silent contradiction resolution, invalid numbering, or treatment without explicit diagnostic state are blockers.

## Output contract
Return state map, findings, contradictions, source gaps, missing tests, and recommended owner.

## Forbidden
Audit only; no edits or silent corrections.
