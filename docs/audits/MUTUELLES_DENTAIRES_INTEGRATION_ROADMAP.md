# Mutuelles dentaires — Integration Roadmap

Date: 2026-09-14
Branch: `feature/mutuelles-dentaires-integration-v2-20260914`
PR: `#493`

## Goal
Integrer un workflow unique de feuille de soins CNSS/CNOPS/FAR a partir des donnees existantes Digital Crown, avec validation praticien, tracabilite NGAP et archivage du PDF final dans le dossier patient, sans dupliquer Honoraires, Ordonnance, CatalogAct ni DocumentArchive.

## UX cible verrouillee
`Patient -> Honoraires -> Preparer feuille de soins -> Revue/validation -> PDF -> DocumentArchive`

- CTA principal depuis une note d'honoraires lorsque le patient a un organisme compatible.
- Acces secondaire depuis Documents sur une note d'honoraires existante.
- Ecran intermediaire obligatoire: identite, assure/beneficiaire, INPE, actes, dents, honoraires, NGAP, champs manquants.
- Ambiguite NGAP = choix praticien, jamais fuzzy matching silencieux.
- Generation finale uniquement apres validation explicite du praticien.
- PDF final archive automatiquement dans le dossier patient.
- Reimpression historique depuis le snapshot archive, jamais recalcul implicite avec un nouveau referentiel.

## Strategie archive P0
Pas de nouvel enum SQL immediatement:
- `DocumentType.AUTRE`;
- tags `insurance_submission`, organisme, version template;
- `clinical_data.kind = INSURANCE_SUBMISSION`;
- snapshot complet `InsuranceSubmissionDraft` + provenance Honoraires + template/version/hash + NGAP/version + validation praticien.

Un type documentaire dedie ne sera ajoute qu'apres migration additive testee.

## Roadmap / etat

### Lot 1 — Contrat runtime pur — IMPLEMENTE
`InsuranceSubmissionDraft` type, deterministe et fail-closed.
Preuve code: schema dedie + tests EXACT/AMBIGUOUS/NO_MATCH/validation.

### Lot 2 — Adaptateur Honoraires -> Draft — IMPLEMENTE
Construction depuis `DocumentArchive.clinical_data.payments[*]` et les `Acte` derives.
Preuve code: dents depuis snapshot; mismatch historique fail-closed.

### Lot 3 — Archivage PDF valide — IMPLEMENTE
Archivage du PDF final dans `DocumentArchive` uniquement apres validation praticien.
Preuve code: snapshot/tags/provenance, ArchiveService, test de hash fichier.

### Lot 4 — Liaison structuree actes/catalogue — IMPLEMENTE
Cible additive: `source_line_uid` immuable + `catalog_act_id` nullable.
Implementation:
- extension ORM additive de `Acte`;
- migration idempotente au `create_all()` pour DB historiques;
- aucun backfill;
- UID genere pour toute nouvelle ligne Honoraires et snapshotte dans `DocumentArchive` quand l'archive canonique existe;
- edition avec UID explicite matchee par UID; historique sans UID conserve fallback index controle;
- `catalog_act_id` accepte uniquement si `CatalogAct` actif existe;
- suppression/shrink ne reactive jamais une ancienne ligne soft-deleted;
- rollback physique disponible pour certification/tests, jamais execute automatiquement.

Regression CI observee sur CI #4031:
- test legacy `test_edit_honoraires_replaces_amount_lines_and_business_date` appelait directement `persist_honoraires_lines()` avec un document id non archive;
- la premiere implementation exigeait l'archive pour snapshotter l'UID et cassait cette primitive interne;
- correction commit `49111ea62f2f33c7d0b55a56c7b1231e0ba31cd3`: snapshot archive si elle existe, compatibilite service directe sinon;
- aucune relaxation du flux document reel: lorsqu'une note est generee/archivée, l'UID reste persiste dans `DocumentArchive` + `Acte`.

### Lot 5 — Referentiel NGAP local versionne — MOTEUR IMPLEMENTE / DONNEES PRIMAIRES NON ACTIVEES
Architecture:
- `CatalogAct` reste la source clinique unique;
- table additive `ngap_catalog_mappings` = couche reglementaire versionnee, vide par defaut;
- liaison explicite `catalog_act_id + reference_version`;
- `code_kind = NGAP | INTERNAL | OTHER`;
- NGAP: code, coefficient, libelle officiel, flags accord/radiographie, rule id;
- provenance: autorite, URL, SHA-256, validite, statut;
- `VERIFIED_PRIMARY` impose un SHA-256 de 64 caracteres au niveau DB;
- aucun parsing de `CatalogAct.code`, car ce champ legacy peut contenir NGAP ou interne;
- aucun fuzzy matching par libelle.

Resolution:
- `PRIMARY_HASH_PENDING` / source non verrouillee / reference expiree => `OUTDATED`;
- code non-NGAP ou absence de mapping => `NO_MATCH`;
- `EXACT` uniquement par mapping explicite `CatalogAct.id`, version primaire `VERIFIED_PRIMARY`, SHA-256 verrouille et periode valide;
- `apply_ngap_reference_to_draft()` applique la version a toutes les lignes et conserve version/hash;
- plusieurs hashes sous une meme version => blocage;
- toutes les lignes EXACT + aucun champ restant => `READY_FOR_REVIEW`, sinon `INCOMPLETE`;
- toute reappplication invalide une validation praticien anterieure.

Sources primaires/corroborantes recroisees:
- Ministere de la Sante et de la Protection Sociale: arrete n°177-06 du 27/01/2006, B.O. n°5414 du 20/04/2006;
- data.gov.ma: ressource NGAP correspondant a l'arrete;
- CNOPS: nomenclature / arrete 177-06;
- ONMD communique 01/26 du 02/02/2026: utilisation appropriee NGAP + TNR;
- ONMD: referentiel medico-administratif des actes dentaires;
- ANAM: convention nationale chirurgiens-dentistes et arretes applicables.

Blocage primaire reel:
- les endpoints PDF primaires testes ont renvoye 403/502/timeout selon la source;
- impossible de recuperer reproductiblement les octets du binaire officiel dans cette session;
- donc aucun SHA-256 officiel n'est invente et aucune ligne de production n'est marquee `VERIFIED_PRIMARY`.

### Lot 6 — Renderer CNSS — GATE IMPLEMENTE / RENDU BLOQUE PAR TEMPLATE
Ordre futur: CNSS `610-1-04` -> CNOPS -> FAR.

Gate `assert_insurance_render_ready()` implemente:
- draft `VALIDATED` obligatoire;
- template PDF binaire obligatoire;
- SHA-256 template attendu = hash reel des octets;
- reference NGAP version + SHA-256 obligatoires;
- toutes les lignes `EXACT` avec code/rule tracables;
- mismatch => blocage avant rendu.

Reference CNSS `610-1-04` deja validee comme reference cabinet. Des copies secondaires confirment le formulaire bilingue et sa structure, mais aucun binaire officiel CNSS techniquement recuperable et verrouillable n'a encore ete obtenu. Les coordonnees de rendu ne seront donc pas inventees.

### Lot 7 — UX/UI
Obligatoire: BEFORE -> Goal -> mockup/reference -> implementation -> AFTER memes viewports -> comparaison/tests -> score visuel.
Success: generation depuis Honoraires et Documents sans nouveau sous-systeme.

### Lot 8 — Gate cabinet
Activation seulement si:
- template CNSS/CNOPS/FAR binaire + hash verrouilles;
- NGAP primaire versionne et hash verrouille;
- mappings metier representatifs valides;
- migration/rollback testes;
- archivage/reimpression verifies;
- rendu/UX certifies.

## CI connue
CI #4031: **FAILURE** sur une regression de compatibilite de `persist_honoraires_lines`; cause identifiee et corrigee par `49111ea...`.
Sur ce meme ancien HEAD: PostgreSQL #457, provenance #47 et browser #2942 etaient **SUCCESS**.
Le HEAD courant doit etre recertifie apres les commits NGAP/render-gate plus recents.

## Ordre restant
`recertification HEAD -> verrouillage binaire NGAP -> population/validation NGAP reelle -> verrouillage template CNSS -> renderer CNSS -> BEFORE/mockup -> UX -> AFTER/tests -> CNOPS/FAR -> gate cabinet`

## Interdits
Second moteur Honoraires, second catalogue clinique, Ordonnance bis, fuzzy mapping silencieux, backfill artificiel, signature/cachet/accord assureur fabrique, auto-cotation sans source primaire hashée, rendu approximatif d'un formulaire officiel, deploiement Vercel sans autorisation explicite.

## Etat
`LOTS_1_4_IMPLEMENTED / LOT_5_ENGINE_IMPLEMENTED_SOURCE_DATA_PENDING / RENDER_GATE_IMPLEMENTED / PRIMARY_HASH_PENDING / CNSS_TEMPLATE_BINARY_PENDING / CI_PENDING / RUNTIME_NOT_ACTIVATED`

## Next exact
Recertifier le HEAD courant. En parallele, reprendre le verrouillage du binaire primaire NGAP et du template CNSS uniquement via des sources officielles/reproductibles. Apres hash primaire NGAP: peupler un premier echantillon de mappings dentaires, validation metier, puis renderer CNSS `610-1-04`.
