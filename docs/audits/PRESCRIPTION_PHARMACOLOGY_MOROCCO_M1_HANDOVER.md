# Digital Crown — Pharmacologie Maroc M1 handover

Date: 2026-09-16
Status: ACTIVE — M1-B2 merged; AMMPS RCP transport proven; strict identity mapping pending; target dental families remain fail-closed; no clinical activation

## Goal
Construire la couverture pharmacologique dentaire Maroc avec preuve réglementaire fail-closed, puis validation scientifique indépendante avant toute activation clinique.

## Invariants
- Digital Crown reste local/on-premise.
- Aucun déploiement clinique/data sur Vercel.
- CI verte != validation scientifique/clinique.
- Recherche négative ou bouton désactivé != preuve d'absence réglementaire.
- Aucun `AUTO_OK`, aucune activation clinique M1.
- Aucun `SNAPSHOT_VERIFIED` sans vrai PDF AMMPS + URL officielle exacte + bytes + SHA-256 concordant + identité de présentation + revue indépendante.
- Aucun RCP ne peut être qualifié dentaire sur simple voisinage HTML; l'association exacte modal ↔ href ↔ identité est requise.

## Lots fermés
- M1-A PR #517 → `d474ad18ba47d55a0d53f1f90e47a451f4dbac5e`.
- M1-B0 PR #518 → `81bf142021cdf4770e9c6ca92078306ac4898783`.
- M1-B1 PR #519 → `21651f22df9ba5210078969aa46abc527ba9e2bd`.
- Wave 1 evidence refresh PR #522 → `12f2550aaa38f3045095152ab862b587db109238`.
- Gate déterministe PR #526 → `a396acfd6570ff24ca683009e1f31bdb3f2c0d92`.
- Réparation gate PR #537 → `fb3a870e2fba92a005a3e3de57ee378042b23be3`.
- M1-B2 PR #525 → `601cee32bab3169143cf61ca917e35d7bd1d6ee5`.

## M1-B2 preuve finale
HEAD pré-merge `4b4cfd968951c97af39d3e757afde5185ffeb196`.
- deterministic gate `35109483397`: SUCCESS;
- targeted tests: 33 passed;
- CI `35109483296`: SUCCESS;
- T2 `35109483225`: SUCCESS;
- reviewer indépendant `35109624600`: `approve_with_reservations`, 0 blocker, 0 major, 0 missing test, `clinical_activation_authorized=false`;
- post-merge CI `35110253634`: SUCCESS;
- PostgreSQL upgrade `35110253569`: SUCCESS.

## Wave 1 documentaire
- READY_FOR_CAPTURE_TRANSPORT: paracetamol, ibuprofen, amoxicillin, penicillin_v, clarithromycin.
- PENDING_RCP_LINK_CONFIRMATION: metronidazole.
- PENDING_CURRENT_PRESENTATION_DISCOVERY: clindamycin.

Aucune donnée clinique extraite ou activée.

## Acquisition ciblée vérifiée
Branche: `research/pharmacology-rcp-first-capture-20260916`.
- Amoxicilline run `35110885162`: contrôles RCP désactivés, aucun PDF.
- Ibuprofène run `35115618383`: `NO_ENABLED_IBUPROFEN_RCP_CONTROL`.
- Paracétamol run `35116683651`: `NO_ENABLED_PARACETAMOL_RCP_CONTROL`.
- Pénicilline V run `35117194902`: `NO_ENABLED_PENICILLIN_V_RCP_CONTROL`.
- Chaîne READY run #6 `35121834201`: SUCCESS; les 5 familles READY ont toutes `NO_ENABLED_RCP_CONTROL`.
- Pending discovery run #7 `35123369625`: SUCCESS; metronidazole = 12 contrôles RCP scoppés, 0 actif; clindamycin = 2 présentations topiques dans ce pass, RCP désactivés, aucune présentation systémique/orale commercialisée utile prouvée.

## Census global AMMPS RCP — preuve complète
- #8 `35126944871`: échec technique, cap pageCount trop bas.
- #9 `35127141170`: échec réseau `UND_ERR_SOCKET`; aucune conclusion scientifique.
- Commit robuste `d700dce5ebec123f1e44aaaf3e1e2ade72e2d941`.
- #10 `35127544097`: SUCCESS.
- Artifact `10459709561`, digest `sha256:b530bdac73f1dc46fa89aef993f05affc5a126d0dd6e51a2368a92842854b90e`.

Preuve exacte:
- 9908 médicaments;
- 826/826 pages;
- 0 page échouée;
- 9908 contrôles RCP;
- 48 actifs;
- 9860 désactivés;
- 49 URL PDF candidates détectées.

Conclusion autorisée: l'UI AMMPS supporte réellement des RCP actifs, mais seulement 48/9908 entrées au moment du census. Les 7 familles ciblées ne faisaient pas partie des contrôles RCP actifs observés.

## Transport RCP AMMPS — mécanisme prouvé
- #11 `35130929361`: échec technique du découpage HTML, aucune conclusion réglementaire.
- Correction `a1df648f60dc77a438e777cf79d95d6f9e5f923d`.
- #12 `35131011934`: SUCCESS.
- Artifact `10460757859`, digest `sha256:2931e5058a2097a4bf76f03c797748d7849bc1f0d27f1ba96b9c9ab8a03e5a0e`.

Trois RCP actifs vérifiés end-to-end:
1. modal9736 → 200 `application/pdf`, `%PDF-`, 310960 bytes, SHA-256 `fc9842a03a4fdfefbd3bfa8c79a46c41bfa86882639c7c7c6ec675746ae3bff7`.
2. modal5208 → 200 `application/pdf`, `%PDF-`, 355809 bytes, SHA-256 `ee5f1060106c7ba69385d51ec0d56c633fd6086238f1f696ba0aff7660595bf8`.
3. modal9807 → 200 `application/pdf`, `%PDF-`, 359648 bytes, SHA-256 `fa1dc791059498539ea459fc46829e0e0d4007b93007359515220a7c5803d487`.

Mécanisme réellement observé: href explicite sous `uploads/rcp/...`; aucune URL ne doit être fabriquée pour un bouton désactivé.

## Mapping identité des 48 RCP actifs
### #13
Run `35131747120`, commit `67bad3c63d20f76a0988361fb9a828d183e91020`: FAILURE de parsing workflow avant job. Aucune conclusion scientifique.

### #14 — cartographie de voisinage, utile mais insuffisante
Commit `bdb2cc8a6be2ec71d0f0c6288dbc9c98b53ea469`.
Run `35131871843`: SUCCESS.
Artifact `10461837711`, digest `sha256:8af08efbe149de29081359c4e397e999c8ed183eb9613a65dd25ff8a1227cd1b`.
- 48/48 hrefs mappés.
- 2 matches lexicaux remontés: modal9539 avec texte voisin SCANDONEST/mépivacaïne; modal9203 avec texte voisin SOCLAV/amoxicilline-acide clavulanique.
- Revue adversariale: ces 2 matches ne prouvent PAS l'identité du RCP; le voisinage HTML inclut des entrées adjacentes. Ils sont reclassés comme faux positifs/non prouvés et ne peuvent déclencher aucune promotion.

### #15 — mapping strict exact-modal
Commit `cbb223eff8ce6cc4f8765cf03e495e1e69385769`.
Principe:
- localiser exactement le `div` du `modalId` cible;
- borner le bloc à l'entrée du modal suivant;
- exiger exactement 1 href `uploads/rcp/...pdf` dans ce bloc;
- exiger que cet href soit celui du census;
- filtrer les mots-clés dentaires uniquement dans CE bloc;
- aucune mutation manifest/DB, aucune activation clinique.

Run #15 `35142068612`.
État au dernier contrôle: `QUEUED`.

## État repo
Master dernière vérification: `5290df7cb1a12989ef3799f92e32fd49d02d5ca1`, signed/verified.
Branche recherche HEAD: `cbb223eff8ce6cc4f8765cf03e495e1e69385769`.
Aucune mutation manifest, DB, patient, document ou activation clinique issue de cette phase.

## Décision actuelle
- Le mécanisme AMMPS RCP est techniquement prouvé.
- Les 7 familles dentaires ciblées restent fail-closed.
- Les 2 hits de #14 sont invalidés comme preuves d'identité.
- Seul #15 peut décider si l'un des 48 RCP actifs appartient réellement à une molécule dentaire pertinente.

## Next exact
1. Lire le résultat + artifact de #15 `35142068612` une fois exécuté.
2. Si candidat strict réel: capturer son PDF officiel + bytes + SHA-256 + identité de présentation; lancer reviewer indépendant.
3. Si zéro candidat strict: fermer le mapping des 48 actifs et poursuivre uniquement les voies officielles non déduites pour les 7 familles cibles.
4. Aucune activation clinique avant revue scientifique/humaine dédiée.

## Interdits
- Pas de `SNAPSHOT_VERIFIED` ou `UNAVAILABLE_VERIFIED` à partir d'un bouton désactivé.
- Pas d'URL fabriquée à partir de modalId/timestamp/pattern `/uploads/rcp/`.
- Pas d'assimilation CI verte = validation clinique.
- Pas de sélection sur simple mot-clé voisin.

## Prompt de reprise
`Lis ce fichier depuis docs/pharmacology-m1-handover-20260915. Vérifie master, la branche recherche et #35142068612. Census #35127544097: 9908 médicaments, 826/826 pages, 48 RCP actifs. Transport officiel #35131011934: 3 vrais PDF AMMPS vérifiés. #35131871843 a mappé 48/48 mais ses 2 hits SCANDONEST/SOCLAV étaient des faux positifs de voisinage, donc invalidés. #35142068612 au commit cbb223ef... impose une association stricte modal↔href↔identité. Les 7 familles ciblées restent fail-closed jusqu'à preuve PDF officielle + revue indépendante.`
