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

### 9. Concordance littérature primaire ↔ code et UI — audit Web du 2026-11-04

**Périmètre :** code au parent `e9f34347`, puis micro-correction non clinique de libellé au commit `41463003` ; évaluation documentaire. Les valeurs sources sont citées ci-dessous, mais la validation scientifique **source → construction précise → population → échelle → règle individuelle** n'est pas acquise. Aucun patient, FUE cabinet ou signature humaine.

| Source originale (preuve) | Attendu scientifique exact | Dans Digital Crown | Verdict / action |
|---|---|---|---|
| **Steiner 1953** ([éditeur DOI](https://doi.org/10.1016/0002-9416(53)90082-7)) ; contexte clinique [Steiner 1959](https://doi.org/10.1043/0003-3219(1959)029%3C0008:CICP%3E2.0.CO;2) et [1960](https://doi.org/10.1016/0002-9416(60)90145-7) | Valeurs classiques SNA 82°, SNB 80°, ANB 2°, U1/NA 22°/4 mm, L1/NB 25°/4 mm ; GoGn n'est **pas** GoMe. L1/GoGn 93° dans Steiner 1953, distinct d'IMPA Tweed. | `steiner_protocol_profile_v1.json` : ces chiffres dans un `STEINER_HISTORICAL_REFERENCE_SET_V1`, `classification_authority=false` ; `cephalo_steiner_geometry.py` impose constructions définies. | **Concordance des référentiels historiques principaux** ; pas de certification d'applicabilité universelle ni de transposition vers la méthode Go-Me. Le texte intégral 1959 et toute la construction anatomique doivent être relus avant validation clinique. |
| **McNamara 1984** ([texte intégral original Michigan, tableau I page 451](https://media.dent.umich.edu/labs/mcnamara/files/A%20method%20of%20cephalometric%20evaluation.pdf)) | Ann Arbor non traités **73 F, 38 H** ; Co-Gn F **120,2±5,3 mm**, H **134,3±6,8** ; Co-A F **91,0±4,3**, H **99,8±6,0** ; ANS-Me F **66,7±4,1**, H **74,6±5,0**. Moyenne âge F 26 ans 8 mois, H 30 ans 9 mois. L'article dit 8 % d'agrandissement **« whenever possible »**. | Six références `MEAN_SD` exactes dans `cephalo_norm_registry.py` avec sexe/taille/âge et `active_for_patient_classification=False`. `cephalo_mcnamara_geometry.py` mesure en **mm physiques calibrés**. | **6/6 exactes** par rapport au tableau I ; **HOLD comparaison individuelle** tant que provenance du facteur d'agrandissement 8 %, échelle et protocole ne sont pas réconciliés. Ne pas diviser d'office par 1,08. |
| **McNamara 13 facteurs** (composition méthode originale précédente) | La méthode comporte d'autres constructions (N-perp, axe facial, incisives, voies aériennes) qui demandent les repères précis. | `clinical_reference_profiles_v1.json` comporte **13 lignes de catalogue**, dont `M_FACIAL_AXIS_MCNAMARA_DEG_V1` = `IMPLEMENTATION_MISSING` et **4** = `BLOCKED_LANDMARK` (U1-A vertical, L1-A-Pog, pharynx supérieur/inférieur). L'une indique encore `contrat dédié à matérialiser`. | **ÉCART UI résolu sans activer de calculs :** titre `CephaloR23G4ReferencePanel.tsx` clarifié « 13 facteurs référencés (non tous calculables) ». L'ancien « 13 facteurs » ne prouvait pas 13 valeurs opérationnelles. Tests backend/visuels réels encore nécessaires. |
| **Ousehal, Lazrak, Chafii 2012** ([PubMed PMID 22236522](https://pubmed.ncbi.nlm.nih.gov/22236522/), [éditeur](https://www.sciencedirect.com/science/article/pii/S1761722711001136)) | Échantillon CCTD Casablanca, **71 patients** classe I non traités, **47 F / 24 H**, **19–27 ans** (moyenne 22,73±1,69) ; décalage sagittal moyen plus marqué et proclinaison de l'incisive inférieure ; auteurs refusent de généraliser sans autre recherche. | Référence bibliographique `MOROCCO_STEINER_OUSEHAL_2012` présente ; **aucun profil numérique marocain activé**. | **Concordance des métadonnées** ; tableau des moyennes détaillées non intégralement vérifié ici, **aucune « norme marocaine » patient** à activer. Aucun enfant ne peut être couvert par cet échantillon d'adultes. |
| **CRANIOM 2010/2011** ([partie 1](https://doi.org/10.1051/odfen/2010406), [partie 2 éditeur](https://www.cambridge.org/core/journals/journal-of-dentofacial-anomalies-and-orthodontics/article/abs/new-method-of-using-cephalometric-measurements-in-orthodontics-part-2-or-how-standard-deviations-can-be-the-practitioners-false-friends/4FE2C16785D64E24E83771B4462E74D4)) | Extrêmes d'inclinaison **L1 / plan mandibulaire de Downs 78–114°** et **U1 / Frankfort 97,5–130,1°** observés dans leur méthode ; **extrêmes descriptifs**, non règles de traitement ni percentiles. | `CRANIOM_L1_DOWNS_MP_EXTREMES_YOUNG_ADULT_V1` et `CRANIOM_U1_FH_EXTREMES_YOUNG_ADULT_V1` ont exactement ces bornes, `active_for_patient_classification=False`, `DOWNS_MP_TANGENT` requis pour L1. | **Concordance numérique** ; point anatomique Downs à vérifier séparément ; aucune classification ou indication extraction/absence d'extraction. |
| **Tweed 1946/1954/1969** ([FMA 1946](https://pubmed.ncbi.nlm.nih.gov/21022281/), [triangle 1969](https://pubmed.ncbi.nlm.nih.gov/5253959/)) | Triangle FMA/IMPA/FMIA dépend du plan de Francfort, du plan mandibulaire et de l'axe incisif choisis ; comparer des variantes exige l'identité des constructions. | `tweed_merrifield_protocol_profile_v1.json` signale **Po anatomique–Or / Go–Me**, et **refuse l'équivalence stricte** avec la construction historique via ear-rod ; valeurs historiques contextuelles seulement. | **Concordance de prudence** ; **HOLD normes Tweed appliquées à la variante DC** sans étude de parité sur mêmes clichés. |
| **Merrifield 1966** ([étude originale](https://doi.org/10.1016/0002-9416(66)90250-8), [texte intégral reproduit par Tweed Foundation](https://tweedortho.com/wp-content/uploads/2024/12/profile-line-aid.pdf)) | Ligne **Pog'–lèvre la plus antérieure**, angle Z avec Francfort ; contexte **80° chez l'adulte**, **78° à 11–15 ans**, sous critères esthétiques et dentosquelettiques précisés par l'auteur ; pas une norme universelle. | Références 80 et 78 présentes **display-only** ; `merrifield_z_angle_deg_v1` utilise bien Pog' + lèvre la plus antérieure, mais `_axis_angle_deg` retourne `min(angle,180-angle)`, donc **jamais plus de 90°**. | **ÉCART à examiner :** la formule géométrique efface la distinction des configurations obtuses ; l'angle *inférieur* historique doit être défini sans ambiguïté (orientation image/rayons, cas à >90°) avant toute correction de calcul. **Aucune auto-correction non revue**. |
| **Nguyen et al. 2024** ([texte ouvert](https://pmc.ncbi.nlm.nih.gov/articles/PMC11270148/)) | Les mesures pédiatriques dépendent notamment de l'âge, du sexe, du schéma de croissance et de la population ; revue hétérogène ≠ un tableau universel pour l'enfant. | Référence `PEDIATRIC_NORMS_REVIEW_NGUYEN_2024` documentaire, sans valeurs pédiatriques numériques ni activation. | **Concordance de prudence** ; pas de profil clinique pédiatrique scientifiquement autorisé par cette seule revue. |

**Mise en cohérence historique vs code actuel.** `backend/data/cephalometry/normative_profiles.yaml` est un **inventaire de migration LEGACY_UNVALIDATED**, non le référentiel certifié au HEAD. Il cite d'anciens intervalles `Step4Documents` (p. ex. SNA 76–88°, SNB 74–86° et ANB −2–6°) et d'anciennes références `cephalo_engine`. Au HEAD audité, `Step4Documents.tsx` ne stocke **plus ces plages** dans `ANGLE_CARDS` et affiche explicitement « **Valeur brute · aucune norme locale** » ; `cephalo_engine.py` dit ne plus fournir de z-scores, classification et traitement. **Ne pas confondre ces références historiques archivées avec la présentation clinique actuellement active.** Ne pas modifier l'inventaire ancien : le garder comme trace de migration.

**Décisions de mise en conformité applicative sur cette passe.**
1. **FAIT :** seul libellé frontend `McNamara — 13 facteurs référencés (non tous calculables)` corrigé pour correspondre au manifeste. Aucune formule, valeur source, règle diagnostique/thérapeutique, schéma, token de thème ni PDF clinique changés.
2. **HOLD-MCNAMARA-SCALE :** les six valeurs du tableau original sont correctes **mais pas comparables** aux mm patients tant que l'agrandissement n'est pas résolu par méthode et matériel réels.
3. **HOLD-Z-ORIENTATION :** valider par relecture clinique la définition de l'angle inférieur de Merrifield, construire cas géométriques de référence/contre-exemples et tester avant de modifier `_axis_angle_deg`.
4. **HOLD-MOROCCO-COVERAGE :** obtenir tableaux chiffrés intégraux + méthode + validation sur une cohorte pertinente avant toute activation d'un profil régional ; enfants hors domaine de la série Ousehal.
5. **HOLD-SCIENCE-AUTHORITY :** `source_locked` n'implique ni `patient_approved` ni une série FUE observée. Les métadonnées et l'écran scientifique restent descriptifs, `clinical_validation_available=false`, PDF final `INCOMPLETE`, 0/10 FUE humaines.

**GOAL :** les libellés et états reflètent fidèlement ce qui est réellement calculable ; les références numériques ne deviennent jamais des seuils de décision par simple rapprochement bibliographique.

### 10. Arbitrage ciblé des PDF primaires — McNamara 8 % / Merrifield angle Z (2026-11-04)

**Preuves primaires relues visuellement :**
- [McNamara, Am J Orthod 1984, p.451/Table I, PDF Michigan](https://media.dent.umich.edu/labs/mcnamara/files/A%20method%20of%20cephalometric%20evaluation.pdf) : six couples **moyenne ± SD** Co–Gn, Co–A, ANS–Me (F/H) concordants avec le registre. Le texte mentionne 8 % de magnification pour les mesures **« whenever possible »** et une synthèse historique mélangeant Bolton, Burlington et Ann Arbor. Les tableaux de valeurs linéaires historiques ne sont **pas en mm physiques directement comparables**, et l'article ne prouve pas une conversion uniforme `/1.08` applicable au cliché réel traité par DC. **Décision : HOLD-MCNAMARA-SCALE confirmé** ; ne pas transformer en norme, z-score ou couleur diagnostique sans description étalonnage par acquisition, construction, population, sexe/âge et autorité clinicien.
- [Merrifield, Am J Orthod 1966, p.811–812, Fig.5, PDF Tweed Foundation](https://tweedortho.com/wp-content/uploads/2024/12/profile-line-aid.pdf) : définit l'**angle inférieur** entre Frankfort et profil Pog'–lèvre la plus proéminente. Fig.5 représente le secteur inférieur depuis le rayon Frankfort postérieur jusqu'à la ligne profil vers le menton. Le tableau II des **40 sujets normaux non orthodontiques** contient Z moyen 81,4°, min–max **71–89°** : aucune valeur >90° ne fait partie de cet échantillon ; l'extrapolation au-delà est un contre-exemple mathématique, **pas une validation clinique d'un nouveau seuil**.

**Contre-exemple géométrique synthétique, sans patient (coordonnées de laboratoire) :** Francfort Po=(0,0), Or=(10,0), Pog'=(2,20).
| Lèvre la plus proéminente | Angle inférieur candidat : rayon Or→Po vs rayon lèvre→Pog' | Calcul V1 actuel `merrifield_z_angle_deg_v1` |
|---|---:|---:|
| Ls=(7,10), Li=(6,12) | **63,4349°** | **63,4349°** |
| Ls=(-3,10), Li=(-4,12) | **116,5651°** | **63,4349°** |

Le calcul V1 applique `min(angle, 180-angle)` sur deux **axes non orientés**, effaçant le choix du secteur inférieur historique ; l'application **ne peut donc pas distinguer ces deux configurations synthétiques**. C'est une **collision démontrée de géométrie**, pas une preuve qu'un patient donné a une valeur fausse. L'orientation anatomique Po→Or et le choix lèvre/Pog' doivent faire l'objet d'une revue sur tracés réels anonymisés et images miroir/rotations avant de certifier une correction.

**Preuve de code ajoutée sans modifier la géométrie :** `backend/tests/test_cephalo_r6_tweed_merrifield.py::test_merrifield_v1_folds_supplementary_inferior_angles_audit_only` reproduit les deux sorties V1 identiques et le secteur inférieur candidat distinct. Le test est un **oracle de collision**, **pas un nouveau calcul clinique certifié**.

**Décision de versionnement et de sécurité :** ne **pas** changer en place `merrifield_z_angle_deg_v1` : la fonction est référencée par les méthodes de preuve persistée `MERRIFIELD_Z_ANGLE_DEG_V1` **et** `MERRIFIELD_Z_CANONICAL_DEG_V2`; un changement silencieux altérerait la reproductibilité des analyses existantes. **HOLD-Z-ORIENTATION maintenu**, étude de cas de parité anatomique supervisée requise, puis seulement une nouvelle méthode/identité versionnée avec tests de rétrocompatibilité et décision migration. En attendant, pas d'interprétation clinique d'angle Z et aucune norme Merrifield appliquée au patient.

**Gates restant pour lever les HOLD :**
1. McNamara : relever modalité / calibration / grossissement source et patient, identité exacte des points, population et règle d'équivalence vérifiée ; produire cas-oracles et arbitrage praticien.
2. Merrifield : définir convention orientée et vérification des positions sur tracés cliniques anonymisés avec consentement, comparer au tracé manuel historique, valider l'orientation miroir/rotation et la variante Frankfort ; puis migration de méthode versionnée.
3. Documenter FUE-I/G sur instance cabinet isolée, praticien et traces UI/API/DB. **FUE réelles : 0/10 ; aucune approbation médicale ni signature inventée.**

### 11. Gate humain opérationnel — décision McNamara / Z / FUE (2026-11-04, 0 signature)

**Objet de cette feuille :** obtenir une décision clinique humaine explicite, fondée sur des traces reproductibles ; ne pas confondre le **154/154 PASS CI** ([run #41806570624](https://github.com/hraaaaf/Digital_crown/actions/runs/41806570624)) avec un verdict scientifique. Aucune autorité médicale ne peut être auto-attestée par le code.

| Gate | Pièces obligatoires à produire avant arbitrage | Décision actuelle |
|---|---|---|
| **M1 — McNamara 1984, tableau I** | Original Table I et clause d'agrandissement « whenever possible » ; fiche de l'acquisition pour **chaque** étude : modalité/centre, pixel spacing ou étalon réel et source de calibration, agrandissement connu ou **INCONNU**, identité des points Co/A/Gn/ANS/Me et version géométrique, âge/sexe et population ; comparaison manuelle sur étude *consentie et anonymisée* avec incertitude métrologique et stratégie de non-comparabilité. Ne jamais inférer `/1.08` sans preuve que les deux échelles correspondent. | **HOLD-MCNAMARA-SCALE** : afficher la mesure physique brute ; aucune comparaison normative individuelle. |
| **Z1 — Merrifield 1966** | Fig. 5 du texte original ; convention de secteur **inférieur** définie par des rayons orientés et non des axes non orientés ; tracé manuel indépendant / coordonnées repères Pog' et lèvre la plus proéminente et FH Po–Or ; au minimum : profil courant, profil fortement rétro-positionné/secteur >90° synthétique, lèvres inversées, miroir horizontal et rotation ; résultat attendu du tracé indépendant **défini avant** confrontation au logiciel ; conformité des identités de repères. | **HOLD-Z-ORIENTATION** : collision synthétique V1 reproduite par la CI ; test GREEN prouve l'anomalie, **pas** la justesse clinique d'une formule de remplacement. |
| **V1 — Migration/identité** | Si le gate Z1 conclut à une modification : nouvelle identité méthode et version du calcul ; fixture anciennes analyses et reproductibilité V1/V2 ; scénario conservation/affichage historique ; révision clinique signée, non-réécriture des preuves de mesures déjà archivées. | **NOT_STARTED** : aucune formule V1/V2 remplacée ni migration permise. |
| **C1 — Séance cabinet** | Build local SHA/revision, utilisateur test et étude fictive isolée, 10 fiches FUE-01…10 avec captures BEFORE/ACTION/AFTER, réponse API, événements d'audit DB et retours opérateur. Classer explicitement **FUE-0 API**, **FUE-I interaction écran**, **FUE-G parcours complet**. | **0/10 FUE cabinet**, aucun PASS humain. |

**Trame de décision à compléter uniquement par les personnes présentes :** `gate_id` ; source/article et page/figure ; version code et modèle ; date et équipement ; jeux de données/consentement et anonymisation ; points et constructions audités ; valeur manuelle observée ; valeur logicielle ; unité/échelle et incertitude ; anomalies ; décision `APPROVED | REJECTED | INSUFFICIENT_EVIDENCE` ; justification ; rôle et identité du praticien relecteur ; date et trace authentifiée ; relecture indépendante si nécessaire. Tous ces champs sont **NON RENSEIGNÉS** à cette date.

**Critères de STOP automatiques :** magnification non documentée, ratio non fiable, identité landmark incertaine, source non appariée, erreur géométrique sans solution testée, données cliniques non consenties, défaut d'audit d'auteur, ou absence de signature réelle. **Aucune tolérance chiffrée arbitraire** ; seuils de conformité/tolérances à justifier par méthode et appareil et accepter séparément. Pas de production `clinical_validation_available=true`, pas de bascule `INCOMPLETE`→final PDF, pas d'attribution artificielle « 10/10 FUE ».

**Arbitrage suivant et seulement ensuite :** choisir avec le praticien si Z devient une méthode **nouvellement versionnée** et si McNamara exige des valeurs de référence compatibles avec l'échelle ; chiffrer la marge d'erreur et l'impact rétrospectif. Le test unitaire collision est déjà GREEN, il n'apporte pas cet accord.

### 12. Source indépendante candidate pour la parité anatomique — audit d'éligibilité Aariz/ISBI (2026-11-04)

**Découverte à partir de travaux externes, pas d'un test Digital Crown réalisé** : le jeu de données **Aariz** de Khalid et al., [*Scientific Data* 2025, 12:1336](https://doi.org/10.1038/s41597-025-05542-3), [archive officielle Figshare DOI 10.6084/m9.figshare.27986417.v1](https://doi.org/10.6084/m9.figshare.27986417.v1), [métadonnées API Figshare](https://api.figshare.com/v2/articles/27986417), réunit 1 000 télécrânes anonymisés, 29 repères expert-annotés et plusieurs appareils (7). Les JSON de repères **junior/senior**, une référence moyenne et le CSV **calibration par appareil/image** sont documentés dans l'article ; le [code de lecture des auteurs](https://github.com/manwaarkhd/aariz/blob/main/dataset.py) précise le chargement des deux jeux de repères. La source officielle indique **CC BY 4.0**, une archive unique `Aariz.zip` **2 098 209 792 octets** (file ID `51041642`, MD5 `e0bd645bca6759abdae4f199d841bda6`). **Images/annotations non téléchargées ni redistribuées durant cette passe** : environnement actuel incapable de résoudre les hôtes Figshare, et archive ≈2 Go. Donc **zéro cas Aariz calculé ou vérifié dans Digital Crown**.

**Correspondance préliminaire des identités :** [config.py des auteurs, dictionnaire des 29 landmarks](https://github.com/manwaarkhd/aariz/blob/main/config.py) confirme les labels de la source ; cela **ne prouve pas l'identité géométrique spécifique** des repères `*_anatomic` de Digital Crown.

| Contrôle | Landmarks Aariz présents selon la source | Identités DC exigées dans le code au HEAD | Verdict de faisabilité |
|---|---|---|---|
| **Merrifield Z (candidat)** | `Po`, `Or`, `Pog'`, `Ls`, `Li` | `Po_anatomic`, `Or`, `Pog_soft`, `Ls_soft`, `Li_soft` pour `MERRIFIELD_Z_CANONICAL_DEG_V2` ; le V1 utilise `Po` | **Présence 5/5 source ; correspondance anatomique et orientation INSUFFICIENT_EVIDENCE** : pas de substitution automatique `Po`→`Po_anatomic` ni `Pog'`→`Pog_soft` sans revue du tracé individuel. |
| **McNamara Co–A (candidat)** | `Co`, `A` | `Co_anatomic`, `A` | **2/2 labels disponibles**, identité exacte `Co_anatomic` à confirmer sur image et définition ; besoin de mm/px natifs + preuve de calibration. |
| **McNamara Co–Gn (candidat)** | `Co`, `Gn` | `Co_anatomic`, `Gn_anatomic` | **2/2 labels disponibles**, les **deux** alias anatomiques sont à vérifier sur le tracé et le contrat DC. |
| **McNamara ANS–Me (candidat)** | `ANS`, `Me` | `ANS`, `Me` | **2/2 labels disponibles**, distance brute calibrée testable, **sans** appliquer les moyennes Ann Arbor (agrandissement/source non équivalents). |
| **ISBI 2015 (repli limité)** | 400 clichés, 19 landmarks incluant `Po`, `Or`, `Pog'`, `Ls`, `Li`, `ANS`, `Me`, **pas Co** ; échelle nominale 0,1 mm/px | Z candidat + ANS–Me uniquement | [Étude source de 2016](https://www.nature.com/articles/srep33581) ; **impossible d'en tirer Co–A/Co–Gn** sans inventer le condylion. |

**Séquence minimale d'une future passe de parité sur données publiques (NON EXÉCUTÉE) :**
1. Récupérer en environnement local isolé l'archive officielle et contrôler le MD5 fourni (pas d'images dans GitHub/Notion). Vérifier le CSV de calibration **pour chaque ID d'image** et que les coordonnées JSON correspondent à la taille/orientation du cliché **natif**.
2. Choisir des clichés dont les cinq points Z et les cinq points Co/A/Gn/ANS/Me sont réellement disponibles dans le JSON, comparer indépendamment les annotations expert et l'image, documenter les écarts inter-lecteurs et vérifier les définitions `Co_anatomic`, `Gn_anatomic`, `Po_anatomic` et `Pog_soft` avant toute projection dans DC.
3. Obtenir **un tracé Z avec valeur mesurée manuellement** et protocole de rayons (pas uniquement les coordonnées des landmarks). Comparer en aveugle la mesure DC et le tracé indépendant, en incluant cas de rotation/miroir, lèvre supérieure/inférieure, et profil obtus si présent. Consigner les échecs et cas non interprétables **sans conversion en seuil médical**.
4. Vérifier les distances physiques `Co–A`, `Co–Gn`, `ANS–Me` avec la calibration validée et l'incertitude des points. **Ne jamais comparer automatiquement** ces mm à la référence McNamara 1984 : publication 8 % « whenever possible », populations/matériel différents.
5. Ne traiter comme FUE-G de cabinet que les parcours observés sur Digital Crown **local authentifié** avec trace opérateur/UI/API/DB ; une évaluation externe Aariz constitue un **benchmark R&D, pas une FUE de cabinet ni une signature praticien**.

**État réel de la passe :** source et format officiels vérifiés, compatibilité des noms de repères établie comme **candidate**, **0 image Aariz chargée, 0 valeur Z manuelle extraite, 0 comparaison de mesures DC sur cliché public, 0/10 FUE en cabinet**. McNamara-SCALE et Merrifield-Z restent **HOLD**. Une archive de recherche publique ne justifie pas de libérer R15/PDF. Aucun runtime médical, règle, référentiel ni interface modifié.

### 13. Premier pilote réel d'annotations Aariz — 21 cas multi-appareils (2026-11-04 ; HORS RUNTIME / clinique HOLD)

**Différence avec §12 :** une archive ZIP Figshare complète n'est toujours **pas** récupérable depuis le conteneur (DNS `api.figshare.com` / `ndownloader.figshare.com` / `github.com` en erreur), mais une **copie publique tierce des fichiers d'annotations** a été retrouvée et lue via le connecteur GitHub : [`Annagdy/CNN-CVM`, commit immuable `ea6678cd8ba62b615d909ecb1065023ea73eb827`](https://github.com/Annagdy/CNN-CVM/tree/ea6678cd8ba62b615d909ecb1065023ea73eb827/Aariz_dataset/Aariz). Le dépôt comprend les 1000 lignes du [CSV métadonnées](https://github.com/Annagdy/CNN-CVM/blob/ea6678cd8ba62b615d909ecb1065023ea73eb827/Aariz_dataset/Aariz/cephalogram_machine_mappings.csv) et les annotations JSON senior/junior, mais **l'équivalence binaire au ZIP Figshare officiel (MD5 global) n'est pas vérifiée** ; l'origine exacte des fichiers et les transformations éventuelles des images devront être confirmées. Ceci est une **étude de faisabilité empirique d'une copie publique**, pas un nouvel oracle clinique certifié.

**Prélèvement reproductible, sans identifiants de dossiers dans la PR :**
- Filtrer le CSV `mode=Test` (150 lignes), répartir par la colonne `machine` (sept machines), trier les `cephalogram_id` lexicographiquement **dans chaque machine**, prendre **les 3 premiers par machine** ; total **21 études**, dont les identifiants publics ne sont **pas copiés** dans ce dossier.
- À chaque étude : lire `test/Annotations/Cephalometric Landmarks/{Junior Orthodontists,Senior Orthodontists}/<id>.json` au commit ci-dessus. **42 fichiers JSON effectivement chargés ; 29/29 symboles uniques et correspondance `ceph_id` vérifiés par fichier**. Ce sont des **moyennes d'annotations des deux groupes** publiées par les auteurs, pas les traces brutes de quatre lecteurs individuels. Pour chaque symbole, calculer `ceil((junior_x + senior_x)/2)` et `ceil((junior_y + senior_y)/2)`, comme le [lecteur des auteurs](https://github.com/manwaarkhd/aariz/blob/main/dataset.py).
- McNamara : appliquer **uniquement à titre exploratoire** la distance euclidienne `hypot(dx,dy)` entre Co–A, Co–Gn, ANS–Me sur ces points moyens, puis multiplier par `pixel_size` du CSV **sans appeler ces résultats des mm physiques certifiés** (calibration de l'export non démontrée).
- Merrifield : prendre la lèvre la plus antérieure selon la projection sur `Po→Or` (convention du V1 DC) ; calculer d'une part l'angle aigu sur **axes non orientés** `min(acos(dot),180-acos(dot))` fidèle à `merrifield_z_angle_deg_v1`, et d'autre part le **secteur inférieur candidat orienté** entre `Or→Po` et `lèvre→Pog'`**. Calcul reproductible indépendant **en JavaScript**, non invocation de l'API ou de la fonction Python Digital Crown ; pas de tracé manuel, pas d'image affichée.

**Résultats effectivement obtenus, échantillon non aléatoire n=21 :**

| Groupe appareil | Cas | Co–Gn médian *après facteur CSV*, unité nominale mm — **NON CERTIFIÉE** |
|---|---:|---:|
| ART Plus | 3 | 118,33 |
| Hyperion X5 | 3 | 37,71 |
| ProMax 2D | 3 | 113,14 |
| ProMax with ProTouch | 3 | 114,84 |
| Rotograph EVO | 3 | 188,69 |
| Smart3D | 3 | 43,84 |
| Veraviewepocs 2D | 3 | 69,40 |

- **Angle Z : 21/21** jeux de coordonnées moyennes donnent la même sortie pour la formule aiguë V1 reproduite et le secteur inférieur candidat orienté, à la précision du calcul double ; plage **56,326° à 85,039°**. **18/21** retiennent Ls, **3/21** Li. Aucun de ces 21 cas ne teste le secteur >90° où l'**oracle synthétique R6** révèle la collision ; **on ne peut donc pas lever HOLD-Z-ORIENTATION**. Les différences entre les deux fichiers de groupes d'annotations ne représentent **pas** une étude de reproductibilité clinique indépendante.
- **McNamara :** les facteurs nominaux `pixel_size` du CSV donnent des longueurs Co–Gn extrêmement hétérogènes selon l'appareil, y compris des ordres de grandeur incompatibles avec une comparaison normative directe. **Le résultat ne prouve pas que le CSV est faux** : image exportée/éventuellement redimensionnée, association de calibration et définition des points/âge/cohorte sont non vérifiés. **STOP : ne pas afficher ces nombres comme dimensions physiques interprétables ; ne surtout pas les confronter aux moyennes Ann Arbor 1984.**
- **Sensibilité au groupe annotateur :** sur les sept premières études exploratoires, les différences absolues junior–senior calculées ont atteint **8,539** en unité nominale mm pour Co–Gn, et **3,979°** pour l'angle Z ; ce sont des **différences de coordonnées des deux jeux de groupes**, pas des erreurs par rapport à une vérité clinique ni un critère PASS/FAIL. Les 21 cas ont une répartition d'âge/sexe inconnue dans les données exploitées ici ; aucune généralisation.

**Chaîne de confiance et verdict par niveau :**

| Couche | État |
|---|---|
| JSON externes + CSV de la copie tierce | **TECHNICALLY_READ / provenance source Figshare NOT VERIFIED** ; 42/42 fichiers chargés, 29/29 points structurés, 7 appareils |
| Cohérence de calcul hors application, géométrie Z pour ces 21 cas | **TECHNICALLY_CONCORDANT in-sample** : 21/21, mais seulement angles <90° ; **HOLD clinique** |
| Échelle native de chaque radio / magnification / recadrage / alias `Po_anatomic`, `Co_anatomic`, `Gn_anatomic` | **NOT_EVALUABLE** sans image native, métadonnées DICOM/export et revue anatomique |
| Calcul et tracé réel dans Digital Crown UI/API/DB/PDF | **NOT_RUN** ; aucune analyse patient dans le runtime ; aucune importation de coordonnées réelles dans l'application |
| Tracé indépendant praticien / consensus clinique | **NOT_RUN / HUMAN_GATE_REQUIRED** ; aucun angle Z manuel indépendant validé, aucune signature |
| FUE cabinet | **0/10 observées** |

**Décision actionnable :** source R&D désormais **partiellement échantillonnée en réel**, mais l'écart métrologique fait de la vérification de l'échelle par machine et image **le premier blocage** à résoudre avant tout test McNamara en mm. Obtenir un export natif non modifié (sans dépôt public), contrôler ratio pixel / résolution / éventuel redimensionnement et identités anatomiques sur image, puis effectuer une mesure manuelle indépendante sur un jeu de cas consentis ; seulement ensuite exécuter le véritable runtime Digital Crown en instance locale isolée et la batterie de 10 FUE. **HOLD-MCNAMARA-SCALE et HOLD-Z-ORIENTATION restent inchangés ; pas d'activation médicale ni de R15/PDF.**

**CHANTIER Digital Crown Céphalo V1 · LOT 1/4 R11–R14 NON CLOTURE · SOUS-LOT dossier des sources + 10 FUE préflight synthétiques · NEXT revue clinique indépendante + 10 FUE réelles · GOAL approbation scientifique traçable avant activation R15/PDF.**

### 14. Concordance calibration Aariz source primaire ↔ CSV miroir — 2026-11-04 (AUDIT READ-ONLY ; HOLD)

**Question contrôlée :** la valeur de `pixel_size` issue du miroir public reflète-t-elle sans contradiction la résolution rapportée dans l'article original ? Cette vérification documentaire **ne vérifie pas l'échelle physique effective d'une image native**, l'identité anatomique des repères, ni la validité de la comparaison McNamara. `HOLD-MCNAMARA-SCALE` maintenu.

**Sources et version de confiance distinctes :**
- **Publication primaire** Khalid et al., *Scientific Data* 12:1336 (31 juillet 2025), [article](https://doi.org/10.1038/s41597-025-05542-3), [texte primaire archivé PMC et tableau 2](https://pmc.ncbi.nlm.nih.gov/articles/PMC12313948/) : colonne *Resolution (millimetres/pixel)*, effectifs par appareil. Les [définitions anatomiques au tableau 4](https://pmc.ncbi.nlm.nih.gov/articles/PMC12313948/) définissent Po comme porion anatomique (conduit auditif externe), Co comme condylion postéro-supérieur et Gn comme point mandibulaire entre Pog et Me ; ce vocabulaire **ne certifie pas** la parité des points réellement marqués avec les contrats DC.
- **Source secondaire non canonique de données** : [copie publique Annagdy/CNN-CVM, commit immuable `ea6678cd8ba62b615d909ecb1065023ea73eb827`](https://github.com/Annagdy/CNN-CVM/blob/ea6678cd8ba62b615d909ecb1065023ea73eb827/Aariz_dataset/Aariz/cephalogram_machine_mappings.csv), blob CSV SHA `6f73da5d573715dfcfc683461d197ac81c4fac43`. CSV complet relu par le connecteur GitHub puis compté par appareil/mode/résolution : **1 000 lignes, 1 000 IDs distincts, 0 résolution <=0 ou non numérique, 0 mode hors Train/Valid/Test**. Ce contrôle confirme le contenu du miroir au commit déclaré, **pas** son équivalence bit-à-bit à l'archive [Figshare officielle](https://doi.org/10.6084/m9.figshare.27986417.v1).

| Machine | N primaire | N CSV miroir | mm/px primaire (Table 2) | mm/px CSV miroir | Concordance documentaire |
|---|---:|---:|---:|---:|---|
| ART Plus | 366 | 366 | 0.100 | 0.100 | OUI |
| Veraviewepocs 2D | 177 | 177 | 0.144 | 0.144 | OUI |
| Smart3D | 59 | 59 | 0.100 | 0.100 | OUI |
| **ProMax 2D** | **41** | **41** | **1.139** | **0.139** | **NON — conflit 8,19×** |
| ProMax with ProTouch | 135 | 135 | 0.139 | 0.139 | OUI |
| Hyperion X5 | 143 | 143 | 0.089 | 0.089 | OUI |
| Rotograph EVO | 79 | 79 | 0.135 | 0.135 | OUI |

**Verdict reproductible :** **7/7 effectifs concordants ; 6/7 résolutions nominales concordantes ; 1/7 SOURCE_CONFLICT**. Pour les **41 études ProMax 2D**, le ratio numérique `1.139 / 0.139 = 8.1942446...` signale une divergence qui produirait le même ratio de différence dans n'importe quelle distance convertie depuis des pixels si on appliquait naïvement ces deux facteurs alternatifs. **La publication peut comporter une coquille, le CSV du miroir peut différer de l'original, ou la documentation peut mélanger conventions : aucune de ces explications n'est démontrée.** Ne pas transformer la vraisemblance en correction. Aucune longueur nominale du §13 (dont Co–Gn ProMax 2D) ne devient une dimension physique certifiée.

**Accès aux images / STOP instrumenté :** la copie GitHub contient au moins un fichier d'image de test [PNG figé](https://github.com/Annagdy/CNN-CVM/blob/ea6678cd8ba62b615d909ecb1065023ea73eb827/Aariz_dataset/Aariz/test/Cephalograms/cks2ip8fp29yl0yuf6ry9266i.png) annoncé **4,94 Mo** par l'interface du dépôt ; son blob SHA est `c61d32766cee00dc6cfed904114b309c51c3fd49`. La lecture binaire via connecteur n'a pas fourni de pixels décodables et le conteneur isolé échoue à résoudre `raw.githubusercontent.com` en DNS ; aucune largeur/hauteur native, ratio, `PixelSpacing` DICOM, transformation, miroir/rotation ou qualité anatomique n'a donc été **mesurée**. Le GitHub PNG de référence n'est pas une preuve d'un original DICOM ni une archive officielle Figshare validée. Un navigateur auxiliaire n'a pas pu démarrer faute de crédits de ce service ; **pas de test visuel simulé**. La source [`dataset.py` de l'auteur](https://github.com/manwaarkhd/aariz/blob/main/dataset.py) charge les images par `cv2.imread`, mais cela ne prouve pas leur absence de redimensionnement lors d'une étape antérieure.

**Contrôles nécessaires pour lever le seul conflit documentaire :** (1) extraire **en local isolé** le CSV du ZIP Figshare officiel après intégrité/hash vérifié ; (2) comparer octet à octet ou contenu par ID au CSV du miroir ; (3) contacter les auteurs/consulter un erratum pour la valeur ProMax 2D 1.139/0.139 ; (4) journaliser la source de vérité corrigée et versionnée sans toucher aux données persistées V1/V2. **Pour lever le HOLD clinique**, il faudra **en plus** chaque image native/échelle DICOM ou référence validée, appariement des repères Po/Co/Gn et tracé Z indépendant réellement relu, mesure aveugle sur Digital Crown runtime, puis 10 FUE cabinet avec signature humaine. Ces étapes supplémentaires restent `NOT_RUN`.

**Sécurité/décision inchangée :** aucune formule, registre, norme, seuil, patient, modèle, interface clinique, DB, migration ou PDF activé ; `clinical_validation_available=false`, PDF `INCOMPLETE`, **0/10 FUE cabinet**, PR Draft, pas de merge/déploiement. **Classification : MAJOR conflit de source empêchant d'affirmer toute conversion McNamara ProMax 2D ; pas un bug de calcul DC démontré.** Aucun seuil clinique 2 mm ni facteur d'agrandissement universel activé. Données tierces non redistribuées.

**CHANTIER Digital Crown Céphalo V1 · LOT 1/4 R11–R14 OUVERT · SOUS-LOT audit scientifique Aariz source ↔ miroir ProMax 2D · NEXT vérifier ZIP officiel/erratum puis image native et revue humaine, FUE cabinet · GOAL calibration correcte avant R15/PDF.**

### 15. Contre-expertise documentaire selon la fiche source Orthodontiste v1.0.0 — 2026-11-04 (PAS UNE INVOCATION D'AGENT ; clinique HOLD)

**Provenance et limites d'attribution.** L'utilisateur a demandé l'avis de « notre agent orthodontiste dans les sources ». Fiche fournie en source du projet `Orthodontiste.md.txt`, frontmatter `name: orthodontiste`, version 1.0.0 du 2026-11-04, profil `read-only` / `CANDIDATE / HUMAN CLINICAL APPROVAL REQUIRED` ; ses exigences ORTHO-07/09/10/11/12/13/14/15/18/21/22/36/37/39/40 ont été **appliquées ici comme grille documentaire par l'assistant coordinateur**. Son chemin annoncé `.claude/agents/Orthodontiste.md` **n'a pas été trouvé** ni sur la branche de PR #1208 ni sur le défaut du dépôt via GitHub. Aucun moteur de délégation d'agent disponible dans cette conversation ; l'annuaire des agents Notion est soumis à une offre Business ; **l'agent Orthodontiste n'a PAS été exécuté séparément**, et ceci **n'est ni un avis orthodontique humain, ni une seconde lecture indépendante, ni une signature**. La fiche source de Project est une instruction candidate, pas une pièce prouvant l'état du code à ce HEAD.

**Périmètre audité :** absence de clichés natifs/overlays et de consultation clinique ; études Aariz de §13–14 (21 coordonnées d'annotations tierces, 7 appareils, aucun DICOM natif) ; registre et contrats `docs/CEPHALO_DIAGNOSTIC_SPEC.md`, `docs/SRPOSE38_LANDMARK_CONTRACT.md`, original Aariz [Khalid et al. 2025, tableaux 2 et 4](https://pmc.ncbi.nlm.nih.gov/articles/PMC12313948/), travaux primaires [McNamara 1984](https://media.dent.umich.edu/labs/mcnamara/files/A%20method%20of%20cephalometric%20evaluation.pdf) et Merrifield 1966 déjà référencés en §9–11. Le contrat SRPose38 est techniquement explicite : index 3 = `Po`, index 8 = `Gn`, index 24 = `Co`, index 13/12 = lèvres inférieure/supérieure, index 15 = `Pog_soft` ; ce mapping de **noms** n'établit pas l'identité des points placés sur une image Aariz particulière.

| Couche de contrôle issue de la grille Orthodontiste | Verdict de cette revue documentaire | Pourquoi / condition de levée |
|---|---|---|
| IMAGE (ORTHO-07–09, 14) | **NOT_EVALUABLE** | Original natif non affiché ni calibré : cadrage, ratio, latéralité, orientation/miroir, export/redimensionnement, Pixel Spacing/Imager Pixel Spacing non contrôlés. Fournir image non altérée et traçabilité d'acquisition dans environnement autorisé. |
| LANDMARKS (ORTHO-10–13) | **NOT_EVALUABLE** | `Po` Aariz est défini anatomique dans l'article, mais parité avec `Po_anatomic` DC non prouvée cas par cas ; `Co`→`Co_anatomic` et `Gn`→`Gn_anatomic` sont **hypothèses de mapping**, pas validations ; `Pog'`→`Pog_soft`, `Ls`/`Li`→`Ls_soft`/`Li_soft` requièrent le même contrôle. Contrat `Po` modèle SRPose38 est explicitement `CERTIFIED_WITH_CAUTION` ; ne pas confondre porion anatomique et ear-rod. Obtenir overlay natif + double repérage indépendant et convention d'étude. |
| GEOMETRY (ORTHO-15, 22) | **EVIDENCE_CONFLICT / HOLD-Z-ORIENTATION** | Test R6 sur cas synthétique montre que V1 `merrifield_z_angle_deg_v1` rabat 63,4349° et 116,5651° vers 63,4349°. Concordance 21/21 cas Aariz externes **strictement <90°** ne discrimine pas ces secteurs ; pas d'oracle humain Z. Revoir fig. originale, deux rayons orientés, cas miroir/rotation et valeur manuelle indépendante avant *nouvelle méthode versionnée*. Aucun écrasement V1/V2. |
| MEASUREMENTS (ORTHO-09, 18, 21, 36) | **EVIDENCE_CONFLICT / HOLD-MCNAMARA-SCALE** | Co–A, Co–Gn, ANS–Me ont des coordonnées candidates, mais le tableau 2 de l'article dit ProMax 2D `1.139` mm/px contre `0.139` dans le miroir (41 cas ; facteur **8.194×**). Échelle image native, magnification, incidence, repère, population et comparaison Ann Arbor 8 % non vérifiés. Les longueurs pixelées exploratoires ne sont **PAS** des mm physiques normatifs. Demander CSV ZIP officiel/erratum et vérification métrologique par étude. |
| NORMS / INTERPRETATION (ORTHO-24, 36, 40) | **BLOCKED pour classification clinique** | Aucune norme populationnelle/âge/indication approuvée ; `active_for_patient_classification=false`. Une exactitude numérique n'autorise pas interprétation diagnostique. |
| CLINICAL (ORTHO-01–06, 25–33, 40) | **HUMAN_GATE_REQUIRED** | Aucun patient/âge/denture/examen/consentement ni relecteur orthodontiste indépendant à ce dossier ; 0 accord humain. Pas de diagnostic, plan ou décision thérapeutique. |
| REPORT / UI/API/DB/PDF (ORTHO-35, 38, 39) | **BLOCKED pour finalisation** | `clinical_validation_available=false`, PDF `INCOMPLETE`, pas de tracé public évalué de bout en bout dans le runtime, ni d'acceptation cabinet. |

**VERDICT GLOBAL : BLOCKED (validation anatomique clinique), distinct de FUE-0 documentaire réalisé.** Les noms de repères et structures JSON sont **documentés**, sans localisation visuelle certifiée ; le calcul angulaire en repère non déformé peut être indépendant d'une échelle uniforme en mm, mais **pas** des erreurs de ratio, symétrie/orientation ou convention de secteur. L'absence de mm étalonnés bloque les **distances**, pas arbitrairement toute géométrie angulaire. Aucune « validation orthodontiste » ne peut être inférée de l'application de cette checklist.

**Sévérités ciblées / critères de levée :**
1. **BLOCKER-A (Po/Co/Gn/Pog')** : annotateurs et modèle peuvent employer des conventions différentes malgré les labels communs. Revue image originale + overlay zoomable, source du landmark (anatomique vs construit/ear-rod), double lecture manuelle, version d'analyse et arbitrage documentés ; en attendant, toutes les mesures **dépendantes** de ces repères restent non certifiées.
2. **BLOCKER-Z (Merrifield)** : demander à un orthodontiste habilité un traçage indépendant de l'angle Z inférieur et du choix de lèvre, sur cas normal + obtus + miroir/rotation, sans leur communiquer la réponse du code, puis comparer les constructions, pas seulement le chiffre. Ne pas corriger par `min(angle,180-angle)`.
3. **BLOCKER-MM (McNamara)** : obtenir CSV/ZIP officiels et faire arbitrer 1.139 vs 0.139 mm/px ; ensuite contrôler image native/transformations et marge d'incertitude. **Interdire** comparaison individuelle avec tableaux historiques 1984 jusqu'à normalisation de technique et validation populationnelle.
4. **MAJOR-REPRO** : les deux fichiers `Junior Orthodontists` et `Senior Orthodontists` sont des moyennes de groupes, non quatre tracés indépendants ; 21 cas choisis non aléatoirement, aucun >90°, aucune erreur clinique par mesure/limite d'accord évaluée. Il faut un oracle manuel distinct et des cas adversariaux non sélectionnés par convenance.

**FUE-0 de cette passe :** contrats agent fournis + SOURCE_POLICY documentaire contrôlés ; pas de nouveau test runtime exécuté par cet audit ; précédent HEAD `bc69b491` : 154/154 pytest PASS en 9,58 s sur run #41838275176 et sept CI terminées. **FUE cabinet 0/10**, aucun patient/coordonnées brutes/identifiant/radiographie exportés. **Aucune signature clinique, activation, remplacement de formule, code, norme, migration, merge ou déploiement.**

**NEXT pour un vrai avis séparé de l'agent :** importer/faire reconnaître la fiche `.claude/agents/Orthodontiste.md` dans l'environnement d'agents où elle est exécutable, lui fournir **ce dossier documentaire** sans patients ni images nominatives, exiger réponse structurée IMAGE/LANDMARKS/GEOMETRY/MEASUREMENTS/NORMS/CLINICAL/REPORT avec contre-exemples, sources et refus. En parallèle, faire une lecture humaine de clichés originaux non nominatifs dans un cadre autorisé ; **un agent même réellement invoqué ne remplace pas le praticien habilité**. Reporter le retour indépendant authentifié et daté dans la même section canonique/Notion sans écrire `approved_by_clinician=true` sans preuve.

**CHANTIER Digital Crown Céphalo V1 · LOT 1/4 OPEN · SOUS-LOT protocole Orthodontiste appliqué documentairement · NEXT vraie invocation si runner disponible + overlays natifs + avis orthodontiste humain signé · GOAL lever les réserves anatomiques avant R15/PDF.**

### 16. Agent Orthodontiste installable dans Claude Code — config FUE-0 (2026-11-04 ; PAS ENCORE INVOCATION)

**Déclencheur :** demande utilisateur « Go » après contre-expertise documentaire §15. Cette passe **corrige le blocage d'installation identifié**, pas un problème de mesure clinique : la source du Project `Orthodontiste.md.txt` de 2026-11-04 indiquait `.claude/agents/Orthodontiste.md`, absent du dépôt et sans délimiteurs YAML dans la copie Project. Au HEAD de cette passe, [la définition de sous-agent a été ajoutée sur la PR Draft #1208](https://github.com/hraaaaf/Digital_crown/blob/feat/ceph-v1-r14-audit-receipts-20261103/.claude/agents/Orthodontiste.md) avec du vrai **YAML frontmatter** encadré par `---`, sans changer la doctrine d'audit clinique de sa source ; body conservé, titre en Markdown. Identifiant d'invocation `orthodontiste` ; `model: inherit`, `effort: high`, `permissionMode: plan`, `tools: Read, Grep, Glob, Bash, WebSearch, WebFetch`, **aucun `Write` ni `Edit` dans les tools déclarés**. Interdits internes : toute édition clinique, upload de patients, migration, approbation automatique, fusion et déploiement. Note : l'accès `Bash` n'est pas une garantie système d'immuabilité ; le mode plan et les gardes du contexte sont indispensables.

**Preuve FUE-0 de configuration vérifiée :**
- Fichier cible au commit d'installation `959c3303fc9e9b3a5ed303b85a3760f3e950c70b`, GitHub blob SHA `cfe7adf069a1941ee8654cd57c1aac46e2c699b7` ; il correspond **exactement** au SHA1 Git blob calculé localement sur la fiche Project transformée (en-tête YAML + liste `skills` standard + corps original, sans coupes).
- Parsing YAML local avec `PyYAML.safe_load` : **PASS**, `name=orthodontiste`, cinq skills, `permissionMode=plan` ; aucune permission `Edit/Write` incluse ; convention identique à [scientific-reviewer existant](https://github.com/hraaaaf/Digital_crown/blob/feat/ceph-v1-r14-audit-receipts-20261103/.claude/agents/scientific-reviewer.md).
- Résolution GitHub des cinq chemins `.claude/skills/<skill>/SKILL.md` : **5/5 PRESENTS au SHA initial `80e4cce4`** : `scientific-source-research`, `validate-cephalo-pipeline`, `audit-panoramic-report-pipeline`, `audit-clinical-diagnosis-flow`, `review-scientific-pull-request`.
- Sous-agent **chargé/exécuté dans un vrai Claude Code : NOT_RUN** : le conteneur de cette conversation n'a pas la commande `claude`, et les outils GitHub connectés ne peuvent pas exécuter une session Claude Code ni déclencher de sous-agent autonome. **Ne pas présenter le FUE-0 de configuration comme un audit indépendant réalisé.**

**Instruction de lancement reproductible dans une session Claude Code autorisée, depuis le clone de cette branche/PR** (AUCUNE EXÉCUTION attestée dans cette passe) :

> Utilise exclusivement le sous-agent `orthodontiste` déclaré dans `.claude/agents/Orthodontiste.md` pour un audit READ-ONLY de la PR #1208 et du dossier unique `docs/audits/CEPH_V1_LOT1_SCIENCE_APPROVAL_FUE_PREFLIGHT.md`. Lis AGENTS.md, STATE.md, la roadmap consolidée et les contrats SRPose38/cephalo, puis §9–16. Contredis en priorité les mappings `Po/Po_anatomic`, `Co/Co_anatomic`, `Gn/Gn_anatomic`, `Pog'/Pog_soft`, la géométrie Merrifield 63.4349/116.5651° et le conflit Aariz ProMax 2D 1.139/0.139 mm/px. Produis les statuts IMAGE/LANDMARKS/GEOMETRY/MEASUREMENTS/NORMS/CLINICAL/REPORT, tableaux source et preuves, limites, contre-exemples et chaque condition de levée. N'affirme avoir vu ni image native ni DICOM ni tracé humain sans accès et preuve. Aucun patient nominatif, aucune écriture, aucun avis clinique signé, aucun merge/deploy. Consigne le SHA exact, le modèle/runner et l'heure du rapport ; retourner `BLOCKED` si la preuve critique manque.

**Oracles toujours manquants :** radiographies anonymisées **natives** dans un environnement permis (aucun fichier natif ouvert ici ; DNS `raw.githubusercontent.com` non résolu et connecteur GitHub refuse les binaires), Pixel Spacing et résolution/rotation de l'export, arbitrage du CSV Figshare officiel contre tableau primaire Aariz ProMax 2D, tracé indépendant humain de l'angle Z et des repères Co/Gn/Po, mesure aveugle sur vrai Digital Crown local, **0/10 FUE cabinet**. Même un rapport autonome du sous-agent ne serait **pas** une signature de praticien.

**Décision : AGENT-CONFIG READY / AGENT-RUN NOT_RUN / CLINICAL HOLD.** Aucune activation de R11/R13, aucun changement méthode versionnée, `clinical_validation_available=false`, PDF `INCOMPLETE`, PR Draft ; ne pas fusionner/déployer. Avant d'accorder un GO clinique, obtenir l'avis d'un orthodontiste humain habilité, daté, sur les médias et tracés réels. Aucun faux `approved_by_clinician=true`.

**CHANTIER Digital Crown Céphalo V1 · LOT 1/4 OPEN · SOUS-LOT agent Orthodontiste activable mais non invoqué · NEXT lancer le sous-agent dans Claude Code avec preuves, apporter les radios natives et validation clinique humaine · GOAL avis indépendant traçable sans confondre revue IA et certification clinique.**

### 17. Accès réel aux JPEG publics Aariz — vérification de métadonnées et cadrage des limites (2026-11-04)

**Nouveau constat reproductible :** malgré le DNS bloqué dans le conteneur, le connecteur GitHub a permis de décoder et examiner visuellement deux JPEG de téléradiographies anonymisées provenant du miroir public de recherche [Annagdy/CNN-CVM, commit fixe ea6678cd](https://github.com/Annagdy/CNN-CVM/tree/ea6678cd8ba62b615d909ecb1065023ea73eb827/Aariz_dataset/Aariz/test/Cephalograms), un appareil **Veraviewepocs 2D** et un **ProMax 2D**. Dimensions JPEG réellement décodées : **959 × 1198** et **1256 × 1592** pixels. Leurs deux jeux de fichiers JSON par image, Junior/Senior, ont été lus : 4/4 JSON, 29 symboles chacun, **116/116 coordonnées dans les bornes pixel**. Cela prouve uniquement la compatibilité technique de ces exports/annotations, PAS l'anatomie correcte des repères, l'égalité du miroir au ZIP officiel Figshare, ni la calibration DICOM/clinique. Aucun JPEG, point brut ni annotation recopiés ici.

**Schéma du repère cutané :** le symbole public correspondant au pogonion cutané se termine par le caractère grave U+0060 et non une apostrophe simple ; cette orthographe apparaît aussi dans [config.py des auteurs](https://github.com/manwaarkhd/aariz/blob/main/config.py). La correspondance avec Pog_soft Digital Crown est un candidat de mapping à déclarer explicitement, puis à confirmer anatomiquement sur image, pas une substitution automatique.

**Conflit ProMax 2D maintenu :** une application directe du coefficient **1,139 mm/pixel** du [Tableau 2 primaire](https://pmc.ncbi.nlm.nih.gov/articles/PMC12313948/) à un export JPEG de 1256 pixels de large impliquerait un champ horizontal théorique de **1430,58 mm** (plus de 1,4 m). Les [caractéristiques Planmeca ProMax 2D](https://www.planmeca.com/dental-imaging/panoramic-machines/planmeca-promax-2d/technical-specifications/) annoncent une plage céphalométrique de l'ordre de 18–30 cm et des pixels image 48/96/144 µm. Le facteur **0,139 mm/pixel** dans le CSV du miroir est ainsi nettement plus plausible pour un raster de cette taille, mais **ni erreur de l'article ni source de vérité ne sont démontrées** ; export, rééchantillonnage et magnification restent inconnus. Aucune conversion mm ni norme ne devient validée.

**Ce qui demeure NOT_RUN/NOT_EVALUABLE :** pas d'invocation indépendante du sous-agent Claude Code orthodontiste (CLI indisponible), ni overlay de repères anatomiques accepté par praticien ; aucun DICOM natif/résolution certifiée, aucun Z indépendant aigu/obtus, aucune décision clinique/signature. La présence d'un dispositif visible de positionnement auriculaire impose d'examiner la différence porion anatomique / ear rod, sans préjuger du placement effectif. **0/10 FUE cabinet**, clinical_validation_available=false, PDF INCOMPLETE, HOLD-Z-ORIENTATION et HOLD-MCNAMARA-SCALE. Aucun code/règle/DB/patient/merge/déploiement modifié.

**NEXT :** lancer l'agent orthodontiste dans un vrai runner Claude Code sur la PR Draft avec les clichés anonymisés et leurs références, réaliser l'overlay contrôlé Po/Co/Gn/Pog cutané, acquérir échelle native et contre-tracé humain, puis FUE cabinet. Le progrès image ne vaut pas validation clinique.

**CHANTIER Digital Crown Céphalo V1 · LOT 1/4 OPEN · SOUS-LOT images publiques et preuves géométriques limitées · NEXT runner Orthodontiste et clinique humaine · GOAL mesures scientifiquement contrôlées avant R15/PDF.**

### 18. Artefacts JPEG source-lockés et surimpression de repères — FUE-0 technique (2026-11-04)

**Résultat NOUVEAU, vérifié sur un runner réel GitHub Actions (PAS sur le runtime dentaire) :** [workflow source R&D](https://github.com/hraaaaf/Digital_crown/blob/2e6fa6b28b9014c130d4acaed118e5090786a98c/.github/workflows/ceph-v1-lot1-aariz-overlays.yml) et [script isolé](https://github.com/hraaaaf/Digital_crown/blob/2e6fa6b28b9014c130d4acaed118e5090786a98c/scripts/research/aariz_overlay_lab.py) ajoutés sur PR Draft #1208. Workflow d'accès public uniquement (pas de secrets, pas de backend/DB), contrôles git blob SHA du miroir immuable, dimensions raster, 29 symboles Junior + 29 Senior pour chaque cliché et absence de repères hors cadre. **6/6 sources vérifiées et 116/116 coordonnées in-bounds**. Le calcul de consensus emploie la moyenne avec plafond des groupes publiée par les auteurs. Les points indiqués sont **des annotations candidates** issues d'une source externe ; aucune correction manuelle, aucun jugement anatomique clinique.

**Images effectivement générées :** [GitHub Actions PR #41854786533](https://github.com/hraaaaf/Digital_crown/actions/runs/41854786533) SUCCESS, job public-source-overlay ; [artifact ZIP #13336449320](https://github.com/hraaaaf/Digital_crown/actions/runs/41854786533/artifacts/13336449320), 2 612 526 octets, **7 jours** de rétention ; 2 téléradiographies anonymisées publiques (Veraviewepocs 959×1198, ProMax 1256×1592), chacune avec **une vue complète, un zoom postérieur Po–Or–Co, un zoom mandibulo-labial Gn–Me–Pog-soft–Ls–Li**, soit **6 PNG**. Deuxième exécution du même SHA sur push [#41854771882](https://github.com/hraaaaf/Digital_crown/actions/runs/41854771882) SUCCESS également, ce qui confirme la répétabilité mais duplique le coût CI ; réserver ensuite le déclencheur au pull request. Manifest avec SHA exact, URLs et blobs, validation clinique à false et avis agent séparé NOT_RUN ; logs FUE-0 SOURCE OVERLAY PASS consultés, ZIP téléchargé et intégrité CRC vérifiée, les 6 PNG ouverts, rendu visuel contrôlé par le coordinateur.

**Source et conditions d'usage :** [archive Figshare officielle 27986417/v1](https://doi.org/10.6084/m9.figshare.27986417.v1), licence **CC BY 4.0** attestée par [l'API Figshare](https://api.figshare.com/v2/articles/27986417), taille archive originale ~2,1 Go (non téléchargée), référence Khalid et al., Scientific Data 2025. Les 6 blobs publics utilisés ici viennent de la **copie non officielle** [Annagdy/CNN-CVM@ea6678cd](https://github.com/Annagdy/CNN-CVM/tree/ea6678cd8ba62b615d909ecb1065023ea73eb827/Aariz_dataset/Aariz/test), leur intégrité vis-à-vis de ce miroir est contrôlée par SHA git ; **égalité binaire avec Figshare NON VÉRIFIÉE**. Aucune image ou annotation brute ajoutée aux commits ; les exports annotés résident uniquement dans les artifacts CI à courte rétention. La licence ne garantit pas à elle seule la validité d'un repère ou d'un facteur de calibrage.

**Review anatomy — verdict limité à l'image :** la superposition rend les repères Po, Or, Co, Gn et la lèvre/pogonion cutané visibles et leurs décalages Junior/Senior inspectables, mais aucun médecin n'a contre-tracé ou signé. Le zoom postérieur ProMax montre un dispositif radiographique auriculaire voisin de Po ; la distinction **porion anatomique vs ear-rod/porion machine** exige une expertise explicite au lieu d'une supposition d'identité des points. Le segment Po–Or (jaune), Co–Gn (magenta) et le segment labial (bleu) sont des **constructions géométriques candidates, pas des analyses validées**. Les deux cas ne prouvent pas l'angle Z obtus, ne résolvent pas les alternatives 63,4349/116,5651°, ni l'échelle ProMax primaire 1,139 vs miroir 0,139 mm/pixel. **Aucune valeur de longueur en mm clinique ni norme activée.**

**Gates :** IMAGE_PUBLIC_MIRROR=VISUALLY_RENDERED, PIXEL_BOUNDS=PASS, SOURCE_MIRROR_SHA=PASS, ARTIFACT_VISUAL_OPEN=PASS, DICOM_NATIVE=NOT_EVALUABLE, ANATOMICAL_PARITY_HUMAN=NOT_RUN, Z_MANUAL_ORACLE=NOT_RUN, OFFICIAL_FIGSHARE_HASH_MATCH=NOT_RUN, ORTHODONTISTE_CLAUDE_SUBAGENT=NOT_RUN (runner absent), CABINET_FUE=0/10, CLINICAL=HOLD, clinical_validation_available=false, PDF INCOMPLETE. **CI vert ≠ validation clinique**, et le dossier médical du patient ne doit jamais être importé dans une action GitHub publique.

**NEXT :** un orthodontiste humain ou l'agent indépendant exécuté dans un vrai Claude Code doit confronter Po/Co/Gn et le profil cutané aux overlays et descriptions anatomiques (en lecture seule) ; ensuite un praticien habilité vérifie l'original natif, la calibration DICOM, les cas Z obtus et signe une décision clinique avant 10 FUE cabinet. Aucun merge ni déploiement autorisé.

**CHANTIER Digital Crown Céphalo V1 · LOT 1/4 OPEN · SOUS-LOT FUE-0 réelles superpositions image source · NEXT revue Po–Co–Gn/Pog sur overlays et oracle humain · GOAL preuve anatomique et étalonnage défendables avant R15/PDF.**

### 19. Revue visuelle ciblée Po/Or/Co/Gn et profil cutané — 2026-11-04 (coordinateur, pas une approbation clinique)

**Provenance.** Contrôle visuel sur les [6 superpositions publiques dans l'artefact GitHub #13338620134](https://github.com/hraaaaf/Digital_crown/actions/runs/41855594616/artifacts/13338620134) (2 JPEG Aariz du miroir tiers, chacun full/posterior/profile), et calcul séparé des écarts entre [annotations Junior et Senior](https://github.com/Annagdy/CNN-CVM/tree/ea6678cd8ba62b615d909ecb1065023ea73eb827/Aariz_dataset/Aariz/test/Annotations/Cephalometric%20Landmarks). Les repères ont été examinés par le **coordinateur ChatGPT**, sans invocation indépendante du sous-agent Orthodontiste ni revue d'un praticien habilité. Définitions comparatives : [Aariz Scientific Data 2025](https://www.nature.com/articles/s41597-025-05542-3) et [StatPearls: Cephalometric Points](https://www.ncbi.nlm.nih.gov/books/NBK594272/table/article-131913.table1/). Ces définitions n'attestent ni l'identité locale du pixel source ni la convention propre à une méthode de Digital Crown.

**Écarts Euclidiens Junior/Senior, valeurs en pixels NON converties en mm :**

| Repère | Veraviewepocs 2D (px) | ProMax 2D (px) | Lecture permise |
|---|---:|---:|---|
| Po | 3,61 | 0 | Accord géométrique ≠ porion osseux démontré |
| Or | 6,40 | 7,07 | À contre-pointer : ancrage du plan de Francfort |
| Co | 0 | 0 | Accord des moyennes, pas preuve de position condylienne juste |
| Gn | 0 | 1 | Position image plausible, point construit à certifier |
| Me | 2,24 | 2,24 | Région mentonnière à revoir |
| Ls | 3,16 | 0 | Tissu mou candidat |
| Li | 0 | 2 | Tissu mou candidat |
| Pog cutané (symbole source Pog + U+0060) | 0 | 0 | Candidat de correspondance avec Pog_soft, non certifié |
| R, hors cibles de Co–Gn/Z | 0 | 29,73 | Divergence de groupe à ne pas masquer |

17/29 points identiques entre les deux fichiers de groupes sur Veraviewepocs ; 18/29 sur ProMax. Les fichiers sont **des moyennes de groupes** et non quatre tracés individuels. Un accord parfait sur Co/Pog cutané ne mesure pas la reproductibilité indépendante de ces repères.

**Sensibilité exploratoire de l'angle Z hors moteur DC, par fichier de groupe séparé :** Veraviewepocs Junior **77,4513°** versus Senior **75,5031°**, écart **1,9482°** ; ProMax Junior **57,8427°** versus Senior **58,0596°**, écart **0,2168°**. Ces différences peuvent dépendre de Po, Or, lèvres et pogonion simultanément : **ne pas les attribuer uniquement à Or**. Quatre résultats aigus, aucun angle >90° : le contre-exemple Merrifield V1 63,4349/116,5651° reste non arbitré. Aucun tracé manuel d'angle Z ni validation de sa convention.

**Constats anatomiques visuels — impressions NON certifiables :**
1. **ANA-Po-01 / BLOCKER :** sur ProMax, Po est voisin d'un dispositif circulaire de positionnement auriculaire ; l'identité exacte entre sommet osseux du méat auditif et repère instrumental est **NOT_EVALUABLE** sur ces overlays. Interdire Po source → Po_anatomic sans double marquage et référentiel.
2. **ANA-Or-02 / MAJOR :** Or est visible vers les rebords orbitaires mais diffère de 6,4–7,1 px entre groupes ; le plan de Francfort et les angles associés exigent un tracé indépendant sur image non annotée. Aucun seuil en mm admis tant que calibration non certifiée.
3. **ANA-Co-03 / BLOCKER :** Co est dans la région condylienne attendue ; les deux groupes ont les mêmes coordonnées sur les deux images, **sans prouver le point postéro-supérieur exact ni le mapping Co_anatomic**. Double contour possible à arbitrer.
4. **ANA-Gn-04 / MAJOR :** Gn et Me projetés près de la symphyse osseuse, distribution visuellement plausible ; il faut vérifier construction de Gn, Pog osseux/Me et méthode avant Co–Gn clinique.
5. **ANA-Soft-05 / MAJOR :** Ls, Li et pogonion cutané paraissent proches du contour facial antérieur ; segment labial bleu = construction candidate, PAS ligne Merrifield approuvée. Vérifier indépendamment la lèvre tangente et les secteurs aigu/obtus.
6. **ANA-MM-06 / BLOCKER :** échelle ProMax discordante 1,139 mm/pixel publication contre 0,139 miroir, origine DICOM/export et magnification non certifiées. Aucune distance Co–Gn en mm clinique, aucun profil normatif.

**Grille de décision humaine à remplir, actuellement TOUTES CASES NON RENSEIGNÉES :** sur chacun des 2 cas, identifier source native, date/lecteur/relecture, état **APPROUVÉ_SUR_NATIVE / REFUSÉ / NON_ÉVALUABLE** pour Po osseux versus instrument, Or, Co, Gn/Me, Ls/Li/Pog cutané, construction Z obtuse, calibration/mm. Tracé en aveugle sur cliché non annoté, puis comparaison à l'overlay et justification des corrections ; aucune signature fictive. Cette grille ne vaut pas FUE de cabinet et un accord sur deux JPEG tiers ne certifie pas les productions patient.

**Décision :** image source publique = consultée ; 29 repères × 2 groupes × 2 images = contrôlés géométriquement, mais **LANDMARKS_ANATOMICAL_PARITY=NOT_APPROVED**, **ORTHODONTISTE_AGENT_RUN=NOT_RUN**, **HUMAN_SIGNOFF=NONE**, **NATIVE_DICOM_SCALE=NOT_EVALUABLE**, **HOLD-Z-ORIENTATION**, **HOLD-MCNAMARA-SCALE**, **clinical_validation_available=false**, PDF **INCOMPLETE**, **CABINET_FUE=0/10**. Pas de modification de formule/méthode, aucune activation médicale, PR Draft sans merge/deploy.

**NEXT :** transmettre les 6 superpositions et clichés non annotés au praticien pour revue indépendante des cibles Po/Or/Co/Gn/soft ; récupérer convention de tracé, incertitude et calibration native ; vérifier un vrai cas Z obtus avant nouvelle méthode versionnée, puis FUE cabinet. L'agent Orthodontiste ne peut pas être déclaré exécuté sans runner autonome.

**CHANTIER Digital Crown Céphalo V1 · LOT 1/4 OPEN · SOUS-LOT revue visuelle ciblée §19 · NEXT arbitrage humain Po/Or/Co/Gn et calibration native · GOAL lever les réserves anatomiques sur preuve avant R15/PDF.**


### 20. Reprise R14 : oracle synthétique Z obtus et clarification ProMax — 2026-11-04 (FUE-0, clinique HOLD)

**PRE.** Source unique vérifiée : ce dossier §19, [PR #1208 Draft](https://github.com/hraaaaf/Digital_crown/pull/1208), branche `feat/ceph-v1-r14-audit-receipts-20261103`, HEAD initial `94fad0f049044618ba80f3ce2ed229fbe30639af`. Goal : vérifier sur l'implémentation et une construction **strictement synthétique** la conservation du secteur aigu/obtus de Z, puis isoler exactement ce que les sources permettent de conclure sur l'échelle ProMax ; sans activation médicale.

**R14 exact-HEAD terminé.** [Run #41861357086](https://github.com/hraaaaf/Digital_crown/actions/runs/41861357086), job `backend-r14-hold` #126683693058, logs inspectés : checkout `94fad0f`, **154 passed in 9.95s**, COMPLETED/SUCCESS. Autres contrôles du même SHA : [Aariz #41861357077](https://github.com/hraaaaf/Digital_crown/actions/runs/41861357077), [Scope #41861357076](https://github.com/hraaaaf/Digital_crown/actions/runs/41861357076), [UI #41861357099](https://github.com/hraaaaf/Digital_crown/actions/runs/41861357099), Theme09 #41861357053, Theme10 #41861357025, Theme11 #41861357040 = SUCCESS ; M6-I #41861357057 = SKIPPED hors scope. Il s'agit de **preuves du SHA initial**, pas d'un futur HEAD documentaire ou de validation clinique.

**Z : contrat vérifié dans le code.** `backend/services/cephalo_tweed_merrifield_geometry.py` : `merrifield_z_angle_deg_v1` utilise `_axis_angle_deg` qui retourne `min(angle_rays, 180.0-angle_rays)`. Les valeurs de l'axe ne peuvent dépasser 90°. Le test existant `backend/tests/test_cephalo_r6_tweed_merrifield.py::test_merrifield_z_angle_selects_most_protrusive_lip_and_is_mirror_invariant` contrôle un résultat aigu 63,4349° et un miroir ; il ne démontre pas la préservation du secteur obtus.

**Oracle mathématique indépendant (hors Digital Crown ; aucune anatomie patient).** Deux jeux de points avec `Po=(0,0)`, `Or=(10,0)`, `Pog_soft=(2,20)`, direction horizontale `u=(10,0)`. On calcule l'angle non réflexe des rayons avec `degrees(atan2(abs(cross(u,v)),dot(u,v)))`, puis le résultat de la formule entre axes avec `min(angle,180-angle)`.

| Fixture synthétique | Ls_soft | Li_soft | v=Ls-Pog_soft | Rayons atan2 | Axe V1 |
|---|---|---|---|---:|---:|
| Z-SYN-ACUTE | (7,10) | (6,12) | (5,-10) | 63,434948823° | 63,434948823° |
| Z-SYN-OBTUSE | (-3,10) | (-4,12) | (-5,-10) | **116,565051177°** | **63,434948823°** |

Dans chaque fixture Ls reste la lèvre choisie par la projection Po→Or, selon la règle du code. **Constat technique :** le moteur replie le secteur obtus sur l'aigu et perd l'information de secteur. **Aucun bug clinique définitivement établi** : l'angle entre **axes** peut être intentionnel ; il faut une décision sur la construction/secteur Merrifield exact. Le [papier primaire Merrifield 1966](https://www.sciencedirect.com/science/article/pii/0002941666902508) est identifié (DOI `10.1016/0002-9416(66)90250-8`), mais sa méthode intégrale n'est pas disponible ici ; les [descriptions secondaires](https://scielo.org.za/scielo.php?pid=S0011-85162019000700008&script=sci_arttext) ne suffisent pas pour activer un changement. **HOLD-Z-ORIENTATION reste fermé.**

**ProMax : précision documentaire importante.** Le [Tableau 2 de Khalid et al. (Scientific Data 2025)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12313948/) donne **ProMax 2D : 1,139 mm/px (41 images)** mais **ProMax with ProTouch : 0,139 mm/px (135 images)**. Ce sont deux libellés d'appareils distincts ; attribuer automatiquement 0,139 à ProMax 2D serait une confusion possible. Le CSV du miroir attribue 0,139 au cas nommé ProMax 2D, mais l'identité avec l'archive Figshare officielle, le modèle réel, la calibration DICOM et l'éventuel resize ne sont pas certifiés. À titre **purement arithmétique**, 1256 px × 1,139 = 1430,584 mm ; × 0,139 = 174,584 mm ; ces produits ne démontrent pas le champ réel. **HOLD-MCNAMARA-SCALE reste fermé.**

**POST / limites.** FUE-0 de lecture source + oracle synthétique réalisé, tests R14 prouvés sur `94fad0f`. `ORTHODONTISTE_AGENT_RUN=NOT_RUN` ; cliché natif DICOM et correction de magnification NOT_EVALUABLE ; vrai traçage en aveugle Po/Or/Co/Gn/soft NOT_RUN ; angle Z clinique >90° NOT_VERIFIED ; décision orthodontiste humain NONE ; `clinical_validation_available=false`, PDF `INCOMPLETE`, **0/10 FUE cabinet**. Aucun code, modèle, formule, norme, DB, média patient ou UI modifiés. PR Draft, aucun merge ni déploiement. La CI est à revérifier sur le nouveau HEAD documentaire.

**NEXT exact :** confirmer identité appareil + CSV officiel Figshare + échelle native/crop/magnification ; obtenir un contre-tracé aveugle humain sur les sources natives et une convention signée pour l'angle Z (y compris >90°), Po/Or/Co/Gn/soft ; seulement ensuite envisager une correction versionnée et les 10 FUE cabinet. Ni le présent oracle ni un agent IA ne remplacent cette approbation.

**CHANTIER Digital Crown Céphalo V1 · LOT 1/4 OPEN · SOUS-LOT R14 fini, oracle Z obtus documenté · NEXT native + convention Z + signature humaine + CI exact HEAD · GOAL lever HOLD-Z et HOLD-MCNAMARA avant R15/PDF.**


### 21. Source primaire Merrifield, provenance Figshare et plan de validation humaine — 2026-11-04 (FUE-0)

**PRE :** reprise depuis le §20 avec PR #1208 OPEN/DRAFT, HEAD `354bb7182b6b54726d54424b5afacd75de8ec81b`. Goal : affiner les deux blocages à partir d'un document scientifique original et des métadonnées officielles de l'archive sans importer d'images patients, puis préparer une décision humaine falsifiable ; aucun changement moteur ni activation clinique.

**CI exact HEAD du §20 :** 8 workflows GitHub terminés : 7 SUCCESS, M6-I SKIPPED hors périmètre. [R14 #41868053415](https://github.com/hraaaaf/Digital_crown/actions/runs/41868053415), job `backend-r14-hold` #126707328824, logs examinés : **154 passed in 7.66s** sur le commit `354bb718` ; [Aariz #41868053903](https://github.com/hraaaaf/Digital_crown/actions/runs/41868053903), [Scope #41868053492](https://github.com/hraaaaf/Digital_crown/actions/runs/41868053492), [UI #41868053441](https://github.com/hraaaaf/Digital_crown/actions/runs/41868053441), Theme09 #41868053520, Theme10 #41868053851 et Theme11 #41868053691 SUCCESS. Aucun artefact de ces runs ne vaut signature médicale. Cette CI est celle du **HEAD de départ**, pas du commit documentaire ultérieur.

#### 21.1 Merrifield original : NOUVELLE source primaire réellement consultée

**Correction de l'état documentaire du §20 :** le document original complet est désormais accessible chez la [Tweed Foundation, copie PDF de Merrifield 1966, American Journal of Orthodontics 52(11):804–822](https://tweedortho.com/wp-content/uploads/2024/12/profile-line-aid.pdf), DOI `10.1016/0002-9416(66)90250-8`. Consultation directe du texte et des illustrations **Fig. 2 (ligne de profil), Fig. 5 (angle Z), Fig. 6 (constructions)**, avec capture visuelle des pages imprimées 812–813, le 2026-11-04. Il ne s'agit plus d'un simple résumé secondaire.

La source primaire stipule que la **ligne de profil** est tangente au pogonion cutané et au point le plus antérieur de la lèvre la plus protrusive (supérieure ou inférieure) et est prolongée jusqu'au plan de Francfort. L'angle Z est explicitement l'**angle inférieur** issu de leur intersection (texte original imprimé p. 811 ; Fig. 5 imprimée p. 812). La figure montre le secteur usuel voisin de 80°. **Le PDF ne formalise pas de branche calculatoire algorithmique pour une géométrie obtuse >90° :** ne pas interpréter `116,565051177°` de la fixture §20 comme une norme médicale ni une validation de la convention sans traçage clinique indépendant.

**Écart démontrable avec Digital Crown V1 :** le code replie par `min(angle, 180-angle)` sans information de secteur ; la méthode originale fixe une position de l'angle *inférieur*, non seulement la valeur du plus petit angle entre axes. Cela justifie le maintien du **HOLD-Z-ORIENTATION** et l'exigence d'un **oracle tracé sur la Figure 5 + un cas obtus**, sans encore autoriser de patch, de diagnostic ou de norme. Un agent IA et une revue interne ne signent pas cette convention à la place du praticien.

#### 21.2 Figshare officiel et limites exactes du contrôle du miroir

L'[API officielle Figshare, article #27986417/v1](https://api.figshare.com/v2/articles/27986417) confirme un **seul objet livré** : `Aariz.zip`, `file_id=51041642`, **2 098 209 792 octets**, **MD5=e0bd645bca6759abdae4f199d841bda6**, licence CC BY 4.0. La taille et l'empreinte décrivent **l'archive entière**, pas un JPEG ou le CSV en son sein. Publication 2025-05-21, modification 2025-07-31. Aucun CSV autonome n'est listé dans cette API ; l'appartenance des deux JPEG et du CSV miroir à cette archive officielle reste **NON VÉRIFIÉE**, faute de lecture de l'archive et de comparaison membre à membre.

**Limite d'accès explicitement observée :** une tentative HTTP Range du téléchargeur Figshare dans l'environnement de travail s'est arrêtée sur `DNS_RESOLUTION_FAILED` ; **aucun octet de l'archive n'a été obtenu**. Ne pas déclarer l'archive téléchargée ou comparée.

**Comparaison des deux cas publics du miroir épinglé** `Annagdy/CNN-CVM@ea6678cd`, CSV Git blob `6f73da5d573715dfcfc683461d197ac81c4fac43` :
- cas Veraviewepocs 2D : `pixel_size=0.144` mm/px, cohérent avec [Table 2 de Khalid et al. 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12313948/) ; image JPEG exportée, pas le DICOM natif ;
- cas ProMax 2D : `pixel_size=0.139` dans le CSV miroir, **versus 1.139 mm/px ProMax 2D dans le tableau primaire**. Le même tableau réserve 0.139 mm/px au **ProMax with ProTouch**. Cette concordance numérique avec un *autre* appareil n'autorise ni substitution ni correction a priori.

Le [constructeur Planmeca, ProMax 2D](https://www.planmeca.com/dental-imaging/panoramic-machines/planmeca-promax-2d/technical-specifications/) indique pour le produit une taille de pixel image sélectionnable de **48/96/144 µm**, un champ céphalométrique de l'ordre de **18–30 cm** et un agrandissement de **1.13**. Ce sont **des caractéristiques générales**, pas la métadonnée de l'export de l'étude ; ne PAS transformer ces tailles de pixel en l'échelle clinique du JPEG. Le contraste apparent `1256px × 1.139 mm/px = 1430.584mm` est un signal d'incohérence **sous hypothèse d'absence de redimensionnement**, pas une preuve absolue de faute dans l'article. **HOLD-MCNAMARA-SCALE maintenu.**

**Métrologie DICOM — [PS3.3 2026c §10.7](https://dicom.nema.org/medical/dicom/current/output/chtml/part03/sect_10.7.html) :** enregistrer `Pixel Spacing (0028,0030)` (ordre ligne, colonne), `Imager Pixel Spacing (0018,1164)` s'il est présent, `Pixel Spacing Calibration Type (0028,0A02)`, description `(0028,0A04)`, taille du raster et transformations export/crop/resize. L'absence de ces informations n'établit ni calibration ni absence de calibration. Une dimension en mm exige provenance et convention, y compris hypothèses géométriques et de profondeur.

#### 21.3 Paquet d'arbitrage humain opérationnel — champs NON RENSEIGNÉS

Les images Aariz publiques demeurent des **cas méthodologiques de référence**, pas des FUE cabinet. Le praticien doit compléter sur les originaux non annotés, **avant** toute comparaison avec les superpositions :

| Contrôle | Pièce attendue (non nominative) | État maintenant |
|---|---|---|
| Origine et chaîne d'acquisition | fichier natif ou export traçable, hash, appareil exact, orientation, crop et transformation | NON FOURNI |
| Po versus oreille instrumentale | double positionnement si distinct, règle de porion osseux explicitée, annotation indépendante | HUMAN_GATE_REQUIRED |
| Or / Francfort | point inférieur orbitaire, éventuelle projection bilatérale, FH reconstruite sans voir consensus | HUMAN_GATE_REQUIRED |
| Co / Gn / Me | convention de chaque landmark et des constructions, incertitude et motifs de refus | HUMAN_GATE_REQUIRED |
| Ls/Li/Pog' et Z | ligne tangente, secteur inférieur de la Fig. 5, mesure indépendante, cas obtus tracé | HUMAN_GATE_REQUIRED |
| ProMax / McNamara mm | identité appareil + CSV officiel + DICOM + grossissement/export, intervalle de validité | BLOCKED |
| Calcul ↔ vue ↔ API ↔ PDF | valeur, version, arrondi, non-computable, aucune activation avant accord | NOT_RUN |
| Date, lecteur, décision clinique | APPROUVÉ SUR NATIF / REFUSÉ / NON ÉVALUABLE pour chaque cas et repère ; justification et signature habilitée | NONE |

**POST :** l'article original a été consulté avec inspection visuelle de la Figure 5 ; provenance Figshare officialisée au niveau ZIP et CSV miroir au niveau Git SHA ; confusion ProMax 2D/ProTouch explicitée ; 154/154 tests R14 sur HEAD précédent confirmés. **Aucune lecture des membres du ZIP officiel, aucun original DICOM ni validation des repères par praticien, aucune invocation réelle du sous-agent Orthodontiste**. `clinical_validation_available=false`, PDF final `INCOMPLETE`, **0/10 FUE cabinet** ; les deux HOLD restent fermés. Aucun changement de code clinique, modèle, norme, UI, patient, merge ni déploiement. Les CI du nouveau HEAD documentaire ne sont pas héritées.

**NEXT exact :** obtenir les fichiers natifs / la correspondance officielle Figshare et l'arbitrage des auteurs/constructeur, puis contre-tracés en aveugle avec décision Z (secteur inférieur) et Po/Or/Co/Gn ; enfin, seulement si signé, correction de méthode versionnée et batterie 10 FUE cabinet avant R15/PDF.

**CHANTIER Digital Crown Céphalo V1 · LOT 1/4 OPEN · SOUS-LOT source Merrifield originale + provenance Figshare + gate humain préparés · NEXT examen des natifs, arbitrage signé et CI exact HEAD · GOAL lever scientifiquement les deux HOLD avant R15/PDF.**


### 22. Réplication contrôlée des coordonnées Aariz (ground truth du code auteur) + CI exact SHA — 2026-11-04 (FUE-0, HOLD)

**PRE / périmètre.** Reprise du HEAD `f1738c0e1106c41189a6fc596b144043fac5abae` sur [PR #1208 DRAFT](https://github.com/hraaaaf/Digital_crown/pull/1208) ; seul le présent canonique scientifique/FUE peut être modifié. Objectif : finir les preuves exact-SHA et répliquer la construction réelle des points de référence Aariz, **pas requalifier des annotations comme contre-tracés humains**. Aucune touche code clinique, modèle, calibration, activation, merge, deployment ni donnée patient.

**CI pleinement achevée sur ce SHA (puisque le §21 était HEAD avant la présente écriture) :** les huit workflows terminés, **7 SUCCESS + 1 M6-I SKIPPED hors périmètre**. Run [R14 #41870754819](https://github.com/hraaaaf/Digital_crown/actions/runs/41870754819), job `backend-r14-hold` #126716831015 : log de checkout `HEAD is now at f1738c0` et résultat **`154 passed in 7.14s`** vérifiés. SUCCESS aussi [Aariz #41870755512](https://github.com/hraaaaf/Digital_crown/actions/runs/41870755512), [Scope #41870754949](https://github.com/hraaaaf/Digital_crown/actions/runs/41870754949), [UI #41870755602](https://github.com/hraaaaf/Digital_crown/actions/runs/41870755602), Theme09 #41870755079, Theme10 #41870755668, Theme11 #41870754927. Ne pas transférer cette preuve au prochain commit documentaire sans nouvel exact-HEAD.

**Code upstream réel, distinct du CSV miroir :** [dépôt original des auteurs `manwaarkhd/aariz`, commit `0634b8b4e6783b13fb6383fac694d61123904d3c`](https://github.com/manwaarkhd/aariz/tree/0634b8b4e6783b13fb6383fac694d61123904d3c). Dans [`dataset.py` lignes `get_landmarks`](https://github.com/manwaarkhd/aariz/blob/0634b8b4e6783b13fb6383fac694d61123904d3c/dataset.py), Git blob `ce3d7c03e97ebd3f0f0b1fc63889f5b8f58f8482`, l'oracle utilisé par **ce chargeur** est :
`x_gt=ceil(0.5*(x_junior+x_senior))`, `y_gt=ceil(0.5*(y_junior+y_senior))`, appliqué index par index sur les 29 repères. La [liste d'IDs et symboles `config.py`](https://github.com/manwaarkhd/aariz/blob/0634b8b4e6783b13fb6383fac694d61123904d3c/config.py) contient explicitement Po/Or/Co/Gn/Ls/Li/Pog' et Ramus. **Senior n'est pas le ground truth produit par ce chargeur**, les deux dossiers sont des *moyennes de groupes* et non quatre traces personnelles, et l'arrondi `ceil` peut changer la coordonnée de 1 px. Cela ne suffit pas à prouver que toute évaluation externe Aariz utilise nécessairement ce même chargeur/arrondi.

**Réplication hors runtime Digital Crown, à partir de quatre JSON publics du miroir épinglé** [`Annagdy/CNN-CVM@ea6678cd`](https://github.com/Annagdy/CNN-CVM/tree/ea6678cd8ba62b615d909ecb1065023ea73eb827/Aariz_dataset/Aariz/test/Annotations/Cephalometric%20Landmarks) ; contrôle des 29 `landmark_id` à position égale Junior/Senior pour chaque cas avant moyenne. Unités **px de l'image du miroir**, jamais millimètres :

| Cas | Landmark | Junior (x,y) | Senior (x,y) | `ceil((J+S)/2)` | `dist(J,S)` en px |
|---|---|---|---|---|---:|
| Veraviewepocs 2D `cl6cc2n5k405307716g0393xo` | Po | (307,538) | (310,540) | **(309,539)** | 3.606 |
| idem | Or | (657,530) | (662,526) | **(660,528)** | 6.403 |
| idem | Co | (370,553) | (370,553) | **(370,553)** | 0 |
| idem | Gn | (703,946) | (703,946) | **(703,946)** | 0 |
| ProMax 2D `cl5lc0isd1298072u53z31emu` | Po | (106,679) | (106,679) | **(106,679)** | 0 |
| idem | Or | (703,562) | (710,563) | **(707,563)** | 7.071 |
| idem | Co | (199,687) | (199,687) | **(199,687)** | 0 |
| idem | Gn | (805,1181) | (806,1181) | **(806,1181)** | 1.000 |

Les écarts Junior/Senior sont **non nuls pour 12/29 landmarks Veraviewepocs et 11/29 ProMax**. *Maximum par cas sur les 29 points* : Veraviewepocs **Or 6.403 px** ; ProMax **Ramus `R` 29.732 px** [J=(209,870), S=(219,898)], bien que Ramus ne soit pas le repère central de la décision Z. Cas Po/Co sans écart ne signifie **pas** que la position osseuse réelle est correcte. Cette moyenne reproductible n'est PAS un nouvel avis de médecin, ni une mesure de performance clinique, ni un contrôle du ZIP officiel.

**Chaîne de provenance des quatre JSON dans le miroir** (Git blob SHA, pas identité avec Figshare) :
- Veraviewepocs Junior `fa5bdf3841aea69bd74efcfdfba3bfdeb1fc00e4`, Senior `2186adfdbc2b9be821c8a4da5cddcf3572f00907`.
- ProMax Junior `fcc0d7f1eaad54c3e2099dafa230530d0e0e5cbd`, Senior `3447e8ef82d3aae2ef1fe11e28a6bbde22b4815d`.

**Archive officielle — limite réconfirmée techniquement :** DNS `api.figshare.com`, `ndownloader.figshare.com`, `figshare.com` et `github.com` a échoué dans le conteneur (getaddrinfo `[Errno -3] Temporary failure in name resolution`, `curl (6)`). Le connecteur GitHub donne accès aux JSON et au code auteur, et l'API Figshare via recherche web aux métadonnées, **pas** aux octets du ZIP 2.1 Go dans ce runtime. Aucun Range reçu ; aucun CRC/MD5 membre ni correspondance CSV/image entre ZIP officiel et miroir certifiés. Une extraction côté environnement réseau autorisé devra contrôler SHA-256 de chaque membre et les dimensions/transformations ; ne pas entreprendre un transfert de 2 Go pour une simple CI.

**POST / décision.** FUE-0 reproductibilité code source/annotations : **PASS technique** pour le chargeur auteur sur les 2 cas *du miroir* ; CI R14 sur `f1738c0` **154/154 PASS**, les 7 workflows applicables SUCCESS. **NO GO clinique** : origine image native et calibration NOT_VERIFIED, angle Z secteur inférieur à décider par praticien, Po/Or/Co/Gn indépendants NOT_RUN, vrai sous-agent Orthodontiste NOT_RUN, signature médecin NONE, `clinical_validation_available=false`, PDF `INCOMPLETE`, **0/10 FUE cabinet**. **HOLD-Z-ORIENTATION et HOLD-MCNAMARA-SCALE fermés.** Un éventuel nouveau HEAD ne sera pas dit CI-vert par héritage.

**NEXT exact :** vérification fichier-à-fichier du ZIP officiel si environnement réseau disponible, métadonnées DICOM originales de la machine, arbitrage de l'écart ProMax 2D/ProTouch auprès de l'équipe source, double traçage praticien en aveugle et signature de la matrice §21 ; ensuite seulement versionner correctif scientifique et effectuer 10 FUE cabinet.

**CHANTIER Digital Crown Céphalo V1 · LOT 1/4 OPEN · SOUS-LOT CI f1738c0 + réplication 29 points Aariz (mirroir seul) · NEXT ZIP officiel/natifs et contre-tracé signé · GOAL lever HOLD-Z et HOLD-MCNAMARA sans faux GO clinique.**

### 23. Calibration ProMax : comparaison constructeur + régressions fail-closed au runtime — 2026-11-04 (FUE-0, clinique HOLD)

**PRE — état figé.** [PR #1208 Draft](https://github.com/hraaaaf/Digital_crown/pull/1208), HEAD initial `17c398d53846efe2e8a66a6c9f991236ddd8b19a`, CI initiale 7 SUCCESS / 1 SKIPPED et R14 **154 passed in 6.00s** [run #41872231689](https://github.com/hraaaaf/Digital_crown/actions/runs/41872231689). Objectif de cette passe : empêcher que le conflit de coefficients ProMax de l'article et du CSV ne soit silencieusement pris pour une calibration dans le runtime, grâce à des **tests de sécurité purement synthétiques**. Aucun algorithme ou norme clinique ne peut être approuvé par ce sous-lot.

**Divergence systématique du CSV miroir, non identité avec Figshare :** [Git blob `6f73da5d573715dfcfc683461d197ac81c4fac43`, dépôt `Annagdy/CNN-CVM@ea6678cd`](https://github.com/Annagdy/CNN-CVM/blob/ea6678cd8ba62b615d909ecb1065023ea73eb827/Aariz_dataset/Aariz/cephalogram_machine_mappings.csv), CSV complet 1 000 lignes relues : **ProMax 2D 41/41 lignes ont `pixel_size=0.139`**, ProMax with ProTouch 135/135 ont aussi `0.139`. L'[article original, Table 2](https://pmc.ncbi.nlm.nih.gov/articles/PMC12313948/) attribue pourtant **1.139 mm/px à ProMax 2D** (N=41), **0.139 à ProMax with ProTouch** (N=135). Cela n'est donc pas une seule ligne du miroir anormale ; la source officielle du CSV inclus dans le ZIP Figshare n'est toujours pas lue. **Aucune correction arbitraire de l'article ou du CSV n'est justifiée.**

**Contexte constructeur qui renforce la nécessité d'identifier la tête céphalo exacte :**
- [Planmeca ProMax 2D — spécifications françaises officielles](https://www.planmeca.com/fr/imagerie-dentaire/appareils-panoramiques/units-dimagerie-planmeca-promax-2d/caracteristiques-techniques/) : taille image sélectionnable 48 / 96 / 144 µm ; grossissement céphalométrique nominal 1.13× ; tailles du champ et du raster variables selon configuration/export.
- [Manuel de la gamme ProMax (PDF)](https://www.acmerevival.com/wp-content/uploads/2022/09/Planmeca-ProMax-2D-Users-Manual.pdf), section caractéristiques : capteur plan **ProCeph 139 µm** alors que le céphalostat panoramique à balayage comporte un capteur **48 µm**. Ces chiffres sont des caractéristiques matérielles, **pas la calibration effective des JPEG**. L'égalité numérique `139 µm=0.139 mm` et la proximité `1.139≈1.13` ne démontrent pas une confusion de capteur, de source ou d'unité ; la machine et la chaîne native ne sont pas identifiées.
- Le §21 définit la preuve DICOM/native requise. Une **règle physique visible, documentée et contrôlée**, distincte des ratios du CSV, peut fournir une calibration par deux points de *l'image concernée* si son identité/échelle/rendu sont vérifiés ; cela ne réconcilie pas pour autant les annotations, l'anatomie, les normes historiques et l'agrandissement.

**Relecture réelle du code de sécurité au HEAD initial :**
- [`cephalo_runtime_evidence.py`](https://github.com/hraaaaf/Digital_crown/blob/17c398d53846efe2e8a66a6c9f991236ddd8b19a/backend/services/cephalo_runtime_evidence.py) : `_calibration_source` ne crée une preuve `kind="calibration"` que pour `MANUAL_TWO_POINT` avec `distance_mm / hypot(p2-p1) == runtime pixel_ratio` (tolérance numérique, pas validation clinique) ou `AUTO_FIDUCIAL_PROFILE` `AUTO_VERIFIED` avec `provenance`. En absence de cette preuve, il retourne `None`.
- [`cephalo_evidence_case_integrity.py`](https://github.com/hraaaaf/Digital_crown/blob/17c398d53846efe2e8a66a6c9f991236ddd8b19a/backend/services/cephalo_evidence_case_integrity.py) : interdit de lier une mesure à une source non `kind='calibration'` et impose patient/case exact. Ne pas confondre cette validation *technique* avec la preuve que l'échelle ou le fiducial reflète l'anatomie.
- [`cephalo_auto_calibration_evidence.py`](https://github.com/hraaaaf/Digital_crown/blob/17c398d53846efe2e8a66a6c9f991236ddd8b19a/backend/services/cephalo_auto_calibration_evidence.py) : recalcul du ratio des graduations et concordance avec le profil déclaré et `AUTO_VERIFIED`. Les tests préexistants du runtime couvrent des candidats invalides, mais pas explicitement la divergence `0.139` / `1.139`.

**NOUVEAU : régressions fail-closed `backend/tests/test_cephalo_v1_lot1_fue_preflight.py`** (test-only, aucun changement de moteurs) :
1. Paramètres externes `0.139` et `1.139` injectés **sans preuve d'étalonnage** dans `CephaloEngine` et le constructeur d'évidence. Résultat exigé : **0 source calibration**, aucune mesure `requires_calibration` `AVAILABLE`, toutes les valeurs linéaires `None`, `validate_case_evidence_graph` satisfait.
2. Paramètres externes `0.139` et `1.139` avec **une vraie géométrie synthétique discordante** : règle 50 px =10 mm, donc ratio indépendant 0.2 mm/px. Résultat exigé : **`CephaloRuntimeEvidenceError` sur mismatch de géométrie** ; aucun arbitrage de valeur au nom de ProMax.
3. Les deux tests sont paramétrés (4 cas pytest supplémentaires) et **ne constituent pas 4 FUE cabinet**. Les cas testés ne représentent aucun vrai patient.

**POST — statut de preuve à ne PAS anticiper :** code + tests synthétiques ajoutés comme régression de refus, aucune norme/mesure anatomique/diagnostic/règle/DB/PDF/UI modifiée. La CI du **nouveau SHA** doit être consultée après le push pour affirmer le nombre de tests réellement PASS ; la CI précédente `17c398d` ne s'applique pas automatiquement. **HOLD-MCNAMARA-SCALE, HOLD-Z-ORIENTATION maintenus**, ZIP officiel/DICOM/contre-tracé praticien toujours NON FOURNIS, `clinical_validation_available=false`, PDF `INCOMPLETE`, **0/10 FUE cabinet**. Aucun merge, ni déploiement.

**NEXT précis :** récupérer un original ou un export calibrable avec règle dont la longueur physique est connue (ou DICOM natif + transformation), obtenir l'appareil exact et clarification CSV/Article auteurs ; contre-tracés indépendants de Po/Or/Co/Gn/soft et secteur inférieur Z en clinique ; uniquement ensuite envisager R15/PDF et les 10 FUE cabinet.

**CHANTIER Digital Crown Céphalo V1 · LOT 1/4 OPEN · SOUS-LOT preuve source ProMax + régressions ratio non fiable · NEXT CI exact SHA + acquisition native et validation praticien · GOAL aucune mesure McNamara certifiée sans provenance vérifiée, puis levée des deux HOLD.**

### 24. Preuve indépendante ProMax 2D Digital et question officielle aux auteurs Aariz — 2026-11-04 (FUE-0, clinique HOLD)

**PRE.** HEAD initial `bd1806403a66c7f58e12ee55ddb078b6f06fe521`, [PR #1208 OPEN/DRAFT](https://github.com/hraaaaf/Digital_crown/pull/1208), CI technique **7 SUCCESS / M6-I SKIPPED ; R14 158/158 PASS en 7.55 s**, unique canonique §23 consulté avant cette passe. Mandat : résoudre par recherche le conflit de provenance, pas choisir une valeur sans image native.

**Nouvelle pièce primaire externe, indépendante du dataset Aariz (étude publiée 26 juillet 2024)** : Danz JC, Stöckli S, Rank CP, « Precision and accuracy of craniofacial growth and orthodontic treatment evaluation by digital image correlation: a prospective cohort study », *Frontiers in Oral Health*, DOI [10.3389/froh.2024.1419481](https://www.frontiersin.org/journals/oral-health/articles/10.3389/froh.2024.1419481/full), section « Interventions ». Les auteurs documentent des céphalogrammes **Planmeca ProMax 2D Digital one-shot**, capteur **139 µm/pixel**, export **JPEG lossless**, **grossissement 1.13** appliqué pour calibrer au plan médio-sagittal réel. Source primaire lue en **HTML officiel de l'éditeur**, même contenu figurant dans le PDF mais ce dernier n'a pas pu être rendu en screenshot par l'outil. Il s'agit d'une *autre cohorte* (30 patients), d'une configuration identifiée d'un ProMax 2D Digital, **pas du matériel ni des radiographies Aariz**.

**Tri des affirmations pour la décision scientifique :**
1. **VÉRIFIÉ indépendamment :** une chaîne ProMax 2D Digital avec capteur de 139 µm (= 0.139 mm au plan du capteur) et magnification 1.13 est documentée dans une étude réelle. Le constructeur mentionne lui aussi plusieurs capteurs/tailles image selon la configuration (§23).
2. **VÉRIFIÉ dans le miroir épinglé (pas dans les octets Figshare) :** toutes les **41/41** lignes ProMax 2D du CSV ont `0.139` ; 135/135 ProMax with ProTouch ont également `0.139` (§23).
3. **VÉRIFIÉ dans l'article Aariz 2025 primaire :** Table 2 imprimée **`ProMax 2D = 1.139 mm/px`** et **`ProMax with ProTouch = 0.139 mm/px`**, sans attribution patient par patient dans la table.
4. **NON DÉMONTRÉ :** que les 41 ProMax Aariz ont le même capteur 139 µm, la même taille image/export, la même correction d'agrandissement, ou une identité octet-à-octet des JPEG/CSV miroir et ZIP officiel. `1.139` ne doit pas être transformé en `0.139` par simple analogie, ni `1.13` (grossissement sans dimension) confondu avec `1.139 mm/px` (pas pixel). L'absence d'erratum dans les résultats explorés n'est pas preuve d'absence d'erratum.
5. **NE PAS UTILISER EN CLINIQUE :** ni `0.139` ni `1.139` comme ratio effectif de l'image Aariz sans l'original natif et la transformation géométrique vérifiée. Les tests synthétiques 158/158 garantissent seulement le fail-closed pour les chemins évalués, pas une bonne calibration patient.

**Source auteur identifiée pour une vraie réponse de provenance :** article Scientific Data 2025 [DOI 10.1038/s41597-025-05542-3](https://www.nature.com/articles/s41597-025-05542-3), correspondant **Muhammad Moazam Fraz** (`moazam.fraz@seecs.edu.pk`, adresse publique publiée dans l'article). [Dépôt de code des auteurs `manwaarkhd/aariz`](https://github.com/manwaarkhd/aariz), consulté : `dataset.py` calcule le consensus Junior/Senior (§22), mais **aucun CSV `cephalogram_machine_mappings.csv` dans sa racine publique** ; le dépôt `manwaarkhd/cephalometrix` ne contient que README/LICENSE lors de cette passe. Cela ne garantit pas que la racine archive officielle possède les mêmes valeurs que le miroir.

**Questions techniques à adresser au correspondant/auteur des acquisitions (NON ENVOYÉES) :** 
- Confirmez-vous `1.139` versus `0.139 mm/px` **pour ProMax 2D N=41**, et, si nécessaire, la présence d'un erratum ou d'une version officielle corrigée ?
- Le CSV **à l'intérieur du ZIP Figshare v1** contient-il `0.139` pour les mêmes 41 lignes ou `1.139`, et y a-t-il une empreinte SHA-256 de référence de ce CSV et des deux cas de test ?
- Pour les cas `cl5lc0isd1298072u53z31emu` (ProMax 2D) et `cl6cc2n5k405307716g0393xo` (Veraviewepocs 2D), fournissez **modèle/capteur**, image native ou métadonnées de calibration, dimensions et toute conversion/rotation/resize de l'original vers le JPG distribué, ainsi que la définition précise de `pixel_size` (capteur, export, plan médio-sagittal, agrandissement).
- Une règle physique valide ou un champ DICOM `PixelSpacing/ImagerPixelSpacing` suffit-il pour vérifier chaque export ? Si oui, fournissez la méthode et le contrôle appliqués. Aucun export patient privé requis dans une correspondance initiale.

**Limitations de l'environnement :** nouvel essai direct réseau conteneur `api.figshare.com`, `ndownloader.figshare.com` et `github.com` : **DNS getaddrinfo failed** ; aucun octet du ZIP officiel (~2.1 GB) ne peut être lu, aucun hash membre vérifié. Le miroir et la revue documentaire ne remplacent pas le ZIP natif.

**POST / NON-GO maintenu :** Source indépendante PRO MAX 139 µm et grossissement 1.13 **VERIFIED pour la cohorte Danz uniquement** ; correspondance avec Aariz **NOT_VERIFIED**, aucune modification de méthode en mm. **HOLD-Z-ORIENTATION** + **HOLD-MCNAMARA-SCALE** restent actifs, `clinical_validation_available=false`, PDF final `INCOMPLETE`, Orthodontiste indépendant `NOT_RUN`, **0/10 FUE cabinet**. Aucun code clinique, modèle, moteur, DB, interface, fichier patient, merge ou déploiement modifié. Les CI du prochain HEAD documentaire devront être vérifiées par SHA exact avant de les appeler « green ».

**NEXT :** réponse officielle sur la résolution et les modalités d'export, source native DICOM/JPEG + transformation et calibration indépendamment vérifiables, contre-tracé clinique Po/Or/Co/Gn + profil/secteur inférieur Z en aveugle et signature par praticien ; puis seulement batterie de 10 FUE cabinet et décision sur R15/PDF.

**CHANTIER Digital Crown Céphalo V1 · LOT 1/4 OPEN · SOUS-LOT concordance ProMax externe démontrée mais non transposable à Aariz · NEXT réponse auteurs et archive/étalonnage natifs + validation praticien · GOAL lever deux HOLD par preuves, sans substitution par corrélation d'appareils.**

### 25. Audit calculs DC selon contrats FACAD : Tweed/Wits, McNamara, Z ; rattachement 13 tests à R14 — 2026-11-04 (FUE-0, clinique HOLD)

**PRE : commande du praticien orthodontiste.** « Go et si t'as une confusion fais confiance au rapport de Facad ». On accepte la documentation officielle **FACAD 3.14.1.1111** déjà étudiée comme référence **pour la formule, les noms, l'ordre des arguments et le sens des variantes *FACAD***. On **n'invente pas** que la variante du logiciel équivaut nécessairement à l'article historique Jacobson/McNamara/Merrifield. Les points sont fournis par les poids de notre modèle actuel ; pas de réentraînement, audit de localisation point par point ou recherche Aariz. Baseline [PR #1208](https://github.com/hraaaaf/Digital_crown/pull/1208) OPEN/DRAFT, HEAD initial `871de97692cd72fb619f18d3ae663e0edad8cb27`, [R14 #41890253795](https://github.com/hraaaaf/Digital_crown/actions/runs/41890253795) **158/158 PASS en 9,82 s** avec 7 workflows applicables SUCCESS et M6-I SKIPPED. Le présent chapitre suit les §§1–24 du **même** canonique, sans créer un second registre.

**1. Tweed/Wits — définition directe FACAD :** [audit source-locké `CEPHALO_LOT08_TWEED_FACAD_GAP_RESOLUTION.md`](https://github.com/hraaaaf/Digital_crown/blob/871de97692cd72fb619f18d3ae663e0edad8cb27/docs/audits/CEPHALO_LOT08_TWEED_FACAD_GAP_RESOLUTION.md) + [contrat machine versionné `ortho_lot08_tweed_facad_gap_resolution_v1.json`](https://github.com/hraaaaf/Digital_crown/blob/871de97692cd72fb619f18d3ae663e0edad8cb27/docs/audits/schemas/ortho_lot08_tweed_facad_gap_resolution_v1.json) :
- `OLa = Mid-point(Is,Ii)` : **milieu des points incisifs supérieur/inférieur** ; `OLp` est un **point postérieur à placer explicitement**, non un point automatiquement deviné des poids.
- `OL = Line(OLp,OLa)`, sens sérialisé **OLp → OLa**.
- `Wits = ProjLine(OL,B,A)`, déplacement signé sérialisé **B → A**, projeté le long de ce `OL`. Ne pas inverser les arguments pour faire coïncider arbitrairement le signe.
- `OL/FH = Angle2ln(FH,OL)`, `FH = Line(P,Or)` avec `P` du vendor = Porion : c'est le **cant du plan vendor**, non la preuve automatique d'une équivalence historique stricte Downs.
- L'ancien `Wits_Appraisal` et ses repères `Occ_Ant/Occ_Post` sont **QUARANTINED** ; aucun alias à `M_FACAD_TWEED_WITS_BISECTED_OL_MM_V1`, aucune norme FACAD promue à la classification patient, et pas de mesure vendor `AVAILABLE` sans `OLp_Facad_Tweed` réellement saisi/source-bound et ratio physique prouvé. Le moteur [`cephalo_engine.py`](https://github.com/hraaaaf/Digital_crown/blob/871de97692cd72fb619f18d3ae663e0edad8cb27/backend/services/cephalo_engine.py) ne produit actuellement pas de Wits ; ce n'est **pas** un calcul à déclarer validé.

**2. McNamara — liens et différences explicites :** [audit FACAD McNamara](https://github.com/hraaaaf/Digital_crown/blob/871de97692cd72fb619f18d3ae663e0edad8cb27/docs/audits/CEPHALO_LOT08_MCNAMARA_FACAD_GAP_RESOLUTION.md) + [contrat source-locké](https://github.com/hraaaaf/Digital_crown/blob/871de97692cd72fb619f18d3ae663e0edad8cb27/docs/audits/schemas/ortho_lot08_mcnamara_facad_gap_resolution_v1.json) :
- `LAFH` FACAD = **ANS–Me**, même famille et repères que le segment numérique canonique `M_ANS_ME_MM_V1`, sous réserve de calibration valide.
- `Max-Mand diff = Co–Gn - Co–A` : même relation algébrique mais **Co FACAD = « Condyle, posterior point »**, tandis que **Co_anatomic DC = Condylion postérosupérieur**. **Ne pas déclarer équivalence des valeurs** ou aliaser `M_CO_GN_MINUS_CO_A_MM_V1` tant que l'identité du repère n'est pas résolue.
- `Is-A = ProjLine(FH,A,Is)` : le bord incisif n'est pas la surface coronaire exigée par la construction stricte McNamara ; `Ii to A-Pog = Dist3p(Pog,A,Ii)` avec `changeRightLeft=true`, ce n'est pas non plus `L1_facial_surface`. Respect du signe, de l'ordre et de la famille *edge* au lieu du mauvais alias *surface*.
- `Nasolabial = Angle3p(SN,MS,Ls)` centré sur SN (ordre / rotation FACAD), et `Ls Cant = Angle2ln(Ls-N,N-perp)` : ces variantes ne sont pas automatiquement les méthodes McNamara ou les champs legacy de DC. Les audits R8 existants vérifient l'euclidien × ratio pour `Co–A`, `Co–Gn`, `ANS–Me`, et le fail-closed en absence de calibration, **pas la parité FACAD même-radio**.

**3. Merrifield Z — écart déterministe côté DC, source FACAD insuffisante pour corriger :**
- [`cephalo_tweed_merrifield_geometry.py`](https://github.com/hraaaaf/Digital_crown/blob/871de97692cd72fb619f18d3ae663e0edad8cb27/backend/services/cephalo_tweed_merrifield_geometry.py) calcule `_axis_angle_deg` = `min(_ray_angle_deg,180-_ray_angle_deg)`. La sortie de `merrifield_z_angle_deg_v1` est donc **toujours dans [0°,90°]**.
- Exemple **entièrement synthétique** : `Po=(0,0)`, `Or=(10,0)`, `Pog_soft=(0,10)`, `Ls_soft=(-5,15)`, `Li_soft=(-6,15)` ; direction FH vers +x, lèvre supérieure sélectionnée, angle des **rayons** = **135°**, code retourne **45°** par pliage. C'est une perte d'information de secteur démontrée mathématiquement, **pas une règle de diagnostic/erreur clinique déjà tranchée**.
- Le mapping FACAD [`ortho_lot08_facad_dc_existing_protocol_mapping_v1.json`](https://github.com/hraaaaf/Digital_crown/blob/871de97692cd72fb619f18d3ae663e0edad8cb27/docs/audits/schemas/ortho_lot08_facad_dc_existing_protocol_mapping_v1.json) classe le `Z` vendor vers `M_MERRIFIELD_Z_FH_DEG_V1` en **`CANDIDATE_GEOMETRY_REVIEW`** : il ne contient **pas** un oracle numérique direct FACAD du secteur de l'angle supérieur à 90°. Par la règle « confiance au rapport FACAD », **le rapport commande de ne pas prétendre cette équivalence**. Le Workbench rend déjà « Merrifield · orientation non certifiée ». **HOLD-Z-ORIENTATION reste actif ; ne pas patcher la formule en choisissant un secteur non documenté.**

**4. Exécution de tests accrue, sans logique médicale modifiée :** l'actuelle CI [`.github/workflows/ceph-v1-r14-review-receipts.yml`](https://github.com/hraaaaf/Digital_crown/blob/871de97692cd72fb619f18d3ae663e0edad8cb27/.github/workflows/ceph-v1-r14-review-receipts.yml) exécutait 158 tests mais **pas les 13 tests FACAD déjà écrits** :
- [`test_cephalo_lot08_tweed_facad_gap_contract.py`](https://github.com/hraaaaf/Digital_crown/blob/871de97692cd72fb619f18d3ae663e0edad8cb27/backend/tests/test_cephalo_lot08_tweed_facad_gap_contract.py) — **6 tests** : ordre OL/ProjLine B→A, OLp manuel, anti-alias legacy, distinction Downs/Jacobson, normes non promues, parité même-radio non revendiquée.
- [`test_cephalo_lot08_mcnamara_facad_gap_contract.py`](https://github.com/hraaaaf/Digital_crown/blob/871de97692cd72fb619f18d3ae663e0edad8cb27/backend/tests/test_cephalo_lot08_mcnamara_facad_gap_contract.py) — **7 tests** : Co identitaire distinct, ANS–Me, bords incisifs vs surfaces, ordre des arguments et signe, tissus mous, activation clinique bloquée.
- **Nouveau câblage :** inclusion de ces deux **fichiers préexistants** dans le pytest R14 + les filtres de déclenchement push/PR correspondants. Aucune modification de ces tests, du code métier ou de leurs manifestes. **171 PASS est l'attendu mathématique (158+13), et non un résultat annoncé avant les logs du nouveau HEAD.** Ce sont des **tests de contrat/documentation**, pas une comparaison de valeurs FACAD/DC sur la même image clinique ni des FUE réelles. Le test de moteur R6 actuel continue de couvrir la géométrie DC sans prétendre résoudre le HOLD-Z.

**5. Prochaine décision produit bornée :** trancher par l'orthodontiste le choix de référence *Jacobson strict* ou *variante Wits FACAD avec OLp manuel* (privilégier FACAD pour la variante demandée), conserver la distinction condylienne FACAD vs DC, contrôler l'angle Z sur une situation géométrique explicitement orientée avant toute correction versionnée ; puis mesurer FMA/IMPA/FMIA, SNA/SNB/ANB, les mm **uniquement après calibration source-bound**, et vérifier le parcours patient local jusque PDF **INCOMPLETE** tant que clinique non approuvée. Les anciens tests de refus R14 restent FUE-0 ; **0/10 FUE cabinet** réalisées.

**POST / STOP :** un seul canonique du lot augmenté, un workflow CI ajusté, **aucun code de calcul**, norme, IA, UI, DB, patient, PDF, modèle ou règle diagnostique modifié, aucun merge/déploiement. `HOLD-Z-ORIENTATION` / `HOLD-MCNAMARA-SCALE`, `clinical_validation_available=false`, PDF `INCOMPLETE`, PR DRAFT maintenus. Relecture du HEAD final et logs R14 obligatoire avant verdict de CI.

**CHANTIER Digital Crown Céphalo V1 · LOT 1/4 OPEN · SOUS-LOT audit de calculs DC par contrats FACAD + 13 tests existants réintégrés · NEXT CI exact SHA, puis oracle du Z orienté, calibration réelle et 10 FUE cabinet · GOAL sécuriser les conventions et éviter les fausses équivalences numériques.**

### 26. Passage d'oracles numériques déterministes Wits FACAD / DC McNamara / secteur Z — 2026-11-04 (CANDIDAT NON CLINIQUE)

**PRE** — HEAD d'entrée `8c62465385e1adde387eea89d543891e7f806510`, PR Draft #1208. Décision praticien : sources FACAD validées, ne plus contrôler leur provenance. Audit du comportement Digital Crown uniquement ; un oracle purement mathématique ne valide ni le landmark IA ni l'étalonnage natif. Le test des 13 contrats R14 (171/171 PASS) était principalement documentaire et ne constituait aucune comparaison numérique directe FACAD↔DC.

**Implémentation isolée, sans activation :** `backend/services/cephalo_facad_wits_candidate.py` ajoute une fonction déterministe **candidate uniquement**, `facad_tweed_wits_bisected_ol_mm_candidate_v1`, avec `OLa=milieu(U1_incisal,L1_incisal)`, direction `OLp→OLa` et projection signée `B→A` ; multiplication par `mm_per_pixel` **seulement** quand une valeur explicite positive finie est fournie. `OLp` est une entrée obligatoire, jamais devinée. Refus de géométrie absente/dégénérée et de ratio manquant/invalide. Ce module n'est relié à aucun registre de mesures cliniques, API, UI, DB, FUE ni PDF ; **pas de Wits activé et aucune parité directe avec FACAD sur un même cliché revendiquée**.

**Contrat CI ajouté :** `backend/tests/test_cephalo_facad_dc_numeric_oracles.py` : +16 cas pytest réellement collectés et exécutés (signe Wits positif/négatif/nul ; orientation oblique/miroir ; redimensionnement vs étalonnage ; 9 refus paramétrés ; non-enregistrement ; fonctions McNamara DC réellement appelées sur oracle 3-4-5 + rotation/resize ; collision réelle du Z V1 sur valeurs aiguë/obtuse). L'oracle Z décrit une collision, **pas un correctif autorisé**. Aucun changement de `merrifield_z_angle_deg_v1`, de version de méthode existante, du schéma de calibration ou de la logique clinique.

**Gates stricts :** `HOLD-Z-ORIENTATION`, `HOLD-MCNAMARA-SCALE` et Wits vendor `CANDIDATE_ONLY` ; pas de norme FACAD, aucune validation/activation R11/R13/R15 ; `clinical_validation_available=false`, PDF `INCOMPLETE`, 0/10 FUE cabinet. Prochaine preuve après CI : oracles numériques exportés d'un même tracé FACAD et Digital Crown sur instance locale autorisée, avec mm/pixel natif documenté et arbitrage secteur Z signé. Aucun merge ni déploiement.

**POST exécuté sur le HEAD calculs `54106b4966f9d2db0ef4be6d5fcad507c7c110be` :** [GitHub R14 #41906116202](https://github.com/hraaaaf/Digital_crown/actions/runs/41906116202), job #126841104217, checkout de `54106b4` observé dans les logs, **187/187 PASS en 10,07 s**, 0 échec, 0 skip pytest dans la suite. Les 16 nouveaux tests passent réellement sur les moteurs/candidat. Les 7 workflows applicables de ce HEAD sont SUCCESS ; M6-I SKIPPED hors scope. Quatre chemins changés, zéro migration ou activation clinique. Correction de comptage documentaire +17→+16 dans ce POST ; la CI de ce changement documentaire seul doit être contrôlée à son propre SHA avant prétendre au GREEN exact-HEAD final. La réussite ne valide toujours ni mm/pixel natif ni parité numérique avec un même cliché FACAD.

### 27. Reprise 2026-11-04 — R14 confirmé au dernier HEAD et gate de parité numérique same-trace

**PRE / base exacte :** [PR Draft #1208](https://github.com/hraaaaf/Digital_crown/pull/1208), HEAD `b1bb278ec61ea43d36e20959ffbf468009f81e38`. [R14 #41906657229](https://github.com/hraaaaf/Digital_crown/actions/runs/41906657229), job #126843010149 : checkout exact `b1bb278e` vu dans les logs ; **187 passed in 9.00s**, aucune erreur pytest ni skip dans ce run. Les **7 workflows applicables SUCCESS**, M6-I seul SKIPPED hors scope. Aucun merge/déploiement. Les 16 tests ajoutés demeurent des oracles **synthétiques** : ils prouvent des calculs déterministes DC, non des résultats émis par FACAD sur ce même cliché.

**Audit des entrées déjà disponibles, sans rouvrir FACAD :**
- Contrats FACAD de construction et d'ordre des arguments : **PROJECT_LOCKED**, validés par décision du praticien ; ne pas chercher une autre provenance.
- [Manifeste direct de parité existant](https://github.com/hraaaaf/Digital_crown/blob/b1bb278ec61ea43d36e20959ffbf468009f81e38/docs/audits/schemas/ortho_lot08_facad_ricketts_direct_parity_evidence_v1.json) : `status=DIRECT_DEFINITION_OBSERVED`, **`evidence_records=[]` et `parity_rows=[]`**, deux profils `UNOBSERVED`. Il concerne Ricketts 32F/13F, pas une preuve Wits ou McNamara. Dossier `docs/audits/evidence/facad` **absent de ce HEAD** (API 404). [Validateur source existant](https://github.com/hraaaaf/Digital_crown/blob/b1bb278ec61ea43d36e20959ffbf468009f81e38/audit/cephalo_lot08_facad_parity_validate.py) : contrôle les SHA, les exports directs et l'identifiant même-tracé ; ne pas créer un second validateur Ricketts.
- [Benchmark Notion historique](https://app.notion.com/p/40377c66336281d5bdacdffd1cff0334) : **0/6 exports authentifiés** et aucune parité numérique, état compatible avec la lecture actuelle du manifeste. Aucun export patient/valeur native Wits-McNamara-Z découvert dans cette passe. **Same-trace FACAD↔DC = NOT_RUN / EVIDENCE_MISSING**, pas FAIL du moteur et pas PASS de concordance.

**Données minimales requises pour la prochaine passe numérique, à traiter uniquement en environnement local autorisé et sans média/donnée patient sur GitHub/Notion :**
1. **Identité du tracé** non nominative et identique FACAD/DC, version FACAD, version DC, empreinte SHA-256 des fichiers d'export originaux, date, système de coordonnées, transformations/crop/rotation et orientation prouvée.
2. **Wits vendor :** coordonnées non nominatives `OLp` *placé manuellement*, `Is/U1_incisal`, `Ii/L1_incisal`, `A`, `B`, valeur FACAD exportée, signe et unité. Vérifier `OLa=(Is+Ii)/2`, ligne `OLp→OLa`, projection `B→A`, et valeur DC candidate. Ne jamais substituer `Occ_Ant/Occ_Post`.
3. **McNamara :** coordonnées `Co_FACAD_posterior`, `Co_anatomic_DC` documenté distinct, `A`, `Gn`, `ANS`, `Me` ; valeurs FACAD `Co-A`, `Co-Gn`, `ANS-Me` ; source réelle `mm/pixel`, magnification, chaîne d'export/redimensionnement et comparabilité physique. L'égalité de valeurs sans identité des points et échelle **n'est pas une parité certifiée**. Ne pas appliquer `/1.08` par défaut.
4. **Z :** référence d'orientation et choix du secteur du clinicien, points `Po`, `Or`, `Pog'`, `Ls`, `Li`; valeur exportée et construction indépendante (secteur >90° nécessaire). Référence FACAD `Z` ne fournit pas actuellement de correctif secteur autorisé : ne pas modifier `merrifield_z_angle_deg_v1` ni les IDs persistés.
5. **Critère de succès à établir avant lecture du résultat :** comparateur à unités et arrondis explicites, delta chiffré par mesure, refus par entrée absente ou calibrage invérifiable, statut `NUMERIC_MATCH` / `DIFFERENT` / `NOT_COMPARABLE` par mesure, et validation clinique humaine séparée.

**POST :** audit READ-ONLY du moteur et des preuves existantes ; **pas de modification de calcul, d'activation clinique, de droits patient, de DB, d'UI ou de PDF** dans cette passe. La seule modification est le présent reçu dans le **canonique unique**. Après son commit documentaire, confirmer le nouveau HEAD puis la CI de ce HEAD avant de lui attribuer `187/187 PASS`. Les tests numériques de code restent vérifiés sur `b1bb278ec61ea43d36e20959ffbf468009f81e38` ; cette conclusion ne sera pas transposée sans preuve.

**Gates maintenus :** `HOLD-Z-ORIENTATION`, `HOLD-MCNAMARA-SCALE`, Wits `CANDIDATE_ONLY`, `clinical_validation_available=false`, PDF `INCOMPLETE`, FUE cabinet **0/10**. Prochaine action conditionnée à **un export numérique direct autorisé du même tracé**, et non à une nouvelle recherche des sources FACAD.

### 28. PRE — 2026-11-04 — FUE-0 comparateur local FACAD/DC, hors runtime clinique

**BASE VERROUILLÉE** : PR #1208 DRAFT `a25255e41c9a084b5026cadd6b64fce394b60f43`, [R14 #41915508578](https://github.com/hraaaaf/Digital_crown/actions/runs/41915508578) **187/187 PASS**, 7 workflows applicables SUCCESS, M6-I SKIPPED. Sources FACAD déjà validées. Le §27 confirme **0 export numérique authentifié du même tracé** et aucune calibration native prouvée ; `same_trace_numeric_parity_observed=false`.

**GOAL et scope PRE :** ajouter un comparateur **strictement local et expérimental** de valeurs mm FACAD exportées contre résultats calculés par les fonctions DC existantes Wits candidate / McNamara, avec identité même-image, déclaration de calibration source-bound, coordonnées/frame, référence condylienne vérifiée, valeur et tolérance entrées explicitement. Sortie uniquement numérique et statut `NUMERIC_MATCH` / `DIFFERENT` / `NOT_COMPARABLE` ; jamais `CLINICALLY_VALIDATED` par un test synthétique. Angle Z toujours `HOLD-Z-ORIENTATION`. Tests de cas positifs/négatifs synthétiques via R14, aucun patient/fixture réelle sur GitHub ni Notion, aucun export lu dans CI ; pas de second validateur Ricketts, API/UI/DB/PDF/registre inchangés. POST avec preuve finale uniquement une fois les tests exécutés.

**POST d'implémentation candidate — FUE-0 NON CLINIQUE (2026-11-04) :**
- `audit/cephalo_v1_facad_dc_local_compare.py` est un comparateur **CLI local seulement**. Il appelle **les moteurs DC existants** `facad_tweed_wits_bisected_ol_mm_candidate_v1`, `mcnamara_co_a_mm_v1`, `mcnamara_co_gn_mm_v1`, `mcnamara_ans_me_mm_v1` ; ne lance jamais FACAD, n'écrit aucun fichier, ne transmet rien, n'expose ni image, ni identifiant de cas, ni coordonnées dans sa sortie et n'active aucune mesure clinique.
- Contrat JSON local `schema_version=CEPH_V1_FACAD_DC_LOCAL_SAME_TRACE_V1`, entrées `facad` et `digital_crown` avec `same_trace_case_id` strictement identiques, `source_image_sha256` identique, `export_sha256` distincts déclarés, `version` des deux sources, `facad.unit=mm`, `facad.values_mm={Wits,Co-A,Co-Gn,ANS-Me}`, `digital_crown.landmarks_px`, `coordinate_frame_verified=true`, `calibration={verified:true,source:<evidence locale>,mm_per_pixel:<ratio natif>}`, `manual_olp_verified=true`, `co_reference_equivalence_verified=true` **uniquement si l'opérateur peut attester les identités anatomiques** et `tolerance_mm` prédéfinie avant mesure. Ces champs sont des **DÉCLARATIONS** : le CLI ne prouve pas qu'un fichier FACAD réel est source des valeurs et ne valide pas un certificat numérique. L'exigence de SHA de l'image strictement identique exige un contrôle explicite du flux d'image/crop en local, sans conversion silencieuse.
- Usage sur poste autorisé, pas en CI avec de vraies données : `python -m audit.cephalo_v1_facad_dc_local_compare --input-json /chemin/local/prive/mesures.json`. Ne **jamais** ajouter le JSON du patient dans Git/CI/Notion, même anonymisé de manière réversible. La sortie a les statuts `NUMERIC_MATCH`, `DIFFERENT`, `NOT_COMPARABLE` par mesure, `delta_mm=DC−FACAD`, scope `LOCAL_DECLARED_VALUES_ONLY_NOT_CLINICALLY_VALIDATED`, `same_trace_numeric_parity_observed=false` de manière invariante.
- `Z` n'est **jamais** comparé dans ce CLI : `NOT_COMPARABLE/HOLD_Z_ORIENTATION` jusqu'à décision clinique sur le secteur. Les valeurs `Co-A`/`Co-Gn` restent refusées si équivalence du `Co` FACAD et `Co_anatomic` DC non attestée ; `ANS-Me` et `Wits` peuvent rester comparables indépendamment de ce blocage.
- Nouveaux tests **synthétiques seulement** `backend/tests/test_cephalo_v1_facad_dc_local_compare.py`, filtres workflow R14 modifiés pour son lancement, suite exacte à confirmer dans les logs du nouveau HEAD. FUE-0 outil local testable, **0/10 FUE patients**, sans merge/déploiement. Aucune donnée FACAD réellement exportée, aucune calibration native ou secteur Z médical validé ; source FACAD acceptée sans réenquête.

**Gate toujours ouvert :** `HOLD-MCNAMARA-SCALE`, `HOLD-Z-ORIENTATION`, Wits `CANDIDATE_ONLY`, `clinical_validation_available=false`, PDF `INCOMPLETE`. **NEXT** : lancer cet outil avec un **vrai export même-cliché en local** et vérifier les preuves par le praticien. Ne pas interpréter les tests synthétiques comme validation FACAD↔DC.

**Perfection Pass numérique adversariale (même passe, avant la CI finale) :** revue de garde-fous sur **nombres finis mais extrêmes**. Correction isolée de `_number` : refuser un entier JSON au-delà de la plage float sans `OverflowError`. Correction du delta `DC−FACAD` : tout `inf` dû à une soustraction de valeurs finies opposées retourne `NOT_COMPARABLE/NUMERIC_DELTA_NONFINITE`, pas une sortie JSON non standard ni un faux `NUMERIC_MATCH`. Deux tests synthétiques négatifs ajoutés. Pas de changement de Wits candidate, McNamara, Z, normes, API ou règles cliniques. Le résultat sera prouvé uniquement par la CI sur le HEAD post-correctif.

### 29. 2026-11-04 — REVUE SCIENTIFIQUE EXTERNE ET DÉCISION PRATICIEN : FORMULES CONSERVÉES, FUE CABINET APRÈS BUILD

**PRE — décision du praticien :** la littérature scientifique publique doit trancher le calcul ; si elle le confirme, on le **conserve sans nouvelle campagne d'exports FACAD numérique avant l'intégration**. L'application doit d'abord être mergée puis construite en environnement de test ; le praticien réalisera les essais cliniques ensuite. Sources vendor FACAD spécifiques : **déjà validées**, aucune nouvelle enquête sur leur provenance. HEAD d'entrée `a592949eb40e843e390948788913ffae3bf767f8`, [R14 #41917940837](https://github.com/hraaaaf/Digital_crown/actions/runs/41917940837) 211/211 PASS, huit workflows applicables SUCCESS, M6-I SKIPPED. Revue circonscrite à **Wits candidat, McNamara linéaire et Merrifield Z** : ce rapport **n'est pas** un audit de tous les protocoles orthos de l'application.

**MATRICE SCIENCE ↔ CODE (recherches externes, pas résultat d'export FACAD) :**

1. **Wits / projection : CONFORME POUR LA GÉOMÉTRIE, VARIANTE VENDOR DISTINCTE.** Jacobson (1975) décrit les projections perpendiculaires de A et B sur le plan occlusal, AO–BO, avec signe positif quand AO est antérieur à BO. Le code `facad_tweed_wits_bisected_ol_mm_candidate_v1` réalise la projection scalaire de **B→A** sur le vecteur unitaire **OLp→OLa** × mm/pixel. Cette formule est une réalisation mathématique correcte de la différence des projections **si la direction est postérieur→antérieur** ; le plan vendor `OLa=milieu(Is,Ii)`, `OLp` manuel est la **construction FACAD source-lockée**, et **NON** une revendication d'identité avec le plan occlusal fonctionnel original de Jacobson. Les études documentent une sensibilité à la définition du plan et à la répétabilité ; ne jamais transporter des normes d'une variante à l'autre.
   Sources : [Jacobson 1975, Am J Orthod, DOI 10.1016/0002-9416(75)90065-2](https://pubmed.ncbi.nlm.nih.gov/1054214/) ; [Haynes & Chau 1995, DOI 10.1016/S0889-5406(95)70108-7](https://pubmed.ncbi.nlm.nih.gov/7771370/) ; [comparaison de plans de référence (2001)](https://pubmed.ncbi.nlm.nih.gov/11298316/). **Action : KEEP AS-IS, CANDIDATE_ONLY**, sans auto-activation Wits ni nouvelle équivalence FACAD↔Jacobson.

2. **McNamara : GÉOMÉTRIE DES TROIS DISTANCES CONFIRMÉE, ÉCHELLE CONDITIONNELLE.** Co–A = longueur effective médiofaciale, Co–Gn = longueur mandibulaire effective, ANS–Me = hauteur faciale antérieure inférieure ; `mcnamara_*_mm_v1` calcule distance euclidienne × rapport mm/pixel positif. Conforme en formule **si repères homologues et calibration native correcte**. La littérature décrit Co comme un point postérosupérieur condylien et l'identification de Co comme variable ; **ne pas équivaloir automatiquement** un `Co` vendor de définition différente au `Co_anatomic` DC. La correction de magnification varie avec l'appareil / situation : `mm_per_pixel` doit provenir d'une calibration physique documentée ; ne jamais imposer un facteur universel.
   Sources : [McNamara 1984, Am J Orthod, DOI 10.1016/S0002-9416(84)90352-X](https://pubmed.ncbi.nlm.nih.gov/6594933/) ; [définitions des repères/longueurs Co–A, Co–Gn, ANS–Me, 2026](https://journals.sagepub.com/doi/10.1177/03015742261462317) ; [Co et sa reproductibilité, étude landmarks](https://pubmed.ncbi.nlm.nih.gov/11168282/) ; [magnification et calibration instrumentale](https://pubmed.ncbi.nlm.nih.gov/31793469/). **Action : KEEP AS-IS** pour le moteur, conserver le garde-fou `HOLD-MCNAMARA-SCALE` pour sortie clinique avant calibration vérifiée, et distinguer le condylion vendor du DC.

3. **Z Merrifield : CONSTRUCTION ANATOMIQUE CONFIRMÉE, OPÉRATEUR ANGULAIRE V1 NON PLEINEMENT JUSTIFIÉ.** Merrifield décrit la droite du pogonion cutané à la lèvre la plus proéminente et son angle avec Frankfort. Le code implémente bien cette **sélection de lèvre/ligne** ; toutefois `_axis_angle_deg=min(raw, 180−raw)` ramène par définition tous les secteurs obtus en angles aigus : les tests R14 ont reproduit la collision `63.43°` versus `116.57°`. La littérature consultée **ne justifie pas** de rabattre systématiquement tous les secteurs sur `0–90°`. **Action : garder le code V1 historique inchangé et versionné, mais NE PAS activer ni revendiquer sa conformité clinique complète.** Le bridge canonique possède déjà `MERRIFIELD_Z_ANGLE_DEG_V1=UNMAPPED_CANONICAL_ID` et la sortie clinique reste bloquée ; ne pas retirer le verrou pour accélérer le build.
   Sources : [Merrifield 1966, Am J Orthod, DOI 10.1016/0002-9416(66)90250-8](https://www.sciencedirect.com/science/article/abs/pii/0002941666902508) ; [revue scientifique ligne de profil / Z, 2021](https://pmc.ncbi.nlm.nih.gov/articles/PMC8402232/) ; [définition intersection inférieure Frankfort, revue](https://pmc.ncbi.nlm.nih.gov/articles/PMC9444627/). **Statut : `HOLD-Z-ORIENTATION` maintenu, aucun correctif spéculatif ni changement d'ID.**

**POST — DÉCISION DE SÉQUENÇAGE APPLICABLE AU CHANTIER, sans inventer validation clinique :**
- **La revue de formules Wits/McNamara est clôturée sur les limites ci-dessus : ne pas relancer des recherches de provenance ni imposer d'exports FACAD same-trace comme condition de conservation du code ou de préparation d'un build technique.**
- **La preuve de validité de la formule n'est pas une certification de mesure clinique** : qualité des landmarks, respect de la calibration native, secteur Z et résultat PDF diagnostique restent des critères applicatifs distincts. Conserver `clinical_validation_available=false`, PDF `INCOMPLETE`, Wits `CANDIDATE_ONLY`, `HOLD-MCNAMARA-SCALE` et `HOLD-Z-ORIENTATION`.
- **Séquence recommandée par décision du praticien** : figer les moteurs sans refactor ; vérifier l'intégration du code sans activation de Z, Wits ou d'unités MM non étalonnées ; **build de test sur un environnement local autorisé (aucun déploiement Vercel)** ; puis **10 FUE cabinet exécutées par le praticien** et remontée d'anomalies réelles uniquement. Des FUE humains avant build ne sont donc plus présentés comme condition préalable à l'intégration d'un composant **isolé NON CLINIQUE**, mais demeurent impératifs avant tout statut `CLINICAL_VERIFIED`/mise en exploitation clinique.
- **Non-gate de revue ≠ autorisation automatique de merge d'une stack entière** : la PR #1208 porte **104 commits / 40 fichiers** contre une base `feat/ceph-v1-l3-practitioner-gate-20261102` (et non master). Une décision d'intégration doit examiner l'ensemble du diff, le bon destinataire et la sécurité des sorties patient ; la présente preuve **ne valide pas** les autres 39 chemins.
- Aucune formule, token de thème, méthode, DB, UI, PDF, poids IA ni norme modifiés dans ce passage **documentaire**. PR non mergée, pas de déploiement. Un succès CI du nouveau commit documentaire n'est attribué qu'à son SHA exact après contrôle.

**GOAL :** conserver les calculs étayés, éviter les contrôles redondants, accélérer un build **testable sans revendication clinique** ; arbitrer Z et les FUE cabinet **après build** à partir d'essais observés.

### 30. PRE/POST — 2026-11-04 — AUDIT D'INTÉGRATION DE LA STACK #1208 : isolement tenant des reçus cliniques

**PRE audité :** [PR #1208](https://github.com/hraaaaf/Digital_crown/pull/1208) OPEN/READY, HEAD d'entrée `873f0b4fc653a92c8266552fac908f096b2ba80c` ; base `feat/ceph-v1-l3-practitioner-gate-20261102` `5aacab15c3837d7d0d76fa575ab02acc68e6752c`, 105 commits / 40 fichiers. La CI R14 211/211 et la R18 (audit+visuel) sont SUCCESS, M6-I SKIPPED hors scope, zéro review GitHub enregistrée. Revue des 40 patches et inspection des routes R11/R12/R13/R14, CAS JSON SQLite/PG, audit de staging, calibration, Wits/McNamara, UI tokenisée et projection PDF : les chaînes clinicien/révision/provenance restent confinées et PDF `INCOMPLETE` avec source registries vides. Aucune preuve des 10 FUE cabinet (reportés volontairement après build local par décision du praticien).

**Trouvaille corrigeable et importante avant merge :** `read_blocker_review_receipts` de `backend/services/cephalo_r14_review_receipt.py` ne bornait pas le SELECT AuditLog par `employer_id` alors que les lectures R11/R13/R14 le font. La route GET vérifiait l'accès patient, mais les reçus conservés pouvaient provenir d'un tenant différent pour le même identifiant de ressource après une réaffectation de contexte. Le risque est une fuite d'historique d'audit, **pas** une autorité clinique.

**POST correctif minimal :** la lecture accepte le `tenant_id` obtenu de `current_user.get_employer_id()` par la route et ajoute une égalité explicite `AuditLog.employer_id == tenant_id` aux critères SQL ; aucun nom ou identifiant fourni par le client n'est utilisé pour ce filtre. Trois anciens appels de test adaptés ; nouveau cas négatif **vraie SQLite en mémoire**, avec deux lignes AuditLog même patient/même analyse/même auteur, mais employeurs distincts ; la lecture du cabinet 7 ne doit recevoir qu'un reçu du cabinet 7, et le cabinet 9 aucune ligne. **+1 test pytest** attendu en R14 ; résultat de CI non revendiqué avant exécution exacte.

**Gates inchangés :** Wits `CANDIDATE_ONLY`, `HOLD-MCNAMARA-SCALE`, `HOLD-Z-ORIENTATION`, `clinical_validation_available=false`, PDF `INCOMPLETE`, 0/10 FUE cabinet. Aucun nouvel élément patient, LLM, norme, formule, UI, DB, migration ou déploiement. Fusion autorisée uniquement vers la **branche base de la PR** après contrôles CI et revue du diff ; aucune fusion sur master. Build TEST local ou workflow de CI identifié, jamais déploiement Vercel. **Next** : exécuter R14+R18 au nouveau SHA, inspecter preuves de sécurité/privacy/CI, puis décision de merge contrôlé et build.

### 31. PRE/POST — 2026-11-04 — build FRONTEND TEST exact HEAD non déployé

**PRE :** utilisateur a ordonné de procéder à la revue/merge technique puis au build de test, mais aucun déploiement Vercel ni installation cabinet. Le `README.md` et `docs/CABINET_ONPREM_GUIDE.md` distinguent l'UI statique (Vite) du backend FastAPI, et réservent l'installation Windows `DigitalCrown.exe` au circuit `INSTALLABLE_CERTIFIED` sur master avec approbation humaine. Le script existant `frontend/scripts/build-guard.mjs` accepte `build:test`, sortie isolée `dist-test` et évite le `dist` réel du cabinet. L'environnement actuel ne peut pas cloner GitHub (`Could not resolve host github.com`) : aucune compilation locale réelle n'est revendiquée.

**POST implémenté, preuve de CI attendue :** workflow nouveau `.github/workflows/ceph-v1-lot1-isolated-test-build.yml` en mode **NO DEPLOY**, checkout du SHA exact, Node 22, `npm ci`, `npm run build:test`, `VITE_API_URL` vidé pour ne pas figer l'API du cabinet, contrôle JSON du `dist-test/build-manifest.json` et de `index.html`, archive GitHub Actions `ceph-lot1-test-frontend-<SHA>` avec rétention 7 jours. Les déclencheurs couvrent la PR et les pushes sur les deux branches de travail ; aucune donnée patient ou secret n'est fournie en CI.

**Limite de portée :** cet artefact est un **build statique du frontend de TEST**, pas une `DigitalCrown.exe`, pas un backend empaqueté, pas un installateur cabinet, pas une version certifiée et surtout pas une autorisation de déploiement. Un workflow vert prouvera compilation, manifeste et artifact à son SHA, **PAS une validation clinique ou FUE cabinet**. Après intégration, les essais au poste du praticien sont à réaliser dans un environnement autorisé avec données locales; toutes les sorties cliniques sous HOLD restent bloquées. Aucun autre changement de thème/UX/code clinique.

### 32. 2026-11-05 — POST FUSION PR #1208, BUILD TEST POST-MERGE ET VERROU INSTALLABLE

**PRE vérifié** : PR #1208 OPEN/READY à `b7e06d0d504261b99425e1b21a5ef6479652b19b`, 107 commits/41 chemins, base `feat/ceph-v1-l3-practitioner-gate-20261102` @ `5aacab15c3837d7d0d76fa575ab02acc68e6752c`. 9 workflows applicables SUCCESS, R14 212/212 PASS en 10,21 s, R18 audit/visuel SUCCESS, frontend isolé TEST [build #41938317406](https://github.com/hraaaaf/Digital_crown/actions/runs/41938317406) SUCCESS, artifact #13374888972 ; M6-I SKIPPED hors scope. L'utilisateur a donné GO explicite pour merge contrôlé et version de test ; pas d'autorisation Vercel.

**POST FUSION RÉELLE** : [PR #1208](https://github.com/hraaaaf/Digital_crown/pull/1208) = `MERGED`, commit de fusion **`18ef4679c6858a97266d13b092299c276ed4a5f4`**. Ref branche cible `feat/ceph-v1-l3-practitioner-gate-20261102` vérifiée exactement à ce SHA, `master` **non touché** (HEAD lu `a95454459a0f28a25622b420df9ef271053d47b5`). Audit des changements sensible (R11–R14, CAS JSON PostgreSQL/SQLite, routes patient/cabinet, calibration, contrôle PDF, Wits/McNamara/Z, UI token de thème) ; correction critique précédemment intégrée : `AuditLog.employer_id` explicite dans lecture des blocker-review receipts avec test synthétique d'isolation inter-cabinets. Aucune donnée patient réelle, aucune DB, migration ou service cabinet déployés.

**CIRCUIT BUILD TEST** : workflow existant `.github/workflows/ceph-v1-lot1-isolated-test-build.yml`, déclenché à nouveau par le présent document unique sur la **branche cible post-merge**, doit produire `frontend/dist-test` + manifeste SHA et archive `ceph-lot1-test-frontend-<SHA>`. Les conclusions et le SHA seront ajoutés à Notion APRÈS les logs, pas préemptivement. Le fichier canonique **unique par lot** reste celui-ci, aucune deuxième page GitHub pour ce lot.

**BLOCAGE INSTALLER WINDOWS NON CONTOURNABLE** : `docs/CABINET_CERTIFIED_RELEASE_POLICY.md` : il est interdit de transformer un HEAD/branche/artefact CI en EXE installable directement ; `DigitalCrown.exe` / `DigitalCrownSetup.exe` exigent `CODE_CERTIFIED` du HEAD master exact + assets runtime certifiés composés en `INSTALLABLE_CERTIFIED` et vérifications locales avant packaging. Cette PR a été mergée sur une branche de feature, **pas master** ; l'archive TEST contient **uniquement le frontend**, aucun backend encapsulé ni données scientifiques. Ne pas annoncer une version Windows installable tant que le parcours certifié officiel n'est pas accompli, et ne pas demander au praticien de lancer l'artefact dans le cabinet réel.

**HOLD scientifiques inchangés** : `clinical_validation_available=false`, PDF `INCOMPLETE`, Wits `CANDIDATE_ONLY`, `HOLD-MCNAMARA-SCALE`, `HOLD-Z-ORIENTATION`. Les 10 FUE cabinet par le praticien attendent une release locale INSTALLABLE_CERTIFIED ; aucun PASS clinique anticipé.

**NEXT** : confirmer build isolé exact SHA post-merge et CI associées ; préparer séparément la PR cible master pour le pipeline `CODE_CERTIFIED` après revue d'impact générale et approbation, composer ensuite un bundle d'assets runtime certifié sur le poste autorisé, puis seulement TEST cabinet.

**GOAL** : intégration technique prouvée, build de test reproductible, et aucune fausse installation ou validation clinique.

### 33. PRE — 2026-11-05 — PR MASTER CANDIDATE REVIEW, NO MERGE / NO INSTALL

**GO scope** : le praticien demande d'avancer vers CODE_CERTIFIED et un installateur. Le `AGENTS.md` actif sur master (§ Autopilot) exige un **accord distinct pour chaque fusion** : ce GO autorise uniquement **l'ouverture d'une PR DRAFT d'évaluation** pour master, pas son merge, pas la release ni la signature humaine visuelle. La politique `docs/CABINET_CERTIFIED_RELEASE_POLICY.md` interdit de packager une branche ou une archive CI comme `DigitalCrown.exe`.

**PRE branche** : la PR #1208 a été fusionnée vers `feat/ceph-v1-l3-practitioner-gate-20261102` ; HEAD documentaire d'entrée `177b58ba58d3f3f97e89d4aec7d9df14de09f5c0`. `master` = `a95454459a0f28a25622b420df9ef271053d47b5`. Comparaison : **197 commits ahead, 3 behind, 71 chemins**. Les 3 commits master-only concernent des règles/reviewers et le routeur mobile ; aucun écrasement silencieux acceptable. Les PR historiques de couches #1198 et #1206 restent DRAFT et leurs décisions non implicites. Le candidat master est une **stack agrégée** à revue complète, non un cherry-pick validé automatiquement.

**Preuves source** : sur `177b58ba58d3f3f97e89d4aec7d9df14de09f5c0`, 14 workflows applicables SUCCESS + 1 SKIPPED (M6-I hors scope), [frontend test #41940139358](https://github.com/hraaaaf/Digital_crown/actions/runs/41940139358) SUCCESS, artifact #13375936726. R14 sur le code source pré-merge `b7e06d0` 212/212 PASS. Les CI de certification master, PG18, full backend/frontend et sécurité ne sont **pas encore certifiées** sur le candidat agrégé avant la PR ; ne pas interpoler.

**Action PRE limitée** : créer une PR DRAFT vers master pour déclencher les workflows officiels de revue candidate, inspecter diff/conflits, constater BLOCKERS et rendre un verdict `OPEN/READY` ou `BLOCKED` fidèle aux preuves. **Ne pas fusionner master, ne pas lancer certification CODE sur master, ne pas composer assets/EXE, ne pas déployer**. `clinical_validation_available=false`, PDF `INCOMPLETE`, Wits `CANDIDATE_ONLY`, `HOLD-MCNAMARA-SCALE`, `HOLD-Z-ORIENTATION`, 0/10 FUE cabinet restent inchangés.

**GOAL** : construire une chaîne de preuve de candidature master sans confondre compilabilité, certification signée et autorité clinique ; NEXT inspecter CI, approbation visuelle humaine et certification officielle du SHA master après GO séparé.

### 33. POST — 2026-11-05 — PR CANDIDATE MASTER DRAFT #1212 OUVERTE, GATES COMPLETS DÉCLENCHÉS

**Exécution vérifiée** : [PR #1212](https://github.com/hraaaaf/Digital_crown/pull/1212) **OPEN / DRAFT / NOT READY TO MERGE** créée depuis `feat/ceph-v1-l3-practitioner-gate-20261102` vers `master`, commit de branche PRE `3c35e7f2cdafc3bf07d5428fcf47cc6535806e0d`. [Comparaison master...candidate](https://github.com/hraaaaf/Digital_crown/compare/master...feat/ceph-v1-l3-practitioner-gate-20261102) = **198 commits ahead, 3 behind, 71 fichiers**, 7 973 ajouts, 261 suppressions selon GitHub ; `mergeable=true` après recalcul mais `mergeable_state=unstable`, **ce n'est pas une autorisation de fusion**. Le diff inclut de la logique patient/clinique, des PDF et de l'UI ; les PR dépendantes #1198/#1206 sont toujours DRAFT. Aucun autre canonique créé.

**CI précisément observée sur le SHA candidat** : GitHub a lancé la [Cabinet CODE_CERTIFIED candidate regression](https://github.com/hraaaaf/Digital_crown/actions/runs/41987097384) (3 jobs : régression backend complète, tests frontend et build, PostgreSQL 18 rehearsal) ; ils étaient `QUEUED` au relevé initial. Plus de 50 workflows globalement liés au candidat et/ou au push ont été déclenchés ; ne pas les relancer ni prétendre qu'ils sont verts. Les anciennes preuves #1208 et le build frontend isolé restent des preuves partielles sur SHA antérieur, pas un `CODE_CERTIFIED` de master.

**Gate humain réel BLOQUANT** : [UI Human Visual Approval #41987096295](https://github.com/hraaaaf/Digital_crown/actions/runs/41987096295) **FAIL** sur `3c35e7f2cdafc3bf07d5428fcf47cc6535806e0d`, log `Visual gate fails closed: UI changes require explicit visual approval label`. Aucune approbation visuelle du praticien n'est reconstituée ; des captures BEFORE/AFTER au HEAD exact puis l'accord explicite sont nécessaires si l'on veut merger. Le GO utilisateur de préparation n'est **pas** le label d'approbation au sens du workflow trusted.

**Politique installable / assets reconnue** : `backend/scientific_assets.json` liste `cephalo_sota` externe `backend/ai_models/srpose38-tta-1024.onnx` (267 484 931 octets avec SHA-256 épinglé), plus `cephalo_legacy` et `panoramic` externes et non épinglés scientifiquement. Aucune de ces masses de modèles n'a été extraite, uploadée ni recertifiée dans cette passe. Le seul chemin EXE reste `CODE_CERTIFIED` du SHA exact de master → attestation GitHub/Sigstore → bundle assets local de même SHA → `INSTALLABLE_CERTIFIED` → packaging Windows sur machine autorisée. **Aucun binaire Windows certifié, aucune installation et aucun Vercel**.

**GO / NEXT** : candidate DRAFT ouverte et gates demandés ; lire conclusions GitHub sans polling systématique, préparer revue sécuritaire/régression/visuels ; après `REQUIRED` tous verts + preuve humaine, demander un **GO distinct pour merge master**, puis faire certification CODE et composition locale des assets. Les blocages `HOLD-Z-ORIENTATION`, `HOLD-MCNAMARA-SCALE`, Wits `CANDIDATE_ONLY`, `clinical_validation_available=false` et PDF `INCOMPLETE` sont strictement conservés ; **FUE cabinet 0/10**.

**GOAL :** rapprochement master auditable avec preuve GitHub, pas un build Windows fictif.
 
### 34. PRE — 2026-11-05 — correction pré-certification P0/P1, PDF + jsdom + lockfile

**Baseline** : [PR #1212](https://github.com/hraaaaf/Digital_crown/pull/1212) OPEN/DRAFT, `master` inchangé, HEAD d'entrée `d6f597a32ab131e3c6fb4444cfbf337c50aa3bef`. Sur ce commit, [candidate #41987435899](https://github.com/hraaaaf/Digital_crown/actions/runs/41987435899) : backend 5 607 PASS / 3 FAIL (les tests `test_cephalo_p2ter_identity_bound_pdf.py` attendent la chaîne lisible `ÉTUDE CÉPHALO ID : N`), frontend 2 007 PASS / 4 FAIL (jsdom `matchMedia`), PG18 SUCCESS. D'autres CI `npm ci --prefix frontend` FAIL pour 12 entrées facultatives `@napi-rs/canvas` manquantes du lockfile.

**Cause PDF confirmée** : `backend/templates/bilan_ortho_authoritative.html` affiche déjà `Étude Céphalo ID :`, mais `backend/services/generators/bilan_ortho_gen.py::_generate_reportlab`, source de l'export officiel A4, affiche `Étude céphalo :`. Le test ne trouve donc pas le libellé attendu, bien que le SHA/ID HTTP restent corrects. **Correction ciblée** : aligner strictement le libellé ReportLab sur le modèle HTML et conserver ID+révision issus du backend ; ne supprimer ni l'assertion ni le contrôle de lignée patient.

**Cause frontend confirmée** : le composant `LivePreview.tsx` utilise `window.matchMedia` correctement dans le navigateur, mais jsdom ne fournit pas cette API. **Correction ciblée** : mock complet `MediaQueryList` desktop **uniquement dans `LivePreview.r7.test.tsx`**, avec cleanup Vitest ; aucune modification des styles, du mobile réel ou des tokens du thème.

**Lockfile** : le `package-lock.json` V3 est dépourvu des dépendances optionnelles `@napi-rs/canvas` requises par `pdfjs-dist` `5.4.296`; leur provenance et SHA de registre ne doivent **pas être inventés**. Diagnostic temporaire ajouté au workflow TEST existant **après l'artefact de compilation** : `npm install --package-lock-only --ignore-scripts` génère la différence du lockfile sur GitHub Actions (sans commit, sans écraser le build, sans secret) et imprime `CEPH_LOCKFILE_DELTA_B64` pour intégrer ultérieurement les entrées exactes. La validation `npm ci` et la suppression du diagnostic suivront dans un deuxième commit ; **aucun résultat PASS présumé ici**.

**Sécurité** : ni merge master, ni déploiement, ni EXE, ni FUE cabinet. `clinical_validation_available=false`, PDF `INCOMPLETE`, Wits `CANDIDATE_ONLY`, `HOLD-Z-ORIENTATION`, `HOLD-MCNAMARA-SCALE` inchangés. Le commit met à jour exclusivement ce fichier canonique, deux correctifs ciblés et un pas de diagnostic CI transitoire.

**POST diagnostic Node 22 (CI #41998102028, SHA `195c60174188b41ef91a74e69eefa4f272af59df`)** : [build frontend TEST](https://github.com/hraaaaf/Digital_crown/actions/runs/41998102028) SUCCESS, `CEPH_LOT1_TEST_FRONTEND_BUILD_SHA_MATCH=PASS`, artifact #13401431144 créé. **`npm install --package-lock-only` sur Node 22 : `added=0, changed=0, removed=0`**. C'est le point clé : les jobs `npm ci` qui échouent utilisent **Node 24.11.1** (confirmé par logs #41987436207/#41987436099), alors que le workflow de build de test utilise Node 22. Une réparation via npm Node22 serait un faux vert. Le diagnostic éphémère est donc adapté pour exécuter *après le build/upload* `actions/setup-node@v4` sur **Node 24.11.1** avant la génération du delta ; les octets du build validé restent ceux du checkout original. Aucun package ajouté manuellement, aucune intégrité fabriquée. Le prochain rapport doit citer le delta Node24 réel, puis enlever le diagnostic et committer le lock corrigé. Le préfixe `@napi-rs/canvas` provient de l'option `pdfjs-dist`, pas d'une dépendance applicative arbitraire.

**Dernière mise à jour canonique 05/11/2026** — diagnostic Node24 en attente, ne pas déclarer `npm ci` corrigé avant CI.

### 35. POST — 2026-11-05 — réconciliation `npm ci` Node24 avec métadonnées vérifiées

**Preuve reproductible** : [workflow isolé #41998426624](https://github.com/hraaaaf/Digital_crown/actions/runs/41998426624) sur HEAD `24212f2949cc896fb84b030b48481f2c9208a471`, frontend Node22 `npm ci` + `npm run build:test` + manifeste SHA **SUCCESS** (artifact #13401940443). Après upload, `actions/setup-node` sur **Node24.11.1**, `npm install --package-lock-only --ignore-scripts --no-audit --no-fund` fournit le delta `CEPH_LOCKFILE_DELTA_SUMMARY={"added":12,"changed":28,"removed":0}`. Les 12 entrées `node_modules/@napi-rs/canvas*` sont toutes version `0.1.100`, provenance `https://registry.npmjs.org/` et digest `sha512` exact du registre (base64 de leur JSON exporté dans log GitHub). Les 28 changements restants n'ajoutent que `peer: true` à des paquets existants, **sans changer la version, l'URL ou l'intégrité**. Aucun autre changement de dépendance ne sera introduit.

**Fix verrouillé** : `frontend/package-lock.json` V3 conserve le manifeste et les versions/digests existants; ajouter seulement les **12 packages manquants**, avec métadonnées exactes extraites du registre GitHub Actions, et ordonner `packages` alphabétiquement. Aucun nouveau package direct dans `frontend/package.json`. Supprimer la step diagnostique de génération et conserver uniquement un garde ciblé `npm ci --dry-run --ignore-scripts --no-audit --no-fund` sur **Node24.11.1 après** le build isolé Node22 pour prévenir la régression cross-version, sans exécuter les scripts des packages et sans déployer.

**Résultat tests P0 déjà vérifié** : [CEPH P2ter backend #41998109615](https://github.com/hraaaaf/Digital_crown/actions/runs/41998109615) sur `195c601` **36/36 PASS** (dont les 3 tests PDF auparavant FAIL). La suite full frontend reste à certifier sur HEAD final avec le mock jsdom (ne pas revendiquer un résultat anticipé). La réparation lockfile n'a aucun effet sur les modèles d'IA, le runtime clinique, le PDF `INCOMPLETE` ou les autorisations patient.

**NEXT** : attendre les résultats de tests `frontend` complets et `npm ci` Node24 sur SHA final ; enquêter les autres CI rouges indépendantes ; captures BEFORE/AFTER et approval humain exact SHA obligatoires ; aucune fusion master ni release/EXE tant que le gate CODE_CERTIFIED candidate n'est pas vert.

**Statut V1 :** Wits `CANDIDATE_ONLY`, McNamara `HOLD-MCNAMARA-SCALE`, Z `HOLD-Z-ORIENTATION`, `clinical_validation_available=false`, PDF `INCOMPLETE` ; FUE cabinet 0/10. Aucun déploiement Vercel ni données patients.


### 36. PRE/POST technique — 2026-11-05 — FUE-I P2ter historique 409 (sans contournement scientifique)

**PRE observé** : [CI P2ter authentifiée #41999066368](https://github.com/hraaaaf/Digital_crown/actions/runs/41999066368) FAIL sur produit `8d9f27d1563fa54a66ea37a916b93144aca54148`, artefact #13402851829 et rapport exact SHA : `REAL_UI_LOGIN` et `SELECT_OLDER_STUDY_2` PASS, puis deux `PUT /api/ia/analyses/2` 409 à 1280×900 et 1600×1000 ; aucun POST PDF, `page.waitForResponse` expire. La réponse 409 interdit une mutation de graphe sans prochaine révision. C'est un **fail-closed légitime**, pas une autorisation de relaxer le backend. [L3 #41999066863](https://github.com/hraaaaf/Digital_crown/actions/runs/41999066863) 34/34 PASS + 2 captures, lock npm24 PASS, backend P2ter PASS.

**POST correctif candidat (non certifié à ce nouveau SHA)** : `prepareBoundCephaloDocumentSource` accepte facultativement le snapshot actif landmark (ID + x/y) et calibration du store. Il lit **l'étude expressément sélectionnée** via API ; si et seulement si landmarks/ratio sont strictement identiques aux octets de référence persistés ET révision positive certifiée, il réutilise cette révision **sans PUT no-op**. Sinon la sauvegarde stricte historique est conservée et toute 409 reste bloquante ; la sélection est vérifiée avant et après les I/O, le backend PDF continue à vérifier `analysis_id` + `expected_revision`. Le chemin est activé pour les brouillons/archives et prévisualisations du store ; aucun changement du moteur de calcul, de l'auth, de la politique des révisions, des normes, des PDF, du CSS ou des tokens. Tests unitaires ajoutés : historique déjà persisté, repère modifié, ratio modifié, conflit scientifique et révision non vérifiable. **Aucun test PASS présumé avant CI à SHA final**.

**NEXT** : full Vitest, TS, test e2e authentifié réel à deux résolutions + vérification des captures et identité A/B, negative gates et clinical HOLD ; verdict sous contrôle humain. Aucun merge master, EXE, cabinet, Vercel, CODE_CERTIFIED ou INSTALLABLE_CERTIFIED auto.

**Dernière mise à jour canonique 05/11/2026 — candidat FUE-I historique 409, CI après commit indispensable.**


### 37. PRE/POST — 2026-11-05 — PUBLIC ORIGINALS / REAL ONNX38 exact-HEAD FUE-H

**PRE scope demandé par le praticien :** un *vrai* cliché de téléradiographie de profil publique, non une image de démonstration synthétique. Les références Aariz restent des goldsets externes experts pertinents pour **erreur anatomique**, pas une preuve d'upload Cabinet. Pour la preuve d'exécution V1, réutiliser le protocole FUE-H existant de deux **authentiques originaux Wikimedia** : [ANUG, Cephalometric radiograph](https://commons.wikimedia.org/wiki/File:Cephalometric_radiograph.JPG), 2272×1818, SHA256 `ede247cdc573719cd25c928110543978f962f43e296adb1f875cdd45b3fc7ee6`; [Challiyan, lateral cephalogram](https://commons.wikimedia.org/wiki/File:A_lateral_cephalogram_without_true_vertical.jpg), 1000×1255, SHA256 `98c6384dd9cc392ac54bf365173e522a4860ce55a64b8b15e87485dbcc30371b`. Auteurs/licence CC BY-SA 4.0 reconfirmés sur les pages Wikimedia.

**Preuve historique retrouvée, pas preuve nouveau HEAD :** [run réel #39836036083](https://github.com/hraaaaf/Digital_crown/actions/runs/39836036083), commit `8ebd8b013c54ee9417b4edce091c942fbdbaf22b`, 6/6 scénarios PASS, deux importations depuis le **vrai input file React** dans le cabinet FastAPI T2, inférence CPU `SOTA_ONNX_38` (38 points par JPEG), réponse DB, source JPEG protégée hash-vérifiée, séparation des permissions, réouverture des deux radios sous nouvelle session. [Artefact 5 captures #12450269332](https://github.com/hraaaaf/Digital_crown/actions/runs/39836036083/artifacts/12450269332). Le modèle ONNX doit être récupéré du [run #34281082926](https://github.com/hraaaaf/Digital_crown/actions/runs/34281082926), artefact non expiré au préflight, SHA256 `a5ecd466d6d2c4ef02e145a143076a05720c0be56a260224812c23e2ecf42ddb`, 267484931 octets. **Aucune de ces preuves anciennes ne prétend couvrir le HEAD actuel.**

**POST préparation CI (résultat attendu, pas présumé) :** une unique modification **workflow/test-only** de `.github/workflows/ceph-r23h-fue-first-use.yml` ajoute la génération automatique d'un résumé de preuve (originals + hashes, modèle verrouillé, 38 points, captures, SHA exact et limites cliniques) **après un FUE-H strictement vert**. Le workflow existant avec `pull_request` / filtrage de chemin doit ainsi rejouer les vraies radios et publier l'artefact ; le préflight bloque toute image source altérée, modèle absent, faux calibrage, changement d'étude ou échec de login/auth/persistance. Aucune modification du frontend/backend runtime, sources scientifiques, thèmes ou tokens, aucun stockage de vraie donnée patient ; sortie GitHub seule. **RUN/CI PASS à confirmer à nouveau SHA déclenché ; ne pas inférer du précédent succès.**

**Contrôle humain et scientifique inchangé :** le modèle retournant 38 repères = preuve d'exécution **et NON précision anatomique / qualité diagnostique**. `is_calibrated=false` / `mm_per_pixel=null` dans FUE-H ; pas de validité mm ni mesures cliniques ; pas de classification. `clinical_validation_available=false`, PDF `INCOMPLETE`, Wits `CANDIDATE_ONLY`, `HOLD-MCNAMARA-SCALE`, `HOLD-Z-ORIENTATION`, FUE cabinet réel 0/10. Aucune approval visuelle de l'owner, pas de merge master, pas d'EXE, pas de Vercel, pas d'activation cabinet.

**Dernière mise à jour canonique 05/11/2026 — FUE-H public original exact SHA déclenché sur branche candidate ; résultat en attente de vérification des jobs/artefacts.**

### 38. POST — 2026-11-05 — authentic FUE-H deux radios FACAD au SHA Céphalo actuel

**Preuve de run sur le vrai HEAD V1 `aa7fb5569c00b8a22b6493a4b729fab29a9674f4`** : [GitHub Actions #42008168486](https://github.com/hraaaaf/Digital_crown/actions/runs/42008168486) **COMPLETED/SUCCESS**, [artefact #13406715253](https://github.com/hraaaaf/Digital_crown/actions/runs/42008168486/artifacts/13406715253) ouvert/inspecté ; second run indépendant au **même SHA** [#42008167166](https://github.com/hraaaaf/Digital_crown/actions/runs/42008167166) SUCCESS, [artefact #13405913261](https://github.com/hraaaaf/Digital_crown/actions/runs/42008167166/artifacts/13405913261). **Chaque run : 6/6 contrôles PASS**, zéro erreur et cinq captures véritables par run, ZIP compris. Les six structures JSON `checks` correspondent exactement d'un run à l'autre, et les deux PNG `03-reopen-anug.png` et `03-reopen-challiyan.png` sont **byte-identiques** entre les deux runs (SHA256 screenshot A `d76808115162e…`, B `f062f83f51b89…`). Aucune nouvelle application n'a été déployée ni modifiée pour tester.

**Source certifiée / vrai upload / modèle** : images Wikimedia originales **ANUG** et **Challiyan** hashées SHA1 et affichées SHA256 exact (A `ede247cdc573719cd25c928110543978f962f43e296adb1f875cdd45b3fc7ee6`; B `98c6384dd9cc392ac54bf365173e522a4860ce55a64b8b15e87485dbcc30371b`), ONNX local SRPose38 exact SHA256 `a5ecd466d6d2c4ef02e145a143076a05720c0be56a260224812c23e2ecf42ddb`; vrai navigateur Cabinet T2, login, vrai widget upload, vrai HTTP FastAPI/JWT, base SQLite T2 jetable, **38 repères par radio**, études de démo #2 et #3 distinctes, nouvelle session/réouverture complète. Un rôle restreint et un autre cabinet sont rejetés HTTP **403** pour étude ET image. `clinical_release=false`, `scientific_goldset=false`, `patient_real=false`; aucune donnée patient réelle. Report `overall=FUE_H_REAL_UI_ONNX_PERSISTENCE_SECURITY_PASS_NONCLINICAL`.

**Captures EXACTES visibles** (artefact authentique, pas de rendu fabriqué): `01-before-first-file.png` (zéro étude), `02-real-upload-anug.png`, `02-real-upload-challiyan.png` (étapes directement après upload), `03-reopen-anug.png`, `03-reopen-challiyan.png` (relecture après nouveau login avec panneau COM et repères). Les versions POST nouvellement rechargées correspondent pixel à pixel sur 2 runs. **Limitation UI** : le viewport screenshot haut de page n'expose qu'une partie de la radio et de la liste des mesures ; il n'est PAS une preuve de placement exact des 38 landmarks. L'écran immédiatement après upload affiche un avertissement de chaîne/protocole non vérifiés, tandis qu'à la réouverture il expose « 4/10 valeurs prouvées » et quelques ANGLES verts ; auditer la cohérence d'état et éviter de faire passer ces couleurs pour une validation anatomique. Distances en mm et diagnostics non autorisés sans calibration vérifiée et références.

**Limitations et next** : aucun ground truth expert sur ces **deux clichés** identifié, aucune comparaison indépendante point à point, aucune concordance numérique FACAD même tracé ; `is_calibrated=false`, `mm_per_pixel=null` pour les deux. **FUE réel sur input public validé fonctionnellement, NO-GO clinique** ; ne pas lever Wits, McNamara, Z, PDF et validation humaine. Autre CI [CEPH L3 PDF #42008168295](https://github.com/hraaaaf/Digital_crown/actions/runs/42008168295) FAIL au même SHA dans Playwright `locator.evaluate: Execution context was destroyed` lors rechargement Vite optimize deps ; 34 tests ciblés backend PASS, risque test visuel L3 restant indépendant, ne pas proclamer toute la PR verte. `CODE_CERTIFIED candidate` #42008167161 encore IN_PROGRESS au relevé (backend full), sans verdict global.

**Portée de la modification Git :** ce POST est une écriture **documentaire sur une branche de test distincte**, qui conserve les mêmes octets de code que `aa7fb556...`; la PR DRAFT #1212 et `master` restent inchangés et le run prouve uniquement `aa7fb556...`. Aucun nouveau canonique créé, il s'agit du fichier existant.

**Dernière mise à jour canonique 05/11/2026 — deux run FUE-H exact-SHA 6/6 chacun, screenshots AFTER identiques sur 2 runs ; précision anatomique et vraie clinique toujours non certifiées.**

### 39. PRE — 2026-11-05 — FUE-H plein-cliché 38 repères A/B et capture du vrai SVG (branche de test uniquement)

**Demande praticien / cible :** images ANUG et Challiyan exactement identiques (SHA-256 A `ede247cdc573719cd25c928110543978f962f43e296adb1f875cdd45b3fc7ee6`, B `98c6384dd9cc392ac54bf365173e522a4860ce55a64b8b15e87485dbcc30371b`), nouveaux rendus complets avec les 38 vrais repères numérotés et légende lisible, **exclusivement depuis le GET authentifié au SHA précis du test**, ainsi que captures SVG de la vraie UI. Ne jamais générer les landmarks ni inventer leur position.

**Baseline** : produit `aa7fb5569c00b8a22b6493a4b729fab29a9674f4`, PR #1212 DRAFT, FUE-H existant [#42008168486](https://github.com/hraaaaf/Digital_crown/actions/runs/42008168486) 6/6 PASS, mais 5 screenshots non plein-cliché et pas de JSON des positions. Le canonique UNIQUE actuel §38 déjà mis à jour. Uniquement copie du script FUE-H, artefact d'audit généré et workflow minimal sur la branche isolée ; **aucun changement aux fichiers applicatifs**. Nouveau commit implique nouveau SHA : les preuves antérieures ne se transfèrent pas au nouveau commit.

**Gates nouvelles preuves** : source hashée, modèle ONNX local hashé, JWT réel, étude distincte A/B, GET et identité, 38 IDs uniques, x/y finis et image complète non recadrée ; image audit avec distinction « points AUTO non validés » et géométrie explicite, pas d'affirmation mm/normalité/diagnostic. Captures app véridiques séparées des planches d'audit PIL, jamais maquillées. Relever si le statut « 4/10 valeurs prouvées » n'a aucun rapport avec la vérité terrain. Résultat FINAL à remplir après CI ; ne pas toucher `master`, ne pas toucher PR #1212, pas de Vercel ou EXE.

**CLINICAL NO-GO** : `clinical_validation_available=false`, Wits `CANDIDATE_ONLY`, McNamara/Z HOLD, PDF INCOMPLETE, 0/10 FUE cabinet réels. Le PDF L3 [#42008168295](https://github.com/hraaaaf/Digital_crown/actions/runs/42008168295) échoue dans Vite/Playwright `Execution context was destroyed` (reload optimizeDeps), distinct des 38 points ; si traité, contrôle isolé sans contourner le PDF.

### 40. POST — 2026-11-05 — vrai plein-cliché A/B 38 repères, screenshots de l'UI, et revue FUE

**HEAD exécuté (ne pas transférer automatiquement à la documentation future)** : `a7b633b93aa6a50aa72bdc04c621623af3c3cbea`, branche de test `test/ceph-v1-facad-two-public-radios-20261105`, [PR DRAFT #1213](https://github.com/hraaaaf/Digital_crown/pull/1213) **vers la branche DRAFT clinique #1212**, pas vers master. Run exact SHA [#42011785804](https://github.com/hraaaaf/Digital_crown/actions/runs/42011785804) **COMPLETED/SUCCESS, 6/6 FUE-H PASS** + **garde du hors champ clinique** + **plein-cliché à 38 repères × 2 PASS**. [Artefact de preuve #13407028578](https://github.com/hraaaaf/Digital_crown/actions/runs/42011785804/artifacts/13407028578) 5,48 Mo, **12 fichiers** ; ouverture des fichiers et inspection des PNG/JSON effectuée.

**Authenticité** : mêmes radiographies publiques ANUG et Challiyan vérifiées SHA256 des octets JPEG, modèle SRPose38 vérifié SHA256 `a5ecd466d6d2c4ef02e145a143076a05720c0be56a260224812c23e2ecf42ddb`, vraie UI Cabinet + upload input, JWT/FastAPI, 2 analyses #2 et #3 SQLite jetable, réouverture sur second navigateur, `GET` authentifié indépendant, 38 points ID/x/y par radio entièrement finis et dans le cadre original, aucun doublon, refus 403 lecture image/étude hors cabine et secrétariat. `report.json` : `overall=FUE_H_REAL_UI_ONNX_PERSISTENCE_SECURITY_PASS_NONCLINICAL`, `errors=[]`, `checks` 6/6 PASS, `clinical_release=false`, `scientific_goldset=false`, `patient_real=false`.

**NOUVELLES 4 preuves visuelles** :
- `fullfilm-anug-38points-numerotes.png` **3126×2125**, source native 2272×1818 sans recadrage, 38 indices sur positions réelles, tableau de 38 couples x/y en pixels originaux, source hashing et attribution CC BY-SA 4.0.
- `fullfilm-challiyan-38points-numerotes.png` **1644×1727**, source native 1000×1255 sans recadrage, 38 indices, tableau indépendant des 38 couples et identité JSON.
- `04-ui-svg-anug.png` **632×764**, capture directe de l'élément SVG React du véritable Céphalo COM après réouverture (labels COM seulement, interface indique `Landmarks: 38`).
- `04-ui-svg-challiyan.png` **632×764**, vraie capture de la seconde étude COM, même conditions.

`source-locked-38-points.json` est la source probante UNIQUE des superpositions, issue des deux GET authentifiés et réconciliée à la réouverture (pas de nouveaux landmarks inventés) ; `fullfilm-review-index.json` indexe les SHA256 des 2 PNG. Les PNG plein-cliché sont **des planches de revue indépendantes PIL**, pas des captures de l'interface : l'origine n'a pas été altérée, seuls les labels/calques sont ajoutés.

**Analyse critique** : le pipeline réel fonctionne (non-clinique) et les deux images sont maintenant **évaluables visuellement en entier**. Cela **ne valide pas** la précision de positionnement des 38 repères : pas de vérité terrain experte sur les mêmes images, pas de mesure de précision en px/mm, pas de concordance directe FACAD, pas de calibration mm/pixel. Les repères anatomiques peuvent être imparfaits ; un praticien doit approuver chaque point/contour avant tout usage. L'UI COM ne présente qu'un sous-ensemble de labels et son badge `38` signifie **chargés**, non approuvés. `4/10 valeurs prouvées` dans le panneau R23G4 désigne un calcul/protocole disponible, **pas l'exactitude anatomique vérifiée** ; revoir la sémantique pour éviter un green clinique trompeur.

**PDF L3 parallèle** : [ancien run #42008168295](https://github.com/hraaaaf/Digital_crown/actions/runs/42008168295) réexécution des jobs FAILED **déclenchée** pour discriminer le reload Vite/Playwright `locator.evaluate: Execution context was destroyed` de l'exactitude PDF; aucun nouveau PASS inventé à cet instant. Le full backend CODE candidate SHA aa7fb556 restait RUNNING lors de cette passe, distinct du test plein-cliché.

**Gates et versions** : Aucun code produit, couleur/token, backend de calcul ou PDF n'est changé par #1213. `clinical_validation_available=false`, Wits `CANDIDATE_ONLY`, McNamara et Z HOLD, PDF `INCOMPLETE`, 0/10 FUE réels et aucune approval visuelle humaine. Aucun merge master, aucun Vercel, EXE ou installation. **Ce commit POST documentaire déplace le SHA HEAD après la preuve, donc les résultats FUE-H décrits restent rattachés exclusivement à `a7b633b...`; toute validation visuelle/merge exige un contrôle au nouveau HEAD.** Conserver une seule documentation canonique par lot.

**Dernière mise à jour canonique 05/11/2026 — FUE-H 6/6 + 2 planches plein-cliché 38 pts + 2 vrai SVG + JSON de coordonnées PASS sur a7b633b, revue anatomique HOLD.**

### 41. PRE — 2026-11-05 — manque identifié : analyses calculées + PDF DIGITAL CROWN des deux téléradios FACAD

**Retour praticien :** les points seuls, même 38/38, ne répondent pas à la validation Céphalo. Au SHA de test précédent `a7b633b93aa6a50aa72bdc04c621623af3c3cbea`, FUE-H 6/6 et plein-cliché PASS, mais **aucun PDF et aucun tableau de mesures lisibles n'ont été produits pour A et B**. Les sorties déjà remises NE SONT PAS des bilans céphalométriques.

**Mission de ce sous-lot :** sur branche DRAFT de test #1213 et uniquement dans un test T2 sans patients, appeler pour chaque analyse A/B le `GET /api/ia/analyses/{analysis_id}` authentifié et extraire **les valeurs réellement présentes dans `angles_data.metrics`** sans les inventer, conserver les `null` et l'absence de calibration. Prévalider la révision (GET `/api/patients/{id}/cephalo-validation`), puis appeler la vraie route `POST /api/patients/{id}/pdf` avec `analysis_id`, `expected_revision` et `archive:false`, capture des octets PDF OFFICIELS (vrais `%PDF`, id/revision en headers, extraction texte PDF). Générer PNG A4 depuis ces octets pour montrer **le rendu exact de l'application** et remettre 2 PDFs téléchargeables. Les screenshots radio + repères de §40 restent distincts. S'il y a un 409/422 : montrer l'échec et ne JAMAIS forger une révision/une calibration.

**Critères de réussite :** chaque PDF identifié et lié à la bonne étude, non interverti, au moins une page A4 vérifiée; 2 fichiers d'analyse JSON source-authentifiée listant unités/valeurs/NC, pas de norme ni diagnostic inféré, vérification absence de mesure mm non calibrée, et revue PDF visuelle. **Les vert/anormal ne certifient pas l'exactitude anatomique.** Aucun changement de moteur, schéma, thème, ni app backend ; un harness/tests/workflow seulement. Aucun merge master/Vercel/EXE ni clinical approval. État initial `clinical_validation_available=false`, Wits CANDIDATE_ONLY, McNamara/Z HOLD, PDF INCOMPLETE au plan clinique.

**POST :** à compléter strictement sur des artefacts et logs exact SHA.

### 40. BILANS TECHNIQUES NON CLINIQUES — 2026-11-05 — deux radios FACAD, analyse angulaire / PDF d'audit

**PRE/constat** : Le praticien demande explicitement les analyses et le bilan PDF, pas seulement les 38 points. Le précédent FUE-H [#42011785804](https://github.com/hraaaaf/Digital_crown/actions/runs/42011785804), SHA `a7b633b93aa6a50aa72bdc04c621623af3c3cbea`, **6/6 PASS** et artefact #13407028578 fournit deux vrais clichés publics ANUG/Challiyan + **38 points auto chacun** via GET authentifié SQLite, mais **aucun PDF clinique de ces 2 études n'est généré**. La radio A étude T2 #2, B #3 ; `is_calibrated=false`, `mm_per_pixel=null`. Les FUE-P1 [#42011785853](https://github.com/hraaaaf/Digital_crown/actions/runs/42011785853) / FUE-P2 [#42011785726](https://github.com/hraaaaf/Digital_crown/actions/runs/42011785726) indiquent `DOCUMENT_STEPPER_SAFELY_BLOCKS_UNCALIBRATED_STUDY` PASS et `REAL_PROTOCOL_SELECTORS_AND_UNVERIFIED_LABELS` FAIL (sélecteurs COM/Steiner manquants). Ne pas contourner l'export clinique fail-closed, ne pas diagnostiquer.

**POST calculs transparents depuis les points authentifiés de `source-locked-38-points.json`** selon les **7 formules angulaires géométriques** de [`backend/services/cephalo_engine.py` au SHA produit](https://github.com/hraaaaf/Digital_crown/blob/aa7fb5569c00b8a22b6493a4b729fab29a9674f4/backend/services/cephalo_engine.py), sans normes : `SNA/SNB/ANB`, `FMA`, `IMPA`, `I_Francfort`, `Inter_Incisif` ; aucune entrée clinique ni échelle millimétrique inventée.

| Mesure en degrés (brute, aucun verdict clinique) | ANUG A | Challiyan B |
| --- | ---: | ---: |
| SNA | 79.1 | 79.9 |
| SNB | 77.7 | 74.6 |
| ANB = SNA − SNB | 1.4 | 5.3 |
| FMA / Tweed | 31.5 | 27.7 |
| IMPA | 101.1 | 104.3 |
| Incisive sup. / Francfort | 115.9 | 108.4 |
| Inter-incisif | 111.4 | 119.6 |

**Deux PDF réellement produits et inspectés dans le container utilisateur**, trois pages chacun : (1) analyse tabulée angulaire + screenshot véritable de l'UI, (2) radio entière annotée 38 repères + légende sur A3 paysage, (3) table des 38 coordonnées pixel + provenance. Documents **distincts du moteur PDF CLINIQUE officiel** et titrés en première page **NON CLINIQUE / NON SIGNÉ / NON CALIBRÉ**. Sorties générées dans le chat du 05/11/2026 :
- `CEPHALO_ANUG_BILAN_TECHNIQUE_NON_CLINIQUE.pdf` (SHA256 `bfb98896f63223e3762ee8b7cab2894e86fac7fd7831d5a92b6b788dbeb0f591`)
- `CEPHALO_CHALLIYAN_BILAN_TECHNIQUE_NON_CLINIQUE.pdf` (SHA256 `0e9ec21634ed866ee8cae71375ff863daa1fb33794db035b16fdd3ff8650851d`)

**QA PDF** : ReportLab et rendu à 120 DPI via la compétence PDF ; inspection visuelle des trois pages ANUG et extraction PyMuPDF des deux (3 pages, A4/A3/A4), aucun bloc texte hors cadre. Les chiffres ne prétendent **pas** être des réponses persistées du protocole R23G4 ni une comparaison anatomique FACAD : ils sont un **recalcul déterministe externe** des formules contenues dans le module Céphalo, appliqué aux points authentifiés.

**À faire pour un vrai bilan officiel Digital Crown** : établir calibration physique vérifiée si possible, corriger/geler manuellement les 38 repères, rejouer FUE-P1 avec sélecteurs/protocole réellement supportés, exporter via vrai endpoint PDF avec identité étude/révision et contrôler PDF/preview/screenshot. Les 2 radios publiques sans marqueur d'étalonnage **ne doivent pas recevoir de calibration estimée**. Wits candidate, McNamara et Z HOLD, PDF `INCOMPLETE`, `clinical_validation_available=false`, 0/10 FUE cabinet, approbation humaine absente. Aucun code clinique, couleur, token, master, Vercel ou EXE modifié.

**Dernière mise à jour canonique 05/11/2026 — mesures 7 angles × 2 + deux bilans PDF techniques non-cliniques disponibles dans le chat ; export clinique officiel = BLOQUÉ légitimement.**

### 42. PRE — 2026-11-05 — planches Steiner / Tweed / COM des deux radios réelles

**GO du praticien** : après les bilans PDF angulaires, montrer des **tracés géométriques céphalométriques** sur les deux originaux publics ANUG (A) et Challiyan (B), avec visuels lisibles, valeurs SNA/SNB/ANB/FMA/IMPA/IF/inter-incisif, et PDF de revue auditables. Ne pas s'arrêter aux 38 points ni inventer une anatomie intermédiaire.

**Source verrouillée** : `source-locked-38-points.json` issu des GET authentifiés au SHA de run `a7b633b93aa6a50aa72bdc04c621623af3c3cbea` par [GitHub #42011785804](https://github.com/hraaaaf/Digital_crown/actions/runs/42011785804), originaux JPEG à SHA256 `ede247cdc573719cd25c928110543978f962f43e296adb1f875cdd45b3fc7ee6` (ANUG) et `98c6384dd9cc392ac54bf365173e522a4860ce55a64b8b15e87485dbcc30371b` (Challiyan). Formules angulaires relues dans `backend/services/cephalo_engine.py` sur SHA produit `aa7fb556...`: SNA/SNB/ANB à N, FMA entre Go-Me et Po-Or, IMPA = 180° − angle(L1a→L1i,Go→Me), I/Francfort et inter-incisif.

**Portée** : 6 PNG A/B × Steiner, Tweed, COM, 2 PDF techniques + index JSON source/mesures/hash, éventuel script reproductible sur branche de test PR #1213. **Les tracés se limitent à segments entre repères sources** : Steiner SN/NA/NB, Tweed FH/GoMe/L1, COM agrégation angulaire sans diagnostic ni contour cutané inventé. Original radiographique jamais rééchantillonné pour la géométrie originale. Les PDF sont des **documents d'audit externes, pas ceux de l'export clinique officiel** ; rester explicite sur le modèle automatique non contrôlé et `mm_per_pixel=null`.

**NO-GO clinique maintenu** : `clinical_validation_available=false`, Wits CANDIDATE_ONLY, McNamara/Z HOLD, PDF OFFICIEL INCOMPLETE, FUE cabinet réel 0/10, approbation humaine absente. Aucun merge master, déploiement Vercel, EXE ou levée de gate.

**POST** à compléter uniquement après génération, inspection PNG/PDF et preuve de cohérence des chiffres et des 38 points.

### 42. POST — 2026-11-05 — Steiner / Tweed / COM, A+B, PDF de revue et validation des images

**PRE lié à cette passe** : §42 PRE, baseline de provenance `source-locked-38-points.json` API GET authentifié réel, source ONNX SHA `a7b633b...`, photo source ANUG et Challiyan vérifiées SHA256 et CC BY-SA 4.0. **Il s'agit d'une production d'audit externe locale, pas d'une nouvelle inférence ONNX ni d'un export PDF officiel de Digital Crown.** PR #1213 reste DRAFT, #1212/master inchangés.

**POST : six PNG réels produits et rendus en conversation** depuis seulement 38 landmarks auto d'origine pour A et B :
- `anug-steiner-traces-geometriques.png`, `challiyan-steiner-traces-geometriques.png` : segments SN, NA, NB, angles SNA/SNB/ANB (N commun), positions d'origine x/y verrouillées ;
- `anug-tweed-traces-geometriques.png`, `challiyan-tweed-traces-geometriques.png` : plan FH Po-Or, mandibulaire Go-Me, axe L1a–L1i, FMA/IMPA ;
- `anug-com-traces-geometriques.png`, `challiyan-com-traces-geometriques.png` : combinaison explicite des sept segments (SN, NA, NB, FH, Go-Me, U1a-i, L1a-i), sept angles bruts SNA, SNB, ANB, FMA, IMPA, I/Francfort, inter-incisif.

**Valeurs calculées et recoupées par assertions des formules de `backend/services/cephalo_engine.py` au `aa7fb556...`** : ANUG SNA 79.1° SNB 77.7° ANB 1.4° FMA 31.5° IMPA 101.1° I/FH 115.9° interincisif 111.4°. Challiyan SNA 79.9° SNB 74.6° ANB 5.3° FMA 27.7° IMPA 104.3° I/FH 108.4° interincisif 119.6°. **Pas de valeurs normatives, classification, hypothèses ou distances mm**. Les tracés ne sont pas une segmentation de tissus mous ou un contour osseux interpolé (pas d'information source pour en dessiner un). Photos sources inchangées sur disque ; calques rendus dans des PNG d'audit indépendants.

**Deux PDFs physiques de revue générés et vérifiés** : `CEPHALO_ANUG_STEINER_TWEED_COM_AUDIT_NON_CLINIQUE.pdf` SHA256 `703895f92087fee6f8f1192407126f3cd123daca62784bb066e46adab5e435e6` (4 pages) ; `CEPHALO_CHALLIYAN_STEINER_TWEED_COM_AUDIT_NON_CLINIQUE.pdf` SHA256 `a678f69ce51d1677272cda86978988231174896ead08e313f34eedc260334754` (4 pages). Chaque PDF contient (1) 7 angles + limites sur A4 (2) Steiner A3 paysage (3) Tweed A3 paysage (4) COM A3 paysage. **PDF généré par ReportLab externe**, pas par endpoint de bilan patient Digital Crown, strictement « AUDIT NON CLINIQUE » en page 1 ; la création ne prétend donc pas lever le blocage volontaire de l'export clinique pour ces 2 radios sans calibration.

**QA physique** : rendu des deux PDF en PNG à 100 DPI et inspection de la première page et des planches A/B ; vérification structure PyMuPDF 4 pages chacune (8 pages), tous blocs texte dans limites ; assertions SHA sources, modèle, 38 ID distincts, x/y finis dans cadre, et exact 7 angles pour chaque source, SHA256 de 6 images et 2 PDF réinscrit dans `traces-provenance.json`. ZIP complet des 10 fichiers `Cephalo_FACAD_Steiner_Tweed_COM_ANUG_Challiyan_AUDIT_2026-11-05.zip` SHA256 `486c1e099d1c9d50addd555320ea81201e4fd771d3504d17146f4089be51650d`, contient le script Python de reproduction, 6 PNG, 2 PDF, manifest JSON.

**État projet GitHub au SHA juste avant ce POST `d4487e1a3a155ac07adb0a7108c9b90d3a9efae8`** : branche #1213 DRAFT, run test-only CI Scope #42018667717 SUCCESS, R14 #42018667606 SUCCESS, frontend test #42018667595 SUCCESS, FUE-H #42018667542, FUE-P1 #42018667736 et FUE-P2 #42018667464 **IN_PROGRESS** au relevé. Gate « UI Human Visual Approval » #42018660457 **FAIL** comme non approuvé; ne pas auto-signer ni présenter PASS clinique. Ce PASS des audités externes ne remplace pas la CI live du nouveau SHA documentaire.

**Blocages maintenus** : preuve ONNX technique réutilisée du run antérieur et non nouvellement inférée, pas de contours anatomiques expertisés, aucune comparaison FACAD même image / ground truth, `is_calibrated=false` / `mm_per_pixel=null`, `clinical_validation_available=false`, Wits CANDIDATE_ONLY, McNamara/Z HOLD, PDF officiel INCOMPLETE, FUE cabinet réel 0/10. **No merge master, no Vercel, no EXE, no patient release.**

**NEXT** : faire la revue visuelle humaine des deux plans Steiner et Tweed + COM, marquer les erreurs de placement landmark par landmark, puis produire une nouvelle vraie analyse corrigée via l'app avec révision contrôlée. Sans expert confirmé ni échelle mm, seule l'analyse angulaire de recherche reste autorisée.

**Dernière mise à jour canonique 05/11/2026 — 6 PNG source-lock + 2 PDFs techniques (8 pages) + manifest et ZIP vérifiés, pas de GO clinique.**


### 43. POST — 2026-11-05 — V2 arcs angulaires réels et labels sans collision sur ANUG + Challiyan

**Demande/état d'entrée de ce sous-lot** : l'utilisateur a donné « Okay go » après une note **7,5/10 visuelle** et **3/10 clinique**, avec les objectifs arcs d'angles, déplacement étiquettes et comparaison FACAD expert même image. Baseline source §42 : deux radios publiques Wikimedia Commons CC BY-SA 4.0, images originales SHA256 A `ede247cdc573719cd25c928110543978f962f43e296adb1f875cdd45b3fc7ee6` et B `98c6384dd9cc392ac54bf365173e522a4860ce55a64b8b15e87485dbcc30371b`, origine landmarks `source-locked-38-points.json` émis par GET authentifié du run [#42011785804](https://github.com/hraaaaf/Digital_crown/actions/runs/42011785804) SHA `a7b633b93aa6a50aa72bdc04c621623af3c3cbea`, moteur géométrique au HEAD produit `aa7fb5569c00b8a22b6493a4b729fab29a9674f4`. Aucun git PRE distinct n'a été poussé pour ce nouvel incrément visuel : ce POST documente l'écart de gouvernance sans prétendre à une annotation PRE faite avant exécution.

**Sortie V2 physique produite dans la conversation** : 6 PNG `anug-{steiner,tweed,com}-arcs-et-labels.png` et `challiyan-{steiner,tweed,com}-arcs-et-labels.png`, 2 PDF `CEPHALO_ANUG_STEINER_TWEED_COM_ARCS_AUDIT_NON_CLINIQUE.pdf` SHA256 `d8651a64dec668b25ba9c715ce6d5673d34d7bf000d5e6dad4b95a5cda27711d` et `CEPHALO_CHALLIYAN_STEINER_TWEED_COM_ARCS_AUDIT_NON_CLINIQUE.pdf` SHA256 `7c435a0784f38b87ef25787eaac0b31c1890ec2e421b45d2719b7bec28c99e8f`; PDF **4 pages chacun** (A4 mesures + 3 A3 paysage Steiner/Tweed/COM). Dossier ZIP `Cephalo_FACAD_Arcs_Steiner_Tweed_COM_V2_2026-11-05.zip` SHA256 `8bb996a7fdf574123fdeed19d9247505e13ad91df74c25d148840103f0f7a26e` avec 6 PNG, 2 PDF, JSON provenance, script de reproduction et limites.

**Constructions** : arcs calculés par vecteurs dans l'image sur le vrai sommet à N pour SNA=angle SN/NA, SNB=angle SN/NB, ANB=angle NA/NB (calcul par différence SNA-SNB), à l'intersection des **droites** pour FMA (Go-Me/FH), IMPA (axe incisif inferieur/Go-Me), incisive supérieure/Francfort et interincisif (axes U1/L1). Chaque sweep est contrôlé par assertion indépendante `abs(angle_arc - angle_moteur) < 0.11°`. ANUG FMA : prolongements **pointillés** jusqu'à l'intersection réelle des droites sur le cliché. Challiyan FMA : intersection réelle x=-147 px à l'**extérieur de l'image native**, donc schéma angulaire **déporté et marqué** hors photo, avec deux rayons, valeur 27,7°. Aucune position anatomique créée par l'inset.

**Géométrie et collision** : packing déterministe des étiquettes des landmarks utilisés dans chaque protocole, boîtes de légendes garanties dans le cadre, zéro recouvrement boîte/boîte et zéro masque de repère voisin, marqueurs d'origine non déplacés, aucune extrapolation de profil mou. Statut visuel supérieur à §42, mais ne pas présenter un « score certifié ». Chaque image porte « NON CLINIQUE / POINTS AUTO NON EXPERTISÉS / PAS DE CALIBRATION » et « AUDIT GRAPHIQUE — PAS L'INTERFACE NI FACAD ». Les valeurs angulaires source demeurent inchangées : A `79.1, 77.7, 1.4, 31.5, 101.1, 115.9, 111.4` degrés, B `79.9, 74.6, 5.3, 27.7, 104.3, 108.4, 119.6` degrés (ordre SNA, SNB, ANB, FMA, IMPA, I/FH, inter-incisif). **Ces valeurs n'ont pas été comparées à une mesure experte sur les mêmes clichés**.

**QA PDF** : script PDF skill `render_pdf.py` DPI 110 appliqué aux deux PDF ; 8 pages rendues et contact sheets ouverts visuellement ; PyMuPDF 4 pages/patient et une image par page A3, tous les blocs texte dans le cadre ; fichiers hashés sur disque. Manifest `traces-arcs-provenance.json` : source SHA & modèle SHA, 38 ID uniques, exactement les 7 angles par cas, `overlaps=0`, `arc_placement` et géométrie, `scientific_goldset=false`, `clinical_accuracy_validated=false`, `landmark_deviation_px=null` et `landmark_deviation_mm=null` ; aucun patient réel ni mm inventé.

**Vérification FACAD** : recherches web sur les deux titres exacts Commons ne donnent que **les deux originaux**, sans annotation experte de ces mêmes images (<https://commons.wikimedia.org/wiki/File:Cephalometric_radiograph.JPG>, <https://commons.wikimedia.org/wiki/File:A_lateral_cephalogram_without_true_vertical.jpg>). Documentation Facad <https://www.facad.com/wp/tracing/> indique placement / correction manuel des repères et non un goldset livré pour ces JPG ; manuel <https://www.facad.com/dox/dox313/FacadTracingRefMan.pdf> précise la nécessité de calibrer pour les distances. Résultat : `FACAD_SAME_IMAGE_GOLDSET=NOT_FOUND`, **erreur en px non mesurée**, aucune équivalence FACAD déclarée.

**Portée STRICTE** : création locale d'artefacts externes de revue uniquement. **Aucun changement aux composants applicatifs**, tokens CSS du thème, moteur de calcul, PDF clinique, `master`, PR clinique DRAFT #1212, aucune fusion/EXE/Vercel. La branche PR de test #1213 DRAFT reste documentaire et de harness. La remise des PNG/PDF n'est pas un FUE produit du HEAD documentaire.

**GitHub runs HEAD de la PR #1213 `036275151f5bfe2557bc565bfb67bcd9b2f1ae4d` au relevé** : [CI Scope #42019506353](https://github.com/hraaaaf/Digital_crown/actions/runs/42019506353) SUCCESS, [frontend TEST build #42019506295](https://github.com/hraaaaf/Digital_crown/actions/runs/42019506295) SUCCESS, [R14 audited HOLD #42019506160](https://github.com/hraaaaf/Digital_crown/actions/runs/42019506160) SUCCESS, [FUE-H #42019506217](https://github.com/hraaaaf/Digital_crown/actions/runs/42019506217) SUCCESS ; [FUE-P1 #42019506051](https://github.com/hraaaaf/Digital_crown/actions/runs/42019506051) FAIL, [FUE-P2 #42019506230](https://github.com/hraaaaf/Digital_crown/actions/runs/42019506230) FAIL, [UI Human Visual Approval #42019501727](https://github.com/hraaaaf/Digital_crown/actions/runs/42019501727) FAIL/NOT APPROVED. **Aucun verdict full-green**.

**Gates HOLD maintenus** : `clinical_validation_available=false`, Wits `CANDIDATE_ONLY`, McNamara `HOLD-MCNAMARA-SCALE`, Z `HOLD-Z-ORIENTATION`, PDF clinique `INCOMPLETE`, 0/10 FUE cabinet réels. **Next** : praticien examine points/anatomie A+B, annote les erreurs, fournit ou produit via FACAD de vrais tracés experts des mêmes images ; introduire arcs + layout dans le **code React réel** en héritant des tokens thème, sur branche indépendante avec captures FUE React, réparer FUE-P1 / sélecteurs avant de prétendre à une validation utilisateur.

**Dernière mise à jour canonique : 05/11/2026 — POST V2 6 images arcs/labels, 2 PDF (8 pages), source-locked, zéro chevauchement technique, concordance FACAD en attente.**

### 44. PRE — 2026-11-05 — audit PR historiques des vrais tracés Céphalo

**Rappel précis du praticien :** « Regarde les anciens PR cephalo y avait bien des tracés effectués ». Ne pas réinventer arcs/tracés si les anciens PR et composants apportent déjà une implémentation saine. Inventorier les PR historiques (notamment #878 R23-E/F Focus, #1003 R23-G UI parity, #1198 Steiner/COM V1 et R15/F5), les fichiers React SVG/constructeurs qui ont réellement existé, leur présence éventuelle sur le HEAD clinique #1212 `aa7fb556...`, captures/FUE exact SHA et le statut des validations humaines. Différencier tracés graphiques, constructions calculées, Focus au survol et véritables tracés experts ; ne pas confondre « UI approuvée » et « précision clinique certifiée ».

**Entrée** : SHA branche DRAFT #1213 avant passe `036275151f5bfe2557bc565bfb67bcd9b2f1ae4d` (ou SHA courant du fichier canonique au moment de l'écriture); branche clinique #1212 reste DRAFT, master intouché. Document unique `docs/audits/CEPH_V1_LOT1_SCIENCE_APPROVAL_FUE_PREFLIGHT.md`. Audit/documentation seulement, aucune modification produit, merge, Vercel ni EXE.

**Critères** : identifier PR, SHA, preuves et noms de fichiers concrets ; vérifier le code HEAD actuel avant toute proposition ; choisir réutilisation/remise en service plutôt que nouveau moteur parallèle ; préserver tokens du thème, source-lock, gates de non-fabrication, `clinical_validation_available=false`, 0/10 FUE réels et UI Human Approval non transférable.

**POST** à remplir avec résultats des PR, conclusions, recommandation de suite et statut CI réel.

### 44. POST — 2026-11-05 — verdict sur anciens PR Céphalo et moteur de tracé

**Demande vérifiée dans le code source et l'historique GitHub, sans nouvelle modification produit** : le praticien a raison, **les vrais tracés existaient déjà dans la vraie UI React**. Les planches externes SVG/PIL Steiner/Tweed/COM réalisées dans cette conversation ne sont pas un remplacement acceptable de ce moteur. Avant d'écrire un nouveau renderer, réemployer l'implémentation existante, évaluer ses guards, et faire une capture dans le navigateur du HEAD testé.

**PR historiques vérifiées** :
- [#878](https://github.com/hraaaaf/Digital_crown/pull/878) OPEN DRAFT head `b593e56e4fd488701a982fcaeef245a27c14f939` : R23-E/F **tracés SVG interactifs + édition 38 repères + Focus par analyse + zoom partagé + étiquettes intelligentes**; fichier `frontend/src/features/ortho/CephaloTracingLayerBase.tsx`, `CephaloTracingLayer.tsx`, `components/cephaloLabelLayout.ts`, `cephaloConstructionViewport.ts`, `cephaloAngleRecognition.ts`, tests. Le run de **validation visuelle R23-E** [#38967093654](https://github.com/hraaaaf/Digital_crown/actions/runs/38967093654) est réellement `COMPLETED/SUCCESS` au `c5ea5000a6f1a52e8d2da168638b3e118d00dbeb` (16 octobre 2026), **seulement ce SHA** ; aucune approbation valide automatiquement sur head R23-F ni #1212; artifacts anciens non accessibles dans ce run à la consultation (`artifacts=[]`).
- [#911](https://github.com/hraaaaf/Digital_crown/pull/911) OPEN DRAFT head `d86d2963e3b31e6cacc2b77838f93d509460dfd1` : projections read-only R23-G2 de protocoles, pas autorité clinique autonome.
- [#1003](https://github.com/hraaaaf/Digital_crown/pull/1003) OPEN DRAFT head `4996b26a7392e8d45258295f875c9d090ed3962d` : COM10 read-only avec **Focus seulement si preuve mesurée active et même source** ; `lines: []` quand aucune géométrie autorisée — pas de faux SVG.
- [#1198](https://github.com/hraaaaf/Digital_crown/pull/1198) OPEN DRAFT head `99f653cea1e73f9b7d740e4e08e1280e2f78df36` : sélection V1 limitée **COM Digital Crown et Steiner complet 1953+1959 (15 facteurs, PAS 15/15 calculés certifiés)**, synchronisée entre tracé, Workbench et clinique ; anciens choix hors V1 refusés. Il manque des landmarks source/manuels pour une partie de Steiner.
- [#458](https://github.com/hraaaaf/Digital_crown/pull/458) et [#477](https://github.com/hraaaaf/Digital_crown/pull/477) MERGED : studio scientifique R15/R15bis, mise en page et tokens sémantiques ; ne pas confondre avec moteur de plans. [#620](https://github.com/hraaaaf/Digital_crown/pull/620) MERGED : **superposition longitudinale** F5 de 2 périodes, méthode distincte d'un tracé latéral Steiner/Tweed sur une radio.

**HEAD clinique actuel de comparaison** : PR #1212 DRAFT `aa7fb5569c00b8a22b6493a4b729fab29a9674f4`. Les vrais SVG subsistent dans [`frontend/src/features/ortho/CephaloTracingLayerBase.tsx`](https://github.com/hraaaaf/Digital_crown/blob/aa7fb5569c00b8a22b6493a4b729fab29a9674f4/frontend/src/features/ortho/CephaloTracingLayerBase.tsx#L290-L419): branches `showSteiner` SN, NA, NB ; `showTweed` FH Po_anatomic→Or, Go→Me, L1 apex/incisal ; autres selon garde. Le wrapper [`CephaloTracingLayer.tsx`](https://github.com/hraaaaf/Digital_crown/blob/aa7fb5569c00b8a22b6493a4b729fab29a9674f4/frontend/src/features/ortho/CephaloTracingLayer.tsx#L259-L324) rend **COM, McNamara, Ricketts** `referenceHold` (baseAnalysis `r23-reference-hold`), et code `const showCom = false` : l'ancienne géométrie COM est volontairement désactivée tant qu'elle n'est pas source-certifiée ; les multiples JSX `data-r19-construction` toujours présents sont donc **inaccessibles en COM**. Le wrapper initialise `mode='com'` par défaut sans `activeAnalysis` externe. C'est une cause source et prouvée de visualisation **repères sans traits COM** ; pas la preuve d'une disparition du moteur.

**Régressions/migrations de présentation** : ancien `cephaloConstructionViewport.ts` et ancien `components/cephaloLabelLayout.ts` de #878 ne sont **pas présents** au HEAD #1212, tandis que `getCephaloZoomViewBox` a été réimplémenté dans le Base et `CephaloLandmarkReticles.tsx` embarque désormais une autre collision-évitement inline pour les labels ; donc ne pas restaurer naïvement deux versions concurrentes. Le même `cephaloAngleRecognition.ts` reste identique (`sha 4c857516db4f443bf77325a6fda48b03fe837667`), et `CephaloTracingLayerBase.tsx` a changé (`c370d54...` ancien / `a720634...` actuel). Panneau V1 [`Step1Cephalo.tsx`](https://github.com/hraaaaf/Digital_crown/blob/aa7fb5569c00b8a22b6493a4b729fab29a9674f4/frontend/src/features/ortho/components/Step1Cephalo.tsx#L128-L149) fournit **déjà** `<select id="cephalo-ready-analysis">` `V1_CEPHALO_PROTOCOLS` à deux options (`com`, `steiner`).

**Cause du FUE-P1 FAIL contrôlée à la ligne près** : [`frontend/scripts/fue-ceph-p1-authenticated.mjs`](https://github.com/hraaaaf/Digital_crown/blob/aa7fb5569c00b8a22b6493a4b729fab29a9674f4/frontend/scripts/fue-ceph-p1-authenticated.mjs#L87-L104) attend encore `['all','steiner','tweed','mcnamara','com','ricketts']` et échoue avec `Missing protocol select options ["com","steiner"]`. Ce **contrôle d'acceptation est devenu obsolète** après le contrat V1 #1198 ; l'observation actuelle ne démontre **pas** que les deux options COM/Steiner sont absentes : **elles sont bien les deux options trouvées**. Aligner le harness sur exactement les deux modes, valider l'exclusion des autres et prendre de véritables screenshots de **l'affichage Steiner dans React** avant de rouvrir un sujet produit.

**Garde clinique de provenance sur les deux téléradios exactes** : `source-locked-38-points.json` du run ONNX réel [#42011785804](https://github.com/hraaaaf/Digital_crown/actions/runs/42011785804) confirme chacun des deux : `Po` et `Or` existent, mais **pas `Po_anatomic`**, repère distinct explicitement exigé par le rendu Tweed historique (`showTweed seg(poAnatomic,or_,'fh',...)`). Ne jamais remplacer `Po_anatomic` par `Po` silencieusement pour produire un faux FH Tweed. **COM** peut devenir un renderer visuel uniquement après audit source de ses constructions et décision clinique explicite ; ne pas se contenter de passer `showCom=true`.

**Plan de réemploi net** :
1) Corriger seulement l'attente obsolète du FUE-P1 sur branche isolée et obtenir des captures véritables du renderer React **Steiner**, incluant la visibilité SN/NA/NB et les points, sur les 2 images source ; donner au praticien des captures BEFORE/AFTER au **même SHA de code testé**.
2) Réutiliser le Base + pont Focus existants, sans duplicata Python dans l'application. Ne porter vers le courant les fonctions de clipping/étiquettes du R23-E que si les tests visuels prouvent un vrai manque (il existe déjà un autre layout collision dans `CephaloLandmarkReticles`). Tout style doit hériter des tokens sémantiques du thème.
3) Garder COM `referenceHold` tant qu'une preuve source-exacte n'autorise pas chaque construction ; arc d'angle uniquement pour géométrie autorisée et même source, pas de contour/classe simulé. Garder PO_anatomic manquant et mm/calibration `NOT_AVAILABLE`.

**Verdict : ancien moteur à RÉUTILISER, pas à réécrire.** Prochain lot = HARNESS V1 FIX + capture Native React Steiner × A/B ; pas de changement produit pendant cet audit. PR #1213 DRAFT et #1212/master intacts hors écriture documentaire dans le canonique. Aucune validation clinique : `clinical_validation_available=false`, Wits candidate, McNamara/Z HOLD, PDF officiel INCOMPLETE, 0/10 FUE cabinet réels. Approbation UI R23-E ancien SHA non transférable.

**Dernière mise à jour canonique : 05/11/2026 — audit PR historiques #878/#911/#1003/#1198 et composants React actuels, correction de la cause FUE-P1 identifiée ; aucun nouveau code produit.**

### 45. PRE — 2026-11-05 — correction FUE-P1 V1 et captures React Steiner ANUG/Challiyan

**GO praticien** : rectifier le harness FUE-P1 obsolète et récupérer les vrais tracés React Steiner sur les deux vraies radios publiques via FUE-H authentifié (pas Photoshop/Python). Moteur actuel sur base clinique #1212 SHA `aa7fb5569c00b8a22b6493a4b729fab29a9674f4` contient déjà dans `CephaloTracingLayerBase.tsx` les segments SN/NA/NB sous `data-cephalo-line-key`. Le test `frontend/scripts/fue-ceph-p1-authenticated.mjs` compare à tort le sélecteur V1 à `['all','steiner','tweed','mcnamara','com','ricketts']` alors que `cephaloV1ProtocolScope.ts` n'autorise exactement que `com` et `steiner` depuis #1198 ; ne pas forcer les anciens modes dans l'UI.

**Plan borné** : (1) vérifier dans FUE-P1 présence exacte et sélection persistante des deux modes V1, labels de manque de preuve ; pas de prétention à la couverture complète COM/Steiner ; (2) utiliser le FUE-H réel avec JPEG ANUG/Challiyan vérifiés SHA et SRPose38 source authentifié pour capturer, si possible, un état **Steiner natif** et les 3 lignes SN/NA/NB sur le même SVG base, et un état COM réellement protégé, en produisant un artefact Actions PNG + JSON noms/SHA ; (3) rerun exact SHA et lire logs/artefacts ; (4) documenter vrais résultats, y compris FAIL éventuel, dans canonique et Notion. 

**Contraintes** : ne pas ajouter de dessin géométrique parallèle, ne pas réactiver `showCom=false`, ne jamais assimiler Po et Po_anatomic pour Tweed, aucune calibration mm synthétique, aucun diagnostic ni validation clinique ; conserver thème et composants actuels ; branche PR #1213 DRAFT, PR #1212/master inchangés, pas de Vercel/EXE/merge. `clinical_validation_available=false`, PDF clinique INCOMPLETE, FUE cabinet réel 0/10.

**POST :** à renseigner strictement à partir des captures React réelles et logs/actions, pas des dessins externes.

### 45. POST — 2026-11-05 — code FUE V1 corrigé, preuves native React soumises à la CI (PENDING)

**Code poussé sur PR #1213 DRAFT uniquement** : (a) commit `22d0149c97aa37efb09a9048fd43e18bb9c06d99` dans `frontend/scripts/fue-ceph-p1-authenticated.mjs` pour remplacer l'assertion des six anciens modes par la vérification **exactement des deux modes V1 activables COM et Steiner** ; COM SVG en HOLD (aucune ancienne géométrie), Steiner SN/NA/NB réel au DOM, captures 03/04. Le contrôle protocole est placé **après** les tests d'interactions/correction/document pour ne pas modifier le jeu de repères pendant les gestes. (b) commit `49d1015c50ff71429346e4b75c88036e33f71e18` dans `frontend/scripts/fue-ceph-r23h-first-use.mjs` : parcours FUE-H original conservé, puis pour chaque image ANUG/Challiyan l'application React doit sélectionner Steiner via l'interface V1, vérifier chaque `<motion.line data-cephalo-line-key="sn|na|nb">` et les 6 coordonnées d'extrémités contre les 38 points GET authentifiés de la **même étude** à une tolérance de 0,05 px. Capture complète page `05-real-react-steiner-{anug,challiyan}.png` et SVG natif `06-real-react-steiner-svg-{anug,challiyan}.png` ; rapports JSON avec identification étude/source, noms d'images et segments. Échec de preuve = FAIL, aucun dessin de substitution.

**Statut CI de ces modifications, NE PAS SURDÉCLARER** : [FUE-H #42035537992](https://github.com/hraaaaf/Digital_crown/actions/runs/42035537992), [FUE-P1 #42035537973](https://github.com/hraaaaf/Digital_crown/actions/runs/42035537973), [FUE-P2 #42035537966](https://github.com/hraaaaf/Digital_crown/actions/runs/42035537966), [frontend test #42035538025](https://github.com/hraaaaf/Digital_crown/actions/runs/42035538025), [R14 #42035538000](https://github.com/hraaaaf/Digital_crown/actions/runs/42035538000) : jobs **QUEUED** au dernier relevé sur HEAD code `49d1015...`; [Scope #42035537963](https://github.com/hraaaaf/Digital_crown/actions/runs/42035537963) **IN_PROGRESS** ; aucun résultat exact SHA prétendu. Le run pré-correctif [FUE-H #42034966138](https://github.com/hraaaaf/Digital_crown/actions/runs/42034966138) sur ancien SHA `cd25e1...` a confirmé **FUE-H 6/6 PASS** mais **FUE-P1 5/6 FAIL** avec `Missing protocol select options ["com","steiner"]` — cela prouve précisément le défaut du harness, **pas** la réussite des nouveaux tests. Les nouveaux PNG ne sont ni téléchargés ni inspectés à ce stade ; ne pas les annoncer livrés. Le commit POST documentaire peut déclencher ses propres CI de SHA différent ; ne pas transférer des statuts entre commits.

**Contrat sécurité conservé** : COM `showCom=false`, métriques non prouvées cachées ; jamais `Po` alias de `Po_anatomic`, Tweed native non validé, ni mm calibrés, ni publication PDF patient, ni contours inventés. Aucune modification du code produit, ni thème, master, PR clinique #1212, merge, EXE, Vercel. `clinical_validation_available=false`, Wits CANDIDATE_ONLY, McNamara/Z HOLD, PDF clinique INCOMPLETE, 0/10 FUE cabinet réels.

**NEXT** : relever les résultats exacts HEAD, récupérer l'artefact `ceph-r23h-first-use`, lire `react_steiner` et inspecter les 4 véritables PNG natifs (2 pages + 2 SVG) ANUG/Challiyan ; réparer si les lignes échouent, sans ajouter de moteur parallèle. Une correction de harness qui compile n'est **pas encore** une FUE validée tant que cette preuve manque.

**Dernière mise à jour canonique 05/11/2026 — POST patch tests/harness, CI queued, captures non certifiées.**

### 46. PRE — 2026-11-05 — FUE-H rouge uniquement à cause de l'assertion de nombre de captures

**Signalement praticien** : « FUE-H IS RED TOUT LE RESTE EST VERT ». Diagnostic vérifié au SHA exact `6f56dafe04ff663d363e2ee9d310a4345e6e4665` : [FUE-H #42036596943](https://github.com/hraaaaf/Digital_crown/actions/runs/42036596943) conclut **FAIL** à la seule étape finale `Publish exact-HEAD public original to ONNX38 proof summary` ; le log Python précise `<stdin> line 8 AssertionError`, qui correspond **exactement** à `assert len(report['screenshots'])==5` dans `.github/workflows/ceph-r23h-fue-first-use.yml` lignes 155-199. Or après ajout des deux screenshots React native `05-real-react-steiner-anug/challiyan.png`, les images page passent de 5 à **7**, et les quatre images SVG (2 avant + 2 Steiner) sont dans `report.svg_screenshots` séparément. Le parcours navigateur a réellement **6/6 PASS** et traces `R23H_NATIVE_REACT_STEINER challiyan` et `anug` PASS : source lock SN/NA/NB. Artifact émis malgré le step rouge : ID `13419397151`, 16 fichiers, run #42036596943.

**Autres runs SHA `6f56dafe...`** : FUE-P1 #42036597040 SUCCESS (6/6), FUE-P2 #42036596939 SUCCESS (phantom synthétique, non clinique), frontend #42036597099 SUCCESS, Scope #42036596732 SUCCESS, R14 HOLD #42036596763 SUCCESS. Human Visual Approval #42036590517 FAIL : volontaire, approbation humaine non obtenue ; ne pas le présenter vert ni contourné.

**Correction ciblée autorisée** : remplacer le nombre d'images page figé par une assertion exacte sur les **7 noms attendus**, vérification indépendante des **4 SVG natifs** et des **2 rapports React Steiner**, provenance/source hash pour A+B ; mettre à jour le résumé Actions ; ne modifier aucun code clinique ou module de dessin. Ne pas changer les gates; produire preuve exact nouveau SHA, déployer/réintégrer uniquement sur autorisation explicite (non donnée). PR #1213 DRAFT, #1212 et master intacts, `clinical_validation_available=false` et 0/10 FUE cabinet réels.

**POST** uniquement après commit correction workflow et lecture des CI.

### 46. POST — 2026-11-05 — FUE-H publication réparée, vraie preuve navigateur contrôlée localement, CI du nouveau SHA en file

**Diagnostic confirmé au SHA d'entrée `6f56dafe04ff663d363e2ee9d310a4345e6e4665`** : [workflow FUE-H #42036596943](https://github.com/hraaaaf/Digital_crown/actions/runs/42036596943) est rouge **uniquement** sur `Publish exact-HEAD public original to ONNX38 proof summary` ; log `File "<stdin>", line 8, AssertionError` => `assert len(report['screenshots'])==5`. À ce moment le véritable FUE-H avait pourtant ses 6/6 checks PASS, et les deux traces `R23H_NATIVE_REACT_STEINER challiyan/anug SEGMENTS_SN_NA_NB_SOURCE_LOCKED_NONCLINICAL` étaient PASS. L'étape d'archivage `actions/upload-artifact` a quand même publié l'artefact #13419397151, 16 fichiers zip (SHA256 du zip `0979740fc0d010c3424acc3bc666640c6aa30843625ce916cd0f9264892c5bca`).

**Correction minimale poussée** : commit [`6f71474745ebef0c1aacdbc470218a362479e2c3`](https://github.com/hraaaaf/Digital_crown/commit/6f71474745ebef0c1aacdbc470218a362479e2c3) dans **le seul workflow** `.github/workflows/ceph-r23h-fue-first-use.yml`. L'étape de publication ne présume plus cinq PNG : exige **exactement 7 captures de page** (pré-import 1, uploads 2, reopens 2, nouveau Steiner React 2), **exactement 4 captures SVG** (2 initiales, 2 Steiner), fichiers existants >10000 octets, **2 études A/B avec les vrais SHA de sources**, `renderer=DIGITAL_CROWN_AUTHENTICATED_REACT_SVG`, `source_lock=AUTHENTICATED_GET_AFTER_REAL_UI_UPLOAD`, `model=SOTA_ONNX_38`, statut `uncalibrated=true` / `expert_verified=false` et trois segments SN/NA/NB par étude. Le résumé Actions est corrigé à 7+4 captures. **Aucun contrôle supprimé, aucun seuil de vérification anatomique abaissé.** Aucun changement au moteur, UI, PDF officiel, schéma ou thème.

**Preuve physique supplémentaire** : artefact GitHub [#13419397151](https://github.com/hraaaaf/Digital_crown/actions/runs/42036596943/artifacts/13419397151) réellement téléchargé. Le ZIP contient exactement 16 fichiers, deux `05-real-react-steiner-{anug,challiyan}.png`, deux `06-real-react-steiner-svg-{anug,challiyan}.png`, `report.json`, `source-locked-38-points.json`, pages et radios 38 points. Vérification locale du script de publication **sur le ZIP original extrait : PASS** pour 7 pages, 4 SVG, présence physique (non vides), 2 cas source hashés et authentifiés, SN/NA/NB 6 extrémités par image avec écart **0,0 px** aux coords récupérées. Capture SVG affichée et inspectée pour A et B : **défaut visuel réel** — certains traits/annotations sont prolongés très loin du champ utile / recouvrent les dents et la face, rendu loin du target premium ; ce défaut visuel n'annule pas la preuve source mais réclame un sous-lot renderer SVG/clip/layout distinct avec validation humaine.

**Statuts GitHub** : sur le SHA précédent `6f56dafe...` : [P1 #42036597040](https://github.com/hraaaaf/Digital_crown/actions/runs/42036597040) SUCCESS 6/6, [P2 #42036596939](https://github.com/hraaaaf/Digital_crown/actions/runs/42036596939) SUCCESS synthétique non-clinique 6/6, [frontend #42036597099](https://github.com/hraaaaf/Digital_crown/actions/runs/42036597099) SUCCESS, [R14 #42036596763](https://github.com/hraaaaf/Digital_crown/actions/runs/42036596763) SUCCESS, [Scope #42036596732](https://github.com/hraaaaf/Digital_crown/actions/runs/42036596732) SUCCESS. [Human Visual Approval #42036590517](https://github.com/hraaaaf/Digital_crown/actions/runs/42036590517) FAILURE/NOT APPROVED (indépendant). Nouveau HEAD patch workflow `6f714747...` : [FUE-H #42044846877](https://github.com/hraaaaf/Digital_crown/actions/runs/42044846877) **QUEUED au dernier contrôle**, P1 #42044846884 QUEUED, P2 #42044846823 QUEUED, frontend #42044847130 QUEUED, Scope #42044847104 PENDING ; aucune certification exact SHA prétendue. Le commit documentaire POST engendrera encore un SHA distinct dont la CI devra être jugée séparément.

**NO-GO inchangé** : PR #1213 DRAFT / #1212 clinical DRAFT / master intact. `clinical_validation_available=false`, aucune validation FACAD même cliché, 0/10 FUE patients réels, pas de calibration physique ni PDF patient admissible, COM HOLD, Po_anatomic manquant pour Tweed, Wits CANDIDATE_ONLY, McNamara/Z HOLD, PDF clinique INCOMPLETE. Aucun merge/deploy/EXE.

**NEXT** : vérifier la fin du [FUE-H #42044846877](https://github.com/hraaaaf/Digital_crown/actions/runs/42044846877) exact SHA patch, comparer l'artefact natif source. Une fois ce gate vert, faire **un lot graphique React** dédié pour raccourcir les traits extrêmes et éviter les masquages de l'anatomie, avec thèmes/token hérités et captures BEFORE/AFTER. Ne pas lier validation visuelle à la simple réussite du CI.

**Dernière mise à jour canonique 05/11/2026 — FUE-H rouge expliqué, workflow réparé sans contournement et assertions de preuve du ZIP vérifiées localement ; CI encore à certifier.**

### 47. PRE — 2026-11-05 — V1 Steiner native SVG cleanup (hide off-protocol overlays, no geometry rewrite)

**Utilisateur « Go » après correction FUE-H** : vérifier à jour FUE-H puis nettoyer la véritable superposition SVG de l'app (pas la planche Python). À l'entrée, la PR #1213 DRAFT est au SHA \`05cdfced45f303df3dc5e8e15e0665b5e662865e\`. FUE-H [#42044846877](https://github.com/hraaaaf/Digital_crown/actions/runs/42044846877) sur le commit workflow \`6f714747...\` = SUCCESS, alors que [FUE-H #42045645883](https://github.com/hraaaaf/Digital_crown/actions/runs/42045645883) du HEAD documentaire est encore IN_PROGRESS au relevé. UI Human Visual Approval n'est PAS obtenue ; ne pas transférer le PASS d'un SHA à l'autre.

**Défaut visuel reproduit sur images réelles** (artefact [#13419397151](https://github.com/hraaaaf/Digital_crown/actions/runs/42036596943/artifacts/13419397151)) : 2 captures SVG natif \`06-real-react-steiner-svg-anug/challiyan.png\` montrent des diagonales étendues partant hors du cliché et traversant la bouche et le fond. Les trois segments Steiner SN/NA/NB proprement ancrés dans les 38 repères ONNX sont pourtant corrects, FUE-H 6/6 PASS sur la capture. Le code historique \`frontend/src/features/ortho/CephaloTracingLayerBase.tsx\` au SHA base \`aa7fb556...\` affiche **sans limitation de protocole** \`francfortLineExtended\` (vecteur multiplié ×10), \`mcNamaraLine\` (vecteur ×1000), projections A′/B′ et tissus mous en mode Steiner. Ce sont des overlays visuels non demandés par Steiner. Les masquer pour Steiner n'efface aucune donnée source.

**Pass minimal à implémenter** : conserver le renderer React existant, les 3 lignes SVG et leurs coordonnées, la sécurité COM HOLD et le futur Tweed sans faux Po_anatomic ; empêcher le mode Steiner de rendre des plans \`francfortLineExtended\`/\`mcNamaraLine\`/projections A′ B′/zones incisorales hors protocole ; ne pas modifier les calculs, la calibration, le parser, la DB, les repères. Préserver mode \`all\` historique et modes spécifiques avec guards explicites, palette du thème existante, tests FUE-H négatifs de traits hors-source. Produire de vraies captures React A+B et comparer BEFORE/AFTER aux mêmes JPEG et points. **Tout QA basé sur un nouveau SHA exact et contrôles humains explicites.**

**Blocages** : \`clinical_validation_available=false\`, PO_anatomic absent des 2 radios, COM showCom=false, Wits candidate, McNamara/Z HOLD, PDF clinique INCOMPLETE, 0/10 FUE patients réels, aucune comparaison FACAD goldset. Aucun merge, Vercel, EXE ou validation visuelle auto. **POST seulement après commits + runs + examen des images.**

### 47. POST — 2026-11-05 — suppression des overlays hors protocole dans Steiner natif React (CI AFTER en file)

**PRE** : §47 sur SHA \`34b999401ef36e5421a31cbdf0449947ccf1a6a3\`. Baseline visuelle **réel BEFORE** : artefact original FUE-H #13419397151 du run #42036596943, 2 captures SVG natives \`06-real-react-steiner-svg-anug.png\`/\`...challiyan.png\`. Ce rendu montrait une diagonale McNamara et une Francfort étendue, alors que les données S/N/A/B et les 3 segments Steiner étaient cohérents au GET source.

**Code changé, PR test #1213 DRAFT uniquement** :
- Commit [\`8b9a3ab7228c1dbd84907159129664288ca3c062\`](https://github.com/hraaaaf/Digital_crown/commit/8b9a3ab7228c1dbd84907159129664288ca3c062) : \`frontend/src/features/ortho/CephaloTracingLayerBase.tsx\` conserve \`showSteiner\` et les 3 segments sources SN/NA/NB. Ajoute \`steinerOnly\` dans le renderer, et trois gardes protocolaires de présentation : \`showFrankfortReference\` = \`all|tweed|mcnamara\`, \`showMcNamaraReference\` = \`all|mcnamara\`, \`showTweedIncisorZones\` = \`all|tweed\`. Les lignes étendues Frankfort (×10) et McNamara (×1000), A′/B′ et les wedges incisifs non Steiner ne sont plus rendus pour Steiner. La surface du profil mou ancien n'est plus superposée à Steiner; le mode \`all\` garde son rendu antérieur. Champs DOM de provenance \`data-cephalo-reference-line\` pour les lignes prolongées **seulement dans les modes autorisés**.
- Commit [\`f4dc4ff3e085de3b509265dba618f4536838d53e\`](https://github.com/hraaaaf/Digital_crown/commit/f4dc4ff3e085de3b509265dba618f4536838d53e) : \`frontend/scripts/fue-ceph-r23h-first-use.mjs\` continue à capturer *les vraies radios via l'authentification, l'ONNX et le renderer React*. Après chaque sélection de Steiner, rejette les \`[data-cephalo-reference-line]\` et la légende « McNamara » ; parcourt les lignes SVG et refuse toute coordonnée non finie ou sortant du cadre image natif A \`2272×1818\`, B \`1000×1255\`. L'assertion positive sur SN, NA, NB contre les 38 repères persistés avec 0,05 px demeure. \`report.react_steiner\` expose \`off_protocol_lines=0\` et \`out_of_image_lines=0\` si vraiment observés.
- Vérification **statique de code** au SHA \`f4dc4ff3\`: contrôles programmatiques **7/7 PASS** (seg Steiner conservés, gardes exactes, soft tissue + zones non-Steiner exclues, tests FUE négatifs présents). **Ceci ne prouve PAS encore la compilation TS/React ou le visuel AFTER.**

**CI & preuves** :
- Baseline avant changement (HEAD \`05cdfced45f303df3dc5e8e15e0665b5e662865e\`) totalement validée du point de vue des workflows techniques : [FUE-H #42045645883](https://github.com/hraaaaf/Digital_crown/actions/runs/42045645883) SUCCESS, FUE-P1 #42045645844 SUCCESS, FUE-P2 #42045645876 SUCCESS *synthetic nonclinical*, frontend #42045645839 SUCCESS, Scope #42045645796 SUCCESS, R14 #42045645805 SUCCESS. **Human Visual Approval #42045639088 FAILURE**, non auto-approuvé.
- Nouvelle preuve AFTER sur code SHA \`f4dc4ff3\` **non terminée** au relevé : [FUE-H #42047650164](https://github.com/hraaaaf/Digital_crown/actions/runs/42047650164) QUEUED, [FUE-P1 #42047650051](https://github.com/hraaaaf/Digital_crown/actions/runs/42047650051) QUEUED, [FUE-P2 #42047649955](https://github.com/hraaaaf/Digital_crown/actions/runs/42047649955) QUEUED, [frontend #42047650232](https://github.com/hraaaaf/Digital_crown/actions/runs/42047650232) QUEUED, [Scope #42047650189](https://github.com/hraaaaf/Digital_crown/actions/runs/42047650189) PENDING ; Theme Wave09 IN_PROGRESS, Wave10/11 QUEUED, UI Human Approval QUEUED. **NO FALSE GREEN**, la correction ne peut recevoir ni note visuelle chiffrée ni certification jusqu'à récupération et inspection des nouveaux PNG A/B. Le présent POST documentaire produira un SHA supplémentaire : ne pas transférer CI entre SHAs.

**Données / sécurité** : aucune formule, donnée landmark, échelle mm, diagnostic, endpoint API, schéma DB, PDF clinique, source ONNX, algorithme d'inférence, couleur thème ou token modifié. Aucun merge, déploiement Vercel ou EXE. Le tracé COM non source-verrouillé reste \`showCom=false\`, Tweed reste hors V1 et sans fausse substitution Po→Po_anatomic. \`clinical_validation_available=false\`, 0/10 FUE cabinet réel, Wits candidate, McNamara/Z HOLD, PDF clinique INCOMPLETE, aucun goldset FACAD same-image.

**NEXT** : lire les résultats du FUE-H exact HEAD corrigé et les 2 captures \`06-real-react-steiner-svg-A/B\` AFTER ; comparer réellement aux deux captures BEFORE, puis valider 390/430/768/1280 et faire signer human visual gate par le praticien sans autosignature. En cas d'échec du nouveau test, corriger l'élément SVG spécifique au diagnostic sans effacer l'assertion.
**Dernière mise à jour canonique : 05/11/2026 — POST correction React Steiner + test négatif source-safe ; CI AFTER en file, pas de certification visuelle par anticipation.**


### 48. PRE — 2026-11-05 — vraie source du FUE-H rouge : lignes dentaires anatomiques SVG (pas McNamara)

**Statut au HEAD d'entrée** PR #1213 DRAFT `05e591d12ae3d8c6c90ae6d6f53572b99a2a9fab` : [FUE-H #42048279963](https://github.com/hraaaaf/Digital_crown/actions/runs/42048279963) **FAIL**, [FUE-P1 #42048279965](https://github.com/hraaaaf/Digital_crown/actions/runs/42048279965) **FAIL**, [FUE-P2 #42048279986](https://github.com/hraaaaf/Digital_crown/actions/runs/42048279986) **FAIL**, même cause par dépendance FUE-H. [Build #42048280029](https://github.com/hraaaaf/Digital_crown/actions/runs/42048280029) SUCCESS ; Scope #42048279985 SUCCESS ; R14 #42048279962 SUCCESS ; Theme Waves 9/10/11 SUCCESS. Human Visual Approval #42048270791 FAIL — gate manuel non satisfait. Logs FUE-H : 5 étapes PASS et échec de réouverture sur `Steiner SVG contains out-of-frame construction lines [{"key":null,"values":[-22,0,22,0]},{"key":null,"values":[0,-2000,0,2000]}]` ×2. S, N, A et B ne sont pas en cause.

**Cause exacte prouvée en code** : `frontend/src/features/ortho/components/AnatomicalTooth.tsx` lignes 36-63 définit deux lignes **en repère local** d'un groupe `transform=translate/rotate/scale`, d'où les coordonnées brutes `-22..22` et `-2000..2000`. `CephaloTracingLayerBase.tsx` les rend encore en mode Steiner pour les deux incisives ; la ligne ×2000 peut polluer visuellement le cliché, et le test FUE-H `svg.locator('line')` attribue à tort des valeurs locales non transformées directement au repère image. Les valeurs ne sont **pas** des McNamara ni une preuve de points ONNX erronés.

**Correction source-safe** : ne pas contourner le test ni modifier les coordonnées médicales. Pour Steiner, retirer seulement les **deux décorations dentaires à axe infini** et les remplacer par les vrais segments `U1_apex → U1_incisal` et `L1_apex → L1_incisal`, en réemployant `seg` + couleurs sémantiques existantes. Conserver les protocoles historiques hors Steiner, les points éditables et les segments S–N, N–A, N–B. Faire exiger par FUE-H les **5** segments natifs SN/NA/NB/U1/L1 et leurs extrémités contre le GET authentifié 38 points ; garder zéro débordement des lignes restantes. Aligner le workflow de résumé d'artifact sur les 5 segments. PAS de saut d'étape via filter des lignes ni abandon de contrôle géométrique.

**Périmètre sécurité** : correctif UI non diagnostique et test uniquement, aucune migration, aucun changement de calcul/ONNX, calibration mm nulle, `clinical_validation_available=false`, COM HOLD, Wits CANDIDATE_ONLY, McNamara/Z HOLD, Tweed Po_anatomic non satisfait, PDF clinique INCOMPLETE, 0/10 FUE cabinet réel. Pas de merge ni déploiement Vercel. Tests et vrais screenshots sur nouveau SHA puis §48 POST + Notion.


### 48. POST — 2026-11-05 — suppression des axes dentaires infinis de Steiner, cinq lignes source-lock, CI en cours

**Cause réellement démontrée**, sur le SHA d'entrée `05e591d12ae3d8c6c90ae6d6f53572b99a2a9fab` : les runs FUE-H [#42048279963](https://github.com/hraaaaf/Digital_crown/actions/runs/42048279963) FAIL, P1 #42048279965 FAIL, P2 #42048279986 FAIL. Les logs montrent cinq contrôles FUE-H PASS et l'échec `FRESH_SECOND_BROWSER_REOPEN_BOTH_SOURCES`, sur les éléments SVG `[-22,0,22,0]` et `[0,-2000,0,2000]` exactement tracés dans le composant `frontend/src/features/ortho/components/AnatomicalTooth.tsx` (lignes 47–55) deux fois, via `transform: translate/rotate/scale`. Pas une panne ONNX ou sécurité ; il s'agit de deux axes dentaires décoratifs infiniment prolongés et détectés par les nouveaux tests qui ne distinguaient pas les coordonnées locales du dessin global.

**Correction produit source-safe** commit [`1cefac7467589359a5720a95c0d535a590f13e9d`](https://github.com/hraaaaf/Digital_crown/commit/1cefac7467589359a5720a95c0d535a590f13e9d) : dans **le renderer existant** `frontend/src/features/ortho/CephaloTracingLayerBase.tsx` uniquement, Steiner autorise maintenant les cinq plans `sn,na,nb,u1,l1` ; U1 et L1 sont des segments finis et directement source-anchored `U1_apex → U1_incisal` et `L1_apex → L1_incisal`, réutilisant la fonction `seg` et les couleurs du thème `P.u1`, `P.l1`. `AnatomicalTooth` n'est plus rendu **en Steiner seulement** ; autres modes historiques inchangés, points et édition conservés, aucune modification du component universel AnatomyTooth ni de ses méthodes de déplacement.

**Preuves FUE durcies** : commit [`04030438fac062478ee3890d419dae99c9028c3d`](https://github.com/hraaaaf/Digital_crown/commit/04030438fac062478ee3890d419dae99c9028c3d) dans `frontend/scripts/fue-ceph-r23h-first-use.mjs` : pour **les deux** radios réelles, exiger maintenant les **5 lignes réelles `data-cephalo-line-key=sn,na,nb,u1,l1`** et contrôler leurs deux coordonnées d'extrémités contre les 38 points API GET authentifiés (tolérance 0,05 px). Conserve le test négatif « aucun trait hors protocole, aucune ligne à coordonnée hors du cliché ». Log PASS positif devient `SEGMENTS_SN_NA_NB_U1_L1_SOURCE_LOCKED_NONCLINICAL`. Commit [`bb7e2b8fa8205226ba9b59e9202c3252f6eade35`](https://github.com/hraaaaf/Digital_crown/commit/bb7e2b8fa8205226ba9b59e9202c3252f6eade35) : la publication `.github/workflows/ceph-r23h-fue-first-use.yml` exige désormais réellement les cinq segments dans les deux rapports JSON, en conservant les vérifications strictes des captures et des SHA JPEG originaux. Aucun filtrage du DOM, aucune diminution de contrôles.

**Vérification pré-CI** : la lecture directe des trois fichiers HEAD `bb7e2b8...` a confirmé 4/4 invariants présents : nouveaux segments natifs U1/L1, anciens Tooth infinis désactivés en Steiner, FUE-H vérifie cinq lignes, résumé Actions vérifie cinq lignes. Le code TypeScript/React n'est déclaré compilé ni fonctionnel par ce contrôle statique.

**Actions GitHub au dernier relevé sur SHA `bb7e2b8...`** : [FUE-H #42056581429](https://github.com/hraaaaf/Digital_crown/actions/runs/42056581429) QUEUED ; [FUE-P1 #42056581527](https://github.com/hraaaaf/Digital_crown/actions/runs/42056581527) IN_PROGRESS (installation dépendances) ; [FUE-P2 #42056581563](https://github.com/hraaaaf/Digital_crown/actions/runs/42056581563) QUEUED ; Scope #42056581454 QUEUED ; nouveaux build/frontend, R14, Theme Waves également QUEUED. Le run du code pré-dernier SHA `04030438` [build #42056515815](https://github.com/hraaaaf/Digital_crown/actions/runs/42056515815) SUCCESS ; **ne pas transférer ce SUCCESS au SHA `bb7e2b8`**. [UI Human Visual Approval #42056575524](https://github.com/hraaaaf/Digital_crown/actions/runs/42056575524) FAILURE (gate manuel) et aucun utilisateur n'a approuvé le rendu AFTER. Le POST documentaire peut créer un nouveau SHA ; la CI de ce SHA sera l'autorité finale.

**NEXT** : vérifier le nouvel FUE-H réel exact SHA et son artefact `05-real-react-steiner-A/B`, `06-real-react-steiner-svg-A/B`. Produire une comparaison visuelle BEFORE/AFTER et tests zoom/pointdrag, puis soumettre à validation humaine ; en cas d'échec corriger sans falsifier les angles/repères. Pas de merge ni Vercel ; aucune preuve clinique expert. `clinical_validation_available=false`, 0/10 FUE cabinet réel, COM HOLD, Po_anatomic distinct de Po, PDF clinique INCOMPLETE, Wits candidate, McNamara/Z HOLD.

**Dernière mise à jour canonique : 05/11/2026 — POST §48 code + test + résumé cinq lignes, CI en cours ; aucune note visuelle après à ce stade.**


### 49. PRE — 2026-11-05 — FUE réel zoom/pan/drag Steiner sur 2 radios A+B

**Autorisation** : « Go » du propriétaire pour la passe de test zoom / déplacement manuel et preuves visuelles préparatoires **uniquement**. Ceci n'est pas la signature Human Visual Approval, ni GO merge/Vercel/EXE/activation clinique.

**Baseline** : PR #1213 DRAFT OPEN `test/ceph-v1-facad-two-public-radios-20261105`, HEAD d'entrée `a54216ed2397247e93ce5975c871ef86d1426d96`. [FUE-H #42057053298](https://github.com/hraaaaf/Digital_crown/actions/runs/42057053298) SUCCESS 6/6 ; [P1 #42057053440](https://github.com/hraaaaf/Digital_crown/actions/runs/42057053440) SUCCESS ; [P2 #42057053421](https://github.com/hraaaaf/Digital_crown/actions/runs/42057053421) SUCCESS ; [build TEST #42057053333](https://github.com/hraaaaf/Digital_crown/actions/runs/42057053333) SUCCESS ; Scope/R14 SUCCESS, Human Visual Approval non accordée. Deux radios publiques ANUG/Challiyan, 38 landmarks source GET chacun, 5 segments Steiner stricts `sn,na,nb,u1,l1`, aucun hors cadre. **Aucune étude réelle de patient de cabinet**.

**Goal / preuve** : exécuter dans Playwright sur l'authentique Cephalo Step1 après le parcours ONNX/SVG : zoom 100/150/200 %, pan/reset, alignement des lignes Steiner aux 38 landmarks au zoom, drag d'un point avec recalcul du tracé et contrôle des autres points, evidence UI 390/430/768/1280/1600 quand supportée. Préserver les assertions source-lock et le non-débordement SVG, la palette héritée et les protections auth/tenant. Distinguer vue zoomée et écriture persistée ; ne jamais tirer une interprétation clinique de deux sources publiques.

**NEXT** : ajouter et exécuter des assertions ciblées, inspecter les images AFTER et les artifacts du SHA final ; si défaut réel, ne pas alléger le test ; POST seulement avec résultat réel et limites. `clinical_validation_available=false`, COM HOLD, PDF clinique INCOMPLETE, 0/10 FUE patients cabinet.

**Dernière mise à jour canonique : 05/11/2026 — PRE §49 ; tests zoom/drag PAS ENCORE exécutes sur le nouveau HEAD.**


### 49. POST — 2026-11-05 — FUE P1 zoom 200%, pan, responsive et drag mono-landmark : code intégré, CI non encore conclue

**Travail effectué** : à partir du PRE `1c4ad43196398486b3edd2785065bdab35fd8c81`, commit [230700249e693ea1fbe650d6b6047dfffa8e9ab9](https://github.com/hraaaaf/Digital_crown/commit/230700249e693ea1fbe650d6b6047dfffa8e9ab9) modifie **un seul fichier de test** `frontend/scripts/fue-ceph-p1-authenticated.mjs` : sur vrai Cabinet React de la fixture T2, sélectionner Steiner, exiger exactement les 5 lignes `sn/na/nb/u1/l1`, comparer leurs coordonnées SVG inchangées à chaque 125/150/175/200%, tester pan droit/bas et reset viewBox, interdire toute modification aux 38 repères GET, enregistrer les captures à 100%,150%,200% + pan, puis des screenshots 390/430/768/1280. Le FUE-P1 existant continue le pointer-drag, undo/redo, Save puis reload; l'assertion supplémentaire exige qu'un seul landmark parmi 38 ait changé. **Zéro code produit, source ONNX, formule, DB, token thème, garde sécurité ou workflow modifié.**

**Etat CI pour le HEAD de code 2307002 au relevé** :
- [CI Scope Gate #42063594365](https://github.com/hraaaaf/Digital_crown/actions/runs/42063594365) COMPLETED/SUCCESS ;
- [CEPH R23-H FUE-H genuine first UI uploads with pinned SRPose38 (experimental) #42063590898](https://github.com/hraaaaf/Digital_crown/actions/runs/42063590898) IN_PROGRESS ;
- [CEPH FUE-P2 real calibrated synthetic phantom to draft PDF (nonclinical) #42063590994](https://github.com/hraaaaf/Digital_crown/actions/runs/42063590994) IN_PROGRESS ;
- [CEPH V1 LOT1 isolated frontend TEST build (NO DEPLOY) #42063591282](https://github.com/hraaaaf/Digital_crown/actions/runs/42063591282) COMPLETED/SUCCESS ;
- [CEPH V1 R14 audited hold receipts (NO DEPLOY) #42063591299](https://github.com/hraaaaf/Digital_crown/actions/runs/42063591299) IN_PROGRESS ;
- [CEPH FUE-P1 genuine authenticated journey beyond prior FUE-H (nonclinical) #42063591070](https://github.com/hraaaaf/Digital_crown/actions/runs/42063591070) IN_PROGRESS ;

**Verdict strict** : le build TEST est SUCCESS s'il est indiqué ci-dessus; les nouveaux tests zoom/drag/viewport sont **NOT YET VERIFIED** tant que le job FUE-P1 exact HEAD n'a pas produit rapport et captures. Le présent POST documentaire change encore le HEAD; ne pas transférer l'ancienne CI au nouveau SHA. Une défaillance est un résultat utile, jamais un motif pour assouplir la sécurité. Human Visual Approval **non obtenu**, approbation du propriétaire interdite par auto-simulation. `clinical_validation_available=false`, 0/10 FUE réels cabinet, COM HOLD, PDF clinique INCOMPLETE. PR #1213 toujours DRAFT, aucun merge/Vercel/EXE.

**NEXT exact** : lire les runs FUE-H, P1, P2 et TEST build après le POST sur SHA exact, inspecter JSON/snapshots P1 ; corriger seulement un défaut démontré et refaire preuve. Si tout est vert, soumettre visuels au propriétaire sans présumer son approbation.

**Dernière mise à jour canonique : 05/11/2026 — POST §49, tests renforcés enregistrés, verdict CI FUE-P1 en attente de preuves.**


### 50. POST — 2026-11-05 — CI technique vérifiée au HEAD `3bae5545`, captures P1 et gate visuel humain séparé

**Fait vérifié depuis le POST §49** : PR [#1213](https://github.com/hraaaaf/Digital_crown/pull/1213) OPEN/DRAFT, HEAD **exact** `3bae5545cb86e1641a4a6e2e43b3e187e05622b9` ; 9 workflows techniques exécutés **COMPLETED/SUCCESS** : [FUE-H #42064107508](https://github.com/hraaaaf/Digital_crown/actions/runs/42064107508), [FUE-P1 #42064107584](https://github.com/hraaaaf/Digital_crown/actions/runs/42064107584), [FUE-P2 #42064107409](https://github.com/hraaaaf/Digital_crown/actions/runs/42064107409), [frontend TEST build #42064107231](https://github.com/hraaaaf/Digital_crown/actions/runs/42064107231), [CI Scope #42064107551](https://github.com/hraaaaf/Digital_crown/actions/runs/42064107551), [R14 #42064107596](https://github.com/hraaaaf/Digital_crown/actions/runs/42064107596), [Theme09 #42064107250](https://github.com/hraaaaf/Digital_crown/actions/runs/42064107250), [Theme10 #42064107548](https://github.com/hraaaaf/Digital_crown/actions/runs/42064107548) et [Theme11 #42064107619](https://github.com/hraaaaf/Digital_crown/actions/runs/42064107619). M6-I [#42064107348](https://github.com/hraaaaf/Digital_crown/actions/runs/42064107348) **SKIPPED**, hors scope ; ne pas présenter comme un dixième SUCCESS.

**Preuve de l'exécution réelle** : logs Actions H `R23H_RESULT ... {passed:6,failed:[],studies:2,errors:[]}`, P1 `FUE_P1_RESULT FUE_P1_REAL_UI_SAFE_PARTIAL__DOCUMENT_BLOCKED_CALIBRATION {passed:6,failed:[],clinical_go:false}`, P2 `FUE_P2_RESULT FUE_P2_FULL_WIZARD_PDF_SYNTHETIC_DESIGN_ONLY_NONCLINICAL_PASS {passed:6,errors:[],clinical_release:false}`. Artefact P1 [#13433042066](https://github.com/hraaaaf/Digital_crown/actions/runs/42064107584/artifacts/13433042066), archive ZIP de 28 fichiers, SHA256 **`bb8db82a358e85ae05a9993303a3f755a7f095f5c3965820d60fa2abdf874957`** vérifié localement. Son `ceph-fue-p1-authenticated/report.json` à SHA exact : six checks PASS, `errors=[]`, Steiner natif 5 lignes `sn/na/nb/u1/l1`, zoom 100→125→150→175→200%, pan, reset, géométrie de source inchangée, viewports 390/430/768/1280, drag d'un seul landmark, undo/redo, SAVE/RELOAD réels PASS. Photos UI `05a/b/c`, `05d` 390/430/768/1280 et `06-correction-saved` inspectées ; voir les archives GitHub pour la preuve brute. **Pas de note visuelle clinique ni signature du propriétaire déduite de ces screenshots automatisés.**

**Verdict borné** : **LOT 1/4 CI/FUE technique GREEN au HEAD de code `3bae5545`**, mais **LOT 1/4 scientifique/clinical et Human Visual Approval NO-GO** tant que le praticien n'a pas validé les rendus ; `clinical_validation_available=false`, 0/10 FUE patients cabinet, FACAD same-image goldset absent, calibration vraie et PDF clinique restent à démontrer ; COM HOLD et McNamara/Z HOLD. FUE-P2 concerne **un fantôme synthétique design-only**, pas un patient clinique.

**Effet de cette écriture documentaire** : elle produira un **nouveau HEAD de documentation**, distinct de `3bae5545`. Les 9 SUCCESS listés plus haut **restent attribués à `3bae5545` uniquement** ; CI éventuelle du nouveau SHA doit être consultée de nouveau avant de revendiquer « all green exact-HEAD ». Aucun merge, Vercel, release/EXE ou autosignature.

**NEXT** : présenter les captures et le rendu interactif au praticien, obtenir une approbation explicite et traçable liée au SHA ; sinon conserver la PR DRAFT. Après cela, seulement, organiser les FUE cliniques indépendantes et goldset scientifique.

**Dernière mise à jour canonique : 05/11/2026 — POST §50, preuve CI technique 9/9 green au HEAD `3bae5545`; gate humain et clinique OPEN.**


### 51. PRE — 2026-11-05 — audit contradictoire « chaque analyse » ≠ cinq traits Steiner

**Question du praticien** : exigence d'un bilan céphalométrique complet avant diagnostic ; ne pas présenter les 5 segments FUE `sn/na/nb/u1/l1` comme un Steiner intégral. **HEAD d'entrée** PR #1213 DRAFT `7fa3b602cad079c0d282b363d00db9bea55f9af4`. Autorisation de lecture/audit et mise à jour documentaire seulement ; **pas de modification de formules, modèle ONNX, modes V1, diagnostic, données, thème, merge, Vercel ou EXE**.

**Constats initiaux sourcés au code exact** : `frontend/src/features/ortho/cephaloV1ProtocolScope.ts` n'autorise en V1 que `COM` et `STEINER`; `Step1Cephalo.tsx` affiche exclusivement ces deux valeurs et désactive l'ancien `all`. `CephaloAnalysisWorkbenchPanel.tsx` définit une liste Steiner de **15** IDs et Tweed/Merrifield **4**, mais aucune présence dans cette liste ne garantit une valeur disponible. `CephaloR23G4ReferencePanel.tsx` est une **référence contrôlée et non certifiée** pour COM 10 / McNamara 13 / Ricketts Atlas 33 et Gregoret 13 ; ces panneaux ne sont pas activés comme sélections cliniques V1. `cephalo_protocol_projection.py` n'invente aucune géométrie ni norme; les autres analyses restent fail-closed sans identité/chaîne de preuves. L'étape 3 conserve des zones de notes praticien et des valeurs descriptives sans diagnostic automatique.

**Goal de cette passe** : dresser pour chaque famille V1/référence/hors V1 la composition exacte, disponibilité effective, dépendance landmarks/calibration, déficit de tracé/document et non-certification. Lire aussi les documents de complétude en distinguant audits anciens des contrats runtime actuels. **NEXT** : POST exact par analyse, pas un GO clinique fictif. `clinical_validation_available=false`; 0/10 FUE cabinet réel, Human Visual Approval pending.

**Dernière mise à jour canonique : 05/11/2026 — PRE §51 audit complétude ; aucune nouvelle validation scientifique déclarée.**


### 51. POST — 2026-11-05 — état exact de CHAQUE analyse : composition ≠ calcul ≠ diagnostic

**Source de vérité audité** sur le HEAD documentaire PRE `3ecebfbad82bf72258817e5af166fb88500863c8` (code identique à `7fa3b60`) : `frontend/src/features/ortho/cephaloV1ProtocolScope.ts`, `components/Step1Cephalo.tsx`, `components/Step3Clinical.tsx`, `components/CephaloAnalysisWorkbenchPanel.tsx`, `components/CephaloR23G4ReferencePanel.tsx`, `backend/services/cephalo_runtime_evidence.py`, `cephalo_runtime_chain.py`, `cephalo_protocol_projection.py`, `cephalo_steiner_protocol_evidence.py`, `cephalo_canonical_analysis_v2.py`, profils `backend/data/cephalometry/*protocol_profile_v1.json` et `clinical_reference_profiles_v1.json`, plus audits de complétude historiques. **Aucun changement produit ni algorithme lors de cette passe.**

**V1 réellement sélectionnable : 2 analyses seulement** — COM Digital Crown et Steiner. `analysis='all'` est un fallback historique désactivé dans le selector et n'est pas une union source-lockée. `Step3Clinical.tsx` propose seulement COM/STEINER, champs descriptifs et notes praticien sans synthèse diagnostique autonome.

**Steiner : 15 mesures définies (11 BASE 1953 + 4 extension 1959), PAS 15 valeurs garanties.** SNA/SNB/ANB ; U1–NA°/mm, L1–NB°/mm, inter-incisif, plan occlusal–SN, SN–GoGn, L1–GoGn ; SND, Pog–NB mm, L1–D line mm/°. Les angles principaux peuvent disposer de preuve typée ; lignes mm nécessitent calibration prouvée ; d'autres nécessitent `Gn_anatomic`, `D_Steiner_1959`, `U1_facial_surface`, `L1_facial_surface`, `Occ_Steiner_Ant/Post`, `Pog_hard`. Les identifiants automatiques homonymes ne sont pas des équivalents historiques autorisés. L'UI déclare `15` lignes et `n/15` calculées, éventuellement NC. Le FUE-H strict de **cinq segments** `sn,na,nb,u1,l1` ne couvre pas les 15 constructions et encore moins leur validité clinique. Le champ `final_gate=SATISFIED` dans le profil est un **gate de composition/source-lock** de la bibliothèque, pas une approbation anatomique individuelle ou clinique ; le label « Steiner complet 1953 + 1959 » doit préciser l'état de calcul et de validation réelle.

**COM Digital Crown : 10 facteurs de synthèse historiques internes, pas une analyse de référence scientifique universelle** : surplomb, recouvrement, IMPA, U1/FH, inter-incisif, FMA/angle de Tweed, A′B′, A→Nperp, B→Nperp, profondeur faciale DC. Mélange de constructions dental/Tweed/CRANIOM/DC, souvent calibrées pour les mm, version legacy Po-Or. `B→Nperp` ≠ Pog→Nperp de McNamara ; `U1/FH` ≠ FMIA du triangle Tweed. L'onglet COM est V1 accessible, mais référence R23-G4 en lecture seule avec valeurs NULL/NC si preuve runtime absente et aucune norme diagnostique universelle.

**Tweed–Merrifield : 4 mesures définies, NON sélectionnable en V1** : FMA, IMPA, FMIA et angle Z de Merrifield (distinct de Tweed). Variante DC `Po_anatomic–Or / Go–Me`, **pas stricte équivalence historique ear-rod Tweed 1954**. Po détecté automatique ≠ Po_anatomic source-autoritaire ; Merrifield Z orientation V1 en revue et sans classification automatique. Profil final_gate=OPEN. Présence de code et du tableau Workbench historique ≠ mode cliniquement disponible.

**McNamara 1984 : 13 facteurs documentés au ledger, NON sélectionnable en V1** : A–Nperp, SNA, Co–Gn, Co–A, différentiel Co–Gn − Co–A, ANS–Me, FH/mandibulaire, facial axis, Pog–Nperp, U1/A vertical, L1/A–Pog, pharynx supérieur/inférieur. Dans les 13 contrats, **5 ont une mention explicite BLOCKED/IMPLEMENTATION_MISSING** : facial axis, deux mesures dentaires à surfaces exactes et deux mesures voies aériennes ; les 8 autres ne sont PAS toutes garanties mesurables car calibration/anatomie/GET requis. Vue R23-G4 lecture seule, pas diagnostic.

**Ricketts : deux variantes de protocole hors sélection V1, non interchangeables** : Atlas 2009 **33 facteurs = 10 EXECUTABLE + 23 CONDITIONAL_EXECUTABLE dans la définition de bibliothèque** ; Gregoret résumé **13 = 7 EXECUTABLE + 6 CONDITIONAL_EXECUTABLE**. L'étiquette EXECUTABLE ne garantit **pas** valeur disponible chez un patient (Po anatomique, Pt_Ricketts, Xi/Pm/CF, identité molaire/canine exacte, plan occlusal, calibration, orientation). Les profils R23-G4 sont lecture seule et n'autorisent ni classification ni source géométrique imaginaire. **Pas de pipeline radiographique PA/frontale ni validité transversale par seule radio latérale.**

**Wits/Downs/autres** : Wits Jacobson reste non promu en protocole V1 ; ancien `Wits_Appraisal` quarantaine faute de plan occlusal/version et signe fiables. Downs possède au moins deux géométries angulaires (facial angle / Y axis) typées, pas analyse autonome complète V1. « Toutes analyses » n'est ni fusion exhaustive, ni consensus scientifique ou interprétation dentaire autorisée.

**Système de diagnostic** : `cephalo_runtime_evidence.py` écrit des champs `findings/diagnoses/problems/objectives/treatment_options/validations/final_plans` **vides** ; `Step3Clinical.tsx` propose des mesures descriptives et des zones de saisie libre avec mention d'origine historique non vérifiée ; `cephalo_r15_clinical_studio.py` conserve `clinical_validation_available=false` sans snapshot praticien autoritatif ; `cephalo_pdf_projection.py` conditionne la sortie complète à `clinical_validation_available` et zéro blockers. FUE-H/P1/P2 9 workflows verts au SHA antérieur `3bae5545` **ne sont PAS une validation de toutes les méthodes ni d'un PDF diagnostique complet** ; P2 = fantôme nonclinique.

**Verdict** : une interface doit séparer `PROFILE_DEFINED`, `MEASUREMENT_AVAILABLE`, `LANDMARK_VERIFIED`, `CALIBRATED`, `NORM_APPLICABLE`, `EXPERT_APPROVED`, `CLINICAL_COMPLETE`, avec numérateur/denominateur par patient et raison NC. Priorité scientifique : complétude effective et visibilité du Steiner (mesures, géométries, preuve source et rapport) et clarifier statut COM V1 avant ouverture d'autres méthodes ; puis Tweed/Merrifield, McNamara, Ricketts versionnés, Wits/Downs, puis synthèse multi-analyses selon preuves. Un diagnostic orthodontique complet requiert en plus examen clinique, occlusion, profil/tissus mous, croissance, imagerie appropriée et validation praticien ; pas de diagnostic automatisé depuis 38 landmarks latéraux.

**Limites** : audit de composition code/runtime, **pas** exécution d'une nouvelle radio patient avec inspection des `n/15`, et aucune mesure clinique individuelle réalisée. Pas de merge, Vercel, EXE ni déclaration de GO clinique. Ce POST crée un SHA documentaire distinct ; CI du SHA précédent ne lui est pas attribuable sans recontrôle.

**Dernière mise à jour canonique : 05/11/2026 — POST §51, matrice de complétude exacte ; nonclinical/clinical HOLD maintenu.**


### 52. PRE — 2026-11-05 — Steiner 15/15 runtime per actual ONNX38 public fullfilms

**Demande / autorisation** : « Next » après diagnostic d'incomplétude. Contrôle du fichier canonique unique **avant** passe, HEAD initial de PR DRAFT #1213 `48beec3b9641a37c59cb0411182ccfd5fc690627`, audits §51 et Roadmap/AGENTS lus. Notion PRE55 enregistré. Aucun déplacement des gates cliniques.

**Constat précis** : `frontend/scripts/fue-ceph-r23h-first-use.mjs` prouve deux radio authentiques publiques (ANUG 2014 et Challiyan 2023), 38 landmarks via ONNX38 réel, image SHA/original, persistance autorisée, UI native React SVG Steiner 5 axes et sécurité entre cabinets ; **ne publie aucune grille des 15 mesures individuelles issues du read-path actif**. `backend/routers/cephalo_analysis_read.py` retourne `project_runtime_chain_read_path` dans `out.angles_data`; `cephalo_protocol_projection.py` expose `scientific_read_path.protocol_profiles.steiner.rows` (11 base + 4 extension), `availability_status`, valeur ou null, measurement refs, source method et classification_authority false ; `cephalo_runtime_chain.py` valide la chaîne active.

**Goal / Success observable** : ajouter au FUE-H (sans modifier le produit médical, backend ni les formules) un audit indépendant depuis **GET authentifié réellement persisté et rouvert** sur **chacun des deux clichés**, sauvegardé comme JSON machine-readable dans l'artefact existant : les 15 identités uniques exactes, ordonnées, `AVAILABLE` seulement si valeur numérique finie + provenance méthode/measurement et `NC` si indisponibilité, absence de millimètres inventés quand calibration non vérifiée, aucun statut normatif clinique. Le script doit **échouer sur une contradiction de sécurité** mais **ne pas transformer l'absence d'un point nécessaire en un faux défaut clinique**. Zéro patient vrai, zéro diagnostic, zéro inférence de norme.

**Plan** : instrumenter `frontend/scripts/fue-ceph-r23h-first-use.mjs` avec garde read-path et rapport par radio, CI H/P1/P2 exact SHA ; relever `n/15` seulement d'un `report.json` GitHub Actions réellement exécuté. Même si le test devient vert, FUE clinique 0/10, FACAD same-image absent, Human Visual Approval OPEN. Déploiement/Fusion/EXE non autorisés.

**Dernière mise à jour canonique : 05/11/2026 — PRE §52, témoin réel 15/15 à créer, aucun résultat patient revendiqué.**


### 52. POST — 2026-11-05 — FUE-H 15/15 Steiner authentifié ajouté sur deux radios publiques, verdict CI encore ouvert

**Modification réellement poussée** : [commit `4517fd55c4357763510abd3ddeac8098fa4f685f`](https://github.com/hraaaaf/Digital_crown/commit/4517fd55c4357763510abd3ddeac8098fa4f685f), **seulement** `frontend/scripts/fue-ceph-r23h-first-use.mjs` (test/playwright FUE-H), aucune modification du moteur, ONNX, UI, thème, base ou PDF. Contrôle ajouté `STEINER_15_READPATH_COVERAGE` après les deux véritables réouvertures dans le navigateur et GETs autorisés, sans injection de landmarks/mesures. Source via `GET /api/ia/analyses/{id}` → `scientific_read_path` `authority=EVIDENCE_GRAPH_V1`, `active_chain=VERIFIED`, `protocol_profiles.steiner`, `STEINER_STATIC_PROTOCOL_PROFILE_V1` source-lock. Correspondance stricte des 15 IDs en ordre, vérification `AVAILABLE` = numérique fini avec `measurement_refs` et `value_authority_method_id`; `NC` = valeur null; toutes `classification_authority=false`; aucune mesure `_MM_` autorisée tant que `is_calibrated=false`. Résultats par ANUG/Challiyan avec SHA-256 image, compte `available_count/nc_count`, identités/statuts/méthodes/refs et contexte NC, fichier nouveau `artifacts/ceph-r23h-first-use/steiner-15-coverage.json` et copie dans `report.json`. La CI H/ P1 / P2 utilise le même script réel; l'archive H l'exposera.

**Résultat établi AUJOURD'HUI** : la couverture instrumentée est commitée et le script relu après commit, mais **aucun résultat réel n/15 n'a encore été produit ou observé sur ce nouvel exact HEAD** ; les runs étaient QUEUED juste après le commit. Ne pas inventer « 15/15 calculés », ni même une valeur disponible. La présence de 15 colonnes/IDs source-locked ne prouve pas les 15 mesures cliniques exactes. Aucun bilan normatif, diagnostic, classification, goldset expert, approbation visuelle ou PDF clinique autorisé. Les deux clichés restent publics, patient fictif et environnement T2 disposable ; **0/10 FUE cabinet réel**.

**Runs associés au commit de test `4517fd55` au premier relevé** : [FUE-H #42073619787](https://github.com/hraaaaf/Digital_crown/actions/runs/42073619787) QUEUED, [FUE-P1 #42073619680](https://github.com/hraaaaf/Digital_crown/actions/runs/42073619680) QUEUED, [FUE-P2 #42073619648](https://github.com/hraaaaf/Digital_crown/actions/runs/42073619648) QUEUED, [Build #42073619833](https://github.com/hraaaaf/Digital_crown/actions/runs/42073619833) QUEUED, [Scope #42073620062](https://github.com/hraaaaf/Digital_crown/actions/runs/42073620062) QUEUED, R14/Theme09/10/11 QUEUED ; M6-I SKIPPED hors scope. Résultat 9/9 vert ancien uniquement HEAD `48beec3`, **pas transféré** à `4517fd55` ni au futur commit documentaire POST.

**Risques encore OPEN** : statut réel NC expliqué de façon prudente ; `nc_context` pour mm associe calibration non vérifiée mais ne prétend **pas** identifier l'unique cause si landmark requis aussi absent ; pour angles, absence ou invalidité de source ne permet aucune inférence anatomique. La preuve H donne les n/15 disponibles *techniquement* sur deux clichés, pas la précision des repères ni la parité avec FACAD/goldset sur mêmes images, et ne débloque ni travaux ultérieurs ni clinique.

**NEXT concret** : obtenir l'artefact exact-HEAD et reporter les comptes ANUG/Challiyan avec 15 lignes chacune ; isoler les NC par origine de preuve, cible bornée par source, calibration réelle et validation praticien, avec FUE adversariale négative. Aucun merge, déploiement Vercel ni EXE.

**Dernière mise à jour canonique : 05/11/2026 — POST §52, test H Steiner 15/15 ajouté, n/15 exact observé en attente de CI.**


### 53. PRE — 2026-11-05 — lecture indépendante de l’artefact FUE-H exact HEAD (Go)

**Sources relues avant conclusion** : PR #1213 DRAFT HEAD \`dee9ac93ae45c1b4db47f53bb9cbe9532549b837\` ; canonique §52 ; Notion PRE56. FUE-H [#42073826915](https://github.com/hraaaaf/Digital_crown/actions/runs/42073826915) **SUCCESS** et archive [#13437698027](https://github.com/hraaaaf/Digital_crown/actions/runs/42073826915/artifacts/13437698027), ZIP SHA256 \`57708828e040f6c448d79c9fc887d474a46b4e1f3afe79f093a595c2128f24bf\` **égal au digest GitHub**. Source interne \`steiner-15-coverage.json\` \`head=dee9ac93...\`; \`report.json\` \`errors=[]\` et check \`STEINER_15_READPATH_COVERAGE: PASS\`. Deux images publiques sourcées par SHA256 et traitement réel ONNX38, patient T2 fictif, 0 patient clinique.

**Objectif** : contrôler les 30 cellules de mesure, classifier les NC par contrat de point et calibration, établir les priorités de prochaine FUE sans inventer 15/15, sans altérer les formules ni diagnostiquer.

### 53. POST — 2026-11-05 — Steiner observé 6/15 ANUG, 6/15 Challiyan : 9 NC expliqués

**Preuve** : [FUE-H #42073826915](https://github.com/hraaaaf/Digital_crown/actions/runs/42073826915) et \`steiner-15-coverage.json\` téléchargé, extrait et vérifié localement ; tête source \`dee9ac93ae45c1b4db47f53bb9cbe9532549b837\` ; schéma \`CEPH_STEINER_15_NONCLINICAL_V1\`, \`clinical_release=false\`, \`source=AUTHENTICATED_GET\`. Runs **9/9 SUCCESS** à ce SHA, M6-I SKIPPED hors scope : H [#42073826915](https://github.com/hraaaaf/Digital_crown/actions/runs/42073826915), P1 [#42073827296](https://github.com/hraaaaf/Digital_crown/actions/runs/42073827296), P2 [#42073827032](https://github.com/hraaaaf/Digital_crown/actions/runs/42073827032), frontend [#42073826830](https://github.com/hraaaaf/Digital_crown/actions/runs/42073826830), Scope [#42073826918](https://github.com/hraaaaf/Digital_crown/actions/runs/42073826918), R14 [#42073826781](https://github.com/hraaaaf/Digital_crown/actions/runs/42073826781), Theme09 [#42073827093](https://github.com/hraaaaf/Digital_crown/actions/runs/42073827093), Theme10 [#42073826748](https://github.com/hraaaaf/Digital_crown/actions/runs/42073826748), Theme11 [#42073827403](https://github.com/hraaaaf/Digital_crown/actions/runs/42073827403).

**30 résultats du read-path actif, 15 identités ordonnées sur les deux clichés** (aucun résultat clinique validé) :

| Steiner / canonical ID | ANUG | Challiyan | Disponibilité des deux |
|---|---:|---:|---|
| SNA · \`M_SNA_DEG_V1\` | 79,1° | 79,9° | AVAILABLE |
| SNB · \`M_SNB_DEG_V1\` | 77,7° | 74,6° | AVAILABLE |
| ANB · \`M_ANB_DEG_V1\` | 1,4° | 5,3° | AVAILABLE |
| U1–NA angle · \`M_U1_NA_DEG_V1\` | 32,5° | 20,8° | AVAILABLE |
| U1–NA mm · \`M_U1_NA_MM_V1\` | NC | NC | NOT_COMPUTABLE |
| L1–NB angle · \`M_L1_NB_DEG_V1\` | 34,6° | 34,2° | AVAILABLE |
| L1–NB mm · \`M_L1_NB_MM_V1\` | NC | NC | NOT_COMPUTABLE |
| Inter-incisif · \`M_INTERINCISAL_DEG_V1\` | 111,4° | 119,6° | AVAILABLE |
| Plan occlusal–SN · \`M_OCCLUSAL_PLANE_SN_DEG_V1\` | NC | NC | NOT_COMPUTABLE |
| SN–GoGn · \`M_SN_GOGN_DEG_V1\` | NC | NC | NOT_COMPUTABLE |
| L1–GoGn · \`M_L1_GOGN_DEG_V1\` | NC | NC | NOT_COMPUTABLE |
| SND · \`M_SND_DEG_V1\` | NC | NC | NOT_COMPUTABLE |
| Pog–NB mm · \`M_POG_NB_MM_V1\` | NC | NC | NOT_COMPUTABLE |
| L1–D-line mm · \`M_L1_DLINE_MM_V1\` | NC | NC | NOT_COMPUTABLE |
| L1–D-line angle · \`M_L1_DLINE_DEG_V1\` | NC | NC | NOT_COMPUTABLE |

**Scores bornés** : ANUG **6 AVAILABLE / 9 NC / 15** ; Challiyan **6 / 9 / 15**. 6/15 = **40 % de couverture de rangées calculées sur ces deux clichés non calibrés**, **pas l'avancement global du lot ni l'exactitude orthodontique**. Les six disponibles sont des angles produits par ONNX38 non expert-vérifiés. Aucun résultat mm n'est exposé, conformément à \`is_calibrated=false\` et \`mm_per_pixel=null\`.

**Causes techniques identifiées via les contrats du backend** \`backend/services/cephalo_steiner_protocol_evidence.py\` et \`steiner_protocol_profile_v1.json\`, plus les 38 IDs exacts de l'artefact (les 38 contiennent \`Gn\` et \`D_point\` mais **pas** \`Gn_anatomic\` ni \`D_Steiner_1959\`) :

- **Quatre NC en mm** : \`U1–NA mm\` = \`U1_facial_surface\` explicite + calibration ; \`L1–NB mm\` = \`L1_facial_surface\` explicite + calibration ; \`Pog–NB mm\` = \`Pog_hard\` (seul alias \`Pog→Pog_hard\` sur modèle certifié) + calibration ; \`L1–D mm\` = \`L1_facial_surface\`, \`D_Steiner_1959\`, \`Gn_anatomic\` + calibration. La calibration manquante est un blocker certain pour les quatre ; absence des surfaces/D/Gn est un blocker additionnel pour les cas concernés, **sans inférer qu'une présence nominale du détecteur suffit**.
- **Cinq NC angulaires** : plan occlusal–SN exige \`Occ_Steiner_Ant\` + \`Occ_Steiner_Post\` exacts ; SN–GoGn et L1–GoGn exigent \`Gn_anatomic\` ; SND exige \`D_Steiner_1959\` ; L1–D° exige \`D_Steiner_1959\` + \`Gn_anatomic\`. Aucun de ces points n'est automatiquement substituable par \`D_point\`, \`Gn\` détecté ou un plan occlusal approximatif. Leur null est une **protection scientifique**, pas neuf défauts de formules démontrés.
- **Source UI existante** : \`frontend/src/features/ortho/cephaloSteinerProtocol.ts\` expose **six identités à placer manuellement ou selon construction contrôlée** (\`Gn_anatomic\`, \`U1_facial_surface\`, \`L1_facial_surface\`, \`D_Steiner_1959\`, \`Occ_Steiner_Ant\`, \`Occ_Steiner_Post\`) ; \`Step1CephaloBase.tsx\` a un handler de placement explicite et une calibration manuelle. **Existence de ce code ≠ preuve que placement→save→reload→recalcul débloque une mesure sur cliché réel**. Ce parcours n'est pas encore FUE-certifié pour les six identités.
- Le rapport FUE-H \`nc_context\` est intentionnellement générique, **pas un diagnostic automatique des raisons exactes par la chaîne** ; les dépendances ci-dessus sont déduites des contrats sources et de l'absence d'IDs autoritaires, non des champs \`nc_context\` seuls.

**Prochain sous-lot recommandé, dans cet ordre** : 1) FUE interactive réelle de placement des six identités, sauvegarde et reload sur fixture/clique image autorisée, avec provenance sans alias ; test négatif de déplacement/absence/doublons ; 2) calibration **uniquement** sur un fantôme de référence physique connu ou source cliniquement étalonnée autorisée (jamais inventer une distance sur ANUG/Challiyan) et maintien des mm à NC sinon ; 3) vérifier recalcul stable, 15 géométries/tracés et transmission du rapport ; 4) contrôle expert sur goldset indépendant (mêmes images) et validation humaine séparée. Ne pas promettre 15/15 en clinique simplement avec le placement.

**Périmètre exécuté** : audit complet de l'artefact existant, ZIP vérifié avec digest GitHub, fichiers indépendants de lecture/export ; **aucune modification du produit** ni du modèle, aucune image patient privé, aucun merge, Vercel, EXE ou signature clinique. La présente mise à jour **documentaire** génère un nouveau HEAD : les 9 SUCCESS cités restent attachés au SHA de preuve \`dee9ac93\`, pas automatiquement au SHA documentaire ultérieur.

**Dernière mise à jour canonique : 05/11/2026 — POST §53, couverture Steiner 6/15 sur ANUG et Challiyan, prochain FUE six placements/correction.**


### 54. PRE — 2026-11-05 — audit source 38 canaux SRPose → identités Steiner, auto-first sans aliases inventés

**Mission GO** : auditer l'intégralité des 38 sorties SRPose38 et comparer la provenance d'index, leur ID Digital Crown, les définitions anatomiques verrouillées et les dépendances exactes des 15 lignes du Steiner. Proposer le chemin d'automatisation défendable avant une quelconque mutation clinique, sans imposer la pose manuelle de six points par défaut. Notion **PRE57** enregistré ; HEAD de départ `399941cecd77f4315e63f816ea5353ae147a4954` dans PR #1213 DRAFT, non mergée ; `AGENTS.md` et roadmap V1 lus.

**Sources techniques retenues** : `backend/services/srpose38_contract.py` (dictionnaire 0..37), `docs/SRPOSE38_LANDMARK_CONTRACT.md` (table officielle CL index/name/ID, ambiguïtés), `docs/audits/CEPHALO_SRPOSE38_PROVENANCE.md` (audit source checkpoint exact et limitation sémantique), `docs/audits/CEPHALO_VNEXT_LOT03_LANDMARK_ATLAS.md` (cohérence d'IDs), `backend/services/cephalo_landmark_identity_bridge.py` (alias versionnés fail-closed), `backend/services/cephalo_steiner_protocol_evidence.py` et profil Steiner `backend/data/cephalometry/steiner_protocol_profile_v1.json`.

**Point critique établi d'emblée** : modèle ONNX SRPose38 certifié en parité et exact ordre 38 canaux, **mais son checkpoint source publié nomme les catégories numériquement 0–37 sans définir leurs identités anatomiques** (audit de provenance du 15/09/2026). L'inventaire local nomme 38 points ; il ne constitue **pas** une validation anatomique exhaustive des canaux du modèle. Le modèle livre `Gn`, `D_point` et `U6/L6` génériques, non les ancres `Gn_anatomic`, `D_Steiner_1959`, `Occ_Steiner_Ant/Post` ou les surfaces coronaires requises. Ne pas dégrader les protections, ne pas créer de mm sans étalon réel, aucune adaptation produit sans définition autoritative.

**Success observable** : liste exhaustive 38/38, matrice dépendances 15/15 et verdict par groupe `DIRECT_GEOMETRY_CURRENT`, `ALIAS_ONLY_IF_PROVEN`, `CONSTRUCTION_SOURCE_LOCK_REQUIRED`, `MISSING_NEW_LANDMARK`, `CALIBRATION_REQUIRED`; recommandations de FUE pour l'auto-first avec alternatives vérifiables. Pas de merge, Vercel, EXE, données patients ni diagnostic ; validation clinique HOLD.

**Dernière mise à jour canonique : 05/11/2026 — PRE §54, étude 38 points en cours.**


### 54. POST — 2026-11-05 — Audit 38/38 SRPose et 15/15 Steiner : auto-first, véritables gaps distingués

**FUE-0 exécuté sur les sources du HEAD PRE `6132b56ed03f423ceb5c3e70cf86a9a105951ce6`** : parsing indépendant de `backend/services/srpose38_contract.py` vs la table `docs/SRPOSE38_LANDMARK_CONTRACT.md`. **38 entrées, index 0–37 contigus, 38/38 IDs Digital Crown identiques dans le même ordre, zéro collision/mismatch.** Profil `steiner_protocol_profile_v1.json` : **15 identifiants uniques (11 BASE 1953 + 4 EXTENSION 1959)**. Ceci démontre la cohérence **locale** code ↔ contrat documentaire, PAS une validation anatomique amont du checkpoint.

**Important — objection du praticien résolue** : une fois les coordonnées de landmarks anatomiquement corrects connues, droites, plans, angles et projections se construisent de façon déterministe ; aucun marquage manuel systématique ni LLM ne doit être requis. Le moteur possède déjà des formules pour les 15 facteurs. La difficulté résiduelle porte sur les **identités et certains points géométriques non fournis**, plus calibration pour les mm.

**Matrice exhaustive de disposition des 38 canaux (usage Steiner uniquement, pas certification médicale)** :

| Index ONNX | ID logiciel exact | Portée dans ce Steiner 15 |
|---:|---|---|
| 00 | `S` | `GEOMETRY_INPUT_CURRENT` |
| 01 | `N` | `GEOMETRY_INPUT_CURRENT` |
| 02 | `Or` | `NOT_USED_IN_STEINER15` |
| 03 | `Po` | `NOT_USED_IN_STEINER15` |
| 04 | `A` | `GEOMETRY_INPUT_CURRENT` |
| 05 | `B` | `GEOMETRY_INPUT_CURRENT` |
| 06 | `Pog` | `ALIAS_POG_HARD_CONDITIONAL` |
| 07 | `Me` | `NOT_USED_IN_STEINER15` |
| 08 | `Gn` | `NEEDS_EXACT_STEINER_IDENTITY` |
| 09 | `Go` | `GO_VARIANT_HOLD` |
| 10 | `L1_incisal` | `GEOMETRY_INPUT_CURRENT` |
| 11 | `U1_incisal` | `GEOMETRY_INPUT_CURRENT` |
| 12 | `Ls_soft` | `NOT_USED_IN_STEINER15` |
| 13 | `Li_soft` | `NOT_USED_IN_STEINER15` |
| 14 | `Sn_soft` | `NOT_USED_IN_STEINER15` |
| 15 | `Pog_soft` | `NOT_USED_IN_STEINER15` |
| 16 | `PNS` | `NOT_USED_IN_STEINER15` |
| 17 | `ANS` | `NOT_USED_IN_STEINER15` |
| 18 | `Ar` | `NOT_USED_IN_STEINER15` |
| 19 | `D_point` | `NEEDS_EXACT_STEINER_IDENTITY` |
| 20 | `U1_apex` | `GEOMETRY_INPUT_CURRENT` |
| 21 | `L1_apex` | `GEOMETRY_INPUT_CURRENT` |
| 22 | `Cm` | `NOT_USED_IN_STEINER15` |
| 23 | `Ptm` | `NOT_USED_IN_STEINER15` |
| 24 | `Co` | `NOT_USED_IN_STEINER15` |
| 25 | `Prn` | `NOT_USED_IN_STEINER15` |
| 26 | `Ba` | `NOT_USED_IN_STEINER15` |
| 27 | `PT_point` | `NOT_USED_IN_STEINER15` |
| 28 | `Bo` | `NOT_USED_IN_STEINER15` |
| 29 | `Ls2` | `NOT_USED_IN_STEINER15` |
| 30 | `Li2` | `NOT_USED_IN_STEINER15` |
| 31 | `Gn_soft` | `NOT_USED_IN_STEINER15` |
| 32 | `Me_soft` | `NOT_USED_IN_STEINER15` |
| 33 | `G_soft` | `NOT_USED_IN_STEINER15` |
| 34 | `N_soft` | `NOT_USED_IN_STEINER15` |
| 35 | `C_point` | `NOT_USED_IN_STEINER15` |
| 36 | `U6` | `GENERIC_MOLAR_SEMANTIC_HOLD` |
| 37 | `L6` | `GENERIC_MOLAR_SEMANTIC_HOLD` |

**Synthèse exhaustive** : 8 canaux alimentent actuellement les six angles calculés ; `Go` est requis par des angles bloqués et conserve un hold de **variante de Gonion** ; `Pog` peut être projeté conditionnellement en `Pog_hard` via `cephalo_landmark_identity_bridge.py` seulement avec provenance SRPose38 certifiée ; `Gn` et `D_point` sont **2 canaux candidats à une équivalence anatomique ciblée, non prouvée** ; `U6`/`L6` sont des molaires **génériques** ne prouvant ni cuspide exacte ni plan occlusal Steiner ; les **24 autres** n'alimentent aucune des 15 mesures actives. La somme des catégories = **38/38**. Aucune identité supplémentaire ne doit être créée par ressemblance de nom.

**Matrice exhaustive des 15 mesures sur les deux radios publiques réelles ONNX38 (preuve FUE-H HEAD `dee9ac93`)** :


| Facteur | Code | Cas publics | Dépendance qui bloque l'automatisation manquante |
|---|---|---|---|
| SNA | M_SNA_DEG_V1 | AVAILABLE 2/2 | S,N,A par mapping local ; expertise goldset non faite |
| SNB | M_SNB_DEG_V1 | AVAILABLE 2/2 | S,N,B ; même réserve |
| ANB | M_ANB_DEG_V1 | AVAILABLE 2/2 | S,N,A,B ; même réserve |
| U1–NA° | M_U1_NA_DEG_V1 | AVAILABLE 2/2 | U1 apex/incisal,N,A ; même réserve |
| U1–NA mm | M_U1_NA_MM_V1 | NC 2/2 | U1_facial_surface explicite absent + calibration physique manquante |
| L1–NB° | M_L1_NB_DEG_V1 | AVAILABLE 2/2 | L1 apex/incisal,N,B ; même réserve |
| L1–NB mm | M_L1_NB_MM_V1 | NC 2/2 | L1_facial_surface explicite absent + calibration |
| Inter-incisif | M_INTERINCISAL_DEG_V1 | AVAILABLE 2/2 | 2 axes incisifs ; même réserve |
| Occlusal–SN | M_OCCLUSAL_PLANE_SN_DEG_V1 | NC 2/2 | Occ_Steiner_Ant/Post absents ; construction précise 1953 non matérialisée automatiquement |
| SN–GoGn | M_SN_GOGN_DEG_V1 | NC 2/2 | Gn_anatomic absent ; Gn détecteur similaire en nom, contrat exact non prouvé ; version Go à clarifier |
| L1–GoGn | M_L1_GOGN_DEG_V1 | NC 2/2 | Gn_anatomic absent ; version Go à clarifier |
| SND | M_SND_DEG_V1 | NC 2/2 | D_Steiner_1959 absent ; D_point non équivalent attesté |
| Pog–NB mm | M_POG_NB_MM_V1 | NC 2/2 | Pog_hard alias conditionnel existant, calibration absente |
| L1–D mm | M_L1_DLINE_MM_V1 | NC 2/2 | L1_facial_surface + D_Steiner_1959 + Gn_anatomic + calibration |
| L1–D° | M_L1_DLINE_DEG_V1 | NC 2/2 | D_Steiner_1959 + Gn_anatomic dans contrat de construction ; axe perp. à GoGn |


**Différence essentielle** : les six ancres Steiner absentes du mapping direct sont `Gn_anatomic`, `D_Steiner_1959`, `U1_facial_surface`, `L1_facial_surface`, `Occ_Steiner_Ant`, `Occ_Steiner_Post`. `Pog_hard` est un 7e ID absent du mapping brut mais dispose déjà de **l'alias versionné conditionnel** `Pog → Pog_hard`. La règle actuelle `EXPLICIT_ONLY_CANONICAL_IDENTITIES` bloque légitimement `Gn_anatomic`. L'UI permet un secours manuel mais ne prouve pas un parcours clinique autosuffisant.

**Autorité de la source, recoupée avec sources publiques** :
- `docs/audits/CEPHALO_SRPOSE38_PROVENANCE.md` (audit 15/09/2026) a vérifié le repo source du checkpoint exact SRPose/CL-Detection : dataset MMPose déclaré sous numéros `0..37`, **sans nomenclature anatomique** associée à ces numéros. Le mapping `S,N,...L6` est un contrat **local**, historiquement annoncé sans table primaire attachée ; `LEGACY_LOCAL_MAPPING / SOURCE_LOCK_REQUIRED`. La table locale cohérente 38/38 ne ferme **pas** cette incertitude.
- Article du challenge `https://arxiv.org/html/2409.15834v1` : 600 clichés / 38 landmarks ; la figure 3 **illustre** leur anatomie mais, sans lien vérifiable à la **numérotation des annotations effectivement entraînées**, l'image ne certifie pas les couples index→identité du checkpoint.
- Site `https://cl-detection2023.grand-challenge.org/` et dépôt `https://github.com/5k5000/CLdetection2023` : inscription/accord nécessaires pour le dataset, README modèle confirme 38 canaux, dataset représenté par `landmark_1...38` ; il faut obtenir l'annotation native officielle/validation indépendante pour autoriser de nouveaux mappings cliniques.
- `docs/audits/CEPHALO_VNEXT_LOT03_LANDMARK_ATLAS.md` définit `Gn` anatomique candidat mais non automatiquement promu, `U6/L6` sans spécification de cuspides, `Occ_Ant/Post` **compatibilité** non universelle ; `docs/audits/CEPHALO_VNEXT_LOT06_MUST_HAVE_SOURCE_LOCK.md` bloque explicitement `Gn→Gn_anatomic` sans source.
- `backend/services/cephalo_steiner_protocol_evidence.py` et `cephalo_steiner_geometry.py` prouvent la présence d'opérateurs déterministes existants, pas leur résultat avec landmarks manquants.

**Vérités mathématiques utiles** : sur cliché **non calibré**, au plus **11 mesures angulaires / 15** pourraient être calculées **si** toutes les identités/source-locks et constructions occlusales sont vérifiées et obtenues automatiquement. Les **4 distances mm** restent non calculables sans provenance métrologique vraie, même avec tous les landmarks. Si seules les 2 identités `Gn_anatomic` et `D_Steiner_1959` devenaient démontrablement disponibles et la variante `Go` résolue, **quatre angles supplémentaires** seraient théoriquement débloqués (`SN–GoGn`, `L1–GoGn`, `SND`, `L1–D°`), soit **10/15 théoriques non calibrés**, pas un résultat observé ni une autorisation d'alias. Le plan occlusal–SN resterait NC faute de construction automatisée source-lockée. L'expression 10/15/11/15 est une **borne conditionnelle**, pas un score FUE.

**NEXT recommandé — sans overengineering / sans modifier le moteur** :
1. **P0, source de vérité sur le détecteur** : obtenir l'original `train-gt.json`/manuel des 38 catégories avec correspondance index↔anatomie et protocole, ou créer un jeu expert indépendant avec revue praticien, version/hash ; prioriser la définition des canaux 8 (`Gn`), 19 (`D_point`), 9 (`Go`) et, en parallèle, tracer précisément la provenance des huit points qui donnent les six angles courants. Ne pas renommer toutes les données historiques.
2. **P1, automatisation des angles** : **seulement après la preuve sémantique**, ajouter les promotions `Gn_anatomic` et `D_Steiner_1959` **versionnées et testées**, puis matérialiser `OCCLUSAL_PLANE_STEINER_1953_V1` avec points dentaire exacts, géométrie validée et fixtures golden. Interdire les raccourcis `U6/L6 ≡ cuspide mésiovestibulaire`.
3. **P2, mesures linéaires** : acquérir/localiser automatiquement les surfaces faciales coronaires `U1_facial_surface`, `L1_facial_surface` via anatomie/modèle/segmentation autorisée (les apex/incisal seuls ne prouvent pas ces surfaces), puis intégrer la calibration **réelle source/étalon**. Ne pas inventer de mm depuis un JPEG public non calibré.
4. **P3, FUE clinique contrôlée** : 2 clichés publics + fantôme physique calibré, save/reload et recalcul, preuves source-ref/version, tests négatifs de faux alias, puis comparaison du même cliché à un jeu expert et approbation praticien. La correction manuelle demeure **facultative et traçable**.

**Verdict** : **38/38 mapping informatique cohérent, 0/38 canal anatomiquement certifié par ce contrôle statique, 6/15 AVAILABLE sur chacun des deux cas publics, 9/15 NC corrects, zéro faux GO clinique.** Le « 0/38 certifié par ce contrôle » ne prétend **pas** que les 38 coordonnées sont fausses ni qu'aucun travail antérieur de définition clinique n'existe ; il marque seulement ce que le **test d'index local** ne valide pas. **Aucune nouvelle liaison anatomique activée**, pas de code produit, merge, déploiement Vercel, sortie cabinet ou patient réel.

**Preuve finale du POST** : ajout documentaire au seul fichier canonique `docs/audits/CEPH_V1_LOT1_SCIENCE_APPROVAL_FUE_PREFLIGHT.md`, Notion PRE57 / POST57 ; GitHub CI du HEAD POST à revérifier séparément de la preuve FUE-H `dee9ac93`.

**Dernière mise à jour canonique : 05/11/2026 — POST §54, matrice SRPose 38/38 et Steiner 15/15, automatisation priorisée sans faux alias.**


### 55. PRE — 2026-11-05 — décision propriétaire : poids ONNX38 = source opérationnelle du tracé

**Décision utilisateur, explicite** : « valide les points du poids c'est notre base de travail, on capitalise dessus c'est notre source de vérité ». Digital Crown adopte **les 38 coordonnées sorties du modèle ONNX exact pin** comme **source de vérité d'ingénierie pour les constructions géométriques et tests**, en conservant leurs IDs bruts `S,N,...Gn,D_point...`, coordonnées subpixel, image originale et model SHA. Arrêter de bloquer la progression de calcul technique en recherchant systématiquement une équivalence clinique upstream. La décision est une **autorité d'exécution technique de travail**, pas une certification clinique externe ni une autorisation de forcer des alias dans le ledger clinique officiel.

**Base source** : source model `srpose38-tta-1024.onnx` SHA256 `a5ecd466d6d2c4ef02e145a143076a05720c0be56a260224812c23e2ecf42ddb`, mapping local `SOTA_LANDMARKS_MAPPING` 38/38 ordonné, FUE-H déjà attesté sur 2 radios publiques ANUG et Challiyan au HEAD `dee9ac93ae45c1b4db47f53bb9cbe9532549b837`. Archive `13437698027` contenant `source-locked-38-points.json` depuis GET authentifié + 2 images numérotées réellement examinées. 38 points distincts dans les bounds des deux clichés, modèle pin, 0 fausse calibration. Recalcul indépendant en mémoire de six angles depuis ces 38 coordonnées, concordance au dixième avec les six `AVAILABLE` du GET ; quatre autres angles géométriques issus des coordonnées déjà présentes (`Gn`, `D_point`), **exploratoires / non cliniques**. Source des repères = poids, pas nouvelles annotations manuelles.

**GOAL** : valoriser immédiatement le modèle acquis en ajoutant à la **preuve FUE-H non clinique** les quatre angles supplémentaires calculés depuis les points bruts, réutiliser strictement les fonctions géométriques existantes, garder la sortie clinique inchangée `6/15 AVAILABLE` tant que les identities historiques restent sous gate ; garder 4 mm NC sans calibration et occlusal NC sans ancrage sûr ; figer hash source, version de formule, images d'origine, empêcher l'invention de points ou de mm. Tests CI avec valeurs et provenance ; aucune modification ONNX ou produit médical ; zéro mise en production/merge.

**FUE PRE** : [PR #1213](https://github.com/hraaaaf/Digital_crown/pull/1213) DRAFT, HEAD initial `f7f1f8bae6eca86bcb8191b75b30025fa9168381`, Notion PRE58 enregistré ; `AGENTS.md`, roadmap V1 et canonique §54 relus ; CI sur ce HEAD à relever après changement. FUE-H au HEAD `dee9ac93` précédemment 9/9 workflow SUCCESS ; preuves limitées à ce SHA.

**Dernière mise à jour canonique : 05/11/2026 — PRE §55, ONNX38 choisi source d'ingénierie technique, 4 angles exploratoires à certifier sans clinique.**


### 55. POST — 2026-11-05 — 38 landmarks des poids ONNX fixés comme vérité d'ingénierie, 4 angles supplémentaires calculés sans manuel

**Décision prise suite à objection explicite propriétaire** : **le poids `srpose38-tta-1024.onnx` SHA-256 `a5ecd466d6d2c4ef02e145a143076a05720c0be56a260224812c23e2ecf42ddb`, et ses 38 coordonnées en pixels d'origine après GET authentifié, sont la base de vérité opérationnelle du tracé technique Digital Crown.** On capitalise immédiatement sur les points réellement détectés, sans obliger de ressaisir ou replacer six landmarks pour calculer des droites et des angles. Cette décision remplace comme priorité la quête répétitive d'une table amont pour toutes les **opérations de géométrie de recherche** ; elle ne transforme pas les estimations ONNX en diagnostic approuvé ni en preuve de parité clinique.

**FUE-0 locale, sur source FUE-H réellement observée** : archive FUE-H #13437698027 du SHA `dee9ac93ae45c1b4db47f53bb9cbe9532549b837`, ZIP SHA-256 `57708828e040f6c448d79c9fc887d474a46b4e1f3afe79f093a595c2128f24bf`; `source-locked-38-points.json` complet : deux études ANUG/Challiyan, **76/76 coordonnées finies et dans les bounds image** (38 par radio), 38 IDs distincts par radio, image/poids hashes fixés, non calibrées. Deux planches complètes `fullfilm-anug-38points-numerotes.png` et `fullfilm-challiyan-38points-numerotes.png` inspectées visuellement ; l'alignement spatial global est exploitable pour les travaux exploratoires, **sans score d'erreur expert ni certificat clinique**. Recalcul mathématique indépendant six mesures `SNA/SNB/ANB/U1–NA°/L1–NB°/inter-incisif` à partir de ces coordonnées : **6/6 valeurs concordent au dixième** avec `steiner-15-coverage.json` sur chacun des deux clichés.

**Nouveau résultat concret, 4 angles supplémentaires depuis les points BRUTS du modèle** (lignes exactes calculées en test hors interprétation historique, sans ajouter de landmarks manuels, aucune distance mm inventée) :

| Angle modèle issu des poids | ANUG | Challiyan | Entrées brutes |
|---|---:|---:|---|
| `MODEL_SN_GOGN_DEG` | 32,70° | 32,87° | S,N,Go,Gn |
| `MODEL_L1_GOGN_DEG` | 75,77° | 73,20° | L1_apex,L1_incisal,Go,Gn |
| `MODEL_SND_DEG` | 75,86° | 71,97° | S,N,D_point |
| `MODEL_L1_VS_GOGN_NORMAL_DEG` | 14,23° | 16,80° | L1_apex,L1_incisal,Go,Gn |

**Contrat explicitement séparé** : ces quatre valeurs ont le statut `MODEL_NATIVE_EXPERIMENTAL_ONLY`. Elles sont entièrement calculées à partir des 38 points ONNX, mais **ne portent pas les labels cliniques source-certifiés** `Gn_anatomic` ou `D_Steiner_1959` ; le quatrième angle est la direction perpendiculaire à Go-Gn, qui ne dépend mathématiquement pas de la position du point D, bien que le contrat complet de preuve D-line en demande l'identité. **6 mesures historiquement AVAILABLE + 4 angles modèles exploratoires ≠ 10/15 Steiner cliniquement validés**. Le read-path médical reste exactement à 6/15 AVAILABLE sur ces clichés non calibrés, et ses neuf NC ne sont pas falsifiés.

**Changements GitHub prouvés** :
1. [commit test `d3ba3498a555e2977b51c69fc40ab168e1a9bb26`](https://github.com/hraaaaf/Digital_crown/commit/d3ba3498a555e2977b51c69fc40ab168e1a9bb26) : `scripts/ceph_r23h_fullfilm_review.py` réutilise **exclusivement les fonctions géométriques déjà existantes** `steiner_sn_mp_deg_v1`, `steiner_l1_gogn_deg_v1`, `steiner_snd_deg_v1` et `steiner_l1_dline_deg_v1`. Vérifie **l'ordre exact des 38 IDs contre `SOTA_LANDMARKS_MAPPING`**, réutilise les pixels exacts, rejette résultat non fini/hors domaine, crée `artifacts/ceph-r23h-first-use/model-native-4-steiner-angles.json`, lié HEAD, SHA modèle et SHA radio, `clinical_release=false`. Aucun moteur, base, modèle, interface, document clinique ou formule de production modifiés.
2. [commit harness `aec4bf60d2d0ee42f9a16d6a9e1e993ba180ca49`](https://github.com/hraaaaf/Digital_crown/commit/aec4bf60d2d0ee42f9a16d6a9e1e993ba180ca49) : `.github/workflows/ceph-r23h-fue-first-use.yml` vérifie réellement la production de l'artefact expérimental pour les deux clichés, 4 mesures finies chacun et `clinical_authority=false` ; aucune colonne/valeur n'est injectée dans `steiner-15-coverage.json`.

**Gates à la clôture de cette passe** : FUE-0 local sur les anciennes coordonnées ONNX **PASS** (6 angles déjà disponibles réconciliés, 4 angles modèles candidats calculés), **CI nouveau HEAD au premier relevé QUEUED**, [FUE-H #42083529511](https://github.com/hraaaaf/Digital_crown/actions/runs/42083529511), [FUE-P1 #42083529608](https://github.com/hraaaaf/Digital_crown/actions/runs/42083529608), [FUE-P2 #42083529669](https://github.com/hraaaaf/Digital_crown/actions/runs/42083529669), [Scope #42083529579](https://github.com/hraaaaf/Digital_crown/actions/runs/42083529579), [build #42083529777](https://github.com/hraaaaf/Digital_crown/actions/runs/42083529777). Les 9 PASS antérieurs à `dee9ac93` ne sont **pas** ceux des commits actuels. Le présent POST produit un HEAD documentaire distinct : revérifier les CI propres à ce dernier SHA.

**NEXT** : lire le nouveau JSON GitHub CI exact HEAD une fois `SUCCESS` pour confirmer les quatre angles modèle sur les 2 images ; afficher automatiquement les résultats **dans un espace de travail expérimental distinct**, puis décider la promotion au protocole Steiner historique seulement après un contrôle sur mêmes images par orthodontiste ; ouvrir travail de construction du plan occlusal et une calibration physique conforme pour 4 mm. L'objectif maintenant est **d'exploiter les points des poids**, pas de solliciter une pose manuelle par défaut. Aucune autorisation donnée pour fusion, Vercel, EXE, données cabinet, normes ou décisions cliniques.

**Dernière mise à jour canonique : 05/11/2026 — POST §55, ONNX38 vérité d'ingénierie, 4 angles automatiques supplémentaires calculés, CI HEAD final à contrôler.**


### 56. PRE — 2026-11-05 — reprise immédiate / réparer la CI FUE-H du modèle ONNX38

**Mission** : après l'ordre « Non vas y reprend », désactiver le rappel différé et poursuivre immédiatement la preuve exacte des quatre angles expérimentaux calculés depuis les poids ONNX38. Canonique §55 relu ; Notion PRE59 ajouté. PR #1213 toujours DRAFT, départ `0e54e82d83eec0fe48ab4a1eb5c95e8343813a23`.

**Preuve d'échec déterministe** : [FUE-H #42083922038](https://github.com/hraaaaf/Digital_crown/actions/runs/42083922038) FAILURE alors que huit autres jobs SUCCESS et M6-I SKIPPED hors périmètre. Log job `127443857623` : `R23H_RESULT ... passed=7, failed=[], studies=2` — upload, ONNX, GET authentifié, 38 landmarks et Steiner 15 lignes ont passé. L'étape suivante `Produce whole-film 38-landmark numbered review boards` a lancé `python scripts/ceph_r23h_fullfilm_review.py` et échoué à la ligne 142 sur `ModuleNotFoundError: No module named 'backend'`. Cause : exécution d'un fichier sous `scripts/` sans ajout de la racine dans le chemin d'import Python. L'archive [#13443847560](https://github.com/hraaaaf/Digital_crown/actions/runs/42083922038/artifacts/13443847560) a les 17 pièces en amont mais pas `model-native-4-steiner-angles.json`.

**Correction bornée prévue** : dans le workflow FUE-H remplacer l'appel direct du fichier Python par `python -m scripts.ceph_r23h_fullfilm_review` depuis la racine checkout, en conservant tous les arguments, les validations sécuritaires et la source ONNX38. Aucun changement de formules ni des identités, aucun nouveau landmark, calibration inventée, UI ou résultat clinique. FUE = PASS H sur SHA exact avec JSON 2 études × 4 angles, non-clinique ; P1/P2/build/scope sans régression ; PR/Notion/document mis à jour après.

**Dernière mise à jour canonique : 05/11/2026 — PRE §56, import de rapport FUE-H à corriger.**


### 56. POST — 2026-11-05 — chemin d'import FUE-H réparé, run exact HEAD lancé

**Cause racine établie dans log GitHub** : FUE-H [#42083922038](https://github.com/hraaaaf/Digital_crown/actions/runs/42083922038), SHA `0e54e82d83eec0fe48ab4a1eb5c95e8343813a23`, **FAILURE** dans l'étape whole-film source-lockée : `ModuleNotFoundError: No module named 'backend'` dans `scripts/ceph_r23h_fullfilm_review.py:142`, à la première importation des fonctions de géométrie, après 7/7 checks FUE réel et sauvegarde/lecture d'études réussis. Artefact H avait 17 fichiers mais pas le nouveau JSON à quatre angles.

**Correction effectivement commitée** : [`61afb5da2b857d34d49d50270545c4265a2c541c`](https://github.com/hraaaaf/Digital_crown/commit/61afb5da2b857d34d49d50270545c4265a2c541c) change **une seule ligne** de `.github/workflows/ceph-r23h-fue-first-use.yml` : `python scripts/ceph_r23h_fullfilm_review.py` → `python -m scripts.ceph_r23h_fullfilm_review`. Les args `--input/--sources/--output` et tous les tests restent inchangés, les imports backend seront résolus depuis la racine checkout ; aucun modification du moteur, formule, ONNX, UI, thème, données patient ou résultat médical.

**Contrôle post-écriture** : PR #1213 encore DRAFT/non mergée ; vérification par `fetch_file` de la ligne exacte `python -m scripts.ceph_r23h_fullfilm_review`. Nouveau run [FUE-H #42095864408](https://github.com/hraaaaf/Digital_crown/actions/runs/42095864408) **QUEUED** au dernier relevé, plus [FUE-P1 #42095864438](https://github.com/hraaaaf/Digital_crown/actions/runs/42095864438), [FUE-P2 #42095864402](https://github.com/hraaaaf/Digital_crown/actions/runs/42095864402), [isolated frontend TEST build #42095864607](https://github.com/hraaaaf/Digital_crown/actions/runs/42095864607), [CI Scope Gate #42095864642](https://github.com/hraaaaf/Digital_crown/actions/runs/42095864642), R14 #42095864365, Themes09/10/11 #42095864387/#42095864551/#42095864612 QUEUED, M6-I SKIPPED. **Aucun PASS affirmé pour ce nouveau SHA : la réussite exige H SUCCESS et présence JSON avec 2×4 angles.** Le présent POST documentaire ajoutera un commit et un HEAD distinct qui doit être vérifié indépendamment.

**Livraison bornée du passage** : import FUE identifié et corrigé, chaîne de traçage fondée exclusivement sur 38 coordonnées originales ONNX38 conservée, 4 angles exploratoires non cliniques inchangés, read-path Steiner officiel continue 6/15 sur les deux radios non calibrées ; pas de faux 10/15 cliniques, ni diagnostic ni étalon fictif. **NEXT** : lire le run et télécharger `model-native-4-steiner-angles.json` exact SHA, puis auditer l'exposition dans un espace de travail expérimental séparé, sans merge ni deployment.

**Dernière mise à jour canonique : 05/11/2026 — POST §56, correctif import CLI FUE-H poussé, CI exacte en attente.**


### 57. PRE — 2026-11-05 — gate bloquant captures humaines à approuver (propriétaire)

**Instruction explicite** : « Pas d’approbation sans captures à approuver ». CI verte = seulement succès de l'automatisation, **jamais approbation des rendus**. Statut imposé : `HUMAN_VISUAL_APPROVAL_REQUIRED / HOLD` jusqu'à réception et décision *explicite* du propriétaire sur les captures, et gates cliniques indépendants avant tout usage clinique. Aucune approbation déduite du silence ; PR #1213 DRAFT et non mergée ; zéro Vercel, EXE ou mutation cabinet.

**PRE vérifié** : HEAD Git `96d507cd381ac278a28b3d62e39a57bf6eb1a369`, 9/9 workflows requis SUCCESS (FUE-H #42096123950, P1 #42096123998, P2 #42096124046, build #42096123951, Scope #42096124085, R14 #42096123995, Theme09/10/11), M6-I SKIPPED hors scope. [Artefact H #13448099375](https://github.com/hraaaaf/Digital_crown/actions/runs/42096123950/artifacts/13448099375), digest `sha256:a4eb65874e0bf535c2d9de930ee04e85cc16d80fada3184ddb5b47d838b3789f`. Preuve source exact SHA ; le statut humain n'est **PAS APPROVED**.

**Contrat du paquet visuel à présenter** : captures *réelles* ANUG et Challiyan comprenant image native entière avec 38 repères ONNX, + interface applicative/overlay SVG tracé. Indiquer SHA du modèle/source, HEAD, échelle, statut recherche et limites (absence de calibration mm) ; les afficher à l'utilisateur avant décision. En cas de modification d'UI, demander des **BEFORE/AFTER à viewports identiques** 390×844, 768×1024 et 1280×900, comparaison côte-à-côte ; pas de validation sur captures absentes ou non appariées. FUE-H vérifie les artefacts techniques ; revue visuelle humaine distincte.

**Action après PRE** : inspecter ZIP FUE-H, auditer réellement les images et le JSON 2×4 angles, présenter les captures existantes avec invitation explicite « approuver/refuser » ; poster résultat POST §57 puis Notion POST60 ; ne pas écrire `APPROVED` sans réponse. Un seul canonique GitHub pour ce lot.

**Dernière mise à jour canonique : 05/11/2026 — PRE §57, images + approbation obligatoires.**


### 57. POST — 2026-11-05 — FUE-H SUCCESS, captures authentifiées présentées, approbation visuelle EN ATTENTE

**CI exacte avant PRE documentaire** : [FUE-H #42096123950](https://github.com/hraaaaf/Digital_crown/actions/runs/42096123950), HEAD de preuve `96d507cd381ac278a28b3d62e39a57bf6eb1a369`, **SUCCESS**. Les 9 workflows requis de ce SHA (H/P1/P2/frontend/Scope/R14/themes09–11) sont SUCCESS, M6-I SKIPPED. PR #1213 reste DRAFT, jamais fusionnée. L'ajout documentaire §57 PRE crée son propre SHA distinct ; ne jamais transférer le succès de CI d'un SHA à un autre.

**Preuves effectivement téléchargées et relues** : [artefact ZIP H #13448099375](https://github.com/hraaaaf/Digital_crown/actions/runs/42096123950/artifacts/13448099375) SHA-256 archive `a4eb65874e0bf535c2d9de930ee04e85cc16d80fada3184ddb5b47d838b3789f` (digest du provider indépendant confirmé sur octets téléchargés). 18 fichiers, dont 13 PNG réelles, `report.json` 7/7 PASS avec `errors=[]`, `fullfilm-review-index.json`, `source-locked-38-points.json`, `steiner-15-coverage.json`, et **`model-native-4-steiner-angles.json` présent** avec deux radios et quatre angles expérimentaux par radio. `clinical_release=false`, `historical_aliases_certified=false`, `available_official_steiner_rows_modified=false` ; 6/15 AVAILABLE et 9/15 NC dans read-path médical par cliché. Les 38 repères sont source-locked au modèle ONNX et à chaque image ; absence de calibration physique et de goldset anatomique.

**Captures réelles à soumettre au propriétaire pour examen et approbation séparée** :
- `05-real-react-steiner-anug.png` — UI réelle React 1600×1000, radio ANUG, panneau Steiner 6/15 et tracé des lignes ;
- `05-real-react-steiner-challiyan.png` — UI réelle React 1600×1000, autre radio, même parcours ;
- `fullfilm-anug-38points-numerotes.png` — image entière non recadrée originale 2272×1818 avec les 38 coordonnées numérotées/calque de revue ;
- `fullfilm-challiyan-38points-numerotes.png` — original 1000×1255, 38 points ;
- `06-real-react-steiner-svg-anug.png` et `06-real-react-steiner-svg-challiyan.png` — fragments réels de l'overlay SVG ; disponibles dans l'archive.

**Revue critique de l'agent (ne vaut PAS validation du propriétaire)** : les captures UI disent `Steiner complet (1953 + 1959)` mais affichent seulement `6/15 mesures calculées` ; le libellé doit clarifier qu'il s'agit d'un *profil 15 facteurs partiellement calculé*, pas d'une analyse complète achevée. Les six tuiles `Gn anatomique / U1 surface faciale / L1 surface faciale / D Steiner / Occlusal antérieur / Occlusal postérieur` indiquent encore `À placer`, contradictoires avec l'objectif **ONNX38 auto-first sans six placements obligatoires**. Les quatre angles modèles supplémentaires sont prouvés dans le JSON expérimental mais **ne sont pas dessinés dans cet écran** ; les captures ne prouvent donc pas leur intégration UI. L'écran 1600×1000 montre aussi bandeau supérieur/titre coupé partiellement et un toast qui masque une partie du panneau au bas de l'écran. Ces observations sont des **points à corriger avant approbation du rendu final**, pas des erreurs géométriques démontrées.

**Gate explicite ACTIVE** : `HUMAN_VISUAL_APPROVAL_REQUIRED / NOT_APPROVED`, captures à présenter dans le chat à l'utilisateur ; lui demander avis explicite sur (1) emplacement des 38 points et (2) lisibilité/layout/tracés de l'UI. Même si l'utilisateur approuve la capture actuelle, toute future modification du rendu exige BEFORE/AFTER à viewports identiques 390×844 / 768×1024 / 1280×900 + captures et confirmation distincte. Le grand lot clinique reste HOLD ; aucune autorisation de merge, deploy, EXE, patient réel ou décision médicale.

**NEXT** : recueillir approbation/refus explicite des captures ; si refus ou corrections demandées, effectuer une passe UI limitée et photographier before/after + tests responsive, puis nouvelle revue humaine. `FUE-H SUCCESS` ne signifie pas `VISUAL APPROVED`.

**Dernière mise à jour canonique : 05/11/2026 — POST §57, screenshots à approuver, statut NOT_APPROVED.**


### 58. PRE — 2026-11-05 — cadrage fonctionnel Céphalo end-to-end, deux analyses (aucun code)

**Ordre du praticien** : arrêter de traiter Céphalo comme 38 numéros sur une radio. Nouvelle cible : les 38 points issus du poids ONNX identifiés par leurs noms, calibrage dès qu'une réglette graduée fiable est présente, sélection précoce de l'analyse (puis filtrage contextualisé des landmarks/lignes/plans/angles/mm), analyse des moulages structurée par onboarding, diagnostic détaillé et synthétique, plan de traitement rédigé/validé par le praticien, `Créer bilan` puis `Aperçu` et archivage. **Deux analyses réellement complètes dans la première livraison**, à choisir explicitement. Les chiffres seuls dans le paquet de preuve H sont des IDs de board QA et non une UX acceptable.

**Règles incontournables — acquises, non « propositions »** : couleurs (UI **et** géométrie) dérivées des tokens du thème actif, jamais une palette module autonome hardcodée ; conserver tous les acquis de Digital Crown, pas de from scratch ; **définir et valider toutes les spécifications avant la réconciliation technique** ; capture-rendu BEFORE/AFTER et approbation humaine explicite obligatoires ; poids ONNX38 opérationnel source des coordonnées pour la géométrie, correction ponctuelle traçable facultative ; pas d'activation diagnostique/treatment en automatique sans contexte clinique et validation praticien. Les 4 mm non calibrés restent indisponibles, jamais estimés.

**PRE lecture réelle** : PR #1213 DRAFT, HEAD `39524b1b6a78600331229d559cdf126d9e04bc40`, canonique §57 PRE/POST relu et Notion PRE61 ajouté. Existant à inventorier sans modifier : `CephaloWorkspace.tsx` (4 étapes), `Step1CephaloBase.tsx` (ONNX, overlay, calibration), `CephaloLandmarkReticles.tsx` (noms compacts et collisions, à distinguer du board QA numéroté), `CephaloAnalysisWorkbenchPanel.tsx` (sélecteur de 6 familles), `Step2Occlusal.tsx` (DDM et rapports), `Step3Clinical.tsx` (CVM, denture, diagnostic/notes), `Step4Documents.tsx` (brouillon/preview/archive), `calibration_service.py` (candidat réglette en zone haute uniquement), `cephalo_auto_calibration_gate.py` (étalon physique profilé), `cephaloTheme.ts` (tokens partiels, fallback chromatique), `orthoExpertSystem.ts` et `bilan_ortho_engine.py` (aucune décision de traitement autonome).

**Goal** : produire dans cette passe un tableau « déjà existant / écart produit / décision proposée », un parcours cible utilisable et une liste minimale de choix cliniques à approuver ; PAS de reconciliation ni implémentation. **Success** : décisions séparées des hypothèses, protocole de calibration sans tricherie, deux profils candidats motivés, bornes de rapport/diagnostic/plan, thèmes et gate screenshots. GitHub et Notion POST à la fin.

**Dernière mise à jour canonique : 05/11/2026 — PRE §58, atelier de conception, zéro code.**


### 58. POST — 2026-11-05 — Architecture fonctionnelle cible Céphalo V1 : COM et Steiner (proposition, zéro code)

**Nature de la passe** : inventaire source réel + atelier de conception ; **aucune réconciliation ni développement produit**, aucune approbation, aucun changement moteur ni norme, aucun merge ou déploiement. Les propositions suivantes sont **non approuvées** tant que l'utilisateur n'a pas tranché les détails.

#### Décisions explicites du propriétaire — ACQUISES

1. Poids SRPose38 / 38 coordonnées comme **source de travail du tracé** ; les points affichés sur la radio doivent porter leur **nom anatomique** et non leur numéro d'ordre. La numérotation 01..38 des planches FUE-H constitue une **preuve QA**, pas l'UI cible.
2. L'analyse choisie doit filtrer automatiquement **les points, lignes, plans, angles et mesures propres à ce protocole** ; le besoin final dépasse la simple superposition de 38 points.
3. Détecter les graduations d'une réglette et calibrer lorsque sa **longueur physique est déterminable** ; sans preuve de mm réelle, garder les mesures linéaires indisponibles. Éviter l'étalonnage inventé et les conclusions cliniques non fondées.
4. Deux analyses **complètes** seulement en première livraison, puis flux intégral radio → points / calibration / analyse choisie → moulages (onboarding structuré à définir) → diagnostic détaillé puis résumé → plan de traitement → Créer bilan / Aperçu / archive.
5. **ZÉRO couleur de module codée en dur** : tout état UI + tracé hérite des tokens sémantiques du thème choisi, y compris contrastes/états. Pas de reconstruction from scratch. **Finir la définition des fonctionnalités avant toute réconciliation technique**.
6. Validation visuelle propriétaire **obligatoire sur captures authentiques BEFORE/AFTER** aux mêmes viewports ; FUE verte ne vaut jamais approbation.

#### Source code audit — EXISTANT, à réutiliser

| Source | Ce qui existe réellement | Gap de design/implémentation à traiter plus tard |
|---|---|---|
| `srpose38_contract.py`, `cephalo_service.py`, R23-H FUE | Poids ONNX38 pin, 38 points avec IDs, sauvegarde/lecture, captures de 2 cas publics | rendre les noms réellement visibles sur l'image produit plutôt que board QA numéroté ; conserver identité et édition ponctuelle traçable |
| `CephaloLandmarkReticles.tsx` | IDs anatomiques, noms compacts, collisions, focus/hover et déplacement | modes d'affichage noms/protocole et lisibilité, étiquetage non ambigu sans 38 noms superposés |
| `cephaloVisualSemantics.ts`, `CephaloTracingLayerBase.tsx`, Workbench | moteur de plans/axes et famille scientifique de couleurs, sélecteur visuel, tracés existants | choix **unique** d'analyse qui alimente le viewer, métriques, overlay, PDF ; couleurs des familles actuellement basées sur des **hex littéraux fixes** même si mêlés à `--text-main` ; refactor en tokens **du thème global**, sans palette autonome |
| `cephaloCalibration.ts`, `Step1CephaloBase.tsx`, `calibration_service.py`, `cephalo_auto_calibration_gate.py` | états `UNCALIBRATED/CANDIDATE_UNVERIFIED/AUTO_VERIFIED/CLINICIAN_CONFIRMED/MANUAL_TWO_POINT/LEGACY_VERIFIED`; candidat de graduations et workflow de calibration avec profil physique versionné | détecteur actuel recherche **une réglette verticale dans les 30% supérieurs** et n'infère pas les mm à partir de graduations seules ; élargir une fois spécifié les cas d'image/règle ; capturer l'espacement connu, profil/fiabilité, zoom, mm/px et validation |
| `cephaloV1ProtocolScope.ts`, `Step3Clinical.tsx`, `CephaloAnalysisWorkbenchPanel.tsx` | Deux modes V1 cliniques **COM Digital Crown + Steiner 1953/1959** ; sélecteur placé dans Step3 alors que viewer autorise d'autres analyses | unifier source de sélection **dès Step1** et ne livrer que 2 profils décidés ; résorber « Steiner complet » trompeur quand 6/15 affichés |
| `Step2Occlusal.tsx` | DDM max/mand, formes d'arcade, classes molaires/canines R/G, subdivisions | mode onboarding guidé progressif, surplomb/recouvrement/ligne médiane/crossbites selon choix ; **audit obligatoire** des constantes `107` et `90` actuellement dans `calcDDMReelle`, non admissibles comme normes implicites |
| `Step3Clinical.tsx`, `orthoExpertSystem.ts`, `bilan_ortho_engine.py` | observations, CVM/denture explicites, notes diagnostiques/plan éditables ; déduction automatique de plan et de classe désactivée | séparer données mesurées / observations du praticien / diagnostic structuré signé / résumé lisible, sans diagnostic IA non corroboré, aucune décision thérapeutique autonome |
| `Step4Documents.tsx`, `CephaloWorkspace.tsx` | quatre étapes, sauvegarde, brouillon PDF, aperçu `LivePreview`, prévalidation / archivage | flux clair `Créer bilan → Aperçu → Valider/archiver`, même protocole/mesures/calibration au viewer, au diagnostic et au PDF ; vérifier que la preview n'est pas une validation clinique |

**Fait scientifique utile** : 38 points ONNX et **six** Steiner actuellement `AVAILABLE` (sur 2 JPEG publics non calibrés), **quatre angles supplémentaires expérimentaux** calculés dans JSON `model-native-4-steiner-angles.json`. La première version sera dite **complète** seulement si **toutes les mesures obligatoires de chacun des deux profils** ont une sortie justifiée sur un cliché approprié et un dispositif d'échec explicite sinon. Pas de 15/15 imaginaire sans surfaces coronaires, calibration mm et constructions spécifiques. La calibration de règle doit distinguer **repérage des traits** de **connaissance de la distance physique** et tenir compte de l'échelle du plan radiographique.

#### Proposition de parcours — à approuver

1. **Céphalométrie > importer** : image originale, lecture ONNX38 + identité source et sauvegarde ; UI **vrais noms**, mode **Analyse** défaut limité aux points pertinents, mode **Tous les repères** facultatif.
2. **Céphalométrie > calibrer** : détection réglette/traits; si profil de graduations millimétriques versionné/étalonné, proposition `AUTO_VERIFIED` avec segment superposé + contrôle praticien ; sinon demander longueur réelle (deux marques + mm connu) ou garder `NON CALIBRÉ` et poursuivre en version partielle **sans mesures mm**. La méthode, échelle, image et correction sont persistées.
3. **Céphalométrie > protocole / tracé** : sélectionner **un** des deux protocoles V1, faire apparaître points strictement utiles + plans/lignes/angles/mesures ; modes `Points / Constructions / Angles / Mesures / Tout`, sélection mesure ↔ surbrillance des mêmes traits sur radio ; avertir des valeurs `NC`. Changer d'analyse change la vue, **pas** les 38 coordonnées source, ni l'identité historique de l'étude.
4. **Moulages/occlusion** : mini-onboarding conditionnel dans Step2 existant : denture, arcades et DDM (sources et unités), classes molaires/canines droite/gauche, lignes médianes, surplomb/recouvrement, occlusion transverse/croisée et autres champs uniquement s'ils sont cliniquement utiles ; autosave/reprise et `non évalué` explicite. Aucune mesure inventée.
5. **Synthèse clinique** : cartes `Mesures objectives` + `Examen des moulages` + `Observations praticien`, puis **diagnostic détaillé multi-axes** (squelettique, vertical, dentaire, occlusal, tissus mous selon données), **résumé du diagnostic** éditable/validé ; séparé de l'inférence automatique.
6. **Stratégie / Documents** : problème/objectif thérapeutique/options/choix/plan saisis et **validés par praticien** ; bouton `Créer bilan`, `Aperçu` du PDF puis validation/archivage, y compris image des constructions exactes du protocole et provenance des points/calibration. Le brouillon partiel est identifiable ; une analyse **complète** n'est déclarée qu'avec tous les critères déterminés et satisfaits.

**UI recommandée sans repartir de zéro** : garder le stepper actuel en 4 blocs `Céphalométrie` (3 sous-passes), `Moulages`, `Diagnostic`, `Plan & Bilan`. Sur desktop, radio principale à gauche et panneau protocole/constructions/mesures à droite ; radio et résultats en deux onglets sur mobile, contrôles persistants. Couleurs = tokens d'application pour toutes les familles (y compris états et courbes); aucun nouvel hex local. Sélecteur de protocole unique, avant calcul, non un doublon dans Step3.

#### Deux analyses — recommandation, PAS décision utilisateur

Le code `cephaloV1ProtocolScope.ts` borne **déjà** la V1 à `COM Digital Crown` et `Steiner complet (1953 + 1959)`. **Recommandation** : garder précisément **COM + Steiner** pour ne pas disperser le chantier ; ne pas démarrer Tweed/McNamara/Ricketts dans ce premier lot complet. `COM` = convention locale alignée CRANIOM dans `CEPHALO_ANALYSIS_DEPENDENCY_MATRIX.md`, avec nuances historiques/normatives à préserver ; ne pas confondre la composition COM avec Tweed ou McNamara. Le propriétaire doit confirmer le duo et la **liste finale des mesures obligatoires par protocole**, calibrations et données requises avant implémentation.

#### Questions ouvertes, dans cet ordre (max 1 question au propriétaire par passe)

1. **Duo initial** : confirmation de **COM Digital Crown + Steiner 1953/1959** plutôt qu'un autre duo.
2. **Calibration** : formats d'images visés (JPEG/PNG avec règle, DICOM si réellement requis), type réel de réglette physique/espacement et situations sans règle.
3. **Protocole complet** : liste figée des mesures obligatoires pour chaque analyse, définition des points additionnels stricts, gestion `NC` et preuves de précision.
4. **Moulages** : champs obligatoires vs conditionnels, précision requise par denture ; design de l'onboarding par une capture cible soumise à approbation.
5. **Diagnostic et bilan** : sections, niveau d'assistance rédactionnelle sans LLM runtime, signature finale, PDF et source d'archive ; au moins une capture desktop/mobile BEFORE/AFTER à chaque sous-lot.
6. **Enfin seulement** : réconciliation technique et lotissement d'exécution, série FUE bout en bout ; zéro GO avant captures et accord explicite.

**Gate à la clôture de cette discussion** : `SPEC_DISCOVERY / NOT_APPROVED / NO_CODE`, décision clinique inchangée, aucun merge/déploiement ni patients. Les PRE/POST §58 documentent le cadrage (la présente mise à jour documentaire change HEAD et doit avoir sa propre CI).

**Dernière mise à jour canonique : 05/11/2026 — POST §58, atelier produit complet, choix duo ouvert, NO CODE.**


### 59. PRE — 2026-11-05 — atelier Étape 1 : céphalométrie utilisateur (SPEC, zéro produit)

**Owner instruction** : reprendre depuis §58 et Notion POST 61 ; construire un véritable parcours clinique plutôt qu'une simple superposition ONNX38. Les quatre décisions acquises (§58) sont conservées, images BEFORE refusées, duo COM Digital Crown + Steiner 1953/1959 toujours **recommandé/non approuvé**.

**Baseline contrôlée** : PR #1213 DRAFT, HEAD de lecture `67b29d984579ae201378c7f025e7c4065206c3f6` ; neuf workflows pertinents SUCCESS sur ce HEAD (FUE-H, P1, P2, frontend TEST, Scope, R14, Theme09–11), M6-I SKIPPED. Ce succès est non clinique et sans approbation visuelle. `CEPHALO_DIAGNOSTIC_SPEC.md` et contrat `SRPOSE38_LANDMARK_CONTRACT.md` relus ; détail §58 présent ; Notion PRE 62 écrit.

**Goal / Success** : figer en proposition testable le comportement Céphalométrie (import, 38 repères anatomiques, états de provenance/correction, calibration et limites, choix protocole, constructions/mesures, vue et export) et ses critères d'acceptation, sans décider un seuil, une norme ou un traitement. **Gate** : SPEC_DISCOVERY / NO_CODE / NOT_APPROVED ; ne toucher ni au runtime, ni à la CI, ni aux patients, ni à master, ni aux déploiements. **NEXT** : consigner §59 POST et Notion POST 62 ; demander l'arbitrage sur COM + Steiner et les limites de calibration avant de spécifier les étapes 2/3/4.


### 59. POST — 2026-11-05 — spécification fonctionnelle candidate Step1 « Céphalométrie »

**Statut : SPEC_DISCOVERY / DRAFT / OWNER_APPROVAL_PENDING — AUCUN CODE PRODUIT.** Préserve §58 et toutes les décisions déjà acquises. Le produit, le bilan et les captures réelles restent NOT_APPROVED. Le duo COM Digital Crown + Steiner 1953/1959 est recommandé, **non accepté par supposition** ; analyses supplémentaires existantes non supprimées, mais hors cible de complétude V1.

#### 59-A. Contrat d'usage et séquence, sans nouveau wizard indépendant

Conserver les 4 étapes de `CephaloWorkspace.tsx`. Définir dans **Étape 1 / Céphalométrie** quatre sous-tâches cohérentes (un même dossier persisté) :

1. **Importer / vérifier le cliché** : original intact, association au dossier déjà ouvert, modalité profil, orientation, dimensions, date/provenance disponibles, upload local autorisé ; erreur/radio non conforme = statut explicite, pas de tracé affirmé. Réouverture de la même étude identique.
2. **Détecter / contrôler les repères** : 38 sorties SRPose38 associées au contrat exact indices 0..37 ↔ IDs anatomiques ; affichage sur radio de `S, N, Or, Po, A, B, Go, Gn, ...`, pas de numéros de canaux. Statuts par point `AI_CANDIDATE / CLINICIAN_CONFIRMED / MANUAL_CORRECTION / NOT_EVALUABLE` comme spécification d'interface candidate, à réconcilier ultérieurement avec les vrais états persistés. Mode défaut = repères nécessaires à l'analyse choisie ; `Tous les 38` pour inspection volontaire. Désambiguïsation collisions par décalage de labels / connecteurs et focus/hover/clavier ; rendu fidèle au repère natif malgré zoom/crop. Correction facultative tracée (ancien/nouveau, auteur, date) et recalcul de toutes les mesures dépendantes sans modifier les indépendantes.
3. **Étalonner / qualifier** : détecter réglette ou graduations candidates et montrer la zone/segment sélectionnés sur image entière ; ne jamais inférer mm à partir du nombre de traits seuls. Présenter trois distinctions visibles : `RÉGLETTE DÉTECTÉE` (image seulement), `ÉCHELLE DÉTERMINÉE` (longueur réelle étayée par profil étalon/calibrage manuel), `CALIBRATION VÉRIFIÉE` (méthode, échelle effective, géométrie/magnification appropriée et confirmation selon preuve). Si non étalonné ou grossissement incertain, **mm indisponibles**, angles 2D indépendants du mm restant techniquement candidats sous réserve de points, orientation et conventions. Alternative deux marques + distance physique documentée ; conserver le parcours non calibré partiel. DICOM Pixel Spacing ne vaut pas automatiquement correction du grossissement.
4. **Choisir analyse / tracer / contrôler** : sélecteur unique en Step1 ; COM ou Steiner cible V1 sous réserve d'approbation. L'analyse active pilote le graphe de dépendances `landmarks → constructions → lignes/plans → angles/distances → résultats` ; panneaux `Points / Constructions / Mesures` et `Vue combinée` facultative. Sélectionner une mesure met en évidence sur la radio **exactement** ses repères, segments, arcs et l'unité ; revenir au protocole conserve les 38 coordonnées brutes et leurs corrections. Mesure manquante/degénérée/convention non prouvée = `NON CALCULABLE` avec cause précise (pas zéro) ; norme manquante = valeur géométrique conservée mais interprétation non proposée. Le système ne transforme jamais un résultat en diagnostic ou traitement sans praticien.

#### 59-B. Critères de complétude explicites par protocole

Une analyse n'est dite **définie complètement** que lorsque chaque ligne du protocole versionné a ID, définition, source de formule, points/constructions, convention et signe, unité, règle calibration, contraintes qualité, gestion des absences, méthode de calcul, tracé réel et présence/parité UI/API/PDF. Chaque **cas patient** a indépendamment couverture `N disponibles / N attendues` et statut de validation clinique. Ne jamais présenter `Steiner complet` comme 15/15 calculées : sur les 2 JPEG publics, read-path médical encore 6/15 AVAILABLE ; 4 angles en `MODEL_NATIVE_EXPERIMENTAL_ONLY` sans promotion automatique. Ancrages Steiner additionnels (p. ex. surfaces incisives, points D / Gn construits, extrémités du plan occlusal) nécessitent une définition source précise ; pas d'alias automatique fondé sur proximité des noms.

#### 59-C. UI, thème, accessibilité, états

Desktop : cliché prioritaire + panneau protocole/mesures ; mobile : vue radio et onglet résultats sans perdre l'orientation et sans overlays encombrants. Pas de 38 étiquettes affichées en permanence sur le mode principal. Séparer visuellement point IA candidat, point modifié, construction, mesure impossible et confirmation praticien sans dépendre uniquement de la couleur. `cephaloVisualSemantics.ts` / `cephaloTheme.ts` devront **plus tard** hériter exclusivement de tokens sémantiques du thème global pour traits, points, arcs, focus, seuils, alertes et surface — aucun HEX local. Les valeurs brutes, calibrages, positions et états doivent rester identiques après changement de thème ou analyse. Aucun changement de code durant cette passe.

#### 59-D. Critères observables et batterie FUE future (NON EXÉCUTÉE)

- FUE-01 : image correcte → 38 IDs contractuels uniques persistés → les étiquettes anatomiques du mode `Tous` sont lisibles au zoom, jamais des numéros de canaux ; contrôle sur 2 images publiques non patient.
- FUE-02 : COM↔Steiner change les seules couches actives ; coordonnées, corrections et historique inchangés ; sélection d'une mesure surligne uniquement ses dépendances réellement calculées.
- FUE-03 : JPEG sans règle / traits sans étalon → aucune valeur mm ; angles géométriques séparés, NC motivé ; règle avec profil physique connu et grossissement adéquat → échelle et preuves visibles, revue humaine.
- FUE-04 : inversion miroir/crop/ratio d'aspect/repère sensible manquant/dégénérescence → pas de mesure fausse et aucun `0` de repli ; correction contrôlée entraîne recalcul transitif.
- FUE-05 : chaque rang COM/Steiner apparaît au viewer, avec calcul ou cause d'indisponibilité + source/convention ; PDF même ID/unité/état/rendu que l'écran, y compris brouillon partiel.
- FUE-06 : thèmes globalement actifs, 390×844 / 430 / 768×1024 / 1280×900, zoom texte 200 %, souris/tactile/clavier : labels/tracés accessibles, capture BEFORE/AFTER par viewport et accord propriétaire explicite.
- FUE-07 : pas de patient réel en artifact/log/GitHub/Notion ; aucune interprétation clinique ni plan retenu sans praticien, aucun appel LLM runtime ; cohérence backend/frontend/stockage démontrée dans le lot autorisé ultérieur.

**Gate actuel** : tests FUE ci-dessus **NOT RUN**, aucun FUE d'une nouvelle interface n'existe ; l'ancien run du HEAD précédent ne certifie pas cette spécification. Aucune implémentation ni réconciliation technique autorisée avant arbitrages fonctionnels sur les 4 étapes.

**Décisions encore ouvertes, ordre** : 1) confirmer/rejeter officiellement COM + Steiner comme duo V1 ; 2) cadrer formats/réglette/étalon ; 3) figer toutes les lignes COM et Steiner et leur provenance ; 4) spécifier Moulages ; 5) Diagnostic ; 6) Plan/Bilan et signature ; **ensuite seulement** réconciliation technique et lotissement. Notion POST 62 à synchroniser. **Dernière mise à jour canonique : 05/11/2026 — POST §59, Step1 SPEC CANDIDATE, NO CODE.**


### 60. PRE — 2026-11-05 — validation propriétaire du duo V1 et calibration (SPEC ONLY)

**Décision utilisateur acquise** : « Je valide COM Digital Crown + Steiner 1953/1959 comme les deux analyses V1. Continuons les spécifications fonctionnelles sans implémentation. » Désormais **PROJECT_LOCKED pour le choix de duo V1**, en conservant les autres filtres/analyses historiques comme existants hors objectif de complétude initiale. Cette validation **ne couvre pas** la liste fine des mesures, les normes, les constructions manquantes, le rendu, la calibration clinique, les captures ou un déploiement.

**État technique contrôlé avant écriture** : PR #1213 OPEN/DRAFT, HEAD `9c7e0d7fc67973e0a1023b75d37dba76d260392f`; neuf workflows pertinents COMPLETED/SUCCESS sur ce HEAD (FUE-H, FUE-P1, FUE-P2, frontend TEST build, Scope, R14, Theme09/10/11), M6-I SKIPPED. Canonique §59 POST relu, Notion PRE63 enregistré. SUCCESS technique ne signifie ni approbation visuelle ni validité clinique.

**GOAL/SUCCESS/PROOF** : spécifier les scénarios de calibration, états de preuve, actions et refus ciblés, avec une question minimale de cadrage (formats de radios + réglette réellement disponible) ; vérifier compatibilité avec le parcours COM+Steiner sans coder, retester ou réconcilier. **SOURCE SCIENTIFIQUE candidate** : DICOM PS3.3 courant §10.7 (https://dicom.nema.org/medical/DICOM/current/output/chtml/part03/sect_10.7.html), notamment Pixel Spacing, Imager Pixel Spacing, GEOMETRY et FIDUCIAL, et limites de profondeur/grossissement. **GATE** : SPEC_DISCOVERY / NO_CODE / NOT_APPROVED, aucun patient, merge ou Vercel.


### 60. POST — 2026-11-05 — duo COM + Steiner verrouillé ; calibration Step1 spécifiée en candidate

**DECISION PROJECT_LOCKED — uniquement choix du duo** : COM Digital Crown + Steiner (1953/1959) sont les deux analyses cibles V1. Cette décision provient de la confirmation explicite du propriétaire du 05/11/2026. Conserver les autres familles existantes sans les traiter comme parcours complets V1. Ne pas modifier le produit ni inférer une validation du protocole historique intégral, des normes, des landmarks ONNX ou des captures.

**Calibration — DESIGN PROPOSAL / NOT YET APPROVED (et pas une règle clinique activée)**

**S-01 — Origine** : préserver l'original, son format, sa géométrie raster, orientation, dimensions, empreinte d'intégrité et toute métadonnée exploitable. Les formats cibles JPEG/PNG et DICOM restent à arbitrer selon la vraie pratique et la capacité vérifiée ultérieurement ; DICOM est une source possible de données, pas une garantie de calibration.

**S-02 — Détection candidate** : examiner le cliché entier afin de localiser une ou plusieurs réglettes/gradations candidates indépendamment de l'ancienne ROI verticale 30% supérieure ; afficher cadre/segment détecté à l'échelle native, zoom et origine sans recadrer le cliché. Les candidats multiples, incomplets, obliques, rééchantillonnés, distordus ou contradictoires gardent le statut non vérifié. La présence de traits n'identifie ni distance réelle ni position dans la géométrie d'acquisition.

**S-03 — Trois niveaux explicitement distincts** :
- `RULER_DETECTED` / « Réglette détectée » : graduations candidates localisées ; unité/longueur réelles inconnues ; aucune distance mm autorisée sur cette seule preuve.
- `SCALE_DETERMINED` / « Échelle déterminée » : longueur physique connue, profil d'étalon traçable ou deux marques avec distance mm documentée (ou métadonnées DICOM qualifiées), calcul de conversion selon géométrie image ; l'échelle dans le plan de la réglette peut être numérique sans garantir des distances anatomiques exactes.
- `CALIBRATION_VERIFIED` / « Calibration vérifiée » : fiabilité des métadonnées, orientation/ratio, unité, mode GEOMETRY/FIDUCIAL ou fiducial physique, position relative de l'étalon au plan anatomique, éventuel grossissement, méthode/limites et approbation qualifiée contrôlées pour les distances concernées ; ces conditions ne sont **pas** déduites uniquement de la détection automatique. Les états internes existants `UNCALIBRATED/CANDIDATE_UNVERIFIED/AUTO_VERIFIED/CLINICIAN_CONFIRMED/MANUAL_TWO_POINT/LEGACY_VERIFIED` sont **à réconcilier plus tard** sans changer le runtime actuellement.
- `UNCALIBRATED`, `AMBIGUOUS` et `INVALIDATED` sont des issues explicites, pas des preuves supplémentaires.

**S-04 — Méthodes fonctionnelles candidates** :
1) profil d'étalon physique identifié et versionné + graduations mesurables + géométrie pertinente → proposition de conversion ; 2) opérateur sélectionne exactement deux graduations et renseigne leur distance physique connue ainsi que provenance et plan de référence → échelle candidate manuelle ; 3) DICOM natif avec `Pixel Spacing (0028,0030)`, `Imager Pixel Spacing (0018,1164)`, `Pixel Spacing Calibration Type (0028,0A02)`, `Pixel Spacing Calibration Description (0028,0A04)` si présents → qualification distincte de la correction de grossissement et du repère FIDUCIAL/GEOMETRY ; 4) aucune preuve fiable → poursuite du parcours sans distances en mm. **Aucun facteur de grossissement ni pas de graduation choisi arbitrairement.** Même la méthode manuelle n'atteste pas automatiquement la profondeur anatomique.

**S-05 — Affichage minimal** : bandeau `Échelle non vérifiée / Réglage proposé / Calibration vérifiée`, segment(s) visibles sur radio, origine (`étalon / saisie manuelle / DICOM`), valeur et unité mm/pixel uniquement lorsque déterminées, orientation et avertissement sur grossissement, identité/date de la vérification. Boutons `Confirmer selon preuve`, `Corriger`, `Continuer sans mesures mm`. Un simple clic de confirmation ne doit pas transformer une preuve géométriquement insuffisante en « vérifiée » ; exiger la justification et l'action du praticien lorsque pertinente.

**S-06 — Mesures / effets aval** : sans calibration anatomiquement applicable, les distances mm sont `NON_CALCULABLE: CALIBRATION_UNVERIFIED` et l'export indique la même limite. Les angles 2D peuvent rester techniquement calculables si repères, conventions et géométrie/ratio d'aspect sont fiables ; image anisotropiquement étirée ou miroir non résolu bloque également les angles affectés. Une modification/invalidité d'échelle déclenche recalcul transitif/versionné des distances, normes et sections dépendantes du diagnostic et du PDF ; conserver l'historique. Aucune mesure remplacée par zéro, aucun choix thérapeutique automatisé.

**S-07 — Règles de progression** : le praticien peut poursuivre vers Moulages avec une étude partielle et non calibrée, mais le dashboard et le projet de bilan indiquent les mesures absentes ; l'application ne qualifie ni COM ni Steiner comme « cas complet » lorsque des critères requis manquent. La validation de l'étude et du plan thérapeutique reste une action clinique humaine séparée.

**Référence scientifique candidate contrôlée** : DICOM PS3.3 2026c, §10.7 « Basic Pixel Spacing Calibration Macro » https://dicom.nema.org/medical/DICOM/current/output/chtml/part03/sect_10.7.html ; valeurs Pixel Spacing ordonnées rangée/colonne, correction GEOMETRY vs FIDUCIAL, même profondeur/central ray, et absence d'indication fiable si métadonnées de calibration manquantes. `TECH_PRIMARY` pour la lecture de DICOM, **non** preuve de validité clinique d'un fichier importé et non norme orthodontique universelle.

**Future battery FUE-CAL (NOT RUN)** :
- CAL-01 JPEG/PNG sans règle ni métadonnées : 0 mm, angles contrôlés séparément, poursuite en « incomplet ».
- CAL-02 faux traits / règle tronquée / 2 candidats contradictoires : candidat seulement, refus `VERIFIED`.
- CAL-03 graduation sans longueur réelle connue : `RULER_DETECTED`, pas d'échelle arbitraire.
- CAL-04 deux marques + valeur mm attestée : `SCALE_DETERMINED` ; pas de `CALIBRATION_VERIFIED` sans preuve géométrique pertinente.
- CAL-05 DICOM Imager Pixel Spacing seul / correction non décrite : pas de preuve anatomique par magie.
- CAL-06 calibrage anisotrope, zoom, crop, miroir, double-resize : vérifier les transformations indépendamment (angle et distance ne doivent pas avoir de faux PASS).
- CAL-07 correction manuelle de l'échelle après mesure : recalcul dépendant, revue UI/API/DB/PDF, conservation de l'historique.
- CAL-08 états d'échec/accessibilité/thèmes : statut textuel visible, couleurs issues uniquement de tokens du thème global, FUE réelle à valider plus tard par captures BEFORE/AFTER et approbation humaine.

**OPEN / une seule question au propriétaire ensuite** : sur les téléradiographies réellement importées, y a-t-il habituellement une réglette graduée physiquement référencée dans le cliché, ou surtout des JPEG/PNG sans réglette ? La réponse définit le flux par défaut ; demander ensuite le format des sources et des profils d'acquisition/DICOM si nécessaire, avant la matrice complète COM/Steiner.

**GATE / résultat** : décision duo validée ; calibration **candidate**, non approuvée ; études/mesures V1 et captures **non cliniquement validées** ; aucun code, test clinique, patient, merge ou déploiement. Batterie FUE-CAL non exécutée. **NEXT** : confirmer le cas de réglette dominant, préciser ses données réelles, puis couvrir les mesures exactes COM/Steiner avant Moulages, Diagnostic et Bilan. **Dernière mise à jour canonique : 05/11/2026 — POST §60, SPEC_ONLY.**


### 61. PRE — 2026-11-05 — parcours COM+Steiner : matrice fonctionnelle des mesures (SPEC ONLY)

**Demande propriétaire** : « Alors » après validation de COM Digital Crown + Steiner 1953/1959 et cadrage calibration ; poursuivre utilement sans réitérer une question déjà posée ou passer au code. **Hypothèse de conception uniquement** : l'étape d'import doit gérer la présence ET l'absence d'une réglette, sans présumer de ce que le cabinet reçoit le plus souvent.

**Vérifications** : PR #1213 OPEN/DRAFT, HEAD documentaire pré-passe `81595ddc49d97d84ce118e706eabbca2c09a8a24`. §60 POST relu. Documents additionnels lus : `docs/CEPHALO_ANALYSIS_DEPENDENCY_MATRIX.md` (12 lignes COM historiques), `docs/CEPHALO_CONSTRUCTION_REGISTRY.md` (A'B', Francfort et ambigüités Gi/Gs, orientation du regard) et §54 du présent canonique (15 facteurs Steiner, 6/15 AVAILABLE, 9/15 NC sur deux JPEG publics; pas de validation anatomique clinique 38/38). Notion PRE 64 enregistré.

**GOAL/SUCCESS** : construire un inventaire fonctionnel **non-clinique et non final** des deux catalogues, distinguer construction source-verrouillée, entrée ONNX candidate, mesures mm, états et justification d'absence, puis préparer l'arbitrage portant sur la portée exacte de COM ; aucun ajout de norme ou formule. **GATE** : SPEC_DISCOVERY / NO_CODE / NOT_APPROVED, aucun changement produit, aucun merge ou déploiement.


### 61. POST — 2026-11-05 — inventaire COM + Steiner, exigences de complétude (CANDIDATE / SPEC ONLY)

**Statut** : le duo COM Digital Crown + Steiner 1953/1959 reste **PROJECT_LOCKED** par décision explicite. La calibration du §60 demeure **candidate**, non approuvée ; elle doit fonctionner avec **et sans réglette** par choix de robustesse de la future interface, sans présumer le type de cliché dominant et sans accorder de calibration mm implicite. Aucun nouveau code produit, aucune validation normative, visuelle, thérapeutique ou clinique.

#### 61-A — Trois niveaux de vérité à préserver

1. **Catalogue inventorié** : références et IDs présents dans les documents existants ; n'est pas une preuve que la composition de l'analyse historique est exhaustive.
2. **Protocole entièrement spécifié** : liste finale de facteurs démontrée par sources primaires/versionnées avec formule, landmarks/points construits, constructions exactes, unité, conditions d'applicabilité/étalonnage, norme éventuellement pertinente et déclinaison UI/PDF. La source COM (CRANIOM) impose de rechercher l'intégralité originale ; les **12 lignes recensées** aujourd'hui ne permettent pas de déclarer un protocole historique « complet ».
3. **Étude individuelle calculée/validée** : les résultats d'une image restent indépendamment `AVAILABLE`, `NOT_COMPUTABLE`, `CANDIDATE`, `HUMAN_GATE_REQUIRED`, etc. Un protocole historiquement documenté peut produire un cas partiel. `NOT_COMPUTABLE` n'est ni zéro ni absence clinique.

#### 61-B — COM Digital Crown / famille CRANIOM — 12 entrées du référentiel historique (composition finale À APPROUVER)

| Catégorie | Facteurs documentés | Unité | Condition/limite distincte |
|---|---|---|---|
| Dento-alvéolaire | Surplomb ; Recouvrement | mm | Projection d'incisives/plan orienté, échelle réelle vérifiée ; documentation candidate |
| Dento-alvéolaire | Inclinaison incisive mandibulaire / plan mandibulaire ; Inclinaison incisive maxillaire / Francfort ; Angle inter-incisif | degrés | Axe incisif disponible mais choix du plan mandibulaire Downs/variante nécessite source/identité ; Francfort Po-Or source défini |
| Squelettique AP | A'B' sur Francfort ; A / verticale de Nasion ; B / verticale de Nasion ; profondeur faciale S / verticale de Nasion | mm | Projections versionnées Po–Or, S/N/A/B ; calibration pour valeurs mm et contrôle des conventions/signes/source |
| Squelettique vertical | Forme faciale CRANIOM SN / mandibulaire Downs ; Forme mandibulaire CRANIOM Ar–Gi–Gs–Me | degrés | Downs ne s'assimile pas à GoGn ; Gi et Gs absents des 38 canaux, aucune promotion de Go |
| Suivi / posture | A''B'' selon le regard horizontal | mm | Orientation naturelle de tête / protocole photographique requis ; non calculable sinon |

**Réserve scientifique** : il s'agit d'un inventaire extrait de `docs/CEPHALO_ANALYSIS_DEPENDENCY_MATRIX.md`, daté historiquement et non d'un inventaire validé ligne par ligne de la méthode originale. Le projet identifie historiquement COM à CRANIOM (Bonnefont et collaborateurs, publications 2010/2011), source cohorte de 83 jeunes adultes Classe I non traités. Aucune valeur normative ne doit être généralisée à toutes populations/âges ; registres de source/population et vérification clinicien avant activation. Le champ COM ne doit pas fusionner silencieusement Tweed, Steiner ou McNamara.

#### 61-C — Steiner 1953/1959 — 15 facteurs dans le profil source (11 base + 4 extension)

| Groupe fonctionnel | Facteurs du profil documentaire | Statut sur les deux JPEG publics non calibrés (HEAD historique §54) |
|---|---|---|
| Sagittal osseux | SNA, SNB, ANB | 3 AVAILABLE, expertise anatomique non prouvée |
| Incisives et axe | U1–NA° ; L1–NB° ; angle inter-incisif | 3 AVAILABLE, même réserve |
| Incisives / rapports linéaires | U1–NA mm ; L1–NB mm | 2 NC : surfaces coronaires faciales exactes absentes + échelle mm |
| Relations au plan SN/mandibulaire | Occlusal–SN ; SN–GoGn ; L1–GoGn | 3 NC : plan occlusal exact non identifié et/ou Gn_anatomic + variante Go |
| Extension / symphyse | SND ; Pog–NB mm ; L1–D mm ; L1–D° | 4 NC : D_Steiner_1959, Gn_anatomic, surfaces coronaires, calibration selon mesure |

Total **15/15 lignes recensées**, dont **6/15 AVAILABLE** et **9/15 NOT_COMPUTABLE** sur les deux radios témoins au snapshot §54 ; ceci **n'est pas** une validation clinique ou anatomique. Quatre angles ONNX calculés expérimentalement plus tard dans FUE-H ne sont **pas** promus automatiquement parmi les 15 mesures médicales.

**Six identités/constructions spécifiques à traiter sans alias arbitraire** : `Gn_anatomic` ≠ automatiquement `Gn`; `D_Steiner_1959` ≠ `D_point`; `U1_facial_surface` et `L1_facial_surface` ≠ point incisif seul ; `Occ_Steiner_Ant` / `Occ_Steiner_Post` ≠ centroïdes génériques `U6/L6`. `Pog_hard` est un alias conditionnel versionné supplémentaire, pas une libre synonymie. Source de ce tableau : §54 POST du présent canonique, pas une nouvelle observation de patient.

#### 61-D — Contrat écran du catalogue, à approuver

- **Sélecteur V1 unique** : COM / Steiner dans Step1 ; aucune duplication de choix dans Step3 ; historique du choix conservé par étude.
- **Toutes les lignes attendues** de l'analyse choisie figurent dans le panneau `Mesures`, regroupées par sagittal / vertical / dentaire / tissus mous si effectivement prévus par le protocole. Pour chaque mesure : nom/ID/version, valeur, unité, calculable/non-calculable et **raison**, source normative éventuelle distincte, état de confirmation, clic = repères et construction exacts sur la radio.
- **Mesures angulaires** sans mm possibles sous contrôle géométrie/landmarks ; **distances mm** refusées jusqu'à preuve d'étalonnage appliquée à la structure mesurée. Une règle trouvée ne satisfait pas cette preuve.
- **Correction ciblée** : seulement les points/étalons qui bloquent une mesure ; clic du statut ouvre correction avec provenance, ancien/nouveau, auteur, validation ; recalcul des descendants transitifs et propagation jusqu'à PDF, sans changer les indépendants.
- **Un cas partiel peut continuer** vers Moulages et produire un **brouillon** avec lacunes explicites ; « analyse complète » n'est pas un badge fondé sur la présence des titres, et « étude validée » exige toujours praticien + preuves adéquates.
- **Thème** : couleurs de points/plans/valeurs/alertes hériteront des tokens sémantiques globaux ; aucun hex local à réintroduire plus tard.

#### 61-E — Arbitrages restants et contrôles futurs

**Question clinique prioritaire pour la suite** : le premier périmètre COM est-il le **protocole original CRANIOM** avec inventaire exhaustif à confirmer à partir de ses publications, ou **COM Digital Crown personnalisé** composé des mesures historiques documentées ? Les deux ne peuvent être annoncés équivalents sans preuve ; proposer par défaut de garder COM comme profil nommé du produit, tout en documentant sa filiation CRANIOM et en interdisant l'étiquette « CRANIOM complet » tant que la composition n'est pas contrôlée.

**FUE future (NON RUN)** : parcourir chacun des 12 items recensés COM et 15 Steiner dans le panneau ; sélectionner mesure → mettre en évidence dépendances exactes ; supprimer volontairement point Go/Gn/D/surface/incisal/étalon → déclencher NC motivé et ne pas altérer mesures indépendantes ; corriger point/échelle → recalcul + persistance PDF/DB ; changer COM↔Steiner → rendu filtré/coordonnées conservées ; vérifier intégrité de source et absence de patient réel dans les artefacts ; contrôles 390/430/768/1280 et zoom 200 % ; obtenir capture BEFORE/AFTER et accord praticien. Oracles géométriques indépendants et concordance scientifique source/version nécessaires avant GO.

**Résultat/limite** : inventaire **documenté, non cliniquement approuvé** ; 12 COM = état documentaire à réconcilier avec la source originale, 15 Steiner = profil projet source attesté, 6/15 disponible seulement au snapshot référencé. FUE actuel NOT RUN ; no code, no merge, no deploy. **NEXT** : arbitrer le périmètre COM, puis compléter la preuve du catalogue, définir les interactions Moulages et Diagnostic/Plan/Bilan, finir toutes les specs avant réconciliation technique.

**Dernière mise à jour canonique : 05/11/2026 — POST §61, matrice COM+Steiner candidate.**


### 62. PRE — 2026-11-05 — reprise onboarding Moulages/occlusion (SPEC ONLY)

**Instruction propriétaire :** « On reprend notre onboarding !? » après validation COM + Steiner, cadrage calibrage et inventaire §61 ; reprendre les **questions fonctionnelles cliniques dans les quatre étapes actuelles** sans implémentation. Le différend de périmètre COM strict CRANIOM vs profil Digital Crown est laissé OPEN et n'empêche pas de cadrer l'onboarding transversal.

**Baseline / preuve** : PR #1213 OPEN/DRAFT, HEAD `e4c15e0248c13e4b13476ea499c9bb14c15dfe78` ; le présent canonique §61 relu ; Notion PRE65 enregistré. Existant documenté §58 : `Step2Occlusal.tsx` contient DDM max/mand, forme d'arcade, classe molaire/canine D/G et subdivision. Constantes `107`/`90` liées à DDM à auditer, jamais traitées comme références approuvées à ce stade.

**GOAL** : définir Step2 comme onboarding conditionnel, avec denture, provenance des examens/modèles, saisie sans données imposées, DDM avec valeurs/méthodes sourcées, rapports D/G, surplomb/recouvrement, transverse, milieux et observations ; parcours partiel sauvegardable. **Success** : chaque question a une condition d'apparition, unité et statut non évalué explicites, aucune inférence ni traitement automatique. **Gate** : SPEC_DISCOVERY / NOT_APPROVED / NO_CODE ; pas de code, CI, patients, merge ou Vercel déclenchés intentionnellement par un lot produit.


### 62. POST — 2026-11-05 — onboarding Moulages et occlusion : parcours fonctionnel candidat

**Statut** : `SPEC_DISCOVERY / DRAFT / HUMAN_GATE_REQUIRED / NO_CODE`. Quatre étapes globales inchangées : Céphalométrie → Moulages & occlusion → Diagnostic → Plan & Bilan. Cadrage de la **Step2 existante**, sans écran assistant indépendant, sans décision thérapeutique automatique ni activation clinique. Duo COM Digital Crown + Steiner 1953/1959 toujours `PROJECT_LOCKED`; composition exacte historique COM encore à arbitrer séparément.

#### 62-A. Séquence d'onboarding proposée (non approuvée)

| Sous-passe | Question / saisie | Condition d'affichage | Statut/provenance |
|---|---|---|---|
| 1. Denture | temporaire, mixte, permanente, non déterminée ; âge / stade uniquement s'il est déjà documenté dans dossier | toujours, avant calculs dépendants des dents présentes | saisi/confirmé par praticien ; aucune dentition déduite de l'âge seul |
| 2. Disponibilité | examen clinique, moulages physiques, scan numérique exploitable, photographies d'appoint, aucun modèle ; date/source | toujours ; plusieurs sources possibles | une photo seule ne vaut pas un moulage mesurable ; les données non observables restent NON_EVALUE |
| 3. Arcades / espace | maxillaire et mandibulaire séparés ; forme d'arcade ; encombrement/diastèmes observés ; DDM (espace disponible, espace nécessaire, méthode, unité mm et résultat signé si définissable) | si mesure documentée de chaque arcade ; en denture mixte, demander méthode d'estimation des dents non éruptées et source applicable avant DDM | pas de conversion automatique depuis `107`/`90` legacy sans norme source/version/population ; une DDM non mesurée ne devient pas 0 |
| 4. Relations sagittales | molaire droite/gauche + canine droite/gauche : I/II/III/non évaluable, subdivisions si observées, absences/éruption/anomalie si affectent l'évaluation | seulement si denture, dents index et occlusion permettent une classification pertinente ; si dent absent ou relation non observable, marquer NON_EVALUABLE au côté concerné | provenance examen clinique ou modèle ; ne pas forcer symétrie D=G |
| 5. Vertical/transverse | overjet et overbite en mm si mesurés ; béance et supraclusion observées ; lignes médianes (déviation D/G + mesure) ; occlusion croisée antérieure/postérieure, côté, ciseaux, déviation fonctionnelle, courbe de Spee, asymétrie selon données | bloc de base visible, sous-questions uniquement si anomalie/mesure pertinente ; champs numériques facultatifs quand aucune valeur étayée | séparer observation qualitative et mesure documentée ; pas de diagnostic automatique à partir d'un seul critère |
| 6. Vérification | synthèse D/G, arcades, valeurs, unités, sources, champs non évalués et éventuelles contradictions | fin d'étape | sauvegarde brouillon et reprise ; confirmation clinique praticien traçable distincte de validation finale du diagnostic |

**Règles conditionnelles P0** :
- Sans moulages, saisir uniquement ce que l'examen clinique permet réellement ; masquer les mesures de modèle requérant un étalon ou déclarer NON_EVALUABLE. Ne pas empêcher de poursuivre le dossier.
- En denture mixte, demander quelles dents sont présentes et la méthode applicable avant toute prédiction ou DDM ; aucune taille coronaire calculée d'après un seuil implicite.
- Classes molaire/canine droite/gauche totalement indépendantes ; si dent index absente/non éruptée, ne pas forcer classe ou subdivision. 
- Mesures d'overjet/overbite/lignes médianes : distinguer unité numérique et observation qualitative ; ne jamais mettre `0` par défaut.
- Gestion des éléments non évalués/non observés : `NON_EVALUE`, `NON_APPLICABLE`, `A_CONFIRM`, `CONFIRME_PAR_PRATICIEN` sont des états de concept, à réconcilier avec les vrais contrats de persistance uniquement **après** fin des specs.
- Le compte rendu doit conserver provenance, côté, denture, méthode, date, auteur, correction et statut ; aucune conclusion classe squelettique/indication thérapeutique issue automatiquement de la classe molaire.

#### 62-B. UX compacte proposée

Step2 = un **panneau unique progressif**, question courante bien identifiée et retour arrière sans perte de réponse ; résumé d'arcades et côtés constamment accessible ; champs cachés conditionnellement sans effacer leur valeur historique si non pertinente (marquer état / version) ; bouton `Continuer vers diagnostic` même lorsque des données sont manquantes, avec résumé explicite des omissions. Règles UX/couleurs héritées des tokens globaux, jamais HEX locaux, accessibilité clavier/zoom et touch. Ne pas imposer une page par question si cela augmente le nombre de clics ; la progressivité est principalement la révélation conditionnelle dans Step2 existante.

#### 62-C. Batterie FUE prévue — NON EXECUTEE

- FUE-M01 denture permanente, deux modèles mesurés : deux arcades et quatre rapports D/G éditables et persistés.
- FUE-M02 denture mixte : méthode estimation requise pour DDM concernée ; sans preuve, état NON_EVALUE et aucune valeur numérique fictive.
- FUE-M03 molaire manquante d'un seul côté / canine non éruptée : aucune classe automatique côté absent, autre côté conservé.
- FUE-M04 sans moulages : parcours clinique partiel avec absence de mesure, pas de blocage ni d'invention, état retrouvé après réouverture.
- FUE-M05 DDM en mm avec données contradictoires ou unités manquantes : calcul suspendu, source et conflit visibles ; constantes historiques 107/90 jamais activées par défaut.
- FUE-M06 modification de mesure/latéralité : mise à jour seulement des dépendances, historique et bilan/aperçu identiques.
- FUE-M07 contradictions molaires/canines, déviation/occlusion croisée, saisis qualitatives : ne pas produire de diagnostic autonome.
- FUE-M08 navigation réversible, non-effacement des saisies, thème actif, 390/430/768/1280, 200% zoom texte, clavier/tactile, BEFORE/AFTER réelles sur UI autorisée, validation du praticien.

**Arbitrage unique proposé ensuite** : confirmer comme première question du parcours la **denture** plutôt que la disponibilité du modèle. L'ordre « denture d'abord » est recommandé car il conditionne la pertinence des relations dentaires, les méthodes DDM et les champs. Ce n'est pas encore une décision du propriétaire.

**Proof/limitations** : spécification candidate dans ce seul fichier, FUE-M01..08 NON RUN, aucun changement logiciel, aucun patient, merge, Vercel ou approbation des captures. **NEXT** : arbitrage de l'ordre d'entrée Step2, puis préciser les questions conditionnelles et poursuivre Step3/Step4 en atelier, avant réconciliation technique. **Dernière mise à jour canonique : 05/11/2026 — POST §62, onboarding Moulages SPEC ONLY.**


### 63. PRE — 2026-11-05 — exploration de la denture mixte : questions conditionnelles de Step2 (SPEC ONLY)

**Demande :** « Pour notre conception de l'onboarding Moulages, prenons l'exemple d'une denture mixte. Montre-moi les questions conditionnelles suivantes, sans coder. » Considérer l'exemple comme un **parcours hypothétique**, non patient et non validation de l'écran. Le propriétaire ne change pas la décision de V1 COM Digital Crown + Steiner 1953/1959.

**Baseline :** PR #1213 OPEN/DRAFT, HEAD avant PRE `9fedc1e3594593993bdac871a88f4d818a107761`, canonique §62 POST relu, Notion PRE66 écrit. Hériter de Step2 existante, pas de nouvel assistant ; protocoles/DDL mixtes et valeurs `107/90` ne sont pas des règles validées.

**GOAL/SUCCESS :** montrer questions concrètes et embranchements liés à l'existence de modèle mesurable, au statut des dents temporaires/permanentes, aux 1ères molaires permanentes et canines par côté, à l'espace/DDM sourcé, aux observations verticales/transverses, et à la revue. Toutes les branches écartées doivent être explicitement `NON_EVALUE` ou `NON_APPLICABLE`, pas `NORMAL`. Mettre en évidence le cas de modèle absent, les champs absents, le passage en brouillon partiel, et préparer une batterie FUE négative. **Gate** : SPEC_ONLY / HUMAN_APPROVAL_PENDING / NO_CODE / NO_MERGE / NO_DEPLOY.


### 63. POST — 2026-11-05 — simulation conditionnelle concrète : denture mixte, questions 2–7

**Portée** : démonstration de comportement produit sur une denture mixte hypothétique, **pas de données d'un vrai patient**, ni approbation médicale, ni code, ni nouvelle formule. Le praticien a choisi `DENTURE_MIXTE` en question 1 de Step2. Navigation dans le panneau existant; aucune nouvelle page indépendante. Tous les déclencheurs ci-dessous sont une **proposition à approuver**.

| Écran/Question | Texte visible au praticien | Réponses / sources | Question suivante conditionnelle |
|---|---|---|---|
| Q2 | « Sur quelles données repose l'examen de l'occlusion ? » | examen clinique + moulages physiques/scan exploitable ; clinique seule ; photos seulement ; aucune donnée. Sources multiples et date disponibles, ne pas confondre photo et modèle mesurable | si modèle mesurable : branche DDM chiffrée autorisée **si données/méthode réellement renseignées** ; sinon observations qualitatives/mesures documentées indépendamment, DDM `NON_EVALUE`, ne pas forcer upload |
| Q3 | « Quelles dents permanentes sont présentes et évaluables, par arcade/côté ? » | premières molaires permanentes D/G, incisives permanentes, canines permanentes, dents temporaires restantes, absence/extraction/non-éruption/doute ; statut de l'occlusion | si première molaire permanente du côté évaluée et en rapport exploitable : montrer Q5 classe molaire **pour ce côté seulement**. Sinon `NON_EVALUABLE`. Si canine permanente non éruptée, **ne pas imposer classe canine permanente** ; observation de rapports temporaires si pertinente et documentée |
| Q4 | « Souhaites-tu quantifier l'encombrement ou les espaces ? » | arcades maxillaire/mandibulaire séparées : dimensions mesurées, espace disponible et nécessaire, méthode de mesure, dents prises en compte, unité mm, provenance ; méthode d'estimation explicite et versionnée des dents non éruptées | avec modèle fiable et données complètes/méthode applicable : proposer DDM sourcée. Sans modèle, estimation ou source valide : seulement encombrement/diastèmes observés, DDM numérique `NON_EVALUE` ; éviter `0` et constantes legacy `107/90` |
| Q5 | « Quelle relation occlusale est observable à droite et à gauche ? » | molaires droite/gauche puis canines droite/gauche, classe I/II/III uniquement **quand classification pertinente**, côté, source et obstacle ; possibilité non évaluable/non applicable | affichage des relations uniquement si dents de référence/côté en occlusion et classification justifiée ; subdivisions ouvertes uniquement lorsque documentées. Aucune symétrie D/G automatique |
| Q6 | « Observe-t-on un surplomb/recouvrement, un articulé croisé, une asymétrie ou une déviation fonctionnelle ? » | observation qualitative d'abord, puis si mesure étayée surplomb/recouvrement en mm, béance/supraclusion, ligne médiane D/G + amplitude, croisé antérieur/postérieur et côté/dents, ciseaux, observations fonctionnelles et courbe de Spee si source/conditions permettent | si `croisé` : demander secteur et côté ; si `déviation des milieux` : demander max/mand, sens, mm **si mesuré** ; si `déviation fonctionnelle` : observation clinique/praticien requise, jamais déduite du moulage statique |
| Q7 | « Vérifier les données avant Diagnostic » | synthèse par arcade et par côté, valeurs/unités/sources/méthodes, `CONFIRME`, `A_CONFIRM`, `NON_EVALUE`, `NON_APPLICABLE`, contradictions à corriger | bouton `Continuer vers diagnostic` possible sur brouillon partiel avec lacunes explicites ; état de confirmation de Step2 n'est pas validation du diagnostic ni du plan |

**Exemple narratif S-A** : denture mixte ; examen clinique + modèles mesurables ; premières molaires permanentes D/G évaluables ; canines permanentes non éruptées ; espace mandibulaire mesurable mais méthode d'estimation des canines/prémolaires non éruptées absente ; articulé croisé postérieur observé à droite. Le panneau propose les rapports molaires D/G et les questions de secteur/dents pour le croisé D ; ne force pas les classes des canines permanentes ; conserve DDM mandibulaire `NON_EVALUE` tant que les dimensions/méthode ne permettent pas le calcul. Les valeurs/faits sont **exemple fictif**, pas des observations d'image.

**Exemple S-B** : denture mixte, examen clinique seulement, première molaire D non évaluable / G évaluable. On demande uniquement la relation molaire G si elle est documentée, affiche D `NON_EVALUABLE`, ne chiffre pas DDM par défaut, tout en pouvant saisir une observation clinique d'encombrement et poursuivre.

**Exemple S-C** : photos seules sans examen clinique actif ni modèle calibré. Les éléments réellement visibles peuvent être rapportés comme observations non confirmées avec provenance photo ; relations, déviations fonctionnelles et distances non vérifiables restent `NON_EVALUE`. Le parcours reste enregistrable.

**Gates produit / clinique** :
- Pas de déduction de denture à partir de l'âge, de relation canine permanente à partir de canines temporaires ni de relation molaire à partir d'une dent absente.
- `Classe I`, `aucune anomalie`, `DDM 0`, `surplomb 0`, `recouvrement 0` ne sont **jamais des valeurs par défaut**.
- Les méthodes de prédiction denture mixte (si utilisées plus tard) doivent être nommées, sourcées, adaptées aux dents disponibles et validées séparément ; leur présence dans une liste ne valide ni seuil ni population.
- Une saisie conditionnellement masquée à la suite d'un changement de denture/source reste historisée avec statut `STALE/REVIEW` selon le contrat ultérieur, sans contaminer diagnostic/PDF.
- Overlays, surlignages et états héritent du thème global; aucune couleur hex locale. Zéro LLM runtime, diagnostic/traitement sous contrôle praticien.
- Préserver une seule Step2 progressant en six sous-passes au maximum après Q1; pouvoir revenir sans perdre réponses et voir le résumé à tout moment.

**FUE-MIX future — NON RUN** :
1. Mx-01 S-A : modèles mesurables et 6 permanentes D/G présentes → questions molaires activées sans imposer canines permanentes.
2. Mx-02 méthode de DDM manquante → résultat numérique bloqué, observations qualitatives conservées, `NON_EVALUE` dans UI/PDF.
3. Mx-03 dent permanente absente d'un seul côté → classification bloquée côté absent seulement, pas de duplication.
4. Mx-04 sans moulages et photo seule → pas de mm inventés ni d'observation fonctionnelle affirmée, brouillon sauvegardable.
5. Mx-05 croisé postérieur D → secteur/côté révélés ; retrait de l'observation masque questions sans conserver de diagnostic actif obsolète.
6. Mx-06 modification Q2/Q3 après DDM ou classe saisie → invalidation des dépendances obsolètes et synthèse de revue, pas de suppression opaque.
7. Mx-07 synthèse Q7 : absence de classes, DDM, mesures et provenance se répercutent identiquement dans le brouillon clinique et futur bilan.
8. Mx-08 UX/tokens a11y 390/430/768/1280 px, zoom 200 %, clavier, toucher, états non dépendants de la couleur, capture BEFORE/AFTER et validation clinicien.

**Décision ouverte prioritaire** : approuver le séquencement `Denture → Sources → Dents évaluables → Arcades/DDM → Rapports bilatéraux → Vertical/transverse/fonctionnel → Vérification`. Ce n'est pas une approbation par défaut de l'exemple S-A. Le parcours documenté peut ensuite nourrir Step3 Diagnostic et Step4 Plan/Bilan **une fois la spécification entière approuvée**, avant toute réconciliation technique.

**GATE final** : `SPEC_DISCOVERY / CANDIDATE / HUMAN_APPROVAL_REQUIRED / NO_CODE` ; aucun FUE exécuté pour cette interface, aucun cas patient, aucun merge/déploiement. **Dernière mise à jour canonique : 05/11/2026 — POST §63, onboarding denture mixte, questions conditionnelles candidate.**


### 64. PRE — 2026-11-05 — correction fonctionnelle DDM réelle : clinique + céphalométrique

**Instruction propriétaire (autorité clinique de périmètre)** : « La DDM réelle = DDM clinique + DDM céphalo ! Regarde sur le web ! ». La précédente Step2 §62-63 ne décrivait correctement que la composante moulages ; ne plus représenter la DDM réelle comme un nombre exclusivement issu du modèle.

**Baseline vérifiée** : PR #1213 OPEN/DRAFT, HEAD de lecture `4ddd005c14275dc79308762c780ff8b3db41218f`, §63 POST relu. Notion PRE67 écrit. Duo V1 COM Digital Crown + Steiner 1953/1959 maintenu. Aucun code produit autorisé.

**Littérature consultée — sources et limites** :
1. *L'Orthodontie Française*, « La forme des dents. Un élément incontournable du diagnostic » (https://stm.cairn.info/revue-l-orthodontie-francaise-2020-1-page-7) : DDM ≠ encombrement uniquement, prendre en compte inclinaison/position incisive et courbe de Spee ; valeur signée + excès d'espace / – défaut d'espace.
2. Thèse clinique Oran 1, Nabi Fatima épouse Benali (2022), §4.2.1–4.2.3 (https://apidspace.univ-oran1.dz/server/api/core/bitstreams/0ac7613b-803d-4ba4-b969-58bd531036ea/content) : DDM apparente = encombrement + nivellement Spee ; DDM réelle = apparente + effet du repositionnement de l'incisive mandibulaire **décidé par praticien**, au regard des critères céphalométriques, fonctionnels et esthétiques. **Contrôle web screenshot PDF non disponible (cache miss)**, texte extrait uniquement ; corroboration indépendante par dépôt universitaire UMMTO (https://dspace.ummto.dz/server/api/core/bitstreams/60fa8cd2-55f0-470d-a1e3-a59e281e1f45/content).
3. Regragui et al., *International Orthodontics* 2010, https://doi.org/10.1016/j.ortho.2009.12.005 : méthode de discordance espace disponible - espace nécessaire sur moulages, échantillon **adulte** de Rabat ; ce papier ne prouve pas l'algorithme complet de DDM réelle ni estimation en denture mixte.
4. PMC8600854 : conversions « mouvement de l'incisive → gain de place » simples ne sont pas systématiquement validées, ne pas en dériver un multiplicateur clinique arbitraire.

**GOAL / SUCCESS** : spécifier par nom clinique de l'app `DDM_CLINIQUE + DDM_CEPHALO = DDM_REELLE` comme **somme algébrique de composantes exprimées dans le même espace, mêmes unités, même arcade, signe/version tracés**. Documenter sous-contenu Spee, estimations denture mixte, objectif incisif explicite non autonome, absence d'échelle/précision, et interdiction d'afficher un nombre faussement complet. Prouver uniquement cette correction de spec via §64 POST + Notion POST67 et batterie FUE prévue NOT RUN.

**GATE** : SOURCE_CONSISTENT / FORMULA_DETAILS_PENDING_REVIEW / SPEC_ONLY / NO_CODE / HUMAN_SIGNOFF_REQUIRED ; ni changement runtime ni patient, merge, Vercel.


### 64. POST — 2026-11-05 — correction de l'onboarding : DDM RÉELLE = DDM CLINIQUE + DDM CÉPHALO (SPEC)

**Décision clinique de périmètre utilisateur :** le parcours V1 Digital Crown doit modéliser explicitement `DDM réelle = DDM clinique + DDM céphalométrique`. Ce **principe de composition** est accepté comme instruction du propriétaire ; les méthodes de quantification et les conventions de signe **ne sont pas encore cliniquement approuvées**. La correction invalide la représentation implicite de §62/63 où la DDM de moulage semblait suffire pour conclure à la DDM réelle. Conserver §62/63 comme historique, le présent §64 prévaut.

#### 64-A. Modèle clinique de référence — notation métier à afficher

`DDM_REELLE_MM = DDM_CLINIQUE_MM + DDM_CEPHALOMETRIQUE_MM`

**Définir la terminologie avant l'addition** :
- **DDM clinique / apparente**, en pratique surtout mandibulaire pour la construction classique : discordance signée `espace disponible − espace nécessaire` (encombrement en négatif) **plus une correction d'espace chiffrée pour le nivellement de la courbe de Spee lorsque la méthode choisie l'inclut**, avec espace physique, méthode, unité, niveau de preuve et statut du praticien. Une DDM seulement `ED−EN` ne doit **pas** être présentée comme complète si la correction Spee exigée n'est pas déterminée ; séparer `DDM_ENCOMBREMENT`, `SPEE_SPACE_IMPACT`, et `DDM_CLINIQUE`.
- **DDM céphalométrique** : **impact spatial signé en millimètres** du repositionnement **proposé et approuvé** de l'incisive mandibulaire, interprétant la céphalométrie **avec examen clinique, fonctions, esthétique et contraintes biologiques**. `IMPA`, `L1-NB`, etc. ne sont pas **une** DDM céphalométrique en mm ; une différence d'angle ou déplacement linéaire de l'incisive ne se convertit pas directement en espace d'arcade au moyen d'une constante arbitraire. Une politique de conversion doit être documentée/scientifiquement prouvée et choisie pour l'étude.
- **DDM réelle** : somme algébrique des **deux effets sur l'espace d'arcade** signés, de même unité et convention, pour la **même arcade** et le même scénario d'objectif incisif. Ne pas confondre signe numérique de déplacement anatomique et signe d'impact en espace disponible. `0` est un résultat mesuré/étayé, jamais repli par défaut.
- **Cadre scientifique / réserve** : la littérature sur DDM apparente et réelle cadre principalement le **repositionnement incisif inférieur/mandibulaire**, non un automatisme généralisé à une DDM supérieure. Pour maxillaire, garder discordance d'arcade distincte et ne présenter `DDM_REELLE_MAXILLAIRE` qu'après protocole de calcul spécifiquement justifié et approuvé.
- **Denture mixte** : le calcul d'espace nécessaire peut dépendre d'une méthode d'estimation vérifiable pour canines et prémolaires non éruptées, avec statut de maturité, dents prises en compte, leeway-space/potentiel de croissance **séparés des données effectivement mesurées**. Une projection future est `ESTIMATE / FORECAST` et non une certitude de `DDM réelle` actuelle. La courbe de Spee et la pertinence d'un objectif d'inclinaison peuvent être encore indéterminées : `INSUFFICIENT_DATA` est une issue normale.

#### 64-B. Parcours d'onboarding corrigé (ne pas créer une cinquième étape)

| Zone existante | Saisie/lecture | Résultat affiché |
|---|---|---|
| **Step1 Céphalométrie** | Points/analyses COM ou Steiner, géométrie et calibration qualifiées ; statut des mesures incisives utilisables ; **jamais** objectif thérapeutique déduit de la norme | données céphalométriques objective, limites, proposition de déplacement/objectif incisif **à renseigner/valider par praticien ultérieurement** |
| **Step2 Moulages / occlusion** | Q2 sources, Q3 denture évaluée, Q4 espace disponible et nécessaire, correction Spee si documentée, DDM d'encombrement et **DDM clinique / apparente** ; autres rapports D/G, vertical/transverse | carte `DDM clinique` avec composantes, convention de signe, statut et lacunes, plus `DDM céphalo : en attente de définition/validation de l'objectif`; PAS de chiffre DDM réelle prématuré |
| **Step3 Diagnostic / synthèse** | Le praticien prend connaissance de l'axe incisif, de la position, du contexte fonctionnel/esthétique, **définit le repositionnement incisif cible** et approuve le calcul de l'effet en espace avec méthode/version traçable ; vérifie compatibilité même arcade/unité/signe | calcul `DDM clinique + DDM céphalo = DDM réelle` uniquement si les deux nombres et toutes leurs dépendances sont `VERIFIED`; sinon `DDM réelle : NON CALCULABLE / À COMPLÉTER` et cause |
| **Step4 Plan et bilan** | plan signé et validé par praticien, aperçu PDF | bloc de trois DDM/éléments + méthode, provenance, statut et hypothèses visibles ; ne pas proposer extractions/expansion/RAP comme décision automatique selon une somme |

**UX** : présenter trois lignes distinctes `DDM clinique` / `DDM céphalo` / `DDM réelle`, avec sous-lignes (encombrement ED−EN et Spee) et statut. La valeur finale doit toujours être **cachée/remplacée par non calculable** quand une composante chiffrée, méthode, ou signe manque ; ne pas montrer un 0, valeur de secours ou simple `DDM clinique` renommée `réelle`. Résultat cliquable pour ouvrir sa dépendance (modèles/Spee, cliché/objectif incisif, validation). Les couleurs viennent exclusivement des tokens du thème global.

#### 64-C. Conventions + lecture contrôlée, sans normes nouvelles

- **Convention signée candidate** `ED−EN` : manque de place `négatif`, excès `positif`, concordant avec Regragui et al. (2010) et L'Orthodontie Française. Les contributions Spee et incisive doivent être transformées en **impact sur ce même espace**, sans réutiliser naïvement signe de profondeur ou déplacement anatomique ; documenter formule/protocole en source primaire et preuve. **La convention d'écran exacte reste à approuver**.
- **Référence documentaire** : *L'Orthodontie Française*, « La forme des dents. Un élément incontournable du diagnostic », https://stm.cairn.info/revue-l-orthodontie-francaise-2020-1-page-7, confirme qu'il ne faut pas réduire DDM à l'encombrement ; la position incisive et Spee comptent.
- **Référence académique secondaire** : Thèse Oran 1 (Nabi Fatima épouse Benali, 2022), https://apidspace.univ-oran1.dz/server/api/core/bitstreams/0ac7613b-803d-4ba4-b969-58bd531036ea/content, §4.2 : `DDM apparente = encombrement + Spee`, `DDM réelle = apparente + repositionnement de l'incisive inférieure décidé par praticien`. **Texte web consulté, capture screenshot du PDF non accessible (cache miss), pas de vérification visuelle du PDF** ; corroboration par dépôt universitaire UMMTO, https://dspace.ummto.dz/server/api/core/bitstreams/60fa8cd2-55f0-470d-a1e3-a59e281e1f45/content.
- **Référence mesure moulages** : Regragui et al., *International Orthodontics* 8(1), 2010, DOI `10.1016/j.ortho.2009.12.005`, 30 moulages de patients **adultes** à Rabat, `ED−EN`. Ne pas étendre ses résultats à un modèle d'estimation denture mixte.
- **Risque de coefficient** : https://pmc.ncbi.nlm.nih.gov/articles/PMC8600854/ met en garde contre relations fixes simplificatrices entre encombrement, position et inclinaison incisive. Aucune nouvelle constante. Les `107`/`90` anciens sont en audit, interdiction de les considérer comme références normatives validées ou conversion mm.
- **Calcul/plan non autorisés** : deux mesures peuvent être anatomiquement correctes sans produire un objectif de position d'incisive. Le praticien décide du projet et l'atteste ; la DDM réelle n'impose **aucun** type de traitement, extraction, décapage, expansion ou plan.

#### 64-D. FUE DDM futurs — NOT RUN, préalables à toute qualification

1. `DDM-01` clinique signée seule (ED/EN et Spee source-présents), sans objectif incisif : clinique affichée, céphalo `EN ATTENTE`, réelle `NC`.
2. `DDM-02` céphalo angulaire disponible sans calibration mm ou conversion approuvée : aucun impact spatial mm, réelle `NC`.
3. `DDM-03` repositionnement incisif cible renseigné mais non validé par praticien : finale `NC`, pas de plan autonome.
4. `DDM-04` deux effets spatiaux numériquement déterminés, même unité/arcade/convention, sources et accord du praticien : somme **algébrique** conforme oracle externe, pas de conversion implicite ni de valeur issue de norme fixe.
5. `DDM-05` denture mixte avec méthode d'estimation non éruptées absente / courbe de Spee indisponible : DDM clinique partielle, vraie DDM réelle `NC`.
6. `DDM-06` correction ED/EN, Spee, point céphalo, calibration ou objectif incisif : invalidation transitivement correcte de toutes les valeurs en aval, sauvegarde et bilan cohérents, historique.
7. `DDM-07` maxillaire versus mandibulaire : aucune addition inter-arcade ni application automatique du repositionnement mandibulaire à la DDM maxillaire.
8. `DDM-08` fichier patient absent/simulation non clinique, pas de LLM runtime, UI/rapport/PDF trois composantes, thème tokens globaux, 390/430/768/1280 + 200% et captures BEFORE/AFTER avec approbation propriétaire.

**VERDICT** : Principe de l'addition **fonctionnellement accepté sur instruction du praticien et cohérent avec les publications**, **quantification et cible incisive NON APPROUVÉES**, aucune DDM réelle clinique calculée ni rapport activé. Prochain arbitrage nécessaire : la dénomination `DDM clinique` doit-elle **inclure** la correction Spee (recommandé pour correspondre à `DDM apparente`), ou l'afficher en sous-terme distinct à sommer avant DDM céphalo ? Les deux représentations sont équivalentes mathématiquement si la convention est strictement versionnée, mais peuvent produire un double comptage si fusionnées sans règle.

**GATE** : SPEC_DISCOVERY / REVIEW_REQUIRED / NO_CODE / NO_MERGE / NO_DEPLOY. **NEXT** : valider la définition exacte des 3 composants et la convention de signe, puis poursuivre les écrans Step2–Step3 en restant spec-only. **Dernière mise à jour canonique : 05/11/2026 — POST §64, DDM réelle corrigée.**


### 65. PRE — 2026-11-05 — recherche web : vraie méthode de calcul DDM céphalométrique Steiner vs Tweed

**Demande propriétaire** : « Attends attends tu sais comment on calcule la ddm cephalo !? Regarde sur le net ! ». Revoir §64 (DDM réelle = clinique + céphalo) en corrigeant la phrase ambiguë « pas de conversion à coefficient fixe » : une **règle historique chiffrée existe**, mais la justesse clinique/prédictive pour chaque patient ne doit pas être déclarée acquise. Restons en SPEC_ONLY.

**Baseline** : canonique §64 POST et Notion POST67 relus ; PR #1213 DRAFT/OPEN, HEAD documentaire précédent `50ab17d22a7bf346967fc1596ecb5e3f4f4d29a9`. Notion PRE68 écrit.

**SOURCES WEB confirmées (ne pas fusionner les écoles)** :
- **Steiner original** : Cecil C. Steiner, « The Use of Cephalometrics as an Aid to Planning and Assessing Orthodontic Treatment », *Am J Orthod*, 1960, 46(10):721–735 https://bbo.org.br/bbo/files/bibliografia/artigos/56_The_use_of_cep_halometrics.pdf . Texte p.729 confirme : reculer l'incisive mandibulaire de 7 mm réduit de 14 mm le périmètre total, 7 mm par hémiarcade, poste « Relocation 1 ». Attention : Steiner ajustait préalablement la position initiale de l'incisive pour corriger la malposition isolée / forme d'arcade.
- **Steiner enseigné** : https://www.gsortho.ma/blog/boite-de-steiner/ et https://www.gsortho.ma/outils/chevrons-de-steiner/ : `RI_MM = 2 × [i-NB_final_target_MM − i-NB_initial_adjusted_MM]`, projections de la « boîte » et chevrons ; cible construite puis individualisée avec ANB, incisions et menton, jamais valeur générique.
- **Tweed-Merrifield** : revue méthodologique https://doi.org/10.18231/j.ijodr.2022.038 et https://www.gsortho.ma/blog/espace-total-tweed-merrifield/ : convention `0.8 mm` d'espace d'arcade par degré de repositionnement FMIA/IMPA. **Ceci ne remplace pas Steiner** dans les analyses V1. Bornes normatives variant selon références, à choisir explicitement avant tout éventuel mode Tweed futur.
- **Prudence empirique** : https://pubmed.ncbi.nlm.nih.gov/16764682/ rapporte une précision de prévision Steiner insuffisante comme unique fondement du choix thérapeutique.
- **HAS/ANAES** 2002 https://www.has-sante.fr/upload/docs/application/pdf/orthodontie_rap.pdf p.29 : DDM modèle `ED−EN`, mesure/prédiction possible en denture mixte, estimations des prémolaires limitées ; ne soutient PAS en elle-même la formule Steiner/Tweed.

**LIMITATION DE PREUVE** : consultation HTML et texte extrait des PDF via recherche web ; appels `screenshot` PDF HAS et PDF Steiner 1960 ont retourné cache miss/erreur. Aucune capture PDF visuelle vérifiée ; ne pas présenter les PDFs comme relus image par image.

**GOAL/SUCCESS** : corriger la future UX, source-versionner la conversion historique propre à Steiner, afficher les signes, la correction de forme d'arcade et la méthode de détermination du but incisif, bloquer le calcul si `L1–NB_MM` ou calibration/cible manque, séparer Spee du RI dans la boîte. **GATE** : recherche/SPÉCIFICATION uniquement ; aucune formule exécutée en clinique, aucun code, merge, CI clinique ou Vercel.


### 65. POST — 2026-11-05 — DDM céphalo : Steiner ×2 et Tweed–Merrifield ×0,8, formules distinctes

**VERDICT après recherche** : correction chiffrée enseignée **confirmée par source primaire Steiner 1960**, corroborée par supports de formation : la règle historique n'est **pas** « indéfinie » : `RI_STEINER_MM = 2 × (L1_to_NB_TARGET_MM − L1_to_NB_INITIAL_ADJUSTED_MM)`, avec la convention d'espace signée `+ = gain potentiel`, `− = consommation d'espace`. Exemple fictif : initiale 7 mm, cible 4 mm, écart `−3 mm` → `RI = −6 mm` sur les deux hémiarcades. **Cette formule est une convention géométrique clinique de planification, pas une prédiction clinique assurée ni une règle pour une arcade maxillaire.**

#### Source primaire et subtilité indispensable

Steiner, 1960, *The Use of Cephalometrics as an Aid to Planning and Assessing Orthodontic Treatment* (article original, Am J Orthod 46:721–735), https://bbo.org.br/bbo/files/bibliografia/artigos/56_The_use_of_cep_halometrics.pdf : `−7 mm` de recul incisif de **11→4 mm après ajustement de forme d'arcade** donne `−14 mm` de périmètre d'arcade au poste « Relocation 1 » ; l'incisive initiale **avait été mesurée à 13 mm**, et l'auteur a retranché 2 mm pour l'envisager alignée dans une forme d'arcade acceptable. Donc :
- l'incisive initiale brute `i-NB_initial_measured` et sa valeur ajustée selon l'alignement/forme d'arcade `i-NB_initial_adjusted` sont deux informations **séparées** ; ne pas utiliser arbitrairement la première dans une équation conçue pour la seconde ;
- il faut un **objectif i-NB** individualisé d'après chevrons et examen praticien, avec la méthodologie source. Ne pas forcer `i-NB cible = 4 mm`.
- les chevrons Steiner utilisent notamment ANB, I–NA, i–NB, Pog–NB, hypothèses de croissance/position squelettique ; leur fonctionnement exact est un **sous-protocole de planification à spécifier et versionner** (l'actuel profil 15 mesures de géométrie ne suffit pas à lui seul pour déclarer la boîte « calculable »).
- l'étude https://pubmed.ncbi.nlm.nih.gov/16764682/ relève une fiabilité prédictive insuffisante de Steiner en tant que seule base de décision thérapeutique. Utiliser la projection en **simulation contrôlée** et non « optimum automatique ».

#### Tweed est une méthode différente, même si la formule conventionnelle est simple

Revue https://doi.org/10.18231/j.ijodr.2022.038 et https://www.gsortho.ma/blog/espace-total-tweed-merrifield/ : `|RI_TWEED_MM| = 0.8 (mm/degree) × |FMIA_TARGET_DEG − FMIA_MEASURED_DEG|` (ou IMPA avec les conventions de signe équivalentes si FMA inchangé). Exemple FMA 26°, FMIA 57°, FMIA cible 67° ⇒ angle à redresser de 10° ⇒ consommation `−8 mm`. **Coefficient conventionnel**, seuils FMIA/FMA variables selon écoles (67/68°, limites 22/28° vs 20/30°), **ne PAS réactiver automatiquement Tweed** dans la V1 COM + Steiner, ne pas fusionner les deux méthodes ni importer « valeurs normales » universelles. Les constantes `107/90` legacy ne sont pas certifiées par cette découverte et restent en audit.

#### UI / comportement V1 (SPEC CANDIDATE, NON APPROUVÉ)

- **Step1 Céphalométrie** : fournir `L1_to_NB_initial_mm` uniquement si définition exacte `L1_facial_surface` + source anatomique SRPose38 / correction humaine contrôlée + calibration géométrique mm vérifiée. Sur deux JPEG publics sans calibration, `M_L1_NB_MM_V1` reste NC au snapshot §54 ; la formule `×2` ne doit **pas** faire passer le moteur de 6/15 à 7/15.
- **Step2 Moulages** : `encombrement ED−EN` mesuré/estimé, forme d'arcade et ajustement initial Steiner s'il est nécessaire, Spee et provenance ; distinguer la **boîte de Steiner** où `encombrement`, `repositionnement incisif (RI)` et `courbe de Spee` sont trois lignes distinctes. La décision antérieure sur Spee « inclus dans clinique » n'était **pas approuvée** ; proposer des sous-postes conservés séparés et une vue de total sans double comptage.
- **Step3 Diagnostic / objectif praticien** : déterminer selon chevrons Steiner la cible `i–NB` et enregistrer le choix de compromis `initial mesuré→initial ajusté→cible projetée→cible retenue par clinicien`, unités et date ; après vérifications, afficher `RI = 2 × (cible − initial ajusté)`, détailler résultat signé avec variante source `STEINER_LOWER_ARCH_RELOCATION_1_1960`. La **DDM réelle** peut alors être synthétisée en additionnant la DDM clinique définie/étayée et cette correction sans Spee en double. Aucune décision d'extraction, d'ancrage ou d'appareil automatisée.
- **Step4 Bilan** : montrer valeur source, cible, correction du positionnement initial, conversion ×2, signe, hypothèses, Spee et enveloppe d'applicabilité ; si un lien manque afficher `NON CALCULABLE` + cause, jamais `0`, jamais masquer une extrapolation de denture mixte.
- **Protocoles** : DUO V1 COM Digital Crown + Steiner 1953/1959 **déjà verrouillé** ; l'article historique de planification Steiner 1960 est une **référence complémentaire proposée** pour sa boîte/chevrons, ne modifie pas sans accord la liste 15/15 du profil géométrique. L'option Tweed est **comparaison documentaire uniquement**, pas troisième analyse V1.
- **Métrologie / UI** : tous les mm exigent leur origine et étalon, tous les traits/couleurs via tokens du thème global, zéro runtime LLM.

#### Batterie FUE-ST (future / NOT RUN)

- ST-01 : initial `7 mm`, ajustement `0`, cible `4 mm` → `−6 mm` ; ratio et signe vérifiés sur oracle.
- ST-02 : cas source Steiner `13 mm mesuré`, `11 mm ajusté`, `4 mm cible` → `−14 mm` et non `−18 mm`; ne pas confondre les deux états de la dent.
- ST-03 : seule ANB/IMPA/FMIA connue sans `i-NB mm` valide → RI Steiner `NC` (angle seul ne suffit pas pour mode Steiner).
- ST-04 : cible générée par chevrons mais non validée par praticien → RI prévisionnel identifiable, jamais « final clinique » / pas de plan autonome.
- ST-05 : témoin Tweed 10°×0,8 = 8 mm de coût d'espace, **n'entre jamais dans la somme Steiner**, y compris si un autre sous-module historique garde Tweed.
- ST-06 : changer calibration, point incisif, correction de forme, cible ou denture → invalidation/recalcul dirigé, historique.
- ST-07 : Spee présent séparément dans boîte Steiner et éventuellement inclus par définition explicite dans DDM clinique : jamais deux fois dans total.
- ST-08 : denture mixte, germes non mesurés et prévisions de croissance → état `ESTIMÉ / NON ÉVALUÉ` ; pas de faux « définitif », contrôle clinique humain, UI/PDF même provenance.
- ST-09 : thème tokens globaux, aucun patient réel en test/artifacts, FUE futurs avant/après 390/430/768/1280 + zoom 200%, aucun run de ces scénarios encore réalisé.

**PREUVE ET GATES** : article Steiner original **texte extrait et audité via web**, appels screenshot PDF Steiner et HAS ont échoué `cache miss`; ne pas prétendre inspection graphique authentifiée des figures. Confirmations pédagogiques GS Ortho, revue Tweed 2022, étude de valeur prédictive indépendante. Nous pouvons donc **spécifier** ces formules historiques ; pas d'implémentation, de recalcul rétrospectif patient, de certification médicale, de merge ou de déploiement. **NEXT** : valider le mode de détermination cible via chevrons Steiner et la correction de forme d'arcade ; régler la présentation boîte de Steiner des lignes Spee ; poursuivre étape 2 puis 3/4. **Dernière mise à jour canonique : 05/11/2026 — POST §65, DDM céphalo précisée, SPEC ONLY.**


### 66. PRE — 2026-11-05 — McNamara : position incisive et contribution d'espace, ne pas confondre avec Steiner (SPEC ONLY)

**Instruction propriétaire :** « Mmm et mcnamara fait comment !? » (après §65 POST sur la correction `2× Δ(i–NB)` de Steiner). Rechercher ce que McNamara (1984) définit effectivement, ses constructions dento-squelettiques et si une **formule de DDM céphalométrique indépendante** existe réellement dans ce protocole.

**Baseline contrôlée :** PR #1213 OPEN/DRAFT, HEAD `22238f372d97471a02846091fb9d112e38148ba1`, §65 POST relu ; Notion PRE69 écrit. Deux analyses V1 COM Digital Crown + Steiner 1953/1959 verrouillées, McNamara pas sélectionnée en V1. Ne pas ajouter par réponse à une question une analyse/valeur clinique exécutée.

**Sources web** : McNamara JA Jr, « A method of cephalometric evaluation », *Am J Orthod* 1984;86(6):449–469, DOI `10.1016/S0002-9416(84)90352-X`, https://pubmed.ncbi.nlm.nih.gov/6594933/ ; texte intégral indexé via reproduction tierce https://pdfcoffee.com/a-method-of-cephalometric-evaluation-mcnamara-1984-pdf-free.html ; mesure définie dans analyse McNamara https://pmc.ncbi.nlm.nih.gov/articles/PMC8018756/ et revue https://pmc.ncbi.nlm.nih.gov/articles/PMC8770963/ ; dépendance de l'espace à la forme d'arcade selon Mutinelli et al., *Eur J Orthod* 2000 https://pubmed.ncbi.nlm.nih.gov/10822884/. Reproduction tierce ≠ validation graphique de l'original.

**Goal / success** : décrire une mesure clinique `L1 facial surface→A–Pog` (historique 1–3 mm antérieurs dans contexte facial équilibré), le recalage de la ligne après repositionnement mandibulaire projeté, et la différence entre changement de repère squelettique et déplacement réel de l'incisive. Donner un verdict de spécification sans inventer `McNamara = 2 × ΔA–Pog`. **Gate : SPEC ONLY, NO_CODE, NO_APPROVAL, FUE_NOT_RUN**, pas de merge/déploiement.


### 66. POST — 2026-11-05 — McNamara (1984) : A–Pog avec référence squelettique projetée, pas de « DDM ×2 » propre à McNamara prouvée

**Statut : synthèse scientifique documentaire, non spécification approuvée d'une troisième analyse V1.**

**1. Position incisive de McNamara :**
- Référence inférieure : `A–Pog`, droite du point A au Pogonion osseux (ne pas utiliser Pog_soft). Mesure signée **perpendiculaire** entre la surface vestibulaire/coronaire de l'incisive mandibulaire et la ligne, en mm, positive en avant. McNamara 1984 rapporte environ **+1 à +3 mm** pour une face équilibrée, contexte normatif historique, pas cible universelle. Notamment le texte original reproduit mentionne +1,5 mm dans un standard Bolton et +2,3 à +2,7 mm dans échantillon Ann Arbor. Les distributions varient et la norme seule ne prescrit pas une cible pour un patient.
- Référence supérieure : bord facial de l'incisive maxillaire vs verticale depuis point A **perpendiculaire à Frankfort** (et non NA de Steiner), environ **+4 à +6 mm** dans la publication, cadre normatif historique. Cette mesure n'est pas une composante indépendante de DDM clinique.
- Contexte squelettique : McNamara évalue les bases via N-perpendiculaire, longueurs Co–A et Co–Gn, différence maxillo-mandibulaire, hauteur faciale inférieure ANS–Me ; l'incisive ne se lit pas isolément. La **cible** de L1 peut dépendre de la correction/du développement des bases et de facteurs fonctionnels/esthétiques.

**2. Référence dynamique, nuance déterminante pour l'onboarding :**
- Si l'on envisage un déplacement squelettique mandibulaire, McNamara décrit soit la superposition d'un tracé mandibulaire projeté, soit la construction d'un nouveau `A–Pog` en déplaçant géométriquement le point A dans le sens opposé au déplacement mandibulaire prévu afin d'approximer le repère projeté. Il re-mesure la position de L1 vis-à-vis du **nouveau** A–Pog, avec une position incisive projetée dans certains cas de l'ordre de **1 à 2 mm antérieurs**.
- **La différence `(L1–A-Pog)_cible − (L1–A-Pog)_initiale` entre deux droites de référence squelettique qui changent n'est pas, en général, la translation physique de la dent ni la variation du périmètre d'arcade.** Ne pas la multiplier mécaniquement par 2.

**3. Comment transformer une stratégie McNamara en estimation d'espace si un jour autorisée :**
- Étape `mesure initiale` : même image/calibration, A, Pog_hard anatomiquement source-verrouillés, `L1_facial_surface` explicite ; fichier de contexte clinique et classification faciale. Ni `L1_incisal` seul, ni `Pog_soft` ni `Pog_hard` supposé équivalent sans preuve ne sont des alias libres.
- Étape `projection` : praticien renseigne scénario squelettique et pose/valide A–Pog projeté, puis sa **position cible incisive** par rapport à la nouvelle ligne. Faire le transfert dans un référentiel spatial commun pour isoler `déplacement réel mandibulaire-incisif` de la variation de ligne de référence.
- Étape `impact spatial` : une méthode séparée et sourcée pour projeter le mouvement réel de L1 en variation d'espace d'arcade, sensible à forme d'arcade, mécanique, tipping et hypothèses ; **pas de coefficient « McNamara ×2 » démontré comme formule propre à la publication de 1984** dans les sources lues. Les modèles géométriques de Mutinelli et al. (2000) varient selon la forme : environ 1,21–2,07 mm de changement de longueur d'arcade par mm de déplacement dans le modèle, ce qui constitue une démonstration de sensibilité, **pas un multiplicateur clinique directement autorisé**.
- Si les preuves géométriques ou méthode d'espace manquent, `DEPLACEMENT_PREVISIONNEL / NON_EVALUE`, `DDM_CEPHALO_MCNAMARA_NOT_DEFINED`, sans produire de DDM réelle numérique; un objectif incisif ne valide jamais automatiquement une extraction ou appareil.

**Comparatif décisionnel avec analyses V1 :**

| | Steiner (déjà V1) | McNamara (référence documentaire non V1) |
|---|---|---|
| Repère incisive inférieure | surface vestibulaire de L1 à `NB` | surface vestibulaire de L1 à `A–Pog` |
| Situation squelettique projetée | chevrons/objectif incisif dans boîte, cible individualisée | reconstruire A–Pog relatif à la correction des bases, puis objectif incisif |
| « DDM céphalo » | convention de planification Steiner `RI=2×(i–NB cible−i–NB initiale ajustée)` avec preuves et avertissements §65 | **pas de formule universelle autonome ×2 attribuable à McNamara 1984** trouvée ; conversion d'un mouvement réel vers espace = sous-méthode distincte |
| Conséquence | simulation clinique sous validation praticien et calibration mm vérifiée | ne pas intégrer silencieusement une variante McNamara sous le nom Steiner |

**Sources principales vérifiées** :
- McNamara JA Jr. *A method of cephalometric evaluation.* Am J Orthod 1984;86:449–469. DOI `10.1016/S0002-9416(84)90352-X`, PubMed https://pubmed.ncbi.nlm.nih.gov/6594933/ ; texte article via transcription tierce https://pdfcoffee.com/a-method-of-cephalometric-evaluation-mcnamara-1984-pdf-free.html (**reproduction secondaire à utiliser avec prudence**, et article primaire intégral non authentifié via éditeur).
- Étude contrôlant les variables « Lower incisor to A–Po » vs « Upper incisor to Point A vertical », https://pmc.ncbi.nlm.nih.gov/articles/PMC8018756/ ; revue systématique sur repères d'incisive https://pmc.ncbi.nlm.nih.gov/articles/PMC8770963/.
- Mutinelli, Manfredi, Cozzani (2000), *A mathematic-geometric model to calculate variation in mandibular arch form*, *Eur J Orthod* 22:113–125, DOI `10.1093/ejo/22.2.113`, https://pubmed.ncbi.nlm.nih.gov/10822884/ ; variations d'espace selon forme/mécanique (résultat de modèle, pas prescription clinique).

**Future FUE-MCN (NOT RUN)** : (1) L1→A–Pog trace/label exacts, pas L1→NB ; (2) absence L1_facial_surface/Pog_hard/mm calibration bloque mm ; (3) déplacement de A–Pog squelettique sans déplacement dentaire ⇒ **pas** de faux chiffre de gain/perte d'espace ; (4) tout scénario dentaire corrigé réinitialise les projections dépendantes et requiert revue humaine ; (5) aucun multiplicateur ×2 détourné de Steiner ; (6) archivage de contexte/versions sans patient réel ni LLM, état NC dans bilan ; (7) responsive, tokens thème, a11y/200% avec preuves UI après futur GO.

**GOAL/GATE** : réponse documentaire à la question, méthode clinique non activée, **ne pas modifier le choix propriétaire COM Digital Crown + Steiner 1953/1959**. Ne pas ajouter McNamara à la V1, ni code, merge, Vercel, ni nouvelle source de normes. **NEXT** : fermer les détails de la boîte Steiner / DDM et progresser dans le parcours conditionnel denture mixte, puis diagnostic/bilan. **Dernière mise à jour canonique : 05/11/2026 — POST §66, comparaison McNamara/Steiner SPEC_ONLY.**


### 67. PRE — 2026-11-05 — audit « 2,5 pour 1 » incisor advancement : mm vs degrés (SPEC ONLY)

**Question propriétaire** : « Moi j’ai eu dans ma formation d’ortho que 2.5 mm correspond à un mm je sais pas d’où ça sort ». Le couple `2,5` vs `1` possède **au moins deux interprétations différentes** attestées : (a) 1 mm avancée incisive mandibulaire pouvant produire jusqu'à 2,5 mm d'espace dans certaines modélisations (ratio mm/mm), et (b) **2,5°** de vestibuloversion pour ~1 mm d'avancée du bord incisif (angle/deplacement), enseignement MBT. Ne pas déclarer que l'utilisateur voulait l'une précisément sans clarifier l'unité de sa formation.

**Baseline** : PR #1213 OPEN/DRAFT HEAD documentaire `8955b6c960fac17253885ce3e2e4959ebafce279`, canonique §66 POST relu ; Notion PRE70 enregistré. Duo COM Digital Crown + Steiner 1953/1959 reste verrouillé. Aucune formule runtime, patient, merge ou déploiement.

**Sources web** : Laura Duncan, *The Proclination of Mandibular Incisors in Non-extraction Crowded Invisalign Cases*, MSc University of Manitoba (2015), p.80 https://mspace.lib.umanitoba.ca/bitstream/1993/30613/3/duncan_laura.pdf dit que 1 mm d'avancée incisive inférieure peut créer **jusqu'à 2,5 mm d'espace** ; texte PDF accessible, capture screenshot web demandée et échouée `cache miss`. Germane et al. AJODO 1991 (https://pubmed.ncbi.nlm.nih.gov/1815557/) modélisent le gain de périmètre ; une reproduction du papier et une table universitaire rapportent **1,04 mm de gain sur le premier mm incisif**, pas la constante 2,5. MBT 2001 repris par Daniel Richmond https://orthoinsummary.com/blog/space-analysis-how-incisor-movement-impacts-the-space-analysis-part-3/ : `2.5 degrees / 1 mm incisal edge advancement`, tipping approximatif d'une dent de 22 mm ; https://www.nature.com/articles/s41368-025-00350-2 confirme 1 mm ou 2,5°. Steiner 1960 et Royal London utilisent comme **convention de planification** 1 mm AP ↔ environ 2 mm périmètre. Aghera/Chung https://pubmed.ncbi.nlm.nih.gov/25636558/ ~1,66 mm/mm maxillaire, Yitschaky et al. https://pubmed.ncbi.nlm.nih.gov/26991841/ trouve une relation multifactorielle à grande variabilité (1 mm crowding resolved ↔ 0,2 mm AP protrusion + 0,5° proclination en moyenne), non interchangeable avec une conversion causale pure.

**GOAL/SUCCESS** : rechercher l'origine plausible, expliquer les deux unités et limites, dissocier ratio historique enseigné de norme validée, éviter tout coefficient ×2,5 dans V1 sans définition, méthode/version et approbation. **GATE** : SPEC_DISCOVERY / NO_CODE / FUE_NOT_RUN / NO_CLINICAL_GO.


### 67. POST — 2026-11-05 — le « 2,5 pour 1 » retrouvé : deux conversions non interchangeables

**Verdict scientifique/documentaire (NON-CLINICAL)** : Le souvenir `2,5 mm ↔ 1 mm` est plausible et possède une occurrence **quasiment textuelle** dans la thèse Laura O. Duncan, University of Manitoba, MSc 2015, §6.2 p.80 : « 1 mm protrusion of the lower anterior teeth can create as much as 2.5 mm of space », référant à Germane 1991 et Pandis 2010. Cela rapporte **un maximum possible**, pas un rapport moyen ni le résultat démontré de toutes les méthodes ni une « règle McNamara ». Source https://mspace.lib.umanitoba.ca/bitstream/1993/30613/3/duncan_laura.pdf ; extraction PDF vérifiée mais screenshot web `cache miss`, pas de confirmation graphique.

**Différence avec l'enseignement MBT** : Une autre formule de ratio `2,5 / 1` est géométrique et contient **un angle**, pas deux longueurs : selon MBT McLaughlin–Bennett–Trevisi (2001), `2,5°` de vestibuloversion ~ `1 mm` d'avancement de bord incisif inférieur (modèle de bascule sur dent de longueur ≈22 mm). Repris dans https://orthoinsummary.com/blog/space-analysis-how-incisor-movement-impacts-the-space-analysis-part-3/ et https://www.nature.com/articles/s41368-025-00350-2. Cela ne signifie **pas** « 2,5 mm de périmètre créés » ; changement d'inclinaison et déplacement AP dépendent de géométrie et mécanique.

**Confrontation avec résultats primaires / niveaux de preuve** :
- Germane et al., AJODO 1991, 100(5):421–427, DOI `10.1016/0889-5406(91)70081-7`, https://pubmed.ncbi.nlm.nih.gov/1815557/, modèle mathématique et avancement incisif plus efficace que expansion molaire ; transcription de son tableau / compilation académique indique **+1,04 mm de périmètre pour le premier mm d'avancée incisive**, +6,03 mm pour 5 mm d'avancée dans ce modèle, non `2,5 mm` par mm universel. Confrontation nécessaire : la thèse Duncan « as much as 2.5 mm » ne suffit pas pour affirmer que l'article Germane valide `1:2,5` dans toutes conditions ; source reproduite https://id.scribd.com/document/501374901/germane1991 et reprise universitaire https://oaktrust.library.tamu.edu/bitstreams/32d2b644-3f09-4ac7-a9d7-d29349428c97/download.
- Règle de planification **Steiner 1960 / Ricketts 1982** et Royal London : `1 mm avancée AP ≈ 2 mm de périmètre` (heuristique de traitement, avec limites).
- Modélisation maxillaire dans *AJODO*, 2015, https://pubmed.ncbi.nlm.nih.gov/25636558/ : +1,66 mm moyen de périmètre maxillaire par +1 mm protrusion, sur modèle ellipsoïde ; ce n'est pas applicable directement à l'arcade mandibulaire.
- Étude clinique Yitschaky et al. 2016, https://pubmed.ncbi.nlm.nih.gov/26991841/ : résolution d'1 mm de crowding associée en moyenne à +0,2 mm de protrusion L1–A–Pog et +0,5° de proclination mais grande variabilité et influence de plusieurs mécanismes ; **ne pas inverser automatiquement cette régression pour déclarer 1 mm protrusion = 5 mm créés**.

**Matrice de sens (une ligne par unité)** :
| Rapport | Numérateur | Dénominateur | Source/confiance | Usage clinique candidat |
|---|---|---|---|---|
| `2,5 mm / 1 mm` | gain d'espace **possible au maximum** | avancée AP incisive inférieure | thèse MSc 2015 citant études, interprétation exacte du maximum non recoupée dans original Germane | **comparateur/hypothèse de formation**, pas automatisme V1 |
| `2,5° / 1 mm` | inclinaison de la dent | déplacement AP du bord incisif | MBT / modèle géométrique, sensibilité au pivot/longueur | explicatif, **ne pas convertir tout changement d'IMPA en mm sans géométrie patient** |
| `2 mm / 1 mm` | variation d'espace/perimètre de l'arcade | déplacement AP incisif | Steiner 1960/Ricketts 1982/Royal London planning, convention historique | **Steiner boîte comme simulation** avec position initiale ajustée, cible et praticien, §65 |
| `1,66 mm / 1 mm` | périmètre maxillaire modélisé | avancée incisive supérieure | modèle *AJODO* 2015 | contexte comparateur, **pas coefficient mandibulaire** |

**Décision produit** : **aucune approbation du propriétaire pour utiliser ×2,5** ; il est prématuré d'attribuer cette règle à McNamara, CRANIOM ou à Steiner. Le vrai protocole approuvé reste COM Digital Crown + Steiner 1953/1959 ; la boîte Steiner peut proposer son propre coefficient ×2 sous accord clinique et source. Pour modèle mixte, valeurs mesurées/estimées, projet incisif et effets sur DDM restent distincts. Changement de coefficient = version de méthode et revue des dépendances, jamais variable hardcodée dans UI/traitement. Les thèmes restent des tokens globaux, 0 LLM runtime.

**Batterie FUE-2P5 candidate (NON RUN)** : (1) un champ de degré ne devient jamais mm ; (2) mode Steiner 1 mm AP cible → 2 mm espace uniquement si méthode/objectif/calibration valides ; (3) tentative ×2,5 sans méthode source/version → refus et indication `UNVERIFIED_METHOD` ; (4) variation modèle forme d'arcade/croissance/denture mixte → ne pas promettre valeur unique ; (5) résultat clinique non confondu avec prédiction thérapeutique ; (6) PDF/UI source/units/signes cohérents, pas de patient réel, responsive et thème, revue propriétaire avant GO.

**Une seule question de clarification clinique pour le prochain tour** : dans la formation, les `2,5` étaient-ils des **millimètres d'espace gagnés pour un millimètre d'avancée**, ou des **degrés de bascule incisive pour un millimètre d'avancée** ? Si doute, demander la diapo/support du cours et ne pas inventer attribution.

**GATE / RESULT** : origine plausible retrouvée et limitée, aucune règle V1 modifiée, aucune intervention frontend/backend, no merge/deploy/clinical validation, FUE_NOT_RUN. **Dernière mise à jour canonique : 05/11/2026 — POST §67, étude 2,5/1 SPEC_ONLY.**


### 68. PRE — 2026-11-06 — onboarding mixte : modèle DDM par défaut + adaptations (SPEC ONLY)

**Instruction propriétaire** : « Tu me proposes quoi alors !? On valide un modele par défaut et on propose des modifs !? Continuons notre onboarding on doit detziller un peu ». Cadrer le choix d'un modèle clinique candidat par défaut, les corrections humaines auditables et un parcours **précis** denture mixte, sans code. La proposition n'est PAS une approbation explicite du propriétaire d'un coefficient déjà opérationnel.

**Baseline** : PR #1213 OPEN/DRAFT sur `test/ceph-v1-facad-two-public-radios-20261105`, HEAD avant passe `3d909ef0124adb502f4d8d30fc49740ef2e807bf` ; canonique §67 POST relu ; Notion PRE71 ajouté. Deux analyses V1 seules verrouillées : COM Digital Crown + Steiner 1953/1959. La comparaison 2,5°/mm d'espace issue des modèles Mutinelli n'est pas une équation universelle.

**Preuves consultées** : Mutinelli et al., *Eur J Orthod* 2000, https://pubmed.ncbi.nlm.nih.gov/10822884/ (gain d'arcade sensible à la forme et au mouvement) ; étude de validation Moyers/Tanaka-Johnston sur denture mixte, 2025, https://pmc.ncbi.nlm.nih.gov/articles/PMC12724357/ (variabilité individuelle), synthèse https://pmc.ncbi.nlm.nih.gov/articles/PMC12034339/ (limites des références de population), source historique Steiner 1960 https://orthodonticatheneum.com/wp-content/uploads/2023/04/1960_Steiner-Use-of-cephalometrics-in-planning-orthodontic-treatment.pdf (forme d'arcade, relocation et boîte clinique). Les sources doivent être distinguées des choix ergonomiques conçus ici.

**GOAL/SUCCESS** : proposer modèle par défaut explicite, changement de méthode versionné, espace clinique/prediction d'éruption/Spee/leeway et repositionnement incisif toujours distincts, garde-fous des données manquantes, 6 à 7 sections conditionnelles de la Step2 existante et passage Step3, exemples non patients, FUE futures. **Gate** : SPEC_DISCOVERY / HUMAN_APPROVAL_PENDING / NO_CODE / no merge/Vercel.


### 68. POST — 2026-11-06 — onboarding V1 denture mixte détaillé et modèle DDM par défaut (CANDIDATE / NO CODE)

**Règle de gouvernance** : le propriétaire propose « un modèle par défaut et des modifications » ; le schéma ci-dessous est **RECOMMANDÉ, PAS ENCORE VALIDÉ**, ne change ni runtime ni prescriptions. L'onboarding reste dans **quatre étapes** : 1 Céphalométrie, 2 Moulages/occlusion, 3 Diagnostic, 4 Plan/Bilan. Seules analyses V1 validées : COM Digital Crown + Steiner 1953/1959 ; module de planification Steiner 1960 reste un **sous-protocole complémentaire candidat**, pas troisième analyse.

#### 68-A — Choix du modèle par défaut et variantes proposées

1. **Par défaut : « Steiner — repositionnement incisif »**, affichage source-versionné, correction céphalométrique par `2 × (L1–NB cible − L1–NB initiale ajustée)` en **mm d'effet d'espace**, seulement si L1–NB facial surface/étalon qualifié, correction de forme d'arcade explicitée, cible incisive et praticien confirmés. Si mesure, conversion ou cible manque : `NON_CALCULABLE` avec cause, et NON `0`. Les chevrons proposés par Steiner constituent une aide au choix, non décision automatique. Ne pas présenter une simulation comme « résultat clinique définitif ».
2. **Alternative « estimation géométrique individualisée »** : choisir une méthode de projection source-versionnée avec forme d'arcade, mouvement incisif, points d'appui et limites connus et validés ; méthode Mutinelli 2000 est un **comparateur**, pas une fonction numérique V1 déjà qualifiée.
3. **Alternative « contribution clinique manuelle »** : praticien renseigne en mm l'effet attendu sur l'espace, avec provenance/méthode/justification et date. Le système affiche `ESTIMATION CLINICIEN`, pas `AUTOMATIQUE STEINER`.
4. Ne **pas** proposer un simple slider universel de `° par mm` comme méthode clinique par défaut. La relation « 2,5° / 1 mm de DDM » est **un ordre de grandeur possible** pour un modèle d'arcade/bascule (Mutinelli 2000) et est différente de la règle MBT « 2,5° / 1 mm d'avance du bord incisif ». Le mode sélectionné ne se transforme jamais silencieusement en un autre.
5. **Les données source peuvent être corrigées** : position incisive initiale, correction de forme, cible, stade dentaire, mesures ED/EN, courbe de Spee et statut leeway ; chaque correction archive auteur/avant/après/méthode et invalide/recalcule uniquement les dépendants, incluant Step3/PDF. Aucune norme historique/constante legacy `107/90` activée par défaut.

#### 68-B — Parcours concret denture mixte : 7 blocs conditionnels dans la Step2 EXISTANTE

| Bloc | Question visible | Réponses utiles | Déclencheurs et interdictions |
|---|---|---|---|
| **01 Denture** | « Denture temporaire, mixte ou permanente ? » → **mixte choisie** ; « quelles dents restent temporaires ? » | dentition et statut éruption par quadrant, 6 permanentes D/G, incisives inférieures permanentes, canines/prémolaires présentes ou non, pertes précoces, anomalies | aucun âge ne classe automatiquement la dentition ; dent absente = ni largeur `0` ni classe occlusale normale ; limiter la saisie aux dents pertinentes, odontogramme détaillé facultatif |
| **02 Sources** | « Quelles données possèdes-tu ? » | examen clinique, modèles physiques/scan mesurable, photographies, radios intraorales mesurables, téléradio calibrée si disponible | si source insuffisante, conserver constat qualitatif mais ne pas inventer des mm ; ne pas exiger de radiographie supplémentaire pour débloquer une fiche, décision d'imagerie clinique |
| **03 Espace et prédiction** | « Quel espace est disponible et quelles tailles dentaires sont connues ou à estimer ? » | ED maxillaire et mandibulaire mesurés, largeur mésio-distale des dents éruptées, canines/prémolaires non éruptées : mesure radiographique qualifiée, méthode statistique **sélectionnée explicitement** (Moyers percentile exact, Tanaka-Johnston source), ou entrée clinique motivée | jamais prédire sans les entrées nécessaires ; population/percentile et incertitude signalées ; choisir méthode par arcade (pas deux méthodes superposées) ; résultat `DDM_ENCOMBREMENT = ED−EN` signé, `ESTIMÉ` quand EN prédit, pas certifié définitif |
| **04 Spee et espace de transition** | « Courbe de Spee pertinente et mesurable ? Les molaires temporaires résiduelles permettent-elles d'envisager un leeway space ? » | Spee (absente/non évaluable/mesurée, profondeur et méthode si pertinent), espace de transition/leeway par quadrant **mesuré ou estimé**, conservation projetée oui/non/indéterminée | **Spee** : impact sur l'espace si méthode validée, pas constante automatique ; **leeway** : potentiel anatomique distinct de l'espace effectivement conservé. Un leeway hypothétique ne s'ajoute pas à la DDM réelle actuelle et ne s'ajoute pas deux fois à un scénario prévisionnel. Ne pas supposer que le praticien prescrira un mainteneur |
| **05 Occlusion sagittale** | « Relations molaires et canines observables à D/G ? » | molaires permanentes D/G Classe I/II/III si réellement évaluables ; canines permanentes classables uniquement si éruptées/occlusion adaptée ; dentition temporaire décrite séparément, asymétrie/subdivision | aucun copier-coller automatique D/G, aucune classe forcée si dent absente/non-éruptée, angle ANB ne déduit pas classe molaire clinique |
| **06 Vertical, transversal et fonctionnel** | « Surplomb/recouvrement, articulé croisé, milieux et déviation fonctionnelle ? » | mesures mm avec source si observées, déviation des milieux D/G, crossbite antérieur/postérieur avec côté et dents, béance, ciseaux, forme d'arcade, éléments fonctionnels cliniques | champ « mm » seulement si mesure fiable ; si croisé oui → demander côté/secteur, si shift fonctionnel oui → examen clinique obligatoire ; sans examen fonctionnel : `NON_EVALUE` |
| **07 Vérification** | « Souhaites-tu confirmer et passer au diagnostic ? » | synthèse par arcade/côté, mesure vs estimation, statut/limitations, source/date, réouverture/correction | poursuivre sur brouillon partiel permis ; avertissement lacunes, aucune DDM réelle finale ni suggestion extraction/expansion sans Step3 praticien |

**Règle de progressivité** : afficher blocs suivants conditionnellement, sans multiplier les pages. Mettre ED/EN côté arcade et relation D/G visibles simultanément quand disponibles. Un champ masqué parce que sa condition devient fausse perd son statut actif, mais la version historique n'est pas supprimée silencieusement. UI responsive 390/430/768/1280, clavier/tactile/zoom 200%, couleurs uniquement via tokens sémantiques globaux.

#### 68-C — Parcours inter-étapes de la DDM, avec limites propres à la denture mixte

- **Step1 Céphalométrie** : `L1–NB_MM` seulement avec point facial incisif anatomiquement source-verrouillé, calibration pertinente et mesure fiable ; ces conditions restent NC sur deux JPEG témoins. Si indisponible, le reste de l'onboarding fonctionne.
- **Step2 Moulages** : produire une carte **État de l'espace** avec `ED`, `EN mesuré/estimé`, `DDM encombrement ED−EN`, `impact Spee` séparément, `DDM clinique` si la définition choisie intègre les deux, et **leeway potentiel** en panneau d'hypothèse non automatiquement additionné. Ne pas additionner Spee deux fois. La dénomination exacte de DDM clinique incluant Spee demeure soumise à accord propriétaire.
- **Step3 Diagnostic** : proposer préselection `Méthode de planification : Steiner`. Demander/afficher `L1–NB initial mesuré`, `initial ajusté forme arcade`, `cible i–NB projetée par chevrons et facteurs cliniques`, `cible retenue`, puis `effet RI signé ×2` **après validation humaine**. Si mode manuel, saisir `effet mm` avec justification ; si méthode géométrique, source / géométrie et preuve exigées. Calculer `DDM RÉELLE = DDM CLINIQUE + CORRECTION CÉPHALO` uniquement si termes compatibles (même arcade mandibulaire, millimètres signés, stade et période de référence, provenance).
- **Step4 Bilan** : triptyque `DDM clinique / DDM céphalo / DDM réelle` plus postes détaillés `encombrement / Spee / leeway scénario`, niveaux de confiance et résultats par arcade, méthodes/versions et validations. Un résultat `ESTIMÉ` ou `HYPOTHÉTIQUE` demeure ainsi dans le PDF. Le maxillaire possède son propre bilan d'arcade, **sans réutiliser par défaut le déplacement incisif mandibulaire Steiner**.

**Exemple entièrement fictif NON CLINIQUE (cohérence des signes)** : espace disponible mandibulaire `ED=64 mm`, nécessaire estimé `EN=69 mm` → encombrement `−5 mm`; impact Spee `−1 mm` *si mesuré/méthode validée* → DDM clinique `−6 mm`; L1–NB initiale ajustée `5 mm`, cible décidée `4 mm` → RI Steiner `−2 mm`; **DDM réelle projetée = `−8 mm`**. Si l'estimation EN, Spee ou RI n'est pas disponible/validée, ne pas produire `−8 mm`; indiquer `À COMPLÉTER` avec sous-termes manquants. Leeway non ajouté automatiquement ; exemple ne prescrit aucun traitement.

#### 68-D — Batterie FUE prochaine (définie, NON RUN)

- FUE-MX-D01 : cas mixte avec 6 permanentes D/G, canines non éruptées, molaires évaluables → questions conditionnelles pertinentes, sans classes canines permanentes inventées.
- FUE-MX-D02 : modèles mesurés et EN prédit par Moyers/Tanaka choisi → méthode, percentile/population, incertitude et état ESTIMÉ affichés ; jamais EN chiffré sans entrées.
- FUE-MX-D03 : retrait de la méthode EN ou de Spee → DDM clinique/reelle invalidée, pas remplacée par `0`, historique intact.
- FUE-MX-D04 : leeway mesuré et conservateur projeté → potentiel distinct du gain effectif et sans double comptage de ED/EN ni Spee.
- FUE-MX-D05 : L1–NB mm absent, 2 JPEG publics non calibrés → RI Steiner et DDM réelle NC, aucune fausse mesure.
- FUE-MX-D06 : source hypothétique calibrée, `5→4` mm → effet `−2` mm avec oracle ; sortie finale `−8` uniquement pour termes d'exemple complet.
- FUE-MX-D07 : demande de coefficient `2,5°/mm d'espace` → avertissement modèle non universel ; refus de l'activer sans méthode explicitement définie/versionnée.
- FUE-MX-D08 : changer méthode/cible/classe dentition après évaluation → statut revue, recalcul transitif et PDF cohérent, sans faux clinique validé.
- FUE-MX-D09 : croisements D/G, dent non éruptée, photos sans modèles, brouillon partiel, aucun diagnostic autonome.
- FUE-MX-D10 : thèmes globaux, 0 LLM runtime, aucun patient réel GitHub/CI, a11y et captures BEFORE/AFTER à valider par propriétaire ultérieurement.

**Décisions ouvertes, non bloquantes pour avancer** : accepter `Steiner` comme **méthode de planification préselectionnée** (et non simple coefficient en dur), Spee comme sous-poste de DDM clinique sans double comptage, choix explicite de méthode EN en denture mixte (recommandation : mesures individuelles fiables d'abord, méthodes statistiques uniquement si nécessaires avec provenance). L'acceptation de la direction « modèle par défaut et modifications » ne constitue PAS à elle seule validation des calculs cliniques.

**GATE / PREUVE** : SPEC_ONLY / HUMAN_APPROVAL_PENDING, FUE ci-dessus NOT RUN. Aucun code produit, merge, Vercel, patient ni sortie clinique. **NEXT** : faire approuver l'ordre des questions et les garde-fous, puis détailler Step3 Diagnostic et Step4 Bilan avant réconciliation technique. **Dernière mise à jour canonique : 06/11/2026 — POST §68, onboarding mixte et modèle par défaut candidat.**
