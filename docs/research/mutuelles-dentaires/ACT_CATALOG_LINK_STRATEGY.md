# Stratégie liaison — Honoraires / Acte / CatalogAct

Statut : CONCEPTION ONLY — aucune migration appliquée.
Date : 2026-09-14.
Baseline code recroisée : `master` @ `1ce5bc8a6297c89e9b69a8b455ada576d374a6fc`.

## Goal
Obtenir une liaison déterministe et audit-able entre une ligne Honoraires, son `Acte` dérivé et le `CatalogAct` choisi, sans dépendre d'un libellé libre et sans casser les documents historiques.

## État vérifié
- `PaymentItem` contient `acte`, `dent`, `dents`, `montant`, `date`.
- le payload Honoraires complet est archivé dans `DocumentArchive.clinical_data` ;
- `persist_honoraires_lines()` rapproche aujourd'hui les lignes et `Acte` actifs par ordre ;
- les `Acte` sont liés au document par `document_archive_id` ;
- les anciennes lignes surnuméraires sont soft-deleted et ne doivent pas redevenir actives ;
- aucun `catalog_act_id` n'est persisté aujourd'hui dans ce flux ;
- le libellé n'est donc pas une clé métier admissible pour un mapping NGAP automatique.

## Stratégie en deux niveaux

### Niveau A — historique existant, lecture seule
Pour les notes déjà archivées avant toute évolution de schéma :

```text
line = DocumentArchive.clinical_data.payments[index]
acte = active Acte with same document_archive_id, ordered by Acte.id ASC, same active index
```

Garde-fous :
- exclure `Acte.deleted_at != NULL` ;
- vérifier le même nombre de lignes actives et d'Acte actifs ;
- vérifier date/libellé/montant comme signaux de cohérence, jamais comme identifiant primaire ;
- si divergence => `LINK_AMBIGUOUS`, aucune résolution NGAP automatique.

Ce fallback ne doit pas être prolongé comme architecture cible.

### Niveau B — cible additive robuste
Ajouter ultérieurement, seulement dans le chantier d'intégration :

```text
PaymentItem / snapshot Honoraires
  source_line_uid: UUID stable
  catalog_act_id?: int

Acte
  source_line_uid?: UUID
  catalog_act_id?: int FK catalog_acts.id
```

Règles :
- `source_line_uid` créé une fois à la création de la ligne UI, puis conservé lors des éditions ;
- une édition change contenu/prix/date mais pas l'identité de ligne ;
- une ligne supprimée garde son UID dans l'historique ;
- une nouvelle ligne après suppression reçoit un nouvel UID ;
- `catalog_act_id` est nullable et explicite ;
- aucun auto-remplissage par fuzzy matching ;
- changement volontaire de `catalog_act_id` doit être traçable dans le snapshot documentaire.

## Pourquoi `source_line_uid`
L'index seul décrit une position, pas une identité. Les scénarios shrink → expand, réordonnancement, insertion au milieu ou suppression peuvent changer la position tout en conservant l'intention clinique. Un UID immuable supprime cette ambiguïté sans dupliquer les modèles métier.

## Pourquoi snapshot + FK
- le FK `catalog_act_id` donne la relation structurée courante ;
- le document mutuelle doit également snapshotter le code/règle/version utilisés afin qu'une réimpression reste historiquement fidèle si le catalogue évolue.

## Résolution proposée

```text
if source_line_uid exists on both snapshot and Acte:
    match by source_line_uid
elif historical_document:
    fallback by active index + integrity checks
else:
    fail closed

if catalog_act_id is explicit:
    load CatalogAct
else:
    mapping status = NOT_EVALUATED / NO_MATCH
```

## Migration future — contraintes
- colonnes nullable uniquement ;
- aucun backfill obligatoire de `source_line_uid` sur l'historique ;
- aucun backfill inventé de `catalog_act_id` ;
- documents historiques restent lisibles via fallback ;
- les nouveaux documents après activation doivent avoir `source_line_uid` ;
- rollback doit pouvoir ignorer les nouveaux champs sans perte de données historiques.

## Tests requis
1. document historique aligné => fallback déterministe ;
2. document historique nombre de lignes ≠ Acte actifs => fail closed ;
3. shrink d'une note => ancienne ligne soft-deleted jamais rematchée ;
4. expand après shrink => nouvelle ligne ≠ ancien UID ;
5. réordonnancement avec UID => bonne ligne conservée ;
6. `catalog_act_id` absent => aucun NGAP ;
7. `catalog_act_id` invalide/inactif => blocage ;
8. changement catalogue => nouveau snapshot document, ancien snapshot inchangé.

## Décision recommandée
Adopter `source_line_uid` + `catalog_act_id` comme cible d'intégration. Conserver l'index uniquement comme compatibilité historique contrôlée. C'est le chemin le plus simple qui supprime l'ambiguïté structurelle sans créer de second catalogue ni casser la DB existante.