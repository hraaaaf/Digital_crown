# Digital Crown — Pharmacologie Maroc M1 handover

Date: 2026-09-16
Status: ACTIVE — M1-B2 merged; AMMPS RCP transport proven; 48 active RCPs strictly mapped with zero dental target proven; public-route audit complete; official AMMPS request is the next human gate; no clinical activation

## Goal
Construire la couverture pharmacologique dentaire Maroc avec preuve réglementaire fail-closed, puis validation scientifique indépendante avant toute activation clinique.

## Invariants
- Digital Crown reste local/on-premise.
- Aucun déploiement clinique/data sur Vercel.
- CI verte != validation scientifique/clinique.
- Recherche négative ou bouton désactivé != preuve d'absence réglementaire.
- Aucun `AUTO_OK`, aucune activation clinique M1.
- Aucun `SNAPSHOT_VERIFIED` sans vrai PDF AMMPS + URL officielle exacte + bytes + SHA-256 concordant + identité de présentation + revue indépendante.
- Aucun `UNAVAILABLE_VERIFIED` sans preuve officielle explicite d'absence.
- Aucun RCP ne peut être qualifié dentaire sur simple voisinage HTML; l'association exacte modal ↔ href ↔ identité est requise.
- ANSM/EMA ou autre régulateur étranger ne remplace pas la provenance réglementaire AMMPS exigée par le contrat M1.

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

### #14 — cartographie de voisinage, insuffisante
Commit `bdb2cc8a6be2ec71d0f0c6288dbc9c98b53ea469`.
Run `35131871843`: SUCCESS.
Artifact `10461837711`, digest `sha256:8af08efbe149de29081359c4e397e999c8ed183eb9613a65dd25ff8a1227cd1b`.
- 48/48 hrefs mappés.
- 2 matches lexicaux SCANDONEST/mépivacaïne et SOCLAV/amoxicilline-clavulanate.
- Revue adversariale: faux positifs/non prouvés de voisinage HTML; aucune promotion autorisée.

### #15 — mapping strict exact-modal, fermé
Commit `cbb223eff8ce6cc4f8765cf03e495e1e69385769`.
Run `35142068612`: SUCCESS.
Artifact `10465272557`, digest `sha256:15857f36225b3f04375170db9f26e8fb7fe1548c8399efa523db58e52384ad78`.

Preuve exacte:
- `mappedCount=48`;
- `strictBindingCount=48`;
- chaque href actif est rattaché à son modal exact;
- seul match lexical restant = modal9203, titre exact `SMOFKABIVEN E`; le mot `AMOXICIL...` appartient au début de l'entrée SOCLAV suivante et ne prouve aucun RCP SOCLAV;
- zéro RCP actif parmi les 48 n'est prouvé comme appartenant au scope dentaire Wave 1;
- aucune mutation manifest/DB; aucune activation clinique.

Décision: fermer la piste « 48 RCP actifs → candidat dentaire » et ne pas poursuivre le scraping de ces 48 entrées.

## Audit des surfaces officielles AMMPS — fermé
Document: `docs/audits/PRESCRIPTION_PHARMACOLOGY_MOROCCO_RCP_OFFICIAL_SURFACE_AUDIT_2026-09-16.md`.
Commit docs: `398b29ebd50f376dafe993dafc9f46fa8efb6ed8`.

Constats vérifiés:
- la surface Recherche médicaments présente les familles cibles mais leurs contrôles RCP observés sont non actifs;
- la Liste Marocaine des médicaments affiche `Lien RCP / NAF -` pour plusieurs présentations pertinentes et courantes, dont CLAMOXYL 500 mg suspension 60 ml, CLARADOL 500 mg, ZECLAR 25 mg/ml et 500 mg, ainsi que plusieurs amoxicilline/acide clavulanique;
- le RMMG est utile pour l'identité package/EAN, notamment le métronidazole, mais n'est pas un fallback RCP autorisé;
- ces preuves démontrent la non-exposition publique du lien dans ces surfaces, PAS l'absence réglementaire du RCP;
- `UNAVAILABLE_VERIFIED` reste interdit;
- le contrat M1 exige toujours une provenance AMMPS officielle pour `SNAPSHOT_VERIFIED`.

## Demande AMMPS préparée — human gate
Draft: `docs/audits/PRESCRIPTION_PHARMACOLOGY_MOROCCO_RCP_AMMPS_REQUEST_DRAFT_2026-09-16.md`.
Commit docs: `7a701628839b5671ca12fd0fa3afe6823a8aa232`.

Le draft demande pour les 7 familles soit l'URL officielle exacte du RCP courant, soit une copie officielle liée à la présentation, soit la procédure/statut documentaire officiel si le RCP n'est pas publiquement accessible.

Canaux documentés:
- coordonnées institutionnelles courantes publiées sur le site AMMPS + parcours réclamation/recours;
- communiqué AMMPS historique du 15/02/2019: Service de l'enregistrement, `enregistrement.dmp@sante.gov.ma` (`u.dm.dmp@sante.gov.ma` indiqué entre parenthèses). Cette adresse historique n'est pas supposée opérationnelle sans confirmation/réponse.

Aucun message n'a été envoyé. L'envoi est le premier vrai human gate externe.

## État repo
Master dernière vérification: `5290df7cb1a12989ef3799f92e32fd49d02d5ca1`, signed/verified.
Branche recherche HEAD: `cbb223eff8ce6cc4f8765cf03e495e1e69385769`.
Branche docs: `docs/pharmacology-m1-handover-20260915`.
Aucune mutation manifest, DB, patient, document clinique ou activation clinique issue de cette phase.

## Décision actuelle
- Le mécanisme AMMPS RCP est techniquement prouvé.
- Les 48 RCP publics actifs ne contiennent aucun candidat dentaire Wave 1 prouvé.
- Les surfaces AMMPS publiques secondaires confirment l'identité/statut de plusieurs présentations mais n'exposent pas de lien RCP pour les cibles vérifiées.
- Les 7 familles restent fail-closed.
- La prochaine étape n'est plus du scraping: c'est une demande documentaire officielle AMMPS.

## Next exact
HUMAN GATE: confirmer l'envoi de la demande AMMPS préparée et l'identité/signature de l'expéditeur.

Après réponse AMMPS:
1. lier chaque document à la présentation exacte;
2. vérifier domaine/chaîne de provenance officielle, `%PDF-`, bytes et SHA-256;
3. stocker uniquement l'artefact autorisé sous `backend/data/rcp/...`;
4. lancer le reviewer scientifique indépendant;
5. seulement ensuite préparer une promotion manifest;
6. tests/gates exact-head puis closeout.

## Interdits
- Pas de `SNAPSHOT_VERIFIED` ou `UNAVAILABLE_VERIFIED` à partir d'un bouton désactivé ou `Lien RCP / NAF -`.
- Pas d'URL fabriquée à partir de modalId/timestamp/pattern `/uploads/rcp/`.
- Pas de fallback réglementaire ANSM/EMA/CNOPS/RMMG pour satisfaire M1.
- Pas d'assimilation CI verte = validation clinique.
- Pas d'activation clinique avant revue scientifique/humaine dédiée.

## Prompt de reprise
`Lis ce fichier depuis docs/pharmacology-m1-handover-20260915. Vérifie master et la branche recherche. Census #35127544097: 9908 médicaments, 826/826 pages, 48 RCP actifs. Transport #35131011934: 3 vrais PDF AMMPS vérifiés. Mapping strict #35142068612: SUCCESS, 48/48 bindings exacts, zéro candidat dentaire Wave 1 prouvé. L'audit officiel des surfaces AMMPS est dans PRESCRIPTION_PHARMACOLOGY_MOROCCO_RCP_OFFICIAL_SURFACE_AUDIT_2026-09-16.md. La demande AMMPS est prête dans PRESCRIPTION_PHARMACOLOGY_MOROCCO_RCP_AMMPS_REQUEST_DRAFT_2026-09-16.md mais n'a pas été envoyée. Les 7 familles restent fail-closed. Next = human gate pour envoi AMMPS; aucune promotion avant PDF officiel + SHA + revue indépendante.`
