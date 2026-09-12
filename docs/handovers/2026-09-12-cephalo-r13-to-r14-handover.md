# HANDOVER — DIGITAL CROWN / CÉPHALOMÉTRIE — R13 → R14

Date : 2026-09-12  
Repo : `hraaaaf/Digital_crown`  
Fichier canonique : `docs/CEPHALO_DIAGNOSTIC_SPEC.md`

## Goal R13 — atteint et prouvé

Options thérapeutiques évaluables, jamais prescription autonome ; indications/contre-indications sourcées et sélection/rejet praticien audités.

## État vérifié

- candidate R13 : `7fd6fdae604010510b74e5fe908dc76a425a71cf`
- CI #3526 : SUCCESS
- T2 Runtime Browser Certification #2489 : SUCCESS
- PR #444 : MERGED
- merge implementation : `4740b463e49f8ddee9dbb704faaecd086c389beb`
- master post-merge implementation vérifié : `4740b463e49f8ddee9dbb704faaecd086c389beb`
- aucun déploiement
- UI : aucune modification
- review audit avant merge : reviews 0 ; threads 0 ; commentaires PR 0

## Contrat R13 à ne pas casser

- versions : `R13_INDICATION_V1`, `R13_CONTRAINDICATION_V1`, `R13_TREATMENT_OPTION_V1` ;
- chaîne : `objectifs R12 validés → critères thérapeutiques sourcés/versionnés → option évaluée → décision praticien auditée` ;
- le validateur R13 réexécute R12 avant toute évaluation ;
- provenance exacte option → objectifs → problèmes → diagnostics/findings ;
- aucune option ne dérive d'un objectif amont non validé ;
- missing data et contradictions restent visibles et bloquent lorsque requis ;
- toute indication non satisfaite ou contre-indication non levée produit un blocking gate explicite ;
- une contre-indication n'est jamais supprimée/neutralisée silencieusement ;
- `EVALUABLE` n'est jamais synonyme de prescription ou choix ;
- `CLINICIAN_SELECTED` / `CLINICIAN_REJECTED` exigent une `ClinicianValidationEvidence` cohérente cible/action/clinicien/timestamp ;
- registre thérapeutique production vide par défaut : aucune règle/option clinique active sans source-lock + revue ;
- contexte source immuable après enregistrement et revue timezone-aware obligatoire ;
- contexte critère/option doit être compatible avec les valeurs d'applicabilité de chaque source ;
- aucune mécanique, appareil, séquençage ou plan final n'est construit en R13 ;
- `BLOCKED != DROPPED` ; aucune mesure existante n'est abandonnée.

## Frontière R14

R14 = validation clinique finale.

Goal canonique : construire une synthèse/stratégie finale uniquement à partir d'objets R13 valides, avec validation praticien traçable obligatoire avant tout état final. R14 ne doit jamais convertir automatiquement une option `EVALUABLE` en plan, ni contourner les blocking gates R13.

R14 ne doit pas démarrer R15 ni faire une refonte UX/UI. Toute modification visuelle réellement nécessaire suit le cycle BEFORE → Goal → référence/mockup → implémentation → AFTER 390/768/1280+ → comparaison/tests → score.

## Reprise obligatoire R14

Lire dans cet ordre :
1. `AGENTS.md`
2. `STATE.md`
3. `docs/CEPHALO_DIAGNOSTIC_SPEC.md`
4. `docs/CEPHALO_MEASUREMENT_EVIDENCE_RECOVERY.md`
5. `docs/handovers/2026-09-12-cephalo-r13-to-r14-handover.md`
6. vérifier repo/master/HEAD/PR/CI avant toute modification.

## Next exact

Ouvrir une nouvelle fenêtre exclusivement R14, relire les sources ci-dessus, vérifier le master final du closeout R13, puis définir/implémenter uniquement le contrat de validation clinique finale sans démarrer R15.

## Séquence restante

`R14 validation clinique finale → R15 studio UX/UI → R16 PDF/restitution → R17 certification/closeout`

## Blocage réel

Aucun blocage R13 connu. Une validation clinique humaine ne doit jamais être simulée.

## Déploiement

Aucun déploiement Vercel sans autorisation explicite.
