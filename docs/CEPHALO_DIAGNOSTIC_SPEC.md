# DIGITAL CROWN — CÉPHALOMÉTRIE DIAGNOSTIQUE

**FICHIER CANONIQUE DE REPRISE**

## POINTEUR COURANT

- **R18 : FERMÉ ET MERGÉ.**
- **Repo :** `hraaaaf/Digital_crown`.
- **PR R18 :** #494 — MERGED.
- **Candidate produit certifié :** `39660fa45471dbcd8c773148172ec03a854c931f`.
- **HEAD closeout pré-merge certifié :** `172c4d230d8a0baa3b3692dcf7ae0c8721ff3b16`.
- **Merge master réel :** `71a087391d175ffe6f3a9e4e7962c833bab23fa5`.
- **Handover R18 → R19 :** `docs/handovers/2026-09-14-cephalo-r18-final-handover.md`.
- **Closeout post-merge :** `docs/handovers/2026-09-14-cephalo-r18-post-merge-closeout.md`.
- **Détail scientifique R18 :** `docs/CEPHALO_R18_SCIENTIFIC_CONCORDANCE.md`.
- **Audit scientifique/UX :** `docs/audits/CEPHALO_R18_SOURCE_STRICT_TRACING.md`.
- **Archive canonique pré-R18 :** `docs/archive/CEPHALO_DIAGNOSTIC_SPEC_PRE_R18.md`.

## GOAL GLOBAL

`cas patient → image → landmarks → constructions → mesures → analyses → findings → synthèse diagnostique → problem list → objectifs → options thérapeutiques → validation praticien → plan final`

## INVARIANTS NON NÉGOCIABLES

`landmark != construction != measurement != interpretation != diagnosis != indication != treatment plan`

- donnée absente ou géométrie non calculable → `UNKNOWN` / `NOT_COMPUTABLE`, jamais faux `0` ;
- mesure, norme et interprétation restent séparées ;
- `EVALUABLE != selected` ;
- `BLOCKED != DROPPED` ;
- validation finale R14 uniquement avec preuve praticien autoritaire ;
- aucune norme, classe, diagnostic, indication ou traitement n'est inventé ;
- toute migration scientifique garde version/provenance explicites.

## R18 — CONTRAT FERMÉ

### Goal

Aligner strictement :

`convention scientifique versionnée → backend production → frontend clinique → construction graphique → audit reproductible`.

### Décisions certifiées

- géométrie rayons/axes robuste par produit scalaire + `acos`, fail-closed sur dégénérescence ;
- Steiner U1/NA et L1/NB restent des angles d'axes ; les linéaires U1-NA/L1-NB ne sont pas fabriqués sans landmark coronaire requis ;
- conventions CRANIOM explicitement obtuses conservent leur supplément clinique ;
- Ricketts E-line V1 reste lisible ; V2 utilise la distance perpendiculaire la plus courte à Prn-Pog', Frankfort orientant uniquement le signe ;
- aucun snapshot V1 n'est réécrit silencieusement ;
- le viewer expose `Tous / Steiner / Tweed / McNamara-COM / Ricketts` avec constructions filtrées par analyse ;
- au viewport mobile 390, `McNamara / COM` devient visuellement `COM` pour conserver les cinq choix visibles sans modifier la sémantique.

### Preuves finales

Sur le HEAD documentaire exact `172c4d230d8a0baa3b3692dcf7ae0c8721ff3b16` :

- CI #4106 : **SUCCESS** ;
- T2 Runtime Browser Certification #3017 : **SUCCESS** ;
- PostgreSQL Certification #532 : **SUCCESS** ;
- R18 Scientific Concordance #20 : **SUCCESS** ;
- R18 Tracing AFTER #8 : **SUCCESS** ;
- R15 AFTER #87 : **SUCCESS** ;
- R15bis AFTER #48 : **SUCCESS** ;
- M6-I #1817 : SKIPPED, attendu pour ce scope.

Preuve scientifique : `concordance_certified=true`, zéro divergence.

Preuve visuelle : BEFORE figé 390/768/1280 ; AFTER mêmes viewports, 15/15 états valides, `invalidCount=0`, zéro erreur page/console, zéro overflow horizontal. Score visuel/HFE final : **9,4/10**.

PR #494 était mergeable, sans commentaire bloquant, puis a été mergée avec HEAD attendu. `master` a été vérifié exactement sur `71a087391d175ffe6f3a9e4e7962c833bab23fa5` après merge.

## PROTOCOLE R / FENÊTRES

- 1 fenêtre active = 1 numéro R distinct ;
- chaque R garde scope, état, preuves, handover final et prompt du R suivant ;
- aucune feature n'est inventée pour remplir la numérotation ;
- reprise : `AGENTS.md → STATE.md → ce canonical → handover courant → vérifier master/HEAD/PR/CI → agir`.

## R19 — PROCHAINE FENÊTRE PROCÉDURALE

Aucune nouvelle feature céphalométrique n'est pré-planifiée.

R19 doit :
1. lire ce canonical et le handover R18 final ;
2. vérifier `master` courant et la présence du merge R18 `71a087391d175ffe6f3a9e4e7962c833bab23fa5` dans son historique ;
3. ne rouvrir R18 qu'en présence d'une régression prouvée ;
4. démarrer un nouveau chantier uniquement depuis une instruction utilisateur ou une source canonique explicite.

## DÉPLOIEMENT

Aucun déploiement Vercel effectué ni autorisé dans R18.

## NEXT EXACT

Aucune action produit R18 restante. La prochaine action est la reprise R19 uniquement lorsqu'un nouveau chantier réel est défini.
