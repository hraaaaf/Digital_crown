# Mutuelles dentaires — Integration Roadmap

Date de realignement: 2026-09-16
Repo: `hraaaaf/Digital_crown`
Branche du lot courant: `feature/mutuelles-cnops-20260916`
PR courante: `#534`

## Goal global

Un workflow unique de feuille de soins dentaire CNSS/CNOPS/FAR a partir des donnees existantes Digital Crown, avec validation praticien, tracabilite NGAP, template exact verrouille et archivage reproductible dans `DocumentArchive`, sans dupliquer Honoraires, `CatalogAct` ni l'archive documentaire.

UX cible:

`Patient -> Honoraires -> Preparer organisme -> Revue praticien -> Validation -> PDF -> DocumentArchive`

## Architecture verrouillee

- un seul moteur Mutuelles;
- Honoraires reste la source financiere;
- `CatalogAct` reste le catalogue clinique;
- `ngap_catalog_mappings` reste la couche reglementaire versionnee;
- `DocumentArchive` reste l'archive documentaire;
- aucun fuzzy mapping NGAP;
- aucun backfill artificiel;
- aucune signature/cachet/decision assureur fabrique;
- toute donnee inconnue reste fail-closed;
- chaque template finalisable est lie a des octets exacts et a un SHA-256;
- chaque profil overlay est lie a `organization + template_version + template_hash` exacts;
- reimpression historique depuis le snapshot/profil archive, jamais depuis un recalcul implicite courant.

## Moteur commun — ACQUIS

Briques partagees CNSS/CNOPS:

- `InsuranceSubmissionDraft`;
- preparation depuis Honoraires;
- coherence serveur Honoraires/Acte;
- `source_line_uid` / `catalog_act_id`;
- resolution NGAP serveur sans fuzzy matching;
- source store local immuable et hash-addressed;
- validation praticien;
- revalidation anti-stale;
- renderer PDF overlay hash-bound;
- hash PDF final;
- archivage `DocumentArchive` avec preuve de rendu.

`SECONDARY_REFERENCE` reste insuffisant pour finaliser. Le trust final acceptable reste `OFFICIAL_PRIMARY` ou `CABINET_VALIDATED_BINARY` avec provenance explicite.

## NGAP dentaire — REFERENCE VERROUILLEE / RUNTIME NON AUTO-CERTIFIE

Fichier canonique: `docs/audits/MUTUELLES_NGAP_DENTAL_REFERENCE.md`.

Source verrouillee:

- B.O. n°5414 / arrete 177-06;
- fichier `bo_5414_fr.pdf`;
- SHA-256 `e9db137d6a758bd4ad7a506a94a7c0c84726813de3db1e225c761318a75e1fdb`.

Dataset actuel: 145 entrees (`D600-D641`, `D700-D785`, `D800-D816`).

Statut volontaire: `REFERENCE_ONLY_NOT_RUNTIME_CERTIFIED`. Aucun mapping runtime n'est auto-certifie depuis ce JSON.

## CNSS 610-1-04 — ACQUIS

CNSS a ete merge via PR `#493`.

Binaire cabinet valide:

- version `CNSS-610-1-04`;
- 2 pages;
- SHA-256 `e1fb63afb1893886d518135dfb209f24f2464e8cd664e89881fc7c373854864d`;
- trust `CABINET_VALIDATED_BINARY`.

Profil:

- `backend/services/insurance_cnss_610_1_04_profile.py`;
- version `cnss-610-1-04-e1fb63af-v2`;
- capacite 3 lignes;
- zone superieure assure volontairement non remplie;
- aucune coordonnee signature/cachet/decision assureur.

UI CNSS acquise: `Preparer CNSS -> revue -> validation -> finalisation -> archivage`, avec preuves multi-viewport et validation humaine avant merge.

## CNOPS — IMPLEMENTATION ACQUISE / CERTIFICATION FINALE EN COURS

Fichier canonique du lot: `docs/audits/MUTUELLES_DENTAIRES_CNOPS_GATE.md`.

### Binaire

Le cabinet a valide explicitement le 2026-09-16 le binaire exact:

- SHA-256 `89097caca32aef6b4d34d2d06fb9cc6f9bdc1f3c4385cf5558b5742a3af6f505`;
- 2 pages A4 paysage;
- trust limite a `CABINET_VALIDATED_BINARY`;
- template version `CNOPS-DENTAL-CABINET-2026-09-16`.

Cette validation ne vaut pas `OFFICIAL_PRIMARY`.

### Backend

Acquis dans le lot:

- politique administrative CNOPS explicite et fail-closed;
- affiliation assure modelisee separement;
- source store exact/hash-bound;
- profil overlay CNOPS lie au SHA valide;
- capacite 9 lignes;
- router commun CNSS/CNOPS pour prepare/validate/finalize;
- revalidation serveur avant finalisation;
- zones signature/cachet/mutuelle/agent exclues;
- tests backend CNOPS + non-regression des contrats partages.

### Frontend

Acquis dans le lot:

- action `Preparer CNOPS` dans le flow partage;
- composant `CnopsInsuranceSubmissionReview`;
- saisie explicite des donnees assure/beneficiaire;
- revue des lignes cliniques/NGAP en lecture seule;
- action CNSS conservee;
- tests de contrat CNOPS/CNSS.

### Preuve visuelle

Certification runtime reelle du composant React sous Chromium deja acquise sur l'ancien HEAD certifie `2acc3b1214219dc57897eb7388cda4065da2fb43`:

- `Mutuelles CNOPS Visual Certification #1`: SUCCESS;
- `390x844`, `768x1024`, `1280x900`;
- aucune erreur runtime/overflow sur la preuve inspectee;
- validation visuelle humaine explicite acquise le 2026-09-16.

Le HEAD final rebased doit etre recertifie; l'ancienne preuve ne suffit pas seule au merge.

### Rebase non-regressif

Le lot a ete reconstruit au-dessus du master courant plutot que fusionne avec un arbre ancien.

Base de reconstruction verifiee:

- `master@63d3902656d0525dccac60cbc15cf2aa21b1ffd9`;
- tree `af33ffcf33fb9d561e6e9cb42cf156d9ec4d7586`.

Implementation rebasee avant closeout documentaire:

- `70bcff19086f691df224ba4ca47512743027b6f6`;
- `ahead_by=1`;
- `behind_by=0`;
- exactement 21 fichiers modifies, tous dans le perimetre CNOPS/assurance;
- aucune suppression Agenda/Cephalo/Patient Companion.

Ancien HEAD conserve sur `backup/mutuelles-cnops-pre-rebase-20260916`.

### Gate restant CNOPS

Un seul gate technique reste avant passage ready:

`HEAD final closeout -> CI + CNOPS Visual + non-regressions pertinentes -> PR mergeable sans divergence`.

Le merge reste interdit sans accord explicite utilisateur.

## FAR — LOT SUIVANT, NON OUVERT

FAR reste hors scope de PR #534. Il doit reutiliser le meme moteur et repasser ses propres gates de provenance/template/politique administrative/profil overlay/UI/tests.

## Non-regression obligatoire

Avant merge CNOPS, prouver:

- aucune mutation schema/DB non maitrisee;
- aucun dommage donnees patients/documents;
- CNSS prepare/validate/finalize/archive reste fonctionnel;
- source store/hash gates restent fail-closed;
- NGAP reste non fuzzy et non auto-certifie;
- signatures/cachets/decision assureur restent hors rendu automatique;
- aucun fichier de domaines paralleles n'est retire par la reconstruction du lot.

## Interdits

Second moteur Honoraires, second catalogue clinique, fuzzy mapping, backfill artificiel, signature/cachet/accord assureur fabrique, promotion silencieuse d'un template secondaire, mutation production, deploiement Vercel sans autorisation explicite, merge sans accord explicite utilisateur.

## Etat courant

`CNSS_ACQUIRED / NGAP_REFERENCE_LOCKED_REFERENCE_ONLY / CNOPS_BINARY_CABINET_VALIDATED / CNOPS_BACKEND_IMPLEMENTED / CNOPS_UI_IMPLEMENTED / CNOPS_VISUAL_HUMAN_VALIDATED / CNOPS_REBASED_ON_CURRENT_MASTER / FINAL_EXACT_HEAD_CERTIFICATION_REQUIRED / FAR_NOT_STARTED`

## Next exact

1. recertifier le HEAD final apres closeout documentaire;
2. verifier CI, CNOPS Visual et non-regressions pertinentes;
3. verifier PR #534 `mergeable`, `behind_by=0` et perimetre intact;
4. passer PR #534 en ready si tout est vert;
5. attendre l'accord explicite de merge;
6. merger, verifier post-merge et produire le handover FAR.
