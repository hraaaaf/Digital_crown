# Digital Crown — V1.5-04.8-B — Configuration de l'impression (contrat isolé)

**Statut : B1 implémenté sur PR #849, B2 persistance/API/UI NON IMPLÉMENTÉS ; 04.8-B GLOBAL OUVERT / NO-GO impression.** Cette note est un contrat d'intégration et non une habilitation matérielle.

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
