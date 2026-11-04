# Digital Crown — Céphalo V1 — LOT 1/4 (R11–R14)
## Dossier de revue des sources scientifiques et FUE préflight v1

**Statut : HOLD / NOT CLINICALLY APPROVED / NOT DEPLOYED.** Ce dossier ne constitue pas une certification clinique ni une décision d'activation d'une règle. Il accompagne la [PR Draft #1208](https://github.com/hraaaaf/Digital_crown/pull/1208) et le [canonique Notion unique](https://app.notion.com/p/3ec77c663362811db11ec59dbd9eb7d3).

### 1. Inventaire réellement issu du code (pas d'une validation bibliographique externe)

| Registre | Code-source | Etat et portée |
|---|---|---|
| Références normatives descriptives | `backend/services/cephalo_norm_registry.py` | Les sources, échantillons et références chiffrées enregistrés sont des métadonnées. Les références patient sont **inactives** : `active_for_patient_classification=False`. Le registre ne diagnostique pas. |
| R11 — finding et diagnostic | `backend/services/cephalo_diagnostic_rule_registry.py` | Registre **production vide** : `FindingRuleDefinition` et `DiagnosticRuleDefinition` non enregistrés. Aucun seuil ni moteur autonome. Les règles doivent lier source scientifique et version exactes. |
| R13 — critères et options | `backend/services/cephalo_therapeutic_rule_registry.py` | Registre **production vide** : `TherapeuticSourceDefinition`, critères indication/contre-indication, et options non enregistrés. Pas de prescription autonome. |
| Vérification R11 | `backend/services/cephalo_r11_diagnostic_safety.py` | Refuse les références absentes ou inactives utilisées comme classification et exige des bindings source/règle exacts. |
| Vérification R13–R14 | `backend/services/cephalo_r13_therapeutic_safety.py`, `cephalo_r14_final_validation_safety.py` | Vérifie liens d'origine, règles, avis praticien, conflits et conformité des critères. Aucun agrément médical implicite. |
| Présentation et PDF | `backend/services/cephalo_r15_clinical_studio.py`, `cephalo_pdf_projection.py` | `clinical_validation_available=false`, `document_state=INCOMPLETE` tant que les preuves et validations autorisées ne sont pas réunies. |

**Point scientifique critique explicite dans le code :** certaines références McNamara 1984 décrivent un échantillon Ann Arbor et une convention d'agrandissement radiographique de **8 %**. Le code les conserve comme références descriptives et interdit toute comparaison en millimètres physiques calibrés tant que la compatibilité de l'échelle n'est pas prouvée. Les références populationnelles (âge, sexe, population d'origine, état thérapeutique, indications d'inclusion/exclusion) ne doivent pas devenir des normes universelles par défaut.

Ce document n'atteste **ni la qualité réelle d'un article, ni sa pertinence pour la population marocaine, ni l'approbation d'une valeur clinique**. Ces étapes nécessitent une recherche bibliographique et un examen signés par des praticiens qualifiés.

### 2. Fiche de revue obligatoire par source + règle (à remplir par des personnes autorisées)

Ne pas modifier les registres `registry = ...` vides en production avant qu'un dossier individuel contienne TOUS les points ci-dessous :

1. **Source exacte** : titre, auteurs, année, revue/organisme, DOI/PMID/URL officielle et version du document accessible. Référence vérifiée indépendamment de ce dépôt.
2. **Qualité/validité** : type d'étude, comité/consensus, méthode et biais/limites; si données normatives, effectif et stratégie d'échantillonnage.
3. **Population d'applicabilité** : âge, sexe, géographie/ethnicité si pertinent, statut orthodontique, contexte de croissance, pathologies et critères d'exclusion. Les données non démontrées restent « non applicable ».
4. **Mesure et méthode** : landmarks, construction, unité, calibration, convention d'agrandissement (dont 8 % McNamara), incertitude, reproductibilité et identité exacte `method_id`/`method_version`.
5. **R11** : formulation du finding, critères diagnostiques, contre-hypothèses, données manquantes, incohérences, gestion des valeurs limites ; l'interprétation appartient au clinicien.
6. **R13** : indication, contre-indication explicite, alternatives et observation clinique nécessaire, effets indésirables/risques, priorités et cas de refus ; aucune option thérapeutique automatique.
7. **Versioning immuable** : `source_id@version`, `rule_id@version`, contexte requis, référence de revue, journal des modifications et stratégie de révocation.
8. **Relecture indépendante** : identité du chirurgien-dentiste/orthodontiste habilité, date, décision APPROUVER/REFUSER/A_COMPLETER, justification et référence d'une trace vérifiable. Une simple case cochée ou un test synthétique ne vaut pas signature.
9. **Concordance scientifique + logiciel** : résultats sur des cas de référence annotés, double lecture manuelle, seuils et erreurs contrôlés, FUE clinique satisfaisantes.
10. **Décision de publication** : validation explicite de la direction médicale/réglementaire **distincte d'un merge technique**; règle activée seulement via un processus de release séparé et documenté.

**Etat au 2026-11-04 :** aucune revue indépendante signée communiquée; règles diagnostiques et thérapeutiques production laissées vides; tous les champs de décision médicale restent **NON VALIDES**. Ne pas inscrire « APPROUVE » sans preuve vérifiable.

### 3. Dix FUE — matrice de préflight automatisé vs acceptation physique

Les identifiants ci-dessous sont **une proposition de 10 scénarios de recette technique préparatoire**. Les tests `backend/tests/test_cephalo_v1_lot1_fue_preflight.py` exécutent chaque scénario sur des objets **synthétiques**. Ils ne remplacent pas les séances de FUE en cabinet avec un praticien : celles-ci sont **0/10 exécutées** jusqu'à constat et signature individuels.

| ID | Scénario | Attendu de sécurité / preuve CI | Exécution FUE cabinet |
|---|---|---|---|
| FUE-01 | Registries prod + références | R11/R13 restent vides, normes descriptives inactives | **NON EXECUTEE** |
| FUE-02 | Aucune étude sélectionnée | Studio R15 bloqué, validation indisponible | **NON EXECUTEE** |
| FUE-03 | Texte clinique legacy client simulant diagnostic/plan | PDF `INCOMPLETE`, aucune récupération du texte non fiable | **NON EXECUTEE** |
| FUE-04 | Analyse d'un autre patient | Refus 404 avant tout staging ou audit | **NON EXECUTEE** |
| FUE-05 | Staging sans règles diagnostiques approuvées | Refus 409, aucun audit clinique ajouté | **NON EXECUTEE** |
| FUE-06 | Client prétend signer/choisir l'auteur d'une revue R11 | Schéma strict refuse la signature, la validation et l'auteur injectés | **NON EXECUTEE** |
| FUE-07 | Revue d'un finding sans revue du diagnostic lié | Attestation R11/R12 refusée 409 | **NON EXECUTEE** |
| FUE-08 | Deux validations identiques R11 (replay) | Refus 409, un seul audit conservé | **NON EXECUTEE** |
| FUE-09 | Sélection R13 sans attestation R11/R12 | Refus 409, aucune sélection | **NON EXECUTEE** |
| FUE-10 | Demande finale R14 sans règles approuvées | Refus 409, R15/PDF `INCOMPLETE` | **NON EXECUTEE** |

**Critère de clôture des vraies FUE** : pour chaque FUE en cabinet : version du build, étude fictive, acteur/role, patient et tenant de test, étape UI, capture, sortie API, preuve audit DB, résultat attendu/observé, signature du praticien et éventuel défaut bloquant. Aucun test réalisé sur un patient réel. Un test automatisé **PASS** ne doit jamais remplir la colonne « FUE cabinet ».

### 4. Décision de sortie (actuellement interdite)

**NO GO CLINICAL** tant que : sources et règles non approuvées, absence de signature et décision médicale indépendante, impossibilité d'appliquer des règles à une population cible démontrée, absence de validation clinique de terrain, ou 10 FUE cabinet non satisfaites. **Ne pas promouvoir R14 dans R15, ne pas produire un PDF final COMPLETE, ne pas merger ou déployer sans autorisation expresse.**

### 5. Prochain passage minimal

A. Faire relire et annoter par le praticien les dossiers scientifiques **réels**, un protocole puis une règle à la fois (ne rien inventer). B. Transformer les 10 scénarios de sécurité en sessions FUE cabinet tracées. C. Seulement après preuves et arbitrage clinique, envisager une PR distincte d'activation versionnée avec nouveaux tests ; pas dans ce lot préparatoire.

### 6. Revue bibliographique externe ciblée — 2026-11-04 (READ-ONLY ; pas de validation clinique)

**Portée exacte :** contrôle documentaire des références déjà présentes dans `cephalo_norm_registry.py`, non une revue systématique de la littérature, ni une autorisation d'utiliser une norme, d'instancier une règle R11/R13, d'activer R15 ou de signer un PDF. Les décisions du praticien restent **HUMAN_GATE_REQUIRED**.

| ID source | Matériel primaire effectivement contrôlé | Résultat documentaire | Limite et décision |
|---|---|---|---|
| `MCNAMARA_1984` | [Article original McNamara (PDF hébergé Univ. Michigan), p. 451, tableau I](https://media.dent.umich.edu/labs/mcnamara/files/A%20method%20of%20cephalometric%20evaluation.pdf) ; [PubMed 6594933](https://pubmed.ncbi.nlm.nih.gov/6594933/) | **VERIFIED_SOURCE_NUMBERS** : `Co-Gn` F 120.2±5.3 / M 134.3±6.8 mm ; `Co-A` F 91.0±4.3 / M 99.8±6.0 mm ; `ANS-Me` F 66.7±4.1 / M 74.6±5.0 mm. Les six couples enregistrés dans le code correspondent au tableau I ; effectif Ann Arbor 111 (73 F / 38 M). | L'article précise « whenever possible » un agrandissement radiographique de 8 % : cela **ne prouve pas** un facteur uniforme corrigible pour chaque valeur ou chaque équipement. Pas de comparaison avec mm physiques calibrés, pas de règle universelle ni extrapolation aux enfants/patients marocains. `HUMAN_GATE_REQUIRED`. |
| `CRANIOM_PART1_2010` + `CRANIOM_PART2_2011` | [Article/notice éditeur part 1, DOI 10.1051/odfen/2010406](https://www.cambridge.org/core/journals/journal-of-dentofacial-anomalies-and-orthodontics/article/abs/new-method-for-the-utilization-of-cephalometric-measurements-in-orthodontics-or-how-standard-deviations-can-sometimes-be-the-practitioners-false-friends-part-1/ACEE13FF9BD566F6577CAC9E151C4265) ; [part 2, DOI 10.1051/odfen/2011104](https://www.cambridge.org/core/journals/journal-of-dentofacial-anomalies-and-orthodontics/article/abs/new-method-of-using-cephalometric-measurements-in-orthodontics-part-2-or-how-standard-deviations-can-be-the-practitioners-false-friends/4FE2C16785D64E24E83771B4462E74D4) | **VERIFIED_SOURCE_EXCERPT** : 83 jeunes adultes non traités classe I, extrêmes observés `L1/Downs MP` 78–114° et `U1/FH` 97,5–130,1° correspondent aux deux références descriptives. | Extrêmes d'un échantillon sélectionné ≠ seuils diagnostiques universels. Construction géométrique exacte des plans + concordance de méthode/mesure non auditée ; ne pas déclencher extraction/non-extraction sur ces seules valeurs. `HUMAN_GATE_REQUIRED`. |
| `MOROCCO_STEINER_OUSEHAL_2012` | [PubMed 22236522](https://pubmed.ncbi.nlm.nih.gov/22236522/) ; [extrait de l'article éditeur](https://www.sciencedirect.com/science/article/pii/S1761722711001136) | **VERIFIED_ABSTRACT_AND_EXCERPTS** : étude descriptive CCTD Casablanca 71 adultes 19–27 ans, 47 F/24 M, harmonie faciale/classe I, sans orthodontie antérieure. Les auteurs déconseillent la généralisation au Maroc entier. | Texte intégral/tableaux non complètement revus dans cette passe, biais d'échantillon. Aucun seuil marocain clinique approuvé et aucune transposition pédiatrique. `HUMAN_GATE_REQUIRED`. |
| `PEDIATRIC_NORMS_REVIEW_NGUYEN_2024` | [Article intégral PMC11270148](https://pmc.ncbi.nlm.nih.gov/articles/PMC11270148/) ; [PubMed 38898629](https://pubmed.ncbi.nlm.nih.gov/38898629/) | **VERIFIED_REVIEW_SCOPE** : revue de portée de 12 études longitudinales et 33 transversales chez les ≤18 ans avec visage équilibré et occlusion normale ; croissance et effets âge/sexe documentés. | Études hétérogènes, surtout populations blanches ; ne fournit pas un seuil universel activable pour chaque âge/sexe/population. `HUMAN_GATE_REQUIRED`. |
| `CRANIOM_TECHNICAL_REPRODUCTION` | Document secondaire seulement, non réévalué | **NOT_VERIFIED_AS_PRIMARY** | Ne peut à lui seul fonder une règle ou une plage normative activable. |

**Détail de contrôle McNamara :** l'accord numérique porte sur **six couples moyenne/SD de trois mesures linéaires, ventilées par sexe**, pas sur les 13 lignes de la table I, ni sur les normes composites table II, ni sur la correspondance exacte de tous landmarks/algorithmes. Le texte primaire emploie « whenever possible » pour le 8 % ; **ne pas appliquer par défaut une division `/1.08`**. Tout calcul d'équivalence nécessite métadonnées de magnification de l'acquisition, construction anatomique identique et décision scientifique documentée.

**Conclusion scientifique :** 4 familles de références contrôlées au périmètre décrit ci-dessus ; **0 source/règle approuvée pour l'usage clinique de Digital Crown**, **0 décision thérapeutique approuvée**, aucune règle modifiée/activée. Vérification bibliographique ≠ validation clinique ≠ preuve de sécurité/release.

### 7. Feuille de route opératoire des 10 vérifications en cabinet — aucune session exécutée

**Préconditions indispensables :** build on-prem identifiable avec commit exact + hash de l'artefact ; instance isolée non clinique ; utilisateur praticien de test authentifié ; tenant/étude/patient **fictifs** ; API et logs de test uniquement ; images synthétiques ou explicitement libres de données patients ; possibilité de relever UI/API + audit DB. Aucune identité, signature ou approbation fictive ne doit être réinjectée en production. Le praticien juge l'observabilité, la sécurité et la compréhension des refus, pas la validité de seuils scientifiques non encore approuvés.

| Scénario | Manipulation guidée au cabinet (test fictif) | Attendu et pièce de preuve | Niveau possible / limite |
|---|---|---|---|
| FUE-01 | Inspecter registre effectivement chargé par build isolé et écran de normes si existant. | R11/R13 prod vides ; références inertes ; capture/log versionnés. | FUE-0 si inspection seule, pas une UX observée. |
| FUE-02 | Ouvrir le Studio clinique sans analyse sélectionnée. | Aucune validation clinique ni document final disponible ; capture BEFORE/AFTER. | FUE-I si écran exécutable. |
| FUE-03 | Charger étude fictive legacy contenant texte trompeur de diagnostic/plan, demander aperçu PDF. | Texte non promu en vérité médicale ; `INCOMPLETE` avec export inspecté. | FUE-I/G selon chemin réellement exécutable. |
| FUE-04 | Depuis deux dossiers fictifs distincts, tenter de consulter/modifier l'analyse du patient B via l'accès du patient A. | Accès refusé, aucune fuite ni mutation ; preuve API 404 et DB. | Vérification RBAC/API ; FUE-I/G seulement si vrai parcours UI. |
| FUE-05 | Demander une staging R11 avec source/règle clinique absente. | Refus 409, explication visible si UI, zéro audit clinique ajouté. | FUE-I ou FUE-0 API selon affordance réelle. |
| FUE-06 | Rejouer une requête de revue R11 avec auteur/signature client injectés. | Validation de schéma négative, audit inchangé ; capturer payload **sans donnée sensible** et réponse. | Test de sécurité API assisté, **pas** automatiquement FUE-G. |
| FUE-07 | Dans un labo aux règles positives **test-only**, examiner finding mais pas diagnostic puis demander attestation globale. | HTTP 409 et action bloquée ; audit/capture ; ne jamais injecter ces règles en prod. | FUE-I/G si UI disponible ; sinon FUE-0 laboratoire. |
| FUE-08 | Répéter deux fois la même confirmation R11, même cible/stage dans labo isolé. | Une seule trace de revue, deuxième tentative 409 ; audit DB. | API/interaction réelle ; ne pas déduire un résultat concurrency sans test dédié. |
| FUE-09 | Demander décision R13 sans attestation R11/R12 sur étude fictive. | Refus 409, aucune option enregistrée. | FUE-I/G si UI disponible, sinon FUE-0 API. |
| FUE-10 | Demander décision R14 + aperçu R15/PDF sans règles cliniques production approuvées. | Refus 409 ; `document_state=INCOMPLETE`, `clinical_validation_available=false`, jamais PDF final signé. | FUE-I/G si écran/end-to-end disponible. |

**Registre d'exécution à remplir par un humain pour chaque ID** : date/heure ; opérateur et rôle (test, sans identifiants sensibles) ; praticien superviseur ; `git_sha`/build hash ; configuration isolée ; dataset fictif ; niveau FUE-0/I/G réellement exécuté ; BEFORE / action / AFTER ; réponse et code API ; event ID et delta audit/DB ; attendu/observé ; anomalie classée BLOCKER/MAJOR/MINOR ; décision PASS/FAIL/NOT_RUN ; signature ou trace authentifiée de revue humaine. **Statut initial FUE01–FUE10 : NOT_RUN (0/10)**.

**Point d'arbitrage avant recette :** la matrice historique de dix tests techniques ne contient pas dix parcours UI démontrés. Une vérification API-only reste FUE-0 ; elle ne doit jamais être promue en FUE-I/G ni comptée comme expérience utilisateur cabinet sans interface effectivement manipulée. Vérifier l'existence des écrans et préparer le raccordement test avant de prétendre que les dix parcours sont pratiquables. Aucun jalon « 10/10 FUE cabinet » sans exécution distincte, preuves d'observation et acceptation humaine.

### 8. Audit de faisabilité FUE sur le code réel — 2026-11-04 (READ-ONLY)

**Périmètre inspecté au SHA `016ec06d` :**
- `frontend/src/features/ortho/components/ClinicalScientificStudio.tsx` : charge le snapshot R15 avec **GET** `/patients/{patient_id}/cephalo-clinical-studio`, permet de sélectionner les **quatre onglets R11/R12/R13/R14** et affiche blocages/« action praticien ». **Il n'exécute aucun POST R11–R14** ; ses boutons d'étape ne sont que des boutons de navigation.
- `frontend/src/features/ortho/CephaloWorkspace.tsx` : monte le Studio R15, sans câblage des commandes R11–R14 dans le flux inspecté.
- `frontend/src/features/ortho/components/Step4Documents.tsx` : propose **prévisualisation, brouillon et archivage PDF** ; l'affichage d'un brouillon n'est pas une validation clinique.
- `backend/routers/cephalo_clinical_studio.py` : expose réellement les routes authentifiées POST/GET de staging R11–R13, revue individuelle R11, attestation R11/R12, décision R13, décision R14 et revue des bloqueurs. **Routes API présentes ≠ parcours UI exécutable**.
- `frontend/scripts/capture-cephalo-r15-after.mjs` : capture navigateur sur **snapshot API simulé** (route fulfilled), ce qui démontre une surface visuelle testable mais pas une FUE-G réelle avec backend clinique et persistance.

| ID | Classification réalisable à ce stade sans nouveau câblage métier | Preuve non encore réalisée |
|---|---|---|
| FUE-01 | **FUE-0** (inspection registres/backend) | Contrôle du build exact chargé sur l'instance isolée |
| FUE-02 | **FUE-I candidat** (écran Studio sans étude, si reproduit en vrai local) | Capture de l'écran et trace GET live |
| FUE-03 | **Mixte** : API/test de texte legacy + visualisation de PDF/brouillon si l'environnement le permet | Non-promotion vérifiée et PDF `INCOMPLETE` observé sur backend réel |
| FUE-04 | **FUE-0 sécurité API** (croisement patient/analyse) | Réponse 404 et aucun accès/mutation |
| FUE-05 | **FUE-0 API** (POST staging, registre vide) | HTTP 409 et absence d'audit |
| FUE-06 | **FUE-0 contrat API** (payload auteur/signature interdits) | Refus de validation et aucun audit |
| FUE-07 | **FUE-0 API en labo test-only** (revue finding sans diagnostic puis attestation) | HTTP 409, audits inchangés hors scénario voulu |
| FUE-08 | **FUE-0 API en labo test-only** (double revue ciblée) | Une revue authentique, seconde 409 |
| FUE-09 | **FUE-0 API en labo test-only** (R13 sans attestation) | HTTP 409 et aucune option sélectionnée |
| FUE-10 | **Mixte** : FUE-0 refus R14 API + **FUE-I candidat** écran R15/PDF si UI live | HTTP 409, R15 `clinical_validation_available=false`, document `INCOMPLETE`, trace visuelle |

**Conclusion opérationnelle / STOP :** il n'existe pas dans les surfaces inspectées **dix parcours de validation cliniques pilotables par UI**. Il serait trompeur d'annoncer « 10/10 FUE-G cabinet ». Les dix tests backend préflight restent de bons *oracles de sûreté* mais ne couvrent pas l'observation humaine du parcours complet. **0/10 sessions cabinet exécutées ; aucune FUE-I/G revendiquée**. Les seuls candidats immédiats à la FUE visible sont 02 et l'affichage R15/PDF de 03/10, à condition de le constater avec backend réel sur cas fictif. Les autres se contrôlent d'abord par tests API en labo, comptés séparément. Ne pas développer les commandes cliniques UI ni les règles de production avant revue et autorisation humaine. Après avis clinique, décider séparément s'il faut câbler les commandes et refaire les vrais tests du parcours.

**Gates obligatoires avant tout « PASS cabinet »** : (1) build local exact identifié ; (2) cas et compte fictifs isolés ; (3) preuve BEFORE → ACTION → AFTER ; (4) réponse API et audit DB ; (5) classification honnête FUE-0/I/G ; (6) relecture du praticien humain ; (7) aucune PHI exposée. Ces contrôles ne créent aucune approbation réglementaire ni médicale.

**CHANTIER Digital Crown Céphalo V1 · LOT 1/4 R11–R14 NON CLOTURE · SOUS-LOT dossier des sources + 10 FUE préflight synthétiques · NEXT revue clinique indépendante + 10 FUE réelles · GOAL approbation scientifique traçable avant activation R15/PDF.**
