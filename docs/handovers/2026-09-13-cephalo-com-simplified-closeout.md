# CLOSEOUT — Céphalométrie / COM « Analyse simplifiée »

**Date :** 2026-09-13  
**Repo :** `hraaaaf/Digital_crown`  
**Source canonique de reprise :** `docs/handovers/2026-09-12-cephalo-com-simplified-clarified-handover.md`

## GOAL — ATTEINT ET PROUVÉ

Projection dédiée COM exactement conforme au contrat source-sheet verrouillé : **5 mesures dentaires + 5 mesures osseuses**, sans métriques Ricketts/génériques injectées, avec A′B′ documenté selon la construction clinique McNamara/N et sans modifier sa géométrie scalaire déjà correcte.

## ÉTAT VÉRIFIÉ

- PR implémentation : `#460` — MERGED ;
- head candidat certifié : `1e7cccf037b58a518f52e13af619e0773c90b4d7` ;
- master post-merge vérifié : `1e79d236b89a56592128d09451803b9adf4ee0fd` ;
- CI `#3637` : SUCCESS ;
- T2 Runtime Browser `#2587` : SUCCESS ;
- Cabinet Upgrade PostgreSQL `#102` : SUCCESS ;
- Cephalo COM Simplified Visual Certification `#2` : SUCCESS ;
- 6 captures BEFORE/AFTER : 390 / 768 / 1280 px, toutes SUCCESS ;
- aucun déploiement Vercel.

## CONTRAT COM FINAL

### Dentaire — 5

1. Surplomb — mm
2. Recouvrement — mm
3. Incisive inférieure / plan mandibulaire — °
4. Incisive supérieure / Frankfort — °
5. Angle inter-incisif — °

### Osseuse — 5

6. Angle de Tweed / FMA — °
7. A′B′ — mm signé
8. Situation A — mm signé
9. Situation B — mm signé
10. Profondeur faciale — mm

## ÉCARTS CORRIGÉS

- l’UI COM affichait 8/10 mesures : ajout de `A′B′` et `Situation B` ;
- le bloc esthétique Ricketts était visible dans la projection COM : retiré du mode COM ;
- l’evidence graph A′B′ ne dépendait pas de Nasion : `N` est désormais requis ;
- la provenance A′B′ encode explicitement : FH `Po-Or`, McNamara perpendiculaire à FH par N, parallèles par A/B, intersections A′/B′ sur FH, signe positif quand A est antérieur à B ;
- la formule scalaire A′B′ n’a pas été réécrite car elle était déjà mathématiquement correcte.

## TESTS / PREUVES AJOUTÉS

- A′B′ : N manquant => fail-closed ;
- A′B′ : signe positif/négatif ;
- invariance translation ;
- invariance rotation rigide ;
- FH dégénéré => non calculable ;
- Situation A/B : signe et rotation rigide ;
- profondeur faciale : indépendante de A/B et fail-closed ;
- visual cert : BEFORE = 8 mesures + Ricketts ; AFTER = 10 mesures, Ricketts absent, overflow horizontal 0, erreurs console/page 0 aux trois viewports.

## LIMITES CONSERVÉES

- aucune norme/interprétation populationnelle universelle n’est activée par ce closeout ;
- aucune conclusion diagnostique ou thérapeutique automatique n’est créée ;
- les différences de normes historiques restent source-spécifiques ;
- les métriques générales SNA/SNB/ANB/Ricketts restent disponibles hors projection COM dédiée si leur propre contrat l’autorise.

## NEXT EXACT

Reprendre `docs/handovers/2026-09-12-cephalo-r14-to-r15-handover.md` et démarrer **R15 — Studio clinique UX/UI** par audit BEFORE réel, sans modifier l’UI avant Goal + référence/mockup.

## SÉQUENCE RESTANTE CÉPHALO

`R15 studio UX/UI → R16 PDF/restitution → R17 certification/closeout`
