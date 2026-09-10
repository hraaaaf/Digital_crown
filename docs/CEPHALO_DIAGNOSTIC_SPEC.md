# DIGITAL CROWN — CÉPHALOMÉTRIE DIAGNOSTIQUE

**FICHIER CANONIQUE DE REPRISE**  
**Runtime SRPose38 :** PR #388 — `4e3ec0c84b58893d19214268075333042c4021a4`  
**Fondation diagnostique :** PR #390 — `ce7cc5a17d0571290c0b762a553b4feaa534e026`  
**Registre normatif :** PR #391 — `1c055f817e38a694de1d47f8144fcb1d9eaa2e9d`  
**Intégrité inter-objets :** PR #392 — `1566f77ff5ee9d848f8e31787f92e542f16a38b7`  
**Adaptateur MeasurementEvidence :** PR #393 — `65349a62d4b132f6bd6c2cb15f3e52b38e5d38ab`  
**Matérialisation ConstructionEvidence :** PR #394 — `c647c0843b265eadf4a70652ae4608708f48d2be`  
**Frontière patient/cas :** PR #395 — `3e8e39eb88581bd461a8104b9fad96b82d65292a`  
**PR active :** #397 — persistence runtime du graphe typé  
**Statut :** chantier actif ; aucun diagnostic ni plan thérapeutique déclaré certifié

## GOAL GLOBAL

`cas patient → image → 38 landmarks → constructions → mesures → analyses → findings → synthèse diagnostique → problem list → objectifs → options thérapeutiques → validation praticien → plan final`

## INVARIANT

`landmark != construction != measurement != interpretation != diagnosis != indication != treatment plan`

Une donnée manquante reste `UNKNOWN` / `NOT_COMPUTABLE`. Aucune norme, classe, croissance ou indication n'est devinée.

## LOTS

| Lot | Goal | État vérifié |
|---|---|---|
| 0 | Modèle de preuve clinique typé | EN COURS — contrats, registre, resolver, frontière patient/cas, ConstructionEvidence et MeasurementEvidence mergés ; persistence runtime en #397 ; read-path source de vérité restant |
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
- le nouveau bridge de persistence refuse de qualifier un fallback automatique comme SRPose38 et exige l'identité exacte des 38 points.

### CRANIOM
Sources publiées enregistrées :
- Part 1 DOI `10.1051/odfen/2010406` ;
- Part 2 DOI `10.1051/odfen/2011104`.

Constructions versionnées et matérialisables :
- `CRANIOM_A_TO_N_VERTICAL_V1` ;
- `CRANIOM_B_TO_N_VERTICAL_V1` ;
- `CRANIOM_AB_PRIME_V1` ;
- `CRANIOM_S_TO_N_VERTICAL_DEPTH_V1`.

Les quatre mesures correspondantes passent par `MeasurementEvidence`. Sans construction disponible et calibration explicitement prouvée, elles restent `NOT_COMPUTABLE`.

### Graphe de preuve
Le resolver vérifie identifiants, références, registre normatif et gates du plan final. PR #395 ajoute : même patient, même cas, vraie source de calibration, et vrai `ClinicianValidationEvidence` pour tout objet déclaré validé/sélectionné.

### Persistence runtime #397
Le bridge en cours stocke le snapshot sous `_evidence_graph_v1` dans le JSON `CephaloAnalysis.angles_data`. Ce choix est additif et atomique : aucune migration DB n'est nécessaire et le payload public historique reste inchangé.

Le snapshot persiste :
`SourceEvidence → LandmarkEvidence → ConstructionEvidence → MeasurementEvidence`.

Règles fail-closed du bridge :
- mode `SOTA_ONNX_38` + contrat exact 38 points requis pour des landmarks automatiques certifiés ;
- fallback automatique legacy → aucune fausse preuve landmark SRPose38 ;
- auto-calibration legacy seule → aucune mesure linéaire typée `AVAILABLE` ;
- calibration manuelle deux-points explicitement persistée → géométrie recalculée/croisée avec `mm_per_pixel` avant utilisation ;
- raffinement manuel → nouvelle révision ; points SRPose38 initiaux conservés, points courants marqués `MANUAL/OBSERVED`, jamais prétendus `CLINICIAN_VALIDATED` sans audit réel.

`authority_status=PERSISTED_NOT_YET_READ_PATH` : la persistence existe, mais les écrans/API historiques lisent encore le payload de compatibilité. La bascule de lecture reste donc un gate distinct.

## GATES OUVERTS

- CI exacte et review de #397 ;
- faire du graphe persistant la source read-path de vérité sans casser la compatibilité ;
- persister la provenance de calibration manuelle depuis la route `/analyses/{id}/calibrate` ;
- propager l'identité praticien sur les corrections manuelles avant de les qualifier `MANUAL_CORRECTED/CLINICIAN_VALIDATED` ;
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
- #395 HEAD `7daf28d2d7e93c3d34dca97d655fc67db3fb1dfa` : CI `34476589446` success ; T2 `34476589386` success ; merge `3e8e39eb88581bd461a8104b9fad96b82d65292a`.
- #397 : certification du HEAD final requise avant merge.

## NEXT EXACT

1. certifier le HEAD final #397 ;
2. corriger tout échec puis vérifier reviews/threads ;
3. merger #397 uniquement si vert ;
4. post-merge : câbler la provenance réelle de calibration manuelle + audit praticien des corrections ;
5. basculer ensuite le read-path des quatre mesures CRANIOM vers le graphe typé ;
6. poursuivre les conventions mandibulaires.

## SÉQUENCE RESTANTE

`persistence evidence → calibration/audit provenance → read-path source-of-truth → conventions mandibulaires → COM/CRANIOM complet → Steiner → Tweed/Merrifield → Wits/Downs → McNamara → Ricketts/soft tissue → diagnostic multiaxial → problem list/objectifs → options → validation clinique → UX/PDF → closeout`

## DÉPLOIEMENT

Aucun déploiement Vercel sans autorisation explicite.
