# Prescription Pharmacology — Amoxicilline sévère + poids

Status: ACTIVE

## Goal

Sécuriser l’adaptation de l’amoxicilline lorsqu’une infection dentaire sévère est explicitement structurée, en utilisant l’âge et le poids réels sans inférer la sévérité, sans inventer de poids et sans transformer une borne de sécurité en dose automatique.

## Success

- `severeInfection` n’est consommé que via `DentalAbscessContext` explicite ;
- aucun texte libre n’est converti en sévérité clinique ;
- entre 6 mois et 11 ans, poids réel obligatoire ;
- le plafond SDCEP `jusqu’à 30 mg/kg par prise, max 1 g, 3 fois/jour` est calculé comme borne, pas comme prescription automatique ;
- l’absence de poids échoue fermé ;
- les adolescents sont revus manuellement lorsque la recommandation dentaire par âge et le SmPC pondéral doivent être réconciliés ;
- aucune valeur explicitement saisie par le praticien n’est écrasée ;
- le gate Maroc reste inchangé ;
- aucune nouvelle proposition thérapeutique n’est auto-adoptée sans preuve marocaine appropriée.

## Sources vérifiées

### SDCEP — source dentaire primaire

https://sdcepdentalprescribing.nhs.scot/guidance/bacterial-infections/dental-abscess/first-line-antibiotics/amoxicillin/

Règle publiée :
- schémas usuels par âge ;
- infection sévère adultes et 12–17 ans : dose doublée ;
- infection sévère 6 mois–11 ans : augmentation jusqu’à 30 mg/kg par prise, maximum 1 g, trois fois par jour.

### SmPC amoxicilline — cross-check produit

https://www.medicines.org.uk/emc/product/14146/smpc

Le SmPC impose de tenir compte de la sévérité, de l’âge, du poids et de la fonction rénale. Pour l’abcès dentaire avec cellulite diffuse :
- adultes et enfants >=40 kg : en infection sévère, 750 mg à 1 g toutes les 8 heures ;
- enfants <40 kg : 40 à 90 mg/kg/j en prises réparties.

## Divergence importante

Chez certains adolescents légers, une lecture purement par âge de l’escalade SDCEP peut diverger d’une lecture pondérale du SmPC. Digital Crown ne choisit donc pas automatiquement une dose sévère dans ce contexte : `requires_weight` ou `requires_review` selon les données présentes.

## Architecture

`PrescriptionAmoxicillinSevereSafety` est un gate post-arbitrage :

1. vérifie que la molécule est bien l’amoxicilline simple ;
2. exige `DentalAbscessContext.severeInfection === true` ;
3. conserve tous les blocages antérieurs (allergie, absence de preuve, etc.) ;
4. 6 mois–11 ans : exige le poids réel et calcule uniquement la borne `min(30 mg/kg, 1000 mg)` par prise ;
5. adolescent sans poids : `requires_weight` ;
6. adolescent/adulte sévère : `requires_review`, aucune dose internationale sélectionnée automatiquement ;
7. les saisies explicites du praticien restent inchangées mais signalées pour validation.

Le pipeline expose `dentalAbscessContext` comme paramètre explicite. Il n’est pas construit depuis du texte clinique libre.

## Tests

Couverture ajoutée :
- sévère non explicite => comportement précédent inchangé ;
- enfant sévère sans poids => `requires_weight` ;
- enfant 20 kg => plafond 600 mg/prise, aucune dose auto ;
- plafond absolu 1 g ;
- adolescent sévère sans poids => `requires_weight` ;
- adolescent sévère avec poids => `requires_review` ;
- valeurs praticien explicites préservées ;
- adulte sévère => pas de sélection automatique à partir d’une plage internationale.

## UI/UX

Aucun changement visuel dans ce sous-lot. Aucun AFTER visuel requis tant que le gate n’est pas branché à une nouvelle interaction visible.

## Proof

À compléter après PR et CI exacte du HEAD final.
