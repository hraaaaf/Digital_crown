# Mutuelles dentaires — Integration Roadmap

Date: 2026-09-14
Branch: `feature/mutuelles-dentaires-integration-v2-20260914`
Baseline: `master` @ `c8870ecca4c9ac3f3beb00df6030785dd8ee5aa1`
PR: `#493` (draft)

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

## Roadmap
### Lot 1 — Contrat runtime pur
Goal: `InsuranceSubmissionDraft` type, deterministe et fail-closed.
Implementation: CODED.
Success: schema sans DB; EXACT obligatoire avant revue/validation.
Preuve attendue: pytest cible vert.

### Lot 2 — Adaptateur Honoraires -> Draft
Goal: construire depuis `DocumentArchive.clinical_data.payments[*]` et les `Acte` derives.
Implementation: CODED.
Success: dents depuis snapshot; fallback historique par index actif; divergence => blocage.
Preuve attendue: tests alignement/mismatch.

### Lot 3 — Archivage PDF valide
Goal: archiver chaque feuille finalisee dans `DocumentArchive`.
Implementation: CODED.
Success: PDF + snapshot + organisme + template/hash + NGAP/version + source Honoraires conserves.
Preuve attendue: test DB isole `test_insurance_archive_persistence.py` + hash SHA-256.

### Lot 4 — Liaison structuree actes/catalogue
Status: NOT STARTED — gate CI Lots 1-3.
Cible additive: `source_line_uid` immuable + `catalog_act_id` nullable.
Success: historique sans backfill invente; nouveaux liens deterministes.
Preuve: migration sur copie DB + rollback + invariants patients/IDs.

### Lot 5 — Referentiel NGAP local versionne
Success: EXACT/AMBIGUOUS/NO_MATCH/OUTDATED, provenance primaire, validite/hash, fail-closed.
Preuve: cas metier + validation chirurgien-dentiste.

### Lot 6 — Renderers
Ordre: CNSS `610-1-04` -> CNOPS -> FAR.
Success: rendu fidele; aucune signature/cachet/decision assureur fabriquee.
Preuve: comparaison aux references verrouillees + regression PDF.

### Lot 7 — UX/UI
BEFORE -> Goal -> mockup -> implementation -> AFTER memes viewports -> comparaison/tests -> score visuel.
Success: generation depuis Honoraires et Documents sans nouveau sous-systeme.
Preuve: 360/390/768/1440 + tests interaction.

### Lot 8 — Gate cabinet
Activation seulement si templates hash/verrouilles, NGAP primaire versionne, migration/rollback testes, validation metier representative et archivage/reimpression verifies.

## Ordre
`Lot 1 -> Lot 2 -> Lot 3 -> Lot 4 -> Lot 5 -> Lot 6 CNSS -> Lot 7 UX -> CNOPS/FAR -> gate cabinet`

## Interdits
Second moteur Honoraires, second catalogue NGAP, Ordonnance bis, fuzzy mapping silencieux, backfill artificiel, signature/cachet/accord assureur fabrique, deploiement Vercel sans autorisation explicite.

## Etat courant
`LOTS_1_3_CODED / CI_PENDING / RUNTIME_NOT_ACTIVATED`

Derniere preuve codee:
- contrat fail-closed;
- dents lues depuis snapshot Honoraires;
- mismatch lignes/Acte refuse;
- archivage uniquement d'un draft `VALIDATED` et d'un contenu `%PDF`;
- persistance dans `DocumentArchive` via `DocumentType.AUTRE` + snapshot/tags explicites;
- test DB isole ajoute sans toucher la DB cabinet.

Next exact: obtenir CI verte sur le HEAD courant, puis ouvrir Lot 4 et tester la migration additive/rollback avant toute UI.
