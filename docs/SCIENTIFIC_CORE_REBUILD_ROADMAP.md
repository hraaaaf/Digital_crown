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
PR : `#371` — draft, ouverte, `mergeable=true` au dernier contrôle  
Base : `master`

Dernier HEAD observé avant ce commit documentaire : `61bf1bd918d4483d5053276103da101faa5fbfd5`.  
CI de ce HEAD : run `34340916184` **pending** au dernier contrôle.  
Les autres certifications du même HEAD étaient encore pending/in_progress/queued.  
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
- `backend/tests/test_cephalo_engine_reachability.py` interdit tout import runtime direct du moteur legacy hors adapter.
- `cephalo_safe_engine` retire stratégie thérapeutique, métadonnées normatives legacy et T1/T2.
- `cephalo_consistency_validator.py` ne garde que cohérence structurelle, unités et calibration ; aucun seuil clinique local.
- `CephaloService._calculate_complex_ddm()` ne convertit plus IMPA en espace ; DDM clinique explicite conservée.
- contenu praticien explicite conservé.

### Frontend vérifié

- `Step3Clinical.tsx` : aucune génération thérapeutique automatique.
- `Step4Documents.tsx` : aucune table normative locale ni Damon par défaut.
- `orthoExpertSystem.ts` : fail-closed ; aucune extraction/appareil/mécanique/imagerie/chirurgie autonome.
- `cephaloUtils.ts` : CVM âge/sexe, correction DDM par IMPA, apex synthétiques et génération de traitement neutralisés.
- `useOrthoStore.ts` : `sexePatient` est désormais `'M' | 'F' | null`, initialisé/reset à `null`; seules les valeurs sauvegardées exactement `M`/`F` sont restaurées. Le faux défaut masculin et la fuite inter-patient sont supprimés.

### Purge physique appliquée

`backend/services/cephalo_engine.py` a été réécrit en moteur **géométrie seule** :
- imports/services normatifs supprimés ;
- constantes/bornes normatives locales supprimées ;
- z-scores et classifications supprimés ;
- règle DDM `IMPA / 2,5° par mm` supprimée ;
- projections de croissance T1/T2 supprimées, sorties contractuelles vides ;
- stratégie thérapeutique et narration diagnostique supprimées ;
- âge/sexe/CVM restent acceptés uniquement pour compatibilité API et ne pilotent aucune inférence ;
- métadonnées normatives = `None`, `status='N/A'` ;
- mesures géométriques brutes conservées.

`backend/services/bilan_ortho_engine.py` a également été durci après audit croisé :
- suppression des classifications Classe I/II/III, typologies Tweed et labels IMPA automatiques ;
- suppression de la graduation automatique de sévérité DDM ;
- uniquement reformulation de valeurs brutes et données praticien ;
- aucune synthèse diagnostique autonome ;
- plan praticien conservé, sinon message fail-closed.

### Tests ajoutés / adaptés

- `backend/tests/test_cephalo_geometry_only.py` : normes nulles, T1/T2 vides, traitement absent, cohorte non inférée, mesures brutes conservées.
- `backend/tests/test_bilan_ortho_fail_closed.py` : aucune Classe II/III, typologie, sévérité ou pro/rétroalvéolie déduite ; plan praticien seul.
- `backend/tests/test_bilan_ortho_pdf.py` : validateur aligné sur contrat structurel-only, sans pseudo-borne SNA.
- tests historiques clés : `test_cephalo_treatment_boundary.py`, `test_cephalo_engine_reachability.py`, `test_cephalo_consistency_structural_only.py`, tests frontend `cephaloUtils.test.ts`, `orthoExpertSystem.test.ts`.

### Registre normatif

`cephalo_normative_service.py` peut rester comme infrastructure versionnée/fail-closed pour de futurs profils explicitement validés, mais le moteur géométrique et le bilan fail-closed ne l'utilisent plus pour produire une interprétation autonome.

Aucun profil legacy ne doit être marqué validé uniquement parce qu'il a été migré.

### Remaining exact

1. obtenir la CI du HEAD courant et corriger toute régression attribuable au lot ;
2. audit branch-wide des wrappers/imports céphalo legacy restants, notamment `ai_advisor`, puis supprimer ceux prouvés non nécessaires ;
3. vérifier les consommateurs UI/API sur les nouveaux champs fail-closed ;
4. refaire CI + certifications scientifiques ;
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

Auditer branch-wide les wrappers/imports céphalo legacy restants pendant la CI. Si la CI est rouge, corriger la régression ; si elle est verte, terminer la certification du lot puis closeout PR.