# Digital Crown — Pharmacologie Maroc M1 handover

Date: 2026-09-16
Status: ACTIVE — no clinical activation

## Goal
Construire la couverture pharmacologique dentaire Maroc avec preuve réglementaire fail-closed, puis validation scientifique indépendante avant toute activation clinique.

## Invariants
- Digital Crown reste local/on-premise.
- Aucun déploiement de l'application clinique ni de ses données sur Vercel.
- Préserver DB, patients, documents et fonctionnalités validées.
- CI verte != validation scientifique/clinique.
- Reviewer scientifique indépendant, read-only.
- Aucun `AUTO_OK` ni activation clinique par M1-B2.
- Recherche négative != preuve d'absence.
- Aucun `SNAPSHOT_VERIFIED` sans vrai PDF AMMPS + URL officielle exacte + bytes locaux + SHA-256 concordant.

## Lots déjà fermés
- M1-A PR #517 → `d474ad18ba47d55a0d53f1f90e47a451f4dbac5e`.
- M1-B0 PR #518 → `81bf142021cdf4770e9c6ca92078306ac4898783`.
- M1-B1 PR #519 → `21651f22df9ba5210078969aa46abc527ba9e2bd`.
- Wave 1 evidence refresh PR #522 → `12f2550aaa38f3045095152ab862b587db109238`.
- Gate déterministe initiale PR #526 → `a396acfd6570ff24ca683009e1f31bdb3f2c0d92`.
- Réparation gate PR #537 → merge `fb3a870e2fba92a005a3e3de57ee378042b23be3`.

## Wave 1 documentaire
- `READY_FOR_CAPTURE_TRANSPORT`: paracetamol, ibuprofen, amoxicillin, penicillin_v, clarithromycin.
- `PENDING_RCP_LINK_CONFIRMATION`: metronidazole.
- `PENDING_CURRENT_PRESENTATION_DISCOVERY`: clindamycin.
- aucune donnée clinique extraite.

## Première cible RCP réelle
- `AMOXICILLINE SP 1 G COMPRIME DISPERSIBLE BOITE DE 12`.
- regulatory id interne: `ammps-reg:6fd268f476e7efe0c11f0c4b`.
- EPI: `AMANYS PHARMA`.
- page AMMPS: `https://www.ammps.gov.ma/recherche-medicaments?page=42`.
- statut observé: `Commercialisé`.
- contrôle `Télécharger RCP` observé.
- le bouton rendu utilise `javascript:void(0)` dans son href; l'URL PDF exacte n'est donc toujours pas connue et devra être capturée en déclenchant/interceptant la requête réelle.
- aucun `rcp_url`, hash ou `SNAPSHOT_VERIFIED` inventé.

## PR #525 — ACTIVE
Branch: `feat/prescription-pharmacology-morocco-rcp-first-capture-sync`.

### État exact courant
- base intégrée: `fb3a870e2fba92a005a3e3de57ee378042b23be3`;
- HEAD: `4b4cfd968951c97af39d3e757afde5185ffeb196`;
- PR OPEN, non mergée, `mergeable=true` au dernier contrôle;
- diff exactement 3 fichiers:
  - `backend/services/medication_rcp_manifest.py`;
  - `backend/tests/test_medication_rcp_manifest_m1b.py`;
  - `docs/audits/PRESCRIPTION_PHARMACOLOGY_MOROCCO_RCP_M1.md`.

### Historique reviewer
- `35102869526`: échec technique avant revue (`claude-opus-5` indisponible), aucun verdict valide.
- reviewer passé à GitHub Copilot CLI `--model auto`.
- #5 `35108552848`, HEAD `7379dde...`: `approve_with_reservations`, 0 blocage; AMMPS page 42/96 reproduites; réserve = capturer un vrai RCP avant `SNAPSHOT_VERIFIED`.
- #6 `35108878880`, HEAD `84dfb02...`: `request_changes` avec 1 finding bloquant réel `RCP-PATH-SYMLINK-ESCAPE`.

### Finding #6 et correction
Finding: un chemin déclaré sous `backend/data/rcp/*.pdf` pouvait être un symlink résolvant vers un PDF ailleurs dans le repo, car le contrôle résolu restait borné au repo et non au répertoire RCP canonique.

Correction:
- `dab1dc453a430a4bbc5444826608c2979b08a6d1`: confinement après résolution sous le vrai `backend/data/rcp` + refus si le root canonique RCP est lui-même redirigé par symlink;
- `4b4cfd968951c97af39d3e757afde5185ffeb196`: deux tests de régression — symlink fichier sortant du dossier RCP et symlink du dossier canonique RCP.

### Preuve technique exact-head actuelle
Sur `4b4cfd968951c97af39d3e757afde5185ffeb196`:
- Pharmacology Deterministic Scientific Safety Gate #11 / `35109483397`: `SUCCESS`;
- tests ciblés: `33 passed in 0.31s`;
- oracle déterministe: `PASS`;
- artefact gate: `10451164482`;
- digest: `sha256:1aeeaae2f8d6b8252bd90938db5701c0ab1c0f5e65cdc9b77cbc3f259949ac80`;
- PR Merge Summary #82 / `35109483555`: `SUCCESS`;
- CI #4618 / `35109483296`: `IN_PROGRESS` au dernier contrôle;
- T2 #3480 / `35109483225`: `IN_PROGRESS` au dernier contrôle;
- M6-I #2280: `SKIPPED` attendu.

### Reviewer exact-head après correction
Reviewer #7 / run `35109624600` cible:
- HEAD `4b4cfd968951c97af39d3e757afde5185ffeb196`;
- expected base `fb3a870e2fba92a005a3e3de57ee378042b23be3`.

Déjà SUCCESS dans ce run:
- checkout exact;
- scope exact 3 fichiers;
- contrats reviewer;
- tests/oracle;
- capture navigateur AMMPS;
- validation structurelle AMMPS.

Au dernier contrôle, le Copilot reviewer était `IN_PROGRESS`; aucun verdict final #7 n'est encore déclaré.

## État clinique
- aucune activation clinique;
- aucune dose/durée/indication/AUTO_OK ajoutée;
- les 8 entrées amoxicilline restent fail-closed;
- aucune entrée n'est `SNAPSHOT_VERIFIED` ni `UNAVAILABLE_VERIFIED`;
- les IDs `ammps-reg:*` sont des IDs internes déterministes, pas des identifiants émis par l'AMMPS.

## Next exact
1. Lire et valider le JSON du reviewer #7 lié au HEAD exact `4b4cfd...`.
2. Si `request_changes`/`blocked`: corriger le finding réel puis recertifier et rereviewer.
3. Si verdict acceptable: vérifier CI #4618 + T2 #3480, puis master courant, HEAD, mergeability et diff exact 3 fichiers.
4. Si toutes les gates sont satisfaites: merger #525 avec garde sur HEAD exact, conformément à l'autorisation utilisateur de poursuivre la séquence.
5. Vérifier merge SHA + CI post-merge une fois.
6. Mettre ce handover à jour.
7. Continuer par la capture réelle du premier RCP AMMPS en interceptant l'action `Télécharger RCP`, sans inventer l'URL.

## Interdits
- Pas d'activation clinique M1-B2.
- Pas de `SNAPSHOT_VERIFIED` sans artefact réel vérifié.
- Pas de faux verdict reviewer.
- Pas d'assimilation CI verte = validation scientifique.

## Prompt de reprise
`Lis ce fichier depuis docs/pharmacology-m1-handover-20260915, vérifie GitHub actuel, puis reprends au Next exact. Le HEAD #525 connu est 4b4cfd968951c97af39d3e757afde5185ffeb196; ne le suppose pas encore courant sans vérification.`
