---
name: validate-cephalo-pipeline
description: Read-only validation of cephalometric import, orientation, calibration, landmarks, manual correction, dependency recalculation, measurements, normative comparison, interpretation, and report.
context: fork
allowed-tools: Read, Grep, Glob, Bash
---
# Validate cephalometric pipeline

## Trigger
Use for cephalo pipeline audits or regression validation, not for implementing a new metric.

## Workflow
Trace import -> orientation -> calibration -> landmarks -> correction -> full-precision measurements -> validation -> selected norm profile -> interpretation -> report/PDF. Verify transitive dependencies, storage precision, displayed rounding, profile selection, model/source versions, and explicit non-evaluable states.

## Required tests
Resolution and translation invariance; scale/calibration behavior; point-move recalculation; missing landmarks; degenerate geometry; sign/orientation; wrong profile; and PDF parity.

## Forbidden
No edits and no acceptance based solely on existing tests.

## Output contract
Return pipeline map, failed invariants, blocker list, evidence gaps, and missing tests.
