# Allergy Model

## Required distinctions

| Concept | Meaning in the model | Prescribing behavior |
|---|---|---|
| allergy | Immune-mediated or clinically recorded allergy candidate | May trigger a rule-specific block after substance/class resolution |
| intolerance | Non-allergic inability to tolerate a medicine | Kept separate; action depends on reviewed rule |
| side effect | Known or reported adverse effect without allergy classification | Must not automatically create an allergy label |
| unknown reaction | Medicine/reaction reported but details unavailable | Blocks rules that require allergy certainty; prompts clarification |
| family-level allergy | Recorded concern for a defined chemical/drug family | Requires explicit hierarchy and cross-reactivity policy |
| substance allergy | Reaction linked to a stable substance ID | Never inferred only from a brand substring |

## Minimum structured record

- `record_id`, status and provenance.
- Substance or class identifier plus original free text.
- Reaction description and controlled reaction candidates.
- Severity, timing, date and exposure route when known.
- Certainty and verification state.
- Reporter and review history.
- Distinction between allergy and non-allergic adverse reaction.

## Safety behavior

1. `unknown` is not `no known allergy`.
2. Free-text brand matching may raise a candidate but cannot confirm the active substance.
3. A beta-lactam/penicillin label must not trigger an arbitrary alternative drug.
4. Alternative selection requires an approved indication-, population- and jurisdiction-specific rule.
5. Allergy information is reviewed before medication selection and again after exact formulation resolution.
6. The prescriber must see the reason, uncertainty and source of any block.

## Source anchors

- NICE CG183 structured drug-allergy documentation: <https://www.nice.org.uk/guidance/CG183/chapter/recommendations>
- CDC penicillin-allergy clinical features/resources: <https://www.cdc.gov/antibiotic-use/hcp/clinical-signs/index.html>
- SDCEP dental prescribing guidance: <https://www.sdcep.org.uk/published-guidance/drug-prescribing/>

All cross-reactivity and dental alternative rules remain candidate and need clinical review.

