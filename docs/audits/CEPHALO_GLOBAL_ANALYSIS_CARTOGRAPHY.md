# Céphalo-N — Cartographie scientifique globale des analyses

Statut : **CANDIDAT V0 À VALIDATION CLINIQUE — ZÉRO CODE CLINIQUE**

Date : 2026-09-15

## Goal / Succès / Preuve

**Goal** — définir exactement le contenu scientifique de Steiner, Tweed, McNamara, Ricketts et COM avant toute nouvelle géométrie, norme, interprétation ou implémentation.

**Succès** — chaque mesure est rattachée à une version/source, une incidence, un domaine, des landmarks/plans, un statut core/extension et un état Digital Crown. Les variantes ne sont jamais fusionnées silencieusement.

**Preuve** — sources historiques primaires verrouillées quand disponibles, recoupement secondaire, comparaison avec l’état actuel de Digital Crown. La validation clinique finale de la composition appartient au praticien avant la phase géométrique.

## Règles de méthode verrouillées

1. **Aucun code clinique dans ce lot.**
2. `sagittal` et `antéropostérieur` désignent le même axe. Les trois dimensions sont donc : **sagittal/AP, vertical, transversal**.
3. Une téléradiographie de profil ne fournit pas, à elle seule, un bilan transversal frontal valide. Toute mesure transversale doit porter son incidence (`PA/frontale`, ou autre modalité explicitement validée).
4. Landmark ≠ ligne/plan ≠ construction ≠ mesure ≠ norme ≠ interprétation ≠ diagnostic.
5. Une mesure attribuée à un auteur doit être rattachée à une **version/source**. Une extension postérieure n’est pas intégrée au noyau historique sans étiquette de version.
6. Les normes historiques sont documentées mais **ne deviennent jamais des normes actives DC par simple copie**. Population, âge, sexe, taille faciale, agrandissement radiographique et modalité doivent être explicités.
7. Absence de landmark ou de provenance : `NOT_COMPUTABLE` / `SOURCE_MISSING`; aucune substitution géométrique silencieuse.
8. Les analyses seront synthétisées par convergence/divergence/compensation et confiance, **jamais par moyenne naïve de mesures incompatibles**.

## Schéma de la matrice

`ANALYSE | VERSION/SOURCE | INCIDENCE | DOMAINE | MESURE | TYPE | LANDMARKS REQUIS | PLAN/LIGNE | NORME HISTORIQUE / SOURCE | ÂGE/SEXE/POPULATION | CORE/OPTIONNEL | ÉTAT DC`

Deux colonnes logiques devront être ajoutées lors de la phase normative : `NORM_VERSION` et `DC_ACTIVE_NORM`. Elles restent volontairement non activées ici.

---

# 1. Steiner

## Version de référence proposée

- **STEINER_1953_CORE_V1** — Cecil C. Steiner, *Cephalometrics for you and me*, American Journal of Orthodontics 39(10):729-755, 1953, DOI `10.1016/0002-9416(53)90082-7`.
- **STEINER_1959_CLINICAL_EXTENSION_V1** — Cecil C. Steiner, *Cephalometrics in clinical practice*, Angle Orthodontist 29:8-29, 1959, DOI `10.1043/0003-3219(1959)029<0008:CICP>2.0.CO;2`.
- Le travail de planification/compromis de 1960 doit rester une couche séparée de logique clinique et ne doit pas contaminer la définition géométrique de 1953/1959.

## Matrice Steiner

| Version | Incidence | Domaine | Mesure | Type | Landmarks | Plan / ligne | Norme historique | Contexte normatif | Statut | État DC |
|---|---|---|---|---|---|---|---|---|---|---|
| 1953 | Profil | Sagittal/AP squelettique | SNA | angle | S, N, A | SN / NA | 82° | référence historique; non universelle | CORE | Calculé + affiché |
| 1953 | Profil | Sagittal/AP squelettique | SNB | angle | S, N, B | SN / NB | 80° | idem | CORE | Calculé + affiché |
| 1953 | Profil | Sagittal/AP intermaxillaire | ANB | angle | S, N, A, B | NA / NB; différence SNA-SNB | 2° | dépend aussi de géométrie craniofaciale/verticale | CORE | Calculé + affiché |
| 1953 | Profil | Dento-alvéolaire maxillaire | U1–NA angle | angle | U1 apex, U1 axe/couronne, N, A | axe U1 / NA | 22° | historique | CORE | Méthode typée antérieurement; non affichée R19 |
| 1953 | Profil | Dento-alvéolaire maxillaire | U1–NA linéaire | mm | **surface labiale/coronaire U1**, N, A | NA | 4 mm | historique | CORE | **BLOQUÉ landmark coronaire explicite** |
| 1953 | Profil | Dento-alvéolaire mandibulaire | L1–NB angle | angle | L1 apex, L1 axe/couronne, N, B | axe L1 / NB | 25° | historique | CORE | Méthode typée antérieurement; non affichée R19 |
| 1953 | Profil | Dento-alvéolaire mandibulaire | L1–NB linéaire | mm | **surface labiale/coronaire L1**, N, B | NB | 4 mm | historique | CORE | **BLOQUÉ landmark coronaire explicite** |
| 1953 | Profil | Dentaire | Angle interincisif | angle | axes U1, L1 | U1 / L1 | ~130–131° | mesure complémentaire explicitement conservée par Steiner | CORE/SUPPL. | Existe sous `Inter_Incisif`, actuellement rangé COM |
| 1953 | Profil | Vertical / dentaire | Plan occlusal–SN | angle | S, N + définition du plan occlusal | SN / plan occlusal | ~14.5° | définition exacte du plan occlusal à source-locker | CORE | Non exposé dans onglet Steiner |
| 1953 | Profil | Vertical squelettique | GoGn–SN | angle | Go, Gn, S, N | GoGn / SN | ~32° | historique | CORE | Non exposé dans onglet Steiner |
| 1953 | Profil | Dento-alvéolaire mandibulaire | L1–GoGn | angle | axe L1, Go, Gn | L1 / GoGn | ~93° | complément historique | SUPPL. | Non exposé Steiner; IMPA actuel utilise un plan mandibulaire à convention distincte |
| 1953 | Profil | Dentaire / position molaire | U6–NA | mm | U6 + N, A | NA | valeur historique rapportée ~27 mm | suivi de position, définition du point molaire à verrouiller | SUPPL./SERIAL | Non exposé |
| 1953 | Profil | Dentaire / position molaire | L6–NB | mm | L6 + N, B | NB | valeur historique rapportée ~23 mm | suivi de position | SUPPL./SERIAL | Non exposé |
| 1959 | Profil | Sagittal/AP squelettique | SND | angle | S, N, D | SN / ND | ~76–77° dans compilations historiques | point D et convention à implémenter explicitement | EXTENSION CORE 1959 | Absent |
| 1959 | Profil | Relations complémentaires | Pog–NB | mm | Pog, N, B | NB | **pas de moyenne diagnostique universelle**; relation avec L1–NB privilégiée | Holdaway/Steiner; individualisé | EXTENSION CORE 1959 | Absent |
| 1959 | Profil | Dento-alvéolaire mandibulaire | L1–D line, linéaire | mm | L1 surface antérieure, D, Go, Gn | ligne D ⟂ GoGn passant par D | pas de norme fixe universelle | suivi intra-mandibulaire | EXTENSION | Absent |
| 1959 | Profil | Dento-alvéolaire mandibulaire | L1–D line, angulaire | angle | axe L1, D, Go, Gn | axe L1 / D-line | pas de norme fixe universelle | suivi intra-mandibulaire | EXTENSION | Absent |
| 1959 | Profil / séries | Croissance / traitement | lignes incisives et molaires sérielles | déplacement | dents + lignes NA/NB reportées | conventions de superposition Steiner | patient-spécifique | séries temporelles | EXTENSION | Absent comme module Steiner versionné |

### Décision scientifique Steiner à valider

**Proposition** : présenter dans DC deux couches distinctes : `Steiner 1953 — analyse de base` et `Steiner 1959 — extension clinique/sérielle`. Ne pas appeler automatiquement SND, Pog–NB ou D-line « Steiner classique 1953 ».

---

# 2. Tweed

## Version de référence proposée

- **TWEED_1946_FMA_V1** — C.H. Tweed, *The Frankfort-mandibular plane angle in orthodontic diagnosis, classification, treatment planning and prognosis*, American Journal of Orthodontics and Oral Surgery, 1946.
- **TWEED_1954_TRIANGLE_V1** — C.H. Tweed, *The Frankfort-mandibular incisor angle (FMIA) in orthodontic diagnosis, treatment planning and prognosis*, Angle Orthodontist 24:121-169, 1954.

Le noyau Tweed 1954 est **le triangle de trois angles**. Les développements Merrifield (profil/Z-angle, Total Space Analysis, etc.) doivent être une analyse/version séparée `TWEED-MERRIFIELD`, pas un enrichissement silencieux de Tweed 1954.

## Matrice Tweed

| Version | Incidence | Domaine | Mesure | Type | Landmarks | Plan / ligne | Norme historique | Contexte normatif | Statut | État DC |
|---|---|---|---|---|---|---|---|---|---|---|
| 1946/1954 | Profil | Vertical squelettique | FMA | angle | Po anatomique, Or, convention plan mandibulaire | FH / mandibular plane | 25°; variation historique 20–30° | valeurs pragmatiques historiques | CORE | Existe comme `Angle_de_Tweed` et affiché Tweed |
| 1954 | Profil | Dento-alvéolaire mandibulaire | IMPA | angle | axe L1 + plan mandibulaire | L1 / mandibular plane | 90°; variation historique 85–95° | historique | CORE | Calculé + affiché Tweed |
| 1954 | Profil | Dento-alvéolaire / facial | FMIA | angle | axe L1, Po anatomique, Or | L1 / FH | ~65° | dérivé du triangle historique; population non universelle | CORE | **Absent de l’onglet Tweed actuel** |

### Décision scientifique Tweed à valider

Le Tweed actuel est **incomplet** : 2/3 mesures du triangle seulement. FMIA est constitutif de la version 1954 et ne doit pas être remplacé par `I_Francfort`, qui mesure actuellement l’**incisive supérieure** par rapport à Frankfort et n’est donc pas le FMIA de Tweed.

---

# 3. McNamara

## Version de référence proposée

**MCNAMARA_1984_SINGLE_FILM_V1** — J.A. McNamara Jr., *A method of cephalometric evaluation*, American Journal of Orthodontics 86(6):449-469, 1984, DOI `10.1016/S0002-9416(84)90352-X`.

Cette version est une **analyse de téléradiographie latérale**. Elle ne constitue pas une analyse transversale frontale. Le papier distingue analyse d’un film et analyse de films sériels.

La table primaire 1984 documente 13 variables quantitatives : squelette, vertical, dentition et voies aériennes. Le profil des tissus mous et l’angle nasolabial sont utilisés comme contexte clinique, mais l’angle nasolabial n’est pas l’une des 13 lignes du tableau quantitatif principal.

## Matrice McNamara — film unique

| Incidence | Domaine | Mesure | Type | Landmarks | Plan / ligne | Norme historique / source | Contexte | Statut | État DC |
|---|---|---|---|---|---|---|---|---|---|
| Profil | Sagittal/AP maxillaire | A → Nasion perpendicular | mm signé | A, N, Po anatomique, Or | N-perp ⟂ FH | 0 mm dentition mixte; ~1 mm adulte dans normes composites | âge/taille faciale; 8% agrandissement dans données historiques | CORE | Construction voisine existe comme `Situation_A`, mais classée COM; pas dans McNamara UI |
| Profil | Sagittal/AP maxillaire | SNA | angle | S, N, A | SN / NA | valeurs adultes H/F publiées en Table I | sexe/population | CORE CONTEXTUEL | Existe, mais affiché Steiner |
| Profil | Sagittal / taille | Co–A longueur médiofaciale effective | mm | Co, A | segment Co-A | tables selon taille/âge/sexe | agrandissement 8% historique | CORE | Ligne UI McNamara existe; backend versionné non garanti |
| Profil | Sagittal / taille | Co–Gn longueur mandibulaire effective | mm | Co, Gn anatomique | segment Co-Gn | tables selon taille/âge/sexe | idem | CORE | Ligne UI McNamara existe; backend versionné non garanti |
| Profil | Relation intermaxillaire | Différentiel maxillo-mandibulaire | mm | Co, A, Gn | différence des longueurs effectives | petits/moyens/grands visages, tables dédiées | taille faciale | CORE | Absent UI McNamara |
| Profil | Vertical | ANS–Me / LAFH | mm | ANS, Me | segment ANS-Me | valeurs selon taille/âge/sexe | taille faciale | CORE | Ligne UI McNamara existe; backend versionné non garanti |
| Profil | Vertical | Mandibular plane angle | angle | Po anatomique, Or, Go, Me | FH / Go-Me | ~25° mixte, ~22° adulte dans composite historique | change avec croissance | CORE | Pas dans McNamara UI; FMA proche existe sous Tweed avec convention à ne pas présumer identique |
| Profil | Croissance / pattern | Facial axis angle | angle | Ba, N, PTM, Gn construit | Ba-N / PTM-Gn | 90° relation de référence | stable dans convention historique | CORE | **BLOQUÉ antérieurement côté Ricketts faute de source-lock géométrique; source primaire McNamara désormais identifiée** |
| Profil | Sagittal/AP mandibulaire | Pog → Nasion perpendicular | mm signé | Pog, N, Po anatomique, Or | N-perp ⟂ FH | valeurs dépendant de taille faciale et croissance | âge/taille faciale | CORE | Absent; `Situation_B` actuel utilise B, donc **n’est pas cette mesure** |
| Profil | Dento-alvéolaire maxillaire | U1 → A vertical | mm | surface faciale U1, A, FH | A-perp parallèle à N-perp | 4–6 mm | landmark de surface requis | CORE | **BLOQUÉ tant que surface faciale coronaire explicite non disponible** |
| Profil | Dento-alvéolaire mandibulaire | L1 → A-Pog | mm | surface faciale L1, A, Pog | A-Pog | 1–3 mm | landmark de surface requis | CORE | **BLOQUÉ landmark coronaire explicite** |
| Profil | Voies aériennes | Upper pharynx | mm | palais mou postérieur + paroi pharyngée postérieure | plus courte distance selon protocole 1984 | moyenne adulte ~17.4 mm; <5 mm = seulement signal de préoccupation, pas diagnostic | 2D; phase de déglutition; avis ORL requis pour diagnostic | CORE | Absent |
| Profil | Voies aériennes | Lower pharynx | mm | jonction langue postérieure/bord mandibulaire + paroi pharyngée | plus courte distance | ~10–12 mm; >15 mm peut signaler posture antérieure de langue | non diagnostique isolément | CORE | Absent |
| Profil | Tissus mous | Profil / angle nasolabial | angle/observation | columelle/Prn', Sn, Ls selon convention | ligne columellaire / lèvre supérieure | ~110° cité par McNamara depuis Scheideman, pas une des 13 mesures principales | soft-tissue guide prioritaire si conflit | CONTEXTUEL/OPTIONNEL | Absent McNamara |

## McNamara — croissance / séries

Le papier 1984 prévoit une analyse sérielle avec superpositions et tables de croissance, notamment Co-Gn, Co-A, différentiel maxillo-mandibulaire et ANS-Me. Cette couche doit être versionnée séparément de l’analyse statique.

### Décision scientifique McNamara à valider

`MCNAMARA_1984_SINGLE_FILM_V1` doit contenir les **13 variables quantitatives du papier**, avec tissus mous comme contexte. Aucun transversal ne doit être inventé à partir du profil.

---

# 4. Ricketts

## Versions à ne pas mélanger

- **RICKETTS_1960_FOUNDATION_V1** — *A foundation for cephalometric communication*, American Journal of Orthodontics 46(5):330-357, 1960, DOI `10.1016/0002-9416(60)90047-6`. Version historique initiale, plus restreinte.
- **RICKETTS_1981_SUMMARY_DESCRIPTIVE_V1** — R.M. Ricketts, *Perspectives in the clinical application of cephalometrics. The first fifty years*, Angle Orthodontist 51(2):115-150, 1981, DOI `10.1043/0003-3219(1981)051<0115:PITCAO>2.0.CO;2`.

Pour Digital Crown, la version proposée comme **référence globale** est celle de **1981**, car elle publie explicitement un *Summary Descriptive Analysis* avec **11 facteurs latéraux + 12 facteurs frontaux = 23 facteurs**. Elle couvre donc véritablement sagittal/AP, vertical, transversal, dentaire, tissus mous et croissance. Les variantes ultérieures « 33 facteurs », VERT, Ricketts-Faltin, etc. ne doivent pas être fusionnées dans ce noyau sans version spécifique.

## Ricketts 1981 — Lateral / Sagittal Orientation (11 facteurs)

| # | Incidence | Domaine | Mesure | Type | Landmarks | Plan / ligne | Norme historique 1981 | Croissance / contexte | Statut | État DC |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Profil | Croissance / pattern | Facial Axis | angle | Pt, Gn, Ba, N | Pt-Gn / Ba-N | 90° ±3° | moyenne stable; variabilité de changement publiée | CORE | Non calculé; antérieurement bloqué faute de convention sourcée |
| 2 | Profil | Sagittal/AP mandibulaire | Facial Angle | angle | N, Pog, Po anatomique, Or | N-Pog / FH | âge 3 ≈83°±3; âge 18 ≈88° | +~1°/3 ans jusqu’à maturité | CORE | Absent |
| 3 | Profil | Vertical | Mandibular Plane | angle | FH + sub-Go/M selon convention Ricketts | FH / mandibular plane | âge 3 ≈28°±4; âge 18 ≈23° | baisse ~1°/3 ans | CORE | Pas sous Ricketts; angle voisin existe ailleurs |
| 4 | Profil | Vertical / denture height | Oral Gnomon | angle | ANS, Xi, Pm | ANS-Xi-Pm | 46°±3° | stable | CORE | Absent; Xi/Pm manquants dans pipeline actuel |
| 5 | Profil | Vertical / maxillaire | Palatal plane to FH | angle | ANS, PNS, Po, Or | ANS-PNS / FH | 0°±2.5° | stable | CORE | Absent |
| 6 | Profil | Sagittal/AP intermaxillaire | Maxillary Convexity | mm | A, N, Pog | A → facial plane N-Pog | âge 3 ≈4.5 mm; âge 18 ≈1.0 mm | baisse ~0.7 mm/3 ans | CORE | Absent |
| 7 | Profil | Dento-alvéolaire mandibulaire | Lower incisor edge → APo | mm | L1 edge, A, Pog | A-Pog | +1 mm | suit A-Pog avec croissance | CORE | Absent sous Ricketts; landmark coronaire/surface à verrouiller |
| 8 | Profil | Dentaire postérieur | Upper first molar → PTV | mm | U6, Pt/Ptm, FH | Pterygoid Vertical | règle liée à l’âge publiée | +~1 mm/an jusqu’à maturité | CORE | Absent |
| 9 | Profil | Dentaire | Interincisal Angle | angle | axes U1, L1 | U1/L1 | âge 3 ≈122°±5° | +~2°/5 ans | CORE | Existe `Inter_Incisif`, mais classé COM |
| 10 | Profil | Tissus mous | Lower lip → Esthetic Plane | mm signé | Li, Prn, Pog' | E-plane Prn-Pog' | âge 3 ≈0±2 mm; âge 15 ≈−3±2 mm | −~0.25 mm/an | CORE | Calculé `Ligne_E_Li` + affiché Ricketts |
| 11 | Profil | Morphologie mandibulaire / croissance | Bend of Mandible | angle réflexe | corpus axis, condyle axis, points Ricketts associés | corpus axis / condyle axis | ~19° âge3; 22° âge8; 25° âge13; 28° âge18 | +~0.6°/an | CORE | Absent; landmarks/axes spécifiques manquants |

### E-line supérieure

Digital Crown calcule aussi `Ligne_E_Ls` (lèvre supérieure). Cette mesure est scientifiquement utile et rattachable à la famille esthétique de Ricketts, mais **le cue sheet latéral 1981 à 11 facteurs retient explicitement la lèvre inférieure**. `Ls/E-line` doit donc rester `EXTENSION/OPTIONNEL` pour `RICKETTS_1981_SUMMARY_DESCRIPTIVE_V1`, sauf source/version différente explicitement adoptée.

## Ricketts 1981 — Frontal Orientation (12 facteurs)

| # | Incidence | Domaine | Mesure | Type | Landmarks | Plan / ligne | Norme historique 1981 | Croissance / contexte | Statut | État DC |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | PA/frontale | Transversal / nasal | Nasal Cavity Width | mm | NC-R, NC-L | NC-NC | âge 8 ≈24.5±2 mm; âge3 22; âge18 29.5 | +0.5 mm/an | CORE | **Non disponible : pas de pipeline PA** |
| 2 | PA/frontale | Transversal maxillo-mandibulaire | Maxillary Relation droite | mm | J-R, Z/Ag-R selon frontal facial plane | J → Z-Ag | 10±1.5 mm | stable | CORE | Non disponible |
| 3 | PA/frontale | Transversal maxillo-mandibulaire | Maxillary Relation gauche | mm | J-L, Z/Ag-L | J → Z-Ag | 10±1.5 mm | stable | CORE | Non disponible |
| 4 | PA/frontale | Transversal mandibulaire | Mandibular Width | mm | Ag-R, Ag-L | Ag-Ag | âge3 68.25±3; âge8 75; âge13 81.25; âge18 88.50 | **source incohérente : cue sheet dit +1.25 mm/an, Table 9 et valeurs impliquent ~+1.35 mm/an** | CORE / NORM HOLD | Non disponible |
| 5 | PA/frontale | Asymétrie squelettique | ANS / Pog vers plan sagittal central | mm | Cg/repère médian, Z-Z/plan de référence, ANS, Pog | midsagittal reference | 0±2 mm | stable si symétrie | CORE | Non disponible; libellé source 1981 à normaliser sans changer géométrie |
| 6 | PA/frontale | Dentaire transversal | Intermolar Width mandibulaire | mm | surfaces vestibulaires B6-R/B6-L | B6-B6 | ~56±2 mm | peu de changement | CORE | Non disponible |
| 7 | PA/frontale | Dentaire transversal | Intercuspid Width mandibulaire | mm | cuspides B3-R/B3-L | B3-B3 | âge13 ~26±1.5 mm; valeurs âge3/8 publiées | évolution liée à éruption | CORE | Non disponible |
| 8 | PA/frontale | Dento-alvéolaire transversal | Lower molar → Fronto-Denture Plane droite | mm | B6-R, J-R, Ag-R | B6 → J-Ag | âge8 ~6±2 mm | +~0.8 mm/an; valeurs âge6/13/18 publiées | CORE | Non disponible |
| 9 | PA/frontale | Dento-alvéolaire transversal | Lower molar → Fronto-Denture Plane gauche | mm | B6-L, J-L, Ag-L | B6 → J-Ag | idem | idem | CORE | Non disponible |
| 10 | PA/frontale | Asymétrie dentaire | Midpoint lower incisors → Fronto A-Po Plane | mm | iif, repères médiaux | frontal A-Po / midline | 0±1 mm | stable en symétrie | CORE | Non disponible |
| 11 | PA/frontale | Occlusion transversale | Molar crossbite droite | mm | surfaces vestibulaires U6-R/L6-R | relation molaire transverse | upper ~1±1 mm plus buccal | stable | CORE | Non disponible |
| 12 | PA/frontale | Occlusion transversale | Molar crossbite gauche | mm | surfaces vestibulaires U6-L/L6-L | relation molaire transverse | idem | stable | CORE | Non disponible |

### Point critique Ricketts

Le document primaire 1981 contient une **discordance interne** pour la croissance de `Ag–Ag` : le cue sheet annonce +1.25 mm/an alors que la Table 9 annonce +1.35 mm/an et les valeurs 68.25 → 88.50 entre 3 et 18 ans correspondent à +1.35 mm/an. **Aucune norme active DC ne doit être créée tant que cette divergence n’est pas explicitement arbitrée/source-lockée.**

---

# 5. COM

## Conclusion de provenance

À ce stade de l’audit, **aucune analyse historique orthodontique canonique nommée “COM” n’a été source-lockée** dans les sources externes interrogées. En revanche, le dépôt Digital Crown porte explicitement une logique `COM_Skeletal` / « legacy COM flow » dans son moteur et ses constructions.

La règle scientifique doit donc être :

**COM = `COM_DC_LEGACY_V1`, analyse composite interne Digital Crown, tant qu’une source externe précise n’est pas fournie et validée.**

Il est interdit de lui attribuer rétrospectivement un auteur, une population normative ou une « analyse classique » sans preuve.

## Composition actuelle de l’onglet COM R19

Le Workbench R19 expose exactement 10 lignes :

| Incidence | Domaine | Mesure DC actuelle | Type | Landmarks / ligne | Provenance scientifique réelle | Statut scientifique | État DC |
|---|---|---|---|---|---|---|---|
| Profil | Dentaire | Surplomb | mm | U1 edge, L1 edge, FH comme axe de projection | mesure occlusale générique, **pas spécifique COM** | COM composite | Affiché COM |
| Profil | Dentaire | Recouvrement | mm | U1 edge, L1 edge, ⟂FH | mesure occlusale générique | COM composite | Affiché COM |
| Profil | Dento-alvéolaire mandibulaire | IMPA | angle | L1 / mandibular plane | **Tweed 1954** | import inter-analyse | Affiché COM + Tweed |
| Profil | Dento-alvéolaire maxillaire | I / Francfort | angle | U1 / FH | mesure distincte du FMIA de Tweed | provenance COM externe non verrouillée | Affiché COM |
| Profil | Dentaire | Angle inter-incisif | angle | U1 / L1 | Downs/Steiner comme mesure complémentaire historique | import inter-analyse | Affiché COM |
| Profil | Vertical | Angle de Tweed / FMA | angle | mandibular plane / FH | **Tweed** | import inter-analyse | Affiché COM + Tweed |
| Profil | Sagittal/AP | Décalage osseux A’B’ | mm | projections A/B sur FH | **construction CRANIOM/DC versionnée**, pas identifiée comme mesure d’une analyse historique canonique | INTERNE | Calculé/affiché COM |
| Profil | Sagittal/AP maxillaire | Point A → N-perp | mm | A, N, FH | très proche de **McNamara A-Nperp** | import/équivalence à confirmer strictement | Calculé/affiché COM |
| Profil | Sagittal/AP mandibulaire | Point B → N-perp | mm | B, N, FH | **ne correspond pas** au Pog-Nperp McNamara classique | INTERNE / SOURCE MISSING | Calculé/affiché COM |
| Profil | Relations complémentaires | Profondeur faciale DC | mm | S → N-perp, magnitude | construction explicitement décrite comme `legacy COM flow` dans le dépôt | INTERNE / SOURCE MISSING | Calculé/affiché COM |

### Décision scientifique COM à valider

Deux choix seulement sont scientifiquement propres :

- **A — recommandé** : assumer COM comme `Digital Crown Composite`, utile pour regrouper des mesures opérationnelles, mais sans prétendre qu’il s’agit d’une analyse historique homogène ; chaque ligne conserve sa provenance originale.
- **B** : remplacer COM par une analyse externe identifiée, uniquement si son nom complet, sa publication/version et ses mesures sont fournis/source-lockés.

Tant que B n’est pas démontré, COM reste A.

---

# 6. Couverture tridimensionnelle réelle

| Analyse/version | Sagittal/AP | Vertical | Transversal | Dentaire / dento-alvéolaire | Tissus mous | Croissance | Voies aériennes |
|---|---:|---:|---:|---:|---:|---:|---:|
| Steiner 1953/1959 | Oui | Oui | **Non** | Oui | faible/contextuel en 1959 | Oui via séries | Non |
| Tweed 1954 | indirect | Oui | **Non** | Oui, surtout incisive mandibulaire | Non dans noyau 1954 | faible | Non |
| McNamara 1984 | Oui | Oui | **Non sur le film latéral classique** | Oui | contexte clinique | Oui via séries/normes | Oui |
| Ricketts 1981 | Oui | Oui | **Oui, avec PA/frontale** | Oui | Oui | Oui, normes évolutives | nasal/respiration contextuelle |
| COM_DC_LEGACY_V1 | Oui partiel | Oui partiel | **Non** | Oui | Non | Non | Non |

**Conséquence ODF** : la future synthèse globale ne pourra pas prétendre couvrir le transversal à partir du seul pipeline actuel de téléradiographie de profil. Pour la couverture 3D réelle, il faudra une entrée PA/frontale validée, ou une autre modalité validée séparément.

---

# 7. Écart Digital Crown actuel → cartographie cible

## État Workbench R19 vérifié

- Steiner : `SNA`, `SNB`, `ANB` seulement.
- Tweed : `IMPA`, `Angle_de_Tweed` seulement.
- McNamara : `Co_A`, `Co_Gn`, `ANS_Me` seulement, avec affichage conditionné à une valeur backend versionnée.
- COM : 10 lignes composites listées ci-dessus.
- Ricketts : `Ligne_E_Ls`, `Ligne_E_Li` seulement.

## Gaps majeurs

1. **Steiner** — UI très incomplète; linéaires incisifs bloqués par landmarks coronaires explicites; extension 1959 absente.
2. **Tweed** — FMIA manquant; triangle incomplet.
3. **McNamara** — 3 lignes UI sur un noyau primaire de 13 variables; N-perp, Pog-Nperp, dentition, axes verticaux et airway absents.
4. **Ricketts** — 2 mesures E-line actuellement, contre 11 facteurs latéraux + 12 frontaux dans la référence 1981 proposée; aucun pipeline PA.
5. **COM** — onglet hétérogène mélange mesures génériques, Tweed, équivalent McNamara probable et constructions CRANIOM internes. Le nom ne doit plus faire croire à une provenance homogène.

---

# 8. Landmarks nouveaux/manquants pressentis — inventaire, sans implémentation

Cet inventaire prépare la phase géométrique mais **n’autorise aucun code** avant validation clinique de la matrice.

### Profil

- surfaces faciales/coronaires explicites U1 et L1 pour les distances linéaires Steiner/McNamara ;
- Pog dur distinct et stable ;
- D (Steiner 1959) ;
- Co ;
- Ba ;
- PTM/Pt avec convention source-spécifique ;
- Xi, Pm (Ricketts) ;
- point/axe mandibulaire Ricketts pour `sub-Go-M`, corpus axis et condyle axis ;
- PNS ;
- U6 point de référence ;
- paroi pharyngée postérieure, palais mou, bord postérieur de langue pour McNamara airway ;
- Prn, Pog', Li et éventuellement Ls selon version E-line.

### PA/frontale Ricketts

- NC-R/L ;
- Z-R/L (zygomaticofrontal reference) ;
- J-R/L ;
- Ag-R/L ;
- Cg / construction du plan sagittal médian ;
- ANS, Pog en frontal ;
- B6-R/L ;
- B3-R/L ;
- U6-R/L ;
- iif (midpoint incisives inférieures) ;
- repères nécessaires aux plans fronto-facial et fronto-denture.

---

# 9. Normes : politique proposée

Aucune valeur historique ci-dessus ne doit entrer directement comme seuil diagnostique de production.

Chaque future norme devra être un objet versionné au minimum par :

`analysis_version + metric_id + source + modality + age_model + sex + population + magnification/scaling + mean/range/SD + applicability + confidence`.

Cas particuliers déjà démontrés :

- Steiner 1959 lui-même demande d’ajuster les objectifs selon âge, sexe, race, croissance et autres facteurs individuels.
- Tweed 1954 présente ses valeurs comme repères cliniques historiques et discute déjà des moyennes différentes trouvées par d’autres équipes.
- McNamara 1984 combine Bolton, Burlington et Ann Arbor, distingue taille/âge et publie un facteur d’agrandissement radiographique de 8% pour ses données normatives.
- Ricketts 1981 fait explicitement évoluer plusieurs normes avec l’âge et discute corrections biologiques par âge, sexe, type racial et taille ; sa propre source contient au moins une discordance numérique à arbitrer (Ag-Ag).

---

# 10. Synthèse inter-analyses — contrat futur, pas d’implémentation

La synthèse devra comparer des **assertions cliniques**, pas des chiffres bruts :

- `dimension` : sagittal/AP, vertical, transversal ;
- `structure` : maxillaire, mandibule, denture, tissu mou, airway ;
- `finding` : direction + sévérité + mesure(s) support ;
- `analysis_version` ;
- `norm_version` ;
- `evidence_quality` ;
- `confidence` ;
- `convergence` / `divergence` / `compensation` ;
- `reason_for_conflict` lorsque connu (référence différente, âge, compensation dentaire, verticalité, modalité, landmark incertain).

Aucune moyenne de SNA/ANB/A-Nperp/convexité/A’B’ n’est scientifiquement autorisée comme « score sagittal unique » sans modèle explicitement validé.

---

# 11. Human gate avant géométrie

À valider par le praticien :

1. **Steiner** : adopter `1953 core` + `1959 extension` séparés ?
2. **Tweed** : confirmer le triangle 1954 strict à 3 mesures et exclure Merrifield du noyau ?
3. **McNamara** : adopter les 13 mesures quantitatives du papier 1984 comme noyau du film unique, tissus mous en contexte ?
4. **Ricketts** : adopter `1981 Summary Descriptive = 11 latérales + 12 frontales` comme version principale, en conservant 1960 comme version historique distincte ?
5. **COM** : confirmer `COM_DC_LEGACY_V1 = composite interne`, sans prétention d’analyse historique, tant qu’aucune source externe n’est fournie ?
6. Accepter que le **transversal soit fail-closed** sans incidence PA/frontale/modalité validée ?

**Tant que ce gate n’est pas validé, aucune nouvelle formule, géométrie, norme clinique ou interprétation n’est autorisée.**

---

# 12. Sources verrouillées / registre

## Primaires

1. Steiner CC. *Cephalometrics for you and me*. Am J Orthod. 1953;39(10):729-755. DOI `10.1016/0002-9416(53)90082-7`.
2. Steiner CC. *Cephalometrics in clinical practice*. Angle Orthod. 1959;29:8-29. DOI `10.1043/0003-3219(1959)029<0008:CICP>2.0.CO;2`.
3. Tweed CH. *The Frankfort-mandibular plane angle in orthodontic diagnosis, classification, treatment planning and prognosis*. Am J Orthod Oral Surg. 1946.
4. Tweed CH. *The Frankfort-mandibular incisor angle (FMIA) in orthodontic diagnosis, treatment planning and prognosis*. Angle Orthod. 1954;24:121-169.
5. McNamara JA Jr. *A method of cephalometric evaluation*. Am J Orthod. 1984;86(6):449-469. DOI `10.1016/S0002-9416(84)90352-X`.
6. Ricketts RM. *A foundation for cephalometric communication*. Am J Orthod. 1960;46(5):330-357. DOI `10.1016/0002-9416(60)90047-6`.
7. Ricketts RM. *Perspectives in the clinical application of cephalometrics. The first fifty years*. Angle Orthod. 1981;51(2):115-150. DOI `10.1043/0003-3219(1981)051<0115:PITCAO>2.0.CO;2`.

## Recoupements secondaires / normatifs utilisés pour contrôle

- publications contemporaines comparant les variables McNamara et leurs variations populationnelles ;
- compilations céphalométriques historiques pour vérifier les listes Steiner/Tweed ;
- littérature de céphalométrie frontale pour les landmarks Z/J/Ag et l’asymétrie Ricketts.

Les recoupements secondaires ne remplacent jamais la source primaire lorsqu’elle est disponible.

---

# 13. État du lot

- **Fait** : cartographie globale V0 constituée, sans modification du moteur clinique.
- **Fait** : séparation versionnelle proposée pour Steiner, Tweed, McNamara et Ricketts.
- **Fait** : COM identifié dans DC comme composite hétérogène/interne tant qu’une provenance externe n’est pas démontrée.
- **Fait** : nécessité d’une modalité frontale/PA pour Ricketts transversal explicitée.
- **Fait** : discordance normative Ag-Ag Ricketts 1981 signalée et mise en HOLD.
- **Non fait volontairement** : aucune formule nouvelle, aucun landmark nouveau dans le code, aucune norme active, aucune interprétation clinique, aucune UI.
- **Human gate** : validation de la composition/version par le praticien.

Après validation seulement : `landmarks → plans/lignes → angles/distances → constructions SVG → logique par analyse → synthèse inter-analyses → onboarding ODF`.
