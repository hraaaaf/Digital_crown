# FACAD Robert P2 — Bound three angular candidates; forbid the facial-cone alias

**Scope:** Educational compatibility only. PR #1065 is DRAFT. GitHub Actions uses
only the de-identified public **Robert Example** fixture, transcribed from the
24 October 2026 FACAD 3.14.1.1111 operator exports. The primary six raw exports,
integrity manifests and screenshots remain on Google Drive; their GUI provenance
has **not** been independently audited. No patient case or diagnosis.

## What this test executes

- Fixture `audit/fixtures/facad_robert_public_example_20261024_v1.json` contains
  30 sagittal/vertical landmark pairs **already in millimetres**, rounded
  to **0.1 mm**, plus 9 FACAD 32F values and five FACAD 13F shared values.
- `audit/cephalo_facad_robert_public_ci.py` authenticates the fixture's
  byte-for-byte SHA-256; executes **original versioned** DC math-only modules
  by loading their source files from the same checkout. It never launches the
  web/BFF/API runtime or clinical adaptation layer.
- `audit/cephalo_facad_robert_p2_geometry_gate.py` checks the original
  DC Ricketts Atlas2009 profile and the seven-vendor-variants disposition.
  Three angles must agree with the displayed vendor measurements **within
  a mathematically conservative upper bound for decimal rounding**.

## Actual source-specific measurements

| FACAD label | Source construction | DC geometry executed | Gate |
| --- | --- | --- | --- |
| ILi/A-Pog | Ii–Iia against A–Pog | `ricketts_l1_apog_inclination_deg_v1`, measurement `M_RICKETTS_L1_APOG_INCLINATION_DEG_V1` | Rounding consistency candidate, **not** runtime adapter proof |
| ILs/A-Pog | Is–Isa against A–Pog | `ricketts_u1_apog_inclination_deg_v1`, measurement `M_RICKETTS_U1_APOG_INCLINATION_DEG_V1` | Rounding consistency candidate, **not** runtime adapter proof |
| InterIncisal | Incisor axial lines Is–Isa and Ii–Iia | **Actual CRANIOM adapter geometry** `craniom_interincisal_deg_v1(Isa, Is, Iia, Ii)` (instead of Steiner generic primitive); measurement `M_INTERINCISAL_DEG_V1` | Rounding consistency candidate, **not** full adapter proof |
| Facial cone angle | Generic Go–Me against N–Pog | Generic `ricketts_line_angle_acute_deg_v1` only | **FORBIDDEN alias** to `M_RICKETTS_FACIAL_TAPER_NPOG_MP_DEG_V1` |

The final row is **not a fourth anatomical match**. FACAD's “Facial cone
angle” uses **generic Go–Me**, but the canonical DC Ricketts tapered-facial
construction requires **MP_ANGLE_INFERIOR_Ricketts→Me**. This mismatch was
explicitly locked before P2 in
`docs/audits/CEPHALO_LOT08_RICKETTS32_FACAD_FINAL_SEVEN_RESOLUTION.md`.
Do not let a numerically close value create a dangerous same-name alias.

## Mathematical rounding envelope (degrees)

Each exported point coordinate represents a true coordinate within ±0.05 mm.
For a directed line vector, the difference of its two independently
rounded endpoint coordinates has **Euclidean norm ≤ √2 × 0.1 mm**. If the
observed line has length `L > √2 × 0.1`, the true direction can deviate
from the rounded direction by at most

`asin(√2 × 0.1 / L)` radians.

For an angle between two lines, the conservative bound is the sum of the
two angular bounds, plus **±0.05°** for FACAD display rounding to the
nearest tenth of a degree. The `min` or `max` supplementary angle
projection is 1-Lipschitz under perturbations, so it does not expand this
envelope. Calculations use values already in mm; **do not multiply a second
time by 0.038853 mm/pixel**.

`rounding consistent` says only that a displayed value may plausibly
come from the original, more precise marker positions. It is **not**
proof that anatomical landmarks, coordinate reflection, clinical angles,
signs, rounding methods or the Digital Crown adapter are clinically
equivalent. No slack tolerances are invented to mask large differences.

## Other gates stay active

- Convexity, Ii to A-Pog, Is to A-Pog and Li-EL require orientation by
  authentic anatomical Frankfort landmarks **P/Or** for the clinical signs;
  these were **absent** from this particular FACAD marker export.
- Upper lip length: FACAD defines **ANS–STs**; DC expects
  **ANS–manual labial commissure**. This is an explicit anatomical
  incompatibility, irrespective of a matching distance.
- In Ricketts 32F, seven FACAD-specific constructions (including facial
  cone angle, Xi-OL, Xi-PM/OL, Upper lip len, STi-OL, Mand arc and Mand len)
  cannot be silently aliased to DC clinical factors.
- Values for the other 36 factor occurrences, and vendor-display
  rounding and clinical cross-product comparisons, remain unobserved.

## CI and release policy

`python -m unittest -v audit.test_cephalo_facad_robert_p2_geometry_gate`
executes synthetic perturbation, integrity, reference-frame and
source-lock tampering tests. Then
`python -m audit.cephalo_facad_robert_p2_geometry_gate --github-summary`
evaluates the exact pinned public Robert fixture on GitHub Actions using the
checked-out DC math-only code.

Expected summary: **3 angular quantization-consistent candidates,
1 forbidden vendor anatomical alias, 0/45 clinical parities validated;
CLINICAL_NO_GO=true.** Do **not** merge or deploy based on this evidence.
Future work requires independent anatomical crosswalk and source-image
orientation, authentic missing landmarks, **complete clinical adapter**
execution under equivalent input and measurement protocol, and review of
measurement/rounding disagreement at the original (unrounded) precision.

There is no claim of FACAD license validation, real-patient validation, or
normative clinical calibration.
