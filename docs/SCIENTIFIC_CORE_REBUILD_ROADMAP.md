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
3. une seule autorité normative céphalométrique ;
4. observation, interprétation, safety et décision praticien séparées ;
5. provenance/applicabilité explicites pour les règles scientifiques ;
6. tests négatifs/non-régression + CI verts avant merge ;
7. aucun déploiement Vercel sans autorisation explicite.

Règle dure : une couche clinique active `REPLACE` n'est jamais supprimée sans couverture/remplacement prouvé.

---

## 2. ÉTAT REPO À REVÉRIFIER À CHAQUE REPRISE

Repo : `hraaaaf/Digital_crown`  
Branche : `refactor/scientific-core-purge`  
PR : `#371` — draft, ouverte  
Base : `master`

Dernier HEAD observé avant ce commit documentaire : `519174fe11ca4c0f585befab840886cf2dee8eb6`.  
PR observée `mergeable=true` sur ce HEAD.  
CI du HEAD : run `34337218473` **pending** au dernier contrôle.  
Settings TemplateEngine Certification : **SUCCESS** sur le même cycle.  
Ne jamais qualifier la PR de globalement verte sans revérifier le HEAD documentaire créé par ce fichier et tous les checks requis.

---

## 3. ÉTAT GLOBAL

- **Phase 1 — Nettoyage scientifique : EN COURS.**
- Panorama/report : purge fermée et certifiée historiquement.
- Prescription démographique : fail-closed certifiée historiquement.
- Céphalométrie/orthodontie : sécurité runtime fortement durcie ; purge physique legacy et certification finale restantes.
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

Conserver géométrie, calibration, observations et données praticien ; supprimer toute conversion automatique `mesure → diagnostic/indication/traitement` non validée.

### Runtime actuel vérifié

- `CephaloService` utilise `cephalo_safe_engine`, pas `cephalo_engine` directement.
- `backend/tests/test_cephalo_engine_reachability.py` interdit tout import runtime direct du moteur legacy hors adapter.
- `cephalo_safe_engine` retire :
  - stratégie thérapeutique legacy ;
  - statuts/interprétations/z-scores normatifs legacy ;
  - projections T1/T2 de croissance legacy.
- `MeasureData.norm_mean/norm_min/norm_max/z_score` acceptent désormais `None` pour représenter explicitement l'absence d'autorité normative ; `0.0` n'est plus utilisé comme fausse norme fail-closed.
- `cephalo_consistency_validator.py` est réduit à des contrôles structurels : cohérence SNA-SNB≈ANB, unités, calibration. Les normes cliniques locales et Classe II/III via ANB ont été retirées du gate PDF.
- `CephaloService._calculate_complex_ddm()` ne convertit plus IMPA en espace ; DDM clinique explicite conservée.
- plan praticien conservé ; stratégie générée par le moteur filtrée.

### Frontend actuel vérifié

- `Step3Clinical.tsx` : plus de bouton injectant un traitement auto, plus de sévérité DDM/division diagnostique déduites localement ; stratégie praticien reste éditable.
- `Step4Documents.tsx` : mesures brutes, aucune table normative locale, aucun Damon par défaut, aucun appareil stocké dans `profil`.
- `orthoExpertSystem.ts` : adapter descriptif fail-closed ; plus d'extraction, appareil, mécanique, imagerie ou chirurgie automatiques.
- `cephaloUtils.ts` :
  - CVM âge/sexe neutralisé ;
  - IMPA/I-Francfort → DDM neutralisé ;
  - apex manquants non fabriqués ;
  - `generateTreatmentPlan()` ne génère aucun plan ;
  - donnée DDM absente reste absente.
- `useOrthoStore.ts` : defaults Classe I / denture permanente / Damon retirés. Dette restante : `sexePatient='M'` legacy par défaut, actuellement isolé du pipeline scientifique audité mais à remplacer par un état inconnu.

### Registre normatif

`cephalo_normative_service.py` reste l'autorité cible : fail-closed, profils legacy non validés non autoritatifs, pas de fallback silencieux.

Aucun profil legacy ne doit être marqué validé uniquement parce qu'il a été migré.

### Legacy encore physiquement présent

`backend/services/cephalo_engine.py` contient encore :
- `_evaluate_metric()` avec constantes historiques ;
- `calculate_ddm_reelle()` avec règle IMPA / 2,5° par mm ;
- vecteurs fixes `_project_t1_growth/_project_t2_growth` ;
- stratégie nommant Damon, Invisalign, Twin Block, TADs, chirurgie, etc.

**État : QUARANTINÉ, PAS VALIDÉ.** La frontière runtime empêche ces sorties de devenir autoritatives, mais la purge physique reste souhaitable après preuve de couverture suffisante.

### Base scientifique documentée

Voir `docs/ORTHO_SCIENTIFIC_CORE_AUDIT.md`.

Conclusions d'ingénierie déjà verrouillées :
- CVM = appréciation morphologique, jamais âge/sexe seuls ;
- extraction = décision multifactorielle ;
- CBCT = justification individualisée ;
- normes céphalo = applicabilité population/méthode explicite ;
- prédiction individuelle de croissance : méthodes actuelles hétérogènes, validation externe limitée ; vecteurs fixes T1/T2 legacy non autoritatifs.

### Tests clés

- `backend/tests/test_cephalo_treatment_boundary.py`
- `backend/tests/test_cephalo_engine_reachability.py`
- `backend/tests/test_cephalo_consistency_structural_only.py`
- tests frontend `cephaloUtils.test.ts`, `orthoExpertSystem.test.ts`
- contrats statiques frontend de sécurité du lot

### Remaining exact

1. CI du HEAD courant : corriger toute régression attribuable au lot.
2. Remplacer le default UI `sexePatient='M'` par inconnu, avec consommateurs typés.
3. Purger physiquement les branches normatives/croissance/traitement du `CephaloEngine` legacy après preuve branch-wide de non-dépendance.
4. Prouver/supprimer les wrappers/imports legacy restants (`ai_advisor`, helpers privés) sans perte de couverture.
5. Vérifier que l'UI ne consomme que mesures brutes + métadonnées normatives validées.
6. Refaire CI + certifications scientifiques.

---

# CLOSEOUT

Ordre obligatoire :

`code → tests → comportement observé → docs → CI → cohérence PR → merge → CI post-merge`

Conditions avant merge :
- aucun test scientifique rouge ;
- aucune règle thérapeutique autonome active connue ;
- aucune donnée patient synthétique active connue ;
- docs cohérentes avec le HEAD ;
- PR non draft uniquement quand les critères sont prouvés.

**Pas de déploiement Vercel sans autorisation explicite.**

---

## NEXT EXACT

Vérifier la CI du HEAD créé par ce commit documentaire. Si rouge : diagnostiquer/corriger. Si verte : corriger `sexePatient` puis poursuivre la purge physique contrôlée de `CephaloEngine` et refaire la certification.
