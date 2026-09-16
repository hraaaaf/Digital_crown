# Digital Crown — Pharmacologie Maroc M1 handover

Date: 2026-09-16
Status: ACTIVE — handover only, no runtime change

## Goal global
Construire une couverture pharmacologique dentaire exhaustive et systématiquement sourcée Maroc, avec séparation stricte entre preuve réglementaire, indication, dose et activation clinique.

## Invariants
- Local/on-premise. Aucun changement SaaS/Vercel.
- Préserver DB, données patients, documents et fonctionnalités validées.
- Aucun AUTO_OK ni activation clinique sans preuve Maroc suffisante et revue humaine/scientifique requise.
- Recherche négative != preuve d'absence.
- `scientific-reviewer` indépendant requis avant merge de toute implémentation scientifique lorsque le skill l'exige. L'auteur ne peut pas satisfaire lui-même cette gate.
- Une CI verte ne vaut jamais validation scientifique ou clinique.
- Aucun merge sans accord utilisateur explicite.

## Références à lire au démarrage
1. `docs/audits/PRESCRIPTION_PHARMACOLOGY_MOROCCO_COVERAGE.md`
2. `docs/audits/PRESCRIPTION_PHARMACOLOGY_MOROCCO_RCP_M1.md`
3. `docs/audits/PRESCRIPTION_PHARMACOLOGY_MOROCCO_RCP_WAVE1_QUEUE.json`
4. `docs/audits/PRESCRIPTION_PHARMACOLOGY_SCIENTIFIC_GATE.md` si PR #526 est mergée
5. `.claude/rules/scientific-engineering.md`
6. `.claude/agents/scientific-reviewer.md`
7. `.claude/skills/review-scientific-pull-request/SKILL.md`
8. `.claude/skills/scientific-source-research/SKILL.md`

## Master vérifié
- `master`: `e83b9713e80c94c42a16014d802be850c246adde`.
- Ce SHA est le merge de PR #524 `feat(cephalo): add canonical runtime measurement registry`.
- PR #522 pharmacologie reste mergée en squash sous `12f2550aaa38f3045095152ab862b587db109238`.
- Post-merge CI #4460 / run `35020366249` sur le merge #522: SUCCESS.
- Les mouvements de master après #522 ne remplacent pas l'implémentation M1-B2 de #525.

## Lots pharmacologie fermés
- M1-A PR #517 merge `d474ad18ba47d55a0d53f1f90e47a451f4dbac5e`.
- M1-B0 PR #518 merge `81bf142021cdf4770e9c6ca92078306ac4898783`.
- M1-B1 PR #519 merge `21651f22df9ba5210078969aa46abc527ba9e2bd`.
- Wave 1 evidence refresh PR #522 merge `12f2550aaa38f3045095152ab862b587db109238`.
- PR #520 fermée sans merge, superseded par #525; HEAD historique `15430e879f8e763e55f117842ad27364df8257d5`.

## Wave 1 après PR #522
Queue: `docs/audits/PRESCRIPTION_PHARMACOLOGY_MOROCCO_RCP_WAVE1_QUEUE.json`.

État vérifié:
- `READY_FOR_CAPTURE_TRANSPORT`: paracetamol, ibuprofen, amoxicillin, penicillin_v, clarithromycin.
- `PENDING_RCP_LINK_CONFIRMATION`: metronidazole.
- `PENDING_CURRENT_PRESENTATION_DISCOVERY`: clindamycin.
- aucune donnée clinique extraite.
- aucune recherche négative interprétée comme preuve réglementaire d'absence.

Preuves exact-head #522 `0f9af14763bc6d85bc3a028d12f186c55e7ff746`: CI #4447, Catalog #1301, T2 #3323 et PostgreSQL #838 SUCCESS; M6-I #2123 skipped attendu; post-merge CI #4460 SUCCESS.

## PR #525 — M1-B2 transport de capture RCP
- Branch: `feat/prescription-pharmacology-morocco-rcp-first-capture-sync`.
- Base de création: `12f2550aaa38f3045095152ab862b587db109238`.
- HEAD: `d86149c8f4d84f144d2b6548296e12fa1e4b6e14`.
- State au dernier recheck: OPEN / Ready / mergeable=true.
- Changed files: 3 seulement.
- CI exacte: CI #4467 SUCCESS, PostgreSQL #857 SUCCESS, T2 #3342 SUCCESS, M6-I #2142 skipped attendu.

Implémentation: `prepare_verified_snapshot_entry(...)` offline-only; PENDING_DOWNLOAD fail-closed; URL AMMPS HTTPS; date stricte; artefact `backend/data/rcp/*.pdf`; fichier réel obligatoire; bytes concordants; SHA-256 recalculé; aucune persistance automatique; aucune extraction clinique; aucun changement dose/durée/indication/AUTO_OK/DB/patient/document/UI/Vercel.

Aucune revue indépendante `scientific-reviewer` n'est actuellement attestée pour #525. Paquet de revue: commentaire PR `5689006817`. Clarification des gates: commentaire `5689016950`.

## Première cible RCP réelle
- `AMOXICILLINE SP 1 G COMPRIME DISPERSIBLE BOITE DE 12`.
- regulatory id: `ammps-reg:6fd268f476e7efe0c11f0c4b`.
- EPI: `AMANYS PHARMA`.
- page AMMPS: `https://www.ammps.gov.ma/recherche-medicaments?page=42`.
- statut observé: `Commercialisé`.
- contrôle `Télécharger RCP` observé.
- URL/href exact du PDF non capturé.
- aucun `rcp_url`, hash ou `SNAPSHOT_VERIFIED` inventé.

Le vrai PDF AMMPS + URL officielle + artefact local + SHA-256 sont obligatoires avant promotion `SNAPSHOT_VERIFIED`, mais ne sont pas à eux seuls une condition de merge du helper #525 qui ne revendique aucune capture réelle et n'active aucune règle clinique.

## PR #526 — gate déterministe pharmacologie
- Branch: `ci/pharmacology-scientific-gate-20260916`.
- Base vérifiée: master `e83b9713e80c94c42a16014d802be850c246adde`.
- PR: #526, draft, mergeable=true au dernier recheck.
- HEAD exact: `331e008361227e6ed001c2f7e00fc327d4c5994a`.
- Diff final vérifié: 3 fichiers uniquement:
  - `.github/workflows/pharmacology-scientific-gate.yml`
  - `scripts/pharmacology_scientific_gate.py`
  - `docs/audits/PRESCRIPTION_PHARMACOLOGY_SCIENTIFIC_GATE.md`
- Aucun changement runtime clinique, DB, patient, document, UI, catalogue ou déploiement.

### But de #526
Ajouter une gate GitHub Actions déterministe pour les invariants pharmacologie/RCP objectivement testables, sans la présenter comme une validation scientifique.

Le workflow:
- checkout le HEAD candidat exact;
- lance les tests documentaires M0 et RCP ciblés, isolés du `conftest.py` global via `--noconftest`;
- exécute un oracle stdlib indépendant du runtime applicatif;
- vérifie le contrat `scientific-reviewer` et ses deux skills;
- vérifie les états fail-closed du manifest RCP AMMPS;
- produit `report.json` + `summary.md` et un artefact lié au SHA exact.

### Preuve exacte #526 déjà acquise
Pharmacology Deterministic Scientific Safety Gate #3 / run `35071354622`: SUCCESS sur HEAD `331e008361227e6ed001c2f7e00fc327d4c5994a`.

Artefact `10436103626`, digest `sha256:f6a1fdcc5305eb8f8654d667d83b1ec9148404f5a523b86e7cf3aca504af7aa5`.

Rapport vérifié:
- `status=PASS`;
- `candidate_head=331e008361227e6ed001c2f7e00fc327d4c5994a`;
- 8 manifest entries;
- 8 `PENDING_DOWNLOAD`;
- 0 `SNAPSHOT_VERIFIED`;
- 0 `UNAVAILABLE_VERIFIED`;
- `errors=[]`;
- `clinical_activation_authorized=false`;
- `independent_scientific_review_required=true`.

Le premier run de cette gate a échoué uniquement parce que pytest chargeait le `backend/tests/conftest.py` global sans ses dépendances applicatives. Le workflow final isole les tests documentaires avec `--noconftest` et installe `pytest + SQLAlchemy`; le run exact-head final est vert.

### Certifications #526 encore en cours au dernier check
- CI générale #4491: IN_PROGRESS.
- Cabinet Upgrade PostgreSQL #879: IN_PROGRESS.
- T2 Runtime Browser #3364: IN_PROGRESS.
- M6-I #2164: SKIPPED attendu.

Aucun merge de #526 tant que les certifications applicables ne sont pas terminées et sans accord utilisateur explicite.

## Relation #526 → #525
La gate #526 ne protège durablement les nouvelles PR pharmacologie qu'après merge sur `master`. Elle ne transforme pas rétroactivement #525 en PR revue scientifiquement.

Après merge de #526, #525 devra être resynchronisée ou recevoir un événement PR/HEAD permettant d'exécuter la nouvelle gate sur son contenu exact. Même si la gate déterministe passe, la revue indépendante `scientific-reviewer` reste une gate distincte lorsque requise.

## Next exact
1. Finir les certifications exact-head #526.
2. Si échec: diagnostiquer, corriger, rerun; si vert: recheck master/PR/diff/threads.
3. Obtenir accord utilisateur explicite avant merge #526.
4. Après merge #526: vérifier SHA + post-merge CI.
5. Resynchroniser/retester #525 avec la nouvelle gate déterministe.
6. Faire exécuter le `scientific-reviewer` indépendant sur #525 à partir du paquet `5689006817`.
7. Si review acceptable: recheck exact HEAD/CI/master puis obtenir accord utilisateur explicite avant merge #525.
8. Continuer ensuite l'acquisition RCP/corpus clinique Maroc, sans promotion réglementaire fictive ni activation clinique non validée.

## Interdits
- Pas de merge sans accord utilisateur.
- Pas de Vercel deploy.
- Pas d'activation clinique M1.
- Pas de claim `SNAPSHOT_VERIFIED` sans vrai PDF AMMPS + URL officielle exacte + hash concordant.
- Pas de faux reviewer indépendant.
- Pas d'assimilation d'une CI verte à une validation scientifique ou clinique.
