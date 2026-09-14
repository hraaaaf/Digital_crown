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

Le BEFORE produit est la preuve R18 certifiée, car aucun fichier produit céphalométrique n'a changé entre le merge R18 `71a087391d175ffe6f3a9e4e7962c833bab23fa5` et le master de départ R19 `3b22f2a0dbb5b778a53265b97ad3029eeb88e656`.

Preuve de comparaison GitHub : 2 commits d'écart ; les changements céphalo sont exclusivement les documents de closeout R18. Aucun fichier `frontend/src/features/ortho/*` ni moteur céphalométrique n'a dérivé.

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

## Succès observable

- 6 boutons d'analyse, chacun sélectionnable.
- Panneau d'analyse synchronisé avec le tracé.
- COM : 10 lignes explicatives ; sélection `I / Francfort` focalise au minimum Francfort + axe U1.
- Aucun résultat clinique inventé.
- Même fixture déterministe que la lignée R18 ; AFTER sur 390/768/1280.
- `pageErrors=0`, `consoleErrors=0`, `horizontalOverflow=false`.
- Tests frontend et build verts.
- Comparaison visuelle au mockup de référence avant closeout, avec score visuel documenté après inspection des artefacts.

## Non-goals

- Aucun changement de formule backend.
- Aucune nouvelle norme clinique.
- Aucun changement de calibrage.
- Aucun déploiement Vercel.

## État

`EN COURS — implémentation / validation AFTER non encore certifiée.`
