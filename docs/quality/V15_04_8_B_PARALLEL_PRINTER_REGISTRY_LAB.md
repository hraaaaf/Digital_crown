# V1.5-04.8-B — Inventaire imprimantes Cabinet : piste parallèle (LAB)

Base exacte figée : PR #849 HEAD `673e908713b6995afd68d42e8aa8abfa28b76c36` (empilée sur PR #840 encore DRAFT). Aucun merge/master/Vercel et aucun usage de données réelles.

## Objectif observable
Préparer un registre persistant tenant-scoped de cibles imprimantes et de leurs métadonnées **sans les certifier physiquement**, avec contraintes de tenant, unicité, revision CAS et audit. Les seules Stations approuvables sont celles du registre `workstation_modes` réelles et non révoquées. L'état initial de toute imprimante doit rester **`disabled` / `uncertified`**, y compris les destinations `near_station` et `reception`.

## Frontière stable consommée par 04.8-C
Cette piste fournit, à terme, une décision serveur `PrinterTarget` (tenant, printer_id, location, station_id, enabled, secure_release_verified, private_channel_verified, staff_supervised) déjà utilisée par `can_offer_print`. Elle ne publie aucun PDF ni capacité de spool ; `can_offer_print=True` signifie « peut proposer », **pas** « peut imprimer ». 04.8-C doit revalider cette décision au moment du job et de sa libération.

## Requis logiciel indépendant du matériel
1. Révision atomique et liens réels `tenant_id ↔ station_id`, changements/permissions/audit sous propriétaire racine. Empêcher client/browser d'écrire `verified`, `staff_supervised` ou flag de canal privé.
2. Recensement `printer_id`, fabricant/modèle, driver et mode `near_station/reception` sans identification clinique ; champs descriptifs **jamais suffisants pour activer**.
3. Attestation séparée d'un simple enregistrement : **pas de certification fabriquée par un test unitaire/CI**. Source physique vérifiée au **V1.5-10** avec opérateur, mécanisme de remise et preuve indépendante. Jusqu'alors, l'API GET/PUT actuelle demeure **désactivation uniquement**.
4. Tests SQLite/PostgreSQL synthétiques d'isolation tenant, conflits CAS, révocation de Station, suppression d'imprimante, modes disabled et refus de certification forgée. Tests multi-process après stabilisation du schéma.

## Contrôle intégration
Pas de mutation de `backend/main.py`, `alembic/env.py`, `backend/core/schema_runtime.py`, ou des modèles de #840 sans coordination. Ne pas modifier les fichiers que C et D possèdent. Ne pas fusionner cette piste avant validation sur HEAD commun, et laisser `GET PDF Station = 423` intact.

## Statut
**Piste créée, conception figée, développement/CI spécifiques À FAIRE.** 04.8 global OPEN. Aucun test physique dans cette piste ; tout test physique relève exclusivement du LOT10.
