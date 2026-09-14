# Prescription Intelligence V1 — Canonical

Date : 2026-09-14

## Statut

**CLOS — A+B certifiés et mergés sur `master` ; lot C volontairement bloqué (fail-closed).**

Ce fichier est le point de reprise canonique du chantier « Prescription Intelligence V1 ».

## Goal

Permettre dans l’ordonnance un flux sécurisé :

`recherche médicament → sélection explicite d’une présentation documentaire → suggestion clinique uniquement si contexte + règle certifiée suffisants → calcul traçable → validation explicite du praticien`.

## Résultat A — Recherche médicament

- Autocomplete actif uniquement via `/medications/search`.
- Source : snapshot documentaire CNOPS exposé avec provenance explicite.
- Aucun fallback actif vers habitudes, presets ou smart-suggest legacy.
- Recherche par nom commercial ou DCI.
- Une panne du référentiel échoue fermée : aucune suggestion n’est inventée.

## Résultat B — Présentation explicite

- Chaque résultat correspond à une présentation documentaire identifiée par un ID stable `cnops:<sha256>`.
- La sélection explicite renseigne uniquement : nom, dosage documentaire, forme documentaire et provenance.
- La sélection remet toujours `posologie` à vide.
- Toute modification du nom après sélection invalide l’identité documentaire, le dosage, la forme et la posologie associés.
- Aucun fallback silencieux `Comprimés` ou `Sachets` n’existe pour une forme inconnue, une nouvelle ligne, une archive ou le payload final.
- Aucune voie d’administration n’est inférée depuis la forme.

## Résultat C — Suggestion clinique

**NON IMPLÉMENTÉE / BLOQUÉE PAR CONCEPTION.**

L’UI affiche explicitement `Suggestion clinique bloquée` et `Contrôle clinique automatique bloqué`.

Le flux V1 actif n’appelle pas `/prescriptions/smart-suggest/{patient_id}` ni `/prescriptions/safety/check` : ces mécanismes legacy contiennent des règles/mappings cliniques non certifiés selon le contrat V1.

Le modèle patient ne fournit pas encore de façon structurée tout le contexte requis pour généraliser des règles de dose sûres : poids, allergies structurées, fonction rénale/hépatique et indication clinique structurée. C ne pourra être activé qu’après ajout des données nécessaires et certification scientifique de chaque règle.

## Frontière clinique V1

Le chemin actif garantit :

- aucune dose calculée depuis mémoire ou hardcode ;
- aucune règle pharmacologique hardcodée dans le générateur actif ;
- aucun apprentissage silencieux dosage/posologie après archivage ;
- aucun quick preset/protocole legacy actif ;
- aucun choix automatique de forme si la source ne la fournit pas ;
- aucune revendication de sécurité clinique automatique tant que le moteur correspondant n’est pas certifié ;
- validation praticien obligatoire pour le texte persistant de l’ordonnance.

Les services/endpoints legacy peuvent encore exister dans le repo hors du chemin V1 ; leur existence n’est pas une certification et ils ne sont pas utilisés par ce flux.

## Provenance catalogue

Source documentaire : `CNOPS Open Data — Référentiel des médicaments`.

- producteur : CNOPS ;
- portail : Open Data Maroc ;
- licence : Open Data Commons Open Database License (ODbL) ;
- dernière modification publique observée du jeu : `2021-12-13 16:26 UTC` ;
- contenu déclaré : princeps/génériques, prix public, prix hôpital, base de remboursement.

Conclusion : cette source est exploitable comme **snapshot documentaire historique** d’identité/présentation. Elle ne prouve pas le statut de commercialisation actuel en 2026. Le contrat expose donc `current_marketing_status_verified=false`.

## Backend

Fichiers principaux :

- `backend/services/medication_dict.py`
- `backend/routers/medications.py`
- `backend/tests/test_prescription_intelligence_catalog.py`

Contrats testés : provenance, ID présentation stable/résoluble, présentation inconnue fail-closed, validation dosage limitée à la présence documentaire, aucune revendication de commercialisation actuelle.

## Frontend

Fichiers principaux :

- `frontend/src/features/admin/DocumentStudio/Forms/DrugRowV1.tsx`
- `frontend/src/features/admin/DocumentStudio/Forms/PrescriptionAgenticStudioV1.tsx`
- `frontend/src/features/admin/DocumentHub.tsx`
- `frontend/src/features/admin/DocumentStudio/DocumentHubContent.tsx`
- `frontend/src/features/admin/DocumentStudio/useDocumentGenerator.ts`
- `frontend/src/features/admin/DocumentStudio/PrescriptionIntelligenceV1.boundary.test.ts`

Garde-fous testés : catalogue uniquement, sélection explicite, aucune posologie injectée, invalidation des champs associés si le nom change, absence smart-suggest/safety-check legacy, absence de forme implicite, blocage clinique explicite.

## UI/UX — BEFORE → AFTER

Viewports obligatoires : `390×844`, `430×932`, `768×1024`, `1280×900`.

### BEFORE

Référence certifiée Ordonnance Fidelity V3.1 : artifact `10339208565`, digest `sha256:018e71b154551aadba5f90171b735770efde4b19cf03654cf64eaac4044e230d`.

### AFTER exact-head produit

HEAD certifié : `6e9129ebc03e1b73fac36dc2944149c194bcc023`.

Ordonnance Fidelity V3 Visual #70 : **SUCCESS** — run `34878423582`, artifact `10361827618`, digest `sha256:606606845e996b9f794b7b3a03368f809c6e5c11f68c147b714c2958dd064f6a`, 4/4 viewports, touch target minimum `44 px`, aucun overflow horizontal, aucune erreur page.

Ordonnance Composer Visual #34 : **SUCCESS** — run `34878423578`, artifact `10362195361`, digest `sha256:70cac3124ececb85c9554e34535bc211b9de1beb88ec5d0768de723126b0482e`.

### Comparaison

| Viewport | BEFORE | AFTER | Réduction |
| --- | ---: | ---: | ---: |
| 390×844 | 993 px | 636.25 px | 35.9 % |
| 430×932 | 966 px | 590 px | 38.9 % |
| 768×1024 | 939.25 px | 447.25 px | 52.4 % |
| 1280×900 | 889.25 px | 406.25 px | 54.3 % |

Score visuel conservateur : **9.3/10**. Réserve : sur 390/430 px, les deux messages fail-closed occupent encore une hauteur notable avant le premier champ médicament ; densité acceptée au bénéfice de la sécurité explicite.

## Repo / merge

Repo : `hraaaaf/Digital_crown`.

PR : `#487 — feat(prescription): secure Prescription Intelligence V1 A+B` — **MERGED**.

Squash merge produit sur `master` : `c8870ecca4c9ac3f3beb00df6030785dd8ee5aa1`.

## Preuves CI

HEAD produit certifié avant canonical `6e9129ebc03e1b73fac36dc2944149c194bcc023` :

- CI #3986 / `34878423669` : **SUCCESS** ;
- T2 Runtime Browser #2899 / `34878423636` : **SUCCESS** ;
- Patient P7 #1498 / `34878423562` : **SUCCESS** ;
- Catalog Connected Truth #1126 / `34878423561` : **SUCCESS** ;
- PostgreSQL #414 / `34878423557` : **SUCCESS** ;
- Ordonnance Fidelity V3 Visual #70 / `34878423582` : **SUCCESS** ;
- Ordonnance Composer Visual #34 / `34878423578` : **SUCCESS** ;
- Settings R11 #644 / `34878423659` : **SUCCESS** ;
- M6-I #1699 / `34878423604` : **SKIPPED attendu**.

Post-merge `master` sur `c8870ecca4c9ac3f3beb00df6030785dd8ee5aa1` :

- CI #3992 / run `34880364187` : **SUCCESS** ;
- Frontend tests : **SUCCESS** ;
- Frontend build : **SUCCESS** ;
- Backend prod safety/config hardening : **SUCCESS** ;
- Backend test suite : **SUCCESS** ;
- Garde production négative : **SUCCESS**.

## Déploiement

Aucun déploiement Vercel demandé ni réalisé.

## Risques résiduels / lot suivant

1. Le snapshot CNOPS est ancien et ne doit jamais être utilisé comme preuve de disponibilité commerciale actuelle.
2. Les moteurs pharmacologiques legacy restent présents hors du chemin V1 ; ils ne doivent pas être reconnectés sans certification.
3. C exige d’abord un contexte patient structuré suffisant, puis une règle clinique sourcée/versionnée avec au moins deux sources sérieuses concordantes et des tests positifs/négatifs.
4. Aclav reste un exemple UX uniquement jusqu’à identification de la présentation exacte et vérification documentaire/clinique dédiée.

## Lot C — point de reprise

Chemin code vérifié pour le contexte clinique structuré :

`models.Patient → backend/schemas/patient.py → frontend/src/features/patients/PatientIdentityContract.ts → AddPatientForm.tsx / EditPatientForm.tsx`.

Le contrat `PatientBase` utilise `extra="forbid"` : les nouveaux champs doivent être explicitement modélisés et migrés, jamais cachés dans `antecedents_medicaux`.

## Next exact

`Lot C : concevoir et implémenter d’abord le contexte patient clinique structuré minimal, avec migration + API + UI + tests ; maintenir toute suggestion clinique fail-closed jusqu’à certification scientifique séparée des règles.`
