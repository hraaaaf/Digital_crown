# P2ter — audit read-only des archives céphalo après crash (étape 1/3)

Statut : **LABORATOIRE, NON CERTIFIÉ CABINET**. Cette procédure ne modifie **aucun fichier ni archive**. Elle ne remplace pas la sauvegarde + restauration d'une vraie base de cabinet dans un environnement isolé ni la validation humaine.

## Problème et invariant

`ArchiveService.archive_document(..., created_file_paths=...)` écrit un PDF puis valide les métadonnées et `CephaloArchiveClaim` en une transaction SQL. Une exception ordinaire déclenche la vérification SQL avant suppression des fichiers temporaires détenus exclusivement par la requête. Un `SIGKILL`, coupure secteur ou crash OS **court-circuite ce gestionnaire** et peut laisser des octets non référencés, pas forcément supprimables.

Invariants : **aucun doublon** de `patient_id/analysis_id/revision` en DB, **aucune suppression automatique** des anciens PDF, **aucun PDF déjà référencé effacé**. Une erreur de DB est un blocage, pas une preuve d'orphelinat.

## Inspection autorisée en laboratoire

1. Arrêter tous les processus d'écriture ; copier la DB complète et l'arborescence média sous isolation, sans désactiver SQLCipher. Sauvegarder leurs empreintes, secret de copie isolé, rôles minimaux, et tester la restauration. **Ne jamais accéder ici à la DB live.**
2. Vérifier l'unique tête de schéma `ceparch0001` ; le runtime refuse les bases plus anciennes tant qu'une migration **explicite et approuvée** n'a pas été répétée sur une copie conforme.
3. Sur la copie et une session SQLAlchemy **en lecture seule**, appeler `backend.services.archive_service.audit_cephalo_archive_after_crash(db, archive_root=path_to_copied_media_archives, minimum_age_seconds=3600)`. Le résultat est **confidentiel**, ses chemins ne doivent pas être envoyés dans CI, logs ou captures. Le champ `suspected_count` suffit à un bilan public.
4. L'audit inspecte uniquement les PDF sous `<archive_root>/<patient_id>/RAPPORT_CEPHALO/<YYYY>/<M>/<fichier>.pdf`, les compare à **toutes** les références `DocumentArchive.file_path` et ignore les fichiers récents/symlinks. Il conserve les candidats sur disque. Un document référencé n'est **jamais** qualifié orphelin.
5. Toute hypothèse d'orphelinat nécessite une vérification manuelle de l'ancien dossier patient, du hash, des archives historiques, des backups et des écritures in-flight. La **quarantaine/suppression/liaison SQL** est hors de ce sous-lot tant qu'il n'existe pas de décision opérateur explicite et trace d'audit. Ne pas inventer d'archive patient à partir d'un fichier isolé.

## Preuve de laboratoire

`backend/tests/test_cephalo_archive_crash_audit.py` : un vrai sous-processus écrit et `fsync` un faux PDF, puis s'arrête par `SIGKILL`. Après vieillissement synthétique, audit détecte l'orphelin **sans l'effacer**, préserve un PDF connu de la base, exclut les fichiers récents, et échoue si DB indisponible. Vérifier uniquement le run GitHub associé au **HEAD exact**.

## Réserves / GO-NO-GO

- L'audit est un **outil de détection** ; la réparation autonome et la résilience coupure au moment du COMMIT restent non démontrées.
- Le test PostgreSQL compare deux connexions sur une table de revendication clonée ; pas encore tout le chemin FastAPI/JWT sur PG.
- Migration SQLCipher éprouvée sur une copie **synthétique minimale**, pas sur la sauvegarde restaurée du cabinet.
- PR #955 DRAFT et PR compagnon du gate trusted #959 DRAFT ; l'approbation visuelle humaine du HEAD exact ne peut pas être fabriquée.
- Aucun merge, Vercel, installation cabinet ni parité clinique tant que les gates requis sont ouverts.

Registre : `techdoubt.md` dans la branche de travail.
