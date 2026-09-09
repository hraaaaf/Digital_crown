# DIGITAL CROWN — SCIENTIFIC CORE REBUILD — CANONICAL HANDOVER

**Règle de reprise :** vérifier `repo / branche / PR / HEAD / CI` avant toute conclusion. Les runs historiques ne valent jamais état courant.

## GOAL FINAL

Noyau scientifique minimal, explicable, sourcé/versionné et fail-closed.

Invariant : `measurement != diagnosis != indication != treatment`.

Succès : aucune donnée patient inventée influente ; aucune interprétation ou décision clinique autonome non validée ; séparation observation/interprétation/décision praticien ; tests et CI verts avant merge ; aucun déploiement Vercel sans autorisation explicite.

## REPO

Repo : `hraaaaf/Digital_crown`  
Branche : `refactor/scientific-core-purge`  
PR : `#371` — draft, ouverte, mergeable au dernier contrôle  
Base : `master`

Aucun pourcentage global n'est déclaré sans recalcul vérifié.

## LOT 7 — CÉPHALOMÉTRIE / ORTHODONTIE

### État vérifié

- Frontend : aucune génération thérapeutique automatique ; aucune norme locale ; sexe patient nullable/reset `null` ; CVM âge/sexe et DDM par IMPA neutralisés.
- `CephaloService` utilise `cephalo_safe_engine`.
- `cephalo_engine.py` est géométrie seule : normes locales, z-scores, croissance T1/T2, diagnostic et traitement autonomes supprimés.
- `cephalo_consistency_validator.py` ne garde que cohérence structurelle, unités et calibration.
- `bilan_ortho_engine.py` restitue valeurs brutes + données praticien, sans classe/typologie/sévérité/diagnostic/traitement autonome.
- `backend/routers/ia.py` n'importe plus directement `cephalo_engine` ni `ai_advisor`.
- `backend/services/clinical_intelligence.py` ne dépend plus de `ai_advisor` ; son chemin céphalo historique restitue désormais les mesures brutes uniquement, sans cohorte âge-dérivée, diagnostic, indication ou stratégie automatique.
- `backend/services/ai_advisor.py` est supprimé.

### Audit `ai_advisor` corrigé

L'audit initial était incomplet. Deux runs ont révélé des références runtime après suppression du wrapper :

1. CI `34344464825` : référence résiduelle dans `backend/routers/ia.py`, corrigée.
2. CI `34353944361` et T2 `34353944561` : dépendance active dans `backend/services/clinical_intelligence.py`, corrigée par remplacement fail-closed.

Ces runs sont des preuves historiques rouges, pas une certification du HEAD courant.

### Tests clés

- `test_cephalo_geometry_only.py`
- `test_cephalo_treatment_boundary.py`
- `test_cephalo_engine_reachability.py`
- `test_cephalo_consistency_structural_only.py`
- `test_bilan_ortho_fail_closed.py`
- `test_ortho_frontend_fail_closed_contract.py`
- `test_clinical_intelligence_cephalo_fail_closed.py`
- `test_scientific_core_purge_contract.py`

## AUTRES LOTS ENCORE OUVERTS

Les autres chantiers scientifiques restent distincts du closeout ortho. La fermeture du lot ortho ne vaut pas certification scientifique globale.

## CLOSEOUT LOT ORTHO

Ordre : `code → tests → comportement observé → docs → CI → cohérence PR → ready → merge → post-merge`.

Avant merge : aucun rouge scientifique ; aucun comportement clinique autonome non validé connu dans ce lot ; docs cohérentes ; checks requis du même HEAD verts/acceptables.

## NEXT EXACT

Vérifier la CI du HEAD créé après correction `clinical_intelligence` + garde dédié + docs. Si rouge : diagnostiquer/corriger. Si verte : vérifier tous les checks, passer la PR ready, merger, puis vérifier le post-merge. Aucun déploiement Vercel.
