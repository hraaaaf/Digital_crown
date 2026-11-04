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

**CHANTIER Digital Crown Céphalo V1 · LOT 1/4 R11–R14 NON CLOTURE · SOUS-LOT dossier des sources + 10 FUE préflight synthétiques · NEXT revue clinique indépendante + 10 FUE réelles · GOAL approbation scientifique traçable avant activation R15/PDF.**
