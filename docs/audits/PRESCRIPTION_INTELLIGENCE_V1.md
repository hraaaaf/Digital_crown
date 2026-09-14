# Prescription Intelligence V1 — Canonical

Date : 2026-09-14

## Statut

**A+B CERTIFIÉS EXACT-HEAD — canonical de closeout en cours ; lot C volontairement bloqué (fail-closed).**

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

L’UI affiche explicitement :

- `Suggestion clinique bloquée` ;
- `Contrôle clinique automatique bloqué`.

Le flux V1 actif n’appelle pas :

- `/prescriptions/smart-suggest/{patient_id}` ;
- `/prescriptions/safety/check`.

Motif : ces mécanismes legacy contiennent des règles/mappings cliniques non certifiés selon le contrat V1.

Le modèle `Patient` expose actuellement de façon structurée notamment la date de naissance et un champ libre `antecedents_medicaux`, mais pas les champs structurés requis pour généraliser des règles de dose sûres tels que poids, allergies structurées, fonction rénale/hépatique et indication clinique structurée. C ne pourra être activé qu’après ajout des données nécessaires et certification scientifique de chaque règle.

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
- contenu déclaré : princeps/génériques, prix public, prix hôpital, base de remboursement ;
- la CNOPS décrit également son guide médicament comme associant DCI, noms commerciaux, dosage, présentation, classe thérapeutique, PPV et PBR.

Conclusion : cette source est exploitable comme **snapshot documentaire historique** d’identité/présentation. Elle ne prouve pas le statut de commercialisation actuel en 2026. Le contrat expose donc `current_marketing_status_verified=false`.

## Backend

Fichiers principaux :

- `backend/services/medication_dict.py`
- `backend/routers/medications.py`
- `backend/tests/test_prescription_intelligence_catalog.py`

Contrats testés :

- provenance ;
- ID présentation stable et résoluble ;
- présentation inconnue fail-closed ;
- validation dosage limitée à la présence documentaire dans le snapshot ;
- aucune revendication de commercialisation actuelle.

## Frontend

Fichiers principaux :

- `frontend/src/features/admin/DocumentStudio/Forms/DrugRowV1.tsx`
- `frontend/src/features/admin/DocumentStudio/Forms/PrescriptionAgenticStudioV1.tsx`
- `frontend/src/features/admin/DocumentHub.tsx`
- `frontend/src/features/admin/DocumentStudio/DocumentHubContent.tsx`
- `frontend/src/features/admin/DocumentStudio/useDocumentGenerator.ts`
- `frontend/src/features/admin/DocumentStudio/PrescriptionIntelligenceV1.boundary.test.ts`

Garde-fous testés :

- catalogue uniquement ;
- sélection explicite ;
- aucune posologie injectée ;
- invalidation des champs associés si le nom change ;
- absence smart-suggest ;
- absence safety/check legacy dans V1 ;
- absence de forme implicite ;
- blocage clinique explicite.

## UI/UX — BEFORE → AFTER

Viewports obligatoires : `390×844`, `430×932`, `768×1024`, `1280×900`.

### BEFORE

Référence certifiée Ordonnance Fidelity V3.1 :

- artifact `10339208565` ;
- digest `sha256:018e71b154551aadba5f90171b735770efde4b19cf03654cf64eaac4044e230d`.

### AFTER exact HEAD

HEAD certifié :

`6e9129ebc03e1b73fac36dc2944149c194bcc023`

Ordonnance Fidelity V3 Visual #70 : **SUCCESS**

- run `34878423582` ;
- artifact `10361827618` ;
- digest `sha256:606606845e996b9f794b7b3a03368f809c6e5c11f68c147b714c2958dd064f6a` ;
- 4/4 viewports ;
- touch target minimum : `44 px` ;
- aucun overflow horizontal ;
- aucune erreur page.

Ordonnance Composer Visual #34 : **SUCCESS**

- run `34878423578` ;
- artifact `10362195361` ;
- digest `sha256:70cac3124ececb85c9554e34535bc211b9de1beb88ec5d0768de723126b0482e`.

Les deux derniers commits ne modifient pas le produit : `94a6998d...` aligne uniquement un probe Vitest sur `data-safety-status="blocked"`; `6e9129eb...` rend le fixture Composer autonome en mockant `/api/medications/search` à `[]`.

### Comparaison

Hauteur du studio principal BEFORE → AFTER :

| Viewport | BEFORE | AFTER | Réduction |
| --- | ---: | ---: | ---: |
| 390×844 | 993 px | 636.25 px | 35.9 % |
| 430×932 | 966 px | 590 px | 38.9 % |
| 768×1024 | 939.25 px | 447.25 px | 52.4 % |
| 1280×900 | 889.25 px | 406.25 px | 54.3 % |

Le flux remplace les surfaces de protocoles/quick-entry legacy par une hiérarchie documentaire plus courte, avec deux états de sécurité bloqués visibles avant le corps de prescription.

Score visuel conservateur : **9.3/10**. Réserve principale : sur 390/430 px, les deux messages fail-closed consomment encore une hauteur notable avant le premier champ médicament ; cette densité est volontairement acceptée au bénéfice de la sécurité explicite.

## Repo / PR

Repo : `hraaaaf/Digital_crown`

Branche : `feat/prescription-intelligence-v1`

PR : `#487 — feat(prescription): secure Prescription Intelligence V1 A+B`

HEAD produit + probes avant canonical : `6e9129ebc03e1b73fac36dc2944149c194bcc023`

Master observé avant closeout : `1ce5bc8a6297c89e9b69a8b455ada576d374a6fc`.

Depuis la base historique de la PR, master n’a ajouté qu’un fichier documentaire hors scope : `docs/audits/COMPETITIVE_ROADMAP_POST_MEDIA.md`. PR mergeable vérifiée `true` avant closeout ; aucun rebase produit requis.

## CI exact-head avant canonical

Tous les gates du HEAD `6e9129ebc03e1b73fac36dc2944149c194bcc023` sont terminés :

- CI #3986, run `34878423669` : **SUCCESS** ; frontend tests + build **SUCCESS** ; backend tests + durcissement **SUCCESS**.
- T2 Runtime Browser #2899, run `34878423636` : **SUCCESS**.
- Patient P7 #1498, run `34878423562` : **SUCCESS**.
- Catalog Connected Truth #1126, run `34878423561` : **SUCCESS**.
- PostgreSQL #414, run `34878423557` : **SUCCESS**.
- Ordonnance Fidelity V3 Visual #70, run `34878423582` : **SUCCESS**.
- Ordonnance Composer Visual #34, run `34878423578` : **SUCCESS**.
- Settings R11 #644, run `34878423659` : **SUCCESS**.
- M6-I #1699, run `34878423604` : **SKIPPED attendu**.

Le premier run CI du produit avait identifié un unique probe statique obsolète dans `OrdonnanceFidelityV3.u1.test.ts` : il cherchait `data-safety-status={safetyStatus}` alors que V1 utilise l’état fixe `data-safety-status="blocked"`. Le correctif `94a6998d...` modifie uniquement cette assertion. Le run Composer suivant a révélé que son fixture visuel dépendait involontairement d’un appel `/api/medications/search` alors que ce workflow ne démarre aucun backend ; `6e9129eb...` isole désormais le gate en mockant ce seul endpoint à `[]`.

## Déploiement

Aucun déploiement Vercel demandé ni réalisé.

## Risques résiduels / lot suivant

1. Le snapshot CNOPS est ancien et ne doit jamais être utilisé comme preuve de disponibilité commerciale actuelle.
2. Les moteurs pharmacologiques legacy restent présents hors du chemin V1 ; ils ne doivent pas être reconnectés sans certification.
3. C exige d’abord un contexte patient structuré suffisant, puis une règle clinique sourcée/versionnée avec au moins deux sources sérieuses concordantes et des tests positifs/négatifs.
4. Aclav reste un exemple UX uniquement jusqu’à identification de la présentation exacte et vérification documentaire/clinique dédiée.

## Next exact

`pousser ce canonical → vérifier le CI du commit documentaire → squash merge PR #487 → vérifier master/PR post-merge → mettre ce canonical en statut CLOS avec le SHA de merge → vérifier le post-merge.`
