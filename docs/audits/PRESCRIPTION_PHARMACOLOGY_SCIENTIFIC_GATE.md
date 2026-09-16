# Prescription Pharmacology — Deterministic Scientific Safety Gate

Status: PROPOSED — CI governance only, no clinical runtime change

## Goal

Ajouter une gate GitHub Actions dédiée aux changements pharmacologiques documentaires/réglementaires afin de rendre visibles et reproductibles les invariants objectivement vérifiables, sans présenter une CI verte comme une validation scientifique ou clinique.

## Success

Pour toute PR touchant les chemins pharmacologie/RCP couverts :

1. le workflow checkout le HEAD candidat exact ;
2. les tests documentaires M0 et M1-B0/B2 ciblés passent ;
3. un oracle indépendant du runtime applicatif vérifie le contrat `scientific-reviewer` et l'intégrité fail-closed du manifest RCP AMMPS ;
4. un rapport JSON et un résumé Markdown sont produits ;
5. le rapport déclare explicitement `clinical_activation_authorized=false` et `independent_scientific_review_required=true`.

## Proof attendue

Workflow : `.github/workflows/pharmacology-scientific-gate.yml`.

Oracle : `scripts/pharmacology_scientific_gate.py`.

Artefact CI : `pharmacology-deterministic-safety-<HEAD>` contenant `report.json` et `summary.md`.

La preuve n'est acquise qu'après un run GitHub Actions réussi sur le HEAD exact de la PR de ce lot.

## Invariants contrôlés automatiquement

- présence du reviewer `scientific-reviewer` et de ses deux skills ;
- contrat reviewer indépendant/read-only et mode `plan` conservés ;
- contrat de décision `approve | approve_with_reservations | request_changes | blocked` conservé ;
- recherche scientifique ne peut pas activer une règle ;
- manifest RCP JSON structuré avec IDs réglementaires uniques ;
- statuts limités à `PENDING_DOWNLOAD`, `SNAPSHOT_VERIFIED`, `UNAVAILABLE_VERIFIED` ;
- provenance `source_page_url` en HTTPS AMMPS officielle ;
- `PENDING_DOWNLOAD` sans hash/date/artefact/preuve d'absence ni extraction clinique ;
- `UNAVAILABLE_VERIFIED` uniquement avec preuve officielle explicite, sans artefact ni extraction clinique ;
- `SNAPSHOT_VERIFIED` uniquement avec URL AMMPS, date stricte, chemin PDF sûr, vrai fichier local, signature PDF et SHA-256 concordant.

## Ce que cette gate ne valide jamais

- indication clinique ;
- posologie ou durée ;
- population/contre-indications/interactions ;
- pertinence clinique d'une source ;
- arbitrage entre sources contradictoires ;
- approbation praticien ;
- décision `AUTO_OK_MAROC` ;
- revue scientifique indépendante elle-même.

Une CI verte signifie uniquement que les invariants déterministes couverts sont satisfaits.

## Non-régression

Ce lot ne modifie ni runtime clinique, ni DB, ni patients, ni documents, ni UI, ni Vercel. Il ajoute uniquement une gate CI, un oracle documentaire indépendant et ce canonique.

## Merge gate

- run exact-head de la nouvelle gate : SUCCESS ;
- CI générale applicable : SUCCESS ;
- diff final limité au scope gouvernance ;
- aucune régression démontrée ;
- accord utilisateur explicite requis avant merge.
