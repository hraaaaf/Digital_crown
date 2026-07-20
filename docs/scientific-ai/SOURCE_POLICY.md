# Scientific source policy V2

## Evidence priority

Priority A: official health authority, WHO, official standard, current product information, or professional-society guideline.

Priority B: systematic review, meta-analysis, consensus, or original method publication.

Priority C: academic textbook, institutional course, manufacturer or software documentation. Priority C cannot independently activate a clinical rule.

Blogs, forums, social networks, search snippets, AI answers, competitors, and unsourced PDFs must never be the sole basis for a scientific claim.

## Registration

Every record must preserve stable ID, exact title/organization, version/date, access date, jurisdiction, structured population, URL/identifier, license, supported claims, limitations, contradictions, implementation targets, and status. Search snippets are discovery aids only; the source itself must be opened before implementation.

## Status lifecycle

Allowed statuses are candidate, needs_review, approved-by-clinician, rejected, superseded, license-blocked, insufficient-evidence, conflicting-sources, and license_uncertain.

Only a named human clinical reviewer may assign approved-by-clinician, with review date and approval evidence. An AI reviewer may verify structure and recommend a status but cannot approve clinical validity.

Contradictory sources remain conflicting-sources until a documented human decision identifies scope, population, jurisdiction, and rationale. License uncertainty blocks copying source content and blocks dataset/product-data ingestion.

## Activation gate

A source record alone never activates a rule. Every active rule claim must reference applicable approved sources, explicit units and population, versioned deterministic logic, missing-data behavior, independent tests, scientific review, and human clinical approval. Formula sources and normative-profile sources are separate approvals.

## Domain cautions

- INN identifies substances; it does not prove Moroccan authorization, presentation, concentration, availability, or dose.
- ATC/DDD supports utilization statistics; DDD is not an individual prescribing dose.
- A brand never implies strength or concentration.
- A cephalometric formula and a population norm are distinct artifacts.
- A terminology standard does not validate diagnostic logic.
- A model non-detection does not establish absence of pathology.

