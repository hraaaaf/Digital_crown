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
- Copie technique CRANIOM/ODRADE diffusée sur `slot-concept.com` avec les figures et constructions détaillées.

Important : ces références décrivent une **méthode spécifique** et son échantillon de référence. Elles ne transforment pas ses valeurs en normes universelles.

## REGISTRE

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

CRANIOM décrit les distances A et B à la verticale passant par Nasion dans son repère où Francfort est horizontalisé. L'implémentation numérique ci-dessus matérialise cette verticale sans dépendre de l'orientation du fichier image.

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
**Formule runtime historique :** `abs(dot(S - N, unit(Po→Or))) × mm_per_pixel`.  
**État :** `GEOMETRY_VERIFIED_SOURCE_SEMANTICS_TO_CONFIRM`.

La fiche historique fournie au projet appelle cette grandeur « profondeur faciale ». La géométrie est déterministe ; le rattachement normatif exact reste séparé.

## CONSTRUCTIONS NON CERTIFIÉES

### Plan mandibulaire / Gonion

Le runtime historique utilise `Go-Me`. La littérature montre plusieurs conventions de Gonion. La méthode CRANIOM publiée décrit aussi des points goniaques inférieur/supérieur `Gi/Gs` pour certaines mesures verticales, alors que SRPose38 fournit un unique `Go`.

**Décision :** aucune substitution `Go ↔ Gi/Gs` silencieuse. Les mesures qui exigent Gi/Gs restent `NOT_COMPUTABLE` avec SRPose38 tant qu'une convention compatible n'est pas prouvée.

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
7. calibration absente/≤0 pour mesure linéaire → `NOT_COMPUTABLE`.
8. A/B/N/S manquant → seulement les mesures dépendantes deviennent `NOT_COMPUTABLE`.

## NEXT EXACT

Implémenter ces constructions en fonctions pures puis remplacer dans `cephalo_engine.py` les calculs A'B'/A-Nv/B-Nv/profondeur par le registre testé, sans réactiver aucune norme ni diagnostic.