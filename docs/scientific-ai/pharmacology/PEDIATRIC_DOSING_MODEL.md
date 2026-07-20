# Pediatric Dosing Model

## Safety position

No pediatric dose is ready for activation. Every value remains a candidate until the exact source, population, indication, formulation, route, rule version and human clinical approval are recorded.

Never use an age-derived estimated weight for prescribing. Use a measured weight with unit, timestamp and provenance. Missing required weight must block a weight-based rule.

## Deterministic pipeline

```text
verified weight
  x approved mg/kg basis
  -> raw dose per administration or per day
  -> frequency allocation when explicitly defined
  -> per-dose cap
  -> daily cap
  -> explicit formulation concentration conversion
  -> representable volume/tablet quantity
  -> rule-defined rounding
  -> final invariant checks
  -> prescriber confirmation
```

An LLM must never calculate, cap, convert, round or validate a dose.

## Required rule fields

- Age interval and boundary semantics.
- Measured weight, unit and observation date.
- Dose basis: per administration or per day.
- mg/kg value and unit dimensions.
- Frequency and allocation rule.
- Maximum per administration and maximum per day.
- Minimum age/weight when applicable.
- Exact formulation component strength or concentration.
- Route and dosage form.
- Volume/tablet representability constraints.
- Rounding increment and direction.
- Renal/hepatic/pregnancy applicability where relevant.
- Indication, duration and stewardship constraints.
- Source IDs, conflicts, approval and test IDs.

## Calculation constraints

1. Store rational/decimal values in canonical units; never parse localized prose for calculation.
2. Preserve raw, capped, converted and rounded values separately.
3. For liquids, use `dose_mg / concentration_mg_per_mL`; denominator and component must be explicit.
4. For combinations, calculate each active component independently.
5. Reject zero/negative/implausible weight, stale weight per policy, missing concentration and incompatible units.
6. Do not divide a daily value by frequency unless the source explicitly defines that relationship.
7. A display rounding change must not silently change the administered amount.

## Required tests

- Exact lower/upper age and weight boundaries.
- Missing, stale, zero, negative and unit-mismatched weight.
- Per-dose cap before and after daily cap.
- mg/mL and mg/5 mL conversions.
- Combination component conversion.
- Non-representable tablet fraction or liquid increment.
- Frequency changes and duplicate ingredient totals.
- Property tests for monotonic raw dose below caps and capped invariance above caps.

## Candidate sources

- AAPD Useful Medications for Oral Conditions, 2025: <https://www.aapd.org/research/oral-health-policies--recommendations/useful-medications-for-oral-conditions/>
- AAPD Antibiotic Therapy, latest 2026 revision page: <https://www.aapd.org/research/oral-health-policies--recommendations/use-of-antibiotic-therapy-for-pediatric-dental-patients/>
- AAPD pain management guidance: <https://www.aapd.org/globalassets/media/policies_guidelines/bp_pain.pdf>

These sources are candidates and do not establish Moroccan product availability or clinical approval.

