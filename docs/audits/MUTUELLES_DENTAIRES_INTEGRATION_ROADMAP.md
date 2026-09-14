# Mutuelles dentaires — Integration Roadmap

Date: 2026-09-14
Branch: `feature/mutuelles-dentaires-integration-v2-20260914`
Baseline actuelle: `master` @ `4cfa04d651a47fa0cc2c60482e5ff5729148fb86`
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
### Lot 1 — Contrat runtime pur — IMPLEMENTE, CI A RECERTIFIER SUR HEAD
Goal: `InsuranceSubmissionDraft` type, deterministe et fail-closed.
Preuve code: schema dedie + tests EXACT/AMBIGUOUS/NO_MATCH/validation.

### Lot 2 — Adaptateur Honoraires -> Draft — IMPLEMENTE, CI A RECERTIFIER SUR HEAD
Goal: construire depuis `DocumentArchive.clinical_data.payments[*]` et les `Acte` derives.
Preuve code: dents depuis snapshot; mismatch historique fail-closed.

### Lot 3 — Archivage PDF valide — IMPLEMENTE, CI A RECERTIFIER SUR HEAD
Goal: archiver chaque feuille finalisee dans `DocumentArchive`.
Preuve code: PDF valide seulement, snapshot/tags/provenance, test ArchiveService isole.

### Lot 4 — Liaison structuree actes/catalogue — IMPLEMENTE, CI A RECERTIFIER SUR HEAD
Cible additive: `source_line_uid` immuable + `catalog_act_id` nullable.
Implementation:
- extension ORM additive de `Acte`;
- migration idempotente au `create_all()` pour DB historiques;
- aucun backfill;
- UID genere pour toute nouvelle ligne Honoraires et snapshotte dans `DocumentArchive`;
- edition avec UID explicite matchee par UID; historique sans UID conserve fallback index controle;
- `catalog_act_id` accepte uniquement si `CatalogAct` actif existe;
- suppression/shrink ne reactive jamais une ancienne ligne soft-deleted;
- rollback physique disponible pour certification/tests, jamais execute automatiquement.
Preuves attendues CI:
- UID identique snapshot Honoraires / Acte;
- CatalogAct inconnu => 422 + rollback transactionnel;
- migration + rollback conservent l'ID d'une ligne legacy.

### Lot 5 — Referentiel NGAP local versionne — NEXT
Goal: EXACT/AMBIGUOUS/NO_MATCH/OUTDATED, provenance primaire, validite/hash, fail-closed.
Gate: aucune auto-cotation avant source/version primaire et validation metier.

### Lot 6 — Renderers
Ordre: CNSS `610-1-04` -> CNOPS -> FAR.
Success: rendu fidele; aucune signature/cachet/decision assureur fabriquee.

### Lot 7 — UX/UI
BEFORE -> Goal -> mockup -> implementation -> AFTER memes viewports -> comparaison/tests -> score visuel.
Success: generation depuis Honoraires et Documents sans nouveau sous-systeme.

### Lot 8 — Gate cabinet
Activation seulement si templates hash/verrouilles, NGAP primaire versionne, migration/rollback testes, validation metier representative et archivage/reimpression verifies.

## Ordre restant
`CI Lot 4 -> Lot 5 NGAP -> Lot 6 CNSS -> Lot 7 UX -> CNOPS/FAR -> gate cabinet`

## Interdits
Second moteur Honoraires, second catalogue NGAP, Ordonnance bis, fuzzy mapping silencieux, backfill artificiel, signature/cachet/accord assureur fabrique, deploiement Vercel sans autorisation explicite.

## Etat
`LOTS_1_4_IMPLEMENTED / MASTER_ALIGNMENT_PREPARED / CI_PENDING / RUNTIME_NOT_ACTIVATED`

Next exact: pointer la branche sur le merge d'alignement `master`, puis recertifier le HEAD; si vert, construire le referentiel NGAP local versionne a partir de sources primaires verrouillees.
