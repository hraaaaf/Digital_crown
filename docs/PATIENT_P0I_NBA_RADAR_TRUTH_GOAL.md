# Patient P0-I — NBA / Radar truth boundary

## Goal

Conserver les rappels opérationnels factuels de la fiche Patient tout en interdisant qu'un calcul temporel, statistique, commercial ou de détection dentaire soit présenté comme diagnostic, risque clinique retenu, indication thérapeutique ou estimation clinique.

## Référence visuelle BEFORE

Surface réelle existante :
- fiche Patient, toast NBA déclenché après ouverture ;
- ClinicalHub > Radar de Vigilance lorsque des insights sont présents.

Viewports : 390×844, 430×932, 768×1024, 1280×900.

Aucun redesign. Typographie, placement, couleurs et navigation restent ceux de l'application.

## Succès observable

1. Un ancien détartrage ne produit plus automatiquement « risque parodontal élevé », « suggérer détartrage » ou « planifier détartrage ».
2. Aucun grade PLATINUM / Premium n'intervient dans le NBA Patient.
3. Le nombre de semestres ortho ne devient plus un pourcentage de progression clinique ni une date de fin de traitement estimée.
4. Les alertes administratives factuelles restent autorisées : échéance en retard, dossier médical incomplet, absence de RDV futur, annulations répétées, suivi de contact, documents manquants.
5. Les `detections` du moteur panoramique de repérage dentaire ne sont plus décrites comme « anomalies détectées » ni typées `diagnostic`.
6. La panoramique est présentée au maximum comme repérage technique à vérifier par le praticien.
7. Zéro erreur runtime / HTTP 5xx liée à ces changements.

## Cible de contenu

Avant :
- « Détartrage Annuel Dépassé — Risque parodontal élevé — Planifier Détartrage »
- « Patient Premium — Patient PLATINUM… »
- « Progression Orthodontie — 75% d'avancement estimé »
- « Fin de Traitement Estimée »
- « N anomalies détectées sur la panoramique (IA) »

Après :
- aucune conduite clinique automatique provenant uniquement de ces heuristiques ;
- alertes opérationnelles factuelles seulement ;
- « Repérage panoramique — N dents repérées automatiquement. Interprétation clinique : praticien. » lorsque le repérage dentaire existe.

## Hors scope

- redesign du toast ou du Radar ;
- ajout d'un nouveau moteur diagnostique ;
- modification du plan de traitement ;
- décisions thérapeutiques automatiques.
