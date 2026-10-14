# LOT05 — Migration multiformat : laboratoire synthétique S01–S12 (NO-GO données)

Ce sous-lot est un **test d'intégration des composants de prévisualisation**, pas une migration. Il reste empilé sur PR #856 (ORM déclaré), #854 (UI staff), #853 (mapping), #850 (inspecteur), tous DRAFT. Aucun dump réel, patient réel, migration Alembic, endpoint, backend runtime, front, Pocket, Station, Vercel, merge ou DB clinic n'est sollicité.

## Matrice des scénarios — ordre des tests

| Scénario | Source fabriquée (strictement fictive) | Chaîne à éprouver | Attendu honnête |
|---|---|---|---|
| S01 | SQL textuel **MySQL compatible sous-ensemble DDL**, colonnes en anglais, INSERT fictif ignoré | inspecteur 05.1 → vrais noms ORM *déclarés* 05.2-B2a → mapping explicite 05.2-A | Draft non approuvé, `legacy_patients`→`patients`, `first_name`→`prenom`, `last_name`→`nom` ; autre table exclue ; zéro ligne transférée |
| S02 | **Fichier SQLite froid .db**, créé en test, noms français, ligne fictive | même chaîne, ouverture SQLite `mode=ro&immutable=1` sans lire les lignes | Draft non approuvé, `dossiers`→`patients`, `rdv` non mappé |
| S03 | SQL textuel **PostgreSQL compatible sous-ensemble DDL**, colonnes en espagnol, INSERT fictif ignoré | même chaîne | Draft non approuvé, `personas`→`patients`, `nombre`→`prenom`, `apellido`→`nom` ; `citas` exclues |
| S04 | .bak natif factice | inspecteur | Refus : adaptateur non implémenté |
| S05 | Tentative d'affectation du champ `password_hash` | mapping | Refus, zéro credential importé |
| S06 | SQL source modifié après le draft | revalidation | Hash source différent, nouvelle revue requise |
| S07 | Drapeaux `admin_approved/import_permitted` trafiqués | revalidation | Refus, jamais authorization |
| S08 | DDL MySQL non supporté | inspecteur | Refus, pas de parsing approximatif |
| S09 | CSV fictif | inspecteur | Refus, adaptateur CSV à créer |
| S10 | `DROP TABLE` et `INSERT` inclus dans SQL textuel | inspecteur | **Jamais exécutés** ; seuls noms/colonnes du CREATE sont inventoriés |
| S11 | SQLite en mode WAL non certifié copie froide | inspecteur | Refus |
| S12 | Copie hors-ligne non attestée | inspecteur | Refus |

**Traduction** : ces tests prouvent la possibilité de **correspondances choisies manuellement** entre noms de colonnes anglais/espagnols et champs français. Ils ne prouvent **aucune détection automatique de synonymes**, ni conversion des types, dates, valeurs ou textes, ni détection de doublons. Un texte médical en langue étrangère n'est ni traduit ni importé.

**Vrai modèle cible** : les tests chargent les déclarations SQLAlchemy `backend.models` en isolant explicitement l'initialisation du package `backend`, **sans `backend.database`**, et utilisent uniquement l'adaptateur 05.2-B2a. Révision `orm-declared:neo000000027` = valeur dans les sources du LOT05 actuel, **non attestation physique de la DB**. LOT04 possède une branche distincte avec une migration candidate `neo000000028` : cette coexistence empêche toute extrapolation d'une tête physique unique à partir des deux branches.

**Tenant et données** : le champ cible `employer_id` n'est jamais sourcé depuis le dump, et les IDs source ne sont pas copiés. Il faudra une attribution autorisée par le propriétaire du cabinet, régénération/rapprochement des identifiants, vérification relations/FK, spécification de doublons, registre anti-replay, correction des valeurs, backup et rollback. Les inserts dans les fixtures restent du **texte jamais exécuté** ; la seule base SQLite réelle est fictive dans un répertoire temporaire et n'est interrogée que pour le schéma par 05.1. SHA-256 du dump ne certifie ni l'identité ni l'autorisation.

**CI** : GitHub Actions exécute S01, S02, S03 séparément et dans l'ordre ; S04–S12 suite d'adversaires, puis régressions des 25 mapping, 25 ORM, 28 inspecteur de #856 sur Python 3.12 avec dépendance SQLAlchemy 2.0.28. Vérification du SHA GitHub checkout, exécution sans skipped/expected-failure. Aucune UI staff/PWA touchée donc aucune prétention de validation visuelle ou mobile.

## Suite envisagée, soumise à ses propres gates

- **05.2-B2b** : constater le schéma *physique* réel via chemin backend serveur READ-ONLY authentifié, with tenant scope et refus d'écart Alembic ; ne pas muter la DB.
- **05.3** : pipeline de *données fictives seulement* pour dry-run de vraies valeurs, typage, dates, doublons, collisions, relations, provenance et erreurs ; ensuite PostgreSQL/SQLite éphémères isolées.
- **05.4+** : sauvegarde vérifiée, restauration, opération idempotente/rollback, flux de validation propriétaire, infrastructure chiffrée, import source par source ; jamais brancher les fixtures à la vraie production sans gate humain.

**Frontière de vérité : S01–S12 ne testent pas l'import de données dans Digital Crown. Toute prétention contraire est incorrecte.**
