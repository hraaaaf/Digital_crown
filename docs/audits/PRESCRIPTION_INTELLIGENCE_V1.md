# Prescription Intelligence V1 — Canonical

Date : 2026-09-15

## Statut

**CLOS — A+B, C1 et C2 règle 1 certifiés et mergés sur `master`.**

Ce fichier est le point de reprise canonique du chantier Prescription Intelligence V1.

## Goal

`recherche médicament → présentation documentaire explicite → contexte clinique structuré → suggestion clinique seulement si règle certifiée + contexte suffisant → calcul traçable → validation praticien`

A+B, C1 et une première règle C2 atteignent désormais ce flux dans un périmètre clinique volontairement étroit. Aucune prescription autonome n'est autorisée.

## A — Recherche médicament

- autocomplete via `/medications/search` ;
- nom commercial / DCI ;
- snapshot CNOPS avec provenance ;
- aucune habitude/preset/smart-suggest legacy dans le flux actif ;
- panne référentiel = aucune suggestion inventée.

## B — Présentation explicite

- ID stable `cnops:<sha256>` ;
- présentation sélectionnée explicitement ;
- posologie vidée après sélection ;
- modification du nom invalide identité documentaire/dosage/forme/posologie ;
- aucune forme ou voie inférée silencieusement.

Le snapshot CNOPS reste historique : il documente identité/présentation, pas la disponibilité commerciale actuelle en 2026.

## C1 — Contexte clinique structuré

`patient_clinical_contexts` contient notamment poids, allergies médicamenteuses, contexte rénal/hépatique et provenance de mise à jour. Les invariants restent fail-closed. L'indication appartient à l'ordonnance et non au patient.

Migration C1 : `c1ctx0000001`.

Correction UX praticien #497 : les statuts techniques internes ne sont plus affichés au dentiste. Fidelity #103 / run `34903537345`: SUCCESS, artifact `10371681258`, digest `sha256:4db6404230db025a8b14a5e7ab1d6e6f27ff277cf3cbda44452d9003046a5153`, score visuel conservateur 9.4/10.

## C2 — Règle clinique 1 certifiée

Règle : **prophylaxie de l'endocardite infectieuse chez l'adulte, amoxicilline orale, geste dentaire éligible**.

Contrat scientifique : AHA 2021 + ADA, avec ESC 2023 en cross-check indépendant. Périmètre et taxonomie détaillés dans `docs/audits/PRESCRIPTION_INTELLIGENCE_C2_IE_PROPHYLAXIS.md`.

READY uniquement si toutes les conditions explicites passent :

- adulte >=18 ;
- catégorie cardiaque source-exacte éligible ;
- geste dentaire éligible explicitement confirmé ;
- allergie pénicilline/amoxicilline explicitement sûre ;
- aucune allergie médicamenteuse libre non réconciliée ;
- voie orale possible ;
- absence explicitement confirmée de prise actuelle pénicilline/amoxicilline ;
- présentation CNOPS résolue côté serveur ;
- DCI mono-composant exactement AMOXICILLINE/AMOXICILLIN.

Résultat certifié dans ce seul périmètre : **amoxicilline 2 g, dose unique, 30–60 min avant le geste**. Le résultat est read-only et exige toujours la validation du praticien.

Migration C2 : `c2ie0000002` sur `c1ctx0000001`.

Endpoint : `POST /api/prescriptions/clinical-rules/ie-prophylaxis/evaluate`.

Aucune mutation d'ordonnance, aucun autofill de dose, aucun appel aux moteurs legacy `/safety/check` ou `/smart-suggest`.

### Limites C2 conservées

Restent hors automatisation : pédiatrie, alternatives en cas d'allergie, voies parentérales, conversion 2 g → nombre de comprimés/gélules, interprétation du texte libre et scénario CHD complètement réparée avec matériel prothétique <6 mois non réconcilié.

## UI/UX C2

BEFORE : Fidelity #103, artifact `10371681258`, viewports 390/430/768/1280.

AFTER exact-head : Fidelity #112 / run `34920977252`: **SUCCESS**.

- artifact `10377947131` ;
- digest `sha256:c55abc8567562d376e356ae350281fec8d99b237d8227445a545977c576d88c6` ;
- PASS, failures `[]`, pageErrors `[]` ;
- touch min 44 px ;
- aucun overflow horizontal ;
- résultat READY certifié aux quatre viewports ;
- aucun jargon interne visible ;
- score visuel conservateur : **9.0/10**.

Le panneau `Prévention endocardite` est déclenché explicitement par le praticien et reste read-only. Aucun remplissage automatique de la posologie.

## Preuve C2 exact-head avant merge

HEAD : `d4248745aeeee8def06b403dcb971b5e4b9b30b0`.

- CI #4214 / run `34920977105`: SUCCESS ;
- full backend regression DB/patients/documents : SUCCESS ;
- Fidelity #112 : SUCCESS ;
- PostgreSQL #629 : SUCCESS ;
- Patient P7 #1586 : SUCCESS ;
- T2 #3114 : SUCCESS ;
- Catalog #1223 : SUCCESS ;
- Settings #686 : SUCCESS ;
- M6-I #1914 : SKIPPED attendu.

## Merge C2 et post-merge

PR #500 : **MERGED** par squash.

Merge : `0097e3a08340f753803a86d2a1134880ad9ce902`, signature GitHub vérifiée.

Post-merge CI #4216 / run `34935647891`: **SUCCESS** :

- Tests & durcissement : SUCCESS ;
- full backend regression DB/patients/documents : SUCCESS ;
- frontend tests + build : SUCCESS ;
- garde production négative : SUCCESS ;
- M4 A/B/C : SKIPPED attendu sur push.

Aucun déploiement Vercel demandé ni réalisé.

## Frontière clinique actuelle

Une seule règle clinique est certifiée. Cela **n'autorise aucune généralisation** à d'autres antibiotiques, indications, âges, dosages ou situations cardiaques. Toute nouvelle règle est un lot scientifique séparé avec contexte structuré suffisant, >=2 sources sérieuses concordantes, fail-closed explicite, tests positifs/négatifs, revue indépendante et certification UI si exposée au praticien.

## Next exact

`Sélectionner la prochaine règle clinique candidate uniquement après définition d'un nouveau contrat scientifique borné. Ne pas élargir implicitement C2.`
