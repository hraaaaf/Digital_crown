# Politique NGAP — futur moteur mutuelle

Statut : conception uniquement. Aucun mapping NGAP n’est intégré au runtime dans ce lot.

## Goal
Transformer un acte dentaire déjà enregistré dans Digital Crown en code/cotation NGAP uniquement lorsqu’une correspondance autoritative, versionnée, typée et non ambiguë existe.

## Sources autoritatives
1. ONMD : page NGAP et documents associés.
2. Textes/conventions institutionnels CNOPS/ANAM.
3. Communiqué ONMD n°01/26 du 02/02/2026 relatif à la feuille de soins dentaires et à l’usage NGAP/TNR.

`ngap-maroc.com` et autres index privés peuvent aider au contrôle humain mais ne constituent jamais l’unique autorité d’un code automatique.

## Réutilisation obligatoire du catalogue existant
Digital Crown possède déjà `CatalogAct` avec :
- `id` ;
- `name` ;
- `code` ;
- prix ;
- spécialité.

Le commentaire du modèle précise que `code` peut être « NGAP ou interne ». Il ne faut donc pas créer un second catalogue NGAP, mais enrichir/versionner le catalogue existant lorsque le chantier d’intégration sera ouvert.

Gap actuel vérifié : `Acte` n’a pas de `catalog_act_id` et la persistance Honoraires ne conserve aucun identifiant catalogue. Un libellé identique ou proche n’est pas un identifiant métier suffisant.

## Modèle de référence cible
Chaque association NGAP exploitable automatiquement devra contenir au minimum :

```text
catalog_act_id
code_kind              # NGAP | INTERNAL | autre explicite
ngap_code / lettre_cle
coefficient
libelle_officiel
conditions / exclusions
teeth_scope
requires_prior_approval
requires_radiograph
source_authority
source_url
source_document_version
source_hash
verified_at
valid_from
valid_to
status
```

Les valeurs TNR/lettres-clés doivent rester séparées si leur cycle de version diffère.

## Mapping
Ordre de préférence futur :
1. lien stable explicite vers `CatalogAct` ;
2. contexte structuré requis : dent(s) FDI, nombre de dents, type de prothèse, séance, etc. ;
3. règles NGAP versionnées.

Le libellé libre seul est interdit comme clé de génération automatique.

Résultats permis :
- `EXACT` : une seule correspondance valide → préremplissage autorisé ;
- `AMBIGUOUS` : plusieurs correspondances plausibles → choix praticien obligatoire ;
- `NO_MATCH` : aucun mapping → saisie/validation manuelle ;
- `OUTDATED` : référentiel expiré/non vérifié → auto-remplissage interdit.

Aucun fuzzy matching silencieux ne transforme un libellé approximatif en code facturable.

## Dents et contexte
Pour une note Honoraires existante, la source actuelle des dents est le snapshot :

```text
DocumentArchive.clinical_data.payments[*].dent / dents
```

Le modèle `Acte` ne possède pas aujourd’hui de champ dent/dents. Le moteur mutuelle devra lire le snapshot documentaire tant qu’aucune persistance additive plus robuste n’est introduite.

## Règles multi-actes
Les règles de cumul/coefficient sont des règles métier versionnées, jamais une simple addition de lignes. Toute règle appliquée doit être explicitement encodée, sourcée et testée.

## Fonctionnement offline/local-first
- référentiel embarqué/versionné localement ;
- aucune dépendance web pour générer une feuille ;
- mise à jour explicite avec provenance + hash + tests ;
- conservation de la version utilisée dans le snapshot du document.

## Traçabilité du document mutuelle
Le futur `InsuranceSubmissionDraft` doit conserver au minimum :

```text
ngap_reference_version
mapping_result_per_line
source_catalog_act_id?
source_acte_id
source_honoraires_document_id
source_honoraires_line_index_or_stable_id
source_ordonnance_document_id?
template_version
template_hash
generated_at
```

Ainsi une réimpression historique reste explicable même si NGAP/TNR, le catalogue ou le formulaire évoluent.

## Tests requis avant activation
1. acte connu lié au catalogue → code exact ;
2. code catalogue interne → jamais traité comme NGAP ;
3. acte ambigu → blocage + choix humain ;
4. acte inconnu → aucun code inventé ;
5. référentiel expiré/non vérifié → fail-closed ;
6. plusieurs actes même séance → règle de cumul testée ;
7. modification référentiel → anciens documents gardent leur version ;
8. mêmes entrées + même version → même sortie déterministe ;
9. dent(s) récupérées depuis snapshot Honoraires → mapping reproductible.

## Gate métier
Même après engineering vert, un échantillon représentatif `Acte/ligne Honoraires → CatalogAct → NGAP → feuille de soins` devra être relu et validé par un chirurgien-dentiste connaissant les règles AMO/NGAP avant activation cabinet.
