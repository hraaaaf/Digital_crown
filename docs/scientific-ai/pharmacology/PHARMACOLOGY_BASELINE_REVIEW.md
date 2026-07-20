# Pharmacology Baseline Independent Review

```yaml
decision: blocked
blocking_findings:
  - "Active backend rules replace missing weight with 70 kg and calculate unsourced pediatric doses."
  - "Active frontend rules estimate pediatric weight from age and auto-populate dose text."
  - "Preset processing silently substitutes medicines for allergy or pediatric conditions."
  - "Prescription PDF generation precedes non-blocking coherence checks."
  - "An LLM is asked to assess dosing and contraindications and can fail silently."
  - "Medication identity/formulation errors and ambiguity can reach active flows."
  - "The current API cannot represent all conditionally required patient context."
major_findings:
  - "The local 4,234-record catalog has no embedded provenance, snapshot policy, or confirmed reuse license."
  - "No licensed comprehensive drug-interaction source has been selected."
  - "Moroccan market records lack a confirmed supported API/export and reuse agreement."
  - "Backend, frontend, seeds, habits, prompts, tests and PDF use duplicated free-text rules."
minor_findings:
  - "Controlled vocabularies for route, form, units and reaction types remain to be selected."
  - "Source abstracts and exact recommendation locations should be extracted during rule-specific missions."
scientific_uncertainties:
  - "No medication dose, maximum, duration, alternative pathway or Moroccan product is clinically approved."
  - "Moroccan adoption/reconciliation of SDCEP, ADA, AAPD, AHA and ESC guidance is unresolved."
  - "Renal, hepatic, pregnancy and breastfeeding rule sources are product-specific and incomplete."
license_concerns:
  - "AMMPS public data reuse and automated access terms are not confirmed."
  - "DrugBank requires commercial and safety-critical use review."
  - "Foreign product information reuse terms require verification before ingestion."
morocco_data_gaps:
  - "No supported bulk/API feed, stable identifier contract, change history or withdrawal feed was confirmed."
  - "The repository catalog cannot be asserted to reflect current authorization or commercialization."
required_actions:
  - "Run PRESCRIPTION-SAFETY-GATES-1 before any new clinical rule activation."
  - "Obtain AMMPS access/reuse terms and curate current products against official records."
  - "Implement stable identity/formulation data before dose rules."
  - "Select a licensed interaction strategy or approve a bounded dental subset."
  - "Have Moroccan clinician/pharmacist reviewers approve each source-backed rule and golden case."
```

## Review scope

The review covered source hierarchy, licensing, Moroccan applicability, medication identity, pediatric calculations, antibiotic/analgesic architecture, interactions, allergy records, the V2.1 rule schema, synthetic golden cases and the current feature risk audit.

## Independence statement

The reviewer did not approve any source, dose, product, alternative, interaction or contraindication. Passing asset tests would demonstrate structural consistency only, not scientific validation.

