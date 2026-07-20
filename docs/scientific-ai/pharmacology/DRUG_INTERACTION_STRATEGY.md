# Drug Interaction Strategy

## Decision

Digital Crown must not build or maintain a complete interaction database manually. The safe target is a licensed, versioned interaction knowledge source plus a small, independently reviewed dental safety subset for high-priority blocking workflows.

## Options

| Option | Classification | Rationale |
|---|---|---|
| Licensed commercial interaction knowledge base with API/versioning | usable_with_license | Best route for broad coverage if terms allow clinical decision support, caching, audit and Moroccan deployment |
| Official product information (AMMPS RCP, EMA/ANSM SmPC/RCP) | usable | Authoritative product-specific interaction sections, but difficult to normalize and not a complete cross-product engine |
| Curated dental subset derived from approved guidelines/RCPs | usable | Appropriate for a narrow safety gate if every rule is sourced, versioned and reviewed; not a complete interaction checker |
| openFDA drug labels | insufficient | Structured US SPL labels are useful research inputs, but openFDA explicitly disclaims medical-decision reliance and is not Morocco-specific |
| RxNorm/RxNav DDI | not_recommended | RxNav discontinued its drug-drug interaction feature on 2024-01-02 |
| DrugBank | usable_with_license | Commercial licensing and safety-critical/derivative-use restrictions require written agreement and technical validation |
| LLM extraction or live web search at prescription time | not_recommended | Non-deterministic, incomplete, unversioned and unsuitable as a safety authority |

## Required integration contract

- Stable substance and formulation identifiers.
- Source dataset version and retrieval timestamp.
- Direction/severity/evidence fields with controlled vocabularies.
- Patient-context prerequisites and explicit unknown behavior.
- Human-readable rationale and source citation.
- Deterministic request/response caching and outage policy.
- No inference from brand name alone.
- Override requires identity, reason, user and timestamp; blocking interactions require policy-defined authorization.
- Regression tests from approved interaction cases.

## Manual maintenance risk

A handwritten matrix rapidly becomes incomplete because interactions depend on substance, dose, route, indication, patient context, evidence updates and combinations. False negatives are particularly dangerous because absence from a local list can be mistaken for absence of interaction. A manual subset must display its bounded scope and never claim comprehensive clearance.

## Source anchors

- RxNav FAQ: <https://lhncbc.nlm.nih.gov/RxNav/information/FAQs.html>
- openFDA drug label API: <https://open.fda.gov/apis/drug/label/>
- DrugBank licensing: <https://go.drugbank.com/business-development-licensing>
- DrugBank terms: <https://trust.drugbank.com/drugbank-trust-center/terms-of-use>

