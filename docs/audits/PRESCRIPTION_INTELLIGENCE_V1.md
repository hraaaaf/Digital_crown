# Prescription Intelligence V1 — Canonical

Date : 2026-09-14

## Statut

**A+B certifiés et mergés sur `master`. C1 en cours de certification ; toute suggestion clinique reste bloquée (fail-closed).**

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

C1 ajoute uniquement les données structurées nécessaires à de futurs contrôles : poids explicite, allergies médicamenteuses structurées et contexte rénal/hépatique déclaré. L’indication est volontairement **scopée à chaque ordonnance** et non au patient, afin qu’une indication ancienne ne puisse pas être réutilisée silencieusement sur une nouvelle prescription.

Ces données ne suffisent pas à activer une règle clinique. C ne pourra être activé qu’après certification scientifique séparée de chaque règle, avec contexte nécessaire explicite, sources sérieuses concordantes et tests positifs/négatifs.

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

## Backend A+B

Fichiers principaux :

- `backend/services/medication_dict.py`
- `backend/routers/medications.py`
- `backend/tests/test_prescription_intelligence_catalog.py`

Contrats testés : provenance, ID présentation stable/résoluble, présentation inconnue fail-closed, validation dosage limitée à la présence documentaire, aucune revendication de commercialisation actuelle.

## C1 — Contexte clinique structuré

### Ownership

Données patient durables, persistées dans `patient_clinical_contexts` :

- `weight_kg` ;
- `medication_allergy_status` + `medication_allergies` ;
- `renal_context_status` + `renal_context_note` ;
- `hepatic_context_status` + `hepatic_context_note` ;
- provenance minimale `updated_at` / `updated_by_user_id`.

États explicites :

- allergies : `UNKNOWN`, `NONE_KNOWN`, `PRESENT` ;
- rein/foie : `UNKNOWN`, `NO_KNOWN_IMPAIRMENT`, `IMPAIRMENT_REPORTED`.

L’API patient rejette les champs inconnus, notamment `clinical_ready` et `prescription_indication`.

L’**indication de prescription est document-scoped** : elle appartient au `clinical_data` de l’ordonnance, participe au fingerprint de preview et est réhydratée en édition de cette ordonnance. Elle n’est pas enregistrée dans le contexte durable du patient et n’active aucune règle de dose.

### Fichiers C1

Backend :

- `backend/models_patient_clinical_context.py`
- `backend/schemas/patient_clinical_context.py`
- `backend/routers/patient_clinical_context.py`
- `backend/tests/test_patient_clinical_context_c1.py`
- `alembic/versions/c1ctx0000001_add_patient_clinical_context.py`

Frontend :

- `frontend/src/features/admin/DocumentStudio/Forms/PatientClinicalContextPanel.tsx`
- `frontend/src/features/admin/DocumentStudio/Forms/PrescriptionAgenticStudioV1.tsx`
- `frontend/src/features/admin/DocumentStudio/Forms/PrescriptionAgenticStudio.indication.test.tsx`
- `frontend/src/features/admin/DocumentHub.tsx`
- `frontend/src/features/admin/DocumentStudio/DocumentHubContent.tsx`
- `frontend/src/features/admin/DocumentStudio/DocumentPreviewFingerprint.ts`
- `frontend/src/features/admin/DocumentStudio/PrescriptionIntelligenceV1.boundary.test.ts`

### Invariants C1

- poids : valeur finie strictement positive ou inconnue ;
- allergie `PRESENT` exige au moins une allergie explicite ;
- aucune liste d’allergies sous `UNKNOWN` ;
- note rénale/hépatique seulement avec `IMPAIRMENT_REPORTED` ;
- erreur de chargement UI : aucune valeur clinique supposée et sauvegarde bloquée ;
- sauvegarde clinique patient manuelle uniquement ;
- aucune formule, aucun seuil médical, aucun calcul de dose ;
- aucune route `/prescriptions/*` introduite par le panneau C1 ;
- indication injectée uniquement dans le payload `ordonnance`, jamais dans les autres types de document.

Migration C1 : `c1ctx0000001`, chaînée sur `f5a55e700005`.

### UX C1

Le premier AFTER C1 techniquement vert a été refusé après inspection visuelle : le panneau clinique développé par défaut doublait pratiquement la hauteur du studio et repoussait la saisie médicament.

Correction retenue :

- saisie médicament et action `Ajouter une ligne` restent les premières actions métier du studio ;
- contexte patient C1 compact/replié par défaut avec résumé factuel ;
- dépliage explicite `Renseigner`, sauvegarde manuelle puis repli automatique ;
- indication de l’ordonnance reste séparée et document-scoped après la zone médicaments ;
- le certificateur capture désormais une scène C1 dépliée dédiée en plus de `top`, `planning` et `preview`.

## Frontend A+B

Fichiers principaux :

- `frontend/src/features/admin/DocumentStudio/Forms/DrugRowV1.tsx`
- `frontend/src/features/admin/DocumentStudio/Forms/PrescriptionAgenticStudioV1.tsx`
- `frontend/src/features/admin/DocumentHub.tsx`
- `frontend/src/features/admin/DocumentStudio/DocumentHubContent.tsx`
- `frontend/src/features/admin/DocumentStudio/useDocumentGenerator.ts`
- `frontend/src/features/admin/DocumentStudio/PrescriptionIntelligenceV1.boundary.test.ts`

Garde-fous testés : catalogue uniquement, sélection explicite, aucune posologie injectée, invalidation des champs associés si le nom change, absence smart-suggest/safety-check legacy, absence de forme implicite, blocage clinique explicite.

## UI/UX — A+B BEFORE → AFTER

Viewports obligatoires : `390×844`, `430×932`, `768×1024`, `1280×900`.

### BEFORE A+B

Référence certifiée Ordonnance Fidelity V3.1 : artifact `10339208565`, digest `sha256:018e71b154551aadba5f90171b735770efde4b19cf03654cf64eaac4044e230d`.

### AFTER A+B exact-head

HEAD certifié : `6e9129ebc03e1b73fac36dc2944149c194bcc023`.

Ordonnance Fidelity V3 Visual #70 : **SUCCESS** — run `34878423582`, artifact `10361827618`, digest `sha256:606606845e996b9f794b7b3a03368f809c6e5c11f68c147b714c2958dd064f6a`, 4/4 viewports, touch target minimum `44 px`, aucun overflow horizontal, aucune erreur page.

Ordonnance Composer Visual #34 : **SUCCESS** — run `34878423578`, artifact `10362195361`, digest `sha256:70cac3124ececb85c9554e34535bc211b9de1beb88ec5d0768de723126b0482e`.

### Comparaison A+B

| Viewport | BEFORE | AFTER | Réduction |
| --- | ---: | ---: | ---: |
| 390×844 | 993 px | 636.25 px | 35.9 % |
| 430×932 | 966 px | 590 px | 38.9 % |
| 768×1024 | 939.25 px | 447.25 px | 52.4 % |
| 1280×900 | 889.25 px | 406.25 px | 54.3 % |

Score visuel conservateur A+B : **9.3/10**.

## UI/UX — C1 BEFORE → AFTER

BEFORE C1 = dernier état A+B certifié : Ordonnance Fidelity V3 Visual #70, run `34878423582`, artifact `10361827618`, mêmes quatre viewports.

Premier AFTER C1 inspecté : Fidelity #93 sur `f30292e8e4f802a489dbc5d8c9391c99a95470f4` — gate automatique **SUCCESS**, mais version **rejetée visuellement**. Hauteur studio observée : `390 px : 1295.25 px` et `1280 px : 842.25 px`, contre `636.25 px` et `406.25 px` au BEFORE C1 ; la saisie médicament perdait sa priorité visuelle.

AFTER C1 corrigé : **EN ATTENTE DE CERTIFICATION EXACT-HEAD**.

Le gate C1 corrigé exige : contexte patient compact par défaut, indication document-scoped présente, carte médicament + action `Ajouter une ligne` visibles ensemble dans la scène planning, scène C1 dépliée avec les champs structurés visibles, contrôles visibles ≥ 44 px, aucun overflow horizontal, preview desktop conservée.

## Repo / merge

Repo : `hraaaaf/Digital_crown`.

A+B : PR `#487` mergée ; squash merge `c8870ecca4c9ac3f3beb00df6030785dd8ee5aa1`.

C1 : PR `#495 — feat(prescription): add structured patient context C1` — **OPEN**, base `master` `4cfa04d651a47fa0cc2c60482e5ff5729148fb86`.

Candidat C1 corrigé en cours de certification : `7f36b47cadc91a43ba3c48a8139c5487b458b5e2`.

## Preuves CI A+B

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

Post-merge A+B `master` sur `c8870ecca4c9ac3f3beb00df6030785dd8ee5aa1` :

- CI #3992 / run `34880364187` : **SUCCESS** ;
- Frontend tests : **SUCCESS** ;
- Frontend build : **SUCCESS** ;
- Backend prod safety/config hardening : **SUCCESS** ;
- Backend test suite : **SUCCESS** ;
- Garde production négative : **SUCCESS**.

## Preuves C1

Candidat exact-head corrigé `7f36b47cadc91a43ba3c48a8139c5487b458b5e2` :

- CI #4127 / run `34892422969` : **QUEUED** ;
- Ordonnance Fidelity V3 Visual #97 / run `34892423245` : **PENDING** ;
- T2 Runtime Browser #3037 / run `34892422980` : **PENDING** ;
- Patient P7 #1547 / run `34892423105` : **PENDING** ;
- PostgreSQL #552 / run `34892423181` : **PENDING** ;
- Portability Runtime #598 / run `34892423118` : **IN_PROGRESS** ;
- Settings R11 #671 / run `34892423109` : **SUCCESS** ;
- M6-I #1837 / run `34892423217` : **SKIPPED attendu**.

Ces états ne constituent pas encore une certification finale C1.

## Déploiement

Aucun déploiement Vercel demandé ni réalisé.

## Risques résiduels / lot suivant

1. Le snapshot CNOPS est ancien et ne doit jamais être utilisé comme preuve de disponibilité commerciale actuelle.
2. Les moteurs pharmacologiques legacy restent présents hors du chemin V1 ; ils ne doivent pas être reconnectés sans certification.
3. C1 fournit des faits structurés, mais **ne prouve pas leur exactitude clinique** et ne suffit pas à autoriser une règle de dose.
4. L’indication est conservée comme métadonnée de l’ordonnance ; C1 ne l’imprime pas dans le PDF et ne l’interprète pas.
5. Toute règle C suivante exige un contrat clinique séparé, sources versionnées/concordantes, paramètres complets et tests d’acceptation/refus indépendants.
6. Aclav reste un exemple UX uniquement jusqu’à identification de la présentation exacte et vérification documentaire/clinique dédiée.

## Next exact

`Achever les verdicts exact-head du candidat corrigé ; si verts, inspecter l’artifact Fidelity aux quatre viewports et la scène C1 dépliée, comparer au BEFORE A+B, inscrire les preuves finales ici, merger PR #495 par squash, puis vérifier master post-merge.`
