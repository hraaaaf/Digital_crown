# Digital Crown — Pharmacologie Maroc M1 handover

Date: 2026-09-16
Status: ACTIVE — M1-B2 merged; RCP acquisition fail-closed; no clinical activation

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

## M1-B2 — preuve finale
HEAD pré-merge: `4b4cfd968951c97af39d3e757afde5185ffeb196`.
Base: `fb3a870e2fba92a005a3e3de57ee378042b23be3`.
Merge: `601cee32bab3169143cf61ca917e35d7bd1d6ee5`.

Certifications exact-head:
- Pharmacology Deterministic Scientific Safety Gate #11 / `35109483397`: `SUCCESS`;
- tests ciblés: `33 passed in 0.31s`;
- oracle: `PASS`;
- CI #4618 / `35109483296`: `SUCCESS`;
- T2 #3480 / `35109483225`: `SUCCESS`;
- PR Merge Summary #82 / `35109483555`: `SUCCESS`.

Reviewer #7 / `35109624600`:
- `approve_with_reservations`;
- blocking findings: 0;
- major findings: 0;
- missing tests: 0;
- `clinical_activation_authorized=false`.

Post-merge:
- CI #4619 / `35110253634`: `SUCCESS`;
- Cabinet Upgrade PostgreSQL #921 / `35110253569`: `SUCCESS`.

## Wave 1 documentaire
Queue connue:
- `READY_FOR_CAPTURE_TRANSPORT`: paracetamol, ibuprofen, amoxicillin, penicillin_v, clarithromycin.
- `PENDING_RCP_LINK_CONFIRMATION`: metronidazole.
- `PENDING_CURRENT_PRESENTATION_DISCOVERY`: clindamycin.
- aucune donnée clinique extraite.

## Acquisition RCP read-only — résultats vérifiés
Branche de recherche: `research/pharmacology-rcp-first-capture-20260916`.
Aucune mutation manifest et aucune activation clinique dans les probes.

### Amoxicilline
Probe inventaire #2 / run `35110885162`: `SUCCESS`.
Artifact `10451738662`, digest `sha256:e4a88000c3293e090f12e2904fadd05a0cb61e666e99b05d64ec1e24d3b2189a`.

Résultat:
- les 6 présentations amoxicilline liées au manifest sur la page 42 ont un contrôle `Télécharger RCP` rendu mais désactivé (`aria-disabled=true`, classe `disabled-rcp-btn`);
- aucun PDF capturé;
- ne pas conclure `UNAVAILABLE_VERIFIED` à partir de ce seul état UI.

### Ibuprofène
Probe #3 / run `35115618383`: `SUCCESS` sur HEAD recherche `ddda7361e40c0e558fd215fd548a3c386c687c45`.
Artifact `10454722384`, digest `sha256:3d781cf7cd37369df668fcefc8688628ec0967065b924591fa8a2558b22a2ef5`.

Résultat exact du rapport: `NO_ENABLED_IBUPROFEN_RCP_CONTROL`.
- `enabledCount=0`;
- les contrôles ibuprofène inventoriés sont désactivés (`aria-disabled=true`, `disabled-rcp-btn`);
- les présentations orales ALGANTIL 200 mg B10 effervescent, B20 effervescent et B20 dragée sont notamment observées `Commercialisé` mais leur contrôle RCP est désactivé;
- aucun PDF, URL finale ou SHA-256 PDF n'a été capturé;
- aucune promotion réglementaire autorisée.

### Paracétamol
Après deux molécules sans contrôle activé, changement de stratégie conformément à la règle anti-répétition: probe ciblé page 47 lancé via commit recherche `0c66d0e59c1d473b0431d5e19a4315e65e79abae`.
Le probe ne clique que sur un contrôle explicitement activé et n'accepte comme preuve qu'une réponse HTTPS AMMPS 2xx dont les bytes commencent par `%PDF-`, avec URL réelle + SHA-256.
Statut du run à renseigner après résultat; ne pas inventer.

## État repo
Master vérifié pendant l'acquisition: `10c9b084ed0582dc24147808e911defcc2806b50`.
Le master a avancé après M1-B2; aucun nouveau travail produit M1 n'est fusionné depuis la branche de recherche.

## Next exact
1. Lire le résultat + artifact du probe paracétamol lancé sur `0c66d0e...`.
2. Si un unique PDF officiel est capturé: vérifier URL HTTPS AMMPS, status 2xx, `%PDF-`, bytes, SHA-256, identité de présentation, puis revue indépendante avant toute promotion `SNAPSHOT_VERIFIED`.
3. Si aucun contrôle paracétamol n'est activé: enregistrer la preuve fail-closed et passer au prochain candidat Wave 1 (`penicillin_v`, puis `clarithromycin`) sans forcer de bouton désactivé.
4. Ne modifier le manifest qu'après preuve complète + revue indépendante.

## Interdits
- Pas d'activation clinique M1.
- Pas de `SNAPSHOT_VERIFIED` sans artefact réel vérifié.
- Pas de `UNAVAILABLE_VERIFIED` sur simple absence/recherche négative/bouton désactivé.
- Pas de faux verdict reviewer.
- Pas d'assimilation CI verte = validation scientifique.
- Pas d'URL RCP déduite/fabriquée à partir de `javascript:void(0)`.

## Prompt de reprise
`Lis ce fichier depuis docs/pharmacology-m1-handover-20260915, vérifie master et le dernier probe RCP. M1-B2 est mergé et post-merge vert. Amoxicilline et ibuprofène ont été vérifiés fail-closed sans contrôle RCP activé. Reprendre au probe paracétamol, puis poursuivre Wave 1 jusqu'à capturer un vrai PDF AMMPS ou épuiser proprement les candidats, sans promotion SNAPSHOT_VERIFIED avant preuve complète et revue indépendante.`
