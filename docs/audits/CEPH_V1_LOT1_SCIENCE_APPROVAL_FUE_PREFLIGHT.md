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
