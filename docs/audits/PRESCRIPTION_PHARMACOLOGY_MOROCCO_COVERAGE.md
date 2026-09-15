# Prescription Pharmacology Morocco Coverage

Status: ACTIVE — M0 SCIENTIFIC MAPPING

## Goal

Construire une couverture pharmacologique dentaire exhaustive pour Digital Crown, systématiquement sourcée Maroc, sans inventer d’indication, de schéma, de statut réglementaire ou de disponibilité.

M0 est volontairement non-clinique au runtime : aucune nouvelle posologie ni nouvelle auto-proposition n’est activée avant validation de la matrice scientifique.

## Success

M0 est clos uniquement lorsque chaque domaine pharmacologique dentaire pertinent possède une ligne canonique avec, au minimum :

- DCI / composition canonique ;
- indication ou contexte dentaire ;
- voie / forme / présentation ;
- population, âge et poids lorsqu’ils déterminent le schéma ;
- grossesse / allaitement ;
- insuffisance rénale / hépatique ;
- allergies et interactions majeures pertinentes ;
- statut AMM Maroc par présentation ;
- statut de commercialisation AMMPS par présentation ;
- source RCP Maroc et date de vérification ;
- source dentaire marocaine lorsqu’elle existe ;
- source internationale de cross-check lorsqu’elle est nécessaire ;
- niveau d’automatisation et justification ;
- gap explicite lorsqu’une preuve manque.

L’exhaustivité signifie zéro gap silencieux. Elle ne signifie pas que tout devient automatique.

## Hiérarchie des preuves

1. `MOROCCO_RCP_CURRENT` — RCP de la présentation dans la base AMMPS courante. Source clinique/réglementaire produit prioritaire.
2. `MOROCCO_AMMPS_CURRENT` — base AMMPS courante : substance, dosage, forme, EPI, statut AMM/commercialisation et lien RCP.
3. `MOROCCO_RMMG_2026` — Répertoire Marocain des Médicaments Génériques, édition projet janvier 2026 : identité, groupes génériques, voie, EPI, EAN13 et commercialisation des génériques du répertoire.
4. `MOROCCO_DENTAL_GUIDE` — Guide national bucco-dentaire du Ministère de la Santé, édition 2014 : périmètre/usage dentaire national historique. Il ne suffit pas seul à automatiser une posologie en 2026.
5. `MOROCCO_BO_SGG` — Bulletin Officiel / SGG : statut/prix réglementaire et recoupement de spécialités ; pas une source de posologie.
6. `INTERNATIONAL_SUPPORT` — recommandations dentaires actuelles / SmPC étrangers reconnus : cross-check ou gap-filler avec validation praticien ; jamais promotion silencieuse en recommandation marocaine.

## Sources primaires M0 vérifiées le 2026-09-15

- AMMPS — Base de données des médicaments : https://www.ammps.gov.ma/recherche-medicaments — 9 908 présentations au moment de la vérification, RCP téléchargeables et statuts de commercialisation distincts.
- AMMPS — RMMG : https://www.ammps.gov.ma/repertoire-medicaments-generiques — édition projet janvier 2026, 312 substances/groupes affichés au moment de la vérification.
- AMMPS — note RMMG du 05/01/2026 : le répertoire projet recense les génériques effectivement commercialisés et reste dynamique ; la rubrique des excipients à effet notoire était encore en finalisation.
- Ministère de la Santé — Guide de promotion de la santé bucco-dentaire destiné aux professionnels de santé, édition 2014 : https://www.sante.gov.ma/sites/Ar/Documents/Guide%20SBD.pdf

## Statuts à ne jamais confondre

`AMM_ENREGISTREE` ≠ `COMMERCIALISE` ≠ disponibilité temps réel en pharmacie.

Le snapshot conserve séparément au minimum :

- `Commercialisé` ;
- `Commercialisé AO` / variantes AO-export lorsqu’affichées ;
- `Non Commercialisé` ;
- `AMM sans prix` ;
- `Retiré du Marché`.

Digital Crown ne déduira jamais un stock pharmacie temps réel de ces statuts.

## Niveaux d’automatisation cibles

- `AUTO_OK_MAROC` : indication + schéma compatibles avec preuve marocaine actuelle, présentation pertinente vérifiée, aucune contradiction ni donnée patient manquante.
- `PROPOSE_CONFIRM` : support marocain incomplet ou cross-check international nécessaire ; le praticien confirme explicitement.
- `REVIEW_ONLY` : conflit, population à risque, usage hors AMM/off-label, RCP insuffisant ou contexte incomplet.
- `NOT_SUPPORTED` : absence de preuve acceptable, retrait/inadéquation de la présentation, ou contexte hors périmètre.

Aucun nouveau passage vers `AUTO_OK_MAROC` n’est autorisé pendant M0.

## Architecture de données cible

Le runtime cabinet doit rester local/on-premise. Il ne dépendra pas du site AMMPS pour prescrire.

Le référentiel local versionné devra contenir par entrée :

`evidence_version`, `molecule`, `composition`, `dental_indication`, `presentation`, `route`, `form`, `age_rule`, `weight_rule`, `regimen`, `duration`, `pregnancy_rule`, `breastfeeding_rule`, `renal_rule`, `hepatic_rule`, `allergy_rule`, `interaction_rules`, `amm_status`, `market_status`, `epi`, `ean13`, `rcp_url`, `rcp_checked_at`, `morocco_dental_source_ids`, `international_support_ids`, `automation_tier`, `decision_reason`.

Une future mise à jour réseau rafraîchit ce snapshot ; l’Ordonnance consomme uniquement le snapshot validé localement.

## Matrice M0 — état initial

| Domaine | DCI / protocole | Moteur actuel | Preuve dentaire Maroc | AMM/présentation Maroc | RCP dentaire actuel | Décision M0 |
|---|---|---:|---|---|---|---|
| Antalgie | Paracétamol | Oui | Guide 2014 : 1re intention | À figer par snapshot AMMPS | À extraire | Conserver gate actuel ; pas d’upgrade auto M0 |
| Antalgie forte | Paracétamol + codéine | Non | Guide 2014 : 2e intention historique | À vérifier | À extraire | `REVIEW_ONLY` jusqu’à preuve actuelle + règles de risque |
| Antalgie haut risque | Tramadol | Non | Non identifié M0 | Présentations AMMPS à cartographier | À extraire | `REVIEW_ONLY` |
| AINS | Ibuprofène | Oui | Guide 2014 : classe AINS + précautions | À figer par snapshot AMMPS | À extraire | Gate âge/poids existant ; auto Maroc non élargi M0 |
| AINS | Diclofénac | Non | Guide 2014 : classe AINS seulement | CATAFLAM 50 mg commercialisé vérifié ; autre présentation retirée observée | À extraire | `REVIEW_ONLY` |
| AINS | Kétoprofène | Non | Guide 2014 : classe AINS seulement | À vérifier | À extraire | `REVIEW_ONLY` |
| Corticoïdes | Corticoïdes systémiques à indication bucco-dentaire | Non | Guide 2014 : classe glucocorticoïdes | À subdiviser par DCI | À extraire | `REVIEW_ONLY` |
| Antibiotique | Amoxicilline | Oui | Guide 2014 : pénicilline A / 1re intention | Présentations 500 mg et 1 g commercialisées vérifiées | À extraire par présentation | `PROPOSE_CONFIRM` tant que schéma Maroc actuel non figé |
| Antibiotique | Phénoxyméthylpénicilline | Oui | Pas de ligne dentaire Maroc actuelle identifiée M0 | ANGIPEN 1 MUI commercialisé AO/export ; suspension AMM sans prix | À extraire | `PROPOSE_CONFIRM` / gap Maroc à résoudre |
| Antibiotique | Métronidazole | Oui | Guide 2014 : 5-nitro-imidazolés | RMMG : formes orales 500 mg et suspension identifiées | À extraire | `PROPOSE_CONFIRM` tant que schéma Maroc actuel non figé |
| Antibiotique | Spiramycine + métronidazole | Non | Guide 2014 : association pour germes anaérobies | BIDONTOGYL/BISPIRAZOLE 1,5 MUI/250 mg commercialisés vérifiés ; BITOGYL AMM sans prix observé | À extraire | Priorité M2 ; `REVIEW_ONLY` avant validation RCP |
| Antibiotique | Amoxicilline + acide clavulanique | Review only actuel | Guide 2014 : 2e intention historique | Présentations commercialisées + non commercialisées + AMM sans prix vérifiées | À extraire | Conflit temporel à résoudre ; `REVIEW_ONLY` |
| Antibiotique | Clarithromycine | Oui | Macrolides cités comme classe dans guide 2014 | ZECLAR suspension commercialisée ; statut variable selon présentation | À extraire | `PROPOSE_CONFIRM` / indication à vérifier |
| Antibiotique | Azithromycine | Non | Macrolides cités comme classe dans guide 2014 | UNIZITRO oral commercialisé vérifié | À extraire | `REVIEW_ONLY` avant preuve dentaire spécifique |
| Antibiotique | Clindamycine | Oui >=12 dans règle internationale | Lincosamides cités en allergie bêta-lactamines dans guide 2014 | À vérifier présentation par présentation | À extraire | `PROPOSE_CONFIRM` au mieux ; priorité M2 |
| Parodontologie | Doxycycline / cyclines | Non | Guide 2014 : réserver aux parodontites agressives spécifiques / juvéniles localisées | À vérifier | À extraire | `REVIEW_ONLY`, indication très restreinte |
| Prophylaxie | Antibioprophylaxie infectieuse dentaire | Non canonique | Source nationale actuelle non encore identifiée | Dépend DCI | À sourcer | `REVIEW_ONLY`; protocole séparé de l’antibiothérapie curative |
| Antifongique | Miconazole | Oui | Source dentaire Maroc actuelle non identifiée | À vérifier | À extraire | `PROPOSE_CONFIRM` international actuellement ; gap Maroc |
| Antifongique | Nystatine | Oui supplément | Source dentaire Maroc actuelle non identifiée | À vérifier | À extraire | `PROPOSE_CONFIRM` international actuellement ; gap Maroc |
| Antifongique | Fluconazole | Oui | Source dentaire Maroc actuelle non identifiée | CANDICID 150 mg commercialisé ; 50 mg non commercialisé observé | À extraire | `PROPOSE_CONFIRM` international actuellement ; gap Maroc |
| Antiviral | Aciclovir | Oui supplément | Source dentaire Maroc actuelle non identifiée | RMMG oral 200/400/800 mg + suspension 80 mg/ml identifiés | À extraire | `PROPOSE_CONFIRM` international actuellement ; gap Maroc |
| Antiseptique | Chlorhexidine | Oui | Guide 2014 : antiseptiques locaux comme classe | BUXIDINE chlorhexidine/chlorobutanol non commercialisé observé ; autres présentations à cartographier | À extraire | Présentation-specific ; pas d’auto tant que snapshot incomplet |
| Anti-inflammatoire local | Benzydamine | Oui | Source dentaire Maroc actuelle non identifiée | À vérifier | À extraire | `PROPOSE_CONFIRM` international actuellement ; gap Maroc |
| Muqueuses | Hydrocortisone oromuqueuse | Oui supplément | Source dentaire Maroc actuelle non identifiée | À vérifier | À extraire | `PROPOSE_CONFIRM` international actuellement ; gap Maroc |
| Muqueuses | Autres corticoïdes topiques oraux | Non | À cartographier | À cartographier | À extraire | `REVIEW_ONLY` |
| Prévention carieuse | Fluorure de sodium 2800 ppm | Oui supplément | Source nationale actuelle à identifier | À vérifier présentation | À extraire | `PROPOSE_CONFIRM` international actuellement ; gap Maroc |
| Prévention carieuse | Fluorure de sodium 5000 ppm | Oui supplément | Source nationale actuelle à identifier | À vérifier présentation | À extraire | `PROPOSE_CONFIRM` international actuellement ; gap Maroc |
| Prévention carieuse | Bain de bouche fluoré 0,05 % | Oui supplément | Source nationale actuelle à identifier | À vérifier présentation | À extraire | `PROPOSE_CONFIRM` international actuellement ; gap Maroc |
| Xérostomie | Pilocarpine / sialogogues | Non | À identifier | À vérifier | À extraire | `REVIEW_ONLY` |
| Xérostomie | Substituts salivaires | Non | À identifier | Médicament/dispositif à classifier | À vérifier | `REVIEW_ONLY` / hors ordonnance selon statut |
| Hémostase | Acide tranexamique local / systémique | Non | Source dentaire Maroc actuelle non identifiée | À vérifier | À extraire | `REVIEW_ONLY`; usage local potentiellement off-label à distinguer |
| Anesthésie locale cabinet | Articaïne + adrénaline | Hors moteur Ordonnance | Acte chairside, pas prescription ambulatoire | ALPHACAINE N AMM sans prix observé | À extraire | Référentiel cabinet séparé |
| Anesthésie locale cabinet | Lidocaïne ± vasoconstricteur | Hors moteur Ordonnance | Acte chairside | À vérifier | À extraire | Référentiel cabinet séparé |
| Anesthésie locale cabinet | Mépivacaïne | Hors moteur Ordonnance | Acte chairside | À vérifier | À extraire | Référentiel cabinet séparé |
| Sédation/anxiolyse | Benzodiazépines utilisées en odontologie | Non | Aucun protocole Maroc validé M0 | À vérifier | À extraire | `REVIEW_ONLY`, haut risque |
| Urgences cabinet | Adrénaline, bronchodilatateur, glucose, dérivés nitrés, etc. | Hors Ordonnance | Protocole urgence séparé requis | À cartographier | À extraire | Ne jamais mélanger au moteur de prescription ambulatoire |

## Gaps prioritaires à fermer avant M2

1. Extraire et versionner les RCP AMMPS des présentations pertinentes plutôt que seulement constater leur présence dans la base.
2. Vérifier si une recommandation marocaine dentaire plus récente que le guide 2014 existe pour antibiothérapie, prophylaxie, douleur et populations à risque.
3. Cartographier chaque présentation : AMM, commercialisation, dosage, forme, EPI, EAN13 lorsque disponible.
4. Distinguer indication explicitement dentaire du RCP vs simple AMM de la molécule.
5. Distinguer schéma explicitement marocain vs schéma international de support.
6. Recenser les interactions majeures et règles grossesse/rénal/hépatique à partir des RCP marocains.
7. Classer médicaments ambulatoires, médicaments chairside et médicaments d’urgence dans trois périmètres séparés.

## Phases

- M0 — cartographie exhaustive + matrice preuves/gaps, zéro nouvelle règle clinique activée.
- M1 — snapshot local AMMPS/RCP + schéma de données + tests d’intégrité, toujours zéro nouvelle auto-proposition.
- M2 — antibiotiques curatifs + prophylaxie après validation médicale de la matrice.
- M3 — antalgiques + AINS + corticoïdes pertinents.
- M4 — antifongiques + antiviraux + antiseptiques + pathologies muqueuses.
- M5 — fluorures + prévention + xérostomie + hémostase + parodontologie.
- M6 — grossesse/allaitement, insuffisances rénale/hépatique, allergies et interactions systématiques.
- M7 — certification de couverture, non-régression, documentation et closeout.

## Human gate médical

Avant toute activation M2+, présenter la matrice M0 complète au praticien pour valider : indication dentaire, niveau d’automatisation et traitement des divergences de sources.

Ce gate ne bloque pas la collecte des sources, l’extraction des RCP, la normalisation du snapshot ni les tests d’intégrité.

## Contraintes de non-régression

- aucun second moteur Ordonnance ;
- aucun second catalogue clinique ;
- aucune modification de données patient ;
- aucune inférence clinique déterminante depuis du texte libre ;
- aucun poids inventé ;
- aucune disponibilité pharmacie temps réel fabriquée ;
- saisies explicites praticien préservées ;
- `MoroccoPharmacologyPolicy` reste le gate central jusqu’à migration prouvée vers une version data-driven équivalente ou plus stricte ;
- aucune dépendance réseau requise au runtime cabinet.

## Proof M0

En cours. Ce document est le fichier canonique de reprise du chantier à partir de sa création.