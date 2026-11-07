# CPV2-02C — Revue opérateur d'un reçu PROCESSING et de PDF orphelins

**Statut : protocole expérimental de diagnostic FUE-0, non déployé, non applicable au cabinet réel.**
Ni commande de réparation, ni migration, ni approbation de mise en service. Les fichiers/identités
cliniques réels sont interdits dans cette suite de test. PR DRAFT, pas de merge.

## GOAL / SUCCESS / PROOF

- GOAL : revue des reçus PROCESSING/REVIEW_REQUIRED et des orphelins sans supposer leur attribution.
- SUCCESS : anomalies classées sans mutation, sans autorisation de rejouer, supprimer ou restaurer.
- PROOF : 16 tests fictifs Windows/Ubuntu, logs GitHub Actions sur SHA exact.

Seul le périmètre documentaire Pocket est concerné : ordonnance, certificat, devis, libre
(aperçu + archivage) et note d'honoraires (aperçu seulement). Pas de céphalométrie
ni d'échéanciers Desktop dans le gate CPV2-02C.

## Procédure opérateur NON DESTRUCTIVE

1. **Préserver l'intention** : ne pas répéter le POST /api/mobile/documents/archive
   après timeout ou coupure. GET /api/mobile/documents/archive/receipt/{intent_key}
   est la seule reprise autorisée pour la session et l'appareil toujours habilités.
   PROCESSING/REVIEW_REQUIRED demeure verrouillé jusqu'à investigation.
2. **Constituer une preuve isolée** : pour le laboratoire, utiliser uniquement une base
   sqlite3 :memory: et un ZIP BytesIO avec patients fictifs. Une copie chiffrée
   cohérente de vrai cabinet exigerait un gate séparé explicitement approuvé.
3. **Distinguer sources** : le reçu indique l'intention tenant/acteur/appareil/UUID ;
   la ligne DocumentArchive affirme un lien SQL ; le PDF prouve des octets.
   Un nom, une date, une taille ou un hash orphelin ne prouvent JAMAIS le patient.
4. **Inventorier en lecture seule** avec le helper interne
   inventory_pocket_archive_readonly(connexion_isolee, zip_ouvert) : SELECT,
   contrôle des chemins, hash SHA-256 en streaming ; aucune extraction ni mutation.
   Ce n'est pas une route HTTP, un CLI de cabinet ni un outil de restauration.
5. **Trier sans autoriser** par triage_pocket_document_inventory(manifest) :
   HOLD_MANUAL_REVIEW si une anomalie existe ou si l'entrée est incomplète ;
   BYTE_MATCH_EVIDENCE_ONLY si toutes les entrées connues correspondent au bit près.
   Même le second verdict ne prouve ni snapshot exhaustif ni autorisation clinique.
6. **Conserver localement** identifiant interne d'incident, SHA des copies DB et ZIP,
   code source exact, motif et compte d'anomalies, opérateur et horodatage.
   Les identifiants patients et données médico-personnelles ne vont pas dans
   GitHub, Notion, les logs CI ou un service externe.
7. **Gate humain distinct** : intégrité et attribution de chaque dossier vérifiées
   par les responsables autorisés ; sauvegarde cohérente et rollback validés ;
   remédiation future auditable et réversible soumise à approbation explicite.
   Aucune opération corrective n'est exécutée par ces fonctions.

## Matrice de décision

| Indice | Verdict | Actions interdites |
| --- | --- | --- |
| PROCESSING ou REVIEW_REQUIRED | HOLD_MANUAL_REVIEW | Aucun nouveau POST, pas de promotion vers COMPLETED |
| UNLINKED_MEDIA | HOLD_MANUAL_REVIEW | Aucune réattribution patient, suppression, ni renommage |
| MISSING_MEDIA, SHA256_MISMATCH, SIZE_MISMATCH | HOLD_MANUAL_REVIEW | Pas de restauration forcée ou reconstruction silencieuse |
| AMBIGUOUS_PATH, CASE_ALIAS, UNSUPPORTED_SQL_PATH | HOLD_MANUAL_REVIEW | Pas de choix arbitraire d'un fichier |
| ZIP/manifeste vide, incomplet ou contradictoire | HOLD_MANUAL_REVIEW | Aucune validation par défaut |
| Conformité des octets dans un inventaire synthétique | BYTE_MATCH_EVIDENCE_ONLY | Pas de GO clinique, migration ou restauration |

**Invariant machine absolu :** allow_archive_replay=false, allow_sql_mutation=false,
allow_media_delete=false, allow_reassociation=false, allow_restore=false,
allow_clinical_release=false. Le résultat ne recopie ni chemin, nom, UUID, ID SQL
ni empreinte clinique du document. Une dérogation antérieure à une revue indépendante
n'est pas une revue de sécurité passée.

## Limites / Stop

Ces tests ne prouvent ni la complétude d'un dossier clinique, ni une sauvegarde
DB+médias atomique, ni le bon comportement en cabinet réel. Aucun système
de réparation, aucune interface opérateur validée ; mise en service NO-GO.
NEXT : analyser les résultats CI exact-SHA, préparer uniquement une qualification
sur copies synthétiques, puis décider séparément de la future migration/merge.
