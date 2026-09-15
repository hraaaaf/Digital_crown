# Digital Crown — Module Ortho V2

Statut : **CANONICAL FUTURE ROADMAP — PARKED BEHIND CEPHALO-N CLOSEOUT**

Date : 2026-09-15

## 0. PRIORITÉ ABSOLUE — CHANTIER ACTIF

**Le chantier actif reste Céphalo-N / tracé céphalométrique. Il n'est pas terminé.**

`ORTHO_MODULE_V2` est une roadmap préparée pour la suite. **Aucune implémentation Ortho V2 ne doit démarrer tant que le chantier Céphalo-N actuel n'a pas atteint son closeout vérifié.**

Cela signifie notamment que doivent être terminés/validés, selon le périmètre Céphalo-N déjà engagé :

1. cartographie canonique des mesures céphalométriques ;
2. profils d'analyses Steiner / Tweed / McNamara / Ricketts / COM ;
3. landmarks et constructions exactes nécessaires ;
4. calculs géométriques manquants autorisés ;
5. fixtures/tests/non-régression ;
6. tracé SVG synchronisé avec les mesures ;
7. normes/interprétations versionnées uniquement lorsqu'elles sont source-lockées ;
8. workflow de sélection d'analyse et états fail-closed ;
9. bilan céphalométrique/PDF du périmètre Céphalo-N ;
10. CI, docs canoniques, merge et post-merge du chantier Céphalo-N.

**Gate dur : `CEPHALO_N_CLOSEOUT_VERIFIED == true` avant `ORTHO_V2_D0`.**

Le futur agent doit donc commencer par vérifier l'état réel du chantier Céphalo-N. Si Céphalo-N n'est pas clos, il poursuit Céphalo-N et **ne démarre pas Ortho V2**.

---

# 1. Vision Ortho V2 — après Céphalo-N

Construire un **Diagnostic Builder ODF modulaire** : Digital Crown contient une bibliothèque complète de briques diagnostiques, mais le praticien choisit les modules/champs qu'il souhaite activer dans son protocole habituel et peut les adapter patient par patient.

Le système fusionnera de façon traçable les données :

- cliniques ;
- photographiques ;
- moulages / scan intra-oral ;
- radiographiques ;
- céphalométriques ;
- dentaires / dento-alvéolaires ;
- fonctionnelles ;
- tissus mous / esthétiques ;
- croissance / airway lorsque réellement évalués.

La sortie est une synthèse diagnostique dans les trois sens, soumise à validation explicite du praticien avant génération du bilan PDF.

## Succès observable Ortho V2

Le chantier Ortho V2 sera considéré abouti uniquement si :

1. toutes les possibilités ODF retenues sont cartographiées dans un registre de modules versionné ;
2. chaque module possède champs, dépendances, provenance, statut obligatoire/optionnel et règles fail-closed ;
3. le praticien peut enregistrer un profil ODF personnel ;
4. il peut l'adapter pour un patient sans modifier son profil par défaut ;
5. la céphalométrie réutilise le registre canonique final issu de Céphalo-N ;
6. la synthèse distingue sagittal/AP, vertical, transversal, dentaire/dento-alvéolaire, tissus mous, fonctionnel, croissance/airway ;
7. aucune conclusion n'est fabriquée depuis une donnée absente, un landmark non certifié ou une modalité inadéquate ;
8. chaque finding diagnostique cite ses preuves et divergences ;
9. le diagnostic final nécessite validation/modification praticien ;
10. le PDF final est dynamique et reflète uniquement les modules évalués/validés ;
11. DB, patients, documents et fonctionnalités existantes restent compatibles.

---

# 2. Architecture verrouillée

## 2.1 Céphalométrie : mesures d'abord, analyses ensuite

Architecture issue du chantier Céphalo-N :

```text
LANDMARKS / CONSTRUCTIONS
          ↓
CANONICAL MEASUREMENT REGISTRY
          ↓
ANALYSIS PROFILES
Steiner / Tweed / McNamara / Ricketts / COM / futures analyses
          ↓
NORMS / INTERPRETATION versionnées
```

Une analyse ne possède pas une copie de formule. Elle référence un `measurement_id` canonique.

Mesures partagées identifiées :
- SNA : Steiner + McNamara ;
- angle interincisif : Steiner + Ricketts + COM ;
- FH/Go-Me : Tweed DC + McNamara + COM si convention identique ;
- IMPA : Tweed DC + COM.

Faux équivalents interdits :
- `B→Nperp != Pog→Nperp` ;
- `U1/FH != FMIA` ;
- Ricketts Facial Angle `!=` profondeur faciale legacy COM ;
- `Pt_Ricketts != PTM_McNamara` ;
- `Gn_anatomic != Gn_constructed` ;
- `Pog_hard != Pog_soft` ;
- `Go-Me != Go-Gn != Sub.Go.-M` ;
- `L1 edge→A-Pog != L1 facial-surface→A-Pog`.

## 2.2 Une téléradiographie, un graphe patient, plusieurs analyses

Cible Céphalo-N :

```text
Téléradiographie
      ↓
Détection landmarks
      ↓
Validation / correction praticien
      ↓
LANDMARK GRAPH PATIENT UNIQUE
      ↓
Constructions et mesures canoniques
      ↓
Profil(s) d'analyse
      ↓
Normes / lecture versionnées
```

Changer d'analyse ne doit pas relancer inutilement le détecteur ni créer une deuxième instance de SNA/ANB/FMA/etc.

Landmark absent/non certifié → `NOT_COMPUTABLE` / `BLOCKED_*`, jamais approximation silencieuse.

## 2.3 Ortho V2 : diagnostic multimodal

La céphalométrie sera **une source parmi plusieurs**, pas le diagnostic ODF entier.

Le futur diagnostic peut intégrer : examen facial, intra-oral, moulages/scan, relations dentaires, DDM, panoramique, céphalométrie, fonctionnel, tissus mous, croissance/airway.

## 2.4 Modularité praticien

Deux niveaux :

1. **Profil praticien** : protocole ODF habituel enregistré.
2. **Override patient** : activation/désactivation ponctuelle sans modifier le défaut.

Exemple :

```text
Mon bilan ODF standard
[x] Examen facial
[x] Examen intra-oral
[x] Moulages / scan
[x] Classe molaire / canine
[x] DDM clinique
[x] Panoramique
[x] Céphalométrie McNamara
[x] Céphalométrie Steiner
[ ] Tweed
[ ] Ricketts PA
[ ] Bolton
[x] Synthèse diagnostique
[x] PDF
```

## 2.5 Diagnostic assisté, jamais autonome

Le moteur pourra calculer, comparer à une norme versionnée, structurer convergences/divergences et proposer une synthèse.

Il ne doit jamais :
- inventer une donnée ;
- substituer un landmark voisin ;
- fabriquer du transversal céphalométrique depuis un profil ;
- présenter un champ non évalué comme normal ;
- fabriquer un diagnostic final irrévocable ;
- choisir automatiquement un traitement.

Le praticien valide/modifie la conclusion finale.

---

# 3. Bibliothèque cible Ortho V2

## A. Examen facial

- type/proportions faciales ;
- symétrie ;
- tiers faciaux ;
- profil ;
- convexité clinique ;
- projection mentonnière clinique ;
- compétence labiale ;
- exposition incisive au repos ;
- ligne du sourire / sourire gingival ;
- corridors buccaux si retenus ;
- médianes faciales ;
- photos associées.

## B. Examen intra-oral

- phase dentaire / éruption ;
- dents absentes, incluses, ectopiques, surnuméraires si documentées ;
- rotations / versions ;
- médianes ;
- surplomb / recouvrement ;
- béance / supraclusion ;
- articulés croisés ;
- articulé en ciseaux ;
- déviation fonctionnelle si observée.

## C. Relations dentaires sagittales

Toujours séparer droite/gauche :
- Classe d'Angle molaire D/G ;
- classe canine D/G ;
- relation incisive si protocole retenu ;
- asymétrie sagittale dentaire.

## D. Moulages / scan intra-oral

- forme d'arcade maxillaire / mandibulaire ;
- symétrie ;
- largeur intercanine / intermolaire ;
- courbe de Spee ;
- rotations/positions ;
- encombrement / espaces ;
- relation transverse ;
- analyse dimensionnelle si données fiables.

## E. DDM / analyse d'espace

### DDM clinique
- maxillaire / mandibulaire ;
- encombrement ou espace ;
- sévérité ;
- localisation ;
- commentaire praticien.

### Analyse instrumentée
- espace disponible ;
- espace requis ;
- différence ;
- méthode/source ;
- fiabilité.

Ne jamais confondre estimation clinique et mesure instrumentée.

## F. Bolton optionnel

Seulement si les largeurs mésio-distales requises sont disponibles/fiables :
- Bolton antérieur ;
- Bolton total ;
- statut calculable/non calculable.

## G. Panoramique / statut dentaire

- présence/absence ;
- inclusions ;
- agénésies ;
- surnuméraires ;
- axes pertinents ;
- germes/stades si protocole validé ;
- anomalies radiographiques pertinentes.

## H. Céphalométrie

**Dépendance dure : Céphalo-N finalisé.**

Consomme uniquement les contrats finaux Céphalo-N : registre canonique, profils d'analyses, landmarks, constructions, mesures, normes, tracé et sorties validées.

## I. Fonctionnel

Modules séparables : respiration, déglutition, posture linguale, phonation, habitudes, mastication si retenue, ATM.

Toujours distinguer : observé / déclaré / non évalué.

## J. Tissus mous / esthétique

- profil tissus mous ;
- compétence labiale ;
- E-plane si disponible ;
- angle nasolabial si source-locké ;
- exposition incisive / sourire.

## K. Croissance / séries

- comparaison temporelle ;
- superpositions ;
- variations mesures ;
- dates ;
- méthode de superposition versionnée.

## L. Airway optionnel

Indicateurs uniquement avec landmarks/protocole source-lockés. Jamais assimilés à un diagnostic ORL.

## M. Synthèse diagnostique

### Sagittal/AP
maxillaire, mandibule, relation intermaxillaire, relation dentaire, convergences/divergences.

### Vertical
squelettique, dento-alvéolaire, clinique, occlusion verticale.

### Transversal
clinique, moulages/scan, PA si disponible, articulés croisés/asymétries.

**Absence de PA ≠ absence d'évaluation clinique transversale.** Mais aucune mesure céphalométrique frontale ne vient d'une téléradiographie de profil.

### Dentaire / dento-alvéolaire
classes molaire/canine, surplomb/recouvrement, axes incisifs, compensations, DDM, médianes.

### Tissus mous / fonctionnel / croissance-airway
uniquement si modules réellement évalués.

---

# 4. Modèle conceptuel futur

Noms définitifs à confirmer après audit repo :

```text
OrthoModuleDefinition
- module_id
- version
- domain
- label
- dependencies
- fields
- evidence_requirements
- availability_rule
- default_enabled

OrthoPractitionerProfile
- practitioner_id
- profile_id
- enabled_module_ids
- per_module_settings
- version

OrthoPatientAssessment
- patient_id
- assessment_id
- profile_snapshot
- patient_overrides
- module_results
- evidence_refs
- practitioner_validation
- status

OrthoDiagnosticFinding
- finding_id
- domain
- statement
- evidence_refs[]
- source_modules[]
- confidence/status
- practitioner_state

OrthoDiagnosticSynthesis
- sagittal
- vertical
- transverse
- dental
- soft_tissue
- functional
- growth_airway
- practitioner_conclusion
```

Principes : snapshot historique, réutilisation de Patient/DocumentArchive/imagerie/céphalo, aucune migration destructive, aucun second moteur/catalogue métier parallèle.

---

# 5. UX cible future

1. **Configuration protocole** : modules activables + profil par défaut.
2. **Bilan patient** : seulement modules actifs, statuts explicites.
3. **Synthèse** : résultats par domaine, preuves et divergences.
4. **Validation praticien** : accepter/modifier/compléter/exclure.
5. **PDF** : sections dynamiques selon modules réellement évalués/validés.

Tout changement UI/UX devra suivre : BEFORE → Goal → mockup/référence → implémentation → AFTER mêmes viewports → comparaison/tests → score visuel.

---

# 6. Roadmap

## PHASE ACTIVE AVANT ORTHO V2 — CEPHALO-N

**Goal** : terminer complètement le tracé céphalométrique engagé avant d'ouvrir Ortho V2.

**Succès** : closeout Céphalo-N réellement vérifié, docs canoniques cohérentes, tests/CI verts, merge/post-merge effectué.

**Preuve** : état Git/PR/CI + fichiers canoniques Céphalo-N + comportement observé.

## ORTHO-V2-D0 — Audit & registre des modules

**NE DÉMARRE QU'APRÈS LE GATE CEPHALO-N.**

Cartographie exhaustive :
`MODULE | SOUS-MODULE | CHAMP | TYPE | SOURCE DE DONNÉE | DÉPENDANCES | OBLIGATOIRE/OPTIONNEL | OUTPUT | PDF | ÉTAT DC | RISQUE DE DOUBLON`

Zéro nouvelle logique clinique avant validation D0.

## D1 — Contrats de données & profils praticien
Versionnement, profil praticien, snapshot patient, overrides, compatibilité.

## D2 — Intégration Céphalo canonique
Consommer **le Céphalo-N final**, sans duplication.

## D3 — Examen facial & intra-oral
Modules structurés activables.

## D4 — Moulages / scan & relations dentaires
Formes d'arcade, Angle molaire/canine D/G, DDM, occlusion, médianes, transversal dentaire, Bolton optionnel.

## D5 — Panoramique & statut dentaire
Réutiliser l'imagerie existante.

## D6 — Fonctionnel / tissus mous / airway
Modules optionnels et statuts observé/déclaré/non évalué.

## D7 — Synthèse diagnostique
Convergences/divergences, provenance par finding, jamais diagnostic final sans validation praticien.

## D8 — Diagnostic Builder UI
Gate visuel complet obligatoire.

## D9 — PDF ODF V2
Sections conditionnelles, sources, tracés/radios/photos, archivage documentaire existant.

## D10 — Validation clinique & non-régression
Cas synthétiques, anciens patients, profils minimal/complet, dépendances absentes, snapshots, PDF, CI, validation visuelle.

---

# 7. Gates scientifiques / techniques

## Scientifiques
- normes/version/population séparées de la géométrie ;
- landmarks exacts source-lockés ;
- profil ≠ PA ;
- clinique ≠ instrumenté ;
- observé ≠ déclaré ;
- aucune conclusion universelle depuis une seule mesure ;
- airway non diagnostique ORL ;
- traitement hors moteur diagnostique tant qu'un contrat distinct n'est pas validé.

## Techniques
- préserver DB/patients/documents/fonctionnalités ;
- réutiliser services/domaines existants ;
- aucun moteur/table bis sans nécessité prouvée ;
- schémas/migrations explicites ;
- snapshots/versionnement ;
- tests proportionnels ;
- aucun déploiement Vercel sans autorisation explicite.

---

# 8. État connu au 2026-09-15 — toujours revérifier

Repo : `hraaaaf/Digital_crown`

État de référence lors de cette correction :
- `master` observé : `09f247a64c6e024f15194177af03e5383e01d7f4` ;
- PR Céphalo fixtures #513 : ouverte au dernier contrôle, HEAD `c23816ad025840b30b897a461f34cf349fd34dd4`, CI/PG/T2 verts sur cet ancien HEAD ;
- PR registre canonique #515 : draft, branche `audit/cephalo-canonical-measurement-registry` ;
- **ces états sont temporaires : ne jamais les supposer actuels dans une nouvelle fenêtre.**

Règle de reprise : vérifier `master`, branche/HEAD, PR, divergence, CI et surtout **quel sous-lot Céphalo-N reste à terminer**.

---

# 9. Fichiers à lire avant toute reprise

## D'abord : chantier Céphalo-N actif

1. `docs/audits/CEPHALO_GLOBAL_ANALYSIS_VALIDATION.md`
2. `docs/audits/CEPHALO_GLOBAL_ANALYSIS_CARTOGRAPHY.md`
3. `docs/audits/CEPHALO_LANDMARKS_PLANES_SOURCE_LOCK.md`
4. `docs/audits/CEPHALO_PRIMARY_LANDMARK_CONSTRUCTIONS.md`
5. `docs/audits/CEPHALO_SRPOSE38_PROVENANCE.md`
6. `docs/audits/CEPHALO_GEOMETRIC_MEASUREMENT_CONTRACTS.md` / `CEPHALO_GEOMETRY_TEST_COVERAGE.md` si présents sur l'état repris
7. `docs/audits/CEPHALO_CANONICAL_MEASUREMENT_REGISTRY.md`
8. `docs/audits/CEPHALO_ANALYSIS_MEASUREMENT_PROFILES.md`

## Ensuite seulement : futur Ortho V2

9. `docs/audits/ORTHO_MODULE_V2.md`

---

# 10. PROMPT DE HANDOVER — PROCHAIN AGENT

```text
Tu reprends Digital Crown.

REPO
hraaaaf/Digital_crown

PRIORITÉ ABSOLUE
Le chantier actif est encore Céphalo-N / tracé céphalométrique. Il n'est PAS considéré terminé tant que son closeout vérifié n'est pas atteint.

ORTHO_MODULE_V2.md est une roadmap FUTURE. Ne démarre pas ORTHO-V2-D0 tant que Céphalo-N n'est pas réellement clos.

ÉTAPE 1 — REPRISE CÉPHALO-N
1. Vérifie master exact.
2. Vérifie les branches/PR céphalo ouvertes, leurs HEAD, divergence et CI.
3. Lis les fichiers canoniques Céphalo-N.
4. Identifie exactement : terminé / en cours / restant.
5. Poursuis le chemin critique Céphalo-N sans réinventer les lots déjà validés.
6. Termine les mesures/constructions/tracés SVG/normes/interprétations/PDF du périmètre déjà décidé selon les gates scientifiques existants.
7. Préserve DB, patients, documents et fonctionnalités validées.
8. Ferme Céphalo-N avec tests, CI, docs, merge et post-merge.

GATE
ORTHO_V2_D0 est interdit avant : CEPHALO_N_CLOSEOUT_VERIFIED.

ÉTAPE 2 — APRÈS CLOSEOUT CÉPHALO-N SEULEMENT
Lis docs/audits/ORTHO_MODULE_V2.md puis démarre ORTHO-V2-D0.

VISION ORTHO V2
Diagnostic Builder ODF modulaire : bibliothèque exhaustive de modules, profil praticien, overrides patient, preuves multimodales, synthèse sagittale/verticale/transversale, validation praticien, PDF dynamique.

MODULES FUTURS
- examen facial ;
- intra-oral ;
- moulages / scan ;
- Classe d'Angle molaire D/G ;
- classe canine D/G ;
- forme d'arcade ;
- DDM clinique / analyse d'espace ;
- occlusion / transversal dentaire ;
- Bolton optionnel ;
- panoramique ;
- céphalométrie FINALISÉE issue de Céphalo-N ;
- fonctionnel ;
- tissus mous ;
- croissance / airway si évalués ;
- synthèse ;
- validation ;
- PDF.

ARCHITECTURE VERROUILLÉE
- mesures céphalométriques canoniques d'abord, profils d'analyses ensuite ;
- une géométrie calculée une seule fois ;
- graphe de landmarks patient unique ;
- fail-closed si donnée/landmark/modalité absente ;
- diagnostic ODF multimodal ;
- diagnostic final validé par le praticien ;
- aucune régression DB/patient/document ;
- aucun déploiement Vercel sans autorisation.

FAUX ÉQUIVALENTS INTERDITS
B→Nperp != Pog→Nperp
U1/FH != FMIA
Ricketts Facial Angle != COM legacy facial depth
Pt_Ricketts != PTM_McNamara
Gn_anatomic != Gn_constructed
Pog_hard != Pog_soft
Go-Me != Go-Gn != Sub.Go.-M
L1 edge→A-Pog != L1 facial-surface→A-Pog

APRÈS LE GATE CEPHALO
ORTHO-V2-D0 = audit repo + matrice exhaustive :
MODULE | SOUS-MODULE | CHAMP | TYPE | SOURCE | DÉPENDANCES | OBLIGATOIRE/OPTIONNEL | OUTPUT | PDF | ÉTAT DC | RISQUE DE DOUBLON

RÈGLES D'EXÉCUTION
Goal = résultat exact ; Succès = observable ; Preuve = test/donnée/validation.
Ne jamais inventer résultat/action/validation/certitude.
Tâche complexe : découper → exécuter → vérifier → corriger → continuer.
UI : BEFORE → Goal → mockup/référence → implémentation → AFTER mêmes viewports → comparaison/tests → score visuel.
CI pending n'arrête pas le travail indépendant. Pas de polling/sleep.

COMMUNICATION
Résultat → preuve → prochaine action.
Termine chaque message de travail par les REPÈRES factuels.
```

---

# 11. Next exact ACTUEL

**Ne pas démarrer ORTHO-V2-D0.**

**Next exact = reprendre et terminer le chantier Céphalo-N / tracé céphalométrique au point exact où il se trouve après vérification Git/PR/CI.**

Après closeout Céphalo-N vérifié seulement : `ORTHO-V2-D0`.

---

# 12. Closeout futur Ortho V2

Chaque lot suivra :

```text
validation
→ tests / preuves
→ mise à jour ORTHO_MODULE_V2.md
→ cohérence roadmap
→ Git / PR / merge
→ post-merge
→ lot suivant
```

Ce fichier est le **fichier canonique de roadmap future Ortho V2**, mais **Céphalo-N reste le chantier actif tant que son closeout n'est pas prouvé**.
