# HANDOVER — DIGITAL CROWN / CÉPHALOMÉTRIE — R14 → R15

**Date :** 2026-09-12  
**Repo :** `hraaaaf/Digital_crown`  
**Canonique :** `docs/CEPHALO_DIAGNOSTIC_SPEC.md`

## GOAL R14 ATTEINT ET PROUVÉ

`objets R13 valides → stratégie clinique finale structurée → validation/rejet praticien final audité`, sans choix thérapeutique autonome.

## ÉTAT VÉRIFIÉ

- branche implémentation : `feat/cephalo-r14-final-clinical-validation` ;
- candidate HEAD certifié : `017a7eaf7d293c5a7af19fb44987a2d5ff3f675c` ;
- CI #3581 : SUCCESS ;
- T2 Runtime Browser Certification #2536 : SUCCESS ;
- Cabinet Upgrade PostgreSQL Certification #51 : SUCCESS ;
- PR #447 : MERGED ;
- merge implementation : `2f1f1d88bf6027988a398967bed5e65883b729aa` ;
- master post-merge implementation vérifié : `2f1f1d88bf6027988a398967bed5e65883b729aa` ;
- reviews : 0 ; threads : 0 ; commentaires PR : 0 ;
- UI : aucune modification R14 ;
- déploiement : aucun.

## CONTRAT R14 À NE PAS CASSER

- contrat versionné `R14_FINAL_CLINICAL_VALIDATION_V1` ;
- R14 réexécute le validateur R13, donc la chaîne R13 → R12 → R11 reste autoritaire ;
- provenance exacte obligatoire vers options R13, validations de décision, critères/sources, objectifs, problèmes, diagnostics, findings, evidence, missing data et contradictions ;
- `EVALUABLE` ne devient jamais un plan : il crée `clinician_selection_required` et reste bloquant ;
- les options R13 `BLOCKED` ou `CLINICIAN_REJECTED` restent bloquantes ;
- missing data, contradictions et gates sont conservés exactement et bloquent la finalisation ;
- seule une option R13 `CLINICIAN_SELECTED` peut participer à une stratégie R14 non bloquée ;
- `AWAITING_CLINICIAN_VALIDATION` est non final ;
- `CLINICIAN_VALIDATED` / `CLINICIAN_REJECTED` exigent une `ClinicianValidationEvidence` résolue sur la stratégie exacte avec cible, action, clinicien et timestamp cohérents ;
- toute validation finale orpheline ou fabriquée est refusée ;
- les champs libres de stratégie thérapeutique, séquençage ou détails de plan sont interdits à cette couche ;
- aucune nouvelle règle, norme, source ou option thérapeutique clinique réelle n'a été activée ;
- le registre thérapeutique production reste vide par défaut ;
- `BLOCKED != DROPPED` reste obligatoire.

## FICHIERS R14

- `backend/schemas/cephalo_r14_final_validation.py`
- `backend/services/cephalo_r14_final_validation_safety.py`
- `backend/tests/test_cephalo_r14_final_validation_safety.py`

## GOLDENS / REFUS R14

- final validé positif avec option R13 sélectionnée et validation finale exacte ;
- aucune auto-promotion depuis `EVALUABLE` ;
- représentation `BLOCKED` explicite avec `clinician_selection_required` ;
- missing data et gates R13 conservés ;
- contradiction propagée et bloquante ;
- suppression silencieuse de missing data refusée ;
- altération de provenance finding refusée ;
- perte de provenance de validation de décision R13 refusée ;
- validation finale non résolue, mauvaise cible ou orpheline refusée ;
- audit R13 amont invalide refusé par réexécution ;
- champs libres de stratégie/séquençage refusés ;
- timestamp final naïf/non timezone-aware refusé.

## DETTE PRÉEXISTANTE À CONNAÎTRE

`.github/workflows/document-history-actions-visual-cert.yml` était déjà corrompu sur master avant R14 et pouvait produire un workflow visuel sans jobs. R14 ne l'a pas modifié. R15 étant visuel, cette dette doit être évaluée dans son propre scope avant de compter ce workflow comme preuve.

## FRONTIÈRE R15

R15 = **Studio clinique UX/UI Digital Crown**. Il doit rendre les états scientifiques R11/R12/R13/R14 compréhensibles et actionnables sans inventer, masquer ou auto-sélectionner du contenu clinique.

Cycle visuel obligatoire pour tout changement :
`BEFORE réel → Goal écrit → référence/mockup → tokens → implémentation → AFTER mêmes viewports 390/768/1280+ → comparaison → tests → score visuel/revue`.

La validation praticien visible dans l'UI doit produire une vraie preuve traçable conforme aux contrats backend. Une simulation d'action humaine n'est jamais une validation clinique.

Ne pas démarrer R16 dans la fenêtre R15.

## REPRISE OBLIGATOIRE R15

1. `AGENTS.md`
2. `STATE.md`
3. `docs/CEPHALO_DIAGNOSTIC_SPEC.md`
4. `docs/CEPHALO_MEASUREMENT_EVIDENCE_RECOVERY.md`
5. ce handover R14→R15
6. vérifier repo/master/HEAD/PR/CI avant toute modification

## NEXT EXACT

Après merge et vérification du closeout documentaire R14, ouvrir une nouvelle fenêtre exclusivement R15 et commencer par l'audit BEFORE du studio clinique existant, sans modifier l'UI avant Goal + référence/mockup.

## SÉQUENCE RESTANTE

`R15 studio UX/UI → R16 PDF/restitution → R17 certification/closeout`

## DÉPLOIEMENT

Aucun déploiement Vercel sans autorisation explicite.