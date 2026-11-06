# CPV2-02C — Gate de migration du registre d'archives Pocket

**État : PROPOSITION, NON APPLIQUÉE EN CABINET.** Cette PR est DRAFT. Aucune
migration de données patient, aucun déploiement, aucun changement de production
n'est autorisé par le GO d'implémentation/test isolé du 6 novembre 2026.

## Décision de sécurité

L'archivage Pocket est **fail-closed**. `POST /api/mobile/documents/archive`
requiert un `Idempotency-Key` UUIDv4. L'absence de la table locale
`mobile_document_archive_receipts` entraîne HTTP **503**, jamais un
`create_all()` ou une migration silencieuse pendant une requête.

L'aperçu `POST /api/mobile/documents/preview` reste sans archivage et ne
dépend pas de cette table. Le Desktop et ses contrats documentaires ne sont
pas modifiés par le contrat de clé Pocket.

## Table additive proposée

Modèle SQLAlchemy canonique : `backend/services/mobile_document_archive_receipts.py`.
Le modèle est importé à la demande par le chemin Pocket et n'est **pas**
ajouté aux imports généraux de `backend/models.py`.

DDL SQLite/SQLCipher à préparer dans un *plan d'intervention approuvé* :

```sql
CREATE TABLE mobile_document_archive_receipts (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    tenant_id INTEGER NOT NULL,
    actor_id INTEGER NOT NULL,
    device_id VARCHAR(128) NOT NULL,
    idempotency_key VARCHAR(36) NOT NULL,
    patient_id INTEGER NOT NULL,
    document_type VARCHAR(24) NOT NULL,
    request_sha256 VARCHAR(64) NOT NULL,
    state VARCHAR(24) NOT NULL,
    archive_id INTEGER,
    archive_sha256 VARCHAR(64),
    created_at DATETIME NOT NULL,
    completed_at DATETIME,
    CONSTRAINT uq_mobile_document_archive_intent
       UNIQUE (tenant_id, actor_id, device_id, idempotency_key)
);
```

Ce schéma ne doit être installé que par une procédure DBA vérifiée,
avec contrôle du schéma existant, sauvegarde chiffrée et restauration prouvée.
La table contient des métadonnées médicales (patient_id, type, acteur) :
**stockage local protégé, mêmes restrictions que les dossiers patients**.

## Comportement métier

1. Le téléphone sauvegarde l'UUID opaque localement, puis émet un seul POST.
2. Le backend valide l'identité Pocket appairée, les permissions de type,
   le patient et le cabinet avant de créer un reçu `PROCESSING` unique.
3. `ArchiveService.archive_document` rattache le numéro d'archive et le
   SHA-256 du PDF au reçu `COMPLETED` **avant le même commit SQL**.
4. Une réponse perdue se récupère par `GET
   /api/mobile/documents/archive/receipt/{uuid}`. Même session appairée,
   acteur, cabinet, droits courants, révocation et patient sont revérifiés.
   Le PDF est servi seulement si la ligne SQL active et le SHA-256 correspondent.
5. Le même POST avec le même UUID et les mêmes données retrouve le document
   sans nouvelle génération; UUID identique avec données divergentes => 409.
6. `PROCESSING` ou `REVIEW_REQUIRED` n'autorisent **aucun rejeu automatique**.
   Une erreur après COMMIT n'efface jamais un reçu déjà `COMPLETED`.
7. Les notes d'honoraires, encaissements et remplacements de documents
   restent exclus du Pocket.

## Risques et limites encore ouverts

- Un crash **avant** le commit SQL laisse un reçu `PROCESSING` :
  intervention humaine/reconciliation requise, jamais abandon implicite du
  verrou ni deuxième génération. Une procédure de clôture administrateur
  doit être spécifiée, auditée et testée avant ouverture cabinet.
- Les fichiers PDF créés avant un crash et non référencés en SQL exigent
  une politique de nettoyage local sûre (pas de suppression sans preuve).
- Pour une activation complète, il faut tester crash/restart SQLCipher sur
  disque, verrouillage d'écriture, coupure HTTP après commit, double POST
  concurrent, revocation, séparation tenant et validité des PDF.
- Une FUE navigateur↔FastAPI↔SQLite authentifiée reste nécessaire :
  FUE-I existante utilise un backend simulé. La FUE physique iPhone/Android
  est réservée au LOT10 conformément au canonique.

## GATE HUMAIN AVANT CABINET

- [ ] Revue indépendante sécurité/integrité de la migration et de sa rollback.
- [ ] Backup chiffré du cabinet testé, SHA256 et restauration vérifiée.
- [ ] SQLCipher et SQLite sur disque : FUE de crash/restart, audit de l'intégrité.
- [ ] Accord explicite pour **appliquer** la migration au cabinet visé.
- [ ] Exécution surveillée hors données patients de test non autorisées.
- [ ] CI exact SHA, FUE intégration et contrôle post-migration.
- [ ] Accord explicite distinct de merge et de mise en production.

La création de la table dans une **SQLite de test jetable** est la seule
opération autorisée dans cette PR jusqu'à ce gate. Le dossier canonique de
reprise reste la page Notion CROWN POCKET V2 unique.
