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
- snapshot complet `InsuranceSubmissionDraft` + provenance Honoraires + template/version/hash/trust + NGAP/version/hash + validation praticien + preuve de rendu.

## Lot 1 — Contrat runtime — IMPLEMENTE
`InsuranceSubmissionDraft` fail-closed.

Invariants:
- `READY_FOR_REVIEW`: toutes lignes NGAP EXACT + aucun champ non resolu;
- `VALIDATED`: conditions precedentes + praticien/date + template SHA-256/provenance + trust `OFFICIAL_PRIMARY|CABINET_VALIDATED_BINARY` + version/hash NGAP;
- `SECONDARY_REFERENCE` ne peut jamais devenir un document final valide;
- aucune archive finale depuis un draft non `VALIDATED`.

Le snapshot administratif comprend:
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
- `source_line_uid` stable + `catalog_act_id` explicite;
- liaison UID prioritaire, fallback index seulement historique;
- organisme demande doit correspondre a `Patient.assurance`.

### Regressions CI liaison/archive — CORRIGEES
1. CI #4065: UID cree dans `Acte` mais pas durablement marque dans le JSON archive. Correctif `6a4778f8...`: reconstruction snapshot + `flag_modified(archive, "clinical_data")`.
2. CI #4123 sur `7a01205e...`: la metadonnee technique `source_line_uid` enrichissant la premiere archive cassait ensuite la detection de doublon d'une note utilisateur identique; 1548 tests passes avant arret. Correctif: politique NOTE_HONORAIRES qui compare le contenu metier en ignorant uniquement `source_line_uid` et `catalog_act_id=None`, tout en conservant un vrai `catalog_act_id` comme identite significative. Tests dedies ajoutes.
3. CI #4139 sur `8d7415d9...`: fixture de validation reutilisait une instance `CatalogAct` expiree apres appel HTTP. Premier correctif: identite primitive conservee.
4. CI #4141 sur `b7aa96ce...`: cause racine transactionnelle confirmee; `/documents/generate` rend dans une seconde `SessionLocal` en thread, donc un `CatalogAct` seulement `flush()` n'etait pas visible. Correctif test uniquement: commit de la donnee de reference avant appel HTTP.
5. CI #4142 sur `1b8a7879...`: le gate arrivait ensuite jusqu'a la completude administrative et bloquait car la fixture ne renseignait explicitement que 7/13 champs CNSS obligatoires. Correctif `672133f6...`: fixture du test de validation rendue explicitement complete et independante du prefill.

## Lot 3 — Archivage PDF final — IMPLEMENTE
- uniquement draft `VALIDATED`;
- PDF final archive dans `DocumentArchive`;
- snapshot/tags/provenance complets;
- hashes template + NGAP + trust template conserves;
- preuve renderer conservee: version, profil complet de coordonnees, hash profil, hash template, hash PDF final;
- reimpression historique fondee sur le snapshot + profil archive, pas sur le referentiel courant.

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
- SGG/DIO: BO 5414 du 20/04/2006;
- data.gov.ma: ressource NGAP, producteur CNOPS;
- CNOPS: nomenclature 177-06;
- ONMD 01/26 du 02/02/2026: NGAP + TNR;
- ANAM: convention/arretes chirurgiens-dentistes.

Blocage externe: les sources officielles sont identifiees, mais les octets exacts du PDF primaire ne sont pas recuperables de facon reproductible depuis l'environnement actuel (timeouts/403/DNS/cache miss). Aucun hash officiel invente. La File Library et Google Drive ont ete recherches: aucun binaire `177-06`/NGAP primaire n'y est present; seul le communique ONMD 01/26 est present sur Drive comme corroboration.

## Lot 5B — Store local immuable des sources — IMPLEMENTE
`insurance_source_store.py`:
- validation source AVANT stockage;
- stockage hash-addressed `namespace/version/sha256/source.pdf`;
- `manifest.json` deterministe;
- ecriture atomique;
- lecture avec revalidation SHA + identite manifeste;
- collision/alteration => blocage;
- NGAP passe par le controle identite juridique;
- template passe par controle PDF/pages/hash/trust;
- `CABINET_VALIDATED_BINARY` exige l'identite explicite du validateur dans le manifeste.

Commande locale `scripts/lock_insurance_source.py`:
- `--kind ngap|cnss|cnops|far`;
- fichier local + provenance;
- CNSS/FAR cabinet-valide exige `--confirm-cabinet-validation --validated-by "..."`;
- aucun binaire n'a encore ete promu faute de fichier source exact disponible.

## Lot 6 — CNSS 610-1-04 — BACKEND DE PREPARATION/VALIDATION/RENDU GENERIQUE IMPLEMENTE / CALIBRATION BLOQUEE PAR BINAIRE
Reference dentaire confirmee: `CNSS-610-1-04`, 2 pages attendues, ref ANAM `1.2.03.01`.

Une copie secondaire coherente 2 pages a ete retrouvee et recroisee, mais aucune copie officielle CNSS exacte n'est recuperable/verrouillee depuis l'environnement. Elle ne doit pas etre promue silencieusement en `OFFICIAL_PRIMARY`. La voie `CABINET_VALIDATED_BINARY` reste possible uniquement apres validation explicite d'un binaire exact par le praticien/cabinet.

### Politique administrative CNSS — IMPLEMENTEE
- prefill uniquement faits explicites: nom beneficiaire, naissance, sexe, nom praticien;
- INPE seulement depuis une cle explicitement INPE/INP;
- type de soins seulement si tous les Acte sources convergent vers une categorie deterministe;
- note mixte => manuel;
- adresse patient jamais assimilee automatiquement a l'adresse assure;
- CIN/immatriculation/identite assure/lien jamais inventes;
- tous champs obligatoires manquants deviennent `administrative.<field>`.

### Preparation et coherence source — IMPLEMENTEES
`prepare_insurance_draft_from_honoraires()` + `assert_draft_matches_honoraires_source()`:
- relisent Honoraires/Acte cote serveur;
- recroisent patient, organisme, UID, Acte, catalog_act_id, date, dents, libelle, montant;
- toute divergence => blocage avant validation.

### Validation praticien — IMPLEMENTEE
`validate_insurance_draft_by_practitioner()`:
- seul le praticien source peut valider;
- NGAP recalcule depuis la DB, jamais depuis le client;
- completude administrative recalculee;
- template + source NGAP relus dans le store immuable;
- produit un nouveau snapshot `VALIDATED` uniquement si toutes les preuves restent coherentes.

### Renderer generique — IMPLEMENTE
`insurance_pdf_overlay.py`:
- aucune coordonnee assureur hardcodee;
- profil separe lie a `organization + template_version + template_hash`;
- profil canonique serialisable + SHA-256;
- champs signature/cachet/decision assureur explicitement interdits;
- hash template exact obligatoire avant insertion PDF.

### Finalisation rendu -> archive — IMPLEMENTEE
`finalize_insurance_submission_pdf()`:
1. exige un draft deja `VALIDATED`;
2. revalide immediatement DB + NGAP + sources immuables avec le meme praticien/date;
3. compare le snapshot reconstruit au snapshot valide: difference => `stale or altered`, nouvelle revue obligatoire;
4. relit le template exact depuis le store;
5. rend via le profil hash-bound;
6. calcule le SHA-256 du PDF final;
7. archive PDF + profil complet + hash profil + hash PDF final.

Aucune coordonnee CNSS reelle n'est inventee avant verrouillage du binaire exact. La calibration fidele du `610-1-04` reste donc bloquee par le fichier source.

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
- profil de coordonnees calibre/valide sur ce hash exact;
- migration/rollback, archivage/reimpression et UX certifies.

## Certification backend — PROUVEE
HEAD code certifie: `672133f6040e2f6c1bc91f71ceffff2a7380067d`.

Exact-head:
- CI #4143: **SUCCESS**;
- Cabinet Upgrade PostgreSQL #566: **SUCCESS**;
- Clinic P3 Document Provenance #116: **SUCCESS**;
- T2 Runtime Browser #3051: **SUCCESS**;
- Catalog Connected Truth #1192: **SUCCESS**;
- M6-I Biometric #1851: **SKIPPED attendu**.

Closeout documentaire `67d3dcf23c6da45e1385c81e97d3f109902389d0`:
- CI #4146: **SUCCESS**;
- PostgreSQL #568: **SUCCESS**;
- Provenance #118: **SUCCESS**;
- Browser #3053: **SUCCESS**;
- Catalog #1194: **SUCCESS**.

## Realignement master
- `master` courant absorbe: `38dc018426d93437c6a77e9d5856c529096dda5a`;
- les trois commits depuis `e7198b27...` ne modifient que `.github/workflows/ci.yml` et ajoutent/restaurent l'invariant explicite de non-regression, le workflow M4-C complet et les versions d'actions deja en usage;
- merge explicite sur la branche Mutuelles: `7f8d2c6ed31f7ca94c6252fe67fd6d4e92d36cf3`;
- apres merge: **91 ahead / 0 behind**, merge-base exactement `38dc018426d93437c6a77e9d5856c529096dda5a`;
- PR #493: draft, mergeable=true;
- certification exact-head `7f8d2c6e...`: PostgreSQL #584, Provenance #119, Browser #3069 et Catalog #1195 **SUCCESS**; M6-I #1869 **SKIPPED attendu**; CI #4165 encore `in_progress` au dernier controle, seule la regression backend complete restant en execution.

## Interdits
Second moteur Honoraires, second catalogue clinique, Ordonnance bis, fuzzy mapping, backfill artificiel, signature/cachet/accord assureur fabrique, auto-cotation sans source primaire hashee ET validation metier, template secondaire promu en final, rendu approximatif d'un formulaire officiel, deploiement Vercel sans autorisation explicite.

## Etat
`LOTS_1_4_IMPLEMENTED / NGAP_ENGINE_IMPLEMENTED_SOURCE_PENDING / LOCAL_SOURCE_STORE_IMPLEMENTED / CNSS_ADMIN_PREFILL_IMPLEMENTED / SOURCE_CONSISTENCY_GATE_IMPLEMENTED / PRACTITIONER_VALIDATION_GATE_IMPLEMENTED / HASH_BOUND_OVERLAY_IMPLEMENTED / FINALIZATION_ARCHIVE_IMPLEMENTED / BACKEND_CODE_HEAD_CERTIFIED / MASTER_REALIGNED / EXACT_HEAD_SPECIAL_CERTS_GREEN / CI_4165_PENDING / PRIMARY_HASH_PENDING / CNSS_TEMPLATE_BINARY_PENDING / RUNTIME_NOT_ACTIVATED`

## Next exact
1. Obtenir le verdict CI #4165 sur `7f8d2c6e...`; si vert, ne plus muter le HEAD pour de la documentation seule.
2. Recuperer localement le binaire primaire NGAP exact depuis Ministere/DIO -> lock/store/hash.
3. Valider un premier lot representatif de mappings NGAP par praticien.
4. Recuperer/verrouiller le binaire CNSS 610-1-04 exact; a defaut de source officielle recuperable, utiliser `CABINET_VALIDATED_BINARY` uniquement apres validation explicite du fichier exact.
5. Calibrer profil CNSS sur CE hash -> test visuel fidele.
6. BEFORE/mockup -> UX -> AFTER/tests.
7. CNOPS/FAR -> gate cabinet -> closeout/merge.
