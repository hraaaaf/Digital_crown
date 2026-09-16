# Digital Crown — Référentiel dentaire Maroc — Coverage matrix

Date: 2026-09-16
Status: COVERAGE AUDIT — COMPLETENESS NOT CERTIFIED

## Goal
Mesurer la couverture réelle du référentiel médicaments + oral-care/para et isoler ce qui reste à enrichir avant fusion finale.

## Lecture
- `INVENTORIED` : famille présente dans le master.
- `CLINICAL_PASS` : au moins une passe clinique sourcée existe.
- `MA_PASS` : au moins une preuve Maroc existe pour tout ou partie de la famille.
- `ROW_ENRICHMENT_PENDING` : les entrées individuelles ne sont pas encore toutes enrichies dose/âge/poids/CI/interactions/usage.
- `SPECIALIST` : protocole séparé requis.

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
| I | Fluor/reminéralisation | INVENTORIED | CLINICAL_PASS | PARTIAL_MA | ROW_ENRICHMENT_PENDING |
| J | Antiseptiques/bains de bouche | INVENTORIED | CLINICAL_PASS | PARTIAL_MA | ROW_ENRICHMENT_PENDING |
| K | Xérostomie/hyposialie | INVENTORIED | CLINICAL_PASS | PARTIAL_MA | SYSTEMIC_SPECIALIST + PARA_SUPPORTED |
| L | Brosses/hygiène mécanique | INVENTORIED | CLINICAL_PASS | PARTIAL_MA | PRODUCT_ENRICHMENT_PENDING |
| M | Interdentaire | INVENTORIED | CLINICAL_PASS | MA_PASS | PRODUCT_ENRICHMENT_PENDING |
| N | Prothèses amovibles | INVENTORIED | CLINICAL_PASS | MA_PASS | PRODUCT_ENRICHMENT_PENDING |
| O | Orthodontie/aligneurs | INVENTORIED | PARTIAL_CLINICAL | MA_PASS | PRODUCT_ENRICHMENT_PENDING |
| P | Implants/parodonte domicile | INVENTORIED | CLINICAL_PASS | MA_PASS | PRODUCT_ENRICHMENT_PENDING |
| Q | Hypersensibilité/érosion | INVENTORIED | CLINICAL_PASS | MA_PASS_EXAMPLE | PRODUCT_ENRICHMENT_PENDING |
| R | Halitose | INVENTORIED | CLINICAL_PASS | MA_PASS_EXAMPLE | PRODUCT_ENRICHMENT_PENDING |
| S | Blanchiment/colorations | INVENTORIED | CLINICAL_PASS | PARTIAL_MA | REGULATORY/PRODUCT_LIMITS_PENDING |
| T | Ulcères/traumatismes — para | INVENTORIED | CLINICAL_PASS | MA_PASS_EXAMPLE | PRODUCT_ENRICHMENT_PENDING |
| U | Pédiatrie oral-care | INVENTORIED | CLINICAL_PASS | MA_PASS | ROW_ENRICHMENT_PENDING |
| V | Plaque/motivation | INVENTORIED | PARTIAL_CLINICAL | TO_VERIFY_MA | PRODUCT_ENRICHMENT_PENDING |
| W | Gouttières/protège-dents | INVENTORIED | PARTIAL_CLINICAL | TO_VERIFY_MA | SUBFAMILY_PASS_PENDING |
| X | Sevrage tabagique connexe | INVENTORIED | NOT_YET_ENRICHED | TO_VERIFY_MA | OUTER_SCOPE_INTERFACE |
| Y | Sédation/anxiété | INVENTORIED | CLINICAL_PASS | PARTIAL_MA | SPECIALIST_PROTOCOL_REQUIRED |
| Z | Urgences cabinet | INVENTORIED | CLINICAL_PASS | PARTIAL_MA | HIGH_RISK_VALIDATION_PENDING |

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

### Oral-care / para
1. Dentifrices 2800/5000 ppm : disponibilité Maroc et cadre d'usage/prescription.
2. Gel fluoré domicile et professionnel : formulations et fréquence produit-spécifiques.
3. SDF 38% : disponibilité/autorisation Maroc.
4. CPP-ACP/CPP-ACPF : preuves, allergie protéines de lait et disponibilité Maroc à documenter.
5. Hydroxyapatite : ne pas surclasser face au fluor; données produit-spécifiques.
6. Peroxyde d'hydrogène, hexétidine, povidone iodée, dioxyde de chlore, zinc : indications/précautions/disponibilité Maroc.
7. Brosse à doigt nourrisson et produits de dentition : filtre sécurité avant toute recommandation.
8. Hydropulseurs : modèles/familles Maroc et indications pratiques.
9. Adhésifs poudre/bandes/pads et relines OTC : disponibilité et précautions.
10. Nettoyants aligneurs/contentions, protège-dents, boîtes : disponibilité/usage.
11. Révélateurs de plaque : produits Maroc, âge et mode d'emploi.
12. Produits charbon : marché uniquement tant qu'efficacité/abrasivité non validées.
13. Produits post-op spécifiques : dissocier protection mécanique, antiseptique, cicatrisation revendiquée et réelle preuve clinique.
14. Sevrage tabagique : garder comme interface santé générale, pas prescription dentaire automatique.

## Conclusion d'audit
- Les grandes familles attendues dans le scope actuel sont présentes dans le master A–Z.
- `COMPLETENESS CERTIFIED` n'est pas attribué : présence de toutes les grandes familles ne prouve pas que chaque DCI, forme, concentration ou produit marocain pertinent a été capturé.
- Le principal travail restant est désormais l'enrichissement de ligne et la vérification Maroc, pas la construction d'une nouvelle taxonomie.

## Next exact
Créer le `MASTER_DATASET_V1` enrichi en fusionnant les passes existantes, conserver `TO_VERIFY` pour toute cellule non prouvée, puis traiter les lignes restantes par paquets homogènes jusqu'à zéro champ critique non classé.
