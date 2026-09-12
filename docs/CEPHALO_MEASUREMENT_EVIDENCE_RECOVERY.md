# CÉPHALOMÉTRIE — RÉCUPÉRATION DES MESURES / NO-DROP POLICY

**Date :** 2026-09-12  
**Parent :** `docs/CEPHALO_DIAGNOSTIC_SPEC.md`  
**Audit source :** `docs/CEPHALO_COM_VALUE_AUDIT.md`  
**Complément primaire Ricketts :** `docs/CEPHALO_COM_PRIMARY_RECOVERY_RICKETTS_1981.md`  
**Revue attribution inter-incisive :** `docs/CEPHALO_COM_INTERINCISAL_ATTRIBUTION_REVIEW.md`  
**Récupération géométrique source-spécifique :** `docs/CEPHALO_COM_SOURCE_GEOMETRY_RECOVERY.md`

## RÈGLE CANONIQUE

**Aucune mesure n'est abandonnée.**

Une mesure insuffisamment sourcée, ambiguë ou non constructible devient une **dette scientifique active**. Elle reste visible dans le registre avec la raison exacte de son blocage et un chemin de récupération. Un blocage signifie uniquement : « ne pas produire de classification clinique non prouvée maintenant ».

On distingue strictement :

`mesure calculable != référence normative prouvée != finding clinique != diagnostic != indication != traitement`

Une mesure peut donc rester calculable et affichable avec sa provenance même si sa norme ou son interprétation clinique n'est pas encore activable.

## GOAL

Récupérer chaque mesure ou règle présente dans l'audit COM/CRANIOM historique en recherchant la meilleure source disponible, puis :

1. verrouiller la définition géométrique ;
2. verrouiller la source numérique ou la règle source-spécifique ;
3. définir population/âge/sexe/contexte si nécessaire ;
4. conserver les divergences au lieu de les écraser ;
5. n'activer une classification patient qu'après preuve suffisante et tests fail-closed.

## PREUVES RÉCUPÉRÉES — TWEED

### Source primaire

Charles H. Tweed. *The Frankfort-Mandibular Incisor Angle (FMIA) in Orthodontic Diagnosis, Treatment Planning and Prognosis.* Angle Orthodontist. 1954;24(3):121-169.

Copie mise à disposition par la Charles H. Tweed International Foundation for Orthodontic Research :
`https://tweedortho.com/wp-content/uploads/2024/12/frankfort-mandibular-incisor-angle.pdf`

### FMA / IMPA

Le texte primaire de Tweed indique explicitement :

- variation du FMA considérée normale par Tweed : **20–30°** ;
- repère (« norm » dans le texte historique) FMA : **25°** ;
- variation de l'inclinaison incisive mandibulaire : **85–95°** ;
- repère IMPA : **90°**.

Conséquence :

- la ligne historique `IMPA 90° ±5` possède désormais une **source primaire directe** Tweed ;
- la ligne historique `FMA 26° ±4` **ne doit pas être attribuée à Tweed** : la source primaire Tweed retrouvée donne 25° avec une variation 20–30°.

### Compensation IMPA

Tweed décrit également une règle dynamique : pour chaque degré dont le FMA dépasse son repère de 25°, l'inclinaison de l'incisive mandibulaire doit être reculée du même nombre de degrés par rapport au repère de 90°. Son exemple explicite est :

`FMA 35° → +10° au-dessus de 25° → IMPA 80°`.

Décision Digital Crown :

- ne pas enregistrer `80–100°` comme une « norme fixe » universelle ;
- **ne pas abandonner la compensation** ;
- la conserver comme règle Tweed historique source-lockée, dépendante du FMA et de la construction géométrique Tweed exacte ;
- le plan mandibulaire Tweed est une tangente au bord inférieur mandibulaire : `Go-Me` et `Go-Gn` ne sont pas des substitutions source-exactes ;
- le Frankfort historique de Tweed ne doit pas être assimilé silencieusement au `Po-Or` générique Digital Crown sans preuve ;
- avant runtime clinique, verrouiller un contrat de tracing source-spécifique Tweed et tester la formule sur cas goldens.

## FMA 26° ±4 — RICKETTS 1981 SOURCE-LOCKÉ

### Source primaire directe

Robert M. Ricketts. *Perspectives in the clinical application of cephalometrics: The first fifty years.* Angle Orthodontist. 1981;51(2):115-150. PMID `6942666`. DOI `10.1043/0003-3219(1981)051<0115:PITCAO>2.0.CO;2`.

Dans le **Cue Sheet for Ricketts' Summary Descriptive Analysis**, le facteur mandibulaire est défini comme `Mandibular plane (FH to Sub. Go.-M.)` avec :

- âge 3 ans : **28° ±4°** ;
- diminution de **1° tous les 3 ans** jusqu'à la maturité ;
- âge 18 ans : **23°**.

La règle primaire donne donc directement à 9 ans :

`28° - 2° = 26°`, avec dispersion historique `±4°`.

Le texte distingue le **true Frankfort** des proxys liés aux ear rods. La source primaire ne permet donc pas de déclarer le `Po-Or` SRPose38 générique automatiquement équivalent à ce true Frankfort.

### Construction Digital Crown source-spécifique V2

Construction versionnée : `RICKETTS_1981_FMA_TRUE_FH_SUBGO_ME_V2`.

Le chemin est volontairement strict. Quatre repères source-spécifiques sont requis sur la même image :

- `RickettsTruePo` ;
- `RickettsTrueOr` ;
- `RickettsSubGo` ;
- `RickettsMe`.

Dans ce lot, chacun doit être `MANUAL`, `CLINICIAN_VALIDATED`, avec `validated_by` et `validated_at`.

Digital Crown refuse :

- `SRPose38 Po-Or → Ricketts true Frankfort` ;
- `Go → RickettsSubGo` ;
- `Go-Me → RickettsSubGo-RickettsMe` ;
- `Go-Gn → RickettsSubGo-RickettsMe` ;
- un repère source-spécifique automatique non certifié ;
- un repère manuel non validé ;
- les axes dégénérés/non finis ;
- les mélanges d'images.

Lorsque ces conditions sont satisfaites, Digital Crown peut calculer le **FMA brut seulement** selon `RickettsTruePo-RickettsTrueOr / RickettsSubGo-RickettsMe`.

**Décision :**

- `26±4° à 9 ans` et sa règle d'âge sont **SOURCE_LOCKED** ;
- la géométrie exacte dispose d'un chemin manuel audité V2 : `SOURCE_LOCKED_MANUAL_CONSTRUCTION_AVAILABLE` ;
- aucune norme patient n'est activée par cette construction ;
- toute future détection automatique des repères source-spécifiques devra être certifiée séparément avant de remplacer cette saisie manuelle ;
- `patient_classification_references()` reste vide.

### Corroboration peer-reviewed et divergence de convention

Des publications peer-reviewed utilisant explicitement l'analyse de Ricketts confirment `26±4°` à 9 ans, mais certaines emploient une convention géométrique moderne `Po-Or / Go-Gn`. Cette divergence ne doit pas écraser la construction de la source primaire.

Source de corroboration : Ravelo et al., *BioMed Research International* 2021, DOI `10.1155/2021/6670191`.

## INTER-INCISIF `131° ±3°` — CONFLIT D'ATTRIBUTION

### Primaires identifiés

- William B. Downs. *Variations in facial relationships; their significance in treatment and prognosis.* American Journal of Orthodontics. 1948;34(10):812-840. DOI `10.1016/0002-9416(48)90015-3`.
- Cecil C. Steiner. *Cephalometrics for you and me.* American Journal of Orthodontics. 1953;39(10):729-755. DOI `10.1016/0002-9416(53)90082-7`.

### Contradiction retrouvée

La revue systématique de Sangalli et al. 2022 (`10.4041/kjod.2022.52.1.53`) rapporte environ **130° pour Steiner** et **135.4° ±5.8° pour Downs**. Une reconstruction peer-reviewed Downs/Steiner 2022 (`10.3390/digital2020008`) donne également **135.4°** pour Downs, avec une dispersion différente. En parallèle, des sources historiques/pédagogiques secondaires diffusent `131±3°` avec attribution variable à Downs ou Steiner.

**Décision :**

- la mesure inter-incisive reste conservée ;
- `131±3°` reste une dette historique visible ;
- aucune attribution Downs ou Steiner n'est source-lockée pour cette valeur exacte ;
- état : `HISTORICAL_ATTRIBUTION_CONFLICT_PRIMARY_REVIEW_REQUIRED` ;
- relire directement les tableaux/textes primaires Downs 1948 et Steiner 1953/1959 avant tout verrouillage numérique ;
- ne jamais fusionner des conventions divergentes en une norme COM unique.

## U1 / FRANCFORT — 107° ±5 — PISTE BALLARD/EASTMAN

La valeur `107° ±5` est retrouvée dans de la littérature clinique peer-reviewed récente comme référence pour l'angle incisive maxillaire / plan de Francfort.

La recherche historique identifie également **Clifford F. Ballard** comme une source majeure de la céphalométrie Eastman et de la position incisive. Sources historiques/peer-reviewed identifiées :

- Ballard CF. *Some bases for aetiology and diagnosis in orthodontics.* Dental Record. 1948;68:133-145 ;
- Ballard CF. travaux 1951/1953 sur diagnostic et morphologie ;
- MacAllister MJ, Rock WP. *The Eastman Standard Incisor Angulations: Are They still Appropriate?* British Journal of Orthodontics. 1992;19(1):55-58. DOI `10.1179/bjo.19.1.55`.

MacAllister & Rock confirment que les « Eastman Standard values » ont une histoire Ballard/Eastman mais soulignent que leur dérivation exacte était déjà difficile à reconstruire. Les documents pédagogiques francophones attribuent souvent `I/F ≈107°` à Ballard, avec des dispersions rapportées de `±2`, `±3` ou `±5` selon les sources. En outre, les standards Eastman publiés utilisent aussi des mesures incisives sur le **plan maxillaire**, qui ne sont pas interchangeables avec `U1-FH`.

Décision :

- conserver `U1-FH` comme mesure ;
- conserver `107±5` comme référence historique à sourcer ;
- **ne pas fusionner** `U1-FH` avec une mesure Eastman `UI/MX` ou une référence CRANIOM ;
- poursuivre jusqu'au primaire exact définissant **le plan de Francfort + la valeur + la dispersion** avant activation.

La plage historique `97–120°` reste une dette distincte : aucune source exacte n'a été retrouvée lors des recherches ciblées ; elle ne doit pas être reconstruite artificiellement depuis `107±5`.

## PLAGE INTER-INCISIVE 120–142°

Recherche ciblée effectuée sur la plage exacte et sur les termes « compensation interincisive » : **aucune source primaire ou peer-reviewed fiable n'a été retrouvée pour `120–142°` comme plage normative/compensatoire exacte**.

Cette absence de résultat ne supprime pas la ligne.

Décision :
- conserver la plage historique comme dette scientifique ;
- ne pas la dériver de `131±3`, `131±5`, `130±6` ou d'une autre convention ;
- poursuivre par les sources historiques de l'école qui a produit la fiche COM.

## SURPLOMB / RECOUVREMENT

Des cohortes peer-reviewed de sujets à occlusion normale non traitée montrent des valeurs de surplomb et recouvrement autour de 2 mm, avec variation liée à l'âge, à la population et au protocole. Par exemple, une étude brésilienne d'adultes à occlusion normale rapporte en moyenne environ **1.92 mm d'overjet** et **2.45 mm d'overbite** ; des cohortes longitudinales montrent également une variabilité importante avec l'âge.

Conséquence : la plage historique `1.5–3 mm` est plausible comme convention clinique mais **ne peut pas être déclarée universelle** sur cette seule base.

Décision :

- mesures surplomb/recouvrement conservées ;
- références de population doivent être versionnées ;
- la plage `1.5–3` reste à rattacher à sa source historique exacte ou à être remplacée par une référence populationnelle explicitement sourcée ;
- jamais de suppression silencieuse.

## CRANIOM — CE QUI EST DÉJÀ PRIMAIREMENT VERROUILLÉ

Sources éditeur :

- Bonnefont R, Casteigt J, Ernoult J-F, Sorel O. 2010. DOI `10.1051/odfen/2010406`.
- Bonnefont R, Ernoult J-F, Sorel O. 2011. DOI `10.1051/odfen/2011104`.

Les surfaces éditeur Cambridge/JDAO confirment l'étude de **83 jeunes adultes en Classe I non traités** et les extrêmes :

- incisive mandibulaire / plan mandibulaire de Downs : **78–114°** ;
- incisive maxillaire / Francfort : **97.5–130.1°**.

Les auteurs précisent que les mesures osseuses décrivent des typologies plutôt que des anomalies automatiques et placent la céphalométrie après l'évaluation esthétique, parodontale et musculaire.

Ces références restent donc descriptives et ne constituent pas à elles seules une règle diagnostique patient.

## CRANIOM — VALEURS À RÉCUPÉRER, PAS À ABANDONNER

Les valeurs suivantes restent dans la queue scientifique jusqu'au verrouillage numérique primaire direct et/ou de construction :

- `A'B' 9 ans +4.2 ±3.2 mm` ;
- `A'B' adulte +2.3 ±3.1 mm` ;
- `A / verticale N 9 ans +2.8 ±3.3 mm` ;
- `A / verticale N adulte +2.3 ±3.0 mm` avec divergence de transcription `±3.3` dans certaines reproductions ;
- `B / verticale N 9 ans -1.5 ±4.5 mm` ;
- `B / verticale N adulte 0.0 ±4.9 mm` ;
- profondeur faciale `S → verticale N` à 9 ans `61.3 ±5 mm` versus texte arrondi `62±5` ;
- profondeur faciale adulte `70.3 ±5 mm` ;
- construction/orientation NHP pour `A''B''` lorsqu'elle est utilisée au lieu de `A'B'`.

Les surfaces éditeur des deux articles CRANIOM confirment actuellement les extrêmes incisifs, mais n'exposent pas dans leurs abstracts les tableaux numériques linéaires ci-dessus. Le document technique CRANIOM les reproduit ; leur activation normative attend néanmoins une lecture directe du tableau primaire ou une source de même niveau.

## BACKLOG COMPLET — AUCUNE LIGNE SUPPRIMÉE

| Élément historique | État récupération | Next exact |
|---|---|---|
| Surplomb `1.5–3 mm` | mesure conservée, population-dépendance confirmée | retrouver source historique exacte ou définir référence populationnelle versionnée |
| Recouvrement `1.5–3 mm` | mesure conservée, population-dépendance confirmée | idem |
| IMPA `90±5°` | **source primaire Tweed retrouvée ; géométrie source-exacte toujours bloquée** | versionner tracing Tweed historique, sans Go-Me/Go-Gn ni Po-Or générique silencieux |
| Compensation IMPA `80–100°` | **règle dynamique Tweed retrouvée**, plage fixe non prouvée | coder seulement la règle source-spécifique après construction Tweed certifiée |
| U1-FH `107±5°` | corroboré peer-reviewed ; piste Ballard/Eastman identifiée ; plan/dispersion primaire encore ouverts | verrouiller primaire exact U1-FH, sans confondre UI/MX |
| Compensation U1-FH `97–120°` | recherche exacte négative à ce stade | rechercher archives/sources de l'école COM ; ne pas dériver arithmétiquement |
| Inter-incisif `131±3°` | **conflit d'attribution/normes : Downs primaire identifié, Steiner primaire identifié, synthèses divergentes** | relire primaires Downs/Steiner et conserver références source-spécifiques séparées |
| Compensation inter-incisif `120–142°` | recherche exacte négative à ce stade | rechercher archives/sources de l'école COM ; ne pas reconstruire depuis une moyenne ± ET |
| FMA `26±4° à 9 ans` | **source primaire Ricketts 1981 + chemin géométrique manuel V2 audité disponibles** | certifier exact-head ; garder classification inactive ; toute automatisation des repères Ricketts source-spécifiques exige une certification dédiée |
| A'B' 9 ans | technique concordant | récupérer numérique primaire direct |
| A'B' adulte | technique concordant | récupérer numérique primaire direct |
| A/N vertical 9 ans | technique concordant | récupérer numérique primaire direct |
| A/N vertical adulte | divergence `±3.0/±3.3` | résoudre sur publication primaire/table originale |
| B/N vertical 9 ans | technique concordant | récupérer numérique primaire direct |
| B/N vertical adulte | technique concordant | récupérer numérique primaire direct |
| S/N vertical profondeur 9 ans | divergence `61.3/62` | résoudre table primaire + sémantique construction |
| S/N vertical profondeur adulte | technique concordant | récupérer numérique primaire direct + construction |

## RÈGLE D'ACTIVATION

Pour chaque ligne :

`source primaire/forte + définition géométrique exacte + population/contexte + unité + version + tests → référence activable éventuelle`

Sinon :

`mesure conservée + provenance + état BLOCKED/UNKNOWN + dette scientifique explicite`.

Une construction manuelle auditée peut rendre une **mesure brute** calculable sans rendre sa **norme** automatiquement active.

**BLOCKED n'est jamais synonyme de DROPPED.**

## NEXT EXACT

1. certifier exact-head le chemin Ricketts 1981 V2 `RickettsTruePo-RickettsTrueOr / RickettsSubGo-RickettsMe` avec quatre repères manuels validés ;
2. verrouiller le contrat de tracing source-spécifique Tweed avant toute utilisation de la règle de compensation IMPA ;
3. relire directement les primaires Downs 1948 et Steiner 1953/1959 pour résoudre l'attribution/dispersion de l'inter-incisif `131±3°` ;
4. retrouver le primaire exact de `U1-FH 107±5` dans la filiation Ballard/Eastman sans confondre le plan maxillaire et Francfort ;
5. rechercher dans les archives/sources COM les plages exactes `97–120°` et `120–142°` ;
6. récupérer les tableaux numériques CRANIOM primaires pour les valeurs linéaires 9 ans/adulte ;
7. seulement ensuite modifier `cephalo_norm_registry.py` ou activer une règle clinique ;
8. conserver des tests négatifs empêchant toute promotion silencieuse d'une dette scientifique en norme patient.
