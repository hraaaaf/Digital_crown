# DIGITAL CROWN — SCIENTIFIC CORE REBUILD — CANONICAL HANDOVER

**Rôle :** fichier canonique de reprise du chantier Scientific Core.  
**Règle de reprise :** vérifier `repo / branche / PR / HEAD / CI` avant toute modification. Les SHA/runs ci-dessous sont des preuves historiques, jamais l'état courant par défaut.

---

## 1. GOAL FINAL

Reconstruire le noyau scientifique de Digital Crown pour qu'il soit minimal, explicable, sourcé/versionné, patient-specific et **fail-closed** quand une donnée indispensable manque.

Invariant clinique :

`measurement != diagnosis != indication != treatment`

### Succès observable

1. aucune valeur patient synthétique susceptible de modifier une décision clinique ;
2. aucune règle thérapeutique automatique non validée ;
3. aucune interprétation diagnostique autonome non validée ;
4. observation, interprétation, safety et décision praticien séparées ;
5. provenance/applicabilité explicites pour les règles scientifiques conservées ;
6. tests négatifs/non-régression + CI verts avant merge ;
7. aucun déploiement Vercel sans autorisation explicite.

Règle dure : une couche clinique active `REPLACE` n'est jamais supprimée sans couverture/remplacement prouvé.

---

## 2. ÉTAT REPO À REVÉRIFIER À CHAQUE REPRISE

Repo : `hraaaaf/Digital_crown`  
Branche : `refactor/scientific-core-purge`  
PR : `#371` — draft, ouverte, mergeable au dernier contrôle  
Base : `master`

Dernier HEAD code observé avant ce commit documentaire : `951d13fcbd4c336a3a5741d220eb0dc62c6b7576`.
Le commit documentaire créé après ce fichier devient le HEAD à revérifier.

Ne jamais qualifier la PR de globalement verte sans revérifier le HEAD courant et tous les checks requis.

---

## 3. ÉTAT GLOBAL

- **Phase 1 — Nettoyage scientifique : EN COURS.**
- Panorama/report : purge fermée et certifiée historiquement.
- Prescription démographique : fail-closed certifiée historiquement.
- Céphalométrie/orthodontie : purge runtime + purge physique principale appliquées ; certification CI finale restante.
- Consolidation globale : non fermée.
- Certification scientifique globale : non fermée.

Aucun pourcentage global n'est déclaré tant qu'il n'est pas recalculé sur des critères vérifiés.

---

# PHASE 1 — LOTS

## LOT 1 — TreatmentPlanEngine

**État : SUPPRIMÉ / CERTIFIÉ HISTORIQUEMENT.**

Moteur dormant supprimé, imports/tests dédiés retirés, contrat anti-régression ajouté.

---

## LOT 2 — Prescription / Medication Safety Legacy

**État : NETTOYAGE PARTIEL CERTIFIÉ ; REBUILD RESTANT.**

Déjà corrigé :
- allergie générique ≠ pénicilline automatique ;
- rappel détartrage retiré du medication-safety ;
- heuristique `antibiotique sans acte invasif => incohérent` neutralisée sur chemin moderne ;
- alertes spécifiques utiles conservées.

Gap restant : safety pending/error/unverified n'est pas encore prouvé comme gate final save/print de bout en bout.

Classification : `REPLACE / CONSOLIDATE`.

---

## LOT 3 — clinical_rules_engine.py

**État : ACTIF RUNTIME ; démographie fail-closed certifiée ; moteur global `REPLACE / CONSOLIDATE`.**

Politique déjà appliquée :
- aucun `age=30` ou `poids=70` inventé ;
- enfant sans poids => aucune dose pédiatrique calculée ;
- enfant avec poids explicite => poids réel utilisé ;
- adulte sans poids => uniquement chemins ne nécessitant pas le poids.

Règles médicales restantes à reconstruire avec sources/version/applicabilité : prophylaxie, grossesse/AINS, probiotiques, implants, mappings mot-clé → médicament, etc.

---

## LOT 4 — clinical_coherence.py

**État : ACTIF RUNTIME ; `REPLACE / CONSOLIDATE`.**

Reachability historiquement verrouillée vers `backend/routers/documents.py` et `backend/services/elite_manager.py`.

Cible : séparer validation documentaire, comptabilité et medication safety.

---

## LOT 5 — Imagerie panoramique

**État : PURGE FERMÉE / CERTIFIÉE HISTORIQUEMENT.**

Pipeline conservé : `ia.py → panoramic_service → sota_panoramic_service → panoramic_report_engine`.

Wrappers morts supprimés : `panoramic_ai_advisor.py`, `panoramic_expert_engine.py`, `panoramic_vision_service.py`.

---

## LOT 6 — Vision / Report panoramique

**État : FAIL-CLOSED IMPLÉMENTÉ / CERTIFIÉ HISTORIQUEMENT.**

- absence/non-saisie => `non documenté / non évalué` ;
- aucune conduite thérapeutique/CCAM déduite automatiquement d'un label d'imagerie ;
- décision praticien conservée.

---

## LOT 7 — Céphalométrie / Orthodontie

### Goal

Conserver géométrie, calibration, observations et données praticien ; supprimer toute conversion automatique `mesure → diagnostic/indication/traitement` non validée et toute donnée patient inventée.

### Runtime vérifié

- `CephaloService` utilise `cephalo_safe_engine`, pas `cephalo_engine` directement.
- `backend/tests/test_cephalo_engine_reachability.py` interdit tout import runtime direct du moteur hors adapter.
- `cephalo_safe_engine` reste une défense en profondeur contre traitement, métadonnées normatives legacy et T1/T2.
- `cephalo_consistency_validator.py` ne garde que cohérence structurelle, unités et calibration ; aucun seuil clinique local.
- `CephaloService._calculate_complex_ddm()` ne convertit plus IMPA en espace ; DDM clinique explicite conservée.
- contenu praticien explicite conservé.

### Frontend vérifié

- `Step3Clinical.tsx` : aucune génération thérapeutique automatique.
- `Step4Documents.tsx` : aucune table normative locale ni Damon par défaut.
- `orthoExpertSystem.ts` : fail-closed ; aucune extraction/appareil/mécanique/imagerie/chirurgie autonome.
- `cephaloUtils.ts` : CVM âge/sexe, correction DDM par IMPA, apex synthétiques et génération de traitement neutralisés.
- `useOrthoStore.ts` : `sexePatient` est `'M' | 'F' | null`, initialisé/reset à `null`; seules les valeurs sauvegardées exactement `M/F` sont restaurées. Le faux défaut masculin et la fuite inter-patient sont supprimés.
- `backend/tests/test_ortho_frontend_fail_closed_contract.py` verrouille désormais explicitement ce contrat nullable/reset et interdit les fallbacks `'M'`.

### Purge physique appliquée

`backend/services/cephalo_engine.py` est un moteur **géométrie seule** :
- imports/services normatifs supprimés ;
- constantes/bornes normatives locales supprimées ;
- z-scores et classifications supprimés ;
- règle DDM `IMPA / 2,5° par mm` supprimée ;
- projections de croissance T1/T2 supprimées, sorties contractuelles vides ;
- stratégie thérapeutique et narration diagnostique supprimées ;
- âge/sexe/CVM restent acceptés uniquement pour compatibilité API et ne pilotent aucune inférence ;
- métadonnées normatives = `None`, `status='N/A'` ;
- mesures géométriques brutes conservées.

`backend/services/bilan_ortho_engine.py` est fail-closed :
- aucune classification Classe I/II/III ;
- aucune typologie Tweed ;
- aucun label IMPA automatique ;
- aucune graduation automatique de sévérité DDM ;
- uniquement reformulation de valeurs brutes et données praticien ;
- aucune synthèse diagnostique autonome ;
- plan praticien conservé, sinon message fail-closed.

### Tests clés

- `backend/tests/test_cephalo_geometry_only.py`
- `backend/tests/test_cephalo_treatment_boundary.py`
- `backend/tests/test_cephalo_engine_reachability.py`
- `backend/tests/test_cephalo_consistency_structural_only.py`
- `backend/tests/test_bilan_ortho_fail_closed.py`
- `backend/tests/test_bilan_ortho_engine.py` aligné sur le contrat raw-measurement-only
- `backend/tests/test_ortho_frontend_fail_closed_contract.py` avec garde sexe nullable/reset
- tests frontend `cephaloUtils.test.ts`, `orthoExpertSystem.test.ts`.

### Dernier défaut CI corrigé

Run `34340987448` : backend a atteint `277 passed, 1 skipped` puis a échoué sur un test historique exigeant encore la phrase `référence normative non validée` dans le bilan. Le moteur ne doit plus injecter de sémantique normative du tout ; le test a donc été corrigé pour exiger **mesure brute seulement** et absence du terme `normative`.

### Reachability `ai_advisor`

Audit PR-wide :
- `cephalo_service.py` n'importe plus `ai_advisor` ;
- le wrapper lui-même est fail-closed ;
- ses tests de compatibilité restent ;
- un import runtime mort demeure dans `elite_manager.py`.

Ne pas supprimer physiquement `ai_advisor.py` avant suppression sûre de cet import.

### Registre normatif

`cephalo_normative_service.py` reste une infrastructure versionnée/fail-closed pour de futurs profils explicitement validés. Le moteur géométrique et le bilan fail-closed ne l'utilisent plus pour produire une interprétation autonome.

Aucun profil legacy ne doit être marqué validé uniquement parce qu'il a été migré.

### Remaining exact

1. obtenir la CI du HEAD documentaire final et corriger toute régression attribuable au lot ;
2. supprimer l'import mort `elite_manager → ai_advisor` quand une modification sûre du fichier est possible ;
3. si plus aucun consommateur runtime, décider suppression du wrapper + tests de compatibilité ;
4. vérifier tous les checks requis sur le même HEAD ;
5. cohérence PR/docs ;
6. sortir du draft et merger uniquement après preuves vertes ;
7. vérifier le post-merge.

---

# CLOSEOUT

Ordre obligatoire :

`code → tests → comportement observé → docs → CI → cohérence PR → merge → CI post-merge`

Conditions avant merge :
- aucun test scientifique rouge ;
- aucune règle thérapeutique autonome active connue ;
- aucune interprétation diagnostique autonome non validée connue ;
- aucune donnée patient synthétique active connue ;
- docs cohérentes avec le HEAD ;
- PR non draft uniquement quand les critères sont prouvés.

**Pas de déploiement Vercel sans autorisation explicite.**

---

## NEXT EXACT

Vérifier la CI du HEAD créé par ce commit documentaire. Si rouge : diagnostiquer/corriger. Si verte : terminer l'audit `ai_advisor`, vérifier tous les checks requis, mettre la PR en état de closeout et ne merger qu'après preuve complète.
