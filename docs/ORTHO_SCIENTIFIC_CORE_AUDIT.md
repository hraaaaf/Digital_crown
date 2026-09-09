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
| `cephalo_consistency_validator.py` | cohérence structurelle, unités, calibration seulement |
| `bilan_ortho_engine.py` | valeurs brutes + données praticien ; aucune classe/typologie/sévérité/diagnostic/traitement autonome |
| `ai_advisor.py` | supprimé après preuve de non-reachability runtime |

## Frontières de sécurité

- `CephaloService` utilise `cephalo_safe_engine`, pas `cephalo_engine` directement.
- `test_cephalo_engine_reachability.py` verrouille la reachability du moteur.
- `test_cephalo_geometry_only.py` verrouille le contrat géométrie-seule.
- `test_cephalo_treatment_boundary.py` verrouille absence de conversion IMPA→espace et préservation des données praticien.
- `test_cephalo_consistency_structural_only.py` interdit le retour des pseudo-normes dans le gate PDF.
- `test_bilan_ortho_fail_closed.py` interdit classes/typologies/sévérités automatiques.
- `test_ortho_frontend_fail_closed_contract.py` verrouille aussi sexe nullable/reset et interdit tout fallback masculin.

## Purge `ai_advisor`

Audit PR-wide avant suppression :
- `cephalo_service.py` n'importait plus le module ;
- le seul import runtime restant était un import inutilisé dans `elite_manager.py` ;
- aucun appel de `ai_advisor` n'existait dans `elite_manager.py` ;
- les deux tests restants ciblaient uniquement ce wrapper de compatibilité.

Conséquence : import mort retiré, `backend/services/ai_advisor.py` et ses deux tests dédiés supprimés. Aucun remplacement clinique n'est nécessaire car aucun flux runtime n'en dépendait.

## Base scientifique verrouillée

- CVM : morphologie C2-C4, jamais âge/sexe seuls. McNamara & Franchi, Angle Orthod 2018 ; Gabriel et al., AJODO 2009.
- Extraction : décision multifactorielle, jamais DDM/IMPA seuls. Elias et al., Angle Orthod 2024 ; AJODO 2018 PMID 30075925.
- CBCT : justification individualisée. AAOMR position statement 2013.
- Normes populationnelles : applicabilité/provenance explicites ; aucune généralisation silencieuse. Ousehal et al., Int Orthod 2012.
- Croissance T1/T2 : aucun vecteur fixe présenté comme prédiction individuelle ; anciennes projections physiquement retirées.

## Preuve CI historique utile

Run `34340987448` : backend avait atteint `277 passed, 1 skipped` avant un unique échec de test obsolète exigeant encore le texte `référence normative non validée`. Ce test a été aligné sur le contrat plus strict : **mesure brute uniquement, aucune sémantique normative injectée**.

## Remaining exact

1. CI complète sur le HEAD final de purge ;
2. corriger toute régression attribuable au lot ;
3. vérifier tous les checks requis sur ce même HEAD ;
4. mettre PR/docs en cohérence finale ;
5. sortir du draft puis merge uniquement avec preuves vertes ;
6. contrôle post-merge ;
7. aucun déploiement Vercel sans autorisation explicite.
