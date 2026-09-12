# CÉPHALOMÉTRIE — COM / GÉOMÉTRIES SOURCE-SPÉCIFIQUES

**Date :** 2026-09-12  
**Parent scientifique :** `docs/CEPHALO_MEASUREMENT_EVIDENCE_RECOVERY.md`  
**Portée :** fermeture géométrique Ricketts 1981 + gate Tweed historique

## GOAL

Réduire la dette COM sans confondre une géométrie pratique du runtime avec une construction historique source-spécifique.

Succès de ce lot :

- rendre le FMA Ricketts 1981 calculable avec `Po-Or / SubGo-Me` lorsque `SubGo` est explicitement posé et validé par le praticien ;
- interdire `Go` comme alias de `SubGo` ;
- conserver Tweed fail-closed tant que sa tangente basilaire et son Frankfort historique ne sont pas représentés selon un contrat dédié ;
- n'activer aucune norme, classification, finding, diagnostic, indication ou option thérapeutique.

## RICKETTS 1981 — CHEMIN SOURCE-SPÉCIFIQUE

### Preuve primaire déjà verrouillée

Ricketts RM. *Perspectives in the clinical application of cephalometrics: the first fifty years.* Angle Orthod. 1981;51(2):115-150. DOI `10.1043/0003-3219(1981)051<0115:PITCAO>2.0.CO;2`.

Le cue sheet récupéré donne le plan mandibulaire comme vrai Frankfort horizontal versus `Sub. Go.-M.` avec `28±4°` à 3 ans puis diminution de 1° tous les 3 ans, soit `26±4°` à 9 ans.

Des sources anatomiques indépendantes définissent le Subgonion sur le bord inférieur de l'angle mandibulaire. Il ne s'agit donc pas du Gonion générique.

### Contrat Digital Crown

Construction versionnée :

`RICKETTS_1981_FMA_TRUE_FH_SUBGO_ME_V1`

Dépendances :

- `Po` ;
- `Or` ;
- `Me` ;
- `SubGo` explicite.

Le modèle SRPose38 ne fournit pas `SubGo`. Digital Crown accepte donc uniquement, pour cette construction, un `SubGo` :

- d'origine `MANUAL` ;
- `CLINICIAN_VALIDATED` ;
- avec `validated_by` et `validated_at` ;
- appartenant à la même image source que Po/Or/Me.

Le runtime refuse :

- `Go → SubGo` ;
- `Go-Me → SubGo-Me` ;
- `Go-Gn → SubGo-Me` ;
- axes dégénérés ;
- points provenant d'images différentes ;
- SubGo automatique ou manuel non validé.

Une fois ces gates satisfaits, Digital Crown peut produire **le FMA brut en degrés seulement**. La référence historique `26±4° à 9 ans` reste séparée et aucune classification patient n'est activée par ce lot.

## TWEED — GATE SOURCE-EXACT MAINTENU

La littérature Tweed décrit le plan mandibulaire comme une **tangente au bord inférieur de la mandibule**, et non comme un simple segment Go-Me. Des descriptions de la méthode précisent une construction passant antérieurement par Menton et tangentant/postérieurement le bord inférieur dans la région goniale.

Le Frankfort historique de Tweed possède lui aussi une convention propre ; un `Po-Or` générique ne doit pas être présenté comme automatiquement équivalent sans preuve de construction.

Décision :

- `Go-Me` reste interdit comme « Tweed exact » ;
- `Go-Gn` reste interdit comme « Tweed exact » ;
- le Po-Or Digital Crown générique n'est pas déclaré source-exact Tweed ;
- IMPA `90±5°` et la règle dynamique Tweed restent source-lockés numériquement mais géométriquement bloqués ;
- prochaine fermeture : contrat de tracing manuel/audité dédié au Frankfort historique et à la tangente basilaire Tweed.

## TESTS FAIL-CLOSED

`backend/tests/test_cephalo_com_source_geometry.py` couvre :

- Ricketts positif avec SubGo manuel validé ;
- SubGo absent malgré Go présent ;
- SubGo non validé ;
- pseudo-SubGo automatique ;
- mélange d'images ;
- axes dégénérés/non finis ;
- production du FMA brut sans classification ;
- maintien du blocker Tweed et interdiction des substitutions.

## ÉTAT APRÈS CE LOT

- Ricketts FMA : `SOURCE_LOCKED_MANUAL_CONSTRUCTION_AVAILABLE` ;
- Tweed IMPA/FMA : `SOURCE_LOCKED_CONSTRUCTION_BLOCKED` / `SOURCE_LOCKED_RULE_CONSTRUCTION_BLOCKED` ;
- `patient_classification_references()` : toujours vide ;
- aucune mesure supprimée ;
- aucune approximation silencieuse.

## NEXT EXACT

1. certifier le chemin Ricketts exact-head CI/T2 ;
2. verrouiller un contrat de tracing source-spécifique Tweed, ou documenter l'impossibilité image-par-image lorsque le repère historique requis n'est pas observable ;
3. seulement après source + géométrie + contexte + tests, évaluer séparément l'activation normative ;
4. poursuivre la récupération primaire U1-FH et CRANIOM sans mélanger leurs conventions.