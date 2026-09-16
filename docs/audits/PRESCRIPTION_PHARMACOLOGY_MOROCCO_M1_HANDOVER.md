# Digital Crown — Pharmacologie Maroc M1 handover

Date: 2026-09-16
Status: ACTIVE — no clinical activation

## Goal global
Construire une couverture pharmacologique dentaire exhaustive et systématiquement sourcée Maroc, avec séparation stricte entre preuve réglementaire, indication, dose et activation clinique.

## Invariants
- Digital Crown reste local/on-premise; aucun déploiement de l'application clinique ni de ses données sur Vercel.
- Préserver DB, données patients, documents et fonctionnalités validées.
- Aucun `AUTO_OK` ni activation clinique sans preuve Maroc suffisante et revue humaine/scientifique requise.
- Recherche négative != preuve d'absence.
- CI verte != validation scientifique/clinique.
- Le reviewer scientifique doit être indépendant de l'auteur et read-only.
- Aucun merge sans accord utilisateur explicite.

## À lire au démarrage
1. `docs/audits/PRESCRIPTION_PHARMACOLOGY_MOROCCO_COVERAGE.md`
2. `docs/audits/PRESCRIPTION_PHARMACOLOGY_MOROCCO_RCP_M1.md`
3. `docs/audits/PRESCRIPTION_PHARMACOLOGY_MOROCCO_RCP_WAVE1_QUEUE.json`
4. `docs/audits/PRESCRIPTION_PHARMACOLOGY_SCIENTIFIC_GATE.md`
5. `.claude/rules/scientific-engineering.md`
6. `.claude/agents/scientific-reviewer.md`
7. `.claude/skills/review-scientific-pull-request/SKILL.md`
8. `.claude/skills/scientific-source-research/SKILL.md`

## Lots déjà fermés
- M1-A PR #517 → `d474ad18ba47d55a0d53f1f90e47a451f4dbac5e`.
- M1-B0 PR #518 → `81bf142021cdf4770e9c6ca92078306ac4898783`.
- M1-B1 PR #519 → `21651f22df9ba5210078969aa46abc527ba9e2bd`.
- Wave 1 evidence refresh PR #522 → `12f2550aaa38f3045095152ab862b587db109238`.
- PR #520 fermée sans merge, superseded par #525.
- Gate déterministe PR #526 → merge `a396acfd6570ff24ca683009e1f31bdb3f2c0d92`.

## Wave 1 documentaire
- `READY_FOR_CAPTURE_TRANSPORT`: paracetamol, ibuprofen, amoxicillin, penicillin_v, clarithromycin.
- `PENDING_RCP_LINK_CONFIRMATION`: metronidazole.
- `PENDING_CURRENT_PRESENTATION_DISCOVERY`: clindamycin.
- aucune donnée clinique extraite.
- aucune recherche négative promue comme preuve réglementaire d'absence.

## Première cible RCP réelle
- `AMOXICILLINE SP 1 G COMPRIME DISPERSIBLE BOITE DE 12`.
- regulatory id: `ammps-reg:6fd268f476e7efe0c11f0c4b`.
- EPI: `AMANYS PHARMA`.
- page AMMPS: `https://www.ammps.gov.ma/recherche-medicaments?page=42`.
- statut observé: `Commercialisé`.
- contrôle `Télécharger RCP` observé.
- URL/href exact du PDF non capturé.
- aucun `rcp_url`, hash ou `SNAPSHOT_VERIFIED` inventé.

Le vrai PDF AMMPS + URL officielle + artefact local + SHA-256 sont obligatoires avant promotion `SNAPSHOT_VERIFIED`.

## PR #525 — M1-B2 transport de capture RCP — ACTIVE
Branch: `feat/prescription-pharmacology-morocco-rcp-first-capture-sync`.

Le chantier a continué après le précédent handover et master a avancé. Ne pas réutiliser les anciens SHA comme état courant sans vérification GitHub.

### État exact observé lors de la dernière tentative reviewer
Le workflow indépendant a été lancé contre:
- PR cible: `#525`;
- HEAD cible: `7379ddeab663b833b6be43f455c434be28cafe75`;
- base attendue incluse: `1e9fd49af91ffafad89ad9936c6f2e372e883354`.

Le workflow a vérifié avant lancement:
- checkout du HEAD exact `7379dde...`;
- la base `1e9fd49...` est ancêtre du HEAD;
- diff exactement 3 fichiers:
  - `backend/services/medication_rcp_manifest.py`;
  - `backend/tests/test_medication_rcp_manifest_m1b.py`;
  - `docs/audits/PRESCRIPTION_PHARMACOLOGY_MOROCCO_RCP_M1.md`;
- présence des contrats reviewer/skills.

### Reviewer scientifique indépendant — dernier résultat vérifié
Workflow/job: `Independent scientific review — PR 525`.
Run: `35102869526`.
Target HEAD: `7379ddeab663b833b6be43f455c434be28cafe75`.
Expected base: `1e9fd49af91ffafad89ad9936c6f2e372e883354`.

Résultat: **ECHEC TECHNIQUE AVANT REVUE**.

Cause exacte dans les logs:
`Error: Model "claude-opus-5" from --model flag is not available.`

Conséquences:
- aucun verdict scientifique n'a été produit;
- aucune revue indépendante n'est validée;
- aucun `approve`, `approve_with_reservations`, `request_changes` ou `blocked` scientifique ne doit être inventé;
- l'échec ne remet pas en cause à lui seul le code de #525: il concerne le runtime/configuration du reviewer.

Le job a néanmoins créé l'artefact technique `10448857180`, digest ZIP `dd8452f74e4e30a9725fefbfe146714d577bf0842514a901492145f3851b6e53`, mais il ne contient pas un verdict scientifique valide et ne satisfait donc pas la gate.

### Contrat reviewer observé
Le workflow impose notamment:
- reviewer indépendant/read-only;
- lecture des contrats `.claude/agents/scientific-reviewer.md` et skills associés;
- scope figé sur les 3 fichiers #525 + manifest/docs de référence;
- challenge indépendant des claims transport-only/fail-closed/non-activation;
- priorité aux sources AMMPS officielles;
- aucune écriture repo, aucun merge, aucune donnée patient, aucune activation clinique;
- sortie JSON structurée;
- CI verte explicitement insuffisante comme validation scientifique.

## État de sécurité clinique
- aucune activation clinique autorisée;
- aucune nouvelle dose/durée/indication/AUTO_OK autorisée par ce lot;
- aucun vrai RCP n'est déclaré capturé tant que URL officielle + PDF + artefact local + SHA ne sont pas prouvés;
- reviewer indépendant toujours requis avant clôture/merge selon la gouvernance actuelle.

## Next exact — nouvelle conversation
1. Vérifier GitHub ACTUEL: `master`, PR #525, HEAD, base, mergeability, diff et workflows; ne pas supposer que les SHA ci-dessus sont encore courants.
2. Inspecter le workflow reviewer actuellement présent et corriger uniquement la sélection de modèle/runtime responsable de `claude-opus-5 ... not available`.
3. Choisir un modèle réellement disponible dans GitHub Copilot CLI sans affaiblir l'indépendance, le scope read-only ni le contrat scientifique.
4. Relancer une seule revue indépendante sur le HEAD exact courant de #525.
5. Vérifier le JSON/artefact du reviewer et sa liaison au HEAD exact.
6. Si `request_changes`/`blocked`: corriger #525 → tests/gates exact-head → nouvelle revue indépendante.
7. Si verdict acceptable: revérifier master/HEAD/mergeability/diff/CI puis demander/obtenir l'accord utilisateur explicite pour le merge #525.
8. Après merge: vérifier SHA + CI post-merge.
9. Continuer acquisition RCP/corpus clinique Maroc, toujours sans promotion réglementaire fictive ni activation clinique non validée.

## Interdits
- Pas de merge #525 sans accord utilisateur explicite.
- Pas d'activation clinique M1.
- Pas de `SNAPSHOT_VERIFIED` sans vrai PDF AMMPS + URL officielle exacte + hash concordant.
- Pas de faux reviewer indépendant.
- Pas d'assimilation CI verte = validation scientifique/clinique.
- Ne pas considérer l'artefact `10448857180` comme une revue scientifique réussie.

## Prompt de reprise
`Lis intégralement docs/audits/PRESCRIPTION_PHARMACOLOGY_MOROCCO_M1_HANDOVER.md depuis sa branche canonique, puis vérifie GitHub actuel avant toute modification. Reprends au Next exact. Priorité immédiate: réparer l'échec technique du reviewer indépendant PR #525 (modèle claude-opus-5 indisponible), sans contourner la gate ni modifier la logique clinique.`
