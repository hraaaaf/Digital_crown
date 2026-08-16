# Document Studio P7 — audit canonique Compagnon Diagnostique

## 1. Baseline et limites de preuve

### Baseline auditée

- branche : `agent/p7-compagnon-audit` ;
- parent : stack P3→P6 `agent/p4-p6-after-p3` @ `fb75780c44d21e552b396d1f4376b657e8837994` ;
- page canonique : **P7 — Compagnon Diagnostique** ;
- entrée active vérifiée : onglet `plan` de `DocumentHub`, rendu par `TreatmentPlanStudio` ;
- connexion active vérifiée : `TreatmentPlanStudio → onConvertToQuote → convertPlanActsToQuoteItems → P3 Devis`.

### Légende de preuve

- **CODE VÉRIFIÉ** : démontré par source/diff.
- **TEST IDENTIFIÉ** : test présent dans le dépôt, sans présumer qu'il a été exécuté sur ce head.
- **TEST EXÉCUTÉ** : réellement lancé avec résultat observé.
- **INTERACTION RUNTIME** : comportement observé dans l'application réelle.
- **CERTIFICATION CLINIQUE/SCIENTIFIQUE** : validation humaine séparée, absente de cet audit.

Cet audit est principalement statique. Il ne revendique ni validation scientifique des règles diagnostiques, ni validation des protocoles thérapeutiques, ni certification clinique.

---

## 2. Architecture et flux réel

### 2.1 Entrée P7 active

`StudioTabs` expose `Compagnon Diagnostique` via `activeTab === 'plan'`.

`DocumentHub` rend :

```text
P7 / plan
  → TreatmentPlanStudio(patientId)
      → GET /patients/{patientId}
      → état local de questionnaire
      → diagnostic texte + actes proposés
      → édition/suppression/ajout d'actes
      → Créer le devis
  → convertPlanActsToQuoteItems(...)
      → prix = 0
      → dent = Global / 0
  → P3 Devis
```

### 2.2 Moteurs cliniques coexistants

Le dossier Document Studio contient au moins deux générations de logique diagnostique :

1. **flux actif P7** : `TreatmentPlanStudio.tsx`, state machine autonome et règles codées directement dans le composant ;
2. **flux legacy** : `HouseWizard.tsx` + `DiagnosticEngine.ts` + `SafeDiagnosticEngine.ts`.

Le correctif historique PR #38 protège le flux `SafeDiagnosticEngine` contre la substitution thérapeutique automatique, mais **le composant actif `TreatmentPlanStudio` possède encore sa propre logique de substitution**.

`clinical_rules.ts` est désormais une façade legacy pharmacologique fail-closed vers l'arbitre canonique ; cette discipline n'est pas appliquée au moteur diagnostique P7 actif.

### 2.3 Connexion P7 → P3

La conversion vers Devis est financièrement neutre : `convertPlanActsToQuoteItems` met `price: 0` et laisse le chiffrage au catalogue/praticien. C'est la bonne frontière.

En revanche, les actes proposés sont convertis avec `fdi: 'Global'`, car P7 ne collecte aucun site/dent cible.

### 2.4 P7 → P1

Aucune conversion active P7 → Ordonnance n'a été démontrée dans le flux `DocumentHub → TreatmentPlanStudio` inspecté. Les libellés thérapeutiques restent néanmoins prescriptifs dans le plan et les conseils cliniques.

---

## 3. Matrice produit

## GARDER

### G1 — Conversion financière neutre vers P3

**CODE VÉRIFIÉ.**

`convertPlanActsToQuoteItems` ne fabrique aucun prix : `price = 0`.

**Décision : GARDER.** Le diagnostic peut suggérer **quoi examiner/planifier**, jamais inventer le tarif.

### G2 — Patient explicite dans le flux actif

**CODE VÉRIFIÉ.**

`TreatmentPlanStudio` reçoit `patientId` depuis `DocumentHub` et recharge `/patients/{patientId}` pour le contexte médical.

**Décision : GARDER**, mais ajouter un reset de contexte strict sur changement patient.

### G3 — Édition humaine avant conversion

**CODE VÉRIFIÉ.**

Le praticien peut supprimer et ajouter des actes avant de cliquer sur `Créer le devis`.

**Décision : GARDER**, en renforçant le statut « proposition » et la traçabilité.

### G4 — Correctif historique de non-substitution du moteur legacy

**CODE VÉRIFIÉ / TEST IDENTIFIÉ.**

`SafeDiagnosticEngine` vide `medicalHistory` avant d'appeler le legacy puis ajoute seulement des avertissements. `DiagnosticEngine.p5p0.test.ts` couvre pénicilline et AINS.

**Décision : GARDER comme principe de safety**, puis l'appliquer au moteur actif ou supprimer le doublon.

---

## CORRIGER P0

### P0-1 — Substitution thérapeutique automatique encore active dans P7 réel

**CODE VÉRIFIÉ.**

Dans `TreatmentPlanStudio.handleAnswer`, les ATCD sont analysés par substring :

- présence d'un mot lié aux pénicillines + acte contenant `Antibiothérapie` → remplacement par `Clindamycine/Macrolide` ;
- présence d'un mot lié aux AINS + acte contenant `anti-inflammatoire` → remplacement par `corticostéroïdes`.

Le message UI dit explicitement que le protocole a été « automatiquement basculé/modifié ».

Le résultat modifié devient ensuite un acte du plan et peut être converti en P3 Devis.

**Pourquoi P0 :** une donnée médicale textuelle non structurée déclenche un changement thérapeutique automatique sans arbitrage pharmacologique canonique ni validation explicite du praticien.

**Correction :** fail-closed : détecter le signal → avertir → ne jamais substituer automatiquement. Toute proposition médicamenteuse doit passer par la frontière pharmacologique P1 déjà durcie et rester soumise à validation praticien.

### P0-2 — État clinique potentiellement conservé entre deux patients

**CODE VÉRIFIÉ ; scénario de navigation runtime à confirmer.**

`TreatmentPlanStudio` conserve en state local :

- `currentState` ;
- `history` ;
- `finalDiagnosis` ;
- `proposedActs` ;
- `allergyWarning`.

Sur changement de `patientId`, l'effet recharge les ATCD mais **ne réinitialise pas ces états**. `DocumentHub` rend `TreatmentPlanStudio` sans `key={patientId}`.

Si la même instance React est réutilisée lors d'un changement de dossier patient, le diagnostic/plan précédent peut rester affiché puis être converti vers le Devis du nouveau patient.

**Correction :** frontière patient atomique : reset complet dès changement de `patientId` et/ou montage avec `key={patientId}` ; test de non-contamination inter-patient obligatoire.

---

## CORRIGER P1

### P1-1 — Le système présente une proposition déterministe comme un « Diagnostic Établi »

**CODE VÉRIFIÉ.**

L'UI affiche notamment :

- `Diagnostic Établi` ;
- `Plan de Traitement Scientifique` ;
- `Diagnostic établi. Voici le plan de traitement scientifique recommandé`.

Les conclusions proviennent d'un petit arbre de réponses, sans preuve de validation clinique/scientifique attachée au résultat.

**Correction :** terminologie non prescriptive : `Hypothèse diagnostique`, `Éléments à confirmer`, `Proposition de prise en charge à valider par le praticien`.

### P1-2 — Absence de site/dent cible

**CODE VÉRIFIÉ.**

Le state machine ne collecte ni dent, ni surface, ni site anatomique. La conversion P7 → P3 force `fdi: 'Global'`.

**Correction :** lier explicitement le raisonnement à une dent/site quand le motif l'exige ; sinon marquer réellement le plan global. Ne jamais inférer un FDI.

### P1-3 — ATCD/allergies analysés en texte libre par substring

**CODE VÉRIFIÉ.**

`antecedents_medicaux` est abaissé en minuscules puis testé par `includes(...)`.

Ce mécanisme ne distingue pas, par exemple, une allergie affirmée d'une phrase négative contenant le même mot et ne constitue pas une donnée structurée d'allergie.

**Correction :** utiliser les données structurées patient comme source autoritative ; le texte libre peut seulement produire un signal « à vérifier », jamais une décision thérapeutique.

### P1-4 — Règles diagnostiques et thérapeutiques dupliquées dans plusieurs moteurs

**CODE VÉRIFIÉ.**

`TreatmentPlanStudio` encode son propre arbre ; `DiagnosticEngine` contient une autre matrice ; `SafeDiagnosticEngine` n'encapsule que cette seconde matrice.

**Correction :** une seule frontière diagnostique canonique, pure/testable/versionnée ; UI séparée de la logique clinique.

### P1-5 — Legacy `DiagnosticEngine` possède un fallback non fail-closed

**CODE VÉRIFIÉ, mais flux actif non démontré.**

Quand aucune règle ne correspond, `DiagnosticEngine.evaluateDiagnosis` retourne une `Consultation Standard`, affirme un examen normal, propose du paracétamol et un détartrage/polissage.

**Correction :** remplacer par `INSUFFICIENT_DATA / NO_RULE_MATCH`, sans diagnostic rassurant, médicament ni traitement. Puis déprécier ou supprimer le moteur legacy si aucun appel actif ne subsiste.

### P1-6 — Conseils « scientifiques » sans provenance/version

**CODE VÉRIFIÉ.**

`getClinicalTip()` contient des affirmations cliniques déterministes et parfois des pourcentages précis directement codés dans le frontend, sans source, version, date, population, niveau de preuve ou statut de validation affiché.

**Correction :** tant que non validés scientifiquement, les retirer du parcours actif ou les remplacer par un contenu sourcé/versionné avec statut de preuve explicite. La validation médicale elle-même est un gate humain séparé.

### P1-7 — Pas de provenance du raisonnement appliqué

**CODE VÉRIFIÉ.**

La conversion vers P3 transmet les actes, la phase et `Global`, mais pas :

- réponses du questionnaire ;
- règle/version ayant produit la proposition ;
- contexte patient utilisé ;
- éventuels warnings ;
- confirmation clinique du praticien.

**Correction :** snapshot immuable de provenance pour le plan P7 ; P3 reçoit une copie de travail, pas la preuve clinique elle-même.

### P1-8 — Dirty-state P7 absent

**CODE VÉRIFIÉ.**

`StudioTabs` protège Ordonnance et Document Libre contre la perte de modifications, mais aucune garde comparable n'est visible pour `plan`.

**Correction :** signaler un plan P7 non converti/non sauvegardé avant changement d'onglet ou de patient.

### P1-9 — Les actes cliniques peuvent contenir implicitement une prescription

**CODE VÉRIFIÉ.**

Plusieurs branches produisent des actes comme `Antibiothérapie et antalgiques`, `Antibiothérapie de couverture`, `anti-inflammatoires`, etc. Le Devis peut donc recevoir un libellé thérapeutique médicamenteux même si P7 n'ouvre pas directement P1.

**Correction :** P7 → P3 doit produire des actes cliniques facturables/planifiables, pas une prescription médicamenteuse. Une éventuelle P7 → P1 doit être une proposition séparée, explicitement revue dans Ordonnance et repassée par les règles pharmacologiques P1.

---

## AMÉLIORER

### A1 — Transformer le questionnaire en recueil clinique traçable

Conserver les réponses comme données structurées : motif, caractère douleur, percussion, site, imagerie, durée, contexte patient, données manquantes.

### A2 — Distinguer quatre sorties

1. données observées ;
2. hypothèses différentielles ;
3. red flags / informations manquantes ;
4. actes proposés à confirmer.

Ne plus mélanger diagnostic, traitement, médicament, conseil scientifique et devis dans un même résultat.

### A3 — Montrer pourquoi une proposition existe

Afficher les entrées utilisées et les entrées absentes. Une règle ne doit pas ignorer silencieusement une information recueillie.

### A4 — Rendre les transitions réversibles

Permettre `modifier une réponse`, `revenir`, `réinitialiser`, avec recalcul déterministe et suppression de toute sortie dérivée devenue obsolète.

---

## SIMPLIFIER / SUPPRIMER

### S1 — Supprimer la pharmacovigilance locale de `TreatmentPlanStudio`

La page ne doit pas contenir un deuxième moteur pharmacologique par `includes(...)`.

### S2 — Déprécier `HouseWizard` / `DiagnosticEngine` si non branchés

Le flux actif P7 démontré passe par `TreatmentPlanStudio`. Les anciens moteurs augmentent le risque de divergence ou de réactivation accidentelle de comportements non sûrs.

Avant suppression, rechercher tous les imports/callers dans le build réel.

### S3 — Retirer les slogans de certitude clinique

`Diagnostic Établi`, `scientifique recommandé`, `Intelligence Clinique Proactive` ne doivent pas masquer l'absence de certification scientifique du moteur.

---

## 4. Contrat cible P7

### Entrées autorisées

P7 reçoit explicitement :

- `patient_id` actif ;
- dent/site si pertinent ;
- observations cliniques structurées ;
- imagerie/observations uniquement si réellement disponibles ;
- antécédents/allergies structurés en lecture seule ;
- réponses manuelles du praticien.

### Règles de safety

1. **aucune donnée manquante n'est inventée** ;
2. **aucun no-match ne produit un diagnostic ou traitement par défaut** ;
3. **aucune allergie/ATCD ne déclenche une substitution thérapeutique automatique** ;
4. **aucun médicament n'est poussé directement vers Ordonnance** ;
5. **aucun prix n'est inventé** ;
6. **aucune dent n'est inventée** ;
7. **changement de patient = reset atomique du contexte P7** ;
8. toute sortie est `proposition / à confirmer`, jamais un diagnostic final certifié par le logiciel.

### Sortie cible

```text
DiagnosticCompanionProposal
  patient_id
  target_sites[]
  observations{}
  missing_data[]
  differential_hypotheses[]
  red_flags[]
  proposed_acts[]
  medication_review_required: bool
  rule_set_id
  rule_set_version
  evidence_status
  created_at
  practitioner_confirmation
```

Aucune propriété `final_diagnosis` autoritative ne doit être créée par défaut.

---

## 5. Connexions inter-pages

### P7 → P3 Devis

**GARDER la conversion explicite**, avec contraintes :

- snapshot ;
- actes uniquement ;
- prix = 0 jusqu'au catalogue/praticien ;
- dent/site seulement si collecté ;
- aucune molécule/substitution issue des ATCD ;
- provenance P7 conservée séparément.

### P7 → P1 Ordonnance

**Aucune écriture directe.**

Une éventuelle action `Préparer une proposition d'ordonnance` doit :

1. ouvrir P1 ;
2. ne jamais auto-archiver/imprimer ;
3. repasser par le pipeline pharmacologique canonique ;
4. exiger une validation explicite du praticien.

### P7 → dossier patient

Le diagnostic logiciel ne doit pas devenir un diagnostic clinique définitif sans confirmation praticien. Si persistance, stocker proposition + provenance + validation séparément.

---

## 6. Lots correctifs canoniques

### P7-A — Safety boundary immédiate

- supprimer substitutions pénicilline/AINS du `TreatmentPlanStudio` actif ;
- remplacer par warning-only ;
- reset complet sur changement `patientId` ;
- tests de non-substitution et non-contamination inter-patient.

### P7-B — Fail-closed engine unique

- extraire la state machine du composant ;
- `NO_RULE_MATCH / INSUFFICIENT_DATA` ;
- aucune sortie thérapeutique par défaut ;
- déprécier legacy fallback.

### P7-C — Contexte clinique structuré

- dent/site ;
- allergies/ATCD structurés ;
- données manquantes explicites ;
- séparation observation/hypothèse.

### P7-D — Contrat non prescriptif + terminologie

- `Hypothèse à confirmer` ;
- retirer certitude clinique et slogans scientifiques non certifiés ;
- séparer plan clinique et médicament.

### P7-E — Provenance/version/evidence

- règle/version ;
- entrées utilisées ;
- warnings ;
- statut de preuve ;
- confirmation praticien.

### P7-F — Inter-pages

- P7→P3 snapshot neutre ;
- éventuel P7→P1 uniquement via revue P1 ;
- dirty-state et changement patient/onglet.

### P7-G — UX / responsive / accessibilité

- clavier ;
- focus ;
- mobile 390 ;
- tablette 768 ;
- desktop ;
- retour/modification d'une réponse ;
- loading/error patient context.

### P7-H — Validation scientifique et recertification finale

- revue humaine des règles diagnostiques et thérapeutiques ;
- sources/versionnement ;
- cas synthétiques positifs/négatifs/no-match ;
- runtime authentifié ;
- non-contamination inter-patient ;
- P7→P3/P1 ;
- régression full repo.

---

## 7. Gates runtime encore ouverts

1. changement réel patient A → patient B en restant sur P7 ;
2. vérification que le plan A ne reste jamais disponible pour B ;
3. ATCD avec allergie vraie / texte négatif / terme ambigu ;
4. aucune substitution thérapeutique automatique ;
5. no-match / données incomplètes ;
6. conversion P7→P3 sans prix ni dent inventés ;
7. absence d'écriture directe P7→P1 ;
8. changement onglet avec plan non converti ;
9. 390/768/desktop + clavier ;
10. validation scientifique humaine indépendante.

---

## Verdict

**P7 n'est pas certifiable dans son état actuel.**

Deux frontières critiques dominent le chemin :

- **P0 actif : substitution thérapeutique automatique dans `TreatmentPlanStudio`** ;
- **P0 de contexte : état diagnostic/plan non réinitialisé explicitement au changement patient, avec risque de contamination inter-patient si l'instance est réutilisée.**

Le chemin critique est donc : **P7-A → P7-B → P7-C/D/E/F → P7-G → P7-H**.

Aucune conclusion de cet audit ne vaut validation médicale des règles ; la validation scientifique reste un gate humain séparé.
