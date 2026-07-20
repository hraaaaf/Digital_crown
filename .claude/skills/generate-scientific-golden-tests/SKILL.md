---
name: generate-scientific-golden-tests
description: Create independent scientific golden, property-based, and metamorphic tests using synthetic or explicitly approved non-patient data.
allowed-tools: Read, Grep, Glob, Edit, Write, Bash
---
# Generate scientific golden tests

## Trigger
Use after a contract and independent expected-result source exist.

## Hard gate
Stop if expected results would be copied from the implementation, invented by an LLM, derived from patient data, or sourced from an unapproved/licence-uncertain example.

## Workflow
Classify oracle provenance; generate synthetic inputs; encode exact expected behavior and tolerances; add negative, boundary, contradiction, property, metamorphic, serialization, and privacy cases. Store no identifiable metadata.

## Minimum scenarios
Pharma: missing context, allergy, interaction, concentration and maximum. Diagnosis: absent/invalid tooth, missing tests, contradiction. Cephalo: missing/moved point, scale, sign, degenerate geometry. Radiology: mirror/laterality, non-evaluable image, missing localization, metadata leak, unauthorized access.

## Output contract
Return fixture policy, oracle source/derivation, tests, tolerances, commands, and limitations.
