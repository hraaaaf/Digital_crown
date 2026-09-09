# DIGITAL CROWN — SCIENTIFIC CORE REBUILD — CANONICAL HANDOVER

**Rôle :** fichier canonique de reprise.  
**Règle :** à chaque reprise, vérifier `repo / branche / PR / HEAD / CI`. Les SHA/runs historiques ne valent jamais état courant.

## GOAL FINAL

Reconstruire un noyau scientifique minimal, explicable, sourcé/versionné, patient-specific et fail-closed.

Invariant : `measurement != diagnosis != indication != treatment`.

### Succès observable

1. aucune donnée patient synthétique susceptible d'influencer une décision ;
2. aucune règle thérapeutique autonome non validée ;
3. aucune interprétation diagnostique autonome non validée ;
4. observation, interprétation, safety et décision praticien séparées ;
5. provenance/applicabilité explicites ;
6. tests négatifs + CI verts avant merge ;
7. aucun déploiement Vercel sans autorisation explicite.

## REPO

Repo : `hraaaaf/Digital_crown`  
Branche : `refactor/scientific-core-purge`  
PR : `#371` — draft, ouverte, mergeable au dernier contrôle  
Base : `master`

Le HEAD final est celui du commit qui supprime le wrapper `ai_advisor`; le vérifier avant toute conclusion.

## ÉTAT GLOBAL

- Phase 1 nettoyage scientifique : **EN COURS**.
- Panorama/report : purge fermée historiquement.
- Prescription démographique : fail-closed historiquement certifiée.
- Céphalométrie/orthodontie : purge code principale terminée ; certification CI finale restante.
- Prescription/safety globale et `clinical_coherence` : rebuild/consolidation encore restants hors lot ortho.
- Aucun pourcentage global déclaré sans recalcul vérifié.

## LOT 7 — CÉPHALOMÉTRIE / ORTHODONTIE

### Goal

Conserver géométrie, calibration, observations et données praticien ; supprimer toute conversion autonome `mesure → diagnostic/indication/traitement` non validée et toute donnée patient inventée.

### Frontend vérifié

- `Step3Clinical.tsx` : aucune génération thérapeutique automatique.
- `Step4Documents.tsx` : aucune norme locale ni Damon par défaut.
- `orthoExpertSystem.ts` : fail-closed ; aucune extraction/appareil/mécanique/imagerie/chirurgie autonome.
- `cephaloUtils.ts` : CVM âge/sexe, DDM corrigée par IMPA, apex synthétiques et traitement auto neutralisés.
- `useOrthoStore.ts` : `sexePatient: 'M' | 'F' | null`, défaut/reset `null`, restauration uniquement si valeur sauvegardée exactement `M/F`.
- `test_ortho_frontend_fail_closed_contract.py` verrouille ce contrat et interdit `sexePatient='M'` / fallback `'M'`.

### Backend vérifié

- `CephaloService` utilise `cephalo_safe_engine`.
- `cephalo_engine.py` est **géométrie seule** : plus de normes locales, z-scores, DDM IMPA/2,5°, T1/T2 croissance, diagnostic ou traitement autonome.
- `cephalo_safe_engine.py` reste une défense en profondeur.
- `cephalo_consistency_validator.py` ne garde que contrôles structurels/unités/calibration.
- `bilan_ortho_engine.py` ne produit plus Classe I/II/III, typologie Tweed, diagnostic IMPA, sévérité DDM ni traitement autonome. Valeurs brutes + données praticien uniquement.
- `ai_advisor.py` : **supprimé** après audit de reachability. Son seul import runtime résiduel dans `elite_manager.py` était inutilisé et a été retiré ; ses deux tests dédiés ont été supprimés avec lui.

### Tests clés

- `backend/tests/test_cephalo_geometry_only.py`
- `backend/tests/test_cephalo_treatment_boundary.py`
- `backend/tests/test_cephalo_engine_reachability.py`
- `backend/tests/test_cephalo_consistency_structural_only.py`
- `backend/tests/test_bilan_ortho_fail_closed.py`
- `backend/tests/test_bilan_ortho_engine.py`
- `backend/tests/test_ortho_frontend_fail_closed_contract.py`
- frontend : `cephaloUtils.test.ts`, `orthoExpertSystem.test.ts`

### Dernier défaut CI corrigé

Run `34340987448` : `277 passed, 1 skipped`, puis échec unique sur un test historique exigeant encore `référence normative non validée`. Le test a été corrigé pour le contrat actuel : **mesure brute seulement, aucune sémantique normative injectée**.

### Registre normatif

`cephalo_normative_service.py` reste une infrastructure fail-closed/versionnée pour de futurs profils explicitement validés. Aucun profil legacy ne devient autoritatif parce qu'il a été migré.

## AUTRES LOTS SCIENTIFIC CORE ENCORE OUVERTS

- Prescription / medication safety : rebuild restant, notamment gate final save/print à prouver.
- `clinical_rules_engine.py` : règles médicales à reconstruire avec sources/version/applicabilité.
- `clinical_coherence.py` : actif runtime, à séparer/consolider.

La fermeture du lot ortho ne signifie donc pas certification scientifique globale.

## CLOSEOUT LOT ORTHO

Ordre : `code → tests → comportement observé → docs → CI → cohérence PR → ready → merge → post-merge`.

Conditions avant merge :
- aucun test scientifique rouge ;
- aucune donnée patient synthétique active connue ;
- aucune règle thérapeutique autonome active connue ;
- aucune interprétation diagnostique autonome non validée connue ;
- docs cohérentes avec le HEAD ;
- tous les checks requis du même HEAD verts/acceptables.

## NEXT EXACT

Vérifier la CI du HEAD final créé avec la suppression `ai_advisor`. Si rouge : diagnostiquer et corriger. Si verte : vérifier tous les checks, mettre la PR en cohérence/ready, merger, puis vérifier le post-merge. Aucun déploiement Vercel.
