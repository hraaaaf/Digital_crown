# Document Studio P7 — statut d’intégration Compagnon Diagnostique

## Baseline

- Branche : `agent/p7g-responsive-a11y`.
- Baseline audit : PR #81 / `agent/p7-compagnon-audit`.
- Stack corrective : P7-A → P7-B → P7-D → P7-F → P7-G.
- Page canonique : **P7 — Compagnon Diagnostique**.
- Ce document distingue strictement engineering, tests réellement exécutés, runtime et validation scientifique.

## P7-A — safety boundary

**Engineering implémenté.**

- suppression de la substitution thérapeutique automatique liée aux ATCD texte libre ;
- signaux pénicilline/AINS transformés en warning-only ;
- aucun remplacement automatique par clindamycine/macrolide/corticostéroïdes ;
- changement `patientId` = reset atomique questionnaire/historique/hypothèse/actes/warnings ;
- réponse réseau tardive de l’ancien patient ignorée ;
- tests ciblés ajoutés.

**Preuve d’exécution actuelle : aucune exécution CI/runtime observée sur le head final.**

## P7-B — fail-closed legacy engine

**Engineering implémenté.**

Le fallback legacy qui fabriquait `Consultation Standard`, examen normal, paracétamol et détartrage lorsqu’aucune règle ne correspondait est neutralisé à la frontière `SafeDiagnosticEngine` :

- no-match → `Données insuffisantes / règle non couverte` ;
- protocol vide ;
- treatmentPlan vide ;
- validation praticien requise ;
- aucun traitement rassurant par défaut.

Test no-match ajouté au fichier historique `DiagnosticEngine.p5p0.test.ts`.

**P7-B ne signifie pas encore que les deux moteurs P7 sont unifiés.** Le flux actif reste `TreatmentPlanStudio`; le legacy reste présent tant que sa suppression/centralisation n’est pas réalisée.

## P7-C — contexte clinique structuré

**OUVERT — dépendance d’architecture patient.**

Vérification du schéma patient : il existe `antecedents_medicaux: Optional[str]`, mais aucun champ allergies structuré n’a été démontré dans la baseline inspectée.

Conséquence : le chantier n’invente pas une source de vérité d’allergie qui n’existe pas. Le texte libre reste un **signal à vérifier uniquement**, jamais une décision thérapeutique.

Reste à définir puis implémenter, avec gouvernance clinique adaptée :

- allergies structurées ;
- dent/site cible lorsque pertinent ;
- observations vs données manquantes ;
- source autoritative et migration des données existantes.

## P7-D — contrat non prescriptif

**Engineering implémenté.**

Sans modifier les branches cliniques ni les actes proposés :

- `Diagnostic Établi` → `Hypothèse à confirmer` ;
- disclaimer explicite : sortie logicielle déterministe ≠ diagnostic clinique validé ;
- `Plan de Traitement Scientifique` → proposition à valider ;
- conversion P7→P3 renommée comme préparation de devis à partir d’une proposition ;
- bloc de conseils cliniques hard-codés non sourcés/versionnés retiré de l’UI active jusqu’au gate scientifique P7-H ;
- test de contrat UI ajouté.

## P7-E — provenance / version / evidence

**OUVERT — contrat de persistance non défini.**

Aucun modèle canonique persistant de proposition P7 avec :

- rule-set id/version ;
- entrées utilisées ;
- données manquantes ;
- warnings ;
- evidence status ;
- confirmation praticien ;
- timestamp/snapshot ;

n’a été démontré dans le flux actif.

Ce lot exige une décision d’architecture avant persistance afin d’éviter de transformer une proposition logicielle en diagnostic clinique définitif par simple effet de schéma.

## P7-F — dirty-state / inter-pages

**Engineering implémenté.**

- nouveau `P7DirtyState` ;
- réponse/ajout/suppression → dirty ;
- reset/conversion explicite → clean ;
- garde avant changement d’onglet ;
- garde `beforeunload` ;
- changement patient reste un reset fail-safe via P7-A ;
- tests ciblés ajoutés.

La conversion P7→P3 continue de passer par `AccountingPlanConversionPolicy`, qui possède un test existant vérifiant : prix = 0, dent non inventée si absente, phase conservée, proposition vide supprimée.

## P7-G — responsive / accessibilité

**Engineering implémenté.**

- hauteur bornée et adaptée au viewport ;
- options pleine largeur mobile ;
- messages et actes avec wrapping ;
- contrôles d’ajout adaptatifs mobile/desktop ;
- boutons `type=button` ;
- focus visible ;
- noms accessibles reset/suppression/ajout ;
- warning ATCD `role=alert` ;
- résultat `aria-live=polite` ;
- test d’accessibilité des contrôles critiques ajouté.

**Inspection réelle 390/768/desktop non exécutée.**

## P7-H — validation scientifique + recertification finale

**OUVERT — gate humain/externe.**

Aucune conclusion actuelle ne valide médicalement :

- les règles diagnostiques ;
- les libellés thérapeutiques ;
- les seuils/conditions ;
- la pertinence des propositions ;
- les conseils historiques retirés de l’UI.

P7-H doit inclure revue scientifique humaine, sources/versionnement, cas synthétiques positifs/négatifs/no-match, runtime authentifié, non-contamination inter-patient et full-regression.

## Harness automatisé

`scripts/certify_document_studio_p7.sh` regroupe uniquement des tests réellement présents :

1. `DiagnosticEngine.p5p0.test.ts` ;
2. `TreatmentPlanStudio.p7a.test.tsx` ;
3. `TreatmentPlanStudio.p7d.test.tsx` ;
4. `P7DirtyState.p7f.test.tsx` ;
5. `TreatmentPlanStudio.p7g.test.tsx` ;
6. `AccountingPlanConversionPolicy.test.ts` ;
7. full frontend suite ;
8. frontend production build.

Le harness exige Node 20 et un worktree propre et échoue fermé.

**État de preuve : harness écrit, pas encore exécuté avec résultat observé sur le head final.**

## CI

Les heads P7-A, P7-B, P7-D, P7-F et P7-G contrôlés pendant le chantier n’ont pas créé de workflow run observable au moment du contrôle. Cela ne vaut ni PASS ni échec applicatif.

L’infrastructure GitHub Actions avait déjà montré sur P4→P6 des jobs `failure` avec `steps:null`; la cause exacte du non-déclenchement P7 n’est pas prouvée ici.

## Verdict

### Fermé en engineering

- **P7-A** safety thérapeutique / frontière patient ;
- **P7-B** no-match legacy fail-closed ;
- **P7-D** contrat non prescriptif ;
- **P7-F** dirty-state/inter-pages ;
- **P7-G** responsive/accessibilité engineering.

### Ouvert

- **P7-C** contexte clinique structuré : dépendance modèle patient ;
- **P7-E** provenance/version/evidence : dépendance architecture/persistance ;
- **P7-H** validation scientifique humaine + runtime/recertification.

**P7 n’est pas certifié.** Les P0 statiques identifiés au baseline sont corrigés en engineering, mais aucun PASS d’exécution sur le head final n’est revendiqué et les gates C/E/H restent ouverts.
