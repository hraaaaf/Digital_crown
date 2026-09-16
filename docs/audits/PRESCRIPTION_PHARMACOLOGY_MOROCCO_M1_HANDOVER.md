# Digital Crown — Pharmacologie Maroc M1 handover

Date: 2026-09-16
Status: ACTIVE — M1-B2 merged; RCP acquisition fail-closed; global RCP census active; no clinical activation

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
Résultat: les présentations liées au manifest ont des contrôles RCP désactivés; aucun PDF capturé; aucune conclusion `UNAVAILABLE_VERIFIED` autorisée.

### Ibuprofène
Probe #3 / run `35115618383`: `SUCCESS` sur `ddda7361e40c0e558fd215fd548a3c386c687c45`.
Artifact `10454722384`, digest `sha256:3d781cf7cd37369df668fcefc8688628ec0967065b924591fa8a2558b22a2ef5`.
Résultat: `NO_ENABLED_IBUPROFEN_RCP_CONTROL`; aucun PDF/URL finale/SHA-256 PDF capturé.

### Paracétamol
Probe #4 / run `35116683651`: `SUCCESS` sur `0c66d0e59c1d473b0431d5e19a4315e65e79abae`.
Artifact `10455083590`, digest `sha256:46ceaa5835bfec127c6735a2cebbfb9fdec353f903b91aac57957caaeeac19a6`.
Résultat: `NO_ENABLED_PARACETAMOL_RCP_CONTROL`; aucune mutation manifest et aucune activation clinique.

### Pénicilline V
Probe #5 / run `35117194902`: `SUCCESS` sur `d35733b77513a8728240dd6607bd8ad3d5c01cc8`.
Artifact `10454339652`, digest `sha256:99e7fa7cde1146dc51fde61d0809790f7dd0646f26d21df59b52cc75027d0573`.
Résultat: `NO_ENABLED_PENICILLIN_V_RCP_CONTROL`; aucune mutation manifest et aucune activation clinique.

## Enchaînement automatique Wave 1 READY — vérifié
Workflow chainé introduit au commit recherche `9c57795ec6f51c5a7389ad90424d3134bde95033`.
Run chaîne #6: `35121834201` → `SUCCESS`.
Artifact `10457267023`, digest `sha256:71efe115c423fb3107a461d7e471d4fafa116393cadc0f9f9fc5682a304d07fe`.

Résultat exact:
- paracetamol: `NO_ENABLED_RCP_CONTROL`;
- ibuprofen: `NO_ENABLED_RCP_CONTROL`;
- amoxicillin: `NO_ENABLED_RCP_CONTROL`;
- penicillin_v: `NO_ENABLED_RCP_CONTROL`;
- clarithromycin: `NO_ENABLED_RCP_CONTROL`.

Interprétation autorisée:
- la voie UI référencée dans la queue Wave 1 READY n'a produit aucun contrôle RCP activé exploitable;
- cela ne prouve ni l'absence réglementaire du RCP ni l'indisponibilité officielle du médicament;
- aucun PDF officiel n'a été capturé;
- aucune mutation du manifest et aucune activation clinique n'ont eu lieu.

## Pending-family discovery — vérifié
Commit recherche: `ccf03cc376f1592be028700c46ab9a823b4f2f9a`.
Run #7: `35123369625` → `SUCCESS`.
Artifact `10458925243`, digest `sha256:a21f4b7384eae1116c89470ae6799671952cb2befd96f51c1af2e73aaf497fe9`.

### Metronidazole
Résultat exact: `PRESENTATION_WITH_DISABLED_RCP_CONTROL`.
- recherche AMMPS courante par `METRONIDAZOLE` réussie;
- 12 contrôles RCP scoppés, 0 activé;
- présentations orales commercialisées observées dont `FLAGYL 250 MG` comprimé pelliculé B20 et `FLAGYL 500 MG` comprimé pelliculé B20;
- RMMG AMMPS page 11 chargé avec présence de `METRONIDAZOLE`;
- aucun PDF officiel capturé.

Le statut reste `PENDING_RCP_LINK_CONFIRMATION`: bouton désactivé != absence réglementaire.

### Clindamycin
Résultat exact: `PRESENTATION_WITH_DISABLED_RCP_CONTROL`.
- recherche AMMPS courante par `CLINDAMYCINE` réussie;
- 2 contrôles RCP scoppés, 0 activé;
- `DALACINE T TOPIC 300 MG`, solution pour application locale, est marqué `NON COMMERCIALISE`;
- `DUAC 6,67% / 1,28%`, gel, est marqué `RETIRE DU MARCHE`;
- aucune présentation systémique/orale commercialisée utile au scope dentaire n'a été prouvée dans ce pass;
- aucun PDF officiel capturé.

Le statut reste donc prudemment `PENDING_CURRENT_PRESENTATION_DISCOVERY`.

## Pivot technique — census global RCP AMMPS
Après 7 familles avec le même pattern (`javascript:void(0)` + `disabled-rcp-btn` + `aria-disabled=true`), les probes ciblés sont arrêtés.

Census initial commit `0a9db11827ce44a29aa5fb41a97c87d4bb22885b`, run #8 `35126944871`: `FAILURE` avant le scan complet.
Cause exacte: garde-fou interne `pageCount <= 700` trop strict alors que la base courante déduit `826` pages pour `9908` médicaments. Aucune conclusion scientifique/réglementaire ne doit être tirée de ce run.

Réparation: commit `a2164cd38d01c0b565295388cd2887e19241f715` relève uniquement ce garde-fou à `1200` et le timeout à 30 min; logique de lecture et permissions inchangées.
Run #9: `35127141170`.
But: recenser les 826 pages de `recherche-medicaments`, compter les contrôles RCP activés/désactivés et capturer tout href/PDF réellement exposé, sans clic forcé et sans mutation.
État au dernier contrôle: `IN_PROGRESS`.

## État repo
Master vérifié le 2026-09-16: `35c4ee606e953f2f2a8a9d91ab540bf6c7ef476a`, commit GitHub signé/verified.
Le master a avancé après M1-B2; aucun nouveau travail produit M1 n'est fusionné depuis la branche de recherche.

## Next exact
1. Lire le résultat + artifact du census #9 `35127141170` une fois terminé.
2. Si au moins un contrôle RCP actif existe: inspecter son href/transport et capturer un exemple réel officiel avant toute généralisation.
3. Si 0 contrôle actif sur toute la base: considérer la voie UI actuelle AMMPS comme non exploitable pour le contrat PDF strict et chercher une source documentaire officielle AMMPS alternative; ne pas inventer d'URL.
4. Toute capture candidate doit encore satisfaire HTTPS AMMPS + 2xx + `%PDF-` + bytes + SHA-256 + identité de présentation + reviewer indépendant avant `SNAPSHOT_VERIFIED`.

## Interdits
- Pas d'activation clinique M1.
- Pas de `SNAPSHOT_VERIFIED` sans artefact réel vérifié.
- Pas de `UNAVAILABLE_VERIFIED` sur simple absence/recherche négative/bouton désactivé.
- Pas de faux verdict reviewer.
- Pas d'assimilation CI verte = validation scientifique.
- Pas d'URL RCP déduite/fabriquée à partir de `javascript:void(0)`.

## Prompt de reprise
`Lis ce fichier depuis docs/pharmacology-m1-handover-20260915, vérifie master et le census RCP #35127141170. M1-B2 est mergé et post-merge vert. Les 5 candidats READY ont tous été vérifiés sans contrôle RCP activé. Metronidazole est présent avec 12 contrôles RCP désactivés; clindamycin ne fournit dans le pass courant que deux présentations topiques non utilisables comme preuve d'une présentation systémique actuelle. Le census #8 a échoué uniquement sur un cap pageCount trop bas; #9 scanne les 826 pages. Ne promouvoir aucun SNAPSHOT_VERIFIED avant PDF officiel réel + revue indépendante.`
