# DIGITAL CROWN — CÉPHALOMÉTRIE — R15 STUDIO CLINIQUE UX/UI

**Date :** 2026-09-13  
**Statut :** R15 FERMÉ — certifié, mergé et vérifié sur master  
**Base BEFORE produit vérifiée :** `36091c89a6f4ae0679f40980e9f7f3e5e143d6be`  
**HEAD candidat final certifié :** `f70d62df584a38a7deb8341dc608ad14274c3dec`  
**Merge master :** `258762da7aff8e7fd481990e96f32b761d635234`  
**Branche :** `feat/cephalo-r15-clinical-studio-ux`  
**PR :** #458 — MERGED  
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

## AFTER VISUEL FINAL PROUVÉ

Workflow : `Cephalo R15 AFTER` #47.

Preuve exacte du HEAD final :
- run `34782048394` : **SUCCESS** ;
- product HEAD `f70d62df584a38a7deb8341dc608ad14274c3dec` ;
- artifact id `10324659988` ;
- digest `sha256:c16f860f888ce13dce53e81f071baa7126947661a2bdd4887f935fe40c5a5d3e` ;
- 12 captures aux mêmes viewports/scènes que le BEFORE ;
- viewports `390x844`, `768x1024`, `1280x900` ;
- `invalidCount = 0` ;
- zéro egress externe ;
- zéro erreur console/page sur les tentatives finales ;
- zéro overflow horizontal ;
- `analysis_id=9915` lié explicitement sur les trois viewports ;
- aucun ancien libellé dangereux dans les surfaces certifiées ;
- le rendu 768 a nécessité une seconde tentative fraîche après un rendu transitoire vide ; la tentative finale est valide.

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

## TESTS / GARDES FINAUX

HEAD certifié `f70d62df584a38a7deb8341dc608ad14274c3dec` :
- CI #3783 : **SUCCESS** ;
- T2 Runtime Browser Certification #2715 : **SUCCESS** ;
- Cabinet Upgrade PostgreSQL Certification #230 : **SUCCESS** ;
- Cephalo R15 AFTER #47 : **SUCCESS** ;
- Document History Actions AFTER Certification #45 : **SUCCESS** ;
- Document History Actions Visual Certification #1220 : **SUCCESS** ;
- reviews : 0 ; threads : 0 ; commentaires PR : 0 ;
- PR #458 mergeable avant merge ;
- master vérifié inchangé sur `ab4bd58bf17bf567473ebfd6dfbd2e273ebd9426` juste avant merge.

Correction de garde intégrée :
- le test statique legacy qui exigeait `Plan thérapeutique — décision praticien` a été aligné sur le nouveau contrat fail-closed et interdit désormais le retour de ce libellé ;
- `Document History Actions AFTER Certification` génère un `T2_PASSWORD` isolé comme le workflow T2 au lieu d'affaiblir le runtime ;
- les deux certificats Document History sont verts ensemble sur le HEAD final.

## PREUVE DE CLÔTURE R15

- candidate HEAD certifié : `f70d62df584a38a7deb8341dc608ad14274c3dec` ;
- PR #458 : **MERGED** ;
- merge commit : `258762da7aff8e7fd481990e96f32b761d635234` ;
- master post-merge vérifié : `258762da7aff8e7fd481990e96f32b761d635234` ;
- parents du merge : `ab4bd58bf17bf567473ebfd6dfbd2e273ebd9426` + `f70d62df584a38a7deb8341dc608ad14274c3dec` ;
- aucun déploiement.

## NON-GOALS R15

- aucune activation de nouvelle norme ou règle scientifique ;
- aucune création de vraie option thérapeutique ;
- aucune auto-sélection R13 ;
- aucun contournement des gates R11–R14 ;
- aucun PDF/restitution R16 ;
- aucun déploiement Vercel.

## NEXT EXACT

R15 est fermé. Reprendre **R15bis UI/UX** depuis le master post-closeout vérifié, avec le R15 final comme BEFORE réel, puis suivre le cycle obligatoire `BEFORE → Goal → référence/mockup → implémentation → AFTER mêmes viewports → comparaison/tests → score visuel` sans modifier les contrats scientifiques R11–R14.