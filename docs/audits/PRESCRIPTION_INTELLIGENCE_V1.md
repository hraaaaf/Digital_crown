# Prescription Intelligence V1 — Canonical

Date : 2026-09-14

## Statut

**CLOS — A+B et C1 certifiés et mergés sur `master`. Correction UX praticien #497 mergée. Toute suggestion clinique C reste volontairement fail-closed.**

Ce fichier est le point de reprise canonique du chantier « Prescription Intelligence V1 ».

## Goal

Flux cible :

`recherche médicament → présentation documentaire explicite → contexte clinique structuré → suggestion clinique seulement si règle certifiée + contexte suffisant → calcul traçable → validation praticien`.

À l’issue de C1, seules les trois premières briques sont implémentées. Aucune règle de dose n’est activée.

## A — Recherche médicament

- autocomplete uniquement via `/medications/search` ;
- recherche nom commercial / DCI ;
- snapshot CNOPS avec provenance explicite ;
- aucune habitude/preset/smart-suggest legacy dans le flux actif ;
- panne référentiel = aucune suggestion inventée.

## B — Présentation explicite

- ID stable `cnops:<sha256>` par présentation ;
- sélection explicite renseigne nom, dosage documentaire, forme documentaire et provenance ;
- `posologie` remise à vide après sélection ;
- modifier le nom invalide identité documentaire + dosage + forme + posologie ;
- aucun fallback silencieux `Comprimés` / `Sachets` ;
- aucune voie d’administration inférée.

## C1 — Contexte clinique structuré

Persisté dans `patient_clinical_contexts` :

- `weight_kg` ;
- `medication_allergy_status` + `medication_allergies` ;
- `renal_context_status` + `renal_context_note` ;
- `hepatic_context_status` + `hepatic_context_note` ;
- provenance minimale `updated_at` / `updated_by_user_id`.

Invariants :

- poids fini strictement positif ou inconnu ;
- allergie `PRESENT` exige au moins une allergie explicite ;
- aucune liste d’allergies sous `UNKNOWN` ;
- note rénale/hépatique seulement avec `IMPAIRMENT_REPORTED` ;
- erreur de chargement UI = aucune valeur supposée + sauvegarde bloquée ;
- sauvegarde manuelle uniquement ;
- aucun `clinical_ready` ;
- aucune formule, aucun seuil médical, aucun calcul de dose.

### Ownership indication

L’indication appartient à **l’ordonnance**, pas au patient :

- absente du modèle/table/API patient C1 ;
- `prescription_indication` rejeté par l’API `clinical-context` ;
- stockée dans `clinical_data` de l’ordonnance ;
- réhydratée en édition ;
- injectée uniquement dans le payload `type=ordonnance` ;
- jamais injectée dans certificat/devis/etc. ;
- non interprétée cliniquement et non imprimée dans C1.

## Frontière clinique

**Suggestion clinique : NON IMPLÉMENTÉE / BLOQUÉE PAR CONCEPTION.**

Le statut fail-closed reste **interne** :

- `data-clinical-rule-status="blocked"` ;
- `data-safety-status="blocked"` ;
- aucun appel actif à `/prescriptions/smart-suggest/{patient_id}` ;
- aucun appel actif à `/prescriptions/safety/check`.

Important UX : les libellés techniques `Suggestion clinique bloquée`, `Contrôle clinique automatique bloqué`, `legacy` et `V1 certifiée` ne sont plus affichés au praticien.

L’UI praticien affiche uniquement une copie métier :
- `Prescription` ;
- `Recherche médicament → présentation → validation` ;
- `Contexte patient` ;
- poids, allergies, contexte rénal/hépatique et indication de l’ordonnance.

C1 ne prouve pas l’exactitude clinique des données saisies et ne suffit pas à autoriser une règle de dose. Toute règle future doit être certifiée séparément avec paramètres complets, sources concordantes/versionnées et tests positifs/négatifs.

## Provenance catalogue

Source documentaire : `CNOPS Open Data — Référentiel des médicaments`.

- producteur : CNOPS ;
- licence : ODbL ;
- dernière modification publique observée : `2021-12-13 16:26 UTC` ;
- usage : snapshot documentaire historique d’identité/présentation ;
- `current_marketing_status_verified=false`.

Le snapshot 2021 ne constitue pas une preuve de commercialisation actuelle en 2026.

## Migration C1

Migration : `c1ctx0000001`, chaînée sur `f5a55e700005`.

Fichiers principaux :

- `backend/models_patient_clinical_context.py`
- `backend/schemas/patient_clinical_context.py`
- `backend/routers/patient_clinical_context.py`
- `backend/tests/test_patient_clinical_context_c1.py`
- `alembic/versions/c1ctx0000001_add_patient_clinical_context.py`
- `frontend/src/features/admin/DocumentStudio/Forms/PatientClinicalContextPanel.tsx`
- `frontend/src/features/admin/DocumentStudio/Forms/PrescriptionAgenticStudioV1.tsx`
- `frontend/src/features/admin/DocumentStudio/Forms/PrescriptionAgenticStudio.indication.test.tsx`
- `frontend/src/features/admin/DocumentStudio/PrescriptionIntelligenceV1.boundary.test.ts`

## UI/UX C1 — historique

Viewports : `390×844`, `430×932`, `768×1024`, `1280×900`.

### BEFORE C1

Référence A+B : Fidelity #70, run `34878423582`, artifact `10361827618`,
digest `sha256:606606845e996b9f794b7b3a03368f809c6e5c11f68c147b714c2958dd064f6a`.

### Premier AFTER rejeté

Fidelity #93 sur `f30292e8e4f802a489dbc5d8c9391c99a95470f4` : gate automatique vert, rejet humain car contexte clinique développé par défaut et médicament repoussé.

### AFTER C1 certifié avant correction UX praticien

HEAD : `d943a49da1362028e4b02158193b0e82842faf02`.

Fidelity #98 / run `34892570623` : **SUCCESS**.
Artifact `10367746003`.
Digest `sha256:a0686c574578695038ac5b97762e619a9eb9e2244f707a2349237b92fc3ee54e`.

Score visuel conservateur : **9.0/10**.

## Correction UX praticien #497 — BEFORE → AFTER

### Goal

Retirer de l’interface dentiste les statuts techniques internes sans modifier la logique fail-closed ni l’existant DB/patients/documents.

### BEFORE

Le praticien voyait notamment :

- `Suggestion clinique bloquée` ;
- `Contrôle clinique automatique bloqué` ;
- du vocabulaire interne autour de certification/legacy ;
- `Contexte clinique structuré` accompagné de la mention qu’aucun calcul de dose n’était activé.

### AFTER final exact-head

PR head certifié : `352f914735da4c0981d1bdbc9e5619b5d5de7879`.

Fidelity #103 / run `34903537345` : **SUCCESS**.
Artifact : `10371681258`.
Digest : `sha256:4db6404230db025a8b14a5e7ab1d6e6f27ff277cf3cbda44452d9003046a5153`.

Résultats :

- 4/4 viewports PASS ;
- touch target minimum `44 px` ;
- aucun overflow horizontal ;
- `pageErrors=[]` sur les 4 viewports ;
- carte médicament + `Ajouter une ligne` visibles ensemble dans la scène planning ;
- contexte patient replié par défaut ;
- scène contexte dépliée : 4 groupes structurés visibles ;
- preview desktop : `280 px`, largeur éditeur visible `501.6875 px`.

Hauteur planning :

| Viewport | BEFORE correction | AFTER correction | Réduction |
| --- | ---: | ---: | ---: |
| 390×844 | 1054.875 px | 781 px | -26.0 % |
| 430×932 | 975.75 px | 766 px | -21.5 % |
| 768×1024 | 749.75 px | 617.5 px | -17.6 % |
| 1280×900 | 681.75 px | 590.5 px | -13.4 % |

Inspection humaine des mêmes 4 viewports : hiérarchie métier nette, aucun bandeau technique résiduel observé, `Contexte patient` lisible et secondaire après médicament/ajout de ligne.

Score visuel conservateur après correction : **9.4/10**.

## Preuves exact-head #497 avant merge

HEAD : `352f914735da4c0981d1bdbc9e5619b5d5de7879`.

- CI #4159 / run `34903537431` : **SUCCESS** ;
- frontend tests + build : **SUCCESS** ;
- backend full regression suite, DB / patients / documents inclus : **SUCCESS** ;
- garde production négative : **SUCCESS** ;
- M4-A / M4-B / M4-C : **SUCCESS** ;
- Fidelity #103 : **SUCCESS** ;
- Patient P7 #1553 : **SUCCESS** ;
- T2 #3063 : **SUCCESS** ;
- PostgreSQL #578 : **SUCCESS** ;
- Settings #677 : **SUCCESS** ;
- M6-I #1863 : **SKIPPED attendu**.

## Merge #497 et post-merge

PR `#497 — fix(prescription): hide internal certification copy from practitioners` : **MERGED**.

Squash merge : `279a8b56c77dfca36a8e1316d1a5f87d6aa2308e`.

Post-merge CI #4170 / run `34905190921` sur `279a8b56c77dfca36a8e1316d1a5f87d6aa2308e` : **SUCCESS**.

Aucun déploiement Vercel demandé ni réalisé.

## Risques résiduels / lot suivant

1. Le snapshot CNOPS reste historique et ne doit pas être présenté comme preuve de disponibilité commerciale actuelle.
2. Les moteurs pharmacologiques legacy restent hors du chemin V1.
3. C1 fournit des faits structurés mais pas une validation médicale automatisée.
4. L’indication reste métadonnée de l’ordonnance en C1, non interprétée.
5. Toute règle C2 exige une certification scientifique indépendante avant activation.
6. Aclav reste un exemple UX uniquement tant que présentation exacte + règle clinique dédiée ne sont pas certifiées.

## Next exact

`C2 : sélectionner une seule règle clinique candidate, définir son contexte minimal exact, sourcer la règle avec ≥2 sources sérieuses concordantes, modéliser le contrat de calcul/versionnement, écrire les tests positifs/négatifs, puis seulement envisager son activation derrière un gate fail-closed.`
