# P6 Panoramic — Mendeley V3 provenance result

Status: **PASS — FIRST-PARTY SOURCE PINNED; NO SOURCE FDI GROUND TRUTH**

## Goal

Resolve the exact provenance and annotation semantics of Mendeley dataset `73n3kz2k4k` V3 before considering it for Digital Crown panoramic Phase A.

## Source

- dataset: `73n3kz2k4k`
- version: `3`
- DOI: `10.17632/73n3kz2k4k.3`
- record licence: `CC BY 4.0`
- probe: `scripts/p6_mendeley_v3_provenance_probe.py`
- semantic probe commit: `89521f94070b404bd09c4f0cb5e4ee5e55316b71`
- semantic probe run: `32910743873` — **SUCCESS**
- evidence artifact: `9586480059`
- artifact digest: `sha256:e965cf2c0d67027c8928b6539a43c74e8e781df2784ed78b593ebcbf77841b27`

## Exact inventory

- downloadable files: **111**
- total downloaded bytes: **84,254,649**
- root listing SHA256: `0e6c7480669cd552ddc437828f4d5c470e567d6281b05b083071a3fac00dfa52`
- `annotations.json` file id: `a061b0e7-7e30-469d-ad64-60b97ca78b7a`
- `annotations.json` SHA256: `b6de2c396cb76758227562798141a00fb5d769f9d8f9eb3919470f4ff23578bd`
- `annotations.json` size: `242,508 bytes`
- every downloaded file matched its declared size during the run.

## Annotation truth

Direct inspection of the first-party V3 `annotations.json` proves:

- image metadata entries: **107**
- images with regions: **25**
- total regions: **772**
- polygons: **676**
- polylines: **96**
- regions exposing a `Teeth` attribute: **540**
- exact raw `Teeth` value on all 540 such regions: empty string `""`
- scalar tooth-label tokens: **0**
- explicit FDI codes: **0**
- FDI-labelled regions: **0**
- `source_fdi_labels_present=false`
- `fdi_coverage_complete=false`
- `direct_fdi_ground_truth_ready=false`

## Correction of the earlier mirror finding

The previously inspected public preparation mirror was incomplete: it exposed only three annotated images and empty region attributes. That mirror was sufficient to reject its geometry-generated FDI as source truth, but it was **not** an exhaustive view of Mendeley V3.

The first-party probe now supersedes that mirror for inventory claims:

- V3 has **25**, not 3, images containing annotation regions;
- however, the conclusion on FDI remains unchanged and is now stronger: the source `Teeth` attributes are empty and contain **no FDI truth**.

No centroid ordering, tooth-type conversion, arch position or other geometry has been promoted to FDI ground truth.

## Decision

**ELIGIBLE AUXILIARY / RIGHTS-CLEARED IMAGE + SEGMENTATION SOURCE; NOT A DIRECT-FDI TRAINING CORPUS.**

Potential Digital Crown use is limited to roles compatible with the source truth, such as an image pool and tooth-region annotation aid, subject to deduplication and the clinician-controlled FDI protocol.

For Phase A, FDI ground truth must still be created or obtained under a rights-closed, traceable protocol. The canonical path remains `docs/P6_PANORAMIC_FDI_ANNOTATION_PROTOCOL.md`.

## Product boundary

This result does not authorize:

- geometry-derived FDI as ground truth;
- automatic pathology diagnosis;
- training a direct-FDI model from empty `Teeth` attributes;
- any clinical claim.

The active panoramic target remains tooth localization + FDI enumeration with practitioner-controlled clinical semiology.
