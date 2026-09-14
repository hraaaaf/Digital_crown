# Contrat cible — InsuranceSubmissionDraft

Statut : CONCEPTION ONLY — aucun runtime, aucune migration DB.
Date : 2026-09-14.
Baseline de recroisement code : `master` @ `1ce5bc8a6297c89e9b69a8b455ada576d374a6fc`.

## Goal
Définir le DTO de sortie unique qui assemble une feuille de soins dentaire CNOPS/CNSS/FAR à partir des sources de vérité Digital Crown existantes, sans devenir une nouvelle source clinique ou financière.

Succès : chaque champ possède un type, une nullabilité, une provenance et une règle de validation explicites ; aucune donnée n'est inventée ; le DTO permet une réimpression historique traçable.

## Principes
- `InsuranceSubmissionDraft` est un snapshot de préparation/rendu, jamais un modèle métier primaire.
- Aucun champ `AUTO` sans source canonique réellement présente.
- Tout mapping NGAP automatique est fail-closed : `EXACT` seulement.
- `AMBIGUOUS`, `NO_MATCH`, `OUTDATED` exigent validation/saisie praticien.
- Les champs assureur (`INSURER_ONLY`) restent vides côté cabinet.
- Signature/cachet : référence vers un actif réel uniquement, jamais fabrication.
- Le DTO archive les versions réellement utilisées : template + référentiel NGAP + mapping par ligne.

## Schéma logique proposé

```text
InsuranceSubmissionDraft
  draft_version: str
  insurer: CNOPS | CNSS | FAR
  patient_id: int
  generated_at: datetime

  insured_party: InsurancePerson
  beneficiary: InsurancePerson
  relationship_to_insured?: str

  practitioner: PractitionerSnapshot
  care_lines: list[InsuranceCareLine]

  source_honoraires_document_id: int
  source_ordonnance_document_id?: int
  attachments: list[AttachmentRef]

  ngap_reference_version?: str
  ngap_reference_hash?: str
  template_version: str
  template_hash: str
  template_source: str

  practitioner_validation:
    required: bool
    validated_at?: datetime
    validated_by?: int

  unresolved_fields: list[UnresolvedField]
```

## Personnes

```text
InsurancePerson
  patient_id?: int
  last_name: str
  first_name: str
  birth_date?: date
  sex?: str
  cin?: str
  affiliation_number?: str
  insured_account_number?: str
  quality?: str
```

Provenance :
- identité bénéficiaire : `Patient` ;
- assurance générique : `Patient.assurance` ;
- CIN / affiliation / compte / qualité : futures données assurance optionnelles, absentes aujourd'hui du schéma Patient audité ;
- assuré distinct du patient : données assurance optionnelles, jamais créées par déduction silencieuse.

## Praticien

```text
PractitionerSnapshot
  practitioner_id: int
  display_name: str
  cabinet_name?: str
  address?: str
  phone?: str
  inpe?: str
  stamp_asset_id?: str
  signature_asset_id?: str
```

Sources : `User` + `CabinetConfig`. `inpe` auto uniquement si présent. Cachet/signature seulement si actifs réels explicitement configurés.

## Lignes de soins

```text
InsuranceCareLine
  line_index: int
  source_line_uid?: str
  source_acte_id: int
  source_catalog_act_id?: int
  source_honoraires_document_id: int

  care_date: date
  label: str
  teeth_fdi: list[int]
  fee_mad: decimal

  catalog_code_kind?: NGAP | INTERNAL | OTHER
  ngap_mapping_status: EXACT | AMBIGUOUS | NO_MATCH | OUTDATED | NOT_EVALUATED
  ngap_code?: str
  ngap_key_letter?: str
  coefficient?: decimal
  ngap_rule_ids: list[str]
  mapping_evidence?: str
```

### Provenance actuelle vérifiée
- `care_date`, `label`, `fee_mad` : ligne Honoraires / `Acte` dérivé ;
- `teeth_fdi` : `DocumentArchive.clinical_data.payments[*].dent/dents` ;
- `source_acte_id` : `Acte` dérivé lié au même `document_archive_id` ;
- aujourd'hui, correspondance ligne ↔ Acte : ordre des lignes actives ;
- `source_catalog_act_id` : indisponible tant qu'aucun lien structuré n'existe ;
- NGAP : jamais dérivé du libellé seul.

## Pièces jointes

```text
AttachmentRef
  kind: HONORAIRES | ORDONNANCE | RADIOGRAPH | OTHER
  document_archive_id?: int
  filename?: str
  file_hash?: str
  required_by_rule?: bool
  status: AVAILABLE | MISSING | MANUAL_REQUIRED
```

Réutiliser les documents P1/P4 existants. Ne pas recopier le contenu clinique dans un second sous-système.

## Champs non résolus

```text
UnresolvedField
  path: str
  reason: MISSING_SOURCE | AMBIGUOUS_MAPPING | MANUAL_REQUIRED | INSURER_ONLY | OUTDATED_REFERENCE
  message: str
  blocking: bool
```

Le renderer ne doit pas masquer une absence. Toute absence bloquante reste visible avant validation praticien.

## Invariants
1. `patient_id`, `source_honoraires_document_id`, `source_acte_id` doivent référencer des objets existants.
2. `teeth_fdi` est normalisé FDI ; aucune extraction depuis le libellé.
3. `source_catalog_act_id` absent => aucun NGAP automatique.
4. `catalog_code_kind != NGAP` => `ngap_code` non auto-rempli depuis `CatalogAct.code`.
5. `ngap_mapping_status != EXACT` => validation praticien obligatoire et aucun code facturable silencieux.
6. `template_hash` et `template_version` obligatoires pour tout rendu final.
7. Une réimpression historique utilise le snapshot/version archivés, pas la version courante du référentiel.

## Construction déterministe
1. charger Patient + praticien/cabinet ;
2. charger `DocumentArchive` Honoraires ;
3. lire `clinical_data.payments[]` dans l'ordre ;
4. charger les `Acte` actifs du même `document_archive_id`, triés selon la stratégie documentée ;
5. associer ligne ↔ Acte ;
6. résoudre `CatalogAct` seulement par lien structuré ;
7. exécuter les règles NGAP versionnées ;
8. produire `unresolved_fields` ;
9. empêcher le rendu final tant que les blocages exigent une validation humaine.

## Tests documentaires minimum
- assuré = patient, données complètes ;
- bénéficiaire distinct / données assurance manquantes ;
- ligne avec une dent et plusieurs dents FDI ;
- Acte sans `CatalogAct` => `NOT_EVALUATED/NO_MATCH`, aucun code inventé ;
- code catalogue `INTERNAL` => jamais traité NGAP ;
- mapping `AMBIGUOUS` => blocage humain ;
- référentiel expiré => `OUTDATED` ;
- même snapshot + mêmes versions => même DTO hors timestamps techniques ;
- édition Honoraires shrink/expand => aucune réassociation silencieuse à un ancien Acte supprimé.

## Gate runtime
Ce contrat ne suffit pas à ouvrir le code applicatif. Avant intégration : stratégie `source_line_uid/catalog_act_id`, schéma NGAP versionné, templates hashés, tests de migration additive et audit final anti-doublon doivent être verts.