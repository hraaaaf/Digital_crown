# Cephalometry review

## Verdict

V2 is architecturally suitable for deterministic cephalometry, but no current Digital Crown measurement or norm profile is approved by this review. Existing formulas and hard-coded norms remain documented P1 risks and were not modified.

Required pipeline: landmarks -> orientation/calibration -> deterministic full-precision geometry -> validation -> selected versioned norm profile -> interpretation -> report.

No LLM calculates landmark-derived values. Rounding is display-only. Moving a landmark invalidates and recalculates every transitive dependent measurement.

| Analysis | Status | Reason |
|---|---|---|
| Steiner | NEEDS_SOURCE_VERIFICATION | Original identified; formula-by-formula extraction pending |
| Downs | DO_NOT_IMPLEMENT_YET | Original identified; no approved contract |
| Tweed | NEEDS_SOURCE_VERIFICATION | Exact directed formulas/profile require review |
| Ricketts | DO_NOT_IMPLEMENT_YET | Original source set not verified |
| McNamara | DO_NOT_IMPLEMENT_YET | Complete analysis contract not verified |
| Wits/Jacobson | NEEDS_SOURCE_VERIFICATION | Original found; plane, sign and population need review |
| Holdaway | DO_NOT_IMPLEMENT_YET | Original identified; complete contract not verified |
| Jarabak/Bjork | DO_NOT_IMPLEMENT_YET | Original method lineage unresolved |
| Sassouni | DO_NOT_IMPLEMENT_YET | Original identity found; geometry not verified |

REPO_MAP identifies SNA, SNB, ANB, IMPA, incisor/Frankfort, inter-incisal, nasolabial, FMA and other metrics in cephalo_engine.py and ai_advisor.py. Each needs its own canonical landmarks, directed formula, unit, sign, calibration, source, population, precision, limitations and independent tests.

A 2012 study reports candidate Steiner norms from 71 selected young adults in Casablanca; another reports vertical measures from 98 students. These selected, limited samples do not justify a universal Moroccan default.

Required tests include translation/resolution invariance, calibrated scale, orientation/sign, transitive recalculation, missing/coincident points, precision/rounding separation, wrong-profile refusal and PDF parity.

