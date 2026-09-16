# Digital Crown — Pharmacologie Maroc M1 handover

Date: 2026-09-16
Status: ACTIVE — M1-B2 merged; RCP acquisition fail-closed; pending-family discovery active; no clinical activation

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

Le RMMG AMMPS de janvier 2026 confirme des présentations orales de métronidazole dans le répertoire générique; cela ne constitue pas encore une preuve de RCP disponible.

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
Artifact: `10457267023`.
Digest artifact: `sha256:71efe115c423fb3107a461d7e471d4fafa116393cadc0f9f9fc5682a304d07fe`.

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

## Pivot — découverte pending + mécanisme RCP
Après l'échec homogène des 5 candidats READY, la stratégie est changée: ne plus répéter des probes identiques sur les boutons désactivés.

Workflow de découverte introduit au commit recherche `ccf03cc376f1592be028700c46ab9a823b4f2f9a`.
Il cible:
- `metronidazole`: découverte de présentation actuelle, recoupement RMMG AMMPS et inspection des contrôles/attributs/DOM/ressources réseau RCP;
- `clindamycin`: découverte via recherche AMMPS avec variantes `CLINDAMYCINE`, `CLINDAMYCIN`, `DALACINE`, sans conclure à l'absence en cas de résultat négatif.

Le workflow capture aussi les indices techniques du transport RCP: hrefs, attributs, HTML modal/card, formulaires de recherche, scripts, requêtes/réponses réseau intéressantes et toute réponse PDF détectée. Une réponse n'est considérée comme PDF officiel vérifié que si HTTPS AMMPS + 2xx + signature `%PDF-` + SHA-256 réel.

Au moment de cette mise à jour, aucun run associé au commit `ccf03cc...` n'était encore visible; ne pas inventer de résultat.

## État repo
Master vérifié le 2026-09-16: `35c4ee606e953f2f2a8a9d91ab540bf6c7ef476a`, commit GitHub signé/verified.
Le master a avancé après M1-B2; aucun nouveau travail produit M1 n'est fusionné depuis la branche de recherche.

## Next exact
1. Lire une fois le run déclenché par `ccf03cc376f1592be028700c46ab9a823b4f2f9a` dès qu'il est visible/terminé.
2. Inspecter `metronidazole` et `clindamycin`: présentations trouvées, états RCP, indices DOM/réseau et éventuels PDF réels.
3. Si un PDF officiel est capturé: vérifier identité exacte de présentation + URL HTTPS AMMPS + status 2xx + `%PDF-` + bytes + SHA-256, puis lancer un reviewer scientifique indépendant dédié avant toute promotion.
4. Si aucun PDF n'est capturé mais qu'un endpoint/document transport est découvert: créer un probe ciblé read-only sur cet endpoint.
5. Si aucun mécanisme RCP n'est découvert: passer à la cartographie officielle des documents/endpoints AMMPS sans répéter les boutons UI.
6. Ne modifier le manifest qu'après preuve complète + revue indépendante.

## Interdits
- Pas d'activation clinique M1.
- Pas de `SNAPSHOT_VERIFIED` sans artefact réel vérifié.
- Pas de `UNAVAILABLE_VERIFIED` sur simple absence/recherche négative/bouton désactivé.
- Pas de faux verdict reviewer.
- Pas d'assimilation CI verte = validation scientifique.
- Pas d'URL RCP déduite/fabriquée à partir de `javascript:void(0)`.

## Prompt de reprise
`Lis ce fichier depuis docs/pharmacology-m1-handover-20260915, vérifie master et le run du commit recherche ccf03cc376f1592be028700c46ab9a823b4f2f9a. M1-B2 est mergé et post-merge vert. Les 5 candidats READY Wave 1 ont tous donné NO_ENABLED_RCP_CONTROL dans le run chaîne #35121834201; aucun PDF officiel n'a été capturé. La stratégie a pivoté vers découverte metronidazole + clindamycin et inspection du mécanisme RCP AMMPS. Continuer jusqu'à preuve PDF réelle ou cartographie technique solide, sans promotion réglementaire non prouvée.`
