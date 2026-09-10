# CÉPHALOMÉTRIE — MATRICE ANALYSES → MESURES → LANDMARKS

**Statut : chantier actif / COM seed**  
**Parent canonique :** `docs/CEPHALO_DIAGNOSTIC_SPEC.md`  
**Contrat landmarks :** `docs/SRPOSE38_LANDMARK_CONTRACT.md`

## GOAL

Rendre explicite, pour chaque mesure, la chaîne :

`analyse → mesure → landmarks → construction → unité → calibration → formule → source → statut`

Une mesure sans dépendances satisfaites ou sans formule certifiée reste `NOT_COMPUTABLE` ou `UNVERIFIED`, jamais estimée.

## STATUTS

- `VERIFIED_GEOMETRY` : géométrie/formule vérifiée et testable, mais norme clinique éventuellement séparée.
- `CURRENT_IMPLEMENTATION_CANDIDATE` : comportement actuel du code, à confronter à la définition historique/autoritative de l'analyse.
- `SOURCE_REQUIRED` : définition/norme clinique non encore suffisamment sourcée.
- `NOT_COMPUTABLE` : dépendance indispensable absente.

# COM — MATRICE INITIALE

La fiche clinique historique fournie par le praticien fixe le **périmètre fonctionnel** du COM. Elle ne constitue pas à elle seule une source suffisante pour activer des normes numériques dans le moteur.

| Bloc COM | Mesure | Landmarks SRPose38 nécessaires | Construction | Calibration | État scientifique |
|---|---|---|---|---|---|
| Dentaire | Surplomb | U1/UI (#12), L1/LI (#11), Po (#4), Or (#3) | projection du vecteur incisif sur l'axe de Francfort dans le code actuel | mm requis | `CURRENT_IMPLEMENTATION_CANDIDATE` |
| Dentaire | Recouvrement | U1/UI (#12), L1/LI (#11), Po (#4), Or (#3) | projection du vecteur incisif sur la normale au plan de Francfort dans le code actuel | mm requis | `CURRENT_IMPLEMENTATION_CANDIDATE` |
| Dentaire | I / mandibulaire | L1A (#22), L1/LI (#11), Go (#10), Me (#8) | angle axe incisive mandibulaire / plan mandibulaire Go-Me | non | `VERIFIED_GEOMETRY`, norme COM à sourcer |
| Dentaire | I / Francfort | U1A (#21), U1/UI (#12), Po (#4), Or (#3) | angle axe incisive maxillaire / Francfort Po-Or | non | `VERIFIED_GEOMETRY`, norme COM à sourcer |
| Dentaire | Inter-incisif | U1A (#21), U1/UI (#12), L1A (#22), L1/LI (#11) | angle entre axes incisifs | non | `VERIFIED_GEOMETRY`, norme COM à sourcer |
| Osseux | Angle de Tweed / FMA | Go (#10), Me (#8), Po (#4), Or (#3) | angle plan mandibulaire Go-Me / Francfort Po-Or | non | `VERIFIED_GEOMETRY`, définition COM exacte à confirmer |
| Osseux | Décalage maxillo-mandibulaire A'B' | A (#5), B (#6) + plan de référence à certifier | **construction historique A'/B' non encore certifiée** | mm requis | `SOURCE_REQUIRED` |
| Osseux | Situation maxillaire A / verticale Nasion | A (#5), N (#2), Po (#4), Or (#3) | verticale par Nasion perpendiculaire à Francfort ; distance AP signée de A | mm requis | `CURRENT_IMPLEMENTATION_CANDIDATE` |
| Osseux | Situation mandibulaire B / verticale Nasion | B (#6), N (#2), Po (#4), Or (#3) | verticale par Nasion perpendiculaire à Francfort ; distance AP signée de B | mm requis | `CURRENT_IMPLEMENTATION_CANDIDATE` |
| Osseux | Profondeur faciale S / verticale Nasion | S (#1), N (#2), Po (#4), Or (#3) | distance AP de S à la verticale par Nasion | mm requis | `CURRENT_IMPLEMENTATION_CANDIDATE` |
| Suivi | Tracé 1 / Tracé 2 | mêmes dépendances par mesure | comparaison T1/T2 après gate de comparabilité | selon mesure | `SOURCE_REQUIRED` pour protocole COM de superposition |

## CONCORDANCE AVEC LE MOTEUR ACTUEL

`backend/services/cephalo_engine.py` calcule déjà géométriquement :

- surplomb ;
- recouvrement ;
- IMPA ;
- I/Francfort ;
- inter-incisif ;
- SNA/SNB/ANB ;
- angle de Tweed/FMA ;
- projections A/B liées à Nasion/Francfort ;
- profondeur faciale ;
- Wits ;
- longueurs Co-A et Co-Gn ;
- angle nasolabial ;
- distances lèvres / E-line.

**Important :** la présence d'un calcul dans le code ne certifie pas qu'il correspond exactement à une définition COM/Steiner/Tweed/etc. L'association à une analyse clinique est un gate scientifique séparé.

## INVENTAIRE LEGACY — PREUVE PR #371

Le diff de `backend/services/cephalo_engine.py` supprimé lors du durcissement scientifique PR `#371` confirme que l'ancien moteur COM embarquait localement des normes et diagnostics. Cet inventaire sert uniquement à retrouver l'intention historique ; il **ne réactive aucune norme**.

| Mesure legacy | Ancienne valeur codée | Constat |
|---|---:|---|
| Surplomb | 2,25 ± 0,75 mm | correspond à la plage historique 1,5–3 mm |
| Recouvrement | 2,25 ± 0,75 mm | correspond à la plage historique 1,5–3 mm |
| IMPA | 90° ± 5° | concordant avec la fiche |
| I / Francfort | 107° ± 5° | concordant avec la fiche |
| Inter-incisif | 131° ± 10° | **conflit historique connu** avec une autre valeur frontend ±13 ; à arbitrer par source |
| Angle de Tweed | 26° ± 4° | concordant avec la fiche |
| Situation A enfant | 2,8 ± 3,3 mm | concordant avec la fiche |
| Situation A adulte | 2,3 ± 3,0 mm | **diffère de la fiche fournie : ±3,3** |
| Profondeur faciale enfant | 61,3 ± 5 mm | concordant avec la fiche |
| Profondeur faciale adulte | 70,3 ± 5 mm | concordant avec la fiche |
| Décalage A-B | aucune norme autoritative | l'ancien code le qualifiait explicitement de construction interne non validée cliniquement |
| Situation B | aucune norme autoritative active | l'ancien code la qualifiait explicitement de mesure interne non validée comme McNamara |

Le même code contenait auparavant des diagnostics automatiques et des propositions de traitement à partir de seuils locaux ; ils ont été retirés dans PR `#371`. Ils ne doivent pas être restaurés sans registre de règles sourcées, tests de contexte et gate praticien.

## NORMES COM — ÉTAT

La photographie historique montre notamment des plages de normalité/compensation et des valeurs âge/adulte. Une recherche de contrôle a retrouvé certaines valeurs exactes reproduites en ligne, mais dans une source secondaire de qualité insuffisante pour servir de référence clinique canonique.

**Décision :**

- conserver les chiffres de la fiche comme `HISTORICAL_REFERENCE_ONLY` ;
- rechercher la publication, le manuel ou la provenance COM originale ;
- aucune norme COM n'entre dans le registre clinique tant que `source_id`, édition/date, population de référence et unité ne sont pas établis.

## ANALYSES SUIVANTES

Ordre de construction après COM :

1. Steiner ;
2. Tweed/Merrifield ;
3. Wits/Jacobson ;
4. Downs ;
5. McNamara ;
6. Ricketts ;
7. tissus mous/esthétique.

Chaque analyse recevra la même matrice et un statut global `FULL | PARTIAL | NOT_COMPUTABLE`.

## NEXT EXACT

1. sourcer la définition historique de `A'B'` du COM et des normes de la fiche ;
2. certifier les définitions opérationnelles des landmarks nécessaires au COM ;
3. écrire des golden cases géométriques COM sans normes ;
4. ensuite seulement activer les normes COM versionnées.
