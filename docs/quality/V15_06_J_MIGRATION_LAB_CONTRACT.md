# V1.5 / LOT06-J — Migration transactionnelle *simulée* (LAB-ONLY)

Scope : modèle **en mémoire** pour des images et des clés **synthétiques** ; tous les checkpoints sont des objets Python immuables. Ce contrat NE constitue PAS une migration déployable ni une activation clinique.

## Contrat de la machine d'états

- SOURCE : blob DC6A préalablement authentifié avec clé legacy explicite, empreinte SHA-256 de ce blob et SHA-256 du clair attendu. Source conservée **en mémoire** ; clé legacy exigée à chaque appel et **non sauvegardée** par le prototype.
- PREPARED : rewrap DC6A vers un candidat DC6B avec key_id opaque, clés différentes, authentification AES-GCM AAD de cabinet/poste/capture, intégrité du clair et empreinte du candidat. **Seule la copie candidate existe** ; lecture active reste DC6A.
- VERIFIED : le candidat et l'original sont relus, authentifiés et comparés avant éligibilité à COMMIT. Lecture active reste DC6A.
- COMMITTED : le marqueur **simulé** rend DC6B actif ; le blob DC6A et la possibilité de rollback sont conservés **si la clé legacy externe demeure disponible**. Pas de bascule avant VERIFIED.
- ROLLED_BACK : action explicite de l'opérateur (booléen de test, pas vraie authentification), source DC6A authentifiée, candidat retiré du *snapshot*, revision incrémentée. Ce prototype ne supprime **jamais** un fichier ni une clé réels.

Les transitions exigent une révision attendue correspondant au snapshot, et les readers revalident la source et le candidat lorsqu'il existe. Un checkpoint PREPARED ou VERIFIED ne devient **jamais COMMITTED automatiquement** au redémarrage. La simulation injecte une interruption après SOURCE/PREPARED/VERIFIED/COMMITTED et teste l'inspection/reprise/rollback. Une copie candidate corrompue, tronquée ou absente interdit redémarrage/commit, mais n'empêche pas un rollback *explicitement autorisé* si la source historique authentifiée et sa clé externe demeurent disponibles. Aucune lecture ne retombe automatiquement de DC6B à DC6A en cas de perte de la clé cible.

## Limites déterminantes — NO-GO clinique

Une révision en mémoire, des empreintes SHA-256 non signées et un marqueur immuable **ne prouvent pas** une transaction persistée, un verrou CAS interprocess, la résistance au rollback/replay de snapshots historiques, la résistance aux acteurs locaux disposant de droits d'écriture, ni une autorisation opérateur réelle. Aucun journal durable, fsync fichier/répertoire, os.replace, séquence NTFS/SQLite, antivirus, perte réseau, service account, DPAPI escrow, backup indépendant, identity HMAC stable sur rotation, audit patient, ledger clinique ni ACK serveur n'est implémenté. La clé legacy reste obligatoirement disponible dans les opérations du modèle. Pour un futur design physique : préciser journal/ordonnancement d'écriture, crash windows, lecteurs concurrents, rétention et escrow des deux clés, empreintes authentifiées et journal anti-replay, identité de capture indépendante des clés, rollback autorisé/audité, recovery sur machine physique et protocole B2 confirmé.

**Preuves attendues** : GitHub Actions Linux et Windows sur **même SHA**, scénario complet, fautes injectées à tous les checkpoints, mauvaise clé, corruption des deux blobs, key_id/AAD, révision stale, commit anticipé, contrôle de non-branchement. Deux revues adversariales internes et confirmation sur SHA final. Ne pas présenter comme audit indépendant, production-ready ou certifié.
