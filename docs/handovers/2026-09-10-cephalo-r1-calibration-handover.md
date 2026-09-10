# HANDOVER — Digital Crown Céphalométrie R1 Calibration

Date de gel : 2026-09-10

## Goal

Fermer **R1 — calibration céphalométrique assistée par fiducial** avec une chaîne de preuve exploitable cliniquement :

`détection image → candidat non vérifié → profil physique validé lié côté serveur → gate objectif → AUTO_VERIFIED → confirmation praticien optionnelle → CLINICIAN_CONFIRMED`

La calibration ne doit jamais inventer une échelle physique. Les mesures en millimètres restent `NOT_COMPUTABLE` tant qu’aucune calibration vérifiée n’existe.

## Succès observable

R1 n’est fermé que lorsque :

1. aucun fallback implicite `0.1 mm/px` ni distance physique supposée ne peut créer une calibration vérifiée ;
2. la détection produit d’abord un candidat géométrique non vérifié ;
3. `AUTO_VERIFIED` exige un profil physique versionné et validé ;
4. le client API ne peut pas choisir arbitrairement ce profil ;
5. l’identité/version/référence physique du profil sont déjà liées au candidat persisté côté serveur et correspondent au registre validé ;
6. provenance `AUTO_VERIFIED` et `CLINICIAN_CONFIRMED` restent distinctes ;
7. la confirmation praticien ne modifie ni le ratio ni les valeurs déjà calculées, seulement la provenance/audit ;
8. une transition de calibration reconstruit proprement les mesures dépendantes et bloque les états cliniques aval incompatibles ;
9. les sauvegardes ordinaires préservent candidat/décision/statut de calibration et ne deviennent jamais une transition de calibration implicite ;
10. l’UI expose les états de calibration avec possibilité de confirmer/modifier ;
11. cycle visuel complet : BEFORE réel → Goal → référence conforme tokens Digital Crown → implémentation → AFTER 390/768/1280+ → comparaison/tests → revue experte ;
12. CI exacte du HEAD final est verte avant merge.

## État Git vérifié au gel

- repo : `hraaaaf/Digital_crown`
- master : `5f453d906c0562e53c921c683bb16c1a6deb3536`
- branche : `feat/cephalo-auto-fiducial-calibration`
- PR : `#406` — `feat(cephalo): assisted fiducial calibration provenance`
- PR : **open**, **draft**, `mergeable=true`
- code HEAD vérifié avant commit de ce handover : `76520dfc950d18251b1238ce6fd0e32bd0ffb59d`
- dernier commit code : `fix(cephalo): preserve calibration invariants across saves`
- parent direct : `5a9d79ebdab5ecfb2f4db74a134cc52f5d29073b`
- PR au gel : 30 commits, 26 fichiers modifiés

## Preuves CI exactes sur le code HEAD `76520dfc…`

- CI `#3214` — **SUCCESS** — run `34538354526`
- T2 Runtime Browser Certification `#2221` — **SUCCESS** — run `34538354505`
- M6-I Biometric Passkey Certification `#1021` — **SKIPPED** — run `34538354518`

Important : T2 vert prouve le runtime couvert par ce workflow, **pas** une certification visuelle Céphalo. Le dernier artefact T2 inspecté avant ce gel contenait Document Studio et aucune capture Céphalo exploitable.

## Backend terminé et vérifié dans la PR

### 1. Candidat de calibration structuré

`backend/services/cephalo_calibration_candidate.py`

Le candidat contient uniquement la géométrie image : axe, ticks, espacement médian et méthode détecteur. Sa sérialisation garde :

- `status = CANDIDATE_UNVERIFIED`
- `mm_per_pixel = None`
- `distance_mm = None`
- `clinician_validated = False`

Aucune échelle physique n’est inventée au stade candidat.

### 2. Gate objectif d’auto-calibration

`backend/services/cephalo_auto_calibration_gate.py`

`AUTO_VERIFIED` n’est possible qu’avec :

- un `ValidatedFiducialProfile` explicite ;
- une distance physique connue/versionnée ;
- un nombre minimal de ticks ;
- une tolérance géométrique appartenant au profil ;
- un ratio dérivé déterministement et fini.

Sans profil validé : `CANDIDATE_UNVERIFIED`.

### 3. Registre physique fail-closed

`backend/services/cephalo_fiducial_profiles.py`

Le registre production est volontairement **vide par défaut**. Aucun fiducial n’est considéré fiable parce qu’il « ressemble » à une réglette.

### 4. Provenance typée AUTO_VERIFIED

`backend/services/cephalo_auto_calibration_evidence.py`

Seule une décision déjà `AUTO_VERIFIED` peut devenir `SourceEvidence` de calibration. Les contrôles recroisent : profil, référence de validation, géométrie, ratio, timestamp et absence de fausse confirmation praticien.

### 5. Transition de calibration auditée

`backend/services/cephalo_auto_calibration_transition.py`

La transition :

- exige le graphe typé ;
- vérifie patient/case/image/landmarks/constructions ;
- exige que le ratio runtime concorde exactement avec la décision ;
- remplace uniquement la provenance calibration et les mesures qui en dépendent ;
- conserve landmarks/constructions ;
- incrémente la révision ;
- bloque si des preuves cliniques aval existent déjà.

### 6. Confirmation praticien optionnelle

`backend/services/cephalo_auto_calibration_confirmation.py`

La confirmation transforme l’état d’audit en `CLINICIAN_CONFIRMED` sans changer le ratio ni les valeurs déjà calculées.

### 7. API sans sélection de profil par le client

`backend/routers/cephalo_auto_calibration.py`

Correctif critique du commit `5a9d79eb…` :

- `AutoCalibrationRequest` est un trigger vide avec `extra="forbid"` ;
- `profile_id/profile_version` ne viennent plus du caller ;
- `_bound_profile_from_analysis()` exige `profile_binding` déjà persisté dans le candidat ;
- `profile_id`, `profile_version` et `validation_reference` doivent correspondre au registre serveur ;
- sinon : HTTP 409 fail-closed.

Conséquence : un futur registre non vide ne permet pas au frontend de sélectionner arbitrairement un profil physique incompatible avec l’image.

### 8. Invariants de sauvegarde ordinaires

Commit `76520dfc…` : `fix(cephalo): preserve calibration invariants across saves`.

`backend/repositories/cephalo_repository.py` :

- création sans échelle `0.1 mm/px` par défaut ;
- sauvegarde ordinaire préserve `calibration_candidate` et `calibration_decision` ;
- un état spécifique `auto_verified` / `clinician_confirmed` n’est pas rétrogradé silencieusement en simple `verified`.

## Tests présents dans la PR

Couverture ciblée présente pour :

- candidat structuré ;
- détecteur sans distance physique inventée ;
- gate `AUTO_VERIFIED` / fail-closed ;
- registre fiducial ;
- SourceEvidence automatique ;
- transition et recalcul ;
- confirmation praticien ;
- routes API ;
- binding profil côté serveur ;
- runtime source calibration ;
- service initial avec candidat non vérifié ;
- persistance/sauvegarde des invariants calibration.

La CI exacte du code HEAD `76520dfc…` est verte.

## Invariants non négociables

- `landmark != construction != measurement != interpretation != diagnosis != indication != treatment plan`
- absence d’info = `UNKNOWN` / `NOT_COMPUTABLE`
- sans calibration vérifiée : angles possibles, millimètres indisponibles
- aucun `0.1 mm/px` fallback clinique
- aucun seuil clinique/norme/classe/croissance/indication inventé
- aucun diagnostic ou plan thérapeutique autonome
- **ZERO LLM** : ne réintroduire aucun runtime/config/dependency Ollama/Gemini/OpenAI/Anthropic
- local/on-premise ; pas de Vercel deploy sans autorisation explicite

## UI / UX — pas encore certifié

État : **OPEN**.

Le backend est mature, mais le cycle visuel obligatoire n’est pas encore fermé.

Contrat UI cible déjà verrouillé :

- `NON CALIBRÉ`
- `Réglette détectée — non validée` pour un candidat non vérifié
- `AUTO_VERIFIED` quand le profil physique + gate objectif passent
- `CLINICIAN_CONFIRMED` après confirmation humaine optionnelle
- actions cohérentes : confirmer / modifier calibrage / fallback manuel deux points
- aucune couleur ne doit suggérer un diagnostic clinique non validé
- utiliser les tokens réels de `frontend/src/features/ortho/cephaloTheme.ts`, pas une maquette générique inventée.

### BEFORE obligatoire

Aucune capture Céphalo réelle exploitable n’a encore été certifiée dans ce chantier.

Avant toute mutation visuelle : obtenir les BEFORE du vrai écran aux mêmes viewports qui serviront au AFTER :

- 390 px
- 768 px
- 1280 px ou plus

Puis seulement implémenter.

## Ce qui reste

1. obtenir les captures BEFORE réelles du studio Céphalo sans déploiement Vercel ;
2. relire l’état exact de `Step1Cephalo.tsx`, `useOrthoStore.ts`, `cephaloRepository.ts` et composants associés au HEAD courant ;
3. écrire le Goal visuel précis + référence/mockup mappée aux tokens existants ;
4. brancher l’UI sur les contrats backend R1 sans dupliquer la logique scientifique ;
5. vérifier flux : candidat → auto vérifié → confirmation optionnelle → modification/manuelle ;
6. AFTER 390/768/1280+ ;
7. comparaison BEFORE/AFTER + overflow/clipping + clavier/touch + lisibilité ;
8. tests frontend/backend proportionnels au risque ;
9. revue experte UX/UI + score visuel ;
10. mettre à jour `docs/CEPHALO_DIAGNOSTIC_SPEC.md` avec l’état réellement prouvé ;
11. vérifier PR/reviews/threads/mergeability + CI exacte du HEAD final ;
12. passer #406 ready, merge avec expected HEAD, vérifier master ;
13. ouvrir ensuite R2, pas avant.

## Next exact

**Obtenir les BEFORE Céphalo réels à 390 / 768 / 1280 sans déploiement, puis inspecter les composants frontend exacts du HEAD courant avant la première modification UI.**

Si aucun runtime Céphalo capturable n’est disponible localement ou via les outils existants, documenter ce blocage explicitement au lieu de fabriquer une preuve visuelle.

## Avis expert — revue spécialisée interne

Le R1 backend est désormais bien orienté : le point le plus dangereux n’était pas la détection elle-même mais la possibilité qu’une géométrie plausible soit associée à une mauvaise vérité physique. Le binding serveur du profil ferme ce vecteur. Le prochain risque principal est maintenant UX : rendre très distincts `détecté`, `vérifié automatiquement` et `confirmé humainement`, sans transformer un badge rassurant en raccourci scientifique trompeur.

## Fichier canonique du chantier

`docs/CEPHALO_DIAGNOSTIC_SPEC.md`

Ce handover est le fichier de reprise opérationnelle du R1. À la reprise : lire ce fichier, puis vérifier repo / master / PR #406 / HEAD / CI avant toute action.
