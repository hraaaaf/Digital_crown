# Prescription Intelligence V1 — Canonical

Date : 2026-09-14

## Statut

**CLOS — A+B et C1 certifiés et mergés sur `master`. Toute suggestion clinique C reste volontairement bloquée (fail-closed).**

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
- `posologie` est remise à vide après sélection ;
- modifier le nom invalide identité documentaire + dosage + forme + posologie ;
- aucun fallback silencieux `Comprimés` / `Sachets` ;
- aucune voie d’administration inférée.

## C1 — Contexte clinique structuré

### Données patient durables

Persistées dans `patient_clinical_contexts` :

- `weight_kg` ;
- `medication_allergy_status` + `medication_allergies` ;
- `renal_context_status` + `renal_context_note` ;
- `hepatic_context_status` + `hepatic_context_note` ;
- provenance minimale `updated_at` / `updated_by_user_id`.

États explicites :

- allergies : `UNKNOWN`, `NONE_KNOWN`, `PRESENT` ;
- rein/foie : `UNKNOWN`, `NO_KNOWN_IMPAIRMENT`, `IMPAIRMENT_REPORTED`.

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
- `prescription_indication` est rejeté par l’API `clinical-context` ;
- stockée dans `clinical_data` de l’ordonnance ;
- réhydratée en édition de cette ordonnance ;
- injectée uniquement dans le payload `type=ordonnance` ;
- jamais injectée dans certificat/devis/etc. ;
- non interprétée cliniquement et non imprimée dans C1.

## Frontière clinique

**Suggestion clinique : NON IMPLÉMENTÉE / BLOQUÉE PAR CONCEPTION.**

L’UI affiche :

- `Suggestion clinique bloquée` ;
- `Contrôle clinique automatique bloqué`.

Le flux V1 actif n’appelle ni `/prescriptions/smart-suggest/{patient_id}` ni `/prescriptions/safety/check`.

C1 ne prouve pas l’exactitude clinique des données saisies et ne suffit pas à autoriser une règle de dose. Toute règle future devra être certifiée séparément avec paramètres complets, sources concordantes/versionnées et tests positifs/négatifs.

## Provenance catalogue

Source documentaire : `CNOPS Open Data — Référentiel des médicaments`.

- producteur : CNOPS ;
- licence : ODbL ;
- dernière modification publique observée : `2021-12-13 16:26 UTC` ;
- usage autorisé ici : snapshot documentaire historique d’identité/présentation ;
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

## UI/UX C1 — BEFORE → AFTER

Viewports : `390×844`, `430×932`, `768×1024`, `1280×900`.

### BEFORE C1

Référence A+B certifiée : Ordonnance Fidelity V3 #70, run `34878423582`, artifact `10361827618`, digest `sha256:606606845e996b9f794b7b3a03368f809c6e5c11f68c147b714c2958dd064f6a`.

Hauteur studio :

| Viewport | BEFORE |
| --- | ---: |
| 390×844 | 636.25 px |
| 430×932 | 590 px |
| 768×1024 | 447.25 px |
| 1280×900 | 406.25 px |

### Premier AFTER rejeté

Fidelity #93 sur `f30292e8e4f802a489dbc5d8c9391c99a95470f4` : gate automatique vert mais version refusée après inspection visuelle.

Motif : contexte clinique développé par défaut, studio fortement allongé et saisie médicament repoussée.

### AFTER C1 final certifié

HEAD PR certifié : `d943a49da1362028e4b02158193b0e82842faf02`.

Ordonnance Fidelity V3 Visual #98 : **SUCCESS** — run `34892570623`.

Artifact : `10367746003`.

Digest : `sha256:a0686c574578695038ac5b97762e619a9eb9e2244f707a2349237b92fc3ee54e`.

Résultats :

- 4/4 viewports PASS ;
- touch target minimum `44 px` ;
- aucun overflow horizontal ;
- carte médicament + action `Ajouter une ligne` visibles ensemble dans la scène planning ;
- contexte patient compact/replié par défaut ;
- scène C1 dépliée dédiée avec les 4 groupes structurés visibles ;
- preview desktop conservée.

Hauteur studio finale, contexte compact :

| Viewport | BEFORE | AFTER C1 | Écart |
| --- | ---: | ---: | ---: |
| 390×844 | 636.25 px | 1054.875 px | +65.8 % |
| 430×932 | 590 px | 975.75 px | +65.4 % |
| 768×1024 | 447.25 px | 749.75 px | +67.6 % |
| 1280×900 | 406.25 px | 681.75 px | +67.8 % |

La hausse d’empreinte verticale est acceptée en C1 car elle correspond à un nouveau contexte patient structuré + une indication document-scoped, tandis que l’action principale médicament reste prioritaire et visible en scène planning.

Score visuel conservateur C1 : **9.0/10**.

## Preuves exact-head C1 avant merge

HEAD : `d943a49da1362028e4b02158193b0e82842faf02`.

- CI #4129 / run `34892570531` : **SUCCESS** ;
- frontend tests + build : **SUCCESS** ;
- backend prod safety/config hardening : **SUCCESS** ;
- backend test suite : **SUCCESS** ;
- garde production négative : **SUCCESS** ;
- M4-A / M4-B / M4-C contextual bridges : **SUCCESS** ;
- Fidelity #98 / run `34892570623` : **SUCCESS**.

## Merge et post-merge

PR `#495 — feat(prescription): add structured patient context C1` : **MERGED**.

Squash merge : `3b22f2a0dbb5b778a53265b97ad3029eeb88e656`.

Parent master au merge : `9b1b354631d60faa462dc98c629c14bf38fe2ddf`.

Post-merge CI #4140 / run `34895686869` sur `3b22f2a0dbb5b778a53265b97ad3029eeb88e656` : **SUCCESS**.

- frontend tests : **SUCCESS** ;
- frontend build : **SUCCESS** ;
- backend prod safety/config hardening : **SUCCESS** ;
- backend test suite : **SUCCESS** ;
- garde production négative : **SUCCESS** ;
- M4 contextual bridges : **SKIPPED attendu** sur push.

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
