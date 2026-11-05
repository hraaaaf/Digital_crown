# Céphalo 2.0 / Bergen Short — B4 guarded geometry (experimental)

**Scope:** three historical B4 failure modes only; fail closed when any required ray or line is undefined. `None` means **NON CALCULABLE** and must never be changed into 0 or an AVAILABLE measurement. No clinical runtime wiring or PDF authority.

**B4 failures reported in canonical Notion (2026-11-01):** 3-point angle with zero-length ray returned -0 degrees; 4-point angle with zero-length line returned a numeric value; point-to-line distance with degenerate line divided by zero. Those failures happened in `audit/facad_bergen_short_runtime_recalc.py` from a previous FACAD archive; that script is **not present on current GitHub master**, so this isolated module **does not fix or replace the original runtime candidate**.

**Implemented primitives:** unsigned mathematical 3-point and 4-point angles, and unsigned pixel distance from point to an infinite line. Reject missing, malformed, nonfinite, zero and near-zero directions. The use of a fixed numeric epsilon here is an experimental computational policy, not an FACAD claim. The distances are **pixels**, not calibrated mm. **No FACAD-specific orientation, sign, supplementary/obtuse branch or rounding is implied.**

**FUE-0:** `python -m pytest backend/tests/test_facad_bergen_geometry_guard.py -q`. Safety vectors include zero ray/line, invalid point, nan/inf/bool, true 0-degree angle, straight/right angles, translation/rotation/mirror/scaling, near-degenerate geometry. Local isolated execution on 2026-11-01: **17 passed in 0.10s**; GitHub exact-HEAD CI pending.

## Clinical hold — cannot be lifted by these tests

- Historical Bergen Short 12/12 tenth-of-a-unit match came from one **reconstructed synthetic XML**, not the original FACAD FCD and not new independent live FACAD runs. A multi-case same-trace parity matrix with source artifacts is absent.
- Four landmark aliases `Is`, `Isa`, `Ii`, `Iia` are individually **unconfirmed**; no automatic mapping to Crown's 38 points is authorized. Three Bergen Short measurements depend on this unresolved identity mapping.
- Facad Mini (9 nodes) has no independent runtime oracle; no result from Bergen is transferable to Facad Mini.
- Clinical output, profile `requiredness`, PDF status `COMPLETE`, export and patient-facing workflows remain untouched. A practitioner must approve exact alias definitions, image orientation and branch/sign conventions after the vendor-side evidence is available.

**NEXT:** recover the exact reference FCD or run FACAD on same coordinates with captured 12 values and provenance; restore original candidate script, apply this guard *at its actual boundary*, rerun the 14 historical B4 cases and same-trace Bergen matrix. Until then: **SCIENCE HOLD / DO NOT MERGE TO CLINICAL RUNTIME.**
