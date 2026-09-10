# DIGITAL CROWN — CÉPHALOMÉTRIE DIAGNOSTIQUE

**FICHIER CANONIQUE DE REPRISE**  
**Baseline runtime :** SRPose38 merged via PR #388 — `4e3ec0c84b58893d19214268075333042c4021a4`  
**PR chantier :** #390 — `feat/cephalo-diagnostic-spec`  
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
| 0 | Modèle de preuve | objets typés + `evidence_refs` + tests de contrat | SPEC FAITE ; code à faire |
| 1 | Purger logique clinique non sourcée | moteur géométrique sans diagnostic/traitement implicite | FAIT — PR #371 |
| 2 | Runtime SRPose38 exact | 38/38, pipeline ONNX parity certifié, fail-closed asset | FAIT — PR #388 |
| 3 | Contrat des 38 landmarks | ordre, noms, alias et définitions opérationnelles certifiés | EN COURS — ordre 38/38 certifié ; COM critique partiel |
| 4 | Constructions géométriques | plans/axes/projections versionnés + golden tests | EN COURS — CRANIOM A'B'/N-vertical implémentés en fonctions pures |
| 5 | COM / CRANIOM | mesures de la méthode calculables + références spécifiques sourcées séparément | EN COURS — méthode/source identifiées ; normes inactives |
| 6 | Steiner | matrice dépendances + formules + normes sourcées | À FAIRE |
| 7 | Tweed/Merrifield | idem | À FAIRE |
| 8 | Wits/Jacobson + Downs | idem | À FAIRE |
| 9 | McNamara | idem | À FAIRE |
| 10 | Ricketts + tissus mous | idem | À FAIRE |
| 11 | Registre normatif | contexte âge/sexe/population/source/version + fail-closed | À FAIRE |
| 12 | Synthèse diagnostique | règles déterministes explicables, contradictions visibles | À FAIRE |
| 13 | Indications / plan thérapeutique | options sourcées, jamais prescription autonome | À FAIRE |
| 14 | Validation clinique + UX/PDF | cas goldens praticien, traçabilité, BEFORE/AFTER UI | À FAIRE |

## ACQUIS SCIENTIFIQUES DU CHANTIER

### SRPose38

- modèle 38 points intégré et certifié runtime sur CPU ;
- ordre CL-Detection 1..38 ↔ runtime 0..37 documenté ;
- ambiguïtés anatomiques conservées explicitement au lieu d'être devinées.

### Méthode historique COM

Le flux historique Digital Crown appelé `COM` a été rapproché de la méthode **C.R.A.N.I.O.M.** de Bonnefont, Casteigt, Ernoult et Sorel.

Source publiée : *A new method for the utilization of cephalometric measurements in orthodontics... (Part 1)*, Journal of Dentofacial Anomalies and Orthodontics, 2010;13(4):385-400, DOI `10.1051/odfen/2010406`.

Décision produit : le label `COM` peut rester transitoirement pour compatibilité UX, mais le registre scientifique doit identifier la méthode source comme `CRANIOM` et ne pas la confondre avec Tweed/Steiner/Downs/Ricketts.

### A'B' CRANIOM

A' et B' sont les projections orthogonales de A et B sur Francfort. La distance algébrique est positive si A est en avant de B.

Construction versionnée : `CRANIOM_AB_PRIME_V1`.

### Gates encore ouverts

- convention exacte du plan mandibulaire propre à chaque analyse ;
- CRANIOM utilise pour certaines mesures `Gi/Gs`, absents comme points séparés dans SRPose38 ;
- `A''B''` exige un protocole de regard horizontal / photo NHP qui n'existe pas encore ;
- aucune référence normative n'est activée tant que Lot 11 n'est pas implémenté.

## GATES SCIENTIFIQUES

Pour activer une mesure clinique :
1. landmarks définis et disponibles ;
2. construction géométrique versionnée ;
3. formule testée ;
4. unité/calibration explicite ;
5. source scientifique enregistrée ;
6. norme séparée de la mesure brute ;
7. contexte de validité explicite ;
8. cas manquant → `NOT_COMPUTABLE`.

Pour activer une interprétation/diagnostic :
- toutes les dépendances ci-dessus ;
- règle versionnée et sourcée ;
- aucune résolution silencieuse des contradictions entre analyses ;
- preuve par golden cases ;
- validation praticien pour toute conclusion retenue.

Pour activer une proposition thérapeutique :
- diagnostic nécessaire disponible et validé ;
- contexte clinique nécessaire disponible ;
- règle d'indication sourcée ;
- contre-indications/gates représentés ;
- sortie = option à valider par praticien, jamais décision autonome.

## SOUS-FICHIERS CANONIQUES

- `docs/CEPHALO_EVIDENCE_MODEL.md` — modèle de preuve transversal.
- `docs/SRPOSE38_LANDMARK_CONTRACT.md` — contrat 38 landmarks.
- `docs/CEPHALO_CONSTRUCTION_REGISTRY.md` — plans/axes/projections versionnés.
- `docs/CEPHALO_ANALYSIS_DEPENDENCY_MATRIX.md` — analyses → mesures → dépendances.

## NEXT EXACT

Lot 4 : faire passer les golden tests CRANIOM et brancher le moteur courant sur les constructions versionnées sans changement numérique ; puis certifier le plan mandibulaire analyse par analyse avant d'étendre les mesures.

## SÉQUENCE RESTANTE

`Lot 4 wiring/tests → Lot 3 landmarks restants selon besoin → CRANIOM geometry complet → registre normatif → Steiner → Tweed/Merrifield → Wits/Downs → McNamara → Ricketts/soft tissue → diagnostic multiaxial → problem list/objectifs → options thérapeutiques → validation clinique → UX/PDF → closeout`

## DÉPLOIEMENT

Aucun déploiement Vercel dans ce chantier sans autorisation explicite.
