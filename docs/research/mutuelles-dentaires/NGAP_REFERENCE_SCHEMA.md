# Schéma cible — Référentiel NGAP versionné

Statut : CONCEPTION ONLY — aucun référentiel activé dans le runtime.
Date : 2026-09-14.

## Goal
Définir un modèle NGAP déterministe, versionné et traçable adossé au `CatalogAct` existant, sans créer un second catalogue d'actes.

## Principe
`CatalogAct` reste la source de catalogue clinique. Les métadonnées NGAP sont une couche réglementaire versionnée liée au catalogue, pas un remplacement.

## Entité logique proposée

```text
NgapCatalogMapping
  id: UUID/int
  catalog_act_id: int

  code_kind: NGAP | INTERNAL | OTHER
  ngap_code?: str
  key_letter?: str
  coefficient?: decimal
  official_label?: str

  conditions_json?: object
  exclusions_json?: object
  teeth_scope_json?: object
  requires_prior_approval: bool
  requires_radiograph: bool

  source_authority: ONMD | ANAM | CNOPS | OTHER_PRIMARY
  source_url: str
  source_document_version: str
  source_hash: str
  verified_at: datetime
  valid_from?: date
  valid_to?: date

  status: ACTIVE | SUPERSEDED | EXPIRED | UNVERIFIED
  mapping_version: str
```

## Contraintes
1. `catalog_act_id` obligatoire.
2. `code_kind` obligatoire : un `CatalogAct.code` historique ne devient jamais NGAP par supposition.
3. `ngap_code/key_letter/coefficient` sont nullable tant que non vérifiés.
4. `source_hash` + `source_document_version` obligatoires pour `ACTIVE`.
5. plages `valid_from/valid_to` non chevauchantes pour une même règle active sauf justification explicite.
6. `UNVERIFIED`/`EXPIRED`/`SUPERSEDED` interdisent tout préremplissage automatique.
7. une règle appliquée est snapshotée dans le document mutuelle.

## Résultat de mapping par ligne

```text
NgapMappingResult
  status: EXACT | AMBIGUOUS | NO_MATCH | OUTDATED
  mapping_id?: id
  catalog_act_id?: int
  ngap_code?: str
  key_letter?: str
  coefficient?: decimal
  applied_rule_ids: list[str]
  reference_version?: str
  reference_hash?: str
  reason: str
```

Règles :
- `EXACT` : une seule règle active satisfait toutes les conditions structurées ;
- `AMBIGUOUS` : plusieurs règles restent possibles ;
- `NO_MATCH` : aucun mapping admissible ;
- `OUTDATED` : mapping trouvé mais source/version non valide.

Seul `EXACT` autorise le préremplissage. Même dans ce cas, la validation finale du praticien reste explicite avant émission.

## Contexte autorisé
Le moteur peut utiliser uniquement des données structurées :
- `catalog_act_id` explicite ;
- dent(s) FDI ;
- nombre de dents ;
- date/séance ;
- type de prothèse/soin si structuré ;
- contexte clinique explicitement disponible ;
- règles de cumul versionnées.

Le libellé libre seul ne suffit jamais.

## TNR / tarifs
Les valeurs tarifaires réglementaires doivent être versionnées séparément si leur cycle diffère de la nomenclature :

```text
NgapTariffReference
  key_letter_or_code
  value_mad
  source_authority
  source_version
  source_hash
  valid_from
  valid_to
  status
```

Ne pas fusionner artificiellement nomenclature et tarif si les sources/validités sont différentes.

## Offline/local-first
- données de référence embarquées localement ;
- mise à jour explicite, signée/hashée si possible ;
- aucune dépendance réseau pour générer une feuille ;
- anciennes versions conservées pour réimpression et audit ;
- import d'une nouvelle version soumis à validation + tests.

## Tests requis
1. `CatalogAct` code interne => jamais NGAP automatiquement ;
2. mapping exact actif => sortie déterministe ;
3. deux règles valides => `AMBIGUOUS` ;
4. aucune règle => `NO_MATCH` ;
5. mapping expiré => `OUTDATED` ;
6. même entrée + même version/hash => même résultat ;
7. nouvelle version => anciens documents restent reproductibles ;
8. règle de cumul multi-actes testée indépendamment ;
9. source/hash manquants => mapping non activable.

## Gate d'autorité
Avant activation cabinet, chaque version NGAP/TNR doit être recroisée avec des sources primaires métier/institutionnelles déjà listées dans `SOURCES.md`, puis validée sur un échantillon représentatif par un praticien connaissant les règles AMO/NGAP.