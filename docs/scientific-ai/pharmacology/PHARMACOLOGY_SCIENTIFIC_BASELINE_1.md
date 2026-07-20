# Pharmacology Scientific Baseline 1

Mission: `PHARMACOLOGY-SCIENTIFIC-BASELINE-1`
Date: 2026-07-18

## A. Verdict

| Dimension | Score |
|---|---:|
| Baseline readiness | 8/10 |
| Morocco source quality | 5/10 |
| Medication identity model | 9/10 |
| Dosage architecture | 8/10 |
| Pediatric model | 9/10 |
| Interaction strategy | 6/10 |
| Readiness for implementation | 3/10 |

The baseline artifacts are structurally ready for future engineering, but the current prescription feature has unresolved P0 safety architecture blockers. No clinical rule is approved or activated.

## B. Current Digital Crown situation

- The local Morocco-named catalog has 4,234 records, 2,839 unique display names, 1,134 DCI strings and 182 form strings. Its provenance, snapshot date and reuse license are not established.
- The focused inventory contains 22 medication/substance groups found in active rules, presets, seeds or examples.
- Dose, indication, contraindication, interaction and substitution logic is duplicated across backend, frontend, seeds, learned habits, prompts and tests.
- Missing weight is replaced by 70 kg in backend paths, while the frontend can estimate pediatric weight from age.
- Allergy and pediatric preset handling can silently change medicines.
- PDF generation occurs before warning-only coherence review.
- An LLM is asked to assess dosage and contraindications and may fail without a blocking result.
- Current prescription contracts do not represent all conditionally required patient data or rule/source provenance.

## C. Source strategy

| Category | Preferred source | Fallback | Gap |
|---|---|---|---|
| Medication identity | WHO INN plus AMMPS | EMA/ANSM/French official product record | Stable IDs and Moroccan normalization unverified |
| Morocco authorization/market | AMMPS medicine list and generic pilot | Ministry portal | API/export/license/history unconfirmed |
| Dental indications | Current SDCEP/ADA/AAPD guidance | Other authoritative specialty guideline | Moroccan adoption and conflict reconciliation |
| Product safety/formulation | Exact Moroccan RCP | EMA/ANSM RCP as research candidate | Many Moroccan RCP links/rights unverified |
| Pediatric rules | AAPD plus exact product information | Licensed pediatric formulary | No approved local rule or concentration set |
| Interactions | Licensed versioned knowledge base plus RCP | Approved bounded dental subset | No source selected/licensed |
| Prophylaxis | Current AHA and ESC | Moroccan/national cardiology guidance | Adoption and reconciliation needed |
| Allergy records | Structured allergy guideline | Reviewed national policy | Alternative and cross-reactivity rules unapproved |

## D. Morocco

### Official sources found

AMMPS public medicine list, AMMPS generic pilot, AMMPS alerts/recalls, Law 10-22 and Ministry medication/DMP pages.

### Data available

The AMMPS public list advertises product, substance, strength/dose text, form, presentation, authorization status, commercialization status, therapeutic class and price-like fields. The generic pilot advertises 312 substances and an evolving resource.

### Data unavailable or unverified

Supported API/bulk export, stable machine identifiers, historical status feed, full RCP coverage, change SLA and exact normalization semantics.

### License constraints

No explicit reuse and automated-access license was confirmed. Public visibility is insufficient for bulk scraping or commercial redistribution.

### Recommended integration strategy

Request official access/terms, manually curate only the current Digital Crown inventory, preserve raw snapshots and provenance, add two-person review, then automate only through a supported and licensed feed.

## E. Scientific blockers

1. No dose, maximum, duration, indication, alternative or formulation has human clinical approval.
2. Backend default weight and frontend estimated pediatric weight can drive active calculations.
3. Silent medication substitution exists in preset processing.
4. Active frontend/backend rule engines are unsourced and divergent.
5. Product identity is ambiguous; `HEXTRIL` and `AUGMENTIN` demonstrate unsafe collapse.
6. Current clindamycin prophylaxis conflicts with current AHA/ADA guidance.
7. The PDF can be created before non-blocking safety review.
8. LLM output participates in dose/contraindication assessment.
9. Prescription context and provenance contracts are incomplete.
10. No licensed comprehensive interaction source is selected.
11. AMMPS automation and reuse rights are unconfirmed.
12. Moroccan adoption of international dental/cardiology guidance is unresolved.

## F. Priorities

| Priority | Action | Exit criterion |
|---|---|---|
| P0 | Remove invented/estimated clinical inputs from calculation paths | Missing required data deterministically blocks |
| P0 | Stop silent substitutions and unsourced auto-dosing | Only approved versioned rules can propose a candidate |
| P0 | Move deterministic validation before persistence/PDF | Unsafe or incomplete lines cannot generate final output |
| P0 | Remove LLM authority over dose/contraindication decisions | LLM is optional explanation only |
| P0 | Introduce stable substance/formulation identity | Every executable rule resolves explicit components, strength, form and route |
| P1 | Obtain AMMPS terms and curate local products | Provenance and market snapshot available for every supported product |
| P1 | Approve a medication-rule set with Moroccan reviewers | Each rule has source, version, population, formulation and approval evidence |
| P1 | Select interaction data strategy | Licensed source or explicitly bounded approved subset |
| P1 | Reconcile prophylaxis and antibiotic guidance | Current conflicts resolved by recorded clinical review |
| P1 | Replace implementation-derived tests | Approved synthetic golden cases become independent oracles |
| P2 | Add controlled vocabularies and provenance snapshots | Routes/forms/units/reactions are machine validated |
| P3 | Consolidate aliases, seeds and presets | No duplicate authority remains |

## G. Recommended future implementation sequence

`PRESCRIPTION-SAFETY-GATES-1`
-> `PHARMACOLOGY-DATA-MODEL-1`
-> `MOROCCO-MEDICATION-CURATION-1`
-> `PHARMACOLOGY-RULE-APPROVAL-1`
-> `PHARMACOLOGY-RULE-ENGINE-1`
-> `DRUG-INTERACTION-INTEGRATION-1`
-> `PEDIATRIC-DOSING-1`
-> `PRESCRIPTION-UI-INTEGRATION-1`
-> `PRESCRIPTION-PDF-VALIDATION-1`

The safety-gates mission comes first because active P0 behavior must not remain while new data models are introduced.

## H. Tests

| Command | Result |
|---|---|
| `python scripts/validate_scientific_ai_assets.py` | PASS: `SCIENTIFIC_AGENT_SYSTEM_LOCKED_V1` |
| YAML parse for pharmacology assets, registry and schema | PASS: 7 files |
| `python -m pytest tests/scientific_ai/test_validate_scientific_ai_assets.py -q` | PASS: 5 tests |
| `git diff --check` | PASS; existing `STATE.md` line-ending warning only |
| `git diff --name-only -- backend frontend` | PASS: empty |

## I. Git

- Branch: `master`.
- Pre-existing user change preserved: `STATE.md`.
- Scientific infrastructure remains untracked as a whole in the current worktree, so `git diff --stat` only reports the tracked `STATE.md` change and does not enumerate these new files.
- No commit, push or deployment was performed.
- No backend, frontend, database, migration, patient data or production media was changed.

## J. Final status

`PHARMACOLOGY_SCIENTIFIC_BASELINE_BLOCKED`

The status is blocked because P0 findings remain in current runtime behavior and this baseline mission correctly did not alter clinical production code.
