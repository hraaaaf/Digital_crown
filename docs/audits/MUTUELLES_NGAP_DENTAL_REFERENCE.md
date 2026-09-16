# Mutuelles dentaires — Référentiel NGAP dentaire

Date: 2026-09-16
Repo: `hraaaaf/Digital_crown`
Branch: `feature/mutuelles-dentaires-integration-v2-20260914`
PR: `#493`

## Goal
Disposer d’un référentiel auditable et fail-closed `code NGAP -> acte -> coefficient` pour le workflow d’assurance dentaire, sans inventer de coefficient, sans confondre la source clinique `CatalogAct` avec la référence réglementaire, et sans activer automatiquement une cotation en production.

## Succès observable
- JSON de mapping versionné et lisible;
- couverture exacte des plages retenues;
- coefficient principal et coefficient d’anesthésie séparés;
- cas sans coefficient fixe explicitement typés;
- conditions juridiques séparées du mapping;
- identité du binaire verrouillé séparée des URLs de découverte/corroboration;
- loader fail-closed;
- aucune auto-certification `VERIFIED_PRIMARY` depuis le JSON.

## Implémentation
Code head de référence avant ce document: `e2722165631badc6bebcf05e611d640c700f17db`.

Fichiers:
- `backend/data/ngap_dental_177_06.json`
- `backend/data/ngap_dental_177_06_conditions.json`
- `backend/data/ngap_dental_177_06_provenance.json`
- `backend/services/ngap_dental_reference.py`
- `backend/tests/test_ngap_dental_reference_data.py`

## Mapping canonique
Dataset: `ngap-dental-177-06-v1`.

Scope explicite:
- `D600-D641`;
- `D700-D785`;
- `D800-D816`;
- total: **145 codes**.

Colonnes:
- `code`;
- `acte`;
- `coefficient`;
- `anesthesia_coefficient`;
- `entry_type`.

Le scope n’est pas présenté comme l’ensemble de toutes les cotations dentaires possibles en 2026. Les codes radiologiques Z, assimilations/évolutions postérieures, tarifs TNR et règles payeur plus récentes restent hors de ce dataset de base et doivent être versionnés séparément.

Cas non triviaux préservés:
- `D630`: plafond ODF `540`, type `ceiling`;
- `D757`: règle de calcul du bridge, aucun coefficient fixe inventé;
- `D816`: cotation sur devis/accord préalable, aucun coefficient fixe inventé;
- coefficients d’anesthésie séparés lorsque le tableau source fournit une seconde valeur.

## Conditions réglementaires
Dataset: `ngap-dental-177-06-conditions-v1`.

Les conditions sont séparées du mapping afin d’éviter de déduire une règle clinique ou administrative d’un simple coefficient.

Conditions source-bound actuellement matérialisées notamment pour:
- `D608`;
- `D626`;
- `D628`;
- `D629-D641`;
- `D703-D706`;
- `D712`;
- `D720-D732`;
- `D738-D741`;
- `D739-D741` pour la marsupialisation;
- `D757`;
- `D816`.

## Provenance verrouillée
Le binaire verrouillé est décrit séparément dans `ngap_dental_177_06_provenance.json`:
- publication: Bulletin officiel n° 5414 du 20 avril 2006;
- fichier: `bo_5414_fr.pdf`;
- pages: `220`;
- taille: `11 334 738` octets;
- SHA-256: `e9db137d6a758bd4ad7a506a94a7c0c84726813de3db1e225c761318a75e1fdb`.

La copie autonome du Ministère de la Santé et la copie CNOPS sont traitées comme sources de corroboration textuelle, **pas** comme les octets ayant produit ce SHA sans vérification binaire indépendante.

Le loader neutralise l’ancien champ `primary_url` du JSON v1 en `discovery_url`, expose `locked_binary_url = null`, et retire les anciennes règles inline de la vue chargée. Les conditions et la provenance doivent être lues par leurs datasets dédiés.

## Validation réalisée
- JSON conditions: parse valide + 11 règles structurées;
- JSON provenance: parse valide + hash/pages/taille contrôlés;
- Python: `py_compile` du loader et des tests: OK;
- test structurel local du loader sur fixture 145 codes: OK;
- première version du mapping: tests ciblés locaux `8 passed` avant ajout des couches conditions/provenance;
- diff du lot depuis `3d9d4802...`: uniquement données NGAP, loader et tests dédiés;
- recroisement documentaire effectué sur les blocs maxillaires, ODF, soins conservateurs, chirurgie, prothèse et maxillo-facial avec les publications Ministère/CNOPS.

## Invariants de sécurité
- `REFERENCE_ONLY_NOT_RUNTIME_CERTIFIED` n’active aucun mapping production;
- `CatalogAct` reste la source clinique;
- aucune correspondance fuzzy par libellé;
- aucune promotion `VERIFIED_PRIMARY` sans le gate existant source verrouillée + validation praticien;
- aucune URL de découverte n’est assimilée au binaire hashé;
- dérives hash, doublons, trous de couverture et coefficients invalides sont rejetés.

## CI
La certification exact-head finale doit être lue depuis GitHub après le commit documentaire final. Aucun verdict CI futur n’est pré-écrit dans ce fichier.

## Next exact
1. Certifier l’exact HEAD final sur GitHub.
2. Si vert, utiliser ce référentiel comme **evidence/reference layer**, pas comme activation runtime automatique.
3. Avant activation cabinet, traiter séparément les assimilations/évolutions applicables en 2026 et faire valider les mappings `CatalogAct -> NGAP` représentatifs par le praticien.
4. Ne merger la PR #493 qu’après accord explicite utilisateur et résolution de la divergence avec `master`.
