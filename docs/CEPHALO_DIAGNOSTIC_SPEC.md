# DIGITAL CROWN — CÉPHALOMÉTRIE DIAGNOSTIQUE

**FICHIER CANONIQUE DE REPRISE**  
**Baseline runtime :** SRPose38 merged via PR #388  
**Statut :** chantier actif, aucun diagnostic/plan thérapeutique déclaré certifié

## GOAL GLOBAL

Construire un workflow céphalométrique local, déterministe et traçable :

`cas patient → image → 38 landmarks → constructions → mesures → analyses → synthèse diagnostique → indications → proposition thérapeutique → validation praticien`

## INVARIANT DE SÉCURITÉ

`landmark != construction != measurement != interpretation != diagnosis != indication != treatment plan`

Une donnée manquante reste `UNKNOWN` / `NOT_COMPUTABLE`. Aucune valeur, norme, classe, croissance ou indication n'est devinée.

## LOTS

| Lot | Goal | Succès observable | État |
|---|---|---|---|
| 1 | Purger logique clinique non sourcée | moteur géométrique sans diagnostic/traitement implicite | FAIT — PR #371 |
| 2 | Runtime SRPose38 exact | 38/38, pipeline ONNX parity certifié, fail-closed asset | FAIT — PR #388 |
| 3 | Contrat des 38 landmarks | ordre, noms, alias et définitions opérationnelles certifiés | EN COURS |
| 4 | Constructions géométriques | plans/axes/projections versionnés + golden tests | À FAIRE |
| 5 | COM | mesures COM calculables + normes sourcées séparément | EN COURS |
| 6 | Steiner | matrice dépendances + formules + normes sourcées | À FAIRE |
| 7 | Tweed/Merrifield | idem | À FAIRE |
| 8 | Wits/Jacobson + Downs | idem | À FAIRE |
| 9 | McNamara | idem | À FAIRE |
| 10 | Ricketts + tissus mous | idem | À FAIRE |
| 11 | Registre normatif | contexte âge/sexe/population/source/version + fail-closed | À FAIRE |
| 12 | Synthèse diagnostique | règles déterministes explicables, contradictions visibles | À FAIRE |
| 13 | Indications / plan thérapeutique | propositions sourcées, jamais prescriptions automatiques | À FAIRE |
| 14 | Validation clinique + UX/PDF | cas goldens praticien, traçabilité, BEFORE/AFTER UI | À FAIRE |

## GATES SCIENTIFIQUES

Pour activer une mesure clinique :
1. landmarks définis et disponibles ;
2. construction géométrique définie ;
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
- preuve par golden cases.

Pour activer une proposition thérapeutique :
- diagnostic nécessaire disponible ;
- contexte clinique nécessaire disponible ;
- règle d'indication sourcée ;
- contre-indications/gates représentés ;
- sortie = proposition à valider par praticien, jamais décision autonome.

## SOUS-FICHIERS CANONIQUES

- `docs/SRPOSE38_LANDMARK_CONTRACT.md` — contrat 38 landmarks.
- `docs/CEPHALO_ANALYSIS_DEPENDENCY_MATRIX.md` — analyses → mesures → dépendances.

## NEXT EXACT

Lot 3 : compléter les définitions opérationnelles sourcées des landmarks requis par COM, puis Lot 4 : matérialiser les constructions géométriques COM avec golden tests avant toute réactivation normative.

## SÉQUENCE RESTANTE

`Landmarks → constructions → COM geometry → COM sources/norms → Steiner → Tweed/Merrifield → Wits/Downs → McNamara → Ricketts/soft tissue → registre normatif → synthèse diagnostic → indications → validation clinique → UX/PDF → closeout`

## DÉPLOIEMENT

Aucun déploiement Vercel dans ce chantier sans autorisation explicite.
