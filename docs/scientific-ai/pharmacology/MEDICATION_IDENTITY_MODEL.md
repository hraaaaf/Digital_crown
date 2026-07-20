# Medication Identity Model

## Non-equivalences

`INN/DCI != brand != pharmaceutical form != strength != concentration != route != presentation != ATC code != DDD`.

`DDD MUST NEVER BE USED AS AN INDIVIDUAL PRESCRIPTION DOSE.` WHO defines DDD for drug-utilization comparison as an assumed average maintenance dose for a main indication, not a patient prescription.

## Conceptual entities

### Substance

- Stable internal ID.
- Preferred INN/DCI label and language-specific aliases.
- Component role for combinations.
- External identifiers with namespace and version.
- Source and review status.

### Brand

- Brand ID, exact marketed name, manufacturer/holder and country.
- Links to one or more presentations, never directly to an assumed dose.
- A brand alias alone is insufficient to select a formulation.

### Form

- Controlled pharmaceutical form, such as tablet, capsule, oral suspension, oral gel, mouth rinse or injection.
- Release behavior where relevant.
- Must not be inferred from free text when a rule depends on it.

### Strength

- Structured numerator amount/unit per denominator amount/unit or per dosage unit.
- Combination products store every component separately.
- Total tablet mass cannot replace component strengths.

### Route

- Controlled route independent of form.
- Oral, oromucosal, local injection and dental local use must remain distinct.

### Presentation

- Pack size, container, volume, device/cartridge volume and market-specific identifiers.
- A presentation has market authorization and commercialization snapshots.

### MarketAuthorization

- Jurisdiction, authority, authorization number/status, holder, source record, effective dates and snapshot.
- Commercialization and authorization are separate states.

### ClinicalRule

- Versioned indication/population/context-specific rule referencing substances and explicit formulation constraints.
- Never embedded only in a product, prompt, UI preset or PDF template.

## Required invariants

1. A prescription line references a substance plus an explicit formulation or records why the formulation is pending.
2. Fixed combinations enumerate components and component strengths.
3. Brand resolution may narrow candidates but cannot invent concentration, route or authorization status.
4. Alias matching produces candidates requiring deterministic disambiguation.
5. Market records and clinical rules have independent versions.
6. User habits may affect ordering/display only; they cannot alter safety constraints.
7. Rendered instructions preserve the selected rule ID/version and calculation trace.

## Example of prohibited collapse

`Augmentin = amoxicillin/clavulanate 1 g` is insufficient because it omits component strengths, form, route, presentation, jurisdiction and market status. The application must resolve a specific formulation before any calculation or instruction.

## Source anchors

- WHO INN programme: <https://www.who.int/teams/health-product-and-policy-standards/inn>
- WHO INN guidance: <https://www.who.int/publications/m/item/guidance-on-the-use-of-inns>
- WHO ATC/DDD methodology: <https://www.who.int/tools/atc-ddd-toolkit/methodology>

