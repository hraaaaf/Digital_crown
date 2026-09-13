# Digital Crown — Clinique multi-praticiens

## Statut

P0 backend, P1 UX et P2 Patient/actes/facturation sont certifiés et mergés. Le gate de compatibilité d'upgrade cabinet réel est certifié sur données réelles copiées, corrigé puis mergé. L'implémentation P3 Documents/auteurs/signatures est mergée ; le gate reproductible de préservation locale PR #463 reste en cours avant certification finale du lot.

## Goal global

Faire évoluer Digital Crown d'un agenda de cabinet partagé vers un fonctionnement clinique réellement multi-praticiens, sans casser les données historiques ni mélanger les axes licence, abonnement et type de cabinet.

## Principes invariants

- Le tenant canonique reste le cabinet propriétaire : `User.get_employer_id()` / `Appointment.employer_id`.
- Le praticien canonique est un `User.id` existant, pas une table parallèle.
- Un praticien assignable appartient au même cabinet, est actif, approuvé et a le rôle `DENTISTE`; le propriétaire du cabinet est également assignable lorsqu'il est dentiste/admin actif.
- Les données Patients et Documents locales restent la source de vérité et ne sont pas remplacées par une couche cloud.
- Les rendez-vous historiques restent valides sans backfill forcé.
- `praticien_id = NULL` signifie rendez-vous legacy/non assigné et conserve un comportement de blocage global.
- Deux praticiens différents peuvent travailler simultanément.
- Aucun changement de déploiement Vercel dans ce chantier sans autorisation explicite.

## P0 — Agenda multi-praticiens réel — CERTIFIÉ / MERGÉ

- Code HEAD certifié : `f2e96286409ac22783afb3eff6b9651dce9d7ebc`.
- CI `34660038023` : success.
- PR #429 mergée ; merge `f265ebcd9f0654f346a969def5d93f66451af67d`.
- `appointments.praticien_id` nullable, tenant-safe, conflits par praticien et legacy NULL conservés.

## P1 — UX clinique ciblée — CERTIFIÉ / MERGÉ

- Code HEAD certifié : `3c29f2e29b730d447aff72f81416249bdf5073f5`.
- Visual `34681876692`, T2 `34681876693`, CI `34681876685` : success.
- 9 captures Dashboard / Agenda / Team × 390 / 768 / 1280 : 0 overflow, 0 runtime error.
- Score visuel : **9,2 / 10**.
- PR #430 mergée ; merge `1a115752e133e583e523fea7c4180d97db956f75`.

## P2 — Patient, actes et facturation — CERTIFIÉ / MERGÉ

### Goal

Ajouter un référent clinique et une lecture financière multi-praticiens sans modifier la liste Patients locale ni déplacer/réécrire les documents locaux existants.

### Architecture certifiée

- `patients` reste la table canonique locale, sans nouvelle colonne P2.
- `DocumentArchive` et les fichiers/documents locaux restent inchangés.
- table additive `patient_practitioner_assignments` : 0/1 attribution par patient ; aucun backfill forcé.
- praticien référent limité au même cabinet, actif, approuvé et assignable ; secrétaire exclue comme référent.
- `Acte.praticien_id` existant reste la source d'attribution de la production.
- encaissements attribués à un praticien uniquement lorsqu'un lien vers un acte est prouvable, directement ou via un échéancier lié à l'acte.
- paiements sans preuve de rattachement restent explicitement `unattributed_collected` ; aucune ventilation artificielle.
- formulaires Nouveau / Modifier patient restent indépendants du référent afin de ne pas alourdir les données locales historiques.

### BEFORE / AFTER

- BEFORE baseline : `85cc4ca39df3d1064e1d82bb3a6a7048dc3e6d80`.
- BEFORE visual `34685062932` : success.
- 12 captures Dossier / Finances / Modifier / Nouveau × 390x844 / 768x1024 / 1280x900.
- AFTER code HEAD certifié : `33f5e6cc4de8d8345c699088832994e7cdd886a6`.
- AFTER Visual P2 `34685916843` : success.
- T2 Runtime Browser `34685916888` : success.
- Patient P7 `34685916847` : success.
- CI principale `34685916864` : success.
- AFTER : 12/12 captures, 0 overflow horizontal, 0 runtime/page error selon le gate exact-head.
- défaut intermédiaire de placement/capture Finances 390 détecté visuellement puis corrigé avant certification finale.
- score visuel final : **9,2 / 10**.
- PR #433 mergée ; merge `191fd37f05f22770a5431c697bb4fa749f05baca`.
- référence détaillée : `docs/clinic/P2_PATIENT_PRACTITIONER_BILLING.md`.
- aucun déploiement Vercel.

## Gate cabinet réel — COMPATIBILITÉ UPGRADE — CERTIFIÉ / MERGÉ

### Pourquoi ce gate existe

Un premier rehearsal Codex en lecture seule sur la vraie installation cabinet a prouvé la conservation des Patients/Documents/médias, mais a détecté deux incompatibilités bloquantes de runtime :

1. `appointments.praticien_id` absent après startup historique car le runtime cabinet n'exécute pas automatiquement la chaîne Alembic ;
2. enum PostgreSQL historique sans `A_ENCAISSER`, provoquant HTTP 500 sur Finances.

Un troisième risque a été corrigé : seed superadmin automatique au démarrage cabinet.

### Correctifs certifiés

- self-migration ciblée et idempotente de `appointments.praticien_id` + index ;
- FK praticien vers `users(id)` en `ON DELETE SET NULL` ;
- alignement additif de l'enum PostgreSQL avec `A_ENCAISSER` ;
- `seed_admin_user()` interdit automatiquement en `cabinet` et `production` avant ouverture DB/génération de secret ;
- pas d'exécution forcée de toute la chaîne Alembic historique ;
- aucun backfill Patient/Document ;
- chemins DB/media inchangés.

### Preuves exact-head

Candidat certifié : `b4f213b7095e3a93b2b4b155700dee7881ead23d`.

- CI `34691089478` : success.
- T2 `34691089498` : success.
- PostgreSQL 18 certification `34691089505` : success.
- PR #439 mergée avec garde SHA exacte ; merge `f7e652acdae5454303d82a07c03e98a267b4a976`.
- `master` post-merge vérifié sur `f7e652acdae5454303d82a07c03e98a267b4a976`, commit GitHub signé/valide.

### Rehearsal Codex final sur copie fraîche de la vraie installation

Verdict : **GO INSTALLATION**.

Conservation vérifiée BEFORE/AFTER :

- Patients : 293 → 293 ; mêmes IDs/champs critiques ; hash inchangé `8297e1086f27bc6ff527b35f1d6c69ed6e46ca01aed74791ba3ef5b079027e23`.
- Documents DB : 395 → 395 ; mêmes IDs/champs critiques ; hash inchangé `5db831ecc8e1e347b8a6bba330729791094e58f040923802e523ac634533b153`.
- Relations patient-document : hash inchangé `b545fe8bf4386364939eafabb501d7b74c13131e61d048c0715737dfe880d45f`.
- Médias : 2 642 fichiers / 353 518 486 octets avant/après ; hash arbre média inchangé `2564dbb1a7d6d0d507a401f7480307800725bea8a7f0510fd51db6d394e6cfd8`.
- Actes : 281 → 281.
- Paiements : 212 → 212.
- Finances : HTTP 200 après correction enum.
- Scheduler : aucune erreur `UndefinedColumn`, aucun `Daily scheduler failed`.
- attribution/désattribution praticien sur copie : Patient et `DocumentArchive` inchangés.
- seed admin en `cabinet` : utilisateurs 12 → 12, admins 3 → 3, aucun mot de passe généré/imprimé.

Anomalies historiques hors périmètre du changement : 2 247 médias physiques non référencés ; aucune modification par le candidat.

Référence : `docs/clinic/CABINET_UPGRADE_COMPATIBILITY_GATE.md`.

## P3 — Documents, auteurs et signatures — IMPLÉMENTÉ / MERGÉ, CLOSEOUT EN COURS

### Goal

Ajouter une provenance clinique multi-praticiens et une signature praticien applicative liée aux octets archivés, sans déplacer ni réécrire les documents locaux historiques.

### Architecture mergée

- `uploaded_by_id` reste l'acteur technique ; `author_practitioner_id` représente l'auteur clinique.
- `author_practitioner_id`, `signed_by_practitioner_id`, `signed_at` sont additifs et nullable.
- aucun backfill historique ; provenance inconnue = `NULL`.
- auteur limité au même cabinet, actif, approuvé et assignable ; acteur non-praticien sans auteur explicite refusé.
- PDF généré avec l'identité de l'auteur sélectionné ; audit technique conservé séparément.
- signature autorisée uniquement à l'auteur exact d'un document canonique actif dont SHA-256/taille correspondent aux octets physiques.
- remplacement/régénération des octets invalide la signature antérieure.
- types document sans politique explicite de signature refusés fail-closed.
- aucune permission `sign_documents` supplémentaire : permission du type + auteur exact + praticien éligible + intégrité constituent le gate.
- signature = provenance applicative Digital Crown liée au SHA-256/taille ; **pas** une signature électronique qualifiée, PKI ou certificat.

### UI / preuves

- PR #454 provenance backend : merge `04304b7f5428d3c684e54a7de71d76d135b6a3aa`.
- PR #455 Auteur clinique UI : merge `3fc3b0ac604b6a291000dc7c91915cb377713788` ; certification visuelle finale 10.0/10.
- PR #457 signature backend : merge `3b3152813b635393c880c8eb270772060e85e1f6`.
- PR #459 signature Archives UI : HEAD `3e0ca1f08ebbc5f19c28ac2e715cdf4e08480472`, merge `a213376114ca26cedfdb7a112f9320156cf88adb`.
- P3 Signature UI `34727387320` : success, score **10.0/10**, 390x844 / 768x1024 / 1280x900, 0 overflow/runtime error.
- Document History Actions AFTER `34727387326` : success à 390x844 et 1366x700.
- PostgreSQL `34727387310`, T2 `34727387337`, P2 Visual `34727387366`, CI `34727387334`, Patient P7 `34727387347` : success.
- aucun déploiement Vercel.

### Gate de préservation P3

PR #463 ajoute un gate exact-head reproductible sur vault synthétique local + PostgreSQL 18 isolé afin de prouver :

- self-migration provenance idempotente ;
- aucune attribution historique rétroactive ;
- conservation id/patient/path/hash/taille/statut ;
- signature metadata-only sans réécriture des octets ;
- maintien des protections fail-closed existantes.

Ce gate **n'est pas** présenté comme une nouvelle copie de données patient réelles. Le gate cabinet réel ci-dessus reste la preuve de conservation sur copie de l'installation réelle.

### Ressources physiques

Salles/fauteuils sont différés : aucun besoin workflow clinique démontré n'a justifié l'ajout d'un modèle ou d'une UI spéculative dans P3.

Référence détaillée : `docs/clinic/P3_DOCUMENT_PROVENANCE_SIGNATURES.md`.

## Différé

Multi-site : hors périmètre tant qu'un besoin produit réel et prioritaire n'est pas démontré.

## Références

- `docs/PATIENT_P3_CLINIQUE_GOAL.md` reste une référence complémentaire et ne doit pas être confondu avec ce P3 multi-praticiens.
- `docs/clinic/P1_MULTI_PRACTITIONER_UI.md` — spécification P1.
- `docs/clinic/P2_PATIENT_PRACTITIONER_BILLING.md` — spécification et preuves P2.
- `docs/clinic/P3_DOCUMENT_PROVENANCE_SIGNATURES.md` — architecture, claim boundary et preuves P3.
- `docs/clinic/CABINET_UPGRADE_COMPATIBILITY_GATE.md` — gate cabinet réel et procédure de certification.
- Chaîne Alembic : P0 `d3a55e700003`; P2 `e4a55e700004`; P3 provenance `f5a55e700005`, avec self-migrations ciblées pour compatibilité du runtime cabinet historique.

## Next exact

PR #463 : obtenir le gate préservation + CI/PostgreSQL/T2 verts, merger avec garde SHA, puis passer P3 à `CERTIFIÉ / MERGÉ`. Ensuite clôturer le chantier multi-praticiens à la frontière planifiée P3 ; multi-site et ressources physiques restent différés tant qu'un besoin produit réel n'est pas démontré.
