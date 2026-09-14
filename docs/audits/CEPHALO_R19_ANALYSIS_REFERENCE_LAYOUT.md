# CEPHALO R19 — ANALYSIS REFERENCE LAYOUT

## Goal

Recomposer l'étape Céphalométrie selon le mockup validé par le cabinet, **uniquement pour l'agencement et le niveau de détail** : téléradio/tracé à gauche, sélecteur d'analyse, tableau de mesures à droite, détail explicatif de la mesure sélectionnée et liaison visuelle mesure ↔ construction.

Le thème du mockup n'est PAS une source de design. Digital Crown conserve ses tokens `getCephaloPalette()`, sa typographie, ses couleurs, ses composants et ses états.

## Référence visuelle verrouillée

- Source : mockup fourni et explicitement validé par le cabinet le 2026-09-14.
- Dimensions source : `1495 × 1052`.
- SHA-256 source : `ae44a5052cc8feb8805f885bc1c56c74d1a5f4c6378d02c557012da3643cf060`.
- Usage autorisé : structure de page, hiérarchie, densité et détail du panneau d'analyse.
- Usage interdit : copier le thème, inventer une norme, inventer une mesure ou changer une convention scientifique pour ressembler au mockup.

## BEFORE

Le BEFORE produit reste la preuve R18 certifiée. Aucun fichier produit céphalométrique n'avait changé entre le merge R18 `71a087391d175ffe6f3a9e4e7962c833bab23fa5` et le départ R19. La dérive de `master` observée pendant R19 jusqu'à `38dc018426d93437c6a77e9d5856c529096dda5a` ne touche pas le produit céphalométrique ; depuis la base PR `e7198b274438ec05373e8ebee9c84fc80e409149`, elle modifie seulement `.github/workflows/ci.yml`.

Référence BEFORE visuelle : R18 Tracing AFTER #7, run `34889128064`, 15/15 états valides sur `390×844`, `768×1024`, `1280×900`, zéro overflow horizontal, score HFE R18 enregistré `9.4/10`.

## Contrat R19

1. Analyses séparées : `Tous | Steiner | Tweed | McNamara | COM | Ricketts`.
2. `COM` n'est plus un alias de McNamara.
3. À partir du desktop large, le panneau d'analyse est voisin de la téléradio ; aux viewports plus petits il est empilé pour préserver la lisibilité et éviter l'overflow.
4. Chaque ligne du tableau sélectionnée/survolée focalise sa construction géométrique sur la téléradio.
5. Le panneau n'invente aucune donnée : valeur absente = `NC`, norme absente du payload = `—`.
6. L'écart n'est calculé côté UI que si `value/valeur` et `norm_mean` existent dans le résultat ; aucune moyenne n'est codée en dur.
7. Les constructions COM réutilisent strictement les conventions déjà versionnées dans `backend/services/cephalo_constructions.py` et `cephalo_engine.py` : Frankfort Po–Or, verticale de Nasion perpendiculaire à Frankfort, projections A′/B′, composantes surplomb/recouvrement, axes incisifs et plan mandibulaire.
8. McNamara conserve ses constructions R18 ; ses valeurs restent `NC` tant qu'aucun résultat backend versionné ne fournit `Co_A`, `Co_Gn`, `ANS_Me`.
9. Ricketts conserve le contrat R18, notamment la ligne E et les invariants source-strict.
10. La base historique R18 reste immuable : `CephaloTracingLayerBase.tsx` blob `a0fcc90ca9f872c4bdcad927c10585003989990f` ; `Step1CephaloBase.tsx` blob `4349ed3c979f2974a5432146106f2ba0a047fa1f`, identique au `Step1Cephalo.tsx` de la base R19.
11. En COM, les landmarks N/A/B sont volontairement retirés **uniquement du rendu Base R18** afin d'empêcher les projections McNamara historiques non conditionnées de fuir dans COM ; les constructions COM utilisent toujours les landmarks originaux dans l'overlay R19.

## AFTER certifié produit

Produit candidat : `493dd290eec8bd004ec928ebd100707b56099b7c`.

Workflow `Cephalo R19 Analysis Reference AFTER` #7 : run `34903739212` — **SUCCESS**.

Artefact : ID `10371414961`, digest `sha256:8a4c0c2b286d9754b2ec2f1b8c03151f9d6e9bbaf836a8218928e43925b576c3`.

Contrat observé dans `report.json` :

- `productHead=493dd290eec8bd004ec928ebd100707b56099b7c` ;
- `invalidCount=0` ;
- `blockedExternalRequests=[]` ;
- 3 viewports × 6 modes = **18/18 états valides**, tous au premier essai ;
- `horizontalOverflow=false` dans les 18 états ;
- `pageErrors=0`, `consoleErrors=0` ;
- COM : `panelRows=10`, `comConstructionCount=15`, sélection `I_Francfort` synchronisée ;
- fuite historique McNamara en COM : `legacyMcNamaraLeakCount=0` sur les 3 viewports ;
- McNamara conserve ses 3 marqueurs historiques attendus dans son propre mode ;
- Ricketts : construction dédiée détectée ; Steiner/Tweed restent isolés ;
- test focalisé `CephaloAnalysisWorkbenchPanel` : étape CI **SUCCESS** ;
- capture exact-head et vérification du contrat AFTER : étapes CI **SUCCESS**.

Les regressions visuelles historiques restent vertes sur ce même produit candidat : Cephalo R15 AFTER #94 **SUCCESS**, R15bis AFTER #55 **SUCCESS**, R1 AFTER #64 **SUCCESS**.

## Comparaison visuelle avec le mockup

Inspection manuelle de l'artefact R19 #7 sur les mêmes viewports :

- `1280×900` : téléradio/tracé à gauche et panneau d'analyse à droite, proportions et hiérarchie cohérentes avec le mockup ; sélecteur d'analyse au-dessus du tracé ; tableau `Mesure / Valeur / Norme / Écart` et carte détail présents ;
- `768×1024` : panneau empilé, tableau lisible sans débordement ;
- `390×844` : colonnes compactées, valeurs lisibles, aucun overflow horizontal ;
- thème : surfaces, bordures, accent, textes et états proviennent des tokens Digital Crown ; le thème visuel du mockup n'est pas copié ;
- COM : aucune fuite `McNamara / A' / B'` après correction.

**Score visuel R19 : 9.4/10.** L'agencement et le niveau de détail suivent fortement la référence ; les différences restantes sont intentionnelles et relèvent du thème Digital Crown et du responsive, pas d'une divergence de structure.

## Non-goals

- Aucun changement de formule backend.
- Aucune nouvelle norme clinique.
- Aucun changement de calibrage.
- Aucun déploiement Vercel.

## État

`CANDIDAT CLOSEOUT PRÉ-MERGE — AFTER produit certifié ; CI générale et certifications transverses du HEAD documentaire à confirmer avant merge.`
