# CÉPHALOMÉTRIE — REGISTRE DES CONSTRUCTIONS

**Statut : Lot 4 actif**  
**Parent canonique :** `docs/CEPHALO_DIAGNOSTIC_SPEC.md`  
**Contrat landmarks :** `docs/SRPOSE38_LANDMARK_CONTRACT.md`

## GOAL

Versionner séparément chaque construction géométrique utilisée par une analyse clinique afin qu'aucune formule ne dépende d'une convention implicite.

## SOURCE HISTORIQUE CRANIOM

La méthode historiquement appelée « COM » dans Digital Crown correspond au périmètre de la méthode **C.R.A.N.I.O.M.** décrite par René Bonnefont, Jean Casteigt, Jean‑François Ernoult et Olivier Sorel.

Source publiée :
- *A new method for the utilization of cephalometric measurements in orthodontics or how standard deviations can sometimes be the practitioner's false friends (Part 1)*, Journal of Dentofacial Anomalies and Orthodontics, 2010, 13(4):385‑400, DOI `10.1051/odfen/2010406`.

Important : cette référence décrit une **méthode spécifique** et son échantillon de référence. Elle ne transforme pas ses valeurs en normes universelles.

## REGISTRE CERTIFIABLE AVEC SRPOSE38

### `FH_PO_OR_V1`

**Nom :** plan de Francfort anatomique.  
**Dépendances :** `Po`, `Or`.  
**Définition :** droite passant par Porion et Orbitale.  
**Orientation numérique :** vecteur unitaire `Po → Or`, utilisé comme direction antérieure positive.  
**Échec :** `NOT_COMPUTABLE` si Po/Or absents ou confondus.  
**État :** `VERIFIED_GEOMETRY`.

### `CRANIOM_A_PRIME_V1`

**Nom :** A'.  
**Dépendances :** `A` + `FH_PO_OR_V1`.  
**Définition :** projection orthogonale du point A sur le plan de Francfort.  
**État :** `SOURCE_VERIFIED`.

### `CRANIOM_B_PRIME_V1`

**Nom :** B'.  
**Dépendances :** `B` + `FH_PO_OR_V1`.  
**Définition :** projection orthogonale du point B sur le plan de Francfort.  
**État :** `SOURCE_VERIFIED`.

### `CRANIOM_AB_PRIME_V1`

**Nom :** segment algébrique A'B'.  
**Dépendances :** `A`, `B`, `Po`, `Or`, calibration mm/px.  
**Définition :** distance signée entre les projections orthogonales de A et B sur Francfort.  
**Convention :** positive lorsque A est antérieur à B selon `Po → Or`, négative lorsque A est postérieur à B.  
**Formule équivalente :** `dot(A - B, unit(Po→Or)) × mm_per_pixel`.  
**État :** `SOURCE_VERIFIED`.

La publication CRANIOM décrit explicitement A' et B' comme projections orthogonales de A et B sur Francfort et utilise le signe positif quand A est en avant de B.

### `NASION_VERTICAL_FH_V1`

**Nom :** verticale par Nasion dans le repère Francfort horizontalisé.  
**Dépendances :** `N` + `FH_PO_OR_V1`.  
**Définition numérique :** droite passant par N et perpendiculaire à Francfort.  
**État :** `SOURCE_COMPATIBLE_GEOMETRY`.

### `CRANIOM_A_TO_N_VERTICAL_V1`

**Dépendances :** `A`, `N`, `Po`, `Or`, calibration.  
**Définition :** distance AP signée du point A à `NASION_VERTICAL_FH_V1`.  
**Formule :** `dot(A - N, unit(Po→Or)) × mm_per_pixel`.  
**Convention :** positif en avant de Nasion, négatif en arrière.  
**État :** `SOURCE_COMPATIBLE_GEOMETRY`.

### `CRANIOM_B_TO_N_VERTICAL_V1`

Même définition avec B.  
**État :** `SOURCE_COMPATIBLE_GEOMETRY`.

### `CRANIOM_S_TO_N_VERTICAL_DEPTH_V1`

**Dépendances :** `S`, `N`, `Po`, `Or`, calibration.  
**Définition :** distance géométrique de S à la verticale par Nasion, mesurée parallèlement à Francfort.  
**Formule :** `abs(dot(S - N, unit(Po→Or))) × mm_per_pixel`.  
**État :** `GEOMETRY_VERIFIED_SOURCE_SEMANTICS_TO_CONFIRM`.

## IMPLÉMENTATION

Les constructions ci-dessus sont matérialisées dans `backend/services/cephalo_constructions.py`. `backend/services/cephalo_engine.py` est branché sur ces fonctions pour `Situation_A`, `Situation_B`, `Decalage_A_B`, `Profondeur_Faciale` et les projections visuelles A'/B'/N'.

Les anciennes `mcnmara_projections` calculées côté client restent acceptées dans l'API pour compatibilité mais **ne peuvent plus modifier une mesure backend**. Les coordonnées sources des landmarks sont la seule source de vérité géométrique.

## CONVENTIONS MANDIBULAIRES — GATE EXPLICITE

Le terme « plan mandibulaire » n'est pas une construction universelle. Les sources sérieuses décrivent plusieurs variantes :

- un plan `Go-Me` est couramment utilisé dans certains schémas/logiciels ;
- Downs est classiquement décrit par une **tangente au bord inférieur mandibulaire** ;
- Tweed est également décrit dans la littérature par une tangente au bord inférieur, avec Menton antérieurement et la région goniale postérieurement ;
- d'autres analyses utilisent `Go-Gn`.

Sources de contrôle :
- Downs WB. *Variations in facial relationships: Their significance in treatment and prognosis.* Am J Orthod. 1948;34(10):812‑840. DOI `10.1016/0002-9416(48)90015-3`.
- Tweed CH. *The Frankfort-mandibular plane angle in orthodontic diagnosis, classification, treatment planning, and prognosis.* Am J Orthod Oral Surg. 1946;32:175‑230. DOI `10.1016/0096-6347(46)90001-4`.
- Shindoi et al./comparative literature summarized in *Assessing lower incisor inclination change: a comparison of four cephalometric methods* (peer-reviewed): Downs/Tweed use a tangent to the lower mandibular border, whereas other analyses use Go-Me or Go-Gn constructions.

### Conséquence Digital Crown

Le champ historique `Angle_de_Tweed` est actuellement calculé avec `Go-Me`. **Il reste une mesure géométrique legacy, pas une mesure Tweed certifiée**, tant que la convention exacte de la fiche historique `26° ± 4°` n'est pas reliée à une source autoritative.

Même règle pour `IMPA` : l'axe incisif est disponible, mais la construction du plan mandibulaire doit être rattachée explicitement à l'analyse choisie avant toute norme/interprétation.

## CONSTRUCTIONS NON COMPUTABLES OU NON CERTIFIÉES

### CRANIOM `Gi/Gs`

La méthode CRANIOM publiée décrit pour certaines mesures verticales des points goniaques inférieur/supérieur `Gi/Gs`. SRPose38 fournit un unique `Go`.

**Décision :** aucune substitution `Go ↔ Gi/Gs` silencieuse. Ces mesures restent `NOT_COMPUTABLE` tant qu'une construction compatible n'est pas prouvée ou qu'une saisie manuelle explicite n'est pas ajoutée.

### A''B'' / regard horizontal

CRANIOM distingue `A'B'` projeté sur Francfort et `A''B''` projeté sur le plan du regard horizontal. Digital Crown n'a pas actuellement de capture standardisée du regard horizontal liée à la photographie de profil.

**Décision :** `A''B'' = NOT_COMPUTABLE` jusqu'à implémentation/validation du protocole photo + orientation naturelle de tête.

## TESTS GOLDEN DU LOT 4

1. Francfort horizontal : A=+5 mm devant B → A'B' = +5 mm.
2. Francfort incliné : rotation rigide de tous les points ne change pas A'B'.
3. A derrière B → signe négatif.
4. translation globale → valeurs invariantes.
5. changement d'échelle pixel + calibration compensatrice → même valeur mm.
6. Po=Or → `NOT_COMPUTABLE`.
7. calibration absente, non finie ou ≤0 → `NOT_COMPUTABLE`.
8. A/B/N/S manquant → seulement les mesures dépendantes deviennent `NOT_COMPUTABLE`.
9. projection fournie par le client → aucun effet sur la mesure backend.

Tests :
- `backend/tests/test_cephalo_craniom_constructions.py`
- `backend/tests/test_cephalo_craniom_runtime_parity.py`

## NEXT EXACT

Obtenir la preuve CI des golden tests puis séparer explicitement les constructions `TWEED_MP`, `DOWNS_MP` et les besoins `CRANIOM_Gi/Gs` avant d'activer IMPA/FMA comme mesures attribuées à une école.