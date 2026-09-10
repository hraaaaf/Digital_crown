# DIGITAL CROWN — CÉPHALOMÉTRIE DIAGNOSTIQUE

**FICHIER CANONIQUE DE REPRISE**  
**Runtime SRPose38 :** PR #388 — `4e3ec0c84b58893d19214268075333042c4021a4`  
**Fondation diagnostique :** PR #390 — `ce7cc5a17d0571290c0b762a553b4feaa534e026`  
**Registre normatif :** PR #391 — `1c055f817e38a694de1d47f8144fcb1d9eaa2e9d`  
**Intégrité inter-objets :** PR #392 — `1566f77ff5ee9d848f8e31787f92e542f16a38b7`  
**Adaptateur MeasurementEvidence :** PR #393 — `65349a62d4b132f6bd6c2cb15f3e52b38e5d38ab`  
**Matérialisation ConstructionEvidence :** PR #394 — `c647c0843b265eadf4a70652ae4608708f48d2be`  
**PR active :** #395 — frontière patient/cas + audit praticien réel  
**Statut :** chantier actif ; aucun diagnostic ni plan thérapeutique déclaré certifié

## GOAL GLOBAL

`cas patient → image → 38 landmarks → constructions → mesures → analyses → findings → synthèse diagnostique → problem list → objectifs → options thérapeutiques → validation praticien → plan final`

## INVARIANT

`landmark != construction != measurement != interpretation != diagnosis != indication != treatment plan`

Une donnée manquante reste `UNKNOWN` / `NOT_COMPUTABLE`. Aucune norme, classe, croissance ou indication n'est devinée.

## LOTS

| Lot | Goal | État vérifié |
|---|---|---|
| 0 | Modèle de preuve clinique typé | EN COURS — schémas, registre, resolver, ConstructionEvidence et MeasurementEvidence mergés ; frontière patient/cas en #395 ; persistence/source runtime de vérité restante |
| 1 | Purger logique clinique non sourcée | FAIT — PR #371 |
| 2 | Runtime SRPose38 exact | FAIT — PR #388 |
| 3 | Contrat des 38 landmarks | EN COURS — ordre 38/38 certifié ; définitions opérationnelles partielles |
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
- 38 points intégrés et runtime CPU certifié ;
- ordre CL-Detection documenté ;
- fail-closed si asset invalide/absent.

### CRANIOM
Sources publiées enregistrées :
- Part 1 DOI `10.1051/odfen/2010406` ;
- Part 2 DOI `10.1051/odfen/2011104`.

Les références CRANIOM sont spécifiques à leur méthode/population, pas des normes universelles.

Constructions versionnées et désormais matérialisables depuis les landmarks :
- `CRANIOM_A_TO_N_VERTICAL_V1` ;
- `CRANIOM_B_TO_N_VERTICAL_V1` ;
- `CRANIOM_AB_PRIME_V1` ;
- `CRANIOM_S_TO_N_VERTICAL_DEPTH_V1`.

Les quatre mesures runtime correspondantes passent par `MeasurementEvidence` uniquement avec construction compatible et calibration explicite. Sinon elles restent `NOT_COMPUTABLE`; une valeur non finie est refusée/invalidée.

### Graphe de preuve
Le resolver mergé vérifie l'unicité globale des identifiants, l'existence/type des références, la cohérence du registre normatif et les gates du plan final. #395 ajoute la frontière absente : **toutes les SourceEvidence doivent appartenir au même patient et au même cas explicite**, les calibration refs doivent viser une source `kind="calibration"`, et tout diagnostic/problème/objectif accepté ou option sélectionnée doit être soutenu par un vrai `ClinicianValidationEvidence` cohérent.

## GATES OUVERTS

- CI exacte de #395 ;
- branchement/persistence du graphe comme source de vérité du workflow patient ;
- convention du plan mandibulaire propre à chaque analyse ;
- `Gi/Gs` CRANIOM absents comme landmarks SRPose38 distincts ;
- `A''B''` non calculable sans protocole NHP/regard horizontal ;
- aucune référence normative active pour classifier un patient.

## GATES SCIENTIFIQUES

Mesure : landmarks définis → construction versionnée → formule testée → unité/calibration → source enregistrée → norme séparée → contexte explicite → absence = `NOT_COMPUTABLE`.

Diagnostic : règle versionnée/sourcée + contradictions visibles + cas goldens + validation praticien.

Traitement : diagnostic validé + données cliniques requises + indication/contre-indications sourcées + sélection praticien. Jamais de prescription autonome.

## PREUVES CI

- PR #391 HEAD `a1e5e02df6f46a47b1fe2e1af34b415353c852ca` : CI `34471586594` success ; T2 `34471586570` success.
- PR #392 HEAD `13be2f5fbbb0e69d52d3f97341bdedd52ad044d4` : CI `34472921729` success ; T2 `34472921733` success.
- PR #393 HEAD `9739b305a0e98d8a2149d341ee035b4856d3c6ec` : CI `34474219020` success ; T2 `34474219021` success.
- PR #394 HEAD `ef82e6bdded2168f99d6c475b1b5fbf891e3adaf` : CI `34474296352` success ; T2 `34474296300` success.

## NEXT EXACT

1. certifier #395 sur master `c647c0843b265eadf4a70652ae4608708f48d2be` ;
2. si vert et sans review/thread bloquant : merger #395 ;
3. rechercher les PR céphalo déjà ouvertes avant tout nouveau développement ;
4. connecter ensuite la chaîne `Source/Landmark → ConstructionEvidence → MeasurementEvidence` au workflow patient, sans activer diagnostic/normes ;
5. poursuivre les conventions mandibulaires CRANIOM/Tweed/Downs.

## SÉQUENCE RESTANTE

`patient/case integrity → persistence/source-of-truth patient → conventions mandibulaires → COM/CRANIOM complet → Steiner → Tweed/Merrifield → Wits/Downs → McNamara → Ricketts/soft tissue → diagnostic multiaxial → problem list/objectifs → options → validation clinique → UX/PDF → closeout`

## DÉPLOIEMENT

Aucun déploiement Vercel sans autorisation explicite.
