# Morocco Medication Source Strategy

Review date: 2026-07-18

## Conclusion

### Primary source candidate

The Agence marocaine du medicament et des produits de sante (AMMPS) is the primary authority candidate for Moroccan authorization and market-status facts.

- Public medication list: <https://www.ammps.gov.ma/basesdedonnes/liste_marocaine_des_medicaments>
- Generic-medicine pilot repertoire: <https://ammps.gov.ma/repertoire-medicaments-generiques>
- Safety alerts and recalls: <https://www.ammps.gov.ma/alertes-et-rappels/rappel-de-lots-de-specialites-pharmaceutiques-et-dun-produit-de-sante>
- Legal mandate: Law 10-22, <https://www.sgg.gov.ma/BO/FR/2873/2025/BO_7462_Fr.pdf>

The public list advertises product, active substance, dose/strength text, pharmaceutical form, presentation, authorization status, commercialization status, therapeutic class, hospital classification, prices and, for some entries, regulatory documents. The January 2026 generic pilot advertises 312 active substances and is explicitly evolving.

### Secondary source candidates

- Ministry of Health medication portal: <https://www.sante.gov.ma/Medicaments/Pages/default.aspx>
- Ministry DMP role page: <https://www.sante.gov.ma/Pages/ADM_Centrale/DMP.aspx>
- Ministry reimbursement/price guide: <https://www.sante.gov.ma/Documents/Activite/guide%20mdcts%20remboursables.pdf>
- Product information from EMA, ANSM or the French public medicine database may support identity/formulation review, but never proves Moroccan authorization or current commercialization.

## Capability assessment

| Question | Finding | Status |
|---|---|---|
| Official authority? | AMMPS is the national authority under Law 10-22 | candidate, high institutional relevance |
| Current? | AMMPS pages and 2026 pilot are current enough to be candidates; individual records need snapshot dates | needs_review |
| Publicly accessible? | Human-readable public pages were accessible during review | candidate |
| Structured? | Search/filter fields are exposed; underlying public data contract not verified | needs_review |
| Downloadable/exportable? | No official bulk export was confirmed | unavailable/not_verified |
| Public API? | No documented official API was confirmed | unavailable/not_verified |
| Contains DCI? | Active-substance fields are advertised | candidate; normalization quality not audited |
| Contains brand? | Product/specialty names are advertised | candidate |
| Contains strength/form/presentation? | These fields are advertised | candidate |
| Contains AMM/commercialization status? | Both are advertised | candidate |
| Contains price? | Price fields are advertised | candidate; date and legal use must be tracked |
| Reuse license? | No machine-readable reuse license was confirmed | license_uncertain |

## Unavailable data

- Stable API identifiers and change feed.
- Bulk historical authorization/commercialization timeline.
- Guaranteed normalized INN identifiers.
- Complete RCP availability for every product.
- Explicit reuse, redistribution and derivative-database license.
- A documented SLA or schema version.

## License concerns

Public visibility is not permission to scrape, republish, or create a derivative commercial database. Before integration, Digital Crown must obtain or verify terms for automated access, caching, redistribution, refresh frequency, attribution, and retention of withdrawn products.

## Structured data feasibility

Feasible as a controlled ingestion only after AMMPS confirms a supported export/API or grants written permission. Every snapshot must preserve source URL, retrieval time, record identifier, raw value, normalized value, authorization status, commercialization status, and parser version.

## Manual curation required?

Yes for V1. Start with only the substances already present in Digital Crown. A curator should link each candidate product to an AMMPS record, preserve the original record, and require a pharmacist/clinician review before any product participates in a prescribing rule.

## Recommended integration sequence

1. Request official AMMPS access and reuse terms.
2. Define stable internal substance/product/formulation IDs independent of page labels.
3. Curate the current Digital Crown inventory manually with two-person review.
4. Add snapshot/version metadata and withdrawal handling.
5. Automate import only through a supported source and never infer missing fields.

