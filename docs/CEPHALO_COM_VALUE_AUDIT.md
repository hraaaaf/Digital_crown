# CÉPHALOMÉTRIE — COM / CRANIOM VALUE SOURCE LOCK

**Statut :** audit scientifique préalable à R11  
**Parent canonique :** `docs/CEPHALO_DIAGNOSTIC_SPEC.md`  
**Branche :** `feat/cephalo-r11-diagnostic-multiaxial`

## GOAL

Vérifier chaque valeur numérique visible sur la fiche historique « Fiche de mesures céphalométriques du C.O.M. » fournie le 2026-09-12 avant toute utilisation dans Digital Crown.

**Succès observable :** aucune valeur de la fiche n'est transformée en norme patient, règle diagnostique ou plage de compensation sans source explicite, méthode/construction compatible et statut de preuve documenté.

## HIÉRARCHIE DE PREUVE

1. article primaire peer-reviewed avec valeur numérique directement vérifiable ;
2. document technique du groupe/auteurs CRANIOM, utile pour reproduire la méthode mais insuffisant seul pour activer une norme clinique ;
3. littérature peer-reviewed secondaire/conventionnelle, utile pour identifier une convention mais pas pour attribuer une valeur à CRANIOM ;
4. fiche historique fournie, conservée comme trace documentaire mais jamais utilisée seule comme source normative.

Statuts utilisés :
- `PRIMARY_SOURCE_LOCKED` : valeur numérique directement verrouillée sur une source primaire ;
- `TECHNICAL_SOURCE_MATCH_INERT` : valeur retrouvée dans le document technique CRANIOM mais non admise seule comme norme patient ;
- `CONVENTIONAL_REFERENCE_ONLY` : valeur corroborée dans la littérature comme convention d'une autre école ou d'usage courant ;
- `HISTORICAL_ONLY_BLOCKED` : valeur/plage retrouvée uniquement sur la fiche historique ou sans source suffisamment forte ;
- `DIVERGENT_BLOCKED` : sources retrouvées non concordantes ;
- `CONSTRUCTION_BLOCKED` : valeur potentiellement sourcée mais construction Digital Crown non compatible/certifiée.

## SOURCES VERROUILLÉES

### CRANIOM primaire

- Bonnefont R, Casteigt J, Ernoult J-F, Sorel O. *A new method for the utilization of cephalometric measurements in orthodontics or how standard deviations can sometimes be the practitioner's false friends (Part 1).* J Dentofacial Anom Orthod. 2010;13(4):385-400. DOI `10.1051/odfen/2010406`.
- Bonnefont R, Ernoult J-F, Sorel O. *A new method of using cephalometric measurements in orthodontics (part 2) or how standard deviations can be the practitioner's false friends.* J Dentofacial Anom Orthod. 2011;14:105. DOI `10.1051/odfen/2011104`.

Les articles portent sur 83 jeunes adultes en classe I, non traités orthodontiquement. Ils publient directement les plages extrêmes suivantes :
- incisive mandibulaire / plan mandibulaire de Downs : `78–114°` ;
- incisive maxillaire / Francfort : `97.5–130.1°`.

Ces deux plages sont déjà présentes dans `cephalo_norm_registry.py` comme références `EXTREME_RANGE`, descriptives et inactives pour la classification patient.

### Document technique CRANIOM

Document : `https://www.slot-concept.com/bases/slot_communication_pdf/7/fichier.pdf`.

Il reproduit les tableaux détaillés CRANIOM, y compris moyennes, écarts-types, intervalles à 1 ET et valeurs extrêmes. Il reste classé `SECONDARY_TECHNICAL` dans le registre Digital Crown et ne suffit pas seul à activer une classification patient.

## MATRICE DE VÉRIFICATION DE LA FICHE HISTORIQUE

| Mesure fiche | Valeur fiche | Contrôle retrouvé | Statut | Décision Digital Crown |
|---|---:|---|---|---|
| Surplomb | `1.5–3 mm` | CRANIOM technique : moyenne `2.6 ± 0.7 mm`, 1 ET `1.9–3.3`, extrêmes `1.1–4.7` | `HISTORICAL_ONLY_BLOCKED` | Ne pas enregistrer `1.5–3` comme norme CRANIOM |
| Recouvrement | `1.5–3 mm` | CRANIOM technique : moyenne `2.5 ± 1.0 mm`, 1 ET `1.4–3.6`, extrêmes `0.8–5.1` | `HISTORICAL_ONLY_BLOCKED` | Ne pas enregistrer `1.5–3` comme norme CRANIOM |
| I / mandibulaire | `90° ±5` | Littérature Tweed/orthodontique : `IMPA 90° ±5°` est une convention couramment rapportée ; CRANIOM technique adulte : `94.4 ±7.5`, extrêmes `78–114` | `CONVENTIONAL_REFERENCE_ONLY` | Ne pas attribuer `90±5` à CRANIOM ; plage primaire CRANIOM 78–114 déjà enregistrée |
| Compensation I / mandibulaire | `80–100°` | Aucune source forte retrouvée pour cette plage exacte ; elle correspond arithmétiquement à `90±10` mais cela n'est pas une preuve | `HISTORICAL_ONLY_BLOCKED` | Bloqué |
| I / Francfort | `107° ±5` | Valeur `107°` fréquemment rapportée comme référence conventionnelle U1-FH ; CRANIOM technique adulte : `113.7 ±6.8`; primaire CRANIOM : extrêmes `97.5–130.1` | `CONVENTIONAL_REFERENCE_ONLY` | Ne pas attribuer `107±5` à CRANIOM ; plage primaire CRANIOM déjà enregistrée |
| Compensation I / Francfort | `97–120°` | Aucune source forte retrouvée pour cette plage exacte ; CRANIOM primaire publie au contraire `97.5–130.1°` comme plage extrême | `HISTORICAL_ONLY_BLOCKED` | Bloqué |
| Inter-incisif | `131° ±3` | `131°` est une valeur historique/conventionnelle rapportée ; littérature moderne fréquemment `131±5` ou `130±6`; CRANIOM technique adulte `132.7 ±9.6`, extrêmes `112.5–159` | `DIVERGENT_BLOCKED` | Ne pas enregistrer `131±3` sans source primaire exacte et méthode lockée |
| Compensation inter-incisif | `120–142°` | Aucune source forte retrouvée pour cette plage exacte ; ne correspond pas aux extrêmes CRANIOM | `HISTORICAL_ONLY_BLOCKED` | Bloqué |
| Angle de Tweed / FMA | `26° ±4` (`22–30`) | Valeur `26±4` présente dans plusieurs publications cliniques comme référence conventionnelle ; les publications utilisent aussi `25±3/4` ou d'autres références | `CONVENTIONAL_REFERENCE_ONLY` + `CONSTRUCTION_BLOCKED` | Pas d'activation : le runtime historique `Angle_de_Tweed` emploie `Go-Me`, alors que le contrat Tweed exact n'est pas source-locké |
| A'B' 9 ans | `+4.2 ±3.2 mm` (`+1.0..+7.4`) | Correspond exactement au document technique CRANIOM | `TECHNICAL_SOURCE_MATCH_INERT` | Mesure géométrique possible ; classification/norme inactive jusqu'à source numérique primaire directe |
| A'B' adulte | `+2.3 ±3.1 mm` (`-0.8..+5.4`) | Correspond exactement au document technique CRANIOM | `TECHNICAL_SOURCE_MATCH_INERT` | Même décision |
| A / verticale N, 9 ans | `+2.8 ±3.3 mm` (`-0.5..+6.1`) | Correspond au document technique CRANIOM | `TECHNICAL_SOURCE_MATCH_INERT` | Mesure possible ; norme inactive |
| A / verticale N, adulte | `+2.3 ±3.0 mm` (`-0.7..+5.3`) | Tableau technique CRANIOM : `+2.3 ±3.0`; texte technique/secondaires comportent aussi des transcriptions `±3.3` | `DIVERGENT_BLOCKED` | Ne pas activer la statistique adulte avant verrouillage sur table/source primaire |
| B / verticale N, 9 ans | `-1.5 ±4.5 mm` (`-6..+3`) | Correspond au document technique CRANIOM | `TECHNICAL_SOURCE_MATCH_INERT` | Mesure possible ; norme inactive |
| B / verticale N, adulte | `0.0 ±4.9 mm` (`-4.9..+4.9`) | Correspond au document technique CRANIOM | `TECHNICAL_SOURCE_MATCH_INERT` | Mesure possible ; norme inactive |
| Profondeur faciale S → verticale N, 9 ans | `61.3 ±5 mm` (`56.3..66.3`) | Tableau technique affiche `61.3` et `56.3..66.3`, mais le texte du même document donne `62±5`, `57..67`; d'autres reproductions donnent encore d'autres écarts-types | `DIVERGENT_BLOCKED` + sémantique construction à confirmer | Bloqué |
| Profondeur faciale S → verticale N, adulte | `70.3 ±5 mm` (`65.3..75.3`) | Tableau technique concordant ; texte technique arrondi `70±5`, `65..75` | `TECHNICAL_SOURCE_MATCH_INERT` | Norme inactive ; garder géométrie séparée de la référence |

## POINTS IMPORTANTS DE MÉTHODE

### 1. La fiche historique n'est pas le registre normatif

Elle mélange des valeurs conventionnelles anciennes (`90±5`, `107±5`, `131±3`, `26±4`), des plages dites de compensation et des valeurs qui recoupent le futur CRANIOM. Ces familles de nombres ne doivent pas être fusionnées sous une même notion de « norme ».

### 2. CRANIOM n'utilise pas la même philosophie

Les articles CRANIOM insistent sur les valeurs extrêmes observées dans leur échantillon et sur le fait que les mesures osseuses décrivent des typologies plutôt que des anomalies automatiques. Une valeur hors moyenne ±1 ET ne doit donc pas être transformée automatiquement en diagnostic.

### 3. Géométrie ≠ norme

Digital Crown peut calculer une mesure dès lors que sa construction et sa calibration sont vérifiées. Cela n'autorise pas automatiquement une comparaison normative.

Constructions déjà versionnées :
- `CRANIOM_AB_PRIME_V1` ;
- `CRANIOM_A_TO_N_VERTICAL_V1` ;
- `CRANIOM_B_TO_N_VERTICAL_V1` ;
- `CRANIOM_S_TO_N_VERTICAL_DEPTH_V1`.

La dernière reste `GEOMETRY_VERIFIED_SOURCE_SEMANTICS_TO_CONFIRM` dans le registre de constructions et ne doit pas alimenter une règle diagnostique.

### 4. Plan mandibulaire fail-closed

`cephalo_engine.py` calcule encore le champ legacy `Angle_de_Tweed` avec `Go-Me`. Le registre de constructions documente explicitement que cette géométrie n'est pas une mesure Tweed certifiée. Aucune norme Tweed/FMA ne doit y être branchée tant que la construction source-spécifique n'est pas verrouillée.

## CONSÉQUENCE POUR R11

Aucune règle de `FindingEvidence` ne doit être créée à partir d'une valeur `HISTORICAL_ONLY_BLOCKED`, `DIVERGENT_BLOCKED` ou `CONSTRUCTION_BLOCKED`.

Les valeurs `TECHNICAL_SOURCE_MATCH_INERT` peuvent être documentées et liées à la méthode, mais ne doivent pas produire de classification patient tant qu'une référence numérique primaire directement vérifiée n'est pas admise dans `cephalo_norm_registry.py`.

Les deux plages CRANIOM déjà `PRIMARY_SOURCE_LOCKED` (`78–114°`, `97.5–130.1°`) restent elles-mêmes descriptives/inactives conformément au registre R10 : aucun finding patient automatique n'est autorisé tant que `active_for_patient_classification=False`.

## NEXT EXACT

1. auditer le contrat `FindingEvidence` / `DiagnosticHypothesisEvidence` déjà présent ;
2. définir le moteur R11 comme un moteur de règles versionnées qui consomme uniquement des `NormativeEvaluationEvidence` autorisées ou des observations non normatives explicitement sourcées ;
3. préserver `UNKNOWN` / `NOT_COMPUTABLE` et les contradictions ;
4. n'introduire aucune valeur COM bloquée dans le runtime diagnostique ;
5. ajouter des cas goldens fail-closed avant toute règle clinique activable.
