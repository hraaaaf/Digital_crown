---
name: implement-radiology-finding
description: Implement a structured radiology observation/finding contract with localization, evaluability, provenance, confidence semantics, and clinician review state.
allowed-tools: Read, Grep, Glob, Edit, Write, Bash
---
# Implement radiology finding

## Trigger
Use for a new panoramic/radiology observation taxonomy or finding state, not viewer styling.

## Hard gate
Stop on missing approved taxonomy source, unknown modality/anatomical scope, ambiguous localization, unknown confidence semantics, conflicting sources, or license uncertainty.

## Workflow
Define stable ID, canonical name, source IDs, observation type, modality, anatomical scope, localization/laterality requirements, image-quality prerequisites, evaluability, confidence provenance, allowed review states, differential links, reporting rules, limitations, version, and tests.

## Separation rule
Keep image observation -> candidate finding -> clinician-validated finding -> differential -> clinical diagnosis as distinct typed states. `not_detected` never means `absent`.

## Output contract
Return gate result, schema record, state transitions, tests, source/license status, and handoff.
