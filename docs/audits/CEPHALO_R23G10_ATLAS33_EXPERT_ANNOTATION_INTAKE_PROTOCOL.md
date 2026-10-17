# Digital Crown — CEPH-UXCLIN-01 / R23-G10 — Atlas33 expert goldset intake

**2026-10-17 — PREPARATION ONLY / CLINICAL NO-GO — desktop cephalometry.**

## Objective, existing evidence and limits

R23-G10 prepares the **protected manual-annotation campaign** needed to check the Ricketts Atlas 2009 33-factor anatomical source chain. It does not create a goldset, measure a human image, authorize runtime Focus or turn a dataset coordinate into independently verified clinical anatomy.

Upstream: LOT02 Aariz source [Figshare CC BY 4.0](https://doi.org/10.6084/m9.figshare.27986417.v1), already qualified for **LOT02 only**: 1,000 cephalograms, 29 annotated points, seven devices, 700/150/150 train/valid/test, immutable source manifest SHA-256 `73c742db47686b0cf8b75b599b6373d3fc707d9b25a440c8d81d3d99ced241df`. The junior/senior reference files represent expert-group annotations, **not necessarily two independent raw observations**. G9's [strict 33-factor source ledger](schemas/cephalo_r23g9_atlas33_aariz_compatibility_preflight_v1.json) identifies 21 missing literal source-specific landmark identities: those are **not** validated by Aariz, and naming proximity must never substitute for anatomical equivalence. LOT03 landmark definitions, W1/W2/W3 contracts and canonical backend constructions remain the source authority.

At PRE, the authorized Aariz workstation `DESKTOP-3MAJEEH` was **OFFLINE**. The corpus was therefore not accessed, rehashed or annotated in this execution.

## Protected expert workflow

**1. Access and immutable provenance.** On an authorized workstation, use the previously qualified local LOT02 material. Before the first new annotation, recompute the actual frozen manifest SHA and verify each image byte hash, dimensions, dataset use rights, calibration source and split. Bind every record to one unambiguous `case_id` and source-image SHA-256. Keep image bytes, real clinical identifiers, local file paths and expert coordinate files strictly in protected storage; **no upload to GitHub, Actions, Notion, chat or public artifacts**. Version the true validation substrate without exposing data.

**2. Preregister the selection.** Use `train` and `valid` for development of the anatomical protocol; reserve the 150-case LOT02 `test` cohort untouched. Do not mix original model-training/evaluation roles, and record exposure/contamination. A future untouched or external final clinical acceptance dataset needs independent authorization, frozen before results.

**3. Two actual independent experts.** Assign at least two appropriately qualified orthodontists to independently place **all 21 source-specific identities** on the **same images**, blinded to each other, the candidate detector and later adjudicated points. Record verifiable real expert qualifications, source protocol versions, signed time-stamped evidence and study ethics/rights in a protected governance dossier. Pseudonymous tokens in the intake manifest are assignment references **only**; they do not prove credentials, blindness or actual annotations. Predeclare repeat subset/interval for intraobserver reliability and adjudication procedure before reference unblinding. Retain disagreements, invalid and non-computable cases in denominators; do not silently average them.

**4. Exact anatomy and construction chain.** The 21 names come from G9, including `Po_anatomic`, `Pog_hard`, `Pt_Ricketts`, `PR_Ricketts_PTV`, `Pm_Ricketts`, `PNS_Ricketts`, `R1_Ricketts`…`R4_Ricketts`, FOP-specific anchors, distal molar and canine markers. Never replace with generic `Po`, `Pog`, McNamara PTM, arbitrary molar points or screen-space planes. **Derived Xi, PTV, CF, CC, constructed Gn and mandibular plane are source-locked constructions**, not clinical landmarks invented by the UI. G9 aggregate-descriptor gaps for #20 Gn and #22 FH must refer to actual versioned canonical constructors; they are not evidence of absent source points.

**5. Calibration/orientation.** Every signed/linear endpoint must have independently checked same-image `mm_per_pixel` provenance (source, verifier, timestamp, uncertainty), and explicit orthogonal anatomical superior/anterior vectors with mirror state, acquisition/manual-verification provenance and audit evidence. Pixels, screen-Y or plausible-looking drawings cannot substitute. A pending/missing verification remains `NOT_COMPUTABLE`.

**6. Scientific readout — LATER, not G10.** Before results: freeze per-landmark/factor clinical tolerance and error policy, device strata, case selection, sign/unit conventions, observer-repeat analysis and handling of ambiguity. After actual annotations, independently compare each value against a separately computed oracle, quantify point error (mm plus X/Y), signed/absolute angular/linear deviations, systematic bias and limits of agreement, inter-/intraobserver reliability, percentage `NOT_COMPUTABLE` and sample exclusions. LOT04 engineering detector-selection tolerances are **not** universal clinical release cutoffs.

## Source-only implementation and reproducible checks

- `docs/audits/schemas/cephalo_r23g10_atlas33_annotation_intake_template_v1.json`: **zero-case** checked-in assignment template; explicitly no pixels, coordinates, patient data, expert signoffs, clinical authority or upload.
- `scripts/cephalo_r23g10_annotation_intake.py`: strict key allowlist, frozen DOI/manifest SHA, exact G9 21-ID checks, two distinct blinded assignment tokens, split protection, refusal of self-declared verification, optional **protected local** LOT02 original-manifest file SHA and case/split/source-hash linkage. Output is **aggregate structural status only** and `clinical_release=false` even when all checks pass.
- `audit/cephalo_r23g10_contract_tests/test_intake.py`: only synthetic assignment metadata; tests forbid missing/aliased points, forged clinical authority, payloads, leak/upload, same reviewer twice, forced calibration/orientation, contaminated test and wrong source hashes.
- `.github/workflows/cephalo-r23g10-intake.yml`: experimental exact-HEAD source-only CI, no images or model weights.

**Local execution example**, only when the protected frozen LOT02 manifest has been independently materialized and its bytes checked:

```bash
python -m scripts.cephalo_r23g10_annotation_intake \
  --intake <PROTECTED_LOCAL_ASSIGNMENTS.json> \
  --source-manifest <PROTECTED_FROZEN_LOT02_MANIFEST.json>
```

Do not copy either private file into the repo. The CLI **does not** check actual image bytes or annotation placement, only frozen manifest identity and source-image hash references; those must be audited separately on the authorized workstation. Without this source manifest, the empty GitHub template proves **zero** bound cases.

**Gate/exit:** technical PASS only for source inventory/assignment-validator structure and exact-head tests. Never `ATLAS33_CLINICAL_GOLDSET_READY`, independent expert review, patient-source validation, clinical release, merge or deployment from this lot. A genuine goldset requires actual blinded expert annotation, independently checked image calibration/orientation and clinical review on a protected dataset.

**Roadmap:** W1/W2/W3 descriptors ✓ → G9 strict compatibility ✓ → G10 protected intake preparation → actual expert campaign **BLOCKED pending authorized workstation + humans** → independent anatomical/measurement validation → clinical human GO/NO-GO → separate closeout.
