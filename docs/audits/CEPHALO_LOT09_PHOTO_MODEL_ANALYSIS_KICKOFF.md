# Digital Crown Cephalo 2.0 — LOT09 Photo & Dental-Model Analysis Studio — Kickoff

Date: 2026-10-04  
Branch: `feat/ortho-studio-lot09-photo-model-analysis`  
Base: `master@19a91889b8b60ea97e49f717909be9cc83fdf919`

## Goal
Integrate orthodontic arch/model analysis through two explicitly separated pathways without creating unsupported clinical authority:

1. Photo-direct validated measurements.
2. Real/reconstructed 3D model analysis.

## Gate
`ORTHO_MODEL_ANALYSIS_VERIFIED`

LOT09 is OPEN. This kickoff does not satisfy the gate.

## Locked constraints
- ZERO LLM runtime for clinical decision logic.
- Clinician authority remains final.
- No photo-derived millimetres without method-specific validated metric proof.
- Five-photo reconstruction is not equivalent to IOS/cast until validated against reference geometry in the Digital Crown target workflow.
- Segmentation alone is not a model-analysis engine.
- No external model/checkpoint is product-eligible until licence, reproducibility, local performance, privacy/data path, and failure behaviour are reviewed.
- Missing scale, unsupported acquisition, missing tooth identity, or out-of-domain input must fail closed.

## A0 — Evidence / applicability manifest before product code

### Candidate 1 — single occlusal photograph
Source: Hertig et al., European Journal of Orthodontics 2025, DOI 10.1093/ejo/cjaf025; public companion repository `nnistelrooij/crowding`.

Observed supported claim:
- mandibular anterior crowding and Little Irregularity Index from a single occlusal intra-oral photograph.

Published evaluation:
- 125 untreated subjects;
- crowding ICC 0.900, MAD 0.36 mm;
- Little index ICC 0.930, MAD 0.74 mm.

Published limitation:
- not trained on interdental spacing;
- reliability outside tested crowding severity not established.

Repository licence status at kickoff:
- no repository licence file observed in the public root.
- Therefore: BENCHMARK / R&D only; not product-eligible for code/model reuse until rights are clarified.

### Candidate 2 — real 3D models
Source: `amir-abdi/OrthoAid`.

Observed capabilities:
- occlusal/sagittal planes;
- tooth inclination;
- serial model superimposition;
- landmark distances;
- arch curvature / arch-wire matching.

Repository licence:
- MIT observed.

Status:
- BENCHMARK / potentially reusable engineering reference subject to dependency/provenance review.
- Does not by itself validate Digital Crown clinical measurement definitions.

### Candidate 3 — SlicerOrthodonticAnalysis
Observed capabilities:
- model space discrepancy;
- Bolton;
- Peck & Peck;
- landmark-driven reports from image/model.

Licence status at kickoff:
- no licence file observed in the public repository root.

Status:
- BENCHMARK only until licensing and method-source provenance are clarified.

## First implementation boundary
No model inference or clinical product logic yet.

The first executable LOT09 sub-lot must be a deterministic input/measurement contract that:
- distinguishes PHOTO_2D, IOS_3D, CAST_3D, and PHOTO_RECONSTRUCTED_3D;
- records acquisition provenance and scale authority;
- records tooth/landmark identity;
- declares supported measurement IDs;
- returns explicit NOT_COMPUTABLE / OUT_OF_SCOPE states;
- prevents photo-reconstruction output from silently masquerading as IOS/cast geometry.

## Required proof before first clinical measurement activation
- source-locked measurement definitions;
- independent oracle;
- synthetic/reference fixtures;
- negative/fail-closed cases;
- exact-HEAD tests;
- two adversarial perspectives;
- confirmation pass;
- later human/clinical validation against casts/IOS where required.

## Immediate next
LOT09-A0: inventory existing Digital Crown photo/model/mesh code and data paths, then write the typed domain contract and test plan before any measurement implementation.

No merge. No deployment.
