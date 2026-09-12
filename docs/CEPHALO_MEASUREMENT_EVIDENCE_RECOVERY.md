# CÉPHALOMÉTRIE — RÉCUPÉRATION DES MESURES / NO-DROP POLICY

**Date :** 2026-09-12  
**Parent :** `docs/CEPHALO_DIAGNOSTIC_SPEC.md`  
**Audit source :** `docs/CEPHALO_COM_VALUE_AUDIT.md`

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
3. définir population/âge/sex/contexte si nécessaire ;
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
- la ligne historique `FMA 26° ±4` **ne doit pas être attribuée à Tweed** : la source primaire Tweed retrouvée donne 25° avec une variation 20–30°. `26±4` appartient à une autre convention/école dans la littérature et doit rester séparé.

### Compensation IMPA

Tweed décrit également une règle dynamique : pour chaque degré dont le FMA dépasse son repère de 25°, l'inclinaison de l'incisive mandibulaire doit être reculée du même nombre de degrés par rapport au repère de 90°. Son exemple explicite est :

`FMA 35° → +10° au-dessus de 25° → IMPA 80°`.

Décision Digital Crown :

- ne pas enregistrer `80–100°` comme une « norme fixe » universelle ;
- **ne pas abandonner la compensation** ;
- la conserver comme règle Tweed historique source-lockée, dépendante du FMA et de la construction géométrique Tweed exacte ;
- avant runtime clinique, verrouiller la construction du plan mandibulaire Tweed et tester la formule sur cas goldens.

## PREUVES RÉCUPÉRÉES — DOWNS / INTER-INCISIF

### Source primaire bibliographique

William B. Downs. *Variations in facial relationships; their significance in treatment and prognosis.* American Journal of Orthodontics. 1948;34(10):812-840. DOI `10.1016/0002-9416(48)90015-3`.

PubMed et ScienceDirect verrouillent l'article primaire et son échantillon de sujets à excellente occlusion.

Une publication orthodontique secondaire historique attribue explicitement à Downs la valeur **131° ±3°** pour l'angle inter-incisif.

État : **source primaire identifiée, valeur exacte encore à relire directement dans le texte/tableau primaire avant activation numérique**.

Décision : la mesure et la référence historique `131±3` restent dans la file de récupération ; elles ne sont pas supprimées.

## U1 / FRANCFORT — 107° ±5

La valeur `107° ±5` est retrouvée dans de la littérature clinique peer-reviewed comme référence pour l'angle incisive maxillaire / plan de Francfort. Cependant la filiation primaire exacte de cette valeur n'est pas encore verrouillée.

Décision :

- conserver `U1-FH` comme mesure ;
- conserver `107±5` comme référence historique à sourcer ;
- ne pas la présenter comme norme CRANIOM ;
- rechercher l'analyse/école primaire qui définit précisément ce repère avant activation.

La plage historique `97–120°` reste une dette distincte : elle ne doit pas être reconstruite artificiellement depuis `107±5`.

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

Ces références restent descriptives et ne constituent pas à elles seules une règle diagnostique patient.

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

Le manuscrit/audit technique CRANIOM reproduit plusieurs de ces valeurs, mais l'activation normative attend une vérification directe sur la publication primaire ou une source de même niveau.

## BACKLOG COMPLET — AUCUNE LIGNE SUPPRIMÉE

| Élément historique | État récupération | Next exact |
|---|---|---|
| Surplomb `1.5–3 mm` | mesure conservée, source exacte ouverte | retrouver source historique exacte ou définir référence populationnelle versionnée |
| Recouvrement `1.5–3 mm` | mesure conservée, source exacte ouverte | idem |
| IMPA `90±5°` | **source primaire Tweed retrouvée** | verrouiller construction Tweed puis tests |
| Compensation IMPA `80–100°` | **règle dynamique Tweed retrouvée**, plage fixe non prouvée | coder seulement la règle source-spécifique après construction certifiée |
| U1-FH `107±5°` | corroboré peer-reviewed, primaire d'origine ouvert | identifier source primaire/école exacte |
| Compensation U1-FH `97–120°` | ouverte | rechercher source primaire exacte ; ne pas dériver arithmétiquement |
| Inter-incisif `131±3°` | source primaire Downs identifiée + attribution secondaire exacte | relire valeur directement dans primaire avant activation |
| Compensation inter-incisif `120–142°` | ouverte | recherche source exacte / logique de compensation |
| FMA `26±4°` | divergence d'attribution clarifiée | séparer Tweed `25°, 20–30` de la convention `26±4` et sourcer cette dernière |
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

**BLOCKED n'est jamais synonyme de DROPPED.**

## NEXT EXACT

1. poursuivre l'acquisition des sources primaires exactes pour les lignes ouvertes ci-dessus ;
2. verrouiller la construction Tweed/FMA avant toute utilisation de la règle de compensation IMPA ;
3. résoudre la filiation primaire `U1-FH 107±5` et les deux plages de compensation maxillaire/inter-incisive ;
4. récupérer les tableaux numériques CRANIOM primaires pour les valeurs linéaires 9 ans/adulte ;
5. seulement ensuite modifier `cephalo_norm_registry.py` ou activer une règle clinique ;
6. conserver des tests négatifs empêchant toute promotion silencieuse d'une dette scientifique en norme patient.
