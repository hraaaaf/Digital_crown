# ORTHODONTIE — SCIENTIFIC CORE AUDIT

Date: 2026-09-09  
Branch: `refactor/scientific-core-purge`  
PR: #371

## Goal

Invariant obligatoire : `measurement != diagnosis != indication != treatment`.

Le logiciel peut calculer la géométrie, préserver les observations documentées et exposer une infrastructure normative sourcée/versionnée. Il ne doit jamais transformer seul une mesure ou une donnée démographique en diagnostic, indication, appareil, mécanique, imagerie, chirurgie, extraction ou prédiction patient-spécifique.

## État vérifié

| Zone | État |
|---|---|
| `Step3Clinical.tsx` | aucune génération thérapeutique automatique ; décision praticien |
| `Step4Documents.tsx` | valeurs brutes ; aucune norme locale ni Damon par défaut |
| `orthoExpertSystem.ts` | fail-closed ; aucune extraction/appareil/mécanique/imagerie/chirurgie autonome |
| `cephaloUtils.ts` | CVM âge/sexe, DDM par IMPA, apex synthétiques et traitement auto neutralisés |
| `useOrthoStore.ts` | sexe patient nullable, défaut/reset `null`, restauration uniquement `M/F` |
| `cephalo_engine.py` | géométrie seule ; normes/z-scores/croissance/traitement/diagnostic supprimés |
| `cephalo_safe_engine.py` | défense en profondeur conservée |
| `cephalo_consistency_validator.py` | cohérence structurelle, identité SNA-SNB=ANB, unités, calibration seulement |
| `bilan_ortho_engine.py` | valeurs brutes + données praticien ; aucune classe/typologie/sévérité/diagnostic/traitement autonome |
| `clinical_intelligence.py` | synthèse céphalo fail-closed ; motifs ODF = routage de spécialité uniquement, sans hint thérapeutique |
| `ai_advisor.py` | supprimé ; références runtime connues retirées |

## Frontières de sécurité

- `CephaloService` utilise `cephalo_safe_engine`, pas `cephalo_engine` directement.
- `test_cephalo_engine_reachability.py` verrouille la reachability du moteur.
- `test_cephalo_geometry_only.py` verrouille le contrat géométrie-seule.
- `test_cephalo_treatment_boundary.py` verrouille absence de conversion IMPA→espace et préservation des données praticien.
- `test_cephalo_consistency_structural_only.py` interdit le retour des pseudo-normes dans le gate PDF.
- `test_cephalo_service_normative_context.py` vérifie le chemin réel `process_new_radio/refine_analysis` : cohortes `Non classé`, normes/z-scores absents, projections et narrative automatiques vides ; âge/sexe ne créent aucune autorité normative.
- `test_bilan_ortho_fail_closed.py` interdit classes/typologies/sévérités automatiques.
- `test_ortho_frontend_fail_closed_contract.py` verrouille sexe nullable/reset et interdit tout fallback masculin.
- `test_clinical_intelligence_cephalo_fail_closed.py` interdit le retour de `ai_advisor`, d'une synthèse diagnostique ou stratégie thérapeutique céphalo et verrouille `ORTHODONTIE -> motif_treatment_hints == []`.
- `test_scientific_core_purge_contract.py` interdit la réapparition du wrapper `ai_advisor` et de références runtime.

## Purge `ai_advisor` — audit corrigé

L'audit initial était incomplet : après suppression du wrapper, deux CI successives ont révélé des dépendances runtime résiduelles.

1. `backend/routers/ia.py` importait encore `ai_advisor` et importait directement `cephalo_engine` ; les deux imports, inutilisés, ont été retirés.
2. `backend/services/clinical_intelligence.py` importait et appelait réellement `ai_advisor.generate_diagnostic()` pour produire une cohorte enfant/adulte, une synthèse diagnostique et une stratégie thérapeutique céphalo. Ce chemin a été réécrit en sortie fail-closed de mesures brutes uniquement.

Les runs `34344464825` puis `34353944361` ont échoué sur ces références. Ils constituent des preuves historiques rouges, pas une certification du HEAD courant.

## Nettoyage des tests normatifs historiques

Les tests legacy qui imposaient encore des seuils locaux SNA/SNB, classes II/III, soft/hard bounds, warnings IMPA, cohortes automatiques ou obligations d'actes pour tous les motifs ont été supprimés/réécrits lorsqu'ils contredisaient le contrat geometry-only/fail-closed. Aucun seuil clinique n'a été restauré pour satisfaire la CI.

Le validateur conserve uniquement :

- cohérence de structure ;
- identité arithmétique `SNA - SNB = ANB` ;
- contradictions d'unités ;
- avertissement de calibration non vérifiée.

## Preuve de closeout avant mise à jour documentaire

HEAD produit : `a6ddb33041b07a772e55ba7f44b01fa69b2ae1c1`.

- CI `34401719011` : **success**.
- Backend : **3019 passed, 8 skipped, 4 warnings** en 604.31 s.
- Frontend tests/build : **success**.
- Garde production : **success**.
- M4-A / M4-B / M4-C : **success**.
- T2 `34401719076` : **success**.
- P7 `34401719000` : **success**.
- P8 `34401719065` : **success**.
- Settings `34401719008` : **success**.
- Catalog `34401719077` : **success**.
- P6 Windows Packaging `34401719033` : **success**.
- M6-I `34401719102` : **skipped**.
- Patient Indicators `34401719118` : échec de harness connu sur l'attente obsolète du heading `Dossiers Patients`, après backend ciblé 10/10, frontend ciblé 4/4, build et runtimes verts. Aucune régression produit démontrée ; le correctif du workflow est bloqué par le garde d'écriture du connecteur GitHub.

Aucune review ni thread de review n'était ouvert au contrôle de closeout.

## Base scientifique verrouillée

- CVM : morphologie C2-C4, jamais âge/sexe seuls. McNamara & Franchi, Angle Orthod 2018 ; Gabriel et al., AJODO 2009.
- Extraction : décision multifactorielle, jamais DDM/IMPA seuls. Elias et al., Angle Orthod 2024 ; AJODO 2018 PMID 30075925.
- CBCT : justification individualisée. AAOMR position statement 2013.
- Normes populationnelles : applicabilité/provenance explicites ; aucune généralisation silencieuse. Ousehal et al., Int Orthod 2012.
- Croissance T1/T2 : aucun vecteur fixe présenté comme prédiction individuelle ; anciennes projections physiquement retirées.

## Remaining exact

1. vérifier la CI du nouveau HEAD documentaire ;
2. corriger toute régression attribuable au lot ;
3. vérifier les checks visibles sur ce même HEAD ;
4. cohérence PR finale ;
5. sortir du draft puis merge avec `expected_head_sha` exact si les preuves restent acceptables ;
6. contrôle post-merge ;
7. aucun déploiement Vercel sans autorisation explicite.
