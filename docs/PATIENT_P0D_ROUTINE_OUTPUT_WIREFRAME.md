# Patient P0-D — Routine Examen complet — Goal visuel + wireframe

## Chantier
P0-D — Assistants cliniques fail-closed / branche `routine` de `AssistantExamenComplet`.

## Baseline vérifiée
Run `Patient P0-D Routine Baseline` #2 — `32043371503` — SUCCESS.

Le fichier `AssistantExamenComplet.tsx` a le même blob SHA (`2d061127b495719926e2cabb1123e052b3bfb637`) entre le run baseline et le HEAD de préparation du présent document.

Matrice : 390×844, 430×932, 768×1024, 1280×900.

Défaut reproduit sur 4/4 résultats : la collecte de six réponses produit une sortie autoritative du type `Bilan Dentaire Complet — Haut Risque Infectieux — Hygiène Insuffisante — Parodontite Sévère — Caries Actives — Bruxisme — Lésion Muqueuse Suspecte`, puis le moteur ajoute des actes, traitements, imagerie et routages automatiquement.

## Goal
Conserver le wizard et le design existants, mais transformer la sortie Routine en **synthèse d'observations à confirmer**, sans diagnostic autonome, prescription, acte, imagerie ou routage thérapeutique automatique.

## Succès observable
- Les 6 questions et leurs options restent disponibles comme collecte structurée.
- La carte indigo `Proposition clinique à valider — Examen Clinique Complet` reste la même surface visuelle.
- La sortie reprend les réponses comme observations rapportées/constatées, sans les convertir en diagnostic retenu.
- `steps` reste vide.
- `next` reste `null`.
- Aucune sortie automatique ne contient : antibioprophylaxie / Amox 2 g, surfaçage, détartrage prescrit, radiographie imposée, traitement de caries, gouttière, IRM, biopsie, équilibration ou autre acte thérapeutique catégorique.
- Les signaux de vigilance (allergie, antécédent cardiovasculaire déclaré, lésion muqueuse rapportée, etc.) sont affichés comme **éléments à vérifier par le praticien**, pas comme diagnostics.
- Aucun changement de layout, palette ou navigation hors nécessité de lisibilité du texte.

## Référence scientifique / sécurité
La sortie doit respecter le principe P0-D déjà documenté : collecte → observations → données manquantes / vigilance → validation explicite du praticien. Une simple catégorie `Cardiopathie / Prothèse valvulaire` ne suffit pas à déterminer automatiquement une antibioprophylaxie ; l'indication dépend d'une situation cardiovasculaire précisément qualifiée et du geste envisagé.

## Wireframe cible

```text
[Proposition clinique à valider — Examen Clinique Complet]

Observations recueillies :
• Antécédents rapportés : …
• Hygiène observée / renseignée : …
• Statut parodontal renseigné : …
• Statut dentaire renseigné : …
• Examen occlusal renseigné : …
• Tissus mous renseignés : …

Vigilance : … à confirmer par le praticien.
Données à compléter : examen clinique et examens complémentaires décidés selon indication.

Ce questionnaire ne pose pas automatiquement de diagnostic et ne détermine pas de traitement.
Diagnostic, examens complémentaires et conduite thérapeutique : décision du praticien.
```

## Non-goals
- Pas de redesign du ClinicalHub.
- Pas de modification des autres assistants dans ce lot.
- Pas de FHIR ou nouveau modèle médical ici.
- Pas de persistance automatique dans le Master Plan.

## Preuve après exigée
Même matrice 390 / 430 / 768 / 1280, même scénario baseline, avec contrat automatisé interdisant les anciennes sorties autoritatives et inspection visuelle avant/mockup/après.