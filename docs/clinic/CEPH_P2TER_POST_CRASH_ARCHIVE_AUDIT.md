# P2ter — récupération documentaire après crash et répétition sur copie chiffrée

**Lot : CEPH-FAC-PARITY / P2TER-ATOMIC-ARCHIVE — étape 1/3.**
**Statut : procédure proposée / laboratoire synthétique seulement, PAS de validation cabinet.**
Le périmètre automatique est **strictement READ_ONLY** : détecter les anomalies,
préserver les octets et stopper en cas de doute. Aucune suppression, restauration
ou liaison SQL de document patient n'est autorisée par cette procédure seule.

## Risque réel / limites de l'atomicité

La transaction SQL empêche deux requêtes concurrentes d'obtenir le même
`patient_id/analysis_id/revision`. L'écriture du PDF sur disque n'appartient
cependant pas à cette transaction. Un `SIGKILL` ou une perte d'alimentation
après création exclusive (`open('xb')`) et avant COMMIT peut laisser un PDF
non référencé. À l'inverse, une sauvegarde incomplète des médias peut laisser
une **archive SQL référencée sans PDF présent**. Aucun de ces cas n'autorise
la reconstruction ou la suppression automatique d'une pièce clinique.

Les preuves [PG JWT #39147082461](https://github.com/hraaaaf/Digital_crown/actions/runs/39147082461)
et [gate visuel humain #39149254025](https://github.com/hraaaaf/Digital_crown/actions/runs/39149254025)
concernent le HEAD testé à l'époque ; après tout nouveau commit, vérifier le
HEAD de chaque run et la nouvelle attestation éventuelle.

## Préparation opérateur AVANT tout accès à un cabinet réel

1. **Autorisation explicite du responsable cabinet**, identité de l'opérateur,
   approbation de la fenêtre de maintenance et d'un second valideur pour toute
   décision qui affecterait un document patient. Sans ceci, arrêter ici.
2. **Quiescence** : fermer/suspendre tous les writers et connexions utiles,
   confirmer l'arrêt du service, geler les imports/archives, enregistrer l'heure
   et la version. Ne **jamais** copier seulement le fichier principal SQLite
   pendant que WAL/SHM contiennent des transactions en cours. Utiliser une
   sauvegarde SQLCipher cohérente supportée par la version du produit ou
   un snapshot froid de la DB et de ses fichiers associés, plus **toute**
   l'arborescence média. Si cette cohérence ne peut être prouvée, **NO-GO**.
3. Conserver la sauvegarde originelle chiffrée **en lecture seule**, avec
   empreintes SHA-256 de la base / fichiers annexes / médias, taille, schéma
   et inventaire local **confidentiel**. Détenir les clés uniquement via
   la procédure sécurisée du cabinet, sans les écrire dans GitHub, CI, logs,
   tickets ou prompts. Tester la restauration sur **une seconde copie isolée**.
4. Avant toute migration, vérifier sur **la copie restaurée seulement**
   le déverrouillage SQLCipher, `PRAGMA integrity_check`, la validité des
   références `PRAGMA foreign_key_check` et l'accès à des archives PDF
   factices ou autorisées. Toute anomalie bloque la migration et impose
   une revue opérateur. Vérifier séparément que l'original et son contenu
   n'ont pas changé (empreintes).
5. La version cible du schéma est `ceparch0002`. Sur **copie restaurée
   exclusivement**, effectuer la migration **explicite** `alembic upgrade head`
   sous les protections de la procédure de rehearsal. Vérifier de nouveau
   intégrité SQLCipher, absence de perte de lignes/document/claims, liens
   fichiers SQL et hashes média ; ne jamais déclencher de migration au
   démarrage de l'application. Ne pas considérer le laboratoire synthétique
   comme une sauvegarde fidèle du cabinet.

## Audit double-sens sur copie isolée (sans suppression)

Arrêter tous les writers **y compris sur la copie**. En session SQLAlchemy
de lecture seule, avec une arborescence archives copiée explicitement :

```python
from backend.services.archive_service import audit_cephalo_archive_after_crash
report = audit_cephalo_archive_after_crash(
    db, archive_root=path_to_restored_archives, minimum_age_seconds=3600
)
# Ne publier que des agrégats sans noms ni chemins patient.
counts = {
    "suspected_count": report["suspected_count"],
    "missing_referenced_count": report["missing_referenced_count"],
    "unverifiable_references_count": report["unverifiable_references_count"],
}
```

Le rapport complet comporte **des chemins et hash patients confidentiels** :
il reste seulement chez l'opérateur autorisé, hors CI et outils de partage.

- `suspected_count` : PDF présent sous
  `archives/<patient_id>/RAPPORT_CEPHALO/<YYYY>/<M>/*.pdf`
  sans référence SQL, assez ancien pour éviter les écritures récentes.
  **Ce n'est pas une preuve qu'on peut supprimer le fichier.**
- `missing_referenced_count` : PDF céphalo déclaré dans `DocumentArchive`,
  référencé sous `static/archives/`, mais absent, ou chemin symbolique
  suspect dans la copie. **Ce n'est pas une preuve que le fichier n'existe
  nulle part dans les sauvegardes.**
- `unverifiable_references_count` : chemins céphalo historiques, hors
  arborescence auditée, non canoniques, ou dont le répertoire patient ne
  correspond pas à `DocumentArchive.patient_id`. **Ne signifie pas zéro défaut** :
  inspection manuelle complémentaire requise.
- Une base indisponible fait **échouer** l'audit, jamais « zéro anomalie ».
  Les symlinks d'entrée sont ignorés ; aucune suppression / aucun move.
- Contrôler également l'absence de PDF tronqué/corrompu via procédure
  opérateur de comparaison de hash, et la concordance des sauvegardes :
  l'audit double-sens n'est **pas** une certification de contenu PDF.

## Matrice de décision clinique (opérateur + second valideur)

| Observation sur copie | Action autorisée dans ce sous-lot | Ce qui reste interdit |
| --- | --- | --- |
| Trois compteurs zéro ; SQL et hash cohérents | Consigner résultats redigés, conservation des preuves, passer au gate suivant | Déclarer production sûre sans rehearsal cabinet et autorisation |
| PDF sans référence SQL | Conserver les octets ; comparer hors-ligne avec anciens index, backups, heure, étude, hash | Effacer, déplacer, attribuer à un patient ou générer une claim |
| Référence SQL sans PDF | Geler le déploiement ; rechercher copies chiffrées/restaurées et validation médicale | Insérer un PDF supposé, supprimer la ligne, réécrire la référence |
| Référence hors arborescence | Inventaire manuel des magasins historiques et rapprochement | La traiter comme saine ou orpheline par défaut |
| Base illisible, WAL incohérent, collisions, doute d'identité | STOP / NO-GO ; préserver snapshot, consulter DBA et responsable médical | Migration forcée, purge, réparation sans piste d'audit |

Toute réparation effective est **hors du chantier 1/3** tant qu'un plan de
restauration/reprise, la traçabilité patient et l'approbation opérateur n'ont
pas été autorisés explicitement. Après correction autorisée, nouveaux hashes,
preuves de restauration et nouveau contrôle sont obligatoires.

## Preuves automatiques distinctes de la validation cabinet

- `backend/tests/test_cephalo_archive_crash_audit.py` : vrai sous-processus
  `SIGKILL` après `fsync`, ancien PDF non référencé conservé ; PDF lié
  présent et absence de PDF lié, refus de suivre symlink, DB indisponible
  fail-closed. **Lecture seule, zéro octet supprimé.**
- `scripts/ceph_p2ter_sqlcipher_copy_rehearsal.py` : source **synthétique
  chiffrée**, sauvegarde scellée + restauration indépendante avec PDF
  synthétique, hashes de l'original et du média préservés, intégrité SQL
  avant/après, migration additive `ceparch0002`, unicité du claim.
  Cela **ne reproduit pas la complexité d'une vraie base de cabinet**.
- Le gate d'acceptation cabinet nécessite encore la **preuve d'une restauration
  fidèle de base cabinet**, l'inventaire de tous les médias et une décision
  humaine documentée quant à la reprise après crash. Aucun script CI ne
  prétend accéder à une base de patients réelle.

## Conditions de sortie / garde-fous

Gates REQUIRED sur HEAD exact : CI schéma, archive, Chromium + accord visuel
humain renouvelé si HEAD modifié. Revue adversariale **interne** de deux angles,
zéro BLOCKER restant **pour le lot clinique demandé**, opérateur cabinet
identifié et restauration réellement répétée sur copie cohérente. Les
gates expérimentaux restent non bloquants sauf risque réel sécurité/production.
**PR #955 DRAFT, parent #953 DRAFT. Aucun merge ni déploiement sans instruction
spécifique et preuves finales.** Réserves dans `techdoubt.md`.
