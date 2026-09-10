# DIGITAL CROWN — CÉPHALOMÉTRIE DIAGNOSTIQUE

**FICHIER CANONIQUE DE REPRISE**  
**Baseline runtime SRPose38 :** PR #388 — `4e3ec0c84b58893d19214268075333042c4021a4`  
**Fondation diagnostique :** PR #390 — `ce7cc5a17d0571290c0b762a553b4feaa534e026`  
**Registre normatif :** PR #391 — merged `1c055f817e38a694de1d47f8144fcb1d9eaa2e9d`  
**Intégrité inter-objets :** PR #392 — merged `1566f77ff5ee9d848f8e31787f92e542f16a38b7`  
**Branche active :** `feat/cephalo-evidence-graph-resolver` — durcissement patient/cas + audit praticien réel  
**Statut :** chantier actif ; aucun diagnostic ni plan thérapeutique déclaré certifié

## GOAL GLOBAL

Construire un workflow céphalométrique local, déterministe et traçable :

`cas patient → image → 38 landmarks → constructions → mesures → analyses → findings → synthèse diagnostique → problem list → objectifs → options thérapeutiques → validation praticien → plan final`

## INVARIANT DE SÉCURITÉ

`landmark != construction != measurement != interpretation != diagnosis != indication != treatment plan`

Une donnée manquante reste `UNKNOWN` / `NOT_COMPUTABLE`. Aucune valeur, norme, classe, croissance ou indication n'est devinée.

## LOTS

| Lot | Goal | Succès observable | État |
|---|---|---|---|
| 0 | Modèle de preuve | objets typés + références résolues + contexte patient/cas + audit praticien + adaptateur runtime | EN COURS — schémas #390, registre #391, graphe #392 mergés ; durcissement patient/cas en cours ; adaptateur runtime restant |
| 1 | Purger logique clinique non sourcée | moteur géométrique sans diagnostic/traitement implicite | FAIT — PR #371 |
| 2 | Runtime SRPose38 exact | 38/38, pipeline ONNX parity certifié, fail-closed asset | FAIT — PR #388 |
| 3 | Contrat des 38 landmarks | ordre, noms, alias et définitions opérationnelles certifiés | EN COURS — ordre 38/38 certifié ; COM critique partiel |
| 4 | Constructions géométriques | plans/axes/projections versionnés + golden tests | EN COURS — sous-lot linéaire CRANIOM A'B'/N-vertical mergé via #390 ; conventions mandibulaires restantes |
| 5 | COM / CRANIOM | mesures de la méthode calculables + références spécifiques sourcées séparément | EN COURS — méthode + publications Part 1/2 identifiées ; références inertes mergées via #391 |
| 6 | Steiner | matrice dépendances + formules + normes sourcées | À FAIRE |
| 7 | Tweed/Merrifield | idem | À FAIRE |
| 8 | Wits/Jacobson + Downs | idem | À FAIRE |
| 9 | McNamara | idem | À FAIRE |
| 10 | Ricketts + tissus mous | idem | À FAIRE |
| 11 | Registre normatif | contexte âge/sexe/population/source/version + fail-closed | EN COURS — fondation inerte mergée via #391 ; aucune activation patient |
| 12 | Synthèse diagnostique | règles déterministes explicables, contradictions visibles | À FAIRE |
| 13 | Indications / plan thérapeutique | options sourcées, jamais prescription autonome | À FAIRE |
| 14 | Validation clinique + UX/PDF | cas goldens praticien, traçabilité, BEFORE/AFTER UI | À FAIRE |

## ACQUIS SCIENTIFIQUES DU CHANTIER

### SRPose38

- modèle 38 points intégré et certifié runtime sur CPU ;
- ordre CL-Detection 1..38 ↔ runtime 0..37 documenté ;
- ambiguïtés anatomiques conservées explicitement au lieu d'être devinées.

### Méthode historique COM / CRANIOM

Le flux historique Digital Crown appelé `COM` a été rapproché de la méthode **C.R.A.N.I.O.M.** de Bonnefont, Casteigt, Ernoult et Sorel.

Sources publiées :
- Part 1 : Journal of Dentofacial Anomalies and Orthodontics. 2010;13(4):385-400. DOI `10.1051/odfen/2010406`.
- Part 2 : Journal of Dentofacial Anomalies and Orthodontics. 2011;14:105. DOI `10.1051/odfen/2011104`.

Les publications décrivent un échantillon de **83 jeunes adultes Classe I non traités**. Les valeurs CRANIOM restent des références spécifiques à cette méthode/population, jamais des normes universelles.

Décision produit : le label `COM` peut rester transitoirement pour compatibilité UX, mais le registre scientifique identifie la méthode source comme `CRANIOM`.

### Géométrie CRANIOM mergée via #390

- `CRANIOM_AB_PRIME_V1` : A' et B' = projections orthogonales de A et B sur Francfort ; signe positif si A est antérieur à B ;
- `Situation_A`, `Situation_B`, `Decalage_A_B`, `Profondeur_Faciale` recalculés côté backend à partir des landmarks ;
- les projections fournies par le client ne peuvent plus remplacer la géométrie backend ;
- Francfort ou axe dégénéré et calibration invalide restent `NOT_COMPUTABLE`.

### Registre normatif mergé via #391

Le registre versionne source, méthode, mesure, type de référence, unité, population, construction requise et provenance. Une référence numérique doit avoir au moins une source de recherche primaire. Les références restent **inertes** : l'activation directe pour classifier un patient est refusée.

Contexte marocain : l'étude Ousehal et al. 2012 est enregistrée comme source populationnelle sans injecter de valeurs numériques non revalidées dans le runtime.

### Graphe de preuve mergé via #392

`backend/services/cephalo_evidence_graph.py` résout les références entre objets, impose l'unicité globale des identifiants, vérifie les profils/sources normatifs et refuse les plans finaux incohérents. Le cas synthétique de bout en bout et les tests fail-closed sont présents dans `backend/tests/test_cephalo_evidence_graph.py`.

La couche active `cephalo_evidence_case_integrity.py` ajoute le verrou manquant : toutes les sources patient doivent appartenir au **même patient et au même cas explicite**, et tout diagnostic/problème/objectif accepté ou option sélectionnée doit posséder un vrai `ClinicianValidationEvidence` cohérent avec praticien, horodatage et action.

## GATES ENCORE OUVERTS

- preuve CI du durcissement patient/cas + audit praticien réel ;
- adaptateur runtime `CephaloAnalysisResult → MeasurementEvidence` ;
- convention exacte du plan mandibulaire propre à chaque analyse ;
- CRANIOM utilise pour certaines mesures `Gi/Gs`, absents comme points séparés dans SRPose38 ;
- `A''B''` exige un protocole de regard horizontal / NHP non disponible ;
- aucune référence normative n'est active pour classifier un patient.

## GATES SCIENTIFIQUES

Pour activer une mesure clinique : landmarks définis → construction versionnée → formule testée → unité/calibration explicite → source scientifique enregistrée → norme séparée → contexte de validité explicite → donnée manquante = `NOT_COMPUTABLE`.

Pour activer une interprétation/diagnostic : règle versionnée et sourcée, contradictions conservées, golden cases, puis validation praticien.

Pour activer une proposition thérapeutique : diagnostic validé + contexte clinique requis + indication sourcée + contre-indications/gates représentés. La sortie reste une option à valider, jamais une prescription autonome.

## SOUS-FICHIERS CANONIQUES

- `docs/CEPHALO_EVIDENCE_MODEL.md` — modèle de preuve transversal.
- `docs/SRPOSE38_LANDMARK_CONTRACT.md` — contrat 38 landmarks.
- `docs/CEPHALO_CONSTRUCTION_REGISTRY.md` — plans/axes/projections versionnés.
- `docs/CEPHALO_ANALYSIS_DEPENDENCY_MATRIX.md` — analyses → mesures → dépendances.
- `docs/CEPHALO_NORMATIVE_REGISTRY.md` — sources et références normatives versionnées, inertes par défaut.

## PREUVE / CI

PR #390 : merged `ce7cc5a17d0571290c0b762a553b4feaa534e026` après CI/T2 verts.  
PR #391, HEAD `a1e5e02df6f46a47b1fe2e1af34b415353c852ca` : CI `34471586594` **success**, T2 `34471586570` **success** ; merge `1c055f817e38a694de1d47f8144fcb1d9eaa2e9d`.  
PR #392, HEAD `13be2f5fbbb0e69d52d3f97341bdedd52ad044d4` : CI `34472921729` **success**, T2 `34472921733` **success** ; merge `1566f77ff5ee9d848f8e31787f92e542f16a38b7`.

## NEXT EXACT

1. certifier en CI le verrou patient/cas + audit `ClinicianValidationEvidence` ;
2. merger ce durcissement uniquement si vert ;
3. implémenter l'adaptateur runtime `CephaloAnalysisResult → MeasurementEvidence` sans activer de norme/diagnostic ;
4. poursuivre les conventions mandibulaires CRANIOM/Tweed/Downs.

## SÉQUENCE RESTANTE

`patient/case integrity → runtime evidence adapter → conventions mandibulaires → COM/CRANIOM complet → Steiner → Tweed/Merrifield → Wits/Downs → McNamara → Ricketts/soft tissue → diagnostic multiaxial → problem list/objectifs → options thérapeutiques → validation clinique → UX/PDF → closeout`

## DÉPLOIEMENT

Aucun déploiement Vercel dans ce chantier sans autorisation explicite.
