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
- Aucun `SNAPSHOT_VERIFIED` sans vrai PDF AMMPS + URL officielle exacte + artefact local + SHA-256 concordant.
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
- Gate déterministe initiale PR #526 → merge `a396acfd6570ff24ca683009e1f31bdb3f2c0d92`.
- Réparation isolation/dépendances gate PR #537 → merge `fb3a870e2fba92a005a3e3de57ee378042b23be3`.

## Wave 1 documentaire
- `READY_FOR_CAPTURE_TRANSPORT`: paracetamol, ibuprofen, amoxicillin, penicillin_v, clarithromycin.
- `PENDING_RCP_LINK_CONFIRMATION`: metronidazole.
- `PENDING_CURRENT_PRESENTATION_DISCOVERY`: clindamycin.
- aucune donnée clinique extraite.
- aucune recherche négative promue comme preuve réglementaire d'absence.

## Première cible RCP réelle
- `AMOXICILLINE SP 1 G COMPRIME DISPERSIBLE BOITE DE 12`.
- regulatory id interne: `ammps-reg:6fd268f476e7efe0c11f0c4b`.
- EPI: `AMANYS PHARMA`.
- page AMMPS: `https://www.ammps.gov.ma/recherche-medicaments?page=42`.
- statut observé: `Commercialisé`.
- contrôle `Télécharger RCP` observé.
- URL/href exact du PDF non capturé à ce stade.
- aucun `rcp_url`, hash ou `SNAPSHOT_VERIFIED` inventé.

## PR #525 — M1-B2 transport de capture RCP — ACTIVE
Branch: `feat/prescription-pharmacology-morocco-rcp-first-capture-sync`.

### État exact vérifié
- base/master intégré: `fb3a870e2fba92a005a3e3de57ee378042b23be3`;
- HEAD #525: `84dfb02e979e634363814cab8f856983578aefe6`;
- PR: OPEN, non mergée, `mergeable=true` au dernier contrôle;
- diff: exactement 3 fichiers;
- resynchronisation sans force-push, merge commit à deux parents:
  - parent 1: ancien #525 HEAD `7379ddeab663b833b6be43f455c434be28cafe75`;
  - parent 2: master `fb3a870e2fba92a005a3e3de57ee378042b23be3`.

Blobs M1-B2 préservés:
- `backend/services/medication_rcp_manifest.py` → `42821c4793a0347a6e2935933cc846eee806408a`;
- `backend/tests/test_medication_rcp_manifest_m1b.py` → `9218994c996c6c2689dd35028e74bdd457c83773`;
- `docs/audits/PRESCRIPTION_PHARMACOLOGY_MOROCCO_RCP_M1.md` → `b78b4f66f61e21278ac387697db8f995cc75512f`.

### Gate déterministe current exact-head
Sur `84dfb02e979e634363814cab8f856983578aefe6`:
- Pharmacology Deterministic Scientific Safety Gate #9 / run `35108739456`: `SUCCESS`;
- PR Merge Summary #77 / run `35108739524`: `SUCCESS`;
- CI #4613 / run `35108739450`: `SUCCESS`;
- T2 Runtime Browser #3475 / run `35108739508`: `IN_PROGRESS` au dernier contrôle;
- M6-I #2275: `SKIPPED` attendu.

La gate déterministe est une preuve de sécurité machine, pas une validation scientifique/clinique.

## Reviewer scientifique indépendant
Branch reviewer: `ci/pharmacology-independent-reviewer-20260916`.
Permissions: `contents: read`, `copilot-requests: write`; aucune permission de merge/écriture repo pendant la revue.

### Historique utile
- run `35102869526`: échec technique, modèle `claude-opus-5` indisponible; aucun verdict valide.
- passage à GitHub Copilot CLI `--model auto`.
- run #4 `35107274723`: 31 tests PASS + oracle déterministe PASS + capture navigateur AMMPS réussie, puis échec du matcher textuel trop strict avant reviewer.
- matcher réparé: capture `visible text + DOM text + hrefs`, validation structurelle tolérante au rendu.

### Dernier verdict scientifique complet disponible
Reviewer #5 / run `35108552848`, lié à l'ancien HEAD `7379ddeab663b833b6be43f455c434be28cafe75`:
- workflow: `SUCCESS`;
- decision: `approve_with_reservations`;
- blocking findings: 0;
- scientific uncertainties: 0;
- provenance officielle AMMPS page 42 et page 96 indépendamment reproduite;
- tests documentaires et oracle déterministe vérifiés;
- `clinical_activation_authorized=false`.

Réserve/required action du reviewer #5:
avant toute future promotion `SNAPSHOT_VERIFIED`, capturer un vrai PDF RCP AMMPS, conserver les bytes exacts localement, calculer SHA-256 et lier l'artefact à l'URL officielle exacte.

### Reviewer current exact-head
Reviewer #6 / run `35108878880` cible:
- PR #525;
- HEAD `84dfb02e979e634363814cab8f856983578aefe6`;
- expected base `fb3a870e2fba92a005a3e3de57ee378042b23be3`.

Au dernier contrôle:
- checkout exact: SUCCESS;
- scope 3 fichiers: SUCCESS;
- tests/oracle: SUCCESS;
- capture AMMPS navigateur: SUCCESS;
- validation structurelle des présentations AMMPS: SUCCESS;
- Copilot reviewer: IN_PROGRESS;
- aucun verdict final current-head encore déclaré.

## État de sécurité clinique
- aucune activation clinique autorisée;
- aucune nouvelle dose/durée/indication/AUTO_OK autorisée par ce lot;
- aucun vrai RCP n'est déclaré capturé tant que URL officielle + PDF + artefact local + SHA ne sont pas prouvés;
- les regulatory ids `ammps-reg:*` sont des identifiants déterministes internes dérivés des champs présentation, pas des identifiants émis par l'AMMPS.

## Next exact
1. Lire l'artefact JSON du reviewer #6 et vérifier `target_head=84dfb02e...`, `expected_base=fb3a870e...`, decision, findings, required actions et `clinical_activation_authorized=false`.
2. Si `blocked`/`request_changes`: corriger la cause réelle, recertifier exact-head, puis relancer une revue indépendante.
3. Si verdict acceptable: vérifier T2 #3475, master courant, HEAD #525, mergeability et diff exact 3 fichiers.
4. Si toutes les gates sont satisfaites: merger #525 avec garde sur HEAD exact, conformément à l'autorisation utilisateur de poursuivre la séquence.
5. Vérifier merge SHA + CI post-merge une fois; continuer le travail indépendant si la CI tourne.
6. Mettre à jour ce handover avec l'état final M1-B2.
7. Passer à l'acquisition du premier vrai RCP AMMPS sans activation clinique automatique.

## Interdits
- Pas d'activation clinique M1.
- Pas de `SNAPSHOT_VERIFIED` sans vrai PDF AMMPS + URL officielle exacte + hash concordant.
- Pas de faux reviewer indépendant.
- Pas d'assimilation CI verte = validation scientifique/clinique.
- Ne pas considérer les anciens artefacts reviewer comme preuve exact-head après déplacement de #525.

## Prompt de reprise
`Lis intégralement docs/audits/PRESCRIPTION_PHARMACOLOGY_MOROCCO_M1_HANDOVER.md depuis la branche docs/pharmacology-m1-handover-20260915, puis vérifie GitHub actuel. Reprends au Next exact. Ne déclare aucun verdict scientifique current-head sans l'artefact JSON du reviewer lié au HEAD exact.`
