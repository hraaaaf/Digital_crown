# R15 — Studio clinique UX/UI

**Date :** 2026-09-13  
**Repo :** `hraaaaf/Digital_crown`  
**Base auditée :** `1e79d236b89a56592128d09451803b9adf4ee0fd`  
**Handover amont :** `docs/handovers/2026-09-12-cephalo-r14-to-r15-handover.md`

## GOAL

Rendre le Studio céphalométrique compréhensible et sûr pour le praticien en séparant explicitement :

1. **preuve scientifique / mesures brutes** ;
2. **état clinique structuré R11 → R14**, uniquement lorsqu’il existe réellement dans les preuves persistées ;
3. **notes rédigées par le praticien**, jamais préremplies automatiquement par un ancien narratif calculé.

R15 ne crée aucune règle clinique, aucun diagnostic, aucune option thérapeutique et aucun plan final qui n’existe pas déjà comme objet traçable.

## SUCCÈS OBSERVABLE

- un ancien `ai_diagnostic` non marqué ne remplit plus automatiquement les champs éditables praticien ;
- `ai_narrative` d’une nouvelle analyse ne remplit plus automatiquement ces champs ;
- `analyse_moulages_auto` reste descriptive et n’est plus copiée dans `diag.analyse_moulages` ;
- toute nouvelle sauvegarde de notes praticien porte une provenance explicite `CLINICIAN_AUTHORED_V1` ;
- une note marquée praticien se recharge correctement ;
- l’écran expose l’état de la chaîne scientifique typée et ses comptes lorsqu’ils existent ;
- R11 / R12 / R13 / R14 sont affichés avec leurs objets réels s’ils existent, sinon comme **non matérialisés**, jamais inventés ;
- aucune action de validation clinique n’est exposée sans endpoint transactionnel réel et preuve persistée ;
- 390 / 768 / 1280 px : aucun overflow horizontal ni erreur console/page sur le harness certifié.

## PREUVES D’AUDIT — ÉTAT AVANT

### A. Narratif legacy auto-promu

`CephaloWorkspace.handleSelectHistory` charge `anglesData.ai_narrative || loaded.ai_diagnostic` puis copie automatiquement diagnostic, moulages, synthèse et stratégie dans `store.diag`.

### B. Moulages calculés auto-promus

`CephaloWorkspace` copie `computeStep3Data(...).analyse_moulages_auto` dans `diag.analyse_moulages` lorsque le champ praticien est vide/placeholder.

### C. Nouvelle analyse auto-promue

`useOrthoStore.runAnalysis` copie `data.results.ai_narrative` vers les champs `diag` éditables.

### D. Provenance persistée ambiguë

`buildPayload` persiste actuellement les notes praticien sous la clé historique `ai_diagnostic`. Le backend accepte `Dict[str, str]` et le repository écrit cette structure telle quelle. Les anciens dossiers peuvent donc contenir sous la même clé soit du contenu calculé, soit une saisie praticien.

### E. Chaîne typée disponible mais non présentée

Le GET canonique `/ia/analyses/{id}` passe par `project_runtime_chain_read_path`, vérifie le graphe typé et expose `scientific_read_path`. `Step3Clinical` n’en présente actuellement aucun état.

### F. R11 → R14 = contrats de sécurité, pas contenu clinique implicite

Les modules R11/R12/R13/R14 valident provenance, blocages et décisions humaines. Les goldens R14 sont synthétiques ; aucune persistance clinique R13/R14 réelle n’est prouvée dans le parcours actuel. R15 doit donc montrer l’absence comme absence.

## MOCK / RÉFÉRENCE VERROUILLÉE

Conserver les tokens, cartes, accordéons et densité visuelle existants. **Pas de redesign global.**

### Bloc 1 — `Chaîne scientifique`

En haut de l’étape clinique :

- badge `Vérifiée`, `Incomplète` ou `Non disponible` ;
- compteurs Sources / Repères / Constructions / Mesures ;
- statut calibration si disponible ;
- texte court : preuve brute ≠ diagnostic.

### Bloc 2 — `État clinique structuré`

Quatre lignes/cartes compactes :

- R11 Diagnostic : nombre d’objets réels ou `Non matérialisé` ;
- R12 Problèmes / objectifs : idem ;
- R13 Options thérapeutiques : idem, sans auto-sélection ;
- R14 Stratégie finale : statut réel si présent, sinon `Aucune stratégie finale structurée validée`.

Aucun bouton `Valider`, `Accepter`, `Plan final` tant qu’une mutation backend transactionnelle certifiée n’existe pas.

### Bloc 3 — `Notes du praticien`

Les textareas existantes restent éditables mais portent une mention visible :

`Saisie praticien — jamais préremplie automatiquement.`

Le bloc automatique des moulages reste lecture seule et précise :

`Description calculée — non copiée dans la note praticien.`

## PROVENANCE DES NOTES

Nouveau marqueur :

`_origin = CLINICIAN_AUTHORED_V1`

Règle de lecture : seules les structures portant ce marqueur peuvent préremplir `diag`. Les contenus historiques non marqués restent non attribuables et ne sont pas injectés dans les champs éditables.

## NON-GOALS R15

- aucune activation de norme scientifique nouvelle ;
- aucune règle diagnostique/thérapeutique nouvelle ;
- aucun faux workflow de validation R13/R14 ;
- aucun PDF/restitution R16 ;
- aucun déploiement Vercel ;
- aucune suppression de compatibilité backend historique sans migration prouvée.

## TESTS PRÉVUS

### Unitaires

- provenance legacy non marquée rejetée pour édition ;
- provenance `CLINICIAN_AUTHORED_V1` rechargée ;
- sérialisation praticien ajoute le marqueur ;
- parseur evidence graph : chaîne vérifiée / absente / compteurs ;
- R11→R14 absents => statuts explicites `non matérialisé` ;
- objets synthétiques réellement présents => compteurs/statuts reflétés sans extrapolation.

### Régression store/workspace

- `runAnalysis` ne remplit plus `diag` depuis `ai_narrative` ;
- historique legacy ne remplit plus `diag` ;
- moulages auto ne remplissent plus `diag.analyse_moulages` ;
- sauvegarde des notes praticien reste fonctionnelle.

### Visuel obligatoire

BEFORE puis AFTER sur **390 / 768 / 1280 px**, même harness et mêmes données :

- capture full-page ;
- overflow horizontal = 0 ;
- erreurs console/page = 0 ;
- AFTER : chaîne scientifique visible ;
- AFTER : état R11→R14 visible ;
- AFTER : provenance praticien visible ;
- AFTER : aucun bouton de validation clinique fictif.

## NEXT EXACT

1. capturer le BEFORE réel sur la base `1e79d236...` ;
2. vérifier les trois artefacts ;
3. seulement ensuite implémenter le patch minimal R15 ;
4. tests + AFTER mêmes viewports ;
5. PR exact-head + CI ;
6. merge ;
7. closeout R15 ;
8. ouvrir R16 dans un lot séparé.
