# HANDOVER — DIGITAL CROWN / CÉPHALOMÉTRIE — R15bis UI/UX

**Date :** 2026-09-13  
**Repo :** `hraaaaf/Digital_crown`  
**Canonique :** `docs/CEPHALO_DIAGNOSTIC_SPEC.md`  
**Gate d’entrée :** SATISFAIT — R15 mergé, closeouté et vérifié sur `master` `3dbab4e1fe722265932799eff01d4de8de252da9`.  
**Branche active :** `feat/cephalo-r15bis-uiux`  
**PR active :** #477  
**Référence visuelle :** `docs/assets/cephalo/r15bis-ui-reference.jpg`

## GOAL

Transformer le studio céphalométrique issu de R15 en une interface clinique plus lisible, plus structurée et plus rapide à parcourir, **sans modifier aucune logique scientifique, clinique, diagnostique ou thérapeutique**.

Le lot reprend uniquement les qualités structurelles du visuel de référence :
- navigation principale immédiatement lisible ;
- radio/viewer dominant ;
- panneau de résultats séparé et hiérarchisé ;
- sections cliniques regroupées avec icônes simples ;
- tableaux valeur/libellé compacts ;
- états et complétude visibles sans bruit visuel.

Le thème sombre du mockup n’est **pas** une cible. La cible reste l’identité Digital Crown et ses tokens existants.

## SUCCÈS OBSERVABLE

R15bis est réussi seulement si les preuves montrent :

1. navigation principale cohérente et explicite : `Accueil / Patients / Imagerie / Tracés / Analyses / Rapports` lorsque ces destinations existent réellement dans le produit ;
2. viewer/radio reste la surface dominante aux viewports adaptés ;
3. résultats scientifiques/COM/cliniciens regroupés en panneaux lisibles sans masquer la provenance ni la calculabilité ;
4. icônes homogènes, décoratives seulement quand elles n’ajoutent aucune action ;
5. aucun bouton, onglet ou destination factice ;
6. aucun contenu R11/R12/R13/R14 synthétisé ou auto-validé pour remplir l’UI ;
7. aucun changement de calcul, contrat backend, règle de sécurité, norme, source ou validation praticien ;
8. overflow horizontal = 0 aux viewports 390 / 768 / 1280+ ;
9. console/page errors = 0 sur le scénario de certification ;
10. comparaison BEFORE/AFTER documentée + score visuel explicite.

## RÉFÉRENCE VISUELLE

![Référence R15bis UI/UX](../assets/cephalo/r15bis-ui-reference.jpg)

### À reprendre

- top navigation claire avec destinations majeures ;
- séparation forte `viewer` / `résultats` ;
- panneaux de résultats avec titres + icônes ;
- tableaux compacts libellé / valeur ;
- badge de complétude/état seulement s’il est dérivé d’un état réel ;
- hiérarchie visuelle forte et faible densité cognitive.

### À ne pas reprendre

- dark theme comme identité finale ;
- couleurs arbitraires hors tokens Digital Crown ;
- faux écrans ou fausses destinations ;
- métriques mockées dans le runtime ;
- duplication d’informations déjà exposées proprement par R15 ;
- style “dashboard générique” si cela réduit la lisibilité clinique.

## BEFORE OBLIGATOIRE

Baseline exacte : `3dbab4e1fe722265932799eff01d4de8de252da9`.

Workflow : `.github/workflows/cephalo-r15bis-before.yml`.

Méthode : réutiliser le harness R15 AFTER certifié sur la baseline exacte ; conserver son `report.json` brut inchangé et ajouter `r15bis-before-metadata.json` pour qualifier explicitement cette capture comme BEFORE R15bis. Un second harness read-only complète la preuve par une capture du viewer Step 1, toujours exécutée sur le même SHA produit exact.

### Preuve BEFORE déjà vérifiée — chaîne clinique R15

Run `Cephalo R15bis BEFORE #4` : SUCCESS sur le HEAD de démarrage `ce8b1cf9dfd054d46ff66f7a180c22102cf43fe8`.

Artifact : `cephalo-r15bis-before-exact-master`.

Contrat observé :
- `baselineProductHead = 3dbab4e1fe722265932799eff01d4de8de252da9` ;
- viewports exacts `390x844`, `768x1024`, `1280x900` ;
- `invalidCount = 0` ;
- `blockedExternalRequests = []` ;
- console errors = 0 ;
- page errors = 0 ;
- overflow horizontal = 0 ;
- R11/R12/R13/R14, données manquantes, contradictions, contre-indications et action praticien visibles ;
- aucune fausse validation ni action clinique locale.

Hauteur document BEFORE :

| viewport | Step 3 | Step 4 |
| --- | ---: | ---: |
| 390×844 | 4585 px | 4455 px |
| 768×1024 | 3328 px | 3012 px |
| 1280×900 | 2378 px | 1955 px |

### Audit visuel BEFORE

**Navigation**
- header réel : `Actuel / Historique / Sauvegarder` ;
- workflow réel : `Céphalométrie / Moulages / Synthèse clinique / Documents & stratégie` ;
- aucune destination produit supplémentaire ne sera inventée ;
- à 390 px le stepper reste contenu mais dépend d’un scroll horizontal interne.

**Chaîne R11 → R14**
- 390 px : quatre cartes empilées verticalement ; la première fenêtre est presque entièrement consommée par l’introduction + les quatre stades ;
- 768 px : grille 2×2 ;
- 1280 px : grille 4×1 ;
- les états sont corrects et traçables, mais leur représentation est surdimensionnée par rapport à leur rôle de navigation scientifique.

**Panneau sélectionné**
- contenu correct : résumé, gates, provenance, action praticien, données manquantes, contradictions, contre-indications ;
- aucune information clinique ne doit disparaître ;
- densité excessive : plusieurs cartes imbriquées, beaucoup de padding, mêmes informations répétées entre sélecteur de stade et détail.

**Actions**
- `Sauvegarder`, navigation d’étape et actions documentaires existantes restent les seules actions ;
- `Action praticien` R15 est informative quand le backend la déclare indisponible ; aucun faux CTA ne sera créé.

**Responsive / lisibilité**
- point positif : overflow document horizontal déjà nul ;
- problème principal : densité verticale et répétition, pas une casse de layout ;
- sur 390 px, le détail scientifique utile commence trop bas ;
- sur 1280 px, le bloc R15 monopolise la majorité du premier viewport avant les mesures de Step 3.

**Score BEFORE argumenté : 6,4/10**
- hiérarchie : 6/10 ;
- lisibilité : 7/10 ;
- densité : 4,5/10 ;
- cohérence Digital Crown : 7,5/10 ;
- séparation navigation / contenu : 6/10 ;
- responsive : 6,5/10 ;
- sécurité sémantique clinique : 9/10.

Le score est visuel/HFE uniquement ; il ne note pas la validité scientifique.

### Complément BEFORE viewer

Le harness `frontend/scripts/capture-cephalo-r15bis-before-viewer.mjs` capture Step 1 sur le même SHA produit, aux mêmes trois viewports, avec métriques de bounding box, ratio de surface, overflow, console et page errors.

**Gate : aucune modification UI avant SUCCESS de ce complément.**

## GOAL VISUEL FIGÉ AVANT IMPLÉMENTATION

### Hiérarchie cible

1. header du studio compact, lisible, avec patient + vues réelles + sauvegarde ;
2. stepper clinique compact, clairement secondaire au contenu ;
3. Step 1 : viewer conserve la priorité visuelle et gagne l’espace horizontal disponible sur desktop ;
4. Step 3/4 : chaîne R11→R14 devient un rail de statut compact, puis un panneau sélectionné hiérarchisé ;
5. mesures et synthèses restent sous le panneau scientifique, avec valeurs plus compactes et moins de cartes imbriquées ;
6. mobile : ordre de lecture naturel, aucune suppression de preuve et aucun mur de quatre grandes cartes.

### Mockup structurel — desktop

```text
┌ Studio Céphalométrique · Patient ───────────── Actuel | Historique | Sauvegarder ┐
├ 1 Céphalométrie  ›  2 Moulages  ›  3 Synthèse clinique  ›  4 Documents          ┤
│                                                                                   │
│ STEP 1                                                                            │
│ ┌──────────────────────────── VIEWER RADIO DOMINANT ────────────────────────────┐ │
│ │ tracé + contrôles existants, aucun nouvel état clinique                      │ │
│ └───────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                   │
│ STEP 3 / 4                                                                        │
│ ┌ Chaîne clinique scientifique ───────────────────────────── 7 blocages actifs ┐ │
│ │ [R11 Diagnostic] [R12 Problèmes] [R13 Options] [R14 Validation]             │ │
│ ├─────────────────────────────────────┬─────────────────────────────────────────┤ │
│ │ Résumé + gates visibles             │ Provenance                             │ │
│ │                                     │ Action praticien / état backend         │ │
│ ├─────────────────────────────────────┴─────────────────────────────────────────┤ │
│ │ Données manquantes | Contradictions | Contre-indications                     │ │
│ └───────────────────────────────────────────────────────────────────────────────┘ │
│ [Analyse COM / Steiner / Tweed]                                                   │
│ ┌ Mesures compactes libellé / valeur ─┐ ┌ Synthèse descriptive / notes ───────┐ │
│ └──────────────────────────────────────┘ └──────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────────────────┘
```

### Mockup structurel — mobile 390

```text
Studio Céphalométrique
Patient
[Actuel | Historique] [Sauvegarder]

[1 Céphalo] [2 Moulages] [3 Synthèse] [4 Documents]  ← rail interne scrollable

Chaîne clinique scientifique                    [7 blocages]
[R11] [R12] [R13] [R14]                         ← rail compact, pas 4 cartes empilées

Stade sélectionné
Résumé
Blocages
Provenance
Action praticien
Données manquantes / Contradictions / Contre-indications

Analyse
Mesures compactes
Synthèse / notes
```

## MAPPING TOKENS / COMPOSANTS

Aucun nouveau système visuel parallèle.

| rôle | source autorisée |
| --- | --- |
| fond page | `P.bg` |
| surface principale | `P.bgPanel` |
| surface secondaire | `P.bgCard` |
| champs / sous-sections | `P.bgInput` |
| bordures | `P.border` |
| texte | `P.text` |
| texte secondaire | `P.textMuted` / `P.textDim` |
| sélection / navigation | `P.accent` |
| succès système | `P.accentSuccess` |
| avertissement système | `P.accentWarning` |
| erreur / blocage | `P.accentError` |
| profondeur | `P.shadow` / `P.shadowLg` |

Composants conservés et réorganisés : `CephaloWorkspace`, `StepTab`, `ClinicalScientificStudio`, `Step3Clinical`, `Step4Documents`, `Step1Cephalo`.

Le viewer radiographique peut conserver son fond sombre fonctionnel interne ; **le chrome produit autour du viewer reste Digital Crown**. Aucun dark theme global R15bis.

## IMPLÉMENTATION AUTORISÉE

- layout, spacing, typographie, cartes, tableaux, sections, icônes ;
- navigation uniquement vers routes réelles ;
- responsive/adaptation viewer + panneau latéral ;
- regroupement visuel des informations existantes ;
- amélioration accessibilité clavier/ARIA/touch si nécessaire ;
- réutilisation stricte des tokens et composants Digital Crown quand disponibles.

## HORS SCOPE / INTERDITS

- aucune modification des formules céphalométriques ;
- aucune modification COM ou CRANIOM ;
- aucune nouvelle norme ni interprétation ;
- aucune modification du contrat R11/R12/R13/R14 ;
- aucune auto-validation praticien ;
- aucun PDF/restitution R16 ;
- aucun déploiement Vercel sans autorisation explicite.

## AFTER / CERTIFICATION

Après implémentation :

`AFTER 390 / 768 / 1280+ → comparaison avec BEFORE → overflow → console/page errors → interactions essentielles → clavier/touch → score visuel`

Le score visuel doit être argumenté sur :
- hiérarchie ;
- lisibilité ;
- densité ;
- cohérence ;
- séparation viewer/résultats ;
- responsive ;
- fidélité à Digital Crown.

Aucun “10/10” sans captures et comparaison réelles.

## NEXT EXACT

Fermer le complément BEFORE viewer sur la baseline `3dbab4e1fe722265932799eff01d4de8de252da9`, intégrer ses métriques au présent audit, puis seulement modifier les fichiers UI selon le mockup structurel figé ci-dessus.

## SÉQUENCE RESTANTE CÉPHALO

`R15bis BEFORE viewer → implémentation R15bis → AFTER/certification → comparaison/corrections → closeout R15bis → R16 PDF/restitution → R17 certification/closeout`
