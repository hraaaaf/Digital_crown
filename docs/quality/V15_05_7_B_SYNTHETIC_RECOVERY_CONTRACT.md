# Digital Crown LOT05.7-B — laboratoire de restauration SQLite fictif

**Périmètre strict : 05.7-B**, superposé à la PR #963 05.7-A. Toutes les bases sont générées dans un répertoire temporaire isolé, avec 100 patients et 200 rendez-vous **fictifs**. Aucune route d’import, aucun accès clinique, aucune migration Alembic, aucun changement UI ou déploiement. **Import réel NO-GO.**

## Preuves du laboratoire

- SQLite physique sur disque et mode **WAL avec frames commitées au moment du backup** ; vraie API `sqlite3.backup()`, contrôle intégrité/FK et SHA256 des octets de la copie.
- Restauration sur **autre fichier**, preuve digest logique + 100 patients/200 RDV/1 ledger/0 orphelins, fermeture et réouverture, puis lecture dans un **processus Python indépendant**.
- `os._exit(77)` dans un processus qui a commencé un INSERT non commité, puis contrôle de l’absence du patient partiel ; injection d’arrêt entre patients et RDV et rollback transactionnel.
- Replay de lot identique = NOOP ; même identifiant avec payload changé = refus ; contraintes FK composites interdisant RDV orphelin et liaison inter-tenant.
- Corruption des octets, modification logique de copie SQLite pourtant lisible, altération FK avec SHA recalculé = refus ; source ayant changé avant backup = refus.
- Interdiction d’écraser une sauvegarde/cible ; refus de chemin externe, traversée et symlink quand disponible, et nettoyage d’une publication volontairement interrompue.

La seule suite exécutable est `backend/tests/test_legacy_sql_057b_wal_recovery_lab.py` (**22 cas**), Python standard sans import des modules Cabinet. La CI spécifique teste **Linux et Windows, Python 3.11 et 3.12, HEAD exact**. Un SKIP symlink Windows, si les privilèges OS le refusent, n’est pas une preuve de protection contre reparse/junction Windows.

## Limites / BLOCKERS conservés

La fixture et le répertoire temporaire ne sont **pas** un moteur autorisant des bases externes. SQLite non chiffré n’est pas SQLCipher, ni PostgreSQL/pitr ni un backup vrai Cabinet. `os.replace` en mono-processus n’est pas un protocole durable contre TOCTOU/reparse, crash matériel ou concurrence multiprocess ; ni fsync de répertoire, ni RPO/RTO vérifiés, ni coffre médias. Un SHA calculé/recalculé par le même acteur ne prouve pas l’authenticité indépendante du snapshot.

**05.7-C requis avant toute activation :** provenance et légalité du dump, contrôle runtime du propriétaire et de son tenant, schéma Alembic physique complet, backup **ET restauration sur copie isolée de la vraie technologie**, isolation cabinet, contraintes SQL replay, mapping patient/praticien/actes/finance/médias, adjudication de doublons, contrôle humain distinct et plan de reprise/compensation. Toutes les capacités d'import et CTA restent désactivés. Aucun envoi de données médicales dans CI/GitHub/Notion.

**Revues :** deux perspectives adversariales **internes** A sécurité/Windows/transactions et B restauration/preuves métier, notes strictes sur HEAD identique ; jamais qualifier de revue externe indépendante ni de GO clinique.