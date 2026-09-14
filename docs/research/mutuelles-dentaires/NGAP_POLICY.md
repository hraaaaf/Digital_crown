# Politique NGAP — futur moteur mutuelle

Statut : conception uniquement. Aucun mapping NGAP n’est intégré au runtime dans ce lot.

## Goal
Transformer un acte dentaire déjà enregistré dans Digital Crown en code/cotation NGAP uniquement lorsqu’une correspondance autoritative, versionnée et non ambiguë existe.

## Sources autoritatives
1. ONMD : page NGAP et documents associés.
2. Textes/conventions hébergés ou référencés par les organismes institutionnels CNOPS/ANAM.
3. Communiqué ONMD n°01/26 du 02/02/2026 pour les modalités de feuille de soins dentaires et l’usage NGAP/TNR.

`ngap-maroc.com` et autres index privés peuvent faciliter le contrôle humain mais ne constituent jamais l’unique source d’un code automatique.

## Modèle de référentiel proposé
Chaque entrée locale versionnée devra contenir au minimum :

```text
reference_id
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

Les valeurs TNR/lettres-clés doivent être stockées séparément de l’identité de l’acte si leur cycle de version diffère.

## Mapping
Le mapping doit utiliser un identifiant métier stable de l’acte Digital Crown et, lorsque nécessaire, le contexte structuré (dent, nombre de dents, type de prothèse, séance, etc.). Le libellé libre seul n’est pas une clé fiable.

Résultats permis :
- `EXACT` : une seule correspondance valide → préremplissage autorisé ;
- `AMBIGUOUS` : plusieurs correspondances plausibles → choix praticien obligatoire ;
- `NO_MATCH` : aucun mapping → saisie/validation manuelle ;
- `OUTDATED` : référentiel expiré ou non vérifié → auto-remplissage interdit.

Aucun fuzzy matching silencieux ne peut transformer un libellé approximatif en code facturable.

## Règles multi-actes
Les règles de cumul/coefficient doivent être traitées comme règles métier versionnées, pas comme simple addition de lignes. Le texte NGAP institutionnel prévoit des règles spécifiques lorsque plusieurs actes sont effectués au cours d’une même séance ; le moteur futur devra appliquer uniquement des règles explicitement encodées et testées.

## Fonctionnement offline/local-first
- référentiel embarqué/versionné localement ;
- aucune dépendance à un appel web pour générer une feuille ;
- mise à jour du référentiel comme lot explicite avec provenance + hash + tests ;
- conservation de la version de référentiel utilisée dans le snapshot du document.

## Traçabilité du document
Le `InsuranceSubmissionDraft` futur doit conserver au minimum :

```text
ngap_reference_version
mapping_result_per_line
source_acte_id
source_honoraires_document_id
source_ordonnance_document_id? 
template_version
template_hash
generated_at
```

Ainsi, une réimpression historique reste explicable même si NGAP/TNR ou le formulaire évoluent.

## Tests requis avant activation
1. acte connu → code exact ;
2. acte ambigu → blocage + choix humain ;
3. acte inconnu → aucun code inventé ;
4. référentiel expiré/non vérifié → fail-closed ;
5. plusieurs actes même séance → règle de cumul testée ;
6. modification du référentiel → anciens documents conservent leur version ;
7. mêmes données d’entrée + même version → même sortie déterministe.

## Gate métier
Même après engineering vert, un échantillon représentatif acte Digital Crown → code/cotation → feuille de soins devra être relu et validé par un chirurgien-dentiste connaissant les règles AMO/NGAP avant activation en cabinet.