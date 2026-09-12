# CÉPHALOMÉTRIE — RÉCUPÉRATION DES MESURES / NO-DROP POLICY

**Date :** 2026-09-12  
**Parent :** `docs/CEPHALO_DIAGNOSTIC_SPEC.md`  
**Audit source :** `docs/CEPHALO_COM_VALUE_AUDIT.md`  
**Complément primaire Ricketts :** `docs/CEPHALO_COM_PRIMARY_RECOVERY_RICKETTS_1981.md`

## RÈGLE CANONIQUE

**Aucune mesure n'est abandonnée.**

Une mesure insuffisamment sourcée, ambiguë ou non constructible reste une **dette scientifique active**. Un blocage signifie seulement : ne pas produire de classification clinique non prouvée.

`mesure calculable != référence normative prouvée != finding clinique != diagnostic != indication != traitement`

**BLOCKED != DROPPED.**

## GOAL

Pour chaque ligne COM/CRANIOM historique :

1. verrouiller la construction géométrique ;
2. verrouiller la source numérique ou la règle source-spécifique ;
3. expliciter âge/population/contexte ;
4. conserver les divergences ;
5. n'activer une classification patient qu'après source + construction + contexte + version + tests + revue.

## PREUVES RÉCUPÉRÉES — TWEED

### Source primaire

Charles H. Tweed. *The Frankfort-Mandibular Incisor Angle (FMIA) in Orthodontic Diagnosis, Treatment Planning and Prognosis.* Angle Orthodontist. 1954;24(3):121-169.

Le texte primaire verrouille :

- FMA historique Tweed : variation **20–30°**, repère **25°** ;
- inclinaison incisive mandibulaire : **85–95°**, repère IMPA **90°** ;
- règle dynamique : pour chaque degré de FMA au-dessus de 25°, l'IMPA cible diminue d'un degré ;
- exemple primaire : `FMA 35° → IMPA 80°`.

Décisions :

- `IMPA 90±5°` : **numérique source-locké**, construction Tweed exacte encore à verrouiller ;
- `80–100°` : **ne pas l'enregistrer comme plage normative fixe** ; conserver la règle dynamique source-spécifique ;
- ne jamais brancher ces références sur un `Go-Me` legacy sans équivalence géométrique démontrée.

## PREUVES RÉCUPÉRÉES — RICKETTS / FMA 26±4°

### Source primaire directe

Robert M. Ricketts. *Perspectives in the clinical application of cephalometrics: The first fifty years.* Angle Orthodontist. 1981;51(2):115-150. PMID `6942666`. DOI `10.1043/0003-3219(1981)051<0115:PITCAO>2.0.CO;2`.

Le **Cue Sheet for Ricketts' Summary Descriptive Analysis** donne :

- facteur : `Mandibular plane (FH to Sub. Go.-M.)` ;
- âge 3 ans : **28° ±4°** ;
- évolution : **−1° tous les 3 ans** jusqu'à la maturité ;
- âge 18 ans : **23°**.

Donc, à 9 ans :

`28° - 2° = 26°`, dispersion historique `±4°`.

**État vérifié :**

- `26±4° à 9 ans` : **SOURCE_LOCKED** ;
- règle d'âge : **SOURCE_LOCKED** ;
- construction : **BLOCKED** tant que Digital Crown n'implémente pas exactement le vrai Francfort et `Subgonion-Menton`.

### Divergence géométrique à préserver

Des publications peer-reviewed modernes utilisent la référence Ricketts `26±4°` avec d'autres constructions, notamment `Po-Or / Go-Gn`. Cette convention moderne n'autorise pas à réécrire rétroactivement la géométrie de la source primaire 1981.

Décision Digital Crown :

- gate : `RICKETTS_TRUE_FH_SUBGONION_MENTON_EXACT_REQUIRED` ;
- aucun remplacement silencieux par `Go-Me` ou `Go-Gn` ;
- aucune activation patient avant construction versionnée + goldens + revue.

## PREUVES RÉCUPÉRÉES — DOWNS / INTER-INCISIF

William B. Downs. *Variations in facial relationships; their significance in treatment and prognosis.* American Journal of Orthodontics. 1948;34(10):812-840. DOI `10.1016/0002-9416(48)90015-3`.

La source primaire est identifiée et l'attribution historique secondaire `131° ±3°` est retrouvée, mais la valeur exacte n'a pas encore été relue directement dans le tableau/texte primaire.

Décision : `131±3°` reste **PRIMARY_IDENTIFIED_NUMERIC_UNVERIFIED** et non activable.

## U1 / FRANCFORT — 107° ±5 — BALLARD/EASTMAN

La référence `107° ±5°` est corroborée dans la littérature clinique, avec une filiation Ballard/Eastman, mais la dérivation primaire exacte, le plan de référence et la dispersion ne sont pas encore verrouillés.

Sources historiques identifiées :

- Ballard CF. *Some bases for aetiology and diagnosis in orthodontics.* Dental Record. 1948;68:133-145 ;
- MacAllister MJ, Rock WP. *The Eastman Standard Incisor Angulations: Are They still Appropriate?* British Journal of Orthodontics. 1992;19(1):55-58. DOI `10.1179/bjo.19.1.55`.

Décisions :

- conserver `U1-FH` ;
- ne pas confondre `U1-FH` avec `UI/MX` Eastman ;
- `107±5°` reste source primaire exacte à récupérer ;
- `97–120°` reste une dette distincte, non reconstructible arithmétiquement.

## PLAGE INTER-INCISIVE 120–142°

Aucune source primaire ou peer-reviewed suffisamment fiable n'a été retrouvée pour cette plage exacte.

Décision : conserver la dette, ne pas la reconstruire depuis `131±3`, `131±5`, `130±6` ou une autre convention.

## SURPLOMB / RECOUVREMENT

La plage historique `1.5–3 mm` est plausible mais dépend de la population, de l'âge et du protocole.

Décision :

- mesures conservées ;
- aucune universalisation de `1.5–3 mm` ;
- rattacher la valeur historique à sa source exacte ou utiliser une référence populationnelle explicitement versionnée.

## CRANIOM — PRIMAIRE VERROUILLÉ

Sources :

- Bonnefont R, Casteigt J, Ernoult J-F, Sorel O. 2010. DOI `10.1051/odfen/2010406` ;
- Bonnefont R, Ernoult J-F, Sorel O. 2011. DOI `10.1051/odfen/2011104`.

Les publications concernent **83 jeunes adultes Classe I non traités** et verrouillent notamment les extrêmes :

- incisive mandibulaire / plan mandibulaire de Downs : **78–114°** ;
- incisive maxillaire / Francfort : **97.5–130.1°**.

Ces plages restent descriptives et inactives pour une classification patient automatique.

## CRANIOM — VALEURS LINÉAIRES EN RÉCUPÉRATION

Le document technique CRANIOM reproduit les valeurs suivantes, mais elles ne sont pas promues en normes primaires tant que les tableaux primaires directs ne sont pas relus :

- `A'B' 9 ans +4.2 ±3.2 mm` ;
- `A'B' adulte +2.3 ±3.1 mm` ;
- `A / verticale N 9 ans +2.8 ±3.3 mm` ;
- `A / verticale N adulte +2.3 ±3.0 mm`, avec divergence secondaire `±3.3` ;
- `B / verticale N 9 ans -1.5 ±4.5 mm` ;
- `B / verticale N adulte 0.0 ±4.9 mm` ;
- profondeur faciale `S → verticale N` à 9 ans `61.3 ±5 mm`, versus texte arrondi `62±5` ;
- profondeur faciale adulte `70.3 ±5 mm`.

Constructions déjà versionnées :

- `CRANIOM_AB_PRIME_V1` ;
- `CRANIOM_A_TO_N_VERTICAL_V1` ;
- `CRANIOM_B_TO_N_VERTICAL_V1` ;
- `CRANIOM_S_TO_N_VERTICAL_DEPTH_V1`.

La profondeur faciale reste dépendante de la confirmation des sémantiques source.

## BACKLOG COMPLET — 17/17, AUCUNE LIGNE SUPPRIMÉE

| Élément historique | État récupération | Next exact |
|---|---|---|
| Surplomb `1.5–3 mm` | population-dépendant, source universelle non verrouillée | source historique ou référence populationnelle versionnée |
| Recouvrement `1.5–3 mm` | population-dépendant, source universelle non verrouillée | idem |
| IMPA `90±5°` | **source primaire Tweed verrouillée** | construction Tweed exacte + goldens |
| Compensation IMPA `80–100°` | **règle dynamique Tweed verrouillée**, plage fixe rejetée | construction Tweed exacte puis règle source-spécifique |
| U1-FH `107±5°` | corroboration peer-reviewed, primaire exact ouvert | verrouiller plan + valeur + dispersion primaire |
| Compensation U1-FH `97–120°` | source exacte non retrouvée | archives COM, aucune dérivation artificielle |
| Inter-incisif `131±3°` | Downs primaire identifié, numérique direct non relu | relire tableau/texte primaire |
| Compensation inter-incisif `120–142°` | source exacte non retrouvée | archives COM, aucune reconstruction |
| FMA `26±4° à 9 ans` | **Ricketts 1981 primaire verrouillé ; construction bloquée** | `true FH / Subgonion-Menton` versionné + goldens |
| A'B' 9 ans | technique concordant, primaire numérique direct ouvert | récupérer tableau primaire |
| A'B' adulte | technique concordant, primaire numérique direct ouvert | récupérer tableau primaire |
| A/N vertical 9 ans | technique concordant, primaire numérique direct ouvert | récupérer tableau primaire |
| A/N vertical adulte | divergence `±3.0/±3.3` | résoudre sur tableau primaire |
| B/N vertical 9 ans | technique concordant, primaire numérique direct ouvert | récupérer tableau primaire |
| B/N vertical adulte | technique concordant, primaire numérique direct ouvert | récupérer tableau primaire |
| S/N vertical profondeur 9 ans | divergence `61.3/62` | résoudre tableau primaire + sémantique |
| S/N vertical profondeur adulte | technique concordant | récupérer tableau primaire + confirmer construction |

## RÈGLE D'ACTIVATION

`source primaire/forte + définition géométrique exacte + population/contexte + unité + version + tests + revue → référence activable éventuelle`

Sinon :

`mesure conservée + provenance + état BLOCKED/UNKNOWN + dette scientifique explicite`.

Aucun item de ce backlog ne devient automatiquement finding, diagnostic, indication ou traitement.

## NEXT EXACT

1. implémenter/versionner la construction Ricketts `true FH / Subgonion-Menton` et ses goldens ;
2. verrouiller la construction Tweed avant la règle dynamique IMPA ;
3. récupérer le primaire exact `U1-FH 107±5°` ;
4. poursuivre les archives COM pour `97–120°` et `120–142°` ;
5. récupérer les tableaux CRANIOM primaires pour les huit valeurs linéaires ;
6. seulement après preuve suffisante, modifier un registre normatif ou activer une règle clinique ;
7. conserver les tests négatifs empêchant toute promotion silencieuse.
