# Document Studio — P7 Compagnon Diagnostique — audit safety

Date : 2026-08-16
Branche : `agent/p7-compagnon-diagnostique-audit`
Base : P6 Document Libre

## Verdict

**P7 engineering safety local convergé après suppression des sorties diagnostiques/prescriptives autonomes. Certification clinique/scientifique et runtime non revendiquées.**

## Baseline trouvée

Le composant `TreatmentPlanStudio.tsx` produisait directement, à partir d'un arbre de réponses frontend :
- un libellé **« Diagnostic Établi »** ;
- des plans de traitement qualifiés de **scientifiques** ;
- des actes thérapeutiques préremplis ;
- des conseils cliniques hardcodés avec doses, traitements et pourcentages ;
- des substitutions automatiques d'antibiothérapie ou d'anti-inflammatoires à partir de simples mots détectés dans `antecedents_medicaux` ;
- un transfert possible de ces actes générés vers Devis.

Le contexte patient utilisé se limitait essentiellement au texte libre des antécédents. Aucune preuve clinique objective suffisante n'était requise avant les conclusions affichées.

## Findings initiaux

### P0-1 — diagnostic autonome depuis arbre de réponses

Le frontend transformait quelques réponses symptomatiques en diagnostic spécifique et affichait `Diagnostic Établi`.

### P0-2 — adaptation thérapeutique automatique

Une détection lexicale dans les antécédents pouvait remplacer automatiquement une antibiothérapie par `Clindamycine/Macrolide` ou des AINS par des corticostéroïdes.

### P1-1 — conseils cliniques hardcodés

Le composant contenait des affirmations spécifiques de diagnostic/traitement, doses, délais et pourcentages sans mécanisme de source/version/validation visible dans ce flux.

### P1-2 — transfert P7→P3 de traitements générés

Les actes générés par la state machine pouvaient être envoyés au Devis. Le filtre P7→P3 bloquait déjà prescriptions/antibiotiques/antalgiques/AINS/corticoïdes/surveillance/enseignement et neutralisait les prix, mais les autres traitements automatiques pouvaient passer.

### P1-3 — validation praticien insuffisante

Aucune confirmation explicite n'était exigée avant le transfert des actes générés.

### P1-4 — perte silencieuse d'actes praticien

Les actes ajoutés manuellement restaient locaux et pouvaient être perdus lors d'un changement d'onglet ou d'une fermeture navigateur.

## Correction P7

### Frontière clinique

`TreatmentPlanStudio` est devenu un **compagnon d'orientation clinique** :
- aucun diagnostic automatique ;
- aucune prescription ;
- aucune posologie ;
- aucune substitution thérapeutique ;
- aucun plan de traitement automatique ;
- aucun acte thérapeutique prérempli ;
- aucun conseil clinique chiffré/hardcodé.

Les motifs produisent uniquement des checklists génériques de consultation à confirmer humainement.

### Contexte patient

- les antécédents sont chargés en lecture seule ;
- aucune interprétation lexicale automatique ;
- en cas d'échec de chargement, le contexte est explicitement déclaré indisponible ;
- aucune conclusion automatisée n'est produite à partir d'un contexte incomplet.

### Actes praticien

- les actes transférables doivent être saisis manuellement par le praticien ;
- toute modification invalide la confirmation précédente ;
- une case de confirmation explicite atteste que les actes correspondent à la décision clinique du praticien après examen ;
- sans confirmation : zéro payload de transfert.

### P7→P3 Devis

- `DiagnosticCompanionPolicy.buildQuoteTransferPayload()` ne produit un payload que pour des actes praticien confirmés ;
- `AccountingPlanConversionPolicy` reste la seconde barrière :
  - prix toujours `0` ;
  - aucune dent inventée pour `Global` ;
  - prescriptions, antibiotiques, antalgiques, anti-inflammatoires, corticostéroïdes, médicaments, posologies, surveillance et enseignement restent exclus ;
  - une ligne mixte contenant un motif médicamenteux est exclue fail-closed.

### P7→P1 Ordonnance

Aucun chemin automatique P7→Ordonnance n'est présent dans le composant courant. Cette absence est conservée : P7 ne doit pas générer de traitement médicamenteux.

### Dirty-state P7

- nouveaux registres `DiagnosticCompanionDirtyState` ;
- saisie d'acte/brouillon praticien = dirty ;
- `beforeunload` protège le travail ;
- `StudioTabs` demande confirmation avant abandon ;
- reset et transfert confirmé nettoient le dirty-state.

## Preuves locales exécutées

### Policy P7
- `tsc --strict` : **PASS** ;
- assertions initiales safety/transfer : **8/8 PASS**.

### Chaîne consolidée P7→P3 + dirty
- `tsc --strict` : **PASS** ;
- **12/12 assertions PASS** :
  1. transfert refusé sans confirmation ;
  2. acte manuel confirmé transférable ;
  3. normalisation espaces ;
  4. une ligne Devis éligible ;
  5. prix Devis neutre = 0 ;
  6. aucune dent inventée ;
  7. texte médicamenteux possible uniquement comme saisie praticien ;
  8. instruction médicamenteuse filtrée du Devis ;
  9. ligne mixte médicament + acte filtrée fail-closed ;
  10. dirty initial propre ;
  11. dirty après travail praticien ;
  12. dirty nettoyé après reset/transfert.

## Fichiers principaux

- `frontend/src/features/admin/DocumentStudio/TreatmentPlanStudio.tsx`
- `frontend/src/features/admin/DocumentStudio/DiagnosticCompanionPolicy.ts`
- `frontend/src/features/admin/DocumentStudio/DiagnosticCompanionDirtyState.ts`
- `frontend/src/features/admin/DocumentStudio/AccountingPlanConversionPolicy.ts`
- `frontend/src/features/admin/DocumentStudio/StudioTabs.tsx`

## Gates différés

Non exécutés et non revendiqués :
- vrai `npm test` / `npm run build` full-project ;
- runtime authentifié avec patient réel ;
- vérification visuelle et interaction clavier/touch ;
- test réel P7→P3 dans l'application complète ;
- validation clinique/scientifique humaine de toute future orientation qui deviendrait plus spécifique ;
- analyse réglementaire applicable au produit final ;
- ready review / merge / post-merge.

## Conclusion

Les sorties autonomes à risque de la baseline P7 ont été supprimées. Le compagnon courant structure la consultation et protège le transfert des actes praticien, sans diagnostiquer ni prescrire automatiquement.