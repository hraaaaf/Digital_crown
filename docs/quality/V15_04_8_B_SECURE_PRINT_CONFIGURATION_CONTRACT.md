# Digital Crown — V1.5-04.8-B — Configuration de l'impression (contrat isolé)

**Statut : B1 et B2a testés en LAB ; B2b migration additive candidate testée en LAB/PostgreSQL ; B2c API/Settings/registre matériel NON IMPLÉMENTÉS. 04.8-B GLOBAL OUVERT / NO-GO impression.** Cette note est un contrat d'intégration et non une habilitation matérielle.

## Goal

Autoriser le propriétaire du cabinet à proposer une configuration d'impression parmi `disabled` (défaut), `reception`, `near_station` et `both`, sans pouvoir auto-certifier une imprimante, créer une route de PDF Station, déclencher une impression ou exposer de données patient.

## Sources et découpage

- [Station 04.7 — PR #840](https://github.com/hraaaaf/Digital_crown/pull/840), HEAD `445d63b9b1a677a4b0059744cc6c9d08a15a3131` : `WorkstationMode`, session identifiée et autorisation documentaire, Station PDF 423.
- [Pocket #852](https://github.com/hraaaaf/Digital_crown/pull/852), HEAD `80a482fdb87dac8d20395958a783d4ef9bcf4dee` : coffre patient local (aucune autorité sur imprimante publique).
- [Politique 04.8-A — PR #849](https://github.com/hraaaaf/Digital_crown/pull/849) : `can_offer_print`, décision pure sans job ni PDF.
- [SPEC 04.8 — PR #848](https://github.com/hraaaaf/Digital_crown/pull/848) et [contrat Pocket/Station](V15_04_8_POCKET_852_BOUNDARY_CONTRACT.md) : dispositions de confidentialité, spool, identité, autorisation et idempotence.

## B1 — Contrat exécutable ajouté

`backend/services/station_document_print_configuration.py` propose une fonction pure `compile_owner_print_config`. Elle exige une **identité serveur déjà authentifiée** et réduit l'autorité de configuration au propriétaire exact (`actor_user_id == tenant_id`, compte racine sans `employer_id`). Une permission `settings` ou `admin` déléguée n'est pas suffisante. Aucune élévation via un champ de formulaire.

Entrée stricte JSON/Mapping : `schemaVersion=1`, `mode`, `stationIds`, `printerIds` exactement ; toute autre clé est rejetée (notamment `tenantId`, `secureReleaseVerified`, `privateChannelVerified`, `staffSupervised`, chemin PDF, token ou nom de patient). Identifiants limités, non vides, uniques, aucune valeur implicite.

Les inventaires `TrustedStation` et `TrustedPrinter` sont **des données de confiance à fournir par la DB Cabinet / un registre de certification physique, jamais par le frontend**. Station explicitement enregistrée, locataire correct, mode Station, active, non révoquée ; imprimante existante, active, du même cabinet. `reception` exige une supervision réelle établie côté inventaire ; `near_station` exige poste correspondant et **libération sécurisée ET canal privé indépendamment attestés**. Mode `both` exige *deux types* de destination admis simultanément ; pas de dégradation silencieuse vers une destination unique.

`disabled` est l'état par défaut et impose des listes vides. `default_disabled_print_config` fournit le refus par défaut pour une configuration absente ou non migrée. Le compilateur renvoie une `CabinetPrintPolicy` uniquement en mémoire ; il **n'enregistre rien**, ne crée pas d'API et n'autorise aucun `print` effectif.

## B2 — Gates nécessaires avant persistance (NON FAITS)

1. **Schéma et migration additive contrôlés** : table de politique avec identité propriétaire/tenant unique, version/révision et audit de changement ; tables de mapping imprimante et Station par cabinet avec clés composites/FK + unicité et contraintes mode. Par défaut `disabled`, anciennes installations fail-closed. Ne pas modifier `CabinetConfig` à l'aveugle : vérifier d'abord Alembic HEAD, schéma existant, stratégies multi-tenant et rollback/restore. Écrire migration et dry-run sur copie synthétique, y compris mise à niveau puis retour arrière ; **pas de migration aujourd'hui**.
2. **Source de vérité équipement** : inventaire d'imprimantes physiques local, vérification de leur identité/destination/rattachement Station. Séparer la configuration demandée de l'attestation de sortie sécurisée, qui ne doit pas être auto-signée par l'utilisateur ou le navigateur. Changement de station/révocation/inventaire fait tomber les autorisations.
3. **API administration** : route exclusivement Cabinet de confiance avec identité `get_current_user`, contrôle propriétaire et réauthentification/PIN selon le contrat de Settings/Workstation ; validation serveur d'inventaire sous transaction, révision optimistic-lock, audit minimal. Aucune route Station/Pocket d'écriture. Contrôle négatif pour salarié ayant `settings/admin`, cross-tenant, CSRF/session et concurrent update. Aucune activation sur seul succès de sauvegarde.
4. **Activation distincte** : validateur matériel/field gate 04.8-E et consentement humain ; aucune config `both` opérationnelle avant preuve des deux imprimantes réelles. Le simple `allowed=True` de `can_offer_print` n'est pas un job Cabinet ni une preuve de sortie papier.
5. **UI conditionnelle** : config d'abord à l'écran de Settings du propriétaire (vérifier BEFORE sur Desktop/mobile existant), ensuite Station uniquement si politique déjà certifiée ; AFTER 390/430/768/1280, FR/EN/AR RTL, 200 % ; ne jamais utiliser le hook Desktop `useDocumentGenerator` sur Station.

## Tests de B1 / limites

Le workflow `V1.5-04.8 Station Print Policy (LAB)` prend le véritable SHA du HEAD et exécute deux modules indépendants : les tests originaux 04.8-A et les nouvelles négations B1. Parmi les cas : absence de config, rôle salarié même admin, locataire différent, doublon, mode invalide, certification forgée dans le payload, imprimante hors parc/révoquée, Station hors mode, destinations incomplètes, absence de canal privé et non-mutation d'une policy existante après proposition rejetée.

**Ce qui N'EST PAS testé/actif** : vraie sauvegarde/relecture après restart, branchement sur Settings/API, recertification matérielle, Windows/spool/print agent, idempotence serveur/double-clic cross-destination, lecture PDF Cabinet, routage ou libération, E2E mobile/Station.

**Décision de lot** : B1 peut être marqué *tested* uniquement si logs de l'exact HEAD le prouvent. B2 est **OPEN**. LOT04.8 GLOBAL **OPEN / NOT CONVERGED** ; ne pas merger vers #840/master ni déployer Vercel tant que les preuves et accords distincts ne sont pas réunis.


## B2a — store transactionnel isolé ajouté (NON branché au runtime)

Le module `backend/services/station_document_print_store.py` déclare quatre tables SQLAlchemy Core **hors de la métadonnée applicative globale** pour isoler les tests : configuration unique `tenant_id`, allowlists de Station et imprimantes, audit minimal sans patient ni PDF. Le module ne déclenche pas `create_all`, aucune migration, et aucune écriture d'une vraie DB Cabinet. `schema.create_all` n'est invoqué que dans `backend/tests/test_station_document_print_store_v15.py` sur une DB SQLite `:memory:` synthétique.

`save_owner_configuration` réutilise la compilation fail-closed B1, refuse un `expected_revision` invalide, puis écrit sous **une seule transaction SQL** la politique, les deux listes et l'audit. Un update impose `WHERE tenant_id AND revision = expected_revision` ; un premier insert concurrent est protégé par la PK, transformée en conflit explicite. Aucun retry automatique ni fallback de destination. Si l'audit échoue, la transaction doit être annulée. `load_effective_configuration` relit les IDs stockés, recompile avec le **registre d'équipements actuel** ; Station révoquée, perte de vérification secure release, imprimante manquante ou mode `both` incomplet ⇒ `disabled` effectif, avec code de raison neutre. Les erreurs d'accès DB restent des échecs (pas de cache autorisant en dégradé).

**Limites bloquantes B2b** : ce schéma de tests n'est **PAS** une migration. Les FK physiques tenant/station/user/imprimante et le catalogue des attestations matérielles ne sont pas encore appliqués au schéma existant ; aucun endpoint propriétaire avec identité réellement authentifiée, PIN/réauth/CSRF, snapshot d'inventaire transactionnel ni verrou multi-process n'est prouvé. Les propriétés CAS transactionnelles sont des contrats SQL isolés ; tests PostgreSQL de concurrence, restart/récupération, Alembic HEAD/upgrade/downgrade, API vraie et révocation live sont nécessaires avant un quelconque usage en production. Aucun code ne connecte ce store à Station, Desktop, Pocket ou un driver d'impression.

**Gates B2a** : les suites Python LAB 04.8-A, B1, B2a doivent être *réellement exécutées* sur le SHA final, avec assert HEAD et logs relus ; le green de B1 antérieur ne valide pas B2a. Aucune certification matérielle ni impression n'est déclarée.


## B2b — migration additive de schéma proposée (pas d'application cabinet)

**HEAD certifié d'origine :** `17cb51378fe3dcda1f5b210036ef60b903c78250` avant la présente édition documentaire. Le [script `neo000000028`](https://github.com/hraaaaf/Digital_crown/blob/17cb51378fe3dcda1f5b210036ef60b903c78250/alembic/versions/neo000000028_station_print_owner_config.py) est relié à `neo000000027`, tête réelle du graphe Alembic de #849 lors de l'audit. Ajoute uniquement les quatre tables du store B2a, avec FK tenant → `users.id`, PK uniques, checks mode et révision, index audit ; ne crée aucune ligne configurée et ne déclenche aucun job.

Le [gate central de schéma](https://github.com/hraaaaf/Digital_crown/blob/17cb51378fe3dcda1f5b210036ef60b903c78250/backend/core/schema_runtime.py) attend désormais `neo000000028` afin de **refuser le démarrage sur une base trop ancienne** : ce changement de constante est intentionnel, et nécessite un déploiement/migration explicite et sauvegardé si la PR est fusionnée un jour. Il n'exécute **jamais** une migration au démarrage.

**Preuves CI du HEAD source précité** : [04.8 LAB #38367338889](https://github.com/hraaaaf/Digital_crown/actions/runs/38367338889) SUCCESS avec **115 tests** A/B1/B2a/B2b et assert SHA exact ; [Scope #38367338875](https://github.com/hraaaaf/Digital_crown/actions/runs/38367338875) SUCCESS ; [PostgreSQL 18 from scratch #38367338937](https://github.com/hraaaaf/Digital_crown/actions/runs/38367338937) SUCCESS avec tête Alembic unique, première migration intégrale et deuxième `upgrade head` sans changement du schéma. Les tests Alembic B2b exercent également `upgrade` et `downgrade` sur SQLite synthétique. Ils **ne prouvent pas** l'upgrade PostgreSQL d'une base réelle préexistante ni le rollback avec ses données : sauvegarde, dry-run from-existing et vérification d'empreintes restent obligatoires.

**Défauts empêchant B2 GLOBAL CLOSED** : absence de FK composite tenant/Station au niveau DB (l'isolation B1 est logique/serveur), absence de registre de certification physique de l'imprimante, aucun modèle ORM intégré ou API privilégiée avec session/PIN/CSRF, aucune preuve multi-process PostgreSQL CAS, aucun AFTER Settings, aucune libération sécurisée attestée. L'activation du mode `both` en production reste **interdite**.


## B2c — inventaire, route d'administration limitée et répétition migration (EN COURS)

Une tranche **sûre et volontairement limitée** a été ajoutée sur la branche DRAFT : elle ne permet aucune impression, ni même d'activer une destination. Aucune imprimante n'est « certifiée » par simple saisie de l'utilisateur.

- `station_document_print_inventory.py` lit l'identité des Stations directement dans le registre DB `workstation_modes`, filtré par `employer_id` ; mode, rattachement et révocation proviennent du serveur. Une erreur DB ne déclenche pas de fallback client. `independently_certified_printers_for_tenant` renvoie **une allowlist vide** tant que le registre physique n'existe pas. L'ancien formulaire de politique B1 rejette donc toutes les demandes d'activation, même si elles ciblent une imprimante reconnue par le navigateur.
- `station_print_admin_boundary.py` impose l'identité du **propriétaire racine** du cabinet, sans déléguer implicitement la permission `admin` ou `settings`. Pour une mutation sous cookie, Origin doit être explicitement le même et Sec-Fetch-Site ne doit pas être intersite. Les clients Bearer sans cookie gardent la dépendance d'authentification véritable. Toutes les mutations de configuration doivent passer par le contrôle PIN et le limiteur d'échecs déjà existants.
- `backend/routers/station_print_config_admin.py` monté sous `/api/admin/station-print-config` : **GET** propriétaire = mode effectif/révision/raison neutre, en `Cache-Control:no-store` ; **PUT** propriétaire+PIN = uniquement `mode=disabled`, listes vides et revision attendue (CAS transactionnel/audit). `both`, `near_station`, `reception` et les champs de vérification injectés côté client sont refusés. `get_current_user` est la dépendance Cabinet standard, dont la protection Station doit rester active sur `/api/admin/*`. Il n'y a **aucun POST d'impression**, aucune route de PDF, aucun statut de sortie papier.
- Les tests de labo vérifient le contrat sur inventaire SQL synthétique et la **vraie forme FastAPI** du nouveau routeur, sous stubs de login/PIN déclarés : ce sont des tests HTTP de validation, CAS, audit, absence d'activation, origine et propriétaire, **pas** des tests E2E de l'authentification réelle ni du poste de production.
- Le gate `.github/workflows/postgresql-alembic-schema-cert.yml` complète sa certification à neuf par la séquence sur base PostgreSQL **synthétique non vide** : témoin sans données patient → downgrade `neo28→neo27` → constat → upgrade `neo27→neo28` → témoin intact, état impression non activé. La première exécution a découvert un défaut réel du downgrade index d'audit : nettoyage désormais conditionné à l'existence cataloguée, avec assertion séparée de présence de l'index après l'upgrade. Ces nouveaux tests doivent passer sur le **même HEAD final** ; l'ancien green `17cb...` ne suffit plus.

**B2c reste OUVERT** : il manque le registre de certification physique indépendant, une API permettant une *activation explicitement approuvée et certifiée*, les FK composites au niveau DB et des tests de concurrence multi-process PostgreSQL. En outre, vérifier les contraintes réelles sur une base Cabinet préexistante sauvegardée et l'intégration de l'authentification/CSRF et Settings dans un backend installé, avant de déclarer le sous-lot entier convergé. Le scénario synthétique ci-dessus n'est **ni une sauvegarde ni une restauration d'une vraie base Cabinet**. Ne pas toucher à une vraie DB en l'absence de preuve et d'accord distincts.

**Décision** : autorité du propriétaire pour désactiver uniquement, aucun mécanisme de distribution clinique. LOT04.8-B / LOT04.8 GLOBAL toujours OPEN, impression et release NO-GO.
