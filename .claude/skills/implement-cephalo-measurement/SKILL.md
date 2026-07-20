---
name: implement-cephalo-measurement
description: Implement one deterministic cephalometric measurement after formula, landmarks, sign, units, calibration, profile separation, and source approval are verified.
allowed-tools: Read, Grep, Glob, Edit, Write, Bash
---
# Implement cephalometric measurement

## Trigger
Use for requests such as adding Wits, SNA, a distance, angle, or landmark-derived metric. Styling a cephalo screen does not trigger it.

## Hard gate
Create the schema record first. Stop if original/method source is not clinician-approved, formula or landmarks are ambiguous, unit/sign/orientation is unknown, sources conflict, license is uncertain, or the requested norm population is unknown. Formula approval and norm-profile approval are separate gates.

## Workflow
Define canonical name, analysis, source IDs, landmarks and aliases, directed formula, unit, sign convention, orientation/calibration dependency, full-precision computation, display precision, norm profile IDs, missing/degenerate behavior, dependency graph, limitations, and tests. Never use an LLM for geometry.

## Tests
Use independent synthetic geometry for translation/scale, resolution, orientation/sign, calibration, point movement, transitive recalculation, missing point, degenerate geometry, rounding separation, and PDF parity.

## Output contract
Return gate result, measurement record, dependency changes, tests, profile status, and handoff.
