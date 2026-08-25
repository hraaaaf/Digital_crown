# P6 Cephalometry — Clinical Validation Protocol

Status: **PREPARED — NOT YET EXECUTED / NOT A CLINICAL CERTIFICATION**

## Goal

Determine whether the selected `DC-Ceph-UNet29Q4 / Aariz v1` candidate can safely support **clinician-supervised** cephalometric landmarking in Digital Crown on the 20 directly supported landmarks, without fabricating unsupported geometry or turning a technical benchmark into an unearned clinical-equivalence claim.

## Success

The protocol is successful only if all gates below are met on a locked model, locked preprocessing pipeline and prospectively frozen evaluation set:

1. reference annotations are created independently by qualified clinicians and adjudicated without access to model output;
2. the exact production candidate binary and preprocessing are pinned by SHA256/version;
3. performance is reported globally, per landmark, per device and on predefined difficult-case strata;
4. human inter/intra-observer variability is measured on the same validation material;
5. downstream cephalometric measures are assessed only when all required landmarks are directly supported and clinically reviewable;
6. unsupported `Occ_Ant` / `Occ_Post` remain unavailable/manual and are never synthesized;
7. every automated result remains clinician-reviewable/editable before clinical use;
8. no claim of clinical equivalence, diagnostic autonomy or medical-device certification is made from this protocol alone.

## Current locked technical candidate

- model: `DC-Ceph-UNet29Q4 / Aariz v1`
- ONNX SHA256: `809f1d3d2347d2a34f57d4a3415bb319c29f8a25c325d41160e5f28d4e5dadad`
- size: `7,624,307 bytes`
- input: `[1,1,512,512]`
- output: `[1,29,128,128]`
- direct Digital Crown mapping: 20/22 canonical points
- unsupported product points: `Occ_Ant`, `Occ_Post`
- sealed Aariz test, direct-20 technical result:
  - MRE `1.232893 mm`
  - SDR2 `83.1333%`
  - SDR4 `97.2667%`
- technical training run: `32876308676`
- clinical claim: **false**

These numbers are a research baseline only. They are not the acceptance result of this protocol.

## Scientific rationale

The Aariz dataset used a multi-clinician annotation and review process across 1,000 cephalograms from seven imaging devices. Its published technical validation explicitly measured inter-observer variability and corrected difficult landmarks through repeated review.

The cephalometric literature also shows that landmark reliability is landmark-dependent and that inter-examiner error can exceed intra-examiner error. Therefore Digital Crown must not validate only an aggregate MRE.

Recent systematic-review evidence on automatic cephalometric landmarking supports continued expert supervision rather than autonomous clinical use. The validation design therefore treats the model as augmented intelligence, not a replacement for the clinician.

## Scope

### In scope

The 20 directly mapped Digital Crown landmarks covered by the selected candidate:

`S, N, Po, Or, A, B, Go, Me, U1i, U1a, L1i, L1a, Prn, Pog_soft, Sn, Ls, Li, Co, Gn, ANS`

### Out of scope

- automatic construction of `Occ_Ant` or `Occ_Post`;
- automatic Wits when the occlusal plane is unavailable;
- automatic pathology diagnosis;
- treatment recommendation;
- autonomous orthodontic diagnosis;
- any regulatory certification claim.

## Validation design

### Phase 0 — Model and pipeline freeze

Before first validation annotation is compared with the model:

- pin ONNX SHA256;
- pin exact landmark ontology and title-keyed adapter;
- pin resize/letterbox and inverse-coordinate transform;
- pin decoder;
- pin calibration/mm-per-pixel handling;
- pin Digital Crown measurement engine version;
- record OS/runtime versions used for inference.

Any change to these items invalidates the result for the changed candidate and requires a new validation run.

### Phase 1 — Validation image set

Use a **prospectively frozen, de-identified** lateral-cephalogram set representative of the intended cabinet population and devices.

Minimum engineering target before a release decision: **100 independent cephalograms** not used for model training, validation, tuning or threshold selection.

This `n=100` is a pragmatic engineering gate, not a regulatory power calculation. A formal clinical study or regulatory claim requires its own prospective sample-size justification.

The set should include, where available:

- more than one acquisition device;
- mixed image resolutions;
- common positioning variation;
- metallic restorations / orthodontic appliances;
- mixed dentition and permanent dentition where clinically relevant;
- soft-tissue visibility variation;
- difficult `Po`, `Or`, `Go`, `Co` cases;
- images that would normally require manual correction.

Record device and difficulty strata without patient identifiers.

### Phase 2 — Human reference standard

Reference annotations must be produced **without viewing the model output**.

Recommended panel:

- annotator A: qualified clinician trained in lateral cephalometric tracing;
- annotator B: second independent qualified clinician;
- adjudicator: experienced orthodontist for disagreements or predefined difficult cases.

For a predefined reliability subset, both primary annotators repeat the trace after a washout period to estimate intra-observer variability.

Store:

- each raw annotation separately;
- adjudicated reference coordinates separately;
- annotator role and calibration session;
- no patient-identifying data.

Do not average away a clinically meaningful disagreement before it is reviewed.

### Phase 3 — Blinded model inference

Run the exact frozen model once on the locked set.

For every case retain:

- original image dimensions;
- calibration;
- model coordinates before and after inverse transform;
- heatmap/decoder quality signal if available;
- final direct-20 coordinates;
- inference runtime;
- explicit missing/fail-closed state.

The model must never generate `Occ_Ant` or `Occ_Post` from geometry during this phase.

## Primary metrics

Report all of the following:

### Localization

- mean radial error (MRE), mm;
- median radial error, mm;
- 95th percentile radial error;
- SDR at `≤2.0`, `≤2.5`, `≤3.0`, `≤4.0 mm`;
- per-landmark MRE/median/P95/SDR;
- per-device and predefined difficult-stratum results.

The commonly reported 2 mm threshold is an evaluation convention, not a universal clinical-acceptability law.

### Human variability

On the same material:

- inter-observer radial error per landmark;
- intra-observer radial error on the repeat subset;
- systematic coordinate bias where relevant;
- confidence intervals.

AI error must be interpreted against the measured human variability for the same landmark, not against a single global number.

### Downstream measurements

Only evaluate a derived measurement if every required landmark is directly available and the production implementation uses the same geometry.

Report absolute error and agreement for relevant supported measures, including as applicable:

- SNA;
- SNB;
- ANB;
- IMPA;
- I/Frankfort;
- inter-incisal angle;
- FMA/Tweed;
- linear/soft-tissue measures supported by direct points.

Use Bland–Altman style agreement analysis for continuous downstream measures in addition to mean absolute error.

Wits is excluded until the occlusal plane has its own validated definition.

## Release gates

### Gate C1 — Reproducibility

PASS only if:

- exact model SHA and pipeline version are recorded;
- repeated inference on the same input is deterministic within the documented numerical tolerance;
- coordinate transforms round-trip correctly on representative resolutions;
- evidence bundle can be regenerated from a clean environment.

### Gate C2 — Reference-standard integrity

PASS only if:

- two independent clinician annotations exist;
- adjudication rules were frozen before model comparison;
- model output was hidden during reference creation;
- inter/intra-observer variability is reported.

### Gate C3 — Landmark performance

No single aggregate metric is sufficient.

Release requires:

- direct-20 aggregate MRE remains below `2.0 mm`;
- SDR2 is reported and must not materially collapse relative to the locked external Aariz result;
- every landmark is individually reviewed;
- landmarks whose error is materially worse than expert variability are either corrected by a documented manual-review requirement or removed from automatic availability.

The `2.0 mm` aggregate threshold is an engineering release gate aligned with common cephalometric-AI reporting practice, not a statement that every error below 2 mm is clinically harmless.

### Gate C4 — Safety / fail-closed behavior

PASS only if:

- missing or invalid model asset disables automation;
- unsupported landmarks are never synthesized;
- invalid ontology/order fails closed;
- low-quality/ambiguous output can be corrected manually;
- derived measures depending on unavailable landmarks are not silently produced.

### Gate C5 — Clinician workflow

PASS only if a clinician can:

- see the detected landmark;
- move/correct it;
- identify that a point is automated vs manually corrected where useful;
- recompute measurements after correction;
- finish the case without accepting an unsafe automatic point.

### Gate C6 — Clinical claim boundary

Even if C1–C5 pass, the permitted product claim remains:

> clinician-supervised automatic landmark assistance.

It does **not** become:

- autonomous orthodontic diagnosis;
- clinical equivalence to an orthodontist;
- validated treatment recommendation;
- regulatory certification.

Any stronger claim requires a separately designed clinical/regulatory study.

## Edge-case failure set

Maintain a separate, non-training failure set containing examples such as:

- unclear Porion/Orbitale;
- superimposed bilateral structures;
- severe asymmetry/positioning error;
- incomplete field of view;
- appliance artefact;
- very low contrast;
- mixed dentition;
- image/calibration metadata anomaly.

A release candidate must be checked against this set after any model/preprocessing change.

## Evidence bundle

A completed validation must produce:

- `model_manifest.json`
- `validation_set_manifest.json` with de-identified case IDs only
- `reference_annotation_manifest.json`
- `inference_manifest.json`
- `landmark_metrics.json`
- `observer_variability.json`
- `measurement_agreement.json`
- `failure_cases.json`
- `clinical_review_signoff.md`
- hashes for every evidence file

No radiograph or PHI is committed to the public application repository.

## Human gate

Before enabling the new cephalometric candidate in clinical cabinet mode, an experienced orthodontic reviewer must inspect:

1. per-landmark errors;
2. difficult-case failures;
3. downstream angle/linear agreement;
4. the manual-correction UX;
5. unsupported Wits behavior;
6. final claim wording.

This is a genuine human clinical gate and cannot be auto-approved by CI.

## References

1. Aariz benchmark dataset: *A Benchmark Dataset for Automatic Cephalometric Landmark Detection and CVM Stage Classification*, Scientific Data, 2025. DOI `10.1038/s41597-025-05542-3`.
2. Trpkova B, Major P, Prasad N, Nebbe B. *Cephalometric landmarks identification and reproducibility: a meta analysis*. Am J Orthod Dentofacial Orthop. 1997. DOI `10.1016/S0889-5406(97)70242-7`.
3. Lin YM, et al. *The accuracy of artificial intelligence in identifying cephalometric landmarks: A scoping review*. 2026. DOI `10.1016/j.ortho.2026.101205`.
4. *Automatic cephalometric landmark identification with artificial intelligence: An umbrella review of systematic reviews*. 2024. PubMed PMID `38729291`.
5. Vasey B, et al. DECIDE-AI. *Reporting guideline for the early stage clinical evaluation of decision support systems driven by artificial intelligence*. BMJ 2022;377:e070904. DOI `10.1136/bmj-2022-070904`.

## Current status

Protocol prepared only. No clinical image set has been frozen, no human reference annotations have been collected under this protocol, and no clinical release gate is currently claimed as passed.
