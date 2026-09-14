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
- Ecran intermediaire obligatoire: assure/beneficiaire, INPE, nature demande, type de soins, actes, dents, honoraires, NGAP, champs manquants.
- Ambiguite ou donnee absente = saisie/validation praticien, jamais inference silencieuse.
- Generation finale uniquement apres validation explicite du praticien.
- PDF final archive automatiquement dans le dossier patient.
- Reimpression historique depuis le snapshot archive, jamais recalcul implicite avec un nouveau referentiel.

## Strategie archive P0
Pas de nouvel enum SQL immediatement:
- `DocumentType.AUTRE`;
- tags `insurance_submission`, organisme, version template;
- `clinical_data.kind = INSURANCE_SUBMISSION`;
- snapshot complet `InsuranceSubmissionDraft` + provenance Honoraires + template/version/hash/trust + NGAP/version/hash + validation praticien.

## Lot 1 — Contrat runtime — IMPLEMENTE
`InsuranceSubmissionDraft` fail-closed.

Invariants:
- `READY_FOR_REVIEW`: toutes lignes NGAP EXACT + aucun champ non resolu;
- `VALIDATED`: conditions precedentes + praticien/date + template SHA-256/provenance + trust `OFFICIAL_PRIMARY|CABINET_VALIDATED_BINARY` + version/hash NGAP;
- `SECONDARY_REFERENCE` ne peut jamais devenir un document final valide;
- aucune archive finale depuis un draft non `VALIDATED`.

Le snapshot administratif comprend maintenant:
- nature demande `EXECUTION|PRIOR_APPROVAL`;
- assure: nom, immatriculation, CIN, adresse, qualite;
- beneficiaire: nom, naissance, CIN, sexe, lien;
- praticien: nom, INPE;
- type soins `SOINS|PROTHESE|ORTHODONTIE_FACIALE|AUTRES`;
- entente prealable, accident, pieces jointes.

## Lot 2 — Honoraires -> Draft — IMPLEMENTE
- source: `DocumentArchive.clinical_data.payments[*]` + `Acte` derives;
- dents depuis snapshot;
- mismatch historique fail-closed;
- `source_line_uid` stable + `catalog_act_id` explicite.

### Regression CI liaison JSON
CI #4065 a trouve que l'UID etait bien cree dans `Acte` mais pas durablement persiste dans `DocumentArchive.clinical_data` a cause de mutations JSON imbriquees partagees.
Correction `6a4778f8c1cd03b7a45c3284b1ec0f7fa2aa9018`:
- reconstruction snapshot;
- `flag_modified(archive, "clinical_data")` apres mise a jour;
- aucun retour a l'exigence d'une archive pour les appels service legacy.
Le HEAD final doit recertifier cette preuve.

## Lot 3 — Archivage PDF final — IMPLEMENTE
- uniquement draft `VALIDATED`;
- PDF final archive dans `DocumentArchive`;
- snapshot/tags/provenance complets;
- hashes template + NGAP + trust template conserves;
- reimpression historique fondee sur snapshot, pas sur le referentiel courant.

## Lot 4 — Liaison actes/catalogue — IMPLEMENTE
- `Acte.source_line_uid` nullable;
- `Acte.catalog_act_id` nullable FK `CatalogAct`;
- migration additive/idempotente, aucun backfill artificiel;
- rollback certification disponible;
- edition par UID, fallback index uniquement historique;
- CatalogAct inconnu/inactif => fail-closed.

## Lot 5 — NGAP versionnee — MOTEUR IMPLEMENTE / DONNEES PRIMAIRES NON ACTIVEES
`CatalogAct` reste le catalogue clinique. `ngap_catalog_mappings` est uniquement la couche reglementaire versionnee.

Double gate `VERIFIED_PRIMARY`:
1. PDF primaire lisible + marqueurs juridiques `177-06` et `nomenclature generale des actes professionnels` + SHA-256;
2. mapping explicitement valide par praticien actif (`validated_by_practitioner_id`, `validated_at`).

Runtime:
- source non verrouillee / mapping non valide / expiration => `OUTDATED`;
- absence/non-NGAP => `NO_MATCH`;
- `EXACT` uniquement via `CatalogAct.id + reference_version`, jamais `CatalogAct.code` ou fuzzy label;
- plusieurs hashes pour la meme version => blocage.

Sources recroisees:
- Ministere Sante: arrete 177-06 du 27/01/2006;
- SGG: BO 5414 du 20/04/2006;
- data.gov.ma: ressource NGAP;
- CNOPS: nomenclature 177-06;
- ONMD 01/26 du 02/02/2026: NGAP + TNR;
- ANAM: convention/arretes chirurgiens-dentistes.

Blocage externe: endpoints PDF primaires 403/502/timeout/cache miss; aucun hash officiel invente.

## Lot 5B — Store local immuable des sources — IMPLEMENTE
Objectif: ne pas dependre du reseau officiel au runtime cabinet.

`insurance_source_store.py`:
- validation source AVANT stockage;
- stockage hash-addressed `namespace/version/sha256/source.pdf`;
- `manifest.json` deterministe;
- ecriture atomique;
- collision octets/manifest => blocage;
- NGAP passe obligatoirement par le controle identite juridique;
- template passe par controle PDF/pages/hash/trust;
- `CABINET_VALIDATED_BINARY` exige l'identite explicite du validateur dans le manifeste.

Commande locale:
`scripts/lock_insurance_source.py`
- `--kind ngap|cnss|cnops|far`;
- fichier local + provenance;
- CNSS/FAR cabinet-valide exige `--confirm-cabinet-validation --validated-by "..."`;
- aucun binaire n'a encore ete promu faute de fichier source exact disponible.

## Lot 6 — CNSS 610-1-04 — PREPARATION IMPLEMENTEE / RENDERER BLOQUE PAR BINAIRE
Reference cabinet validee: `CNSS-610-1-04`, 2 pages attendues.

Gate renderer:
- draft `VALIDATED`;
- template PDF exact;
- hash octets = hash snapshot;
- template trust accepte;
- version/hash NGAP;
- toutes lignes EXACT.

Aucune coordonnee PDF de rendu n'est inventee avant verrouillage d'un binaire exact.

### Politique administrative CNSS — IMPLEMENTEE
Le controle de completude 610-1-04 impose notamment assure, immatriculation, CIN, lien/adresse, beneficiaire, naissance/CIN/sexe, praticien/INPE, nature demande, type de soins et donnees d'actes.

`prefill_cnss_administrative()`:
- prefill uniquement faits deja explicites: nom beneficiaire, naissance, sexe, nom praticien;
- INPE uniquement si une cle legale explicitement nommee INPE/INP existe; aucun fallback;
- type de soins infere seulement si tous les `Acte` sources appartiennent a une unique categorie deterministe;
- note mixte => type reste manuel;
- patient.adresse n'est jamais copie dans adresse assure car beneficiaire != assure possible;
- aucune CIN, immatriculation, identite assure ou lien de parente invente;
- tous champs obligatoires absents deviennent `administrative.<field>` dans `unresolved_fields`.

## Lot 7 — UX/UI — A FAIRE APRES GATES BINAIRES/METIER
Protocole obligatoire:
`BEFORE -> Goal -> mockup/reference -> implementation -> AFTER memes viewports -> comparaison/tests -> score visuel`.

UX cible:
- CTA Honoraires;
- second acces Documents;
- ecran Preparation feuille de soins;
- champs pre-remplis vs manquants clairement differencies;
- revue NGAP et administrative;
- preview formulaire;
- validation praticien;
- generation + archive.

## Lot 8 — Gate cabinet
Activation seulement si:
- source NGAP primaire binaire/hash verrouillee;
- mappings representatifs valides par praticien;
- template assureur exact verrouille et trust acceptable;
- renderer certifie;
- migration/rollback, archivage/reimpression et UX certifies.

## CI connue
- CI #4031: regression appel service legacy, corrigee `49111ea...`.
- CI #4065 sur `1c01b94...`: **FAILURE** uniquement sur persistance `source_line_uid` dans JSON archive; 1655 tests passes avant arret; PostgreSQL #491, provenance #73, browser #2976 et Catalog #1149 **SUCCESS**.
- correctif exact: `6a4778f8...` (`flag_modified`).
- depuis ce correctif, plusieurs durcissements source-store/template/admin ont ete ajoutes; le HEAD final courant doit etre recertifie en une passe.

## Interdits
Second moteur Honoraires, second catalogue clinique, Ordonnance bis, fuzzy mapping, backfill artificiel, signature/cachet/accord assureur fabrique, auto-cotation sans source primaire hashée ET validation metier, template secondaire promu en final, rendu approximatif d'un formulaire officiel, deploiement Vercel sans autorisation explicite.

## Etat
`LOTS_1_4_IMPLEMENTED / NGAP_ENGINE_IMPLEMENTED_SOURCE_PENDING / LOCAL_SOURCE_STORE_IMPLEMENTED / TEMPLATE_TRUST_GATE_IMPLEMENTED / CNSS_ADMIN_PREFILL_IMPLEMENTED / RENDER_GATE_IMPLEMENTED / PRIMARY_HASH_PENDING / CNSS_TEMPLATE_BINARY_PENDING / CI_RECERTIFICATION_REQUIRED / RUNTIME_NOT_ACTIVATED`

## Next exact
1. Recertifier le HEAD courant et corriger toute regression.
2. Recuperer localement un binaire primaire NGAP exact -> lock/store/hash.
3. Valider un premier lot representatif de mappings NGAP par praticien.
4. Recuperer/verrouiller le binaire CNSS 610-1-04 exact.
5. Renderer CNSS fidele.
6. BEFORE/mockup -> UX -> AFTER/tests.
7. CNOPS/FAR -> gate cabinet -> closeout/merge.
