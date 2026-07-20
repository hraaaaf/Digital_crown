---
name: audit-panoramic-report-pipeline
description: Read-only audit of panoramic upload, storage, access, processing, image quality, candidate findings, clinician validation, report, and PDF.
context: fork
allowed-tools: Read, Grep, Glob, Bash
---
# Audit panoramic report pipeline

## Trigger
Use for imaging pipeline, report consistency, privacy, or review-state audits; not image-viewer cosmetics.

## Workflow
Trace upload -> content validation -> authenticated storage -> metadata handling -> orientation/quality -> processing -> observations -> candidate findings -> validation -> report/PDF. Check tenant access, path safety, MIME/magic bytes, laterality, tooth localization, evaluability, confidence semantics, model/prompt version, provenance, and metadata leakage.

## Blocking findings
Public media, patient fixtures, diagnosis from model output, `not_detected = absent`, report without reviewer state, or unknown dataset/model license.

## Forbidden
Audit only; no code, image, model, or dataset modification.

## Output contract
Return threat/pipeline map, blockers, evidence gaps, missing tests, and owner.
