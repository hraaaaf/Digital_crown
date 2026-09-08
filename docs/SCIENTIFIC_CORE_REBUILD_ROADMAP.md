# DIGITAL CROWN — SCIENTIFIC CORE REBUILD — CANONICAL HANDOVER

**Rôle de ce fichier :** source canonique de reprise de tout le chantier Scientific Core.  
**Règle de reprise :** dans une nouvelle conversation, lire ce fichier en premier, puis vérifier `repo / branche / PR / HEAD / CI` avant toute modification. Ne jamais supposer que les SHA ou runs ci-dessous sont encore courants.

---

## 1. GOAL FINAL

Reconstruire le noyau scientifique de Digital Crown pour qu'il soit :

- minimal et maintenable ;
- explicable ;
- déterministe quand possible ;
- versionné et sourcé ;
- patient-specific quand le contexte clinique le permet ;
- **fail-closed** quand une donnée clinique indispensable manque ;
- sans moteur mort, doublon inutile ou règle clinique inventée ;
- sans donnée patient synthétique ;
- sans diagnostic ou recommandation automatique présentés comme vérité ;
- avec praticien toujours décisionnaire ;
- couvert par tests, golden cases, négatifs, non-régression et CI avant merge.

### Succès observable

1. un moteur canonique par responsabilité scientifique ;
2. aucun wrapper/service scientifique dormant ou redondant non justifié ;
3. aucune règle clinique active non sourcée/versionnée dans le futur moteur ;
4. aucune valeur patient par défaut susceptible de modifier une décision clinique ;
5. séparation nette : contexte patient / observation / diagnostic / safety / recommandation ;
6. provenance et niveau de confiance disponibles lorsque pertinents ;
7. CI + tests scientifiques verts avant merge ;
8. revue humaine obligatoire pour les règles médicales sensibles.

### Preuve finale attendue

- code consolidé ;
- tests unitaires + golden cases + cas négatifs/fail-closed ;
- tests runtime/non-régression ;
- docs canoniques cohérentes ;
- PR certifiée ;
- merge `master` ;
- CI post-merge verte.

**Aucun déploiement Vercel sans autorisation explicite du user.**

---

## 2. PRINCIPES DE CLASSIFICATION

Chaque moteur/règle est classé :

- `KEEP` : actif, utile, responsabilité claire, comportement acceptable.
- `CONSOLIDATE` : actif/utile mais redondant avec un autre moteur.
- `REPLACE` : actif mais scientifiquement insuffisant, trop absolu, non sourcé ou dangereux.
- `DELETE` : mort, obsolète, sans consommateur réel ou responsabilité abandonnée.

Règle dure : **une couche clinique active classée `REPLACE` n'est pas supprimée sans couverture/remplacement prouvé.**

---

## 3. REPO / BRANCHE / PR — DERNIER ÉTAT VÉRIFIÉ

Repo : `hraaaaf/Digital_crown`  
Branche chantier : `refactor/scientific-core-purge`  
PR : `#371` — **draft**, ouverte, mergeable au dernier contrôle  
Base : `master`  
HEAD vérifié avant mise à jour de ce canonique : `626586ab45ac3e91b57cd99d558f18d3fc78bf81`  
Commit HEAD : `test: reject legacy antibiotic act heuristic`

### CI vérifiée sur ce HEAD

- CI principale : run `34226817489` — **SUCCESS**
- Patient Indicators Truth Certification : run `34226817475` — **SUCCESS**
- T2 Runtime Browser Certification : run `34226817448` — **SUCCESS**
- les certifications déjà suivies sur ce lot étaient vertes au dernier contrôle.

**Important :** cette mise à jour documentaire crée un nouveau HEAD. En reprise, toujours relire le HEAD courant et les runs associés.

---

## 4. ÉTAT GLOBAL DU CHANTIER

### Phase 1 — Nettoyage scientifique

**EN COURS.**

Objectif : retirer le code mort et les faux garde-fous, identifier les moteurs actifs, classifier chaque règle/moteur et sécuriser les frontières avant reconstruction.

### Phase 2 — Consolidation

**PAS ENCORE COMMENCÉE FORMELLEMENT.**

Cible : un moteur canonique par responsabilité + contrats d'entrée/sortie normalisés.

### Phase 3 — Rebuild

**PAS ENCORE COMMENCÉE FORMELLEMENT.**

Cible : reconstruire uniquement ce qui manque après purge/consolidation.

### Phase 4 — Certification scientifique

**PAS ENCORE COMMENCÉE FORMELLEMENT.**

Cible : golden cases, cas négatifs, fail-closed, runtime, non-régression, revue humaine des règles sensibles.

---

# PHASE 1 — NETTOYAGE

## LOT 1 — `TreatmentPlanEngine`

### État

**SUPPRIMÉ ET CERTIFIÉ SUR PR.**

### Preuves

- moteur dormant supprimé ;
- imports/tests dédiés retirés ;
- contrat anti-régression ajouté ;
- runners temporaires de purge retirés ;
- CI antérieure `34222898913` : SUCCESS ;
- certifications Patient Indicators, T2 Runtime, Catalog Connected Truth, Patient P7 et Settings TemplateEngine : SUCCESS sur le lot correspondant.

### Décision

`DELETE` confirmé.

---

## LOT 2 — Prescription / Medication Safety Legacy

### Goal

Éliminer les faux signaux et données synthétiques, puis remplacer les heuristiques médicales non sourcées par un moteur patient-specific déterministe et traçable.

### État

**NETTOYAGE PARTIEL CERTIFIÉ. REBUILD RESTANT.**

### Corrections déjà appliquées

- une allergie générique ne devient plus automatiquement une alerte pénicilline ;
- le rappel `pas de détartrage depuis 12 mois` a été retiré du medication-safety ;
- les alertes spécifiques pénicilline et DDI ont été conservées ;
- l'heuristique invalide `antibiotique sans acte invasif => incohérent` a été supprimée/neutralisée aux chemins publics concernés ;
- tests adaptés pour empêcher sa réintroduction ;
- CI du HEAD `626586ab...` : SUCCESS.

### Gap safety UX déjà prouvé dans l'ordonnance

Dans le frontend ordonnance :

- `PrescriptionAgenticStudio.tsx` appelle `/prescriptions/safety/check` et maintient `safetyStatus` ;
- `useDocumentGenerator.ts` valide payload/cohérence locale avant génération ;
- **le générateur final ne connaît pas directement `safetyStatus`** ;
- donc un safety-check pending/error/unverified n'est pas, à lui seul, un gate final de save/print.

Classement : **P0/P1 safety UX à traiter**, sans inventer un hard-stop médical automatique. Tout comportement d'override clinique nécessite décision explicite + règle sourcée.

### Forme pharmaceutique

Vérification antérieure :

- `PrescriptionFormPolicy.ts` préserve les formes explicitement saisies ;
- malgré un fallback ancien `forme || 'Sachets'` dans le générateur, l'intercepteur actuel restaure la forme source ou vide ;
- **ne pas présenter actuellement l'invention silencieuse de forme comme bug prouvé** sans nouvelle régression.

### Classement global

`REPLACE / CONSOLIDATE`.

---

## LOT 3 — `clinical_rules_engine.py`

### État

**ACTIF RUNTIME. AUDIT PARTIEL. `REPLACE / CONSOLIDATE`.**

### Consommateurs vérifiés

- `prescription_service_legacy.py` appelle directement `clinical_rules.analyze_case()` ;
- `prescription_service.py` utilise aussi `clinical_rules` pour normaliser le contexte d'acte ;
- `prescription_agentic_service.py` passe par `prescription_service` et bénéficie de garde-fous modernes de contexte.

### Correction d'analyse importante

Une première lecture avait classé `age` / `poids` comme variables mortes. **C'était faux et a été corrigé.**

Ils sont consommés par le moteur pour :

- déterminer `is_child` ;
- influencer la forme pharmaceutique ;
- alimenter `_calculate_pediatric_dosage()`.

Ne jamais les supprimer comme code mort.

### Défaut pédiatrique critique encore à traiter

`prescription_service_legacy.py` injecte encore historiquement `poids = 70` en dur dans un chemin legacy.

Le wrapper moderne bloque actuellement le chemin legacy pour les patients `<15 ans`, mais le moteur reste dangereux s'il est appelé directement ou depuis un autre consommateur.

**Cible :** supprimer toute valeur clinique synthétique. Si poids/âge requis manquent, la décision correspondante doit devenir non évaluable / fail-closed.

### Règles déjà classées

1. **Clindamycine 600 mg comme alternative automatique de prophylaxie d'endocardite**
   - `REPLACE`.
   - recherche antérieure : recommandations AAPD/AHA contemporaines ne recommandent plus la clindamycine pour cette prophylaxie dentaire.
   - revalider la source/version exacte avant implémentation finale.

2. **Grossesse : tablier plombé + collerette déclarés obligatoires**
   - `REPLACE / CONFLIT DE SOURCES`.
   - certaines recommandations récentes ne préconisent plus le shielding systématique, tandis que des sources plus anciennes divergent.
   - futur moteur : source/version + contexte réglementaire local explicites.

3. **Saccharomyces boulardii ajouté automatiquement après amoxicilline/Augmentin**
   - `REPLACE / DELETE AUTO-RECOMMENDATION`.
   - données insuffisantes pour en faire une recommandation automatique universelle.

4. **Implant => prophylaxie antibiotique automatique**
   - `REPLACE / NON SOURCÉ`.
   - ne pas présenter une prophylaxie universelle comme vérité établie.

5. **Grossesse => AINS interdits uniformément**
   - `REPLACE`.
   - risque et recommandations dépendent notamment de l'âge gestationnel ; l'âge gestationnel doit être explicite si la règle en dépend.

6. **Mapping acte/diagnostic => médicament**
   - `REPLACE / REASONING REQUIRED`.
   - le futur moteur ne doit pas faire `mot-clé acte => molécule` sans diagnostic, symptômes, signes systémiques, traitement étiologique et contexte patient.

### Next sur ce lot

- tracer les éventuels consommateurs supplémentaires ;
- identifier les garde-fous uniques qu'il ne faut pas perdre ;
- supprimer la valeur de poids synthétique ;
- rendre la voie concernée fail-closed ;
- sortir progressivement les règles obsolètes/trop absolues uniquement avec tests et remplacement prouvé.

---

## LOT 4 — `clinical_coherence.py`

### État

**ACTIF RUNTIME. `REPLACE / CONSOLIDATE`.**

### Déjà fait

L'heuristique :

`antibiotique + absence d'acte invasif => incohérence`

a été retirée comme faux signal scientifique, avec test anti-régression sur le chemin concerné.

### Restant

Inventorier chaque règle de cohérence et rechercher :

- doublons avec prescription safety ;
- règles absolues non sourcées ;
- alertes de confort mélangées aux alertes cliniques ;
- règles de dose/interaction qui devraient appartenir au futur Pharmacology Engine.

---

## LOT 5 — Imagerie panoramique

### Goal

Identifier un seul pipeline produit réel, retirer les wrappers morts, consolider les moteurs actifs et empêcher qu'une détection visuelle soit automatiquement transformée en diagnostic ou traitement.

### État vérifié

Pipeline produit actuel identifié :

`/upload-panoramic` → `panoramic_service.detect_teeth_only()` → `sota_panoramic_service`

### Classification courante

| Composant | État courant |
|---|---|
| `panoramic_service.py` | `KEEP / CONSOLIDATE` — utilisé par la route produit |
| `sota_panoramic_service.py` | `KEEP` — pipeline ONNX réellement appelé |
| `panoramic_ai_advisor.py` | `DELETE` candidat fort, suppression NON encore certifiée |
| `panoramic_expert_engine.py` | `DELETE` candidat fort, suppression NON encore certifiée |
| `panoramic_vision_service.py` | `DELETE` candidat fort, suppression NON encore certifiée |
| `panoramic_report_engine.py` | audit restant |
| `vision_service.py` | audit restant |
| `sota_vision_service.py` | audit restant |

### Preuves déjà établies

- `panoramic_service.py` et `sota_panoramic_service.py` implémentent des responsabilités fortement chevauchantes ;
- `panoramic_service.detect_teeth_only()` délègue déjà à `sota_panoramic_service` ;
- `elite_manager` ne consomme pas `panoramic_ai_advisor` dans le chemin inspecté ;
- le produit actuel présente les analyses persistées comme repères dentaires, sans anomalie automatique dans le chemin vérifié.

### ATTENTION

Les trois candidats `panoramic_ai_advisor.py`, `panoramic_expert_engine.py`, `panoramic_vision_service.py` **ne sont pas encore déclarés supprimables avec preuve exhaustive**.

Avant suppression : vérifier imports, routes, tests, scripts, jobs, exports et arbre réel du HEAD. Zéro consommateur prouvé → suppression + contrat anti-régression + CI.

### NEXT EXACT DU CHANTIER

**Finir cette preuve d'usage panoramique puis supprimer uniquement les wrappers réellement morts.**

---

## LOT 6 — Vision / Report Engines

### État

**À AUDITER après la fermeture du cluster panoramique.**

Cibles connues :

- `panoramic_report_engine.py` ;
- `vision_service.py` ;
- `sota_vision_service.py` ;
- generators/reporting associés.

Goal : séparer clairement détection, mesure, interprétation clinique et génération de rapport.

---

## LOT 7 — Céphalométrie

### Pipeline connu à revalider sur HEAD

`upload → ia.py → CephaloService → calibration → VisionEngine PyTorch 19 ou ONNX 38 → CephaloEngine → repository → édition frontend → refine → validator → PDF`

Landmarks historiquement présents : S, N, Or, Po, A, B, Pog, Me, Gn, Go, U1/L1 incisal, UL/LL, Sn, Pog_soft, PNS, ANS, Ar, apex U1/L1, U6/L6, etc.

Mesures historiquement présentes : SNA, SNB, ANB, IMPA, I_Francfort, Inter_Incisif, Wits, Tweed/FMA, naso-labial, surplomb/recouvrement, etc.

### Goal

- un seul pipeline de landmarks réellement supporté ;
- calibration explicite ;
- distinction prediction vs correction manuelle ;
- mesures déterministes à partir de landmarks validés ;
- pas de conclusion clinique automatique non sourcée ;
- validator avant export ;
- golden cases géométriques et cas limites.

### État

**AUDIT NON ENCORE DÉMARRÉ DANS CE CHANTIER.**

---

# PHASE 2 — CONSOLIDATION CIBLE

Après nettoyage :

1. `PatientClinicalContext`
   - âge ;
   - poids/BSA lorsque pertinent ;
   - allergies ;
   - diagnostics/conditions ;
   - médicaments actifs ;
   - grossesse + âge gestationnel si pertinent ;
   - fonction rénale/hépatique ;
   - données biologiques utiles ;
   - indication clinique actuelle.

2. `MedicationKnowledge`
   - DCI/ingrédients ;
   - classe/ATC ;
   - marques ;
   - dosage/strength ;
   - forme ;
   - voie ;
   - présentation ;
   - disponibilité marché/pays ;
   - source/version/date d'effet.

3. `MedicationSafetyEngine`
   - allergie/cross-réactivité ;
   - interactions ;
   - duplications ;
   - contre-indications ;
   - limites de dose ;
   - rénal/hépatique ;
   - grossesse/allaitement ;
   - données manquantes ;
   - sévérité/management explicites.

4. `DentalClinicalReasoningEngine`
   - diagnostic ;
   - symptômes ;
   - signes systémiques ;
   - indication ;
   - traitement étiologique ;
   - proposition explicable, non autoritaire.

5. `ImagingPipeline`
   - acquisition ;
   - détection/landmarks ;
   - mesures ;
   - validation ;
   - interprétation séparée ;
   - rapport.

6. `CephaloEngine`
   - landmarks validés ;
   - calibration ;
   - mesures déterministes ;
   - provenance/version modèle ;
   - correction humaine traçable.

---

# PHASE 3 — MEDICATION INTELLIGENCE TARGET

Le manque principal identifié n'est **pas un meilleur autocomplete** mais un vrai moteur patient-specific de medication intelligence / clinical decision support.

### Flow cible

`médicament sélectionné`
→ résolution marque/DCI/ingrédients
→ chargement contexte patient
→ filtrage formes/forces réellement disponibles
→ détection données indispensables manquantes
→ checks allergy/DDI/rénal/hépatique/grossesse/duplication/dose
→ options pertinentes avec raison/source
→ validation par le praticien
→ override explicite et traçable lorsqu'autorisé.

### Architecture recommandée

Approche **hybride**, pas reconstruction éditoriale de toute la pharmacologie depuis zéro :

- terminology/normalisation type RxNorm utile ;
- labels structurés type DailyMed utiles pour bootstrap ;
- catalogue officiel Maroc/AMM pour disponibilité locale ;
- base de connaissance clinique licenciée à évaluer pour interactions/dose/allergies à niveau professionnel ;
- Digital Crown orchestre, contextualise et explique.

Références externes déjà étudiées lors de l'audit : HAS LAP/LAD, RxNorm/NLM, DailyMed, Medi-Span, UpToDate Lexidrug, Oracle/Multum, Epic CDS Hooks, catalogue AMM Maroc/DMP/ANAM. **Toute règle clinique implémentée doit revalider sa source primaire, sa version et son applicabilité au Maroc avant activation.**

### Alertes cibles

Ne pas implémenter ces seuils comme règles médicales sans revue humaine :

- haute sévérité : allergie sévère documentée, contre-indication majeure, duplication/overdose dangereuse, etc. ;
- intermédiaire : interaction gérable, dose à ajuster, contexte incomplet ;
- information : formulation, administration, adhérence, information générale.

Le praticien reste décisionnaire. Le moteur doit expliquer, pas se faire passer pour le prescripteur.

---

# FRONTEND ORDONNANCE — ÉTAT CONNU

Composants audités antérieurement :

- `DocumentHub.tsx`
- `PrescriptionAgenticStudio.tsx`
- `PrescriptionAgenticStudioLegacy.tsx`
- `DrugRow.tsx`
- `QuickEntryBar.tsx`
- `StudioHeader.tsx`
- `StudioFooter.tsx`
- `useDocumentGenerator.ts`
- `PrescriptionFormPolicy.ts`

### Forces vérifiées dans le code inspecté

- quick entry ;
- DrugRow riche ;
- safety status avec accessibilité ;
- validation payload ;
- draft protection ;
- preview/save/print/archive ;
- policy conservant les formes explicites.

### Risques UX / architecture

- safety check non relié directement au gate final du générateur ;
- surcharge cognitive et plusieurs couches de warnings ;
- architecture R3 superposée au legacy via CSS descendant fragile ;
- modal de preset en `fixed` local, hors `CrownDialog` ;
- dropdown forme utilisant positionnement `fixed` local ;
- densité typographique élevée.

### Visual certification

**NON FAITE pour l'ordonnance complète dans ce chantier.**

Si une modification UI/UX est engagée :

`BEFORE → Goal visuel → mockup/référence → implémentation → AFTER mêmes viewports → comparaison + tests → score visuel`.

Viewports minimum recommandés : `390x844`, `430x932`, `768x1024`, `1366x700`, `1440x900` si disponibles.

Le workflow `mobile-documents-mob5f-cert.yml` certifie surtout `MobileQuickDocumentSheet` et ne doit pas être utilisé comme preuve visuelle de l'éditeur ordonnance complet.

---

# DÉCISIONS DURABLES DU CHANTIER

1. **Pas de LLM comme autorité scientifique ou pharmacologique.**
2. NLP/LLM éventuel uniquement pour parsing, explication ou résumé, jamais comme source primaire de dose/interaction/contre-indication.
3. Aucun patient fictif : pas d'âge, poids, grossesse, fonction rénale, etc. inventés.
4. Donnée indispensable absente : fail-closed pour la décision concernée.
5. Détection image ≠ diagnostic.
6. Diagnostic ≠ traitement automatique.
7. Chaque règle clinique sensible doit avoir source/version/provenance.
8. Conflit de sources : exposer l'incertitude, ne pas fabriquer une vérité unique.
9. Aucune suppression active sans preuve d'usage/remplacement.
10. Aucun déploiement Vercel sans autorisation explicite.
11. Ne pas mélanger ce chantier avec d'autres produits/projets. Les noms de services historiques présents dans le repo ne prouvent aucune relation architecturale externe.

---

# PROCÉDURE DE REPRISE DANS UNE NOUVELLE CONVERSATION

Exécuter dans cet ordre :

1. lire **ce fichier entier** ;
2. vérifier branche `refactor/scientific-core-purge` ;
3. vérifier PR `#371` et son état ;
4. vérifier HEAD courant ;
5. vérifier CI/runs du HEAD courant ;
6. inspecter les changements intervenus depuis le dernier HEAD consigné ;
7. reprendre au `NEXT EXACT` ci-dessous ;
8. après chaque gros lot, remettre à jour ce fichier avec état réellement vérifié ;
9. ne jamais modifier les pourcentages/états sur intuition ;
10. closeout complet avant merge.

---

# NEXT EXACT

## Action immédiate

**Fermer le lot panoramique :**

1. rechercher exhaustivement les consommateurs de :
   - `panoramic_ai_advisor.py`
   - `panoramic_expert_engine.py`
   - `panoramic_vision_service.py`
2. couvrir : imports, routes, tests, scripts, jobs, exports et appels indirects ;
3. si zéro consommateur réel : supprimer les wrappers ;
4. ajouter/adapter le contrat anti-régression ;
5. lancer tests ciblés + CI ;
6. pendant CI, poursuivre l'audit `panoramic_report_engine.py`, `vision_service.py`, `sota_vision_service.py` ;
7. mettre à jour ce canonique avec les preuves.

## Puis

- fermer cluster vision/report ;
- revenir au fail-closed pédiatrique et aux règles restantes de `clinical_rules_engine.py` si non encore clos ;
- inventorier complètement `clinical_coherence.py` ;
- auditer céphalométrie ;
- consolider responsabilités ;
- définir contrats scientifiques ;
- reconstruire Medication Intelligence / Clinical Reasoning ;
- certifier moteurs ;
- closeout docs ;
- PR finale ;
- merge ;
- CI post-merge.

---

# CLOSEOUT ATTENDU

Ordre obligatoire :

`validation → tests/golden cases → docs canoniques → cohérence roadmap → PR → CI → merge → post-merge CI`

Si CI en cours : ne pas attendre passivement. Faire tout travail indépendant, puis revérifier quand nécessaire.

---

## REPÈRES DE REPRISE

- chantier : Digital Crown — Scientific Core Rebuild
- phase : Phase 1 nettoyage
- lot actif : Imagerie panoramique
- Goal actif : un pipeline produit identifié, zéro wrapper scientifique mort, aucune interprétation automatique non prouvée
- repo : `hraaaaf/Digital_crown`
- branche : `refactor/scientific-core-purge`
- PR : `#371` draft
- HEAD produit vérifié avant ce commit documentaire : `626586ab45ac3e91b57cd99d558f18d3fc78bf81`
- CI principale de ce HEAD : `34226817489` — SUCCESS
- dernière preuve : pipeline `/upload-panoramic → panoramic_service.detect_teeth_only() → sota_panoramic_service` identifié ; trois wrappers restent candidats DELETE sans preuve exhaustive finale
- blocage réel : aucun blocage externe connu ; preuve d'usage panoramique à terminer
- Next exact : fermer la preuve des trois wrappers panoramiques puis supprimer uniquement ceux dont zéro consommateur est démontré
- Séquence restante : pano → vision/report → prescription/cohérence résiduelle → céphalo → consolidation → rebuild → certification → closeout → merge → post-merge
- déploiement : aucun déploiement Vercel autorisé dans ce chantier

**FICHIER CANONIQUE : `docs/SCIENTIFIC_CORE_REBUILD_ROADMAP.md`**
