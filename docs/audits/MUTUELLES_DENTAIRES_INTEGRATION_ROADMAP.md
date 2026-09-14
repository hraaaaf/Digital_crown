# Mutuelles dentaires — Integration Roadmap

Date: 2026-09-14
Branch: `feature/mutuelles-dentaires-integration-20260914`
Baseline: `master` @ `1ce5bc8a6297c89e9b69a8b455ada576d374a6fc`

## Goal
Integrer un workflow unique de feuille de soins CNSS/CNOPS/FAR a partir des donnees existantes Digital Crown, avec validation praticien, tracabilite NGAP et archivage du PDF final dans le dossier patient, sans dupliquer Honoraires, Ordonnance, CatalogAct ni DocumentArchive.

## UX cible verrouillee
Flux principal:

`Patient -> Honoraires -> Preparer feuille de soins -> Revue/validation -> PDF -> DocumentArchive`

Regles:
- CTA principal depuis une note d'honoraires lorsque le patient a un organisme compatible;
- acces secondaire depuis Documents sur une note d'honoraires existante;
- ecran intermediaire obligatoire avant PDF: identite, assure/beneficiaire, INPE, actes, dents, honoraires, NGAP, champs manquants;
- ambiguite NGAP = choix praticien, jamais fuzzy matching silencieux;
- generation finale uniquement apres validation explicite du praticien;
- PDF final archive automatiquement dans le dossier patient;
- reimpression historique a partir du snapshot archive, jamais recalcul implicite avec un nouveau referentiel.

## Strategie archive P0
Ne pas ajouter un nouvel enum SQL immediatement. Premier lot compatible DB:
- `DocumentType.AUTRE`;
- tags: `insurance_submission`, organisme (`cnss|cnops|far`), version template;
- `clinical_data.kind = INSURANCE_SUBMISSION`;
- snapshot complet `InsuranceSubmissionDraft` + provenance Honoraires + version/hash template + version NGAP + validation praticien.

Un type documentaire dedie pourra etre introduit ensuite uniquement apres migration additive testee.

## Roadmap

### Lot 1 — Contrat runtime pur
Goal: disposer d'un `InsuranceSubmissionDraft` type, deterministe et fail-closed.
Success: schema importe sans DB; tests unitaires exact/ambiguous/no-match; aucune route/UI/DB modifiee.
Preuve: pytest cible vert.

### Lot 2 — Adaptateur Honoraires -> Draft
Goal: construire le draft depuis `DocumentArchive.clinical_data.payments[*]` et les `Acte` derives.
Success: dents lues depuis snapshot, lien historique controle par index actif, divergence => blocage.
Preuve: fixtures historiques + tests shrink/expand/divergence.

### Lot 3 — Archivage du PDF valide
Goal: archiver chaque feuille finalisee dans `DocumentArchive`.
Success: PDF + snapshot + organisme + template/version/hash + NGAP/version + source Honoraires conserves; document visible/reimprimable.
Preuve: test ArchiveService sur DB de test + hash fichier.

### Lot 4 — Liaison structuree actes/catalogue
Goal: supprimer l'ambiguite de position pour les nouveaux documents.
Cible additive: `source_line_uid` immuable + `catalog_act_id` nullable.
Success: anciens dossiers lisibles sans backfill invente; nouveaux liens deterministes.
Preuve: migration sur copie DB + rollback + invariants patients/IDs.

### Lot 5 — Referentiel NGAP local versionne
Goal: resolution NGAP explicable et offline.
Success: EXACT/AMBIGUOUS/NO_MATCH/OUTDATED; provenance primaire, validite et hash; fail-closed.
Preuve: matrice de cas metier + validation chirurgien-dentiste.

### Lot 6 — Renderers
Ordre: CNSS `610-1-04` -> CNOPS -> FAR.
Success: rendu visuel fidele, champs mappes, aucune signature/cachet/decision assureur fabriquee.
Preuve: comparaison PDF aux references verrouillees et tests de regression.

### Lot 7 — UX/UI
BEFORE obligatoire puis mockup puis implementation puis AFTER memes viewports.
Ecran: `Preparer feuille de soins` avec etats complet/incomplet/ambigu, preview et validation.
Success: generation accessible depuis Honoraires et Documents sans nouveau sous-systeme.
Preuve: captures 360/390/768/1440 + tests interaction + score visuel.

### Lot 8 — Gate cabinet
Activation seulement si:
- templates binaires/hash verrouilles;
- NGAP primaire versionne;
- migration DB testee et rollback valide;
- echantillon representatif acte -> NGAP -> formulaire valide par praticien;
- archivage/reimpression verifies.

## Ordre d'execution
`Lot 1 -> Lot 2 -> Lot 3 -> Lot 4 -> Lot 5 -> Lot 6 CNSS -> Lot 7 UX -> CNOPS/FAR -> gate cabinet`

## Interdits
- second moteur Honoraires;
- second catalogue NGAP;
- nouvelle Ordonnance;
- parsing libelle -> NGAP silencieux;
- backfill artificiel;
- signature/cachet ou accord assureur fabrique;
- deploiement Vercel sans autorisation explicite.

## Etat initial
`INTEGRATION_STARTED / RUNTIME_NOT_ACTIVATED`

Next exact: implementer Lot 1, puis enchainer Lot 2 si les tests de contrat sont verts.
