# Digital Crown — Pharmacologie Maroc M1 handover

Date: 2026-09-16
Status: ACTIVE — M1-B2 merged; AMMPS RCP mechanism proven; active-RCP identity mapping running; target dental families remain fail-closed; no clinical activation

## Goal
Construire la couverture pharmacologique dentaire Maroc avec preuve réglementaire fail-closed, puis validation scientifique indépendante avant toute activation clinique.

## Invariants
- Digital Crown reste local/on-premise.
- Aucun déploiement clinique/data sur Vercel.
- CI verte != validation scientifique/clinique.
- Recherche négative ou bouton désactivé != preuve d'absence réglementaire.
- Aucun `AUTO_OK`, aucune activation clinique M1.
- Aucun `SNAPSHOT_VERIFIED` sans vrai PDF AMMPS + URL officielle exacte + bytes + SHA-256 concordant + identité de présentation + revue indépendante.

## Lots fermés
- M1-A PR #517 → `d474ad18ba47d55a0d53f1f90e47a451f4dbac5e`.
- M1-B0 PR #518 → `81bf142021cdf4770e9c6ca92078306ac4898783`.
- M1-B1 PR #519 → `21651f22df9ba5210078969aa46abc527ba9e2bd`.
- Wave 1 evidence refresh PR #522 → `12f2550aaa38f3045095152ab862b587db109238`.
- Gate déterministe initiale PR #526 → `a396acfd6570ff24ca683009e1f31bdb3f2c0d92`.
- Réparation gate PR #537 → `fb3a870e2fba92a005a3e3de57ee378042b23be3`.
- M1-B2 PR #525 → `601cee32bab3169143cf61ca917e35d7bd1d6ee5`.

## M1-B2 — preuve finale
HEAD pré-merge `4b4cfd968951c97af39d3e757afde5185ffeb196`, base `fb3a870e2fba92a005a3e3de57ee378042b23be3`.
- deterministic gate #11 `35109483397`: SUCCESS;
- tests ciblés: 33 passed;
- CI `35109483296`: SUCCESS;
- T2 `35109483225`: SUCCESS;
- reviewer indépendant #7 `35109624600`: `approve_with_reservations`, 0 blocker, 0 major, 0 missing test, `clinical_activation_authorized=false`;
- post-merge CI `35110253634`: SUCCESS;
- PostgreSQL upgrade `35110253569`: SUCCESS.

## Wave 1 documentaire
Queue:
- READY_FOR_CAPTURE_TRANSPORT: paracetamol, ibuprofen, amoxicillin, penicillin_v, clarithromycin.
- PENDING_RCP_LINK_CONFIRMATION: metronidazole.
- PENDING_CURRENT_PRESENTATION_DISCOVERY: clindamycin.

Aucune donnée clinique extraite ou activée.

## Acquisition ciblée — vérifiée
Branche recherche: `research/pharmacology-rcp-first-capture-20260916`.

- Amoxicilline: run `35110885162`, artifact `10451738662`, digest `sha256:e4a88000c3293e090f12e2904fadd05a0cb61e666e99b05d64ec1e24d3b2189a` → contrôles RCP désactivés, aucun PDF.
- Ibuprofène: run `35115618383`, artifact `10454722384`, digest `sha256:3d781cf7cd37369df668fcefc8688628ec0967065b924591fa8a2558b22a2ef5` → `NO_ENABLED_IBUPROFEN_RCP_CONTROL`.
- Paracétamol: run `35116683651`, artifact `10455083590`, digest `sha256:46ceaa5835bfec127c6735a2cebbfb9fdec353f903b91aac57957caaeeac19a6` → `NO_ENABLED_PARACETAMOL_RCP_CONTROL`.
- Pénicilline V: run `35117194902`, artifact `10454339652`, digest `sha256:99e7fa7cde1146dc51fde61d0809790f7dd0646f26d21df59b52cc75027d0573` → `NO_ENABLED_PENICILLIN_V_RCP_CONTROL`.

### Chaîne READY
Commit `9c57795ec6f51c5a7389ad90424d3134bde95033`, run #6 `35121834201`: SUCCESS.
Artifact `10457267023`, digest `sha256:71efe115c423fb3107a461d7e471d4fafa116393cadc0f9f9fc5682a304d07fe`.
Résultat: les 5 familles READY ont toutes `NO_ENABLED_RCP_CONTROL`.

### Pending discovery
Commit `ccf03cc376f1592be028700c46ab9a823b4f2f9a`, run #7 `35123369625`: SUCCESS.
Artifact `10458925243`, digest `sha256:a21f4b7384eae1116c89470ae6799671952cb2befd96f51c1af2e73aaf497fe9`.
- Metronidazole: présentations actuelles trouvées, 12 contrôles RCP scoppés, 0 actif → reste `PENDING_RCP_LINK_CONFIRMATION`.
- Clindamycin: 2 présentations topiques seulement dans ce pass, RCP désactivés; aucune présentation systémique/orale commercialisée utile au scope dentaire prouvée → reste `PENDING_CURRENT_PRESENTATION_DISCOVERY`.

## Census global AMMPS RCP — preuve complète
Tentatives techniques:
- #8 `35126944871`: échec avant scan, cap interne pageCount trop bas.
- #9 `35127141170`: échec réseau `UND_ERR_SOCKET` pendant scan concurrent; aucune conclusion scientifique tirée.

Stratégie robuste commit `d700dce5ebec123f1e44aaaf3e1e2ade72e2d941`:
- scan séquentiel;
- retries bornés;
- checkpoints;
- artifact `always()`;
- validation seulement sur census complet sans page échouée.

Run #10 `35127544097`: SUCCESS.
Artifact `10459709561`, digest `sha256:b530bdac73f1dc46fa89aef993f05affc5a126d0dd6e51a2368a92842854b90e`.
Preuve exacte:
- `totalMedicaments`: 9908;
- `pageCount`: 826;
- `scannedPageCount`: 826;
- `failedPageCount`: 0;
- `rcpControlCount`: 9908;
- `enabledRcpControlCount`: 48;
- `disabledRcpControlCount`: 9860;
- 49 URL PDF candidates détectées, dont 48 sous le mécanisme RCP actif.

Conclusion autorisée: l'UI AMMPS supporte réellement des RCP actifs, mais seulement 48/9908 entrées au moment du census. Les 7 familles ciblées ci-dessus ne faisaient pas partie des contrôles RCP actifs observés.

## Transport RCP AMMPS — mécanisme prouvé
Run #11 `35130929361`: FAILURE technique uniquement, causée par un découpage HTML fragile du modal (`RCP control missing`). Aucun échec réglementaire à en tirer.

Correction commit `a1df648f60dc77a438e777cf79d95d6f9e5f923d` part directement des hrefs prouvés par le census.
Run #12 `35131011934`: SUCCESS.
Artifact `10460757859`, digest `sha256:2931e5058a2097a4bf76f03c797748d7849bc1f0d27f1ba96b9c9ab8a03e5a0e`.

Trois RCP actifs AMMPS ont été vérifiés end-to-end:
1. `medicamentModal9736` → HTTPS AMMPS, 200, `application/pdf`, `%PDF-`, 310960 bytes, SHA-256 `fc9842a03a4fdfefbd3bfa8c79a46c41bfa86882639c7c7c6ec675746ae3bff7`.
2. `medicamentModal5208` → HTTPS AMMPS, 200, `application/pdf`, `%PDF-`, 355809 bytes, SHA-256 `ee5f1060106c7ba69385d51ec0d56c633fd6086238f1f696ba0aff7660595bf8`.
3. `medicamentModal9807` → HTTPS AMMPS, 200, `application/pdf`, `%PDF-`, 359648 bytes, SHA-256 `fa1dc791059498539ea459fc46829e0e0d4007b93007359515220a7c5803d487`.

Le mécanisme officiel réellement observé est un href explicite sous `uploads/rcp/...`; aucune URL n'est à fabriquer pour un bouton désactivé.

## Mapping identité des 48 RCP actifs — en cours
Objectif: rattacher chacun des 48 hrefs actifs du census à son identité médicament/principe actif courante et filtrer les candidats potentiellement utiles au scope dentaire sans inférence clinique.

Run #13 `35131747120`, commit `67bad3c63d20f76a0988361fb9a828d183e91020`: FAILURE de parsing workflow avant création de job. Aucune requête AMMPS exécutée, aucune conclusion scientifique/réglementaire autorisée.

Workflow simplifié/réparé au commit `bdb2cc8a6be2ec71d0f0c6288dbc9c98b53ea469`:
- lecture read-only des seules pages contenant les 48 hrefs déjà prouvés;
- retries bornés;
- conservation du contexte texte autour de chaque href;
- filtre lexical conservateur des familles anti-infectieuses/antalgiques/anesthésiques potentiellement pertinentes;
- aucune promotion manifest, aucune activation clinique.

Run #14 `35131871843`.
État au dernier contrôle: `IN_PROGRESS`, étape `Map active RCP identities` active.

## État repo
Master vérifié le 2026-09-16: `5290df7cb1a12989ef3799f92e32fd49d02d5ca1`, commit GitHub signed/verified.
Branche recherche HEAD: `bdb2cc8a6be2ec71d0f0c6288dbc9c98b53ea469`.
Aucune mutation manifest, DB, patient, document ou activation clinique issue de cette phase de recherche.

## Décision actuelle
- Le mécanisme AMMPS RCP est techniquement prouvé.
- Les familles dentaires ciblées restent fail-closed parce que leurs contrôles RCP sont désactivés et aucun vrai PDF AMMPS correspondant n'a été capturé.
- Ne pas dériver une URL depuis le numéro de modal ou le pattern de fichier des 48 cas actifs.
- Le mapping #14 doit confirmer explicitement l'identité des 48 hrefs avant toute conclusion sur leur pertinence dentaire.

## Next exact
1. Lire le résultat + artifact du mapping #14 `35131871843` une fois terminé.
2. Vérifier chaque candidat lexicalement pertinent par association explicite href ↔ identité médicament/principe actif; rejeter tout faux positif de voisinage de texte.
3. Si un vrai RCP AMMPS d'une famille cible ou d'une famille dentaire utile est identifié: capturer URL + bytes + SHA-256 + identité de présentation et lancer reviewer indépendant.
4. Sinon poursuivre uniquement des voies officielles non déduites pour les 7 familles cibles.
5. Aucune activation clinique avant revue scientifique/humaine dédiée.

## Interdits
- Pas de `SNAPSHOT_VERIFIED` ou `UNAVAILABLE_VERIFIED` à partir d'un bouton désactivé.
- Pas d'URL fabriquée à partir de `modalId`, d'un timestamp ou d'un pattern `/uploads/rcp/`.
- Pas d'assimilation CI verte = validation clinique.
- Pas de sélection d'un RCP dentaire sur simple mot-clé voisin sans identité explicitement rattachée au href.

## Prompt de reprise
`Lis ce fichier depuis docs/pharmacology-m1-handover-20260915. Vérifie master, la branche recherche et le mapping #35131871843. M1-B2 est mergé/post-merge vert. Census AMMPS #35127544097: 9908 médicaments, 826/826 pages, 0 erreur, 48 contrôles RCP actifs, 9860 désactivés. Transport officiel prouvé par #35131011934 sur 3 vrais PDF HTTPS AMMPS 200 + application/pdf + %PDF- + SHA-256. Les 7 familles dentaires ciblées restent fail-closed. Mapping des 48 actifs: #13 était un échec de parsing sans job; #14 au commit bdb2cc8... est le runner réparé. Prochaine action: exploiter son artifact, vérifier les candidats pertinents, puis seulement lancer une revue indépendante si un vrai RCP utile est prouvé.`
