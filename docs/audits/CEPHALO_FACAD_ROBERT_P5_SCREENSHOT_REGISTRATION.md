# FACAD Robert P5 — Screenshot-overlay congruence (non-clinical)

**Status:** SCREENSHOT/EXPORT PIXEL-ALIGNMENT EVIDENCE ONLY. `CLINICAL_NO_GO=true`.
PR #1065 remains DRAFT; no merge, deployment or runtime activation.

## Inputs (not in public repository)

An operator-supplied screenshot of the **Robert Example** tracing was examined
privately on 25 October 2026. It is a 1920 × 1080 PNG showing the actual
lateral-cephalogram background and red overlay tracing. The screenshot also
contains application UI and example-case demographics; **the screenshot itself
must NEVER be committed to this public repository, included in GitHub Actions
artifacts or printed in CI**. The screenshot's analysis pane visibly says
**“Bergen short”**, **not “Ricketts (32 F)”**.

The comparison uses the already de-identified, pinned
`audit/fixtures/facad_robert_public_example_20261024_v1.json` fixture:
**30 metric coordinate pairs** at nominal 0.1-mm decimal precision, no
second multiplication by the source application's mm/pixel calibration factor.

## Screen alignment experiment: private, manually anchored

Two visually recognizable overlay point rings (`S`, `N`) were located
manually on the screenshot, refined with local red-pixel centroids, and
used to solve the **two-point similarity transform** from exported
metric coordinates to screenshot pixel coordinates. The transform may contain
uniform scaling, translation and a very small rotation. With these two
anchors, fitting the anchors proves **nothing independent**.

The 28 *remaining* landmarks were then projected through the same fixed
transform. Under a strict image criterion of **at least 3 strongly red pixels
within 4 screen pixels** of each projected position:

- **27 / 28 out-of-sample positions** exhibit nearby red tracing pixels;
- **29 / 30 positions overall**, including both fitting anchors, exhibit them;
- the one apparent nonmatch is the soft-tissue chin reference in a part of
  the screenshot **covered by a UI preview/tooltip**.

These counts are **screen overlay proximity**, not independent detection or
clinical validation of named circles. Nearby tracing strokes can also
satisfy a red-pixel test. The screenshot does not show an independent
coordinate-to-name table for all markers; anatomical labels have not been
reconfirmed by a clinician on the source image. The visible analysis
is Bergen short, so this image alone **cannot substantiate the Ricketts
32F/13F output values**, even when screenshot/export case context and overlay
positions are consistent.

Screenshot pixel statistics and human-chosen anchors remain only in the
**local/private** audit record and are not carried into CI.

## Reproducible code and synthetic CI

`audit/cephalo_facad_p5_overlay_registration.py` takes a screenshot
and a **local, explicit 2-anchor JSON** through CLI, and can output
aggregate-only screen concordance without OCR, demographic extraction
or returning the image itself. It consumes only the byte-exact hashed
public educational coordinate fixture in the checkout.
`audit/test_cephalo_facad_p5_overlay_registration.py` runs synthetic
color masks and geometry only; **the real screenshot is deliberately
never downloaded to a GitHub runner**.

The mathematical finding **does not alter**:

- P4's true Digital Crown canonical identity gate: uncertified vendor
  `Pog` must **not** become clinically `Pog_hard`.
- P3's two exploratory angular `MeasurementEvidence` values and
  InterIncisal `ConstructionEvidence` remain nonclinical.
- All signed angular/linear, manual-anatomy and missing Frankfort-point gates.
- The clinical parity ledger stays **0/45**, `CLINICAL_NO_GO=true`.

## Before image-level clinical certification

An operator/clinician must verify each exact anatomical identity and
its associated selected tooth on the full, unobstructed same-trace
source image, independently of this coordinate-guided overlay.
The provenance must be attached to the canonical evidence pipeline
through its **approved** identity-bridge policy; generic manually renamed
FACAD `Pog` remains insufficient.

Separate measurement-set validation must use the Ricketts 32F and 13F
analysis outputs, not a screenshot with the Bergen short pane selected.
