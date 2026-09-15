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
- `master`: `12f2550aaa38f3045095152ab862b587db109238`
- Ce SHA est le squash merge de PR #522.
- Post-merge CI master #4460 / run `35020366249` lancée sur ce SHA ; dernier état observé: `in_progress`. Recheck une seule fois quand nécessaire.

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

## PR #520 — CLOSED / SUPERSEDED
- Branche: `feat/prescription-pharmacology-morocco-rcp-first-capture`
- HEAD historique: `15430e879f8e763e55f117842ad27364df8257d5`
- Fermée sans merge après création du successeur #525.
- Historique/preuves conservés.
- Exact-head historique: CI #4437 SUCCESS, PostgreSQL #829 SUCCESS, T2 #3314 SUCCESS, M6-I skipped attendu.

## PR #525 — M1-B2 resynchronisé sur master courant
Branch: `feat/prescription-pharmacology-morocco-rcp-first-capture-sync`
Base: `12f2550aaa38f3045095152ab862b587db109238`
HEAD actuel: `d86149c8f4d84f144d2b6548296e12fa1e4b6e14`
State: OPEN / Ready
Changed files: 3 seulement

### Preuve de resynchronisation
Les deux commits master arrivés après la base initiale de #520 ne touchaient aucun des trois fichiers M1-B2.

Les deux fichiers exécutables de #525 sont byte-identiques au HEAD historique #520:
- `backend/services/medication_rcp_manifest.py` blob `42821c4793a0347a6e2935933cc846eee806408a`
- `backend/tests/test_medication_rcp_manifest_m1b.py` blob `9218994c996c6c2689dd35028e74bdd457c83773`

Le troisième fichier, `docs/audits/PRESCRIPTION_PHARMACOLOGY_MOROCCO_RCP_M1.md`, a été réaligné volontairement sur l'état documentaire après #522.

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

### CI #525 au dernier check
HEAD `d86149c8f4d84f144d2b6548296e12fa1e4b6e14`:
- CI #4467 QUEUED
- Cabinet Upgrade PostgreSQL #857 IN_PROGRESS
- T2 Runtime Browser #3342 QUEUED
- M6-I #2142 SKIPPED attendu

Le test local n'a pas pu être exécuté dans l'environnement de chat parce que la résolution DNS vers `github.com` a échoué. Ce n'est pas retenu comme preuve de test. La certification GitHub reste la preuve attendue.

## Gate scientifique restante
Aucune revue indépendante `scientific-reviewer` n'est actuellement attestée pour #525.

Ne pas auto-valider cette gate. Ne pas remplacer la revue indépendante par un commentaire de l'agent auteur.

## Première cible RCP réelle
- `AMOXICILLINE SP 1 G COMPRIME DISPERSIBLE BOITE DE 12`
- regulatory id: `ammps-reg:6fd268f476e7efe0c11f0c4b`
- page AMMPS: `https://www.ammps.gov.ma/recherche-medicaments?page=42`
- bouton `Télécharger RCP` observé.
- URL/PDF cible exact toujours non capturé.
- Ne jamais inventer le `rcp_url`.

## Next exact
1. Recheck une seule fois CI #525 et post-merge #522 quand nécessaire.
2. Si CI #525 échoue: diagnostiquer/corriger/retester.
3. Si CI #525 est verte: conserver #525 non mergée tant que `scientific-reviewer` indépendant n'a pas validé et tant que l'utilisateur n'a pas explicitement autorisé le merge.
4. Capturer le vrai PDF RCP AMMPS de la cible amoxicilline via un transport réellement disponible.
5. Stocker sous `backend/data/rcp/*.pdf`, vérifier les octets, calculer SHA-256, renseigner URL/date exactes et promouvoir UNE entrée exacte à `SNAPSHOT_VERIFIED` seulement si toutes les preuves concordent.
6. Tests exact-head -> revue scientifique indépendante -> accord utilisateur -> merge -> post-merge -> lot suivant.

## Interdits
- Pas de merge sans accord utilisateur.
- Pas de Vercel deploy.
- Pas d'activation clinique M1.
- Pas de claim `SNAPSHOT_VERIFIED` sans vrai PDF AMMPS + URL officielle exacte + hash concordant.

## Critère de succès M1-B2
Une entrée RCP exacte est promue à `SNAPSHOT_VERIFIED` uniquement si le PDF AMMPS réel existe localement, son URL officielle est connue, la date est valide, le SHA-256 correspond au fichier relu, les tests passent, la revue scientifique indépendante est satisfaite et la CI exact-head est verte.
