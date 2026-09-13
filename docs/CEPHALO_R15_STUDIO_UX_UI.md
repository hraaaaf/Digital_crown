# DIGITAL CROWN — CÉPHALOMÉTRIE — R15 STUDIO CLINIQUE UX/UI

**Date :** 2026-09-12  
**Statut :** R15 CANDIDAT — certification finale en cours, non mergé  
**Base BEFORE produit vérifiée :** `36091c89a6f4ae0679f40980e9f7f3e5e143d6be`  
**Branche :** `feat/cephalo-r15-clinical-studio-ux`  
**PR :** #458  
**Canonique parent :** `docs/CEPHALO_DIAGNOSTIC_SPEC.md`  
**Déploiement :** aucun ; aucun déploiement Vercel sans autorisation explicite.

## GOAL R15

Construire le Studio clinique UX/UI Digital Crown qui rend les états scientifiques R11/R12/R13/R14 immédiatement compréhensibles et actionnables par le praticien, sans inventer, masquer ou auto-sélectionner de contenu clinique.

### Succès observable

- lecture explicite et continue `R11 → R12 → R13 → R14` ;
- provenance, missing data, contradictions, contre-indications et blocking gates visibles ;
- `EVALUABLE` présenté comme évaluable, jamais comme prescription ou sélection ;
- `BLOCKED != DROPPED` conservé ;
- toute action praticien affichée est soit réellement disponible avec preuve backend traçable, soit explicitement indisponible avec sa raison ;
- champs libres legacy clairement distingués des objets autoritaires R11–R14 ;
- archivage documentaire et validation clinique R14 jamais confondus ;
- BEFORE/AFTER sur les mêmes surfaces et viewports 390 / 768 / 1280+ ;
- CI exact-head + T2 verts avant merge ;
- reviews/threads clean ;
- aucun déploiement.

## EXTENSION DE MISSION INTÉGRÉE

1. remplacer la lecture clinique legacy par une lecture explicite de l'autorité `R11 → R12 → R13 → R14` ;
2. exposer provenance, missing data, contradictions, contre-indications, blockers, `EVALUABLE` et absence de snapshot autoritaire ;
3. aucune validation décorative ou locale ;
4. séparer notes libres et autorité scientifique ;
5. séparer actions documentaires et validation R14 ;
6. remettre en état la certification visuelle préexistante des actions d'historique ;
7. couvrir Étapes 3 et 4 aux mêmes viewports 390 / 768 / 1280+.

## CHRONOLOGIE DE PREUVE

- Goal R15 et contraintes UX/UI définis avant implémentation.
- `21eff261a7128ef733936569dc42d533f832da2e` : premier commit de branche, harness BEFORE uniquement.
- `b6efb79bb821ad6c3c6e6ac85ec90433f175c799` : workflow BEFORE.
- `5abebf9f26b25d622b7e5fde8ca4073952b55005` : première réparation du workflow visuel historique avant code R15.
- `249cf53564b414d895047fc675ea429b694f2c58` : première projection backend R15.
- Écart historique conservé explicitement : la référence/mockup dédiée n'avait pas été commitée avant les premiers changements UI ; ce document ne réécrit pas cette chronologie.

## BEFORE CERTIFIÉ

Workflow : `Cephalo R15 BEFORE`.

Preuve exacte :
- run `34720474029` : **SUCCESS** ;
- produit capturé : `36091c89a6f4ae0679f40980e9f7f3e5e143d6be` ;
- artifact `cephalo-r15-before-exact-master` ;
- artifact id `10305288821` ;
- digest `sha256:93d6dd3da6e6799aa66b6f40c60fabdc9235a213248c6ac88bc28f2b705ce5cc` ;
- viewports : `390x844`, `768x1024`, `1280x900` ;
- 12 captures : Step 3 top + décision et Step 4 top + action ;
- `invalidCount = 0` ;
- aucun egress externe ;
- aucun overflow horizontal sur les captures certifiées ;
- rendu transitoire 768 récupéré par une seconde tentative fraîche, résultat final valide.

Constats BEFORE :
- aucune surface explicite R11/R12/R13/R14 ;
- Step 3 expose directement les formulaires/notes cliniques legacy ;
- Step 4 mélange encore davantage la notion de validation et d'archivage ;
- l'autorité scientifique n'est pas hiérarchisée avant les formulaires.

## GOAL VISUEL

Le praticien doit comprendre sans inférence :
- où se situe le dossier dans R11→R14 ;
- ce qui est autoritaire versus simple note ;
- pourquoi un étage est bloqué ;
- quelles données/preuves manquent ou se contredisent ;
- quelle provenance soutient l'état ;
- si une action praticien est réellement disponible ;
- qu'une action documentaire n'est pas une validation clinique.

Aucun code couleur ne transforme une valeur brute ou une hypothèse non validée en diagnostic implicite.

## RÉFÉRENCE / MOCKUP R15

Référence : identité Digital Crown céphalométrique existante et certification R1, sans design externe générique.

```text
┌ Chaîne clinique scientifique ─────── R11 → R14 ─── N blocages ┐
│ mesure calculable ≠ diagnostic ≠ indication ≠ traitement      │
├───────────┬───────────┬───────────┬───────────┤
│ R11       │ R12       │ R13       │ R14       │
│ [ÉTAT]    │ [ÉTAT]    │ [ÉTAT]    │ [ÉTAT]    │
├───────────────────────────────────────────────────────────────┤
│ étage sélectionné · résumé · blockers · provenance            │
│ missing data · contradictions · contre-indications            │
│ action praticien seulement si preuve backend disponible       │
└───────────────────────────────────────────────────────────────┘

[Notes legacy — hors preuve scientifique]
[Actions documentaires — ne valent jamais validation R14]
```

Mobile : détails empilés, chaîne lisible, aucun élément critique masqué horizontalement.

## TOKENS

Source : `frontend/src/features/ortho/cephaloTheme.ts`.

- fonds/panels/cards/borders/textes depuis les tokens existants ;
- `accentSuccess` réservé à un état réellement validé ;
- `accentWarning` pour attente/action requise/évaluable non sélectionné ;
- `accentError` pour rejet ou blocage réel ;
- aucune couleur diagnostique ajoutée hors contrat ;
- identité sombre/glassmorphisme conservée.

## IMPLÉMENTATION R15

Le Studio est une **projection clinique**, pas un moteur supplémentaire :
- `backend/services/cephalo_r15_clinical_studio.py` projette l'autorité existante en fail-closed ;
- `backend/routers/cephalo_clinical_studio.py` applique le tenant guard avant lecture patient et lie l'analyse demandée ;
- `frontend/src/features/ortho/components/ClinicalScientificStudio.tsx` rend R11–R14, blockers, provenance, missing data, contradictions, contre-indications et action praticien ;
- aucune règle, norme, diagnostic, option ou plan n'est créé localement ;
- faute de snapshots autoritaires persistés, les étages restent explicitement `BLOCKED` et l'action clinique reste indisponible ;
- `EVALUABLE` n'est jamais présenté comme une prescription ;
- Step 3 renomme les champs historiques comme notes libres legacy hors R11/R13/R14 ;
- Step 4 sépare `Prévisualiser`, `Brouillon PDF`, `Archiver le bilan` de toute validation R14.

## AFTER VISUEL PROUVÉ

Run exact candidat vérifié :
- run `34723980208` : **SUCCESS** ;
- product HEAD `c618d6e589ab1a80e0f9e6735c861ad7e222c316` ;
- artifact id `10307316607` ;
- digest `sha256:881019162700bf45cd088fb21a6d7ab1a19e704d1d138f7dfe7edef25da5ff26` ;
- 12 captures aux mêmes viewports/scènes que le BEFORE ;
- `invalidCount = 0` ;
- zéro egress externe ;
- zéro erreur console/page sur les tentatives finales ;
- zéro overflow horizontal ;
- `analysis_id=9915` lié explicitement sur les trois viewports ;
- aucun ancien libellé dangereux (`Diagnostic / Résumé Diagnostique`, `Plan thérapeutique — décision praticien`, `Valider & Archiver`) dans les surfaces certifiées.

Le HEAD de branche continue d'évoluer uniquement pour les gardes/tests/certification ; un AFTER exact du HEAD final reste obligatoire avant merge.

## COMPARAISON BEFORE → AFTER

- **Hiérarchie scientifique :** absente → R11→R14 placée avant les formulaires métier.
- **Blocages :** implicites/absents → blocages actifs et raisons visibles.
- **Provenance :** non structurée → provenance explicite par étage.
- **Données manquantes / contradictions / contre-indications :** sans surface dédiée → trois surfaces dédiées.
- **Action praticien :** ambiguë localement → indisponibilité explicite faute de preuve backend.
- **Notes legacy :** vocabulaire clinique ambigu → notes libres clairement hors autorité R11/R13/R14.
- **Archivage :** `Valider & Archiver` ambigu → `Archiver le bilan`, action documentaire distincte.
- **Responsive :** 390/768/1280 sans overflow document sur AFTER certifié.

## SCORE VISUEL INTERNE

**9,3 / 10 — revue visuelle interne, non expertise humaine externe.**

Barème observé :
- hiérarchie scientifique : 2/2 ;
- séparation autorité / notes / archive : 2/2 ;
- lisibilité des blockers/provenance : 2/2 ;
- intégrité responsive et absence d'overflow : 2/2 ;
- densité/scannabilité mobile : 1,3/2.

Déduction : sur 390 px, la chaîne complète impose naturellement davantage de hauteur et R14 n'est pas entièrement visible dans le premier viewport. Aucun contenu critique n'est masqué, mais la densité verticale empêche de revendiquer un score parfait.

## TESTS / GARDES

Déjà prouvés sur candidats R15 :
- frontend tests/build verts sur le candidat précédent ;
- T2 et PostgreSQL verts sur le candidat précédent ;
- reviews : 0 ; threads : 0 ;
- diff audité : scope R15 + réparation de la dette visuelle historique uniquement.

Correction de garde effectuée :
- le test statique legacy qui exigeait `Plan thérapeutique — décision praticien` a été aligné sur le nouveau contrat fail-closed et interdit désormais le retour de ce libellé.

Dette `Document History Actions Visual Certification` :
- l'ancien workflow dépendait du backend/auth/génération PDF et timeoutait avant même d'atteindre le composant ;
- le nouveau certificat rend le vrai `PatientDocuments` avec fixture déterministe, Chromium frais et contrôles 390/768/1280 ;
- preuve verte du HEAD final encore requise avant merge.

## NON-GOALS R15

- aucune activation de nouvelle norme ou règle scientifique ;
- aucune création de vraie option thérapeutique ;
- aucune auto-sélection R13 ;
- aucun contournement des gates R11–R14 ;
- aucun PDF/restitution R16 ;
- aucun déploiement Vercel.

## GATES RESTANTS AVANT MERGE

1. `Document History Actions Visual Certification` vert sur HEAD final ;
2. CI exact-head verte ;
3. T2 exact-head verte ;
4. PostgreSQL exact-head vert ;
5. AFTER R15 exact-head vert ;
6. reviews/threads toujours clean ;
7. PR mergeable ;
8. merge puis vérification master post-merge ;
9. closeout canonique + handover R16 dans un lot documentaire auditable.

## NEXT EXACT

Obtenir tous les checks exact-head verts sur le dernier commit de certification, corriger toute régression prouvée, puis merger #458 uniquement lorsque les gates ci-dessus sont satisfaits.
