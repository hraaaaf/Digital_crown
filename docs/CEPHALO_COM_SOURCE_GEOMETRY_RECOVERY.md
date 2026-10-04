# CÉPHALOMÉTRIE — COM / GÉOMÉTRIES SOURCE-SPÉCIFIQUES

**Date :** 2026-09-12  
**Parent scientifique :** `docs/CEPHALO_MEASUREMENT_EVIDENCE_RECOVERY.md`  
**Portée :** fermeture géométrique Ricketts 1981 + gate Tweed historique

## GOAL

Réduire la dette COM sans confondre une géométrie pratique du runtime avec une construction historique source-spécifique.

Succès de ce lot :

- rendre le FMA Ricketts 1981 calculable uniquement lorsque le `true Frankfort` et `SubGo-Me` sont représentés par des repères source-spécifiques explicitement tracés et validés ;
- interdire les substitutions silencieuses depuis les repères SRPose38 génériques `Po`, `Or`, `Go`, `Me` ;
- conserver Tweed fail-closed tant que sa tangente basilaire et son Frankfort historique ne sont pas représentés selon un contrat dédié ;
- n'activer aucune norme, classification, finding, diagnostic, indication ou option thérapeutique.

## RICKETTS 1981 — CHEMIN SOURCE-SPÉCIFIQUE

### Preuve primaire verrouillée

Ricketts RM. *Perspectives in the clinical application of cephalometrics: the first fifty years.* Angle Orthod. 1981;51(2):115-150. DOI `10.1043/0003-3219(1981)051<0115:PITCAO>2.0.CO;2`.

Le cue sheet récupéré donne le plan mandibulaire comme **true Frankfort horizontal** versus `Sub. Go.-M.` avec `28±4°` à 3 ans puis diminution de 1° tous les 3 ans, soit `26±4°` à 9 ans. Le texte distingue en outre le vrai Frankfort des proxys liés aux ear rods. Digital Crown ne doit donc pas promouvoir son `Po-Or` automatique générique comme équivalent source-exact sans preuve.

`SubGo` est également distinct du Gonion générique. La géométrie source-exacte doit conserver cette distinction.

### Contrat Digital Crown V2

Construction versionnée :

`RICKETTS_1981_FMA_TRUE_FH_SUBGO_ME_V2`

Dépendances source-spécifiques obligatoires :

- `RickettsTruePo` ;
- `RickettsTrueOr` ;
- `RickettsSubGo` ;
- `RickettsMe`.

Pour ce lot, chacun de ces repères doit :

- être d'origine `MANUAL` ;
- être `CLINICIAN_VALIDATED` ;
- porter `validated_by` et `validated_at` ;
- appartenir à la même image source.

Le runtime refuse :

- `SRPose38 Po-Or → Ricketts true Frankfort` ;
- `Go → RickettsSubGo` ;
- `Go-Me → RickettsSubGo-RickettsMe` ;
- `Go-Gn → RickettsSubGo-RickettsMe` ;
- repère source-spécifique automatique non certifié ;
- repère manuel non validé ;
- axes dégénérés ou non finis ;
- points provenant d'images différentes.

Une fois ces gates satisfaits, Digital Crown peut produire **le FMA brut en degrés seulement**. La référence historique `26±4° à 9 ans`, sa règle d'âge et toute classification patient restent séparées et inactives dans ce lot.

## TWEED — GATE SOURCE-EXACT HISTORIQUE (SUPERCÉDÉ POUR LE PRODUIT)

> **Mise à jour canonique 2026-10-03.** Ce gate reste valable uniquement pour toute revendication de reproduction **stricte** du Tweed 1954. Il ne bloque plus le profil produit Digital Crown : la décision clinique du 2026-09-15 a sélectionné et versionné `DC_TWEED_ANATOMICAL_FH_VARIANT = Po_anatomic-Or` avec `TWEED_DC_MP_GO_ME_V1 = Go-Me`. Cette variante doit être nommée comme telle et ne peut hériter silencieusement des normes historiques de la géométrie stricte 1954.

La littérature Tweed décrit le plan mandibulaire comme une **tangente au bord inférieur de la mandibule**, et non comme un simple segment Go-Me. Des descriptions de la méthode précisent une construction passant antérieurement par Menton et tangentant/postérieurement le bord inférieur dans la région goniale.

Le Frankfort historique de Tweed possède lui aussi une convention propre ; un `Po-Or` générique ne doit pas être présenté comme automatiquement équivalent sans preuve de construction.

Décision :

- `Go-Me` reste interdit comme « Tweed exact » ;
- `Go-Gn` reste interdit comme « Tweed exact » ;
- le `Po-Or` Digital Crown générique n'est pas déclaré source-exact Tweed ;
- IMPA `90±5°` et la règle dynamique Tweed restent source-lockés **comme contexte historique uniquement** ; ils ne reçoivent aucune autorité de classification sur la variante DC ;
- le contrat strict historique reste documenté et non sélectionné ; il n'est plus un blocker produit tant que Digital Crown ne revendique pas l'équivalence stricte.

Sources primaires verrouillées pour le gate Tweed :

- Tweed CH. 1946. DOI `10.1016/0096-6347(46)90001-4` ;
- Tweed CH. *The Frankfort-mandibular incisor angle (FMIA) in orthodontic diagnosis, treatment planning and prognosis.* Angle Orthod. 1954;24(3):121-169.

## TESTS FAIL-CLOSED

`backend/tests/test_cephalo_com_source_geometry.py` couvre :

- Ricketts positif avec les quatre repères source-spécifiques validés ;
- présence de `Po/Or/Go/Me` SRPose38 génériques sans satisfaction du contrat Ricketts ;
- repère source-spécifique non validé ;
- pseudo-repère source-spécifique automatique ;
- mélange d'images ;
- axes dégénérés/non finis ;
- invariance de l'angle de ligne à l'orientation des vecteurs ;
- production du FMA brut sans classification ;
- maintien de l'interdiction d'équivalence stricte Tweed 1954, tout en validant le contrat produit DC sélectionné séparément.

## ÉTAT APRÈS CE LOT

- Ricketts FMA : `SOURCE_LOCKED_MANUAL_CONSTRUCTION_AVAILABLE`, uniquement via le contrat V2 source-spécifique ;
- Tweed IMPA/FMA produit DC : `SOURCE_LOCKED_SELECTED_DC_CONTRACT_AVAILABLE` ; compensation historique : `SOURCE_LOCKED_RULE_REFERENCE_ONLY_SELECTED_DC_CONTRACT` ;
- `patient_classification_references()` : doit rester vide ;
- aucune mesure supprimée ;
- aucune approximation silencieuse.

## NEXT EXACT

1. conserver Ricketts V2 séparé de Tweed ;
2. exposer Tweed uniquement via `DC_TWEED_ANATOMICAL_FH_VARIANT` et les identités canoniques LOT06 ;
3. conserver `TWEED_1954_STRICT_EAR_ROD_FH` comme variante historique non sélectionnée, sans équivalence silencieuse ;
4. maintenir normes/règles historiques hors classification runtime jusqu'à validation dédiée de compatibilité/applicabilité ;
5. poursuivre la récupération primaire U1-FH et CRANIOM sans mélanger leurs conventions.
