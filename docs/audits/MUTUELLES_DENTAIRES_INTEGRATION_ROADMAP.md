# Mutuelles dentaires — Integration Roadmap

Date de realignement: 2026-09-16
Repo: `hraaaaf/Digital_crown`
Branche gate FAR courante: `audit/mutuelles-far-source-gate-20260916`
PR CNOPS: `#534` — MERGED
Merge CNOPS: `5290df7cb1a12989ef3799f92e32fd49d02d5ca1`

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

Briques partagees CNSS/CNOPS et a reutiliser pour FAR:

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

## CNOPS — CLOS / VERIFIED POST-MERGE

Gate historique du lot:
`docs/audits/MUTUELLES_DENTAIRES_CNOPS_GATE.md`.

Closeout final:
`docs/audits/MUTUELLES_DENTAIRES_CNOPS_CLOSEOUT.md`.

### Binaire

Le cabinet a valide explicitement le 2026-09-16 le binaire exact:

- SHA-256 `89097caca32aef6b4d34d2d06fb9cc6f9bdc1f3c4385cf5558b5742a3af6f505`;
- 2 pages A4 paysage;
- trust limite a `CABINET_VALIDATED_BINARY`;
- template version `CNOPS-DENTAL-CABINET-2026-09-16`.

Cette validation ne vaut pas `OFFICIAL_PRIMARY`.

### Backend acquis

- politique administrative CNOPS explicite et fail-closed;
- affiliation assure modelisee separement;
- source store exact/hash-bound;
- profil overlay CNOPS lie au SHA valide;
- capacite 9 lignes;
- router commun CNSS/CNOPS pour prepare/validate/finalize;
- revalidation serveur avant finalisation;
- zones signature/cachet/mutuelle/agent exclues;
- tests backend CNOPS + non-regression des contrats partages.

### Frontend acquis

- action `Preparer CNOPS` dans le flow partage;
- composant `CnopsInsuranceSubmissionReview`;
- saisie explicite des donnees assure/beneficiaire;
- revue des lignes cliniques/NGAP en lecture seule;
- action CNSS conservee;
- tests de contrat CNOPS/CNSS.

### Certification exacte avant merge

HEAD final certifie:
`7d48357c312ca8447f55b5986b0c50454f954ab7`.

Base master au gate final:
`35c4ee606e953f2f2a8a9d91ab540bf6c7ef476a`.

Comparaison:
- `ahead_by=1`;
- `behind_by=0`;
- exactement 21 fichiers dans le perimetre CNOPS/assurance.

Workflows exact-HEAD:
- CI #4655 — SUCCESS;
- T2 Runtime Browser Certification #3513 — SUCCESS;
- Patient P7 Final Certification #1773 — SUCCESS;
- Patient UX1-C Overlay Visual Certification #222 — SUCCESS;
- Clinic P2 Patient Billing Visual Certification #265 — SUCCESS;
- Mutuelles CNOPS Visual Certification #14 — SUCCESS;
- PR Merge Summary #124 — SUCCESS.

Workflow CNOPS #14:
- `capture` — SUCCESS;
- `backend-contract` — SUCCESS;
- artifact `10457336943`;
- digest `sha256:f92f88100cced08d863d9206ca1faa17a70963e0ce69b87ba97cb697253c2476`.

Validation visuelle humaine explicite acquise le 2026-09-16.

### Merge et post-merge

PR #534 mergée après accord utilisateur explicite.

Merge commit:
`5290df7cb1a12989ef3799f92e32fd49d02d5ca1`.

CI push post-merge sur ce commit:
- CI #4674 / run `35126199252` — SUCCESS;
- Full backend regression DB/patients/documents — SUCCESS;
- Frontend tests & build — SUCCESS;
- Garde production négative — SUCCESS.

Cabinet Upgrade PostgreSQL Certification #925:
- Windows PowerShell 5.1 release guards — SUCCESS;
- PostgreSQL 18 + immutable release invariants — SUCCESS.

Aucun déploiement Vercel et aucune mutation production dans ce lot.

Score final CNOPS:
- EXECUTION_SCORE 9.4/10;
- ADVERSARIAL_SCORE 9.4/10;
- retenu 9.4/10, plafonné car exécution et revue adversariale par le même agent.

Statut:
`CNOPS_CLOSED_VERIFIED_POST_MERGE`.

## FAR — SOURCE GATE OUVERT / BLOQUE SUR BINAIRE EXACT

Handover:
`docs/audits/MUTUELLES_DENTAIRES_CNOPS_TO_FAR_HANDOVER.md`.

Prompt de reprise:
`docs/audits/MUTUELLES_DENTAIRES_FAR_START_PROMPT.md`.

Gate courant:
`docs/audits/MUTUELLES_DENTAIRES_FAR_GATE.md`.

FAR doit reutiliser le meme moteur et repasser ses propres gates de provenance/template/politique administrative/profil overlay/UI/tests.

### Contrainte produit FAR — ordonnance séparée

Information explicite fournie par le cabinet:

**Le dossier/feuille de soins FAR contient une page d'ordonnance incluse dans le document. Cette page doit etre traitee separement des autres feuilles/pages FAR.**

État vérifié du source gate:
- exigence produit/cabinet: confirmée;
- binaire FAR exact: absent du repo, du Drive connecté et de la File Library après recherche;
- copies publiques secondaires concordantes: localisées, mais non promues en source de confiance;
- SHA-256 FAR exact: non acquis;
- nombre/index PDF exact de la page ordonnance: non acquis;
- dimensions/champs AcroForm/XFA: non acquis;
- coordonnées overlay ordonnance: interdites tant que le binaire exact manque;
- trust/provenance FAR: non établi pour un SHA exact.

Le lot FAR ne doit donc pas coder à partir d'une hypothèse de pagination.

Principe architectural verrouillé:
- conserver le binaire FAR original verrouillé par SHA-256;
- classifier les pages par rôle sur ce binaire exact;
- traiter l'ordonnance comme une surface clinique logique séparée;
- utiliser une source explicite de prescription liée au dossier FAR;
- aucune molécule, dose, posologie, durée ou fréquence déduite depuis les actes/NGAP/Honoraires;
- conserver la relation avec le dossier FAR global;
- un éventuel réassemblage pour impression/export ne peut intervenir qu'après validation indépendante des sous-documents.

### Source gate FAR

Le gate a été matérialisé avant tout code dans `docs/audits/MUTUELLES_DENTAIRES_FAR_GATE.md`.

Verdict courant:
`NO_GO_IMPLEMENTATION_SOURCE_BINARY_REQUIRED`.

Constats structurants:
- l'entrée historique `FAR_2021_1` du registre est un placeholder et ne prouve pas qu'un binaire FAR exact a été validé;
- `expected_page_count=None` ne permet aucune validation de pagination;
- la validation serveur actuelle possède des politiques administratives CNSS/CNOPS mais rejette FAR comme non implémenté;
- le schéma commun expose déjà `source_ordonnance_document_id`, utilisable comme point de liaison explicite sans fabriquer de prescription.

Human gate exact:
- fournir/acquérir le PDF FAR exact actuellement utilisé/accepté par le cabinet, idéalement non recompressé;
- calculer son SHA-256;
- inspecter nativement pages, dimensions, orientation, AcroForm/XFA et champs;
- confirmer le rôle de chaque page et l'ordonnance;
- documenter la validation cabinet/praticien si la source n'est pas officielle primaire;
- seulement alors choisir provider fields/overlay/mixte et passer le gate en GO ou NO-GO définitif.

## Non-regression obligatoire pour FAR

Avant merge FAR, prouver:

- aucune mutation schema/DB non maitrisee;
- aucun dommage donnees patients/documents;
- CNSS prepare/validate/finalize/archive reste fonctionnel;
- CNOPS prepare/validate/finalize/archive reste fonctionnel;
- source store/hash gates restent fail-closed;
- NGAP reste non fuzzy et non auto-certifie;
- signatures/cachets/decision assureur restent hors rendu automatique;
- ordonnance FAR reste un gate distinct des autres pages;
- aucun fichier de domaines paralleles n'est retire par le lot.

## Interdits

Second moteur Honoraires, second catalogue clinique, fuzzy mapping, backfill artificiel, prescription inventee, signature/cachet/accord assureur fabrique, promotion silencieuse d'un template secondaire, mutation production, deploiement Vercel sans autorisation explicite, merge sans accord explicite utilisateur.

## Etat courant

`CNSS_ACQUIRED / NGAP_REFERENCE_LOCKED_REFERENCE_ONLY / CNOPS_CLOSED_VERIFIED_POST_MERGE / FAR_SOURCE_GATE_BLOCKED_ON_EXACT_BINARY / FAR_PRESCRIPTION_SEPARATE_GATE_REQUIRED`

## Next exact

1. acquérir le PDF FAR exact du cabinet;
2. calculer SHA-256 et taille;
3. inspecter nativement pages/dimensions/orientations/AcroForm/XFA;
4. confirmer la correspondance page logique <-> index PDF et la page ordonnance;
5. documenter provenance + validation cabinet;
6. mettre à jour `MUTUELLES_DENTAIRES_FAR_GATE.md` avec le verdict GO/NO-GO;
7. uniquement si GO, ouvrir le lot d'implémentation FAR.
