# CÉPHALOMÉTRIE — RÉCUPÉRATION PRIMAIRE RICKETTS 1981

**Date :** 2026-09-12  
**Parent scientifique :** `docs/CEPHALO_MEASUREMENT_EVIDENCE_RECOVERY.md`  
**Objet :** dette COM `FMA 26° ±4°`

## GOAL

Verrouiller la meilleure preuve primaire disponible pour la ligne historique COM `FMA 26° ±4°` sans transformer cette valeur en norme patient tant que la construction géométrique source-spécifique n'est pas certifiée.

## SOURCE PRIMAIRE

Robert M. Ricketts. *Perspectives in the clinical application of cephalometrics: The first fifty years.* Angle Orthodontist. 1981;51(2):115-150. PMID `6942666`. DOI `10.1043/0003-3219(1981)051<0115:PITCAO>2.0.CO;2`.

La citation bibliographique et le DOI ont été recoupés sur PubMed.

### Preuve numérique et règle d'âge

Dans le **“Cue Sheet for Ricketts' Summary Descriptive Analysis”**, Ricketts décrit le facteur :

- `Mandibular plane (FH to Sub. Go.-M.)` ;
- valeur à 3 ans : `28° ±4°` ;
- évolution : diminution de `1°` tous les 3 ans jusqu'à la maturité ;
- valeur à 18 ans : `23°`.

La valeur à 9 ans découle donc directement de la règle publiée :

`28° - 2° = 26°`, avec la dispersion historique `±4°`.

**Décision :** `26° ±4° à 9 ans` est désormais **numériquement source-locké sur une source primaire Ricketts**.

## CONSTRUCTION GÉOMÉTRIQUE

La même source précise que la construction est le **vrai plan de Francfort** et un plan mandibulaire **Subgonion–Menton**. Ricketts distingue explicitement le vrai Porion du repère de tige auriculaire.

Digital Crown ne doit donc pas remplacer silencieusement cette construction par :

- `Go-Me` ;
- `Go-Gn` ;
- un Francfort construit depuis un Porion non équivalent au `true Porion` de la source.

Le gate devient :

`RICKETTS_TRUE_FH_SUBGONION_MENTON_EXACT_REQUIRED`.

## VALIDATION CROISÉE

Une publication peer-reviewed récente utilisant l'analyse de Ricketts confirme la référence `26° ±4°`, mais l'implémente avec une convention géométrique moderne différente (`Po-Or / Go-Gn`). Cette divergence renforce la nécessité de conserver séparément :

`valeur historique source-lockée != construction Digital Crown certifiée`.

Référence de corroboration : Ravelo et al., *BioMed Research International*, 2021, article PMC8241511.

## ÉTAT DIGITAL CROWN

- numérique `26° ±4° à 9 ans` : **SOURCE_LOCKED** ;
- règle d'âge : **SOURCE_LOCKED** ;
- construction exacte `true FH / Subgonion-Menton` : **BLOCKED jusqu'à implémentation/versionnage/test** ;
- activation classification patient : **FALSE** ;
- diagnostic/indication/traitement : **aucun changement**.

## NEXT EXACT

1. définir et versionner `true Porion`, `Subgonion` et `Menton` selon le contrat Ricketts ;
2. implémenter la construction `true FH / Subgonion-Menton` sans réutiliser silencieusement `Go-Me` ou `Go-Gn` ;
3. ajouter des goldens géométriques et la règle d'âge ;
4. seulement après revue scientifique dédiée, décider si une référence patient peut être activée.

**BLOCKED != DROPPED.**
