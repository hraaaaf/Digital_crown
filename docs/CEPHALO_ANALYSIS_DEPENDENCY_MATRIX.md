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

Sources publiées de référence :
- Bonnefont R, Casteigt J, Ernoult J-F, Sorel O. *A new method for the utilization of cephalometric measurements in orthodontics or how standard deviations can sometimes be the practitioner's false friends (Part 1).* Journal of Dentofacial Anomalies and Orthodontics. 2010;13(4):385-400. DOI `10.1051/odfen/2010406`.
- Bonnefont R, Ernoult J-F, Sorel O. *A new method of using cephalometric measurements in orthodontics (part 2) or how standard deviations can be the practitioner's false friends.* Journal of Dentofacial Anomalies and Orthodontics. 2011;14:105. DOI `10.1051/odfen/2011104`.

Les publications décrivent **83 jeunes adultes Classe I non traités**. Les valeurs de cette méthode doivent donc être présentées comme références CRANIOM spécifiques, jamais comme normes universelles.

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

Le runtime est branché sur `CRANIOM_AB_PRIME_V1`. Des golden tests dédiés couvrent rotation, translation, changement d'échelle, signe, calibration invalide et géométrie dégénérée.

## RÉFÉRENCES CRANIOM CONFIRMÉES, MAIS NON ENCORE ACTIVÉES

Les publications CRANIOM confirment notamment les bornes extrêmes d'inclinaison incisive utilisées par la méthode :
- incisive mandibulaire : **78° à 114°** par rapport au plan mandibulaire de Downs ;
- incisive maxillaire : **97,5° à 130,1°** par rapport à Francfort.

Un document technique CRANIOM détaillé reproduit également des valeurs pour A'B', Situation A/B et profondeur faciale. Ces nombres restent **secondaires tant qu'ils ne sont pas recoupés dans une source primaire exploitable** et ne doivent pas être activés comme référence clinique canonique.

Statut : `METHOD_SPECIFIC_REFERENCE_PENDING_REGISTRY`.

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

1. obtenir une CI verte sur le HEAD final de PR #390 ;
2. si vert, clore le sous-lot de géométrie linéaire CRANIOM ;
3. créer le registre normatif versionné en distinguant source primaire, source secondaire, population et contexte d'applicabilité ;
4. garder inactives les valeurs CRANIOM non recoupées par une source primaire exploitable ;
5. verrouiller séparément `TWEED_MP`, `DOWNS_MP` et les besoins `CRANIOM_Gi/Gs`.
