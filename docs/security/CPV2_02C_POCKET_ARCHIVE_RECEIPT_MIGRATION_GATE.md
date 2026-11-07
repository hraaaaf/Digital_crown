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

## Procédure de reprise sûre — reçu PROCESSING après interruption

Cette section est une **procédure d'investigation**, pas un outil de
déblocage automatique et pas une autorisation de modifier une DB cabinet.

1. **Geler la nouvelle écriture clinique** pour la même intention UUID.
   Pocket doit afficher `Archivage non confirmé`, conserver l'UUID associé
   au cabinet/appareil/patient et n'autoriser que la requête GET du reçu.
2. Vérifier que la session et l'appareil sont encore appairés et autorisés.
   Aucun contournement des permissions ou de la révocation n'est autorisé
   pour consulter un PDF ou une archive.
3. Sur une **copie isolée et restaurable** de la base chiffrée, relever
   l'UUID, `tenant_id`, `actor_id`, `device_id`, `patient_id`,
   `request_sha256`, `state`, `archive_id`, `archive_sha256`
   et les horodatages. Ne jamais inscrire le contenu médical ou les clés
   secrètes dans les logs de CI ou les tickets.
4. `COMPLETED` : exiger une ligne DocumentArchive active, rattachée au
   patient et à l'acteur attendus. Vérifier les octets PDF et leur SHA-256
   avant de conclure « archivé » ; la simple présence d'un fichier est
   insuffisante.
5. `PROCESSING` après crash : le reçu est un **verrou durable**.
   L'absence d'archive liée ne prouve pas l'absence de PDF orphelin ;
   un fichier orphelin ne prouve pas que la transaction SQL fut validée.
   Ne ni effacer le reçu, ni rendre la clé réutilisable, ni régénérer le
   document avant revue du dossier et résolution d'intégrité.
6. `REVIEW_REQUIRED` : conserver l'incident et les preuves, vérifier
   les archives et médias locaux selon la procédure de sauvegarde.
   Ne jamais transformer cet état en `COMPLETED` sans ligne active et
   empreinte PDF concordantes.
7. Toute procédure future de réparation doit être **un outil distinct**,
   audité, journalisé, soumis à une autorisation humaine et testé
   avec destruction du processus, base SQLCipher sur disque, course entre
   appareils et restauration de sauvegarde avant activation cabinet.

**Preuve machine disponible :**
`backend/tests/test_mobile_document_archive_receipts.py` contient
`test_fresh_process_after_worker_death_keeps_processing_lock` :
un second processus Python quitte réellement après commit du claim ;
une nouvelle session vérifie qu'un POST identique n'acquiert plus le
droit d'écrire (created=false), que l'état est `PROCESSING` et
qu'aucune archive_id n'est inventée. Ce test protège le refus de
rejeu, **pas** une réparation automatique des fichiers non référencés.

**GO/NO-GO :** garder l'archive inactive sur la DB réelle tant que
les essais d'intégration et la procédure de réparation avec reprise
sont non certifiés. Le praticien peut poursuivre l'aperçu PDF sans
activer l'archivage Pocket.

## Inspection forensique déterministe sans mutation (PR DRAFT)

Le module `backend/services/mobile_document_archive_forensics.py` fournit
`inspect_archive_receipt_read_only(db, tenant_id, actor_id, device_id, key,
media_root)`. **Ce n'est pas un endpoint Pocket ni une commande qui ouvre
une DB de cabinet.** Seul un processus local autorisé peut lui fournir une
**copie isolée** de la DB et du répertoire médias, sous un périmètre
`cabinet + acteur + appareil + UUID` explicite.

Résultat volontairement minimal : `receipt_state`, `verified_archive`,
`automatic_replay_allowed=false`, et un code de décision. Aucune donnée
identifiante, aucun chemin, aucun octet clinique ni hash médical n'est
publié dans l'objet de preuve. Le traitement effectue uniquement SELECT,
stat et lecture des fichiers bornés, jamais de COMMIT, UPDATE, DELETE,
unlink, rename, ni POST. Il refuse explicitement toute cible de DB
non attestée isolée via le garde runtime et toute session SQL contenant
des objets en attente (new, dirty ou deleted) ; les SELECT sont exécutés
sans autoflush. Ce refus vaut aussi pour les copies de DB sans attestation
d'isolation : aucune voie de contournement n'est ajoutée.

Les décisions sont **distinctes** :

- `HOLD_FOR_MANUAL_REVIEW` : `PROCESSING` ou `REVIEW_REQUIRED` sans
  archive SQL liée. Le helper n'affirme **jamais** l'absence d'un PDF
  orphelin après un crash. Il conserve le verrou; pas de rejeu.
- `EXISTING_ARCHIVE_VERIFIED` : `COMPLETED` avec patient du même
  cabinet, type, acteur, ligne d'archive active, chemin borné,
  fichier PDF et SHA-256 concordants. Il constate une archive existante,
  **sans** accorder une nouvelle autorisation d'écriture.
- `PATIENT_SCOPE_MISMATCH`, `ARCHIVE_ROW_MISMATCH`,
  `INCONSISTENT_RECEIPT_MANUAL_REVIEW`, `UNSAFE_ARCHIVE_PATH`,
  `MISSING_OR_INVALID_PDF` ou `PDF_HASH_MISMATCH` : anomalie
  nécessitant une investigation humaine, jamais un effacement ou
  une promotion automatique en `COMPLETED`.

L'activation de l'archivage Pocket vérifie maintenant **le schéma complet
et la contrainte SQL UNIQUE (cabinet, acteur, appareil, clé)**, pas
seulement le nom de table. Un schéma incomplet ou sans contrainte reçoit
HTTP 503; aucun fallback ni migration automatique. Tests négatifs :
`backend/tests/test_mobile_document_archive_receipts.py` et
`backend/tests/test_mobile_document_archive_forensics.py`.

### Human gate de résolution réelle

Même si un diagnostic sur copie est `HOLD_FOR_MANUAL_REVIEW`,
**interdiction de recréer automatiquement** un certificat, une ordonnance
ou un devis. Le propriétaire/administrateur doit approuver un dossier
de résolution comprenant l'inventaire signé des archives et médias
associés, les copies sauvegardées/restaurées testées, l'explication
de l'état SQL et un plan réversible. Un processus `PROCESSING`
sans archive liée ne démontre **pas** qu'aucun PDF n'a déjà été produit.
Le code et les tests de cette PR ne fournissent pas de mécanisme de
réparation automatique : ce gate reste explicitement ouvert.

