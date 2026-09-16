# Mutuelles dentaires — Integration Roadmap

Date de realignement: 2026-09-16
Repo: `hraaaaf/Digital_crown`
Branche de closeout courant: `docs/mutuelles-cnops-post-merge-closeout`
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

## FAR — LOT SUIVANT, GATE NON OUVERT

Handover:
`docs/audits/MUTUELLES_DENTAIRES_CNOPS_TO_FAR_HANDOVER.md`.

Prompt de nouvelle conversation:
`docs/audits/MUTUELLES_DENTAIRES_FAR_START_PROMPT.md`.

FAR doit reutiliser le meme moteur et repasser ses propres gates de provenance/template/politique administrative/profil overlay/UI/tests.

### Contrainte produit FAR — ordonnance séparée

Information explicite fournie par le cabinet:

**Le dossier/feuille de soins FAR contient une page d'ordonnance incluse dans le document. Cette page doit etre traitee separement des autres feuilles/pages FAR.**

Statut actuel:
- exigence produit/cabinet: confirmée;
- binaire FAR exact: non encore inspecté dans ce lot;
- SHA-256 FAR: non connu ici;
- nombre/index exact de la page ordonnance: non vérifié;
- coordonnées overlay ordonnance: non connues;
- trust/provenance FAR: à établir.

Le lot FAR ne doit donc pas coder à partir d'une hypothèse de pagination.

Principe architectural à confirmer après inspection du binaire:
- conserver le binaire FAR original verrouillé par SHA-256;
- classifier les pages par rôle;
- traiter l'ordonnance comme un sous-document logique séparé (`FAR_PRESCRIPTION` ou nom cohérent avec le code réel);
- contrat de données, profil overlay, revue praticien, validation/finalisation, tests et preuve visuelle séparés;
- aucune molécule, dose, posologie, durée ou fréquence déduite depuis les actes/NGAP;
- toute prescription provient d'une source explicite et est revue par le praticien;
- conserver la relation avec le dossier FAR global;
- un éventuel réassemblage pour impression/export ne peut intervenir qu'après validation indépendante des sous-documents.

### Premier gate FAR obligatoire

Avant implémentation:
1. identifier le binaire FAR exact;
2. calculer SHA-256, taille, pages et dimensions;
3. inspecter visuellement chaque page;
4. identifier le rôle de chaque page;
5. confirmer précisément la page ordonnance;
6. établir le trust réel de la source;
7. cartographier champs autorisés/interdits;
8. vérifier l'extension minimale du moteur commun;
9. créer `docs/audits/MUTUELLES_DENTAIRES_FAR_GATE.md`;
10. seulement ensuite commencer l'implémentation.

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

`CNSS_ACQUIRED / NGAP_REFERENCE_LOCKED_REFERENCE_ONLY / CNOPS_CLOSED_VERIFIED_POST_MERGE / FAR_SOURCE_GATE_NOT_STARTED / FAR_PRESCRIPTION_SEPARATE_GATE_REQUIRED`

## Next exact

1. merger le closeout documentaire après ses propres checks et accord utilisateur explicite;
2. ouvrir une nouvelle conversation avec `docs/audits/MUTUELLES_DENTAIRES_FAR_START_PROMPT.md`;
3. verifier master/CI actuels;
4. localiser le binaire FAR exact;
5. inspecter FAR page par page et confirmer l'ordonnance;
6. produire le gate FAR;
7. ne coder FAR qu'après ce gate.
