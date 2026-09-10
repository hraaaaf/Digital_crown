# CÉPHALOMÉTRIE — MATRICE ANALYSES → MESURES → LANDMARKS

**Statut : chantier actif / COM-CRANIOM geometry en certification**  
**Parent canonique :** `docs/CEPHALO_DIAGNOSTIC_SPEC.md`  
**Contrat landmarks :** `docs/SRPOSE38_LANDMARK_CONTRACT.md`  
**Registre constructions :** `docs/CEPHALO_CONSTRUCTION_REGISTRY.md`

## GOAL

Rendre explicite la chaîne :

`analyse → mesure → landmarks → construction → unité → calibration → formule → source → statut`

Une dépendance absente reste `NOT_COMPUTABLE`. Une norme non sourcée reste inactive.

## IDENTITÉ DE LA MÉTHODE HISTORIQUE

Le flux appelé historiquement `COM` dans Digital Crown correspond au périmètre de la méthode **C.R.A.N.I.O.M.** de Bonnefont, Casteigt, Ernoult et Sorel.

Source publiée de référence :
- Bonnefont R, Casteigt J, Ernoult J-F, Sorel O. *A new method for the utilization of cephalometric measurements in orthodontics or how standard deviations can sometimes be the practitioner's false friends (Part 1).* Journal of Dentofacial Anomalies and Orthodontics. 2010;13(4):385-400. DOI `10.1051/odfen/2010406`.

La publication décrit un échantillon de jeunes adultes Classe I non traités et insiste sur la séparation entre mesures dentaires, formes osseuses et aide au diagnostic. Les valeurs de cette méthode doivent donc être présentées comme **références CRANIOM spécifiques**, jamais comme normes universelles.

## CRANIOM / COM — MATRICE ACTUELLE

| Bloc | Mesure | Landmarks SRPose38 | Construction | Calibration | État |
|---|---|---|---|---|---|
| Dentaire | Surplomb | U1/UI #12, L1/LI #11 + repère d'orientation | projection incisive actuelle sur axe FH | mm | `CURRENT_IMPLEMENTATION_CANDIDATE` |
| Dentaire | Recouvrement | U1/UI #12, L1/LI #11 + repère d'orientation | projection verticale actuelle dans repère FH | mm | `CURRENT_IMPLEMENTATION_CANDIDATE` |
| Dentaire | I / mandibulaire | L1A #22, L1 #11 + plan mandibulaire | axe L1 / plan mandibulaire | non | `ANALYSIS_DEFINITION_REQUIRED` |
| Dentaire | I / Francfort | U1A #21, U1 #12, Po #4, Or #3 | axe U1 / FH | non | `SOURCE_VERIFIED_GEOMETRY` |
| Dentaire | Inter-incisif | U1A #21, U1 #12, L1A #22, L1 #11 | angle axes U1/L1 | non | `VERIFIED_GEOMETRY`, référence numérique à versionner |
| Osseux | A'B' | A #5, B #6, Po #4, Or #3 | projections orthogonales A', B' sur FH | mm | `SOURCE_VERIFIED_GEOMETRY` |
| Osseux | A / verticale Nasion | A #5, N #2, Po #4, Or #3 | distance AP signée à la verticale N, dans repère FH | mm | `SOURCE_COMPATIBLE_GEOMETRY` |
| Osseux | B / verticale Nasion | B #6, N #2, Po #4, Or #3 | idem | mm | `SOURCE_COMPATIBLE_GEOMETRY` |
| Osseux | Profondeur faciale S / verticale Nasion | S #1, N #2, Po #4, Or #3 | distance parallèle à FH jusqu'à verticale N | mm | `GEOMETRY_VERIFIED_SOURCE_SEMANTICS_TO_CONFIRM` |
| Osseux vertical | Forme faciale CRANIOM | S, N + plan mandibulaire de Downs | angle SN / plan mandibulaire | non | `NOT_COMPUTABLE_EXACTLY` tant que convention mandibulaire non certifiée |
| Osseux vertical | Forme mandibulaire CRANIOM | Ar + Gi + Gs + Me | angle branche montante / plan mandibulaire | non | `NOT_COMPUTABLE` : SRPose38 n'émet pas Gi/Gs séparés |
| Suivi | A''B'' regard horizontal | A, B + protocole photo NHP | projection sur plan du regard | mm | `NOT_COMPUTABLE` sans orientation naturelle de tête validée |

## A'B' — CONSTRUCTION DÉSORMAIS SOURCÉE

CRANIOM définit A' et B' comme les **projections orthogonales des points A et B sur le plan de Francfort**. La valeur algébrique est positive lorsque A est en avant de B et négative dans le cas inverse.

Formule runtime certifiée géométriquement :

`A'B' = dot(A - B, unit(Po→Or)) × mm_per_pixel`

Le calcul historique actuel de `cephalo_engine.py` (`Situation_A - Situation_B`) est algébriquement équivalent. Des golden tests dédiés assurent rotation, translation, changement d'échelle et signe.

## RÉFÉRENCES CRANIOM CONFIRMÉES, MAIS NON ENCORE ACTIVÉES

La source publiée confirme notamment les bornes extrêmes d'inclinaison incisive utilisées par CRANIOM :
- incisive mandibulaire : **78° à 114°** par rapport au plan mandibulaire de Downs ;
- incisive maxillaire : **97,5° à 130,1°** par rapport à Francfort.

Le document CRANIOM détaillé/mirror explicite aussi pour A'B' :
- moyenne à 9 ans : **+4,2 mm**, écart-type **3,2 mm** ;
- moyenne adulte : **+2,3 mm**, écart-type **3,1 mm** ;
- classification CRANIOM fondée sur ces plages spécifiques.

Ces valeurs restent `METHOD_SPECIFIC_REFERENCE_PENDING_REGISTRY` jusqu'au Lot 11 : contexte, âge, population, source/version et règles doivent être encodés séparément de la mesure brute.

## CONFLITS LEGACY DIGITAL CROWN

Le diff retiré en PR #371 montre pourquoi aucune ancienne constante ne doit être restaurée aveuglément :

| Mesure | Ancien code | Constat |
|---|---:|---|
| Surplomb | 2,25 ± 0,75 mm | plage 1,5–3 mm reproduite |
| Recouvrement | 2,25 ± 0,75 mm | plage 1,5–3 mm reproduite |
| IMPA | 90° ± 5° | référence historique, différente de la philosophie CRANIOM des valeurs extrêmes |
| I / Francfort | 107° ± 5° | référence historique ; CRANIOM accepte un intervalle extrême beaucoup plus large |
| Inter-incisif | 131° ± 10° | conflit historique frontend ±13 |
| Angle de Tweed | 26° ± 4° | présent sur la fiche historique ; à distinguer de la forme faciale CRANIOM SN/plan mandibulaire |
| Situation A adulte | 2,3 ± 3,0 mm | diffère de la fiche fournie : ±3,3 |
| A-B | ancien code le qualifiait de construction interne non validée | **corrigé scientifiquement : A'B' CRANIOM est maintenant identifié et sourcé** |

## DÉCISION

1. conserver l'entrée utilisateur `COM` pour compatibilité UX tant que nécessaire ;
2. identifier scientifiquement la méthode comme `CRANIOM` dans le registre ;
3. ne jamais fusionner silencieusement CRANIOM, Tweed, Steiner, Downs ou Ricketts ;
4. garder mesure brute et évaluation normative dans deux objets séparés ;
5. les constructions nécessitant Gi/Gs ou regard horizontal restent `NOT_COMPUTABLE` plutôt que remplacées par Go ou par l'horizontale de l'image.

## ANALYSES SUIVANTES

Steiner → Tweed/Merrifield → Wits/Jacobson → Downs → McNamara → Ricketts → tissus mous/esthétique.

Chaque analyse reçoit un statut `FULL | PARTIAL | NOT_COMPUTABLE` selon ses dépendances réellement disponibles.

## NEXT EXACT

1. faire passer les golden tests des constructions CRANIOM ;
2. brancher `cephalo_engine.py` sur les fonctions versionnées sans changement numérique attendu ;
3. verrouiller le plan mandibulaire propre à chaque analyse ;
4. construire ensuite le registre normatif CRANIOM sans réactiver de diagnostic automatique.