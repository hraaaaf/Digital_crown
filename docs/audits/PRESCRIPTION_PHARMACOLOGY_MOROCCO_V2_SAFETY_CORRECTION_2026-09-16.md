# Digital Crown — Pharmacologie Maroc — correction sécurité V2

Date: 2026-09-16
Status: ACTIVE — SUPERSEDES TEETHING WORDING IN PRIOR V2 AUDIT/COVERAGE NOTES

## Correction
La formulation initiale `firm/chilled teething ring` est remplacée par :

`teething ring / teether (non-drug)`

Motif : les sources pédiatriques soutiennent la famille des anneaux de dentition, mais les caractéristiques de sécurité sont produit-spécifiques. La présence commerciale de modèles réfrigérants au Maroc ne constitue pas une recommandation clinique automatique.

## Guardrail
- `OC-TEETH-002` reste `SAFETY_REVIEW_REQUIRED`.
- `clinical_activation = NO`.
- Les produits médicamenteux de dentition restent séparés et fail-closed.
- Les produits commercialisés doivent être évalués selon leur conception, leur notice et les risques mécaniques/ingestion avant toute recommandation.

## Preuves de sécurité
- AAPD, Perinatal and Infant Oral Health Care, révision 2025 : les anneaux de dentition sont une option symptomatique; les topiques contenant lidocaïne ou benzocaïne ne sont pas recommandés pour la dentition.
- FDA, Safely Soothing Teething Pain in Infants and Children : privilégier un teether ferme, non rempli de liquide, non congelé, avec surveillance; avertissement contre benzocaïne/lidocaïne et bijoux de dentition.

## État repo déjà corrigé
- `PRESCRIPTION_PHARMACOLOGY_MOROCCO_INVENTORY_ADDENDUM_V2_2026-09-16.csv` corrigé.
- `PRESCRIPTION_PHARMACOLOGY_MOROCCO_MASTER_DATASET_V1_2026-09-16.csv` corrigé avec `SAFETY_REVIEW_REQUIRED`.

## Next exact
Poursuivre l'enrichissement V2 sans activer de donnée clinique; le statut Maroc du supplément fluoré systémique reste non prouvé.
