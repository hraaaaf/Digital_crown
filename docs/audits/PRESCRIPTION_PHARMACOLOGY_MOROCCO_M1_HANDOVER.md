# Digital Crown — Pharmacologie Maroc M1 handover

Date: 2026-09-16
Status: ACTIVE — no clinical activation

## Goal global
Construire une couverture pharmacologique dentaire exhaustive et systématiquement sourcée Maroc, avec séparation stricte entre preuve réglementaire, indication, dose et activation clinique.

## Invariants
- Local/on-premise; aucun changement SaaS/Vercel.
- Préserver DB, données patients, documents et fonctionnalités validées.
- Aucun `AUTO_OK` ni activation clinique sans preuve Maroc suffisante et revue humaine/scientifique requise.
- Recherche négative != preuve d'absence.
- CI verte != validation scientifique/clinique.
- `scientific-reviewer` indépendant lorsque la gouvernance l'exige; l'agent auteur ne peut pas auto-satisfaire cette gate.
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

## Master vérifié
- `master`: `a396acfd6570ff24ca683009e1f31bdb3f2c0d92`.
- Ce SHA est le squash merge de PR #526 `ci(pharmacology): add deterministic scientific safety gate`.
- Commit GitHub signé/verified.
- Post-merge CI master #4494 / run `35075198843`: `IN_PROGRESS` au dernier recheck; ne pas le considérer vert tant qu'il n'est pas terminé.

## Lots fermés
- M1-A PR #517 → `d474ad18ba47d55a0d53f1f90e47a451f4dbac5e`.
- M1-B0 PR #518 → `81bf142021cdf4770e9c6ca92078306ac4898783`.
- M1-B1 PR #519 → `21651f22df9ba5210078969aa46abc527ba9e2bd`.
- Wave 1 evidence refresh PR #522 → `12f2550aaa38f3045095152ab862b587db109238`.
- PR #520 closed sans merge, superseded par #525; HEAD historique `15430e879f8e763e55f117842ad27364df8257d5`.
- Gate déterministe PR #526 → merge `a396acfd6570ff24ca683009e1f31bdb3f2c0d92`.

## Wave 1 documentaire
Queue: `docs/audits/PRESCRIPTION_PHARMACOLOGY_MOROCCO_RCP_WAVE1_QUEUE.json`.

État vérifié:
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

Le vrai PDF AMMPS + URL officielle + artefact local + SHA-256 sont obligatoires avant promotion `SNAPSHOT_VERIFIED`. Ils ne sont pas à eux seuls une condition de merge du helper #525, qui ne revendique aucune capture réelle et n'active aucune règle clinique.

## PR #526 — gate déterministe pharmacologie — MERGED
But: automatiser uniquement les invariants objectivement testables, sans prétendre remplacer une validation scientifique.

Fichiers livrés:
- `.github/workflows/pharmacology-scientific-gate.yml`
- `scripts/pharmacology_scientific_gate.py`
- `docs/audits/PRESCRIPTION_PHARMACOLOGY_SCIENTIFIC_GATE.md`

Exact-head pré-merge `331e008361227e6ed001c2f7e00fc327d4c5994a`:
- gate #3 / run `35071354622`: SUCCESS;
- CI #4491 / run `35071354564`: SUCCESS;
- PostgreSQL #879 / run `35071354601`: SUCCESS;
- T2 #3364 / run `35071354605`: SUCCESS;
- M6-I #2164: SKIPPED attendu.

Artefact gate pré-merge `10436103626`, digest `sha256:f6a1fdcc5305eb8f8654d667d83b1ec9148404f5a523b86e7cf3aca504af7aa5`.

## PR #525 — M1-B2 transport de capture RCP — CURRENT
Branch: `feat/prescription-pharmacology-morocco-rcp-first-capture-sync`.

### Resynchronisation sur master après #526
Ancien HEAD: `d86149c8f4d84f144d2b6548296e12fa1e4b6e14`.

Nouveau HEAD exact: `8ae695412a9208ca89f4cd3be741e845c805cf45`.

La resynchronisation a été faite sans force-push par un merge commit à deux parents:
- premier parent = ancien #525 HEAD `d86149c8f4d84f144d2b6548296e12fa1e4b6e14`;
- second parent = master `a396acfd6570ff24ca683009e1f31bdb3f2c0d92`.

Le tree du merge reprend master partout sauf les 3 fichiers M1-B2 intentionnels. PR #525 est de nouveau `mergeable=true` et son diff reste exactement 3 fichiers.

Blobs préservés:
- `backend/services/medication_rcp_manifest.py` → `42821c4793a0347a6e2935933cc846eee806408a`;
- `backend/tests/test_medication_rcp_manifest_m1b.py` → `9218994c996c6c2689dd35028e74bdd457c83773`;
- `docs/audits/PRESCRIPTION_PHARMACOLOGY_MOROCCO_RCP_M1.md` → `b78b4f66f61e21278ac387697db8f995cc75512f`.

### Implémentation M1-B2
- `prepare_verified_snapshot_entry(...)` offline-only.
- entrée source = `PENDING_DOWNLOAD` valide/fail-closed.
- URL RCP HTTPS AMMPS officielle obligatoire.
- date stricte `YYYY-MM-DD`.
- artefact limité à `backend/data/rcp/*.pdf`.
- fichier local réel obligatoire et bytes identiques aux bytes capturés.
- SHA-256 calculé sur l'artefact local réel.
- `snapshot_is_verified(...)` relit l'artefact et refuse fichier absent, hash faux, mauvaise extension ou faux PDF.
- aucune persistance automatique.
- aucune extraction clinique.
- aucun changement dose/durée/indication/AUTO_OK/DB/patient/document/UI/Vercel.

### Gate déterministe sur #525 exact HEAD
`Pharmacology Deterministic Scientific Safety Gate` #4 / run `35075958218`: SUCCESS sur `8ae695412a9208ca89f4cd3be741e845c805cf45`.

Artefact `10438570397`, digest `sha256:c1f753e26c6c40b81d682b26d535093a44beebe1b7a6901805b62d6dad761d20`.

Rapport vérifié:
- `status=PASS`;
- `candidate_head=8ae695412a9208ca89f4cd3be741e845c805cf45`;
- 8 manifest entries;
- 8 `PENDING_DOWNLOAD`;
- 0 `SNAPSHOT_VERIFIED`;
- 0 `UNAVAILABLE_VERIFIED`;
- `errors=[]`;
- `clinical_activation_authorized=false`;
- `independent_scientific_review_required=true`.

### Certifications #525 au dernier recheck
- CI #4500: `IN_PROGRESS`.
- PostgreSQL #887: `IN_PROGRESS`.
- T2 #3372: `IN_PROGRESS`.
- M6-I #2172: `SKIPPED` attendu.

### Revue scientifique indépendante
Toujours non satisfaite.

Paquet historique: commentaire `5689006817`.
Paquet rafraîchi exact-head après resync: commentaire `5694730976`.

Ne pas auto-valider cette gate. Aucun reviewer indépendant réel n'est actuellement attesté dans cette session.

## Next exact
1. Laisser finir les certifications exact-head #525 sans polling passif.
2. Si échec: diagnostiquer/corriger/retester sur nouveau HEAD puis refaire la gate.
3. Si vert: vérifier master, HEAD, mergeability, diff et review threads une fois.
4. Faire exécuter le `scientific-reviewer` indépendant sur #525 à partir du paquet `5694730976`.
5. Si findings: corriger puis rerun/re-review.
6. Si review acceptable: obtenir accord utilisateur explicite avant merge #525.
7. Après merge: vérifier SHA + post-merge CI.
8. Continuer l'acquisition RCP/corpus clinique Maroc sans promotion réglementaire fictive ni activation clinique non validée.

## Interdits
- Pas de merge #525 sans accord utilisateur explicite.
- Pas de Vercel deploy.
- Pas d'activation clinique M1.
- Pas de `SNAPSHOT_VERIFIED` sans vrai PDF AMMPS + URL officielle exacte + hash concordant.
- Pas de faux reviewer indépendant.
- Pas d'assimilation CI verte = validation scientifique/clinique.
