# Pharmacology Versioning Policy

## Versioned objects

| Object | Version trigger | Non-trigger examples |
|---|---|---|
| medication identity | INN/component/identifier merge or split | spelling/display translation with identical identity |
| formulation | component strength, concentration, form, route or presentation identity | cosmetic pack image change |
| market snapshot | authorization/commercialization/price/source snapshot change | local UI sorting |
| prescribing rule | dose, maximum, population, indication, contraindication, interaction, allergy behavior, route, duration or missing-data behavior | prose clarification that cannot change execution |
| guideline/source | upstream edition/version/date or corrected publication | access timestamp alone |
| calculation engine | arithmetic, unit conversion, cap order or rounding behavior | internal refactor proven behavior-identical |

## Rules

1. Use immutable semantic versions for clinical rules. Any executable clinical change creates a new rule version.
2. Never mutate an approved rule in place. Retain prior versions for prescriptions already generated.
3. Record source versions separately from access dates.
4. Market availability is a dated snapshot and does not retroactively alter historical prescriptions.
5. Each prescription stores rule ID/version, identity/formulation IDs/versions, source IDs/versions, calculation trace, context snapshot and approval state.
6. A superseded rule is not deleted; activation windows and replacement links are explicit.
7. Re-approval is mandatory after any clinical version change.
8. Text-only edits require documented behavior-equivalence review but not necessarily a clinical version bump.

## Proposed lifecycle

`draft -> candidate -> needs_review -> approved-by-clinician -> active -> superseded/withdrawn`.

This mission creates only candidate assets. It assigns no clinical approval or active state.

