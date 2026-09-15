# Digital Crown — Pharmacologie Maroc M1 handover

Date: 2026-09-15
Status: ACTIVE — handover only, no runtime change

## Goal global
Construire une couverture pharmacologique dentaire exhaustive et systématiquement sourcée Maroc, avec séparation stricte entre preuve réglementaire, indication, dose et activation clinique.

## Invariants
- Local/on-premise. Aucun changement SaaS/Vercel.
- Préserver DB, données patients, documents et fonctionnalités validées.
- Aucun AUTO_OK ni activation clinique sans preuve Maroc suffisante et revue humaine/scientifique requise.
- Recherche négative != preuve d'absence.
- `scientific-reviewer` indépendant requis avant merge de toute implémentation scientifique. L'auteur ne peut pas satisfaire lui-même cette gate.
- Aucun merge sans accord utilisateur explicite.

## Références à lire au démarrage
1. `docs/audits/PRESCRIPTION_PHARMACOLOGY_MOROCCO_COVERAGE.md`
2. `docs/audits/PRESCRIPTION_PHARMACOLOGY_MOROCCO_RCP_M1.md`
3. `docs/audits/PRESCRIPTION_PHARMACOLOGY_MOROCCO_RCP_WAVE1_QUEUE.json`
4. `.claude/rules/scientific-engineering.md`
5. `.claude/agents/scientific-reviewer.md`
6. `.claude/agents/pharmacology-engineer.md`

## Master vérifié
- `master`: `c6cd103674ea4db530a30dddc9de563e54a0221b`.
- Ce SHA est le merge de PR #498 `fix(ui): remove internal technical statuses from practitioner copy`.
- PR #522 reste mergée en squash sous `12f2550aaa38f3045095152ab862b587db109238`.
- Post-merge CI #4460 / run `35020366249` sur le merge #522: SUCCESS.
- Le mouvement de master après #522 est un lot UI/client-copy. Les versions master de `backend/services/medication_rcp_manifest.py` et `backend/tests/test_medication_rcp_manifest_m1b.py` restent les versions pré-M1-B2; il ne supplante donc pas l'implémentation de #525.

## Lots fermés
- M1-A PR #517 merge `d474ad18ba47d55a0d53f1f90e47a451f4dbac5e`.
- M1-B0 PR #518 merge `81bf142021cdf4770e9c6ca92078306ac4898783`.
- M1-B1 PR #519 merge `21651f22df9ba5210078969aa46abc527ba9e2bd`.
- Wave 1 evidence refresh PR #522 merge `12f2550aaa38f3045095152ab862b587db109238`.

## Wave 1 après PR #522
Queue: `docs/audits/PRESCRIPTION_PHARMACOLOGY_MOROCCO_RCP_WAVE1_QUEUE.json`.

État actuel:
- `READY_FOR_CAPTURE_TRANSPORT`: paracetamol, ibuprofen, amoxicillin, penicillin_v, clarithromycin.
- `PENDING_RCP_LINK_CONFIRMATION`: metronidazole.
- `PENDING_CURRENT_PRESENTATION_DISCOVERY`: clindamycin.
- aucune donnée clinique extraite.
- aucune recherche négative interprétée comme preuve réglementaire d'absence.

Preuves exact-head #522 `0f9af14763bc6d85bc3a028d12f186c55e7ff746`:
- CI #4447 SUCCESS
- Catalog Connected Truth #1301 SUCCESS
- T2 Runtime Browser #3323 SUCCESS
- Cabinet Upgrade PostgreSQL #838 SUCCESS
- M6-I #2123 SKIPPED attendu
- post-merge master CI #4460 SUCCESS

## PR #520 — CLOSED / SUPERSEDED
- Branche: `feat/prescription-pharmacology-morocco-rcp-first-capture`.
- HEAD historique: `15430e879f8e763e55f117842ad27364df8257d5`.
- Fermée sans merge après création du successeur #525.
- Historique/preuves conservés.
- Exact-head historique: CI #4437 SUCCESS, PostgreSQL #829 SUCCESS, T2 #3314 SUCCESS, M6-I skipped attendu.

## PR #525 — M1-B2 transport de capture RCP
Branch: `feat/prescription-pharmacology-morocco-rcp-first-capture-sync`
Base de création: `12f2550aaa38f3045095152ab862b587db109238`
HEAD actuel: `d86149c8f4d84f144d2b6548296e12fa1e4b6e14`
State: OPEN / Ready / mergeable=true au dernier recheck
Changed files: 3 seulement

### Preuve de resynchronisation
Les fichiers exécutables de #525 sont byte-identiques au HEAD historique #520:
- `backend/services/medication_rcp_manifest.py` blob `42821c4793a0347a6e2935933cc846eee806408a`
- `backend/tests/test_medication_rcp_manifest_m1b.py` blob `9218994c996c6c2689dd35028e74bdd457c83773`

Le troisième fichier, `docs/audits/PRESCRIPTION_PHARMACOLOGY_MOROCCO_RCP_M1.md`, a été réaligné volontairement sur l'état documentaire après #522.

Master a ensuite avancé jusqu'à `c6cd103674ea4db530a30dddc9de563e54a0221b` via #498. Le service et le test M1-B2 ne sont pas présents sur master et #525 reste mergeable. Toute mutation/merge doit néanmoins revalider l'état courant de master et de la PR.

### Implémentation M1-B2
- `prepare_verified_snapshot_entry(...)` offline-only.
- Entrée source doit être `PENDING_DOWNLOAD` et fail-closed.
- URL RCP HTTPS AMMPS officielle obligatoire.
- date stricte `YYYY-MM-DD`.
- artefact sous `backend/data/rcp/*.pdf`.
- artefact local doit exister et correspondre exactement aux octets capturés.
- SHA-256 calculé depuis le vrai fichier local.
- `snapshot_is_verified(...)` relit l'artefact et refuse fichier absent, hash faux, mauvaise extension ou faux PDF.
- aucune persistance automatique.
- aucune extraction clinique.
- aucun changement dose/durée/indication/AUTO_OK/DB/patient/document/UI/Vercel.

### CI exacte #525
HEAD `d86149c8f4d84f144d2b6548296e12fa1e4b6e14`:
- CI #4467 / run `35021262382`: SUCCESS
- Cabinet Upgrade PostgreSQL #857 / run `35021262369`: SUCCESS
- T2 Runtime Browser #3342 / run `35021262458`: SUCCESS
- M6-I #2142 / run `35021262442`: SKIPPED attendu

Le test local tenté antérieurement n'avait pas pu démarrer à cause d'un échec DNS vers GitHub; il n'est pas compté comme preuve. Les certifications GitHub ci-dessus constituent les preuves exact-head disponibles.

## Gate scientifique restante
Aucune revue indépendante `scientific-reviewer` n'est actuellement attestée pour #525. `list_pull_request_reviews` a retourné zéro review et aucun reviewer/team nommé n'est configuré dans la PR.

Règles repo relues:
- `.claude/agents/scientific-reviewer.md`: reviewer différent de l'agent auteur, read-only, décision structurée obligatoire;
- `.claude/skills/review-scientific-pull-request/SKILL.md`: `no named reviewer` est bloquant;
- `.claude/rules/scientific-engineering.md`: tests verts != validation scientifique.

Paquet de revue matérialisé dans la conversation PR #525, commentaire `5689006817`, avec HEAD exact, fichiers, claims, preuves CI et output contract requis.

Ne pas auto-valider cette gate. Ne pas remplacer la revue indépendante par un commentaire de l'agent auteur.

## Première cible RCP réelle
- `AMOXICILLINE SP 1 G COMPRIME DISPERSIBLE BOITE DE 12`
- regulatory id: `ammps-reg:6fd268f476e7efe0c11f0c4b`
- EPI: `AMANYS PHARMA`
- page AMMPS: `https://www.ammps.gov.ma/recherche-medicaments?page=42`
- statut courant observé: `Commercialisé`
- contrôle `Télécharger RCP` observé sur la page officielle.
- l'URL/href exact du PDF n'est toujours pas exposé par les transports disponibles.
- aucun `rcp_url`, hash ou `SNAPSHOT_VERIFIED` n'est inventé.

## Clarification des gates
- Le vrai PDF AMMPS + URL officielle + artefact local + SHA-256 sont obligatoires avant toute promotion vers `SNAPSHOT_VERIFIED` et avant clôture scientifique M1-B2.
- Ils ne sont pas, à eux seuls, une condition de merge du helper de transport #525, puisque #525 ne prétend capturer aucun RCP et n'active aucun comportement clinique.
- Les gates de merge #525 sont: revue `scientific-reviewer` indépendante nommée, recheck master/PR/non-régression applicable, CI applicable verte et accord utilisateur explicite.
- Cette clarification est enregistrée sur #525, commentaire `5689016950`.

## Next exact
1. Faire exécuter le reviewer indépendant sur #525 à partir du paquet `5689006817`.
2. Si findings: corriger sur #525, relancer tests/certifications proportionnés, puis refaire une revue indépendante sur le nouveau HEAD.
3. Si review acceptable: rechecker master, mergeability, HEAD et CI une fois.
4. Demander/obtenir l'accord utilisateur explicite avant merge #525.
5. Après merge: vérifier SHA de merge + post-merge CI.
6. Continuer l'acquisition de preuve: capturer le vrai RCP AMMPS si un transport fiable devient disponible; sinon conserver `PENDING_DOWNLOAD` et utiliser séparément les sources professionnelles marocaines/internationales pour le corpus clinique, sans les promouvoir au rang de RCP officiel.
7. Toute future promotion `SNAPSHOT_VERIFIED` exige le PDF AMMPS réel + URL officielle + hash concordant + tests + revue/human gate applicable.

## Interdits
- Pas de merge sans accord utilisateur.
- Pas de Vercel deploy.
- Pas d'activation clinique M1.
- Pas de claim `SNAPSHOT_VERIFIED` sans vrai PDF AMMPS + URL officielle exacte + hash concordant.
- Pas de faux reviewer indépendant.

## Critère de succès M1-B2
Une entrée RCP exacte est promue à `SNAPSHOT_VERIFIED` uniquement si le PDF AMMPS réel existe localement, son URL officielle est connue, la date est valide, le SHA-256 correspond au fichier relu, les tests passent, la revue scientifique indépendante applicable est satisfaite et la CI exact-head est verte.
