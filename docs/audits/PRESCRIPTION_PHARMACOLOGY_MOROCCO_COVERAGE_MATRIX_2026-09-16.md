# Digital Crown — Référentiel dentaire Maroc — Coverage matrix

Date: 2026-09-16
Status: COVERAGE AUDIT — TAXONOMY OPEN — COMPLETENESS NOT CERTIFIED

## Goal
Mesurer la couverture réelle du référentiel médicaments + oral-care/para, isoler les manques et les recouvrements, puis fermer la taxonomie avant enrichissement clinique final.

## Lecture
- `INVENTORIED` : famille présente dans le master ou un addendum canonique.
- `CLINICAL_PASS` : au moins une passe clinique sourcée existe.
- `MA_PASS` : au moins une preuve Maroc existe pour tout ou partie de la famille.
- `ROW_ENRICHMENT_PENDING` : les entrées individuelles ne sont pas encore toutes enrichies dose/âge/poids/CI/interactions/usage.
- `SPECIALIST` : protocole séparé requis.
- `TAXONOMY_OPEN` : au moins une omission ou normalisation de concept reste à fermer.

## État du corpus après audit exhaustif
- Base inventory : 170 lignes.
- Addendum historique : 4 lignes.
- Addendum V2 confirmé : 4 lignes.
- Total énuméré : 178 lignes.
- Ce total n'est **pas** un nombre de concepts uniques : 3 doublons exacts/quasi-exacts et plusieurs recouvrements sémantiques ont été identifiés.
- `COMPLETENESS CERTIFIED` : **NO**.
- `TAXONOMY CLOSED` : **NO**.

| Section | Famille | Inventaire | Passe clinique | Passe Maroc | État principal |
|---|---|---|---|---|---|
| A | Douleur/AINS | INVENTORIED | CLINICAL_PASS | PARTIAL_MA | ROW_ENRICHMENT_PENDING |
| B | Antibiotiques systémiques | INVENTORIED | CLINICAL_PASS | PARTIAL_MA | ROW_ENRICHMENT_PENDING |
| C | Prophylaxie antibiotique | INVENTORIED | PARTIAL_CLINICAL | PARTIAL_MA | ROW_ENRICHMENT_PENDING |
| D | Antifongiques | INVENTORIED | CLINICAL_PASS | PARTIAL_MA | ROW_ENRICHMENT_PENDING |
| E | Antiviraux | INVENTORIED | CLINICAL_PASS | PARTIAL_MA | ROW_ENRICHMENT_PENDING |
| F | Ulcérations/mucites | INVENTORIED | CLINICAL_PASS | PARTIAL_MA | ROW_ENRICHMENT_PENDING |
| G | Anesthésiques locaux/topiques | INVENTORIED | CLINICAL_PASS | PARTIAL_MA | HIGH_RISK_VALIDATION_PENDING |
| H | Hémostase | INVENTORIED | CLINICAL_PASS | TO_VERIFY_MA | SPECIALIST / LOCAL_MEASURES_FIRST |
| I | Fluor/reminéralisation | INVENTORIED + V2_GAPS | CLINICAL_PASS | PARTIAL_MA | TAXONOMY_OPEN + ROW_ENRICHMENT_PENDING |
| J | Antiseptiques/bains de bouche | INVENTORIED | CLINICAL_PASS | PARTIAL_MA | ROW_ENRICHMENT_PENDING |
| K | Xérostomie/hyposialie | INVENTORIED | CLINICAL_PASS | PARTIAL_MA | SYSTEMIC_SPECIALIST + PARA_SUPPORTED |
| L | Brosses/hygiène mécanique | INVENTORIED | CLINICAL_PASS | PARTIAL_MA | PRODUCT_ENRICHMENT_PENDING |
| M | Interdentaire | INVENTORIED + V2_GAP | CLINICAL_PASS | MA_PASS_PARTIAL | PRODUCT_ENRICHMENT_PENDING |
| N | Prothèses amovibles | INVENTORIED | CLINICAL_PASS | MA_PASS | PRODUCT_ENRICHMENT_PENDING |
| O | Orthodontie/aligneurs | INVENTORIED | PARTIAL_CLINICAL | MA_PASS | PRODUCT_ENRICHMENT_PENDING |
| P | Implants/parodonte domicile | INVENTORIED | CLINICAL_PASS | MA_PASS | PRODUCT_ENRICHMENT_PENDING |
| Q | Hypersensibilité/érosion | INVENTORIED | CLINICAL_PASS | MA_PASS_EXAMPLE | PRODUCT_ENRICHMENT_PENDING |
| R | Halitose | INVENTORIED | CLINICAL_PASS | MA_PASS_EXAMPLE | PRODUCT_ENRICHMENT_PENDING |
| S | Blanchiment/colorations | INVENTORIED | CLINICAL_PASS | PARTIAL_MA | REGULATORY/PRODUCT_LIMITS_PENDING |
| T | Ulcères/traumatismes — para | INVENTORIED | CLINICAL_PASS | MA_PASS_EXAMPLE | PRODUCT_ENRICHMENT_PENDING |
| U | Pédiatrie oral-care | INVENTORIED + V2_SAFETY | CLINICAL_PASS | MA_PASS_PARTIAL | SAFETY_REVIEW + ROW_ENRICHMENT_PENDING |
| V | Plaque/motivation | INVENTORIED | PARTIAL_CLINICAL | TO_VERIFY_MA | PRODUCT_ENRICHMENT_PENDING |
| W | Gouttières/protège-dents | INVENTORIED | PARTIAL_CLINICAL | TO_VERIFY_MA | SUBFAMILY_PASS_PENDING |
| X | Sevrage tabagique connexe | INVENTORIED | NOT_YET_ENRICHED | TO_VERIFY_MA | OUTER_SCOPE_INTERFACE |
| Y | Sédation/anxiété | INVENTORIED | CLINICAL_PASS | PARTIAL_MA | SPECIALIST_PROTOCOL_REQUIRED |
| Z | Urgences cabinet | INVENTORIED | CLINICAL_PASS | PARTIAL_MA | HIGH_RISK_VALIDATION_PENDING |

## Omissions confirmées ajoutées en V2
1. `OC-INT-013` — floss holder / reusable floss handle.
2. `OC-FLUOR-004` — prescription/high-strength home-use fluoride gel.
3. `MED-FLUOR-001` — dietary fluoride supplement drops/tablets/lozenges.
4. `OC-TEETH-002` — firm/chilled teething ring, option non médicamenteuse.

Toutes restent `TO_VERIFY_MA`; aucune activation clinique.

## Doublons exacts / quasi-exacts à normaliser
1. `MED-MUC-007` ↔ `MED-LA-008` — benzocaïne topique.
2. `OC-TP-010` ↔ `OC-WHITE-001` — dentifrice blanchissant/détachant.
3. `OC-XERO-004` ↔ `OC-GUM-001` — chewing-gum sans sucre/xylitol.

Décision : ne pas supprimer l'historique tant que `entity_canonical_id`, forme, concentration et tags d'indication ne sont pas introduits. L'exhaustivité ne doit pas être calculée à partir du nombre brut de lignes.

## Recouvrements sémantiques à normaliser
- benzydamine médicament ↔ bain de bouche oral-care ;
- lidocaïne muqueuse ↔ anesthésique topique ;
- fluorure stanneux dentifrice ↔ produit désensibilisant ;
- nitrate de potassium dentifrice ↔ produit désensibilisant ;
- arginine/calcium carbonate dentifrice ↔ produit désensibilisant ;
- sels de strontium dentifrice ↔ produit désensibilisant ;
- hydroxyapatite dentifrice ↔ produit de reminéralisation ;
- CPC/zinc/dioxyde de chlore bain de bouche ↔ familles halitose.

## Sous-familles encore explicitement à fermer

### Médicaments
1. Naproxène/diclofénac/kétoprofène/dexkétoprofène : indication dentaire comparative, dose, durée, CI/interactions, âge/poids et statut Maroc exact par forme.
2. Codéine/tramadol : restrictions d'âge, interactions, grossesse/allaitement et rôle exceptionnel.
3. Céphalosporines, doxycycline, spiramycine et associations : rôle exact / alternatives / allergies / prophylaxie.
4. Antifongiques et antiviraux secondaires : formulations Maroc et posologies exactes.
5. Benzydamine/lidocaïne/benzocaïne topiques : limites d'âge, concentration, durée, méthémoglobinémie pour benzocaïne.
6. Prilocaïne/bupivacaïne/mépivacaïne : doses maximales selon formulation, poids, vasoconstricteur et contexte pédiatrique/adulte.
7. Pilocarpine/cévimeline : disponibilité Maroc et cadre de prescription.
8. Sédation : cadre réglementaire marocain, compétences/monitoring/récupération; aucune activation automatique.
9. Urgences : protocole marocain exact à confronter aux médicaments réellement disponibles au cabinet.
10. Suppléments fluorés systémiques : statut réglementaire Maroc et exposition fluorée locale avant toute donnée opérationnelle.

### Oral-care / para
1. Dentifrices 2800/5000 ppm : disponibilité Maroc et cadre d'usage/prescription.
2. Gel fluoré domicile et professionnel : formulations et fréquence produit-spécifiques.
3. SDF 38% : disponibilité/autorisation Maroc.
4. CPP-ACP/CPP-ACPF : preuves, allergie protéines de lait et disponibilité Maroc à documenter.
5. Hydroxyapatite : ne pas surclasser face au fluor; données produit-spécifiques.
6. Peroxyde d'hydrogène, hexétidine, povidone iodée, dioxyde de chlore, zinc : indications/précautions/disponibilité Maroc.
7. Produits de dentition : toute forme médicamenteuse reste `SAFETY_REVIEW_REQUIRED`; aucune recommandation automatique de benzocaïne/lidocaïne.
8. Floss holder : disponibilité Maroc à vérifier séparément du floss threader et des floss picks.
9. Hydropulseurs : modèles/familles Maroc et indications pratiques.
10. Adhésifs poudre/bandes/pads et relines OTC : disponibilité et précautions.
11. Nettoyants aligneurs/contentions, protège-dents, boîtes : disponibilité/usage.
12. Révélateurs de plaque : produits Maroc, âge et mode d'emploi.
13. Produits charbon : marché uniquement tant qu'efficacité/abrasivité non validées.
14. Produits post-op spécifiques : dissocier protection mécanique, antiseptique, cicatrisation revendiquée et réelle preuve clinique.
15. Sevrage tabagique : garder comme interface santé générale, pas prescription dentaire automatique.

## Conclusion d'audit
- La macro-taxonomie A–Z couvre les grandes zones attendues, mais la taxonomie n'est **pas fermée**.
- Quatre lignes V2 ont été ajoutées après audit; trois doublons exacts/quasi-exacts et plusieurs recouvrements doivent être normalisés.
- `COMPLETENESS CERTIFIED` n'est pas attribué.
- Le travail restant combine encore taxonomie, normalisation, vérification Maroc et enrichissement de ligne.

## Next exact
1. Vérifier au Maroc les 4 lignes V2 sans contact AMMPS : présence marché, source réglementaire publique si disponible, statut séparé de la preuve clinique.
2. Introduire une normalisation canonique des doublons/recouvrements sans supprimer l'historique.
3. Puis enrichir les champs critiques par paquets homogènes jusqu'à zéro champ critique non classé.
