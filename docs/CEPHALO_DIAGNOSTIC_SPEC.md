# DIGITAL CROWN — CÉPHALOMÉTRIE DIAGNOSTIQUE

**FICHIER CANONIQUE DE REPRISE**  
**Runtime SRPose38 :** PR #388 — `4e3ec0c84b58893d19214268075333042c4021a4`  
**Fondation diagnostique :** PR #390 — `ce7cc5a17d0571290c0b762a553b4feaa534e026`  
**Registre normatif :** PR #391 — `1c055f817e38a694de1d47f8144fcb1d9eaa2e9d`  
**Intégrité inter-objets :** PR #392 — `1566f77ff5ee9d848f8e31787f92e542f16a38b7`  
**Adaptateur MeasurementEvidence :** PR #393 — `65349a62d4b132f6bd6c2cb15f3e52b38e5d38ab`  
**Matérialisation ConstructionEvidence :** PR #394 — `c647c0843b265eadf4a70652ae4608708f48d2be`  
**Frontière patient/cas :** PR #395 — `3e8e39eb88581bd461a8104b9fad96b82d65292a`  
**Persistence runtime evidence :** PR #397 — `7aa83d566c87db6796cddea5a1facd891f8b5896`  
**PR active :** #398 — provenance calibration manuelle  
**Statut :** chantier actif ; aucun diagnostic ni plan thérapeutique déclaré certifié

## GOAL GLOBAL

`cas patient → image → 38 landmarks → constructions → mesures → analyses → findings → synthèse diagnostique → problem list → objectifs → options thérapeutiques → validation praticien → plan final`

## INVARIANT

`landmark != construction != measurement != interpretation != diagnosis != indication != treatment plan`

Une donnée manquante reste `UNKNOWN` / `NOT_COMPUTABLE`. Aucune norme, classe, croissance ou indication n'est devinée.

## LOTS

| Lot | Goal | État vérifié |
|---|---|---|
| 0 | Modèle de preuve clinique typé | EN COURS — contrats, resolver, patient/cas, constructions, mesures et persistence runtime mergés ; calibration auditée en #398 ; read-path source de vérité restant |
| 1 | Purger logique clinique non sourcée | FAIT — PR #371 |
| 2 | Runtime SRPose38 exact | FAIT — PR #388 |
| 3 | Contrat des 38 landmarks | EN COURS — ordre/identité 38/38 certifiés ; définitions opérationnelles partielles |
| 4 | Constructions géométriques | EN COURS — CRANIOM linéaire matérialisé ; conventions mandibulaires restantes |
| 5 | COM / CRANIOM | EN COURS — géométrie + références spécifiques inertes disponibles |
| 6 | Steiner | À FAIRE |
| 7 | Tweed/Merrifield | À FAIRE |
| 8 | Wits/Jacobson + Downs | À FAIRE |
| 9 | McNamara | À FAIRE |
| 10 | Ricketts + tissus mous | À FAIRE |
| 11 | Registre normatif | EN COURS — fondation inerte mergée ; aucune activation patient |
| 12 | Synthèse diagnostique | À FAIRE |
| 13 | Indications / options thérapeutiques | À FAIRE |
| 14 | Validation clinique + UX/PDF | À FAIRE |

## ACQUIS VÉRIFIÉS

### SRPose38
- runtime CPU certifié ;
- ordre CL-Detection 38/38 documenté ;
- hash modèle et pipeline déterministes ;
- le bridge persistence refuse qu'un fallback automatique soit qualifié de preuve SRPose38.

### CRANIOM
Sources publiées enregistrées :
- Part 1 DOI `10.1051/odfen/2010406` ;
- Part 2 DOI `10.1051/odfen/2011104`.

Constructions versionnées :
- `CRANIOM_A_TO_N_VERTICAL_V1` ;
- `CRANIOM_B_TO_N_VERTICAL_V1` ;
- `CRANIOM_AB_PRIME_V1` ;
- `CRANIOM_S_TO_N_VERTICAL_DEPTH_V1`.

Les quatre mesures correspondantes passent par `MeasurementEvidence`. Sans construction disponible et calibration prouvée, elles restent `NOT_COMPUTABLE`.

### Graphe de preuve et persistence
Le resolver impose l'existence/type des références. #395 impose même patient, même cas et audit praticien cohérent. #397 persiste `_evidence_graph_v1` dans `CephaloAnalysis.angles_data` avec révisions/historique sans modifier le payload API public.

PR #397 est mergée sur master au commit `7aa83d566c87db6796cddea5a1facd891f8b5896`. Son HEAD final `a52fc93ec8cc37b72b8e9b66e48f5a26d38f91b0` a passé CI `34490188077` et T2 `34490188120` avant merge.

### Calibration auditée #398
Le remplacement du POST `/analyses/{analysis_id}/calibrate` conserve le même contrat public et ajoute :
- p1/p2, distance réelle, ratio recalculé ;
- méthode/version ;
- identité opérateur et horodatage UTC ;
- transaction unique ratio + provenance + géométrie + evidence snapshot ;
- révision `MANUAL_CALIBRATION` sans inventer de nouveaux landmarks/constructions ;
- refus si runtime landmarks et evidence courante divergent ;
- refus si une couche clinique aval existe, plutôt que conserver silencieusement une conclusion potentiellement périmée ;
- analyses legacy calibrables sans fabrication rétroactive de graphe.

Cette section #398 reste **en certification**, pas déclarée mergée.

## GATES OUVERTS

- CI/T2 exact-head + review de #398 puis merge ;
- propager l'identité praticien sur les corrections manuelles avant `MANUAL_CORRECTED/CLINICIAN_VALIDATED` ;
- faire du graphe persistant la source read-path des quatre mesures CRANIOM ;
- convention du plan mandibulaire propre à chaque analyse ;
- `Gi/Gs` CRANIOM absents comme landmarks SRPose38 distincts ;
- `A''B''` non calculable sans protocole NHP/regard horizontal ;
- aucune référence normative active pour classifier un patient.

## GATES SCIENTIFIQUES

Mesure : landmarks définis → construction versionnée → formule testée → unité/calibration → source enregistrée → norme séparée → contexte explicite → absence = `NOT_COMPUTABLE`.

Diagnostic : règle versionnée/sourcée + contradictions visibles + cas goldens + validation praticien.

Traitement : diagnostic validé + données cliniques requises + indication/contre-indications sourcées + sélection praticien. Jamais de prescription autonome.

## PREUVES CI

- #391 : CI `34471586594` success ; T2 `34471586570` success.
- #392 : CI `34472921729` success ; T2 `34472921733` success.
- #393 : CI `34474219020` success ; T2 `34474219021` success.
- #394 : CI `34474296352` success ; T2 `34474296300` success.
- #395 : CI `34476589446` success ; T2 `34476589386` success ; merge `3e8e39eb88581bd461a8104b9fad96b82d65292a`.
- #397 HEAD `a52fc93ec8cc37b72b8e9b66e48f5a26d38f91b0` : CI `34490188077` success ; T2 `34490188120` success ; merge `7aa83d566c87db6796cddea5a1facd891f8b5896`.
- #398 : validation exact-head en cours après rebaseline sur master ; aucune preuve verte finale déclarée à ce stade.

## NEXT EXACT

1. certifier #398 exact-head ;
2. corriger toute défaillance ;
3. vérifier reviews/threads, fermer docs et merger si vert ;
4. post-merge : audit praticien des corrections manuelles ;
5. basculer le read-path des quatre mesures CRANIOM vers le graphe typé ;
6. poursuivre les conventions mandibulaires.

## SÉQUENCE RESTANTE

`calibration provenance → correction-landmark audit → read-path source-of-truth → conventions mandibulaires → COM/CRANIOM complet → Steiner → Tweed/Merrifield → Wits/Downs → McNamara → Ricketts/soft tissue → diagnostic multiaxial → problem list/objectifs → options → validation clinique → UX/PDF → closeout`

## DÉPLOIEMENT

Aucun déploiement Vercel sans autorisation explicite.
