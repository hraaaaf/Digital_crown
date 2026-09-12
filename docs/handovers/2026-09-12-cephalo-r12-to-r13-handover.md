# HANDOVER — CÉPHALOMÉTRIE — R12 → R13

Date : 2026-09-12  
Repo : `hraaaaf/Digital_crown`

## R12 — ÉTAT

**R12 Problem list + objectifs : FERMÉ côté implémentation.**

Goal R12 : `diagnostics validés → problem list traçable → objectifs traçables`, avec missing data et contradictions visibles, sans fuite thérapeutique.

### Preuves certifiées

- branche implémentation : `feat/cephalo-r12-problem-list-objectives`
- candidate HEAD : `dc04d759191828afe85c643719165e7d4fcc916e`
- CI : #3500 — SUCCESS
- T2 Runtime Browser Certification : #2465 — SUCCESS
- PR implémentation : #441
- scope PR : 1 commit, 3 fichiers ajoutés, backend R12 uniquement
- reviews : 0
- threads : 0
- commentaires PR : 0
- merge implementation : `02d4be759e4ddbc24293340c6c10848174ace07a`
- master post-merge implementation vérifié : `02d4be759e4ddbc24293340c6c10848174ace07a`
- UI : aucune modification
- déploiement : aucun

## CONTRAT R12 FERMÉ

Chaîne autorisée :

`measurement evidence → contexte normatif optionnel → finding validé → diagnostic validé → problem-list item → objectif → R13 ultérieur`

Invariant :

`landmark != construction != measurement != interpretation != diagnosis != indication != treatment plan`

Décisions fermées :
- contrats R12 dédiés et versionnés : `R12_PROBLEM_LIST_V1`, `R12_OBJECTIVE_V1` ;
- un problème ne dérive que de diagnostics `ACCEPTED` / `EDITED` ;
- les `finding_refs` d'un problème correspondent exactement aux findings supporting/opposing des diagnostics sélectionnés ;
- chaque finding utilisé est `AVAILABLE` et possède une validation praticien explicite dont la dernière action est `ACCEPT` ou `EDIT` ;
- `missing_data_refs`, contradictions et `evidence_refs` sont propagés exactement ;
- aucun missing/contradiction ne peut disparaître silencieusement ;
- un objectif ne dérive que de problèmes R12 `ACCEPTED` / `EDITED` ;
- la provenance objective → problems → diagnoses → findings reste explicite et exacte ;
- le validateur R12 réexécute le contrat R11 avant ses propres gates ;
- aucune hypothèse non validée ne devient automatiquement problème confirmé ;
- `treatment_options` et `final_plans` sont explicitement refusés dans le snapshot R12 ;
- aucune indication, contre-indication, option thérapeutique, mécanique, appareil ou prescription n'a été introduit en R12 ;
- aucune nouvelle règle clinique, norme, constante ou valeur médicale n'a été activée ;
- aucune validation scientifique clinique humaine n'est revendiquée par les tests/CI.

## GOLDENS R12

- positif : provenance validée complète ;
- négatif : diagnostic non validé → refus ;
- négatif : finding non validé → refus ;
- missing data : propagation exacte problème + objectif ;
- contradiction : propagation exacte ;
- problème non validé → objectif refusé ;
- fuite de couche thérapeutique → refus ;
- champ thérapeutique additionnel dans contrat R12 → refus.

## RÈGLE NO-DROP — AUCUNE MESURE ABANDONNÉE

Autorité : `docs/CEPHALO_MEASUREMENT_EVIDENCE_RECOVERY.md`.

**Une mesure bloquée n'est jamais supprimée.** Elle reste une dette scientifique active avec raison du blocage et chemin de récupération.

`BLOCKED != DROPPED`

Les statuts `CONVENTIONAL_REFERENCE_ONLY`, `HISTORICAL_ONLY_BLOCKED`, `DIVERGENT_BLOCKED` et `CONSTRUCTION_BLOCKED` restent non activables tant que la preuve correspondante manque. McNamara reste inert/scale-blocked. Les références non verrouillées ne doivent pas être transformées en norme patient ou en règle thérapeutique dans R13.

## FICHIERS CLÉS R12

- `backend/schemas/cephalo_r12_problem_objectives.py`
- `backend/services/cephalo_r12_problem_objectives_safety.py`
- `backend/tests/test_cephalo_r12_problem_objectives_safety.py`
- `backend/schemas/cephalo_evidence.py`
- `backend/services/cephalo_r11_diagnostic_safety.py`
- `backend/services/cephalo_diagnostic_rule_registry.py`
- `docs/CEPHALO_DIAGNOSTIC_SPEC.md`
- `docs/CEPHALO_MEASUREMENT_EVIDENCE_RECOVERY.md`

## NEXT EXACT — R13

R13 seulement, dans une nouvelle fenêtre.

Goal canonique R13 : **Options thérapeutiques**.

Contrat cible minimum : les options sont évaluables mais jamais des prescriptions autonomes ; toute indication/contre-indication est sourcée et versionnée ; chaque option dérive d'objectifs R12 validés avec provenance explicite ; les données manquantes et contradictions restent fail-closed ; la sélection reste praticien ; aucun plan final R14 n'est produit automatiquement.

Avant modification :
1. lire `AGENTS.md` ;
2. lire `STATE.md` ;
3. lire `docs/CEPHALO_DIAGNOSTIC_SPEC.md` ;
4. lire `docs/CEPHALO_MEASUREMENT_EVIDENCE_RECOVERY.md` ;
5. lire ce handover ;
6. vérifier master/HEAD/PR/CI réels ;
7. créer une branche R13 depuis master final vérifié.

## PROMPT EXACT À COLLER DANS LA NOUVELLE FENÊTRE R13

```text
MISSION — DIGITAL CROWN / CÉPHALOMÉTRIE — R13 OPTIONS THÉRAPEUTIQUES

Tu reprends le chantier Céphalométrie de Digital Crown.

RÈGLE DE CONTINUITÉ
Cette fenêtre est exclusivement consacrée à R13.
Ne démarre pas R14 ici.
À la fermeture de R13, tu dois obligatoirement :
1. certifier le lot ;
2. merger si toutes les preuves sont acquises ;
3. vérifier master post-merge ;
4. mettre à jour le fichier canonique ;
5. créer un handover compact dans docs/handovers/ pour R14 ;
6. me fournir le prompt exact à coller dans une nouvelle fenêtre pour R14.

REPO
hraaaaf/Digital_crown

REPRISE OBLIGATOIRE
Lis dans cet ordre :
1. AGENTS.md
2. STATE.md
3. docs/CEPHALO_DIAGNOSTIC_SPEC.md
4. docs/CEPHALO_MEASUREMENT_EVIDENCE_RECOVERY.md
5. docs/handovers/2026-09-12-cephalo-r12-to-r13-handover.md
Puis vérifie repo/master/HEAD/PR/CI avant toute modification.

ÉTAT VÉRIFIÉ R12
- R12 implementation candidate : dc04d759191828afe85c643719165e7d4fcc916e
- CI #3500 : SUCCESS
- T2 #2465 : SUCCESS
- PR #441 : merged
- merge implementation : 02d4be759e4ddbc24293340c6c10848174ace07a
- master post-merge implementation vérifié : 02d4be759e4ddbc24293340c6c10848174ace07a
- aucun déploiement

CONTRAT R12 À NE PAS CASSER
- measurement evidence → normative context optionnel → finding validé → diagnostic validé → problem-list item → objectif → options R13 ultérieures
- landmark != construction != measurement != interpretation != diagnosis != indication != treatment plan
- production diagnostic rule registry reste vide tant qu'une règle n'est pas source-lockée/revue
- un problème R12 ne dérive que de diagnostics ACCEPTED/EDITED
- chaque finding utilisé par un problème est AVAILABLE et explicitement validé praticien ; dernière action ACCEPT/EDIT
- provenance problem → diagnostics/findings exacte
- missing data et contradictions propagées exactement
- un objectif ne dérive que de problèmes R12 ACCEPTED/EDITED
- provenance objective → problems → diagnoses → findings exacte
- aucune transformation automatique d'une hypothèse/problème non validé en décision thérapeutique
- R12 n'a introduit aucune indication, contre-indication, option ou plan thérapeutique

RÈGLE NO-DROP MESURES
- aucune mesure n'est abandonnée ;
- BLOCKED signifie dette scientifique active, jamais suppression ;
- si une preuve manque, la rechercher ; si une construction manque, la verrouiller ;
- ne jamais remplacer une preuve absente par une approximation silencieuse ;
- conserver chaque mesure et son état jusqu'à résolution ;
- lire et respecter docs/CEPHALO_MEASUREMENT_EVIDENCE_RECOVERY.md.

R13 — GOAL CANONIQUE
Options thérapeutiques.
Options évaluables, jamais prescription autonome ; indications/contre-indications sourcées et sélection praticien.

SUCCESS R13
- schéma explicite et versionné pour indications, contre-indications et options thérapeutiques ;
- provenance exacte option → objectifs R12 validés → problèmes → diagnostics/findings ;
- aucune option ne dérive d'un objectif/problème/diagnostic/finding non validé ou indisponible ;
- indications/contre-indications portent source, version, contexte et règle explicites ; aucune règle thérapeutique implicite ;
- registre production thérapeutique fail-closed : aucune règle/option clinique active sans source-lock + revue appropriée ;
- missing data, contradictions et gates non satisfaits restent visibles et bloquent l'évaluation/sélection quand requis ;
- aucune contre-indication n'est supprimée ou neutralisée silencieusement ;
- aucune prescription ou sélection automatique : la sélection reste praticien et auditée ;
- aucun plan final, séquençage thérapeutique, mécanique/appareil imposé ou validation clinique finale R14 en R13 ;
- aucune mesure existante supprimée pour insuffisance de preuve : recherche/queue scientifique obligatoire ;
- goldens positif / négatif / missing / contradiction / contre-indication / upstream non validé ;
- invariants inter-objets ;
- exact-head CI verte + T2 verte ;
- review/thread audit propre ;
- diff scope propre ;
- canonical mis à jour ;
- PR mergée ;
- master post-merge vérifié ;
- handover R14 écrit.

AUTONOMIE
Avance sans demander validation tant qu'aucun vrai human gate n'est rencontré. Une validation clinique humaine ne doit jamais être simulée. Corrige puis recertifie si CI rouge. Ne déploie pas sur Vercel sans autorisation explicite.

UI/UX
R13 n'est pas un lot visuel par défaut. Si tu modifies une UI : BEFORE → Goal écrit → mockup/référence → implémentation → AFTER mêmes viewports 390/768/1280+ → comparaison/tests → score visuel.

CLOSEOUT
Ne conclus pas tant que toute action connue et autorisée n'est pas exécutée : certification → merge → master post-merge → canonical → handover R14 → closeout final.

COMMUNICATION
Résultat → preuve → prochaine action.
À chaque message de travail, affiche les REPÈRES connus sans inventer de % ni de preuve.
```

## SÉQUENCE RESTANTE APRÈS R12

`R13 options thérapeutiques → R14 validation clinique → R15 studio UX/UI → R16 PDF → R17 certification/closeout`
