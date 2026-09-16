# Digital Crown — Pharmacologie Maroc M1 handover

Date: 2026-09-16
Status: ACTIVE — M1-B2 merged; RCP acquisition next; no clinical activation

## Goal
Construire la couverture pharmacologique dentaire Maroc avec preuve réglementaire fail-closed, puis validation scientifique indépendante avant toute activation clinique.

## Invariants
- Digital Crown reste local/on-premise.
- Aucun déploiement de l'application clinique ni de ses données sur Vercel.
- Préserver DB, patients, documents et fonctionnalités validées.
- CI verte != validation scientifique/clinique.
- Reviewer scientifique indépendant, read-only.
- Recherche négative != preuve d'absence.
- Aucun `AUTO_OK` ni activation clinique par M1.
- Aucun `SNAPSHOT_VERIFIED` sans vrai PDF AMMPS + URL officielle exacte + bytes locaux + SHA-256 concordant.

## Lots fermés
- M1-A PR #517 → `d474ad18ba47d55a0d53f1f90e47a451f4dbac5e`.
- M1-B0 PR #518 → `81bf142021cdf4770e9c6ca92078306ac4898783`.
- M1-B1 PR #519 → `21651f22df9ba5210078969aa46abc527ba9e2bd`.
- Wave 1 evidence refresh PR #522 → `12f2550aaa38f3045095152ab862b587db109238`.
- Gate déterministe initiale PR #526 → `a396acfd6570ff24ca683009e1f31bdb3f2c0d92`.
- Réparation gate PR #537 → merge `fb3a870e2fba92a005a3e3de57ee378042b23be3`.
- M1-B2 PR #525 → merge `601cee32bab3169143cf61ca917e35d7bd1d6ee5`.

## M1-B2 — preuve finale pré-merge
HEAD exact: `4b4cfd968951c97af39d3e757afde5185ffeb196`.
Base exacte: `fb3a870e2fba92a005a3e3de57ee378042b23be3`.
Diff final: exactement 3 fichiers M1-B2.

Certifications exact-head:
- Pharmacology Deterministic Scientific Safety Gate #11 / `35109483397`: `SUCCESS`;
- tests ciblés: `33 passed in 0.31s`;
- oracle déterministe: `PASS`;
- gate artifact `10451164482`, digest `sha256:1aeeaae2f8d6b8252bd90938db5701c0ab1c0f5e65cdc9b77cbc3f259949ac80`;
- CI #4618 / `35109483296`: `SUCCESS`;
- T2 Runtime Browser #3480 / `35109483225`: `SUCCESS`;
- PR Merge Summary #82 / `35109483555`: `SUCCESS`;
- M6-I #2280: `SKIPPED` attendu.

## Reviewer scientifique indépendant final
Reviewer #7 / run `35109624600`.
Target HEAD: `4b4cfd968951c97af39d3e757afde5185ffeb196`.
Expected base: `fb3a870e2fba92a005a3e3de57ee378042b23be3`.

Artifact:
- ID `10451698081`;
- digest `sha256:4fb424dbd0e97790dd7f588ea1010aeb694050a32e2a6276982d3342563c86c4`.

Verdict:
- `approve_with_reservations`;
- blocking findings: 0;
- major findings: 0;
- missing tests: 0;
- `clinical_activation_authorized=false`.

Le reviewer a indépendamment reproduit/challengé la correction du finding précédent `RCP-PATH-SYMLINK-ESCAPE`; les évasions par symlink fichier et par redirection du dossier canonique RCP sont rejetées.

Réserves restantes, hors scope M1-B2:
1. capturer le vrai RCP officiel avant toute promotion `SNAPSHOT_VERIFIED`;
2. conserver l'URL officielle exacte, les bytes PDF locaux et le SHA-256;
3. aucune activation clinique / `AUTO_OK_MAROC` sans validation clinique humaine ultérieure.

## Merge M1-B2
PR #525 mergée le 2026-09-16.
Merge SHA: `601cee32bab3169143cf61ca917e35d7bd1d6ee5`.
Master vérifié sur ce SHA immédiatement après merge; commit GitHub signé/verified.

Post-merge au premier contrôle:
- CI #4619 / run `35110253634`: `IN_PROGRESS`;
- Cabinet Upgrade PostgreSQL #921 / run `35110253569`: `IN_PROGRESS`.

Ne pas transformer cet état en certification post-merge avant conclusion réelle des runs.

## Wave 1 documentaire
- `READY_FOR_CAPTURE_TRANSPORT`: paracetamol, ibuprofen, amoxicillin, penicillin_v, clarithromycin.
- `PENDING_RCP_LINK_CONFIRMATION`: metronidazole.
- `PENDING_CURRENT_PRESENTATION_DISCOVERY`: clindamycin.
- aucune donnée clinique extraite.

## Première cible RCP réelle
- `AMOXICILLINE SP 1 G COMPRIME DISPERSIBLE BOITE DE 12`.
- regulatory id interne: `ammps-reg:6fd268f476e7efe0c11f0c4b`.
- EPI: `AMANYS PHARMA`.
- page AMMPS: `https://www.ammps.gov.ma/recherche-medicaments?page=42`.
- statut observé: `Commercialisé`.
- contrôle `Télécharger RCP` observé.
- le bouton rendu expose `javascript:void(0)` et non l'URL PDF finale.
- l'URL PDF exacte reste donc à capturer par interaction navigateur + interception de requête/download; ne jamais l'inventer.

## Next exact
1. Préparer un lot d'acquisition RCP read-only depuis master `601cee32...`.
2. Avec navigateur automatisé, identifier la carte exacte AMOXICILLINE SP / 1 G / B12 / AMANYS PHARMA.
3. Attacher des listeners `download`, `request`, `response`, puis déclencher `Télécharger RCP`.
4. Accepter uniquement une ressource réellement observée provenant du domaine officiel AMMPS; conserver URL finale, status/content-type et bytes si PDF.
5. Vérifier signature PDF et calculer SHA-256, sans encore modifier le manifest ni promouvoir `SNAPSHOT_VERIFIED`.
6. Faire revoir indépendamment cette preuve de capture avant toute promotion réglementaire.
7. Recontrôler les runs post-merge #4619 et #921 seulement quand nécessaire.

## Interdits
- Pas d'activation clinique M1.
- Pas de `SNAPSHOT_VERIFIED` sans artefact réel vérifié.
- Pas de faux verdict reviewer.
- Pas d'assimilation CI verte = validation scientifique.
- Pas d'URL RCP déduite/fabriquée à partir du bouton `javascript:void(0)`.

## Prompt de reprise
`Lis ce fichier depuis docs/pharmacology-m1-handover-20260915, vérifie master et les runs post-merge, puis reprends au Next exact. M1-B2 est mergé; le prochain objectif est la capture read-only du vrai RCP AMMPS AMOXICILLINE SP 1 G B12, sans promotion SNAPSHOT_VERIFIED avant preuve complète et revue indépendante.`
