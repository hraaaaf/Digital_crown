# FACAD Robert P3 — production typed evidence pathways, non-clinical

**Status:** research-only; public Robert demo fixture; PR #1065 DRAFT,
no merge, no deploy, `CLINICAL_NO_GO=true`.

## Verified on GitHub (24–25 October 2026)

The original P3 runner at commit `bb428fc31e2dc1b04b17d7135d75b28bcc7226a8`
was executed by [GitHub Actions push run 40142753170](https://github.com/hraaaaf/Digital_crown/actions/runs/40142753170),
where the **real, repository-versioned canonical V2 typed adapter** emitted
two available angular `MeasurementEvidence` items:

- `ILi/A-Pog` through `RICKETTS_L1_APOG_INCLINATION_CANONICAL_DEG_V2`,
  canonical identity `M_RICKETTS_L1_APOG_INCLINATION_DEG_V1`;
- `ILs/A-Pog` through `RICKETTS_U1_APOG_INCLINATION_CANONICAL_DEG_V2`,
  canonical identity `M_RICKETTS_U1_APOG_INCLINATION_DEG_V1`.

Eight tests passed. The canonical model run is **not** the full clinical
runtime/endpoint. Its six proposed FACAD->Digital Crown landmark identities
(`Ii`, `Iia`, `Is`, `Isa`, `A`, `Pog`) are research crosswalk
hypotheses, not anatomically validated. The FACAD coordinates are already in mm.
No Po/Or/FH, image orientation, image calibration, clinical evidence graph or
clinical patient record was fabricated.

## New extension: typed CRANIOM interincisal construction

The P3 runner next invokes **the original**
`backend.services.cephalo_construction_evidence_adapter.materialize_craniom_constructions`
on the same research landmark set. It expects only
`CRANIOM_U1_L1_INTERINCISAL_V1` to be `AVAILABLE`, checks:
the four required `U1_apex, U1_incisal, L1_apex, L1_incisal`,
a shared educational source ref,
`larger_supplementary_v1` angular convention, and an actual
`computed_angle_deg` rounded once by the versioned construction.
The source-locked typed method `CRANIOM_INTERINCISAL_DEG_V1` must map
to `M_INTERINCISAL_DEG_V1` without an alias.

On the rounded Robert demo point positions:
the unrounded math is approximately **140.661748°**;
the typed CRANIOM construction should emit **140.7°**;
FACAD displays **140.9°**.
That **0.2°** printed gap is within the mathematically conservative
**0.781°** coordinate + display quantization envelope documented in P2.

### Mandatory distinction

The interincisal result is a **typed `ConstructionEvidence`**, not a
`MeasurementEvidence` emitted by the complete
`adapt_craniom_measurements` path, because this would require the authentic
runtime `CephaloAnalysisResult` and image evidence which the demo exports do
not supply. Do **not** fabricate a runtime result from the displayed FACAD
numbers to get a green comparison. This P3 extension does **not** authorize
runtime display equivalence or a cross-vendor clinical parity assertion.

Similarly, `Facial cone angle` stays blocked: generic FACAD `Go–Me`
cannot replace the Ricketts-specific mandibular plane required by the
Digital Crown canonical taper, even where values are close.

## Scientific gate

P2 result on public demo: **3 geometric rounding-consistency candidates,
1 incompatible facial cone definition**. P3 now checks **two canonical V2
typed angles + one CRANIOM typed interincisal construction**.

No change to the canonical evidence ledger:
**0/45 clinically certified FACAD–Digital Crown numerical parities**.
Do not alter actual Ricketts equations, accepted landmark authority,
numeric tolerance policy, calibration semantics, or release gating
based solely on this operator-transcribed educational comparison.
