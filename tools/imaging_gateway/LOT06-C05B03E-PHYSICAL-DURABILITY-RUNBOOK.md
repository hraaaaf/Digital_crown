# LOT06 C05B-03E — protocole de preuve matérielle sur poste de TEST

**Statut : protocole prêt à utiliser sur matériel dédié ; AUCUNE coupure physique réalisée par cette PR.**
Ne pas utiliser sur un cabinet en service, un poste patient ou des données cliniques.
La commande ne coupe **jamais** l'alimentation et ne modifie pas la base de l'application.

## Objectif et limites

Séparer quatre preuves qui ne sont **pas équivalentes** :

1. **CI Linux / processus** : reprise SQLCipher/AES-GCM après fermeture/redémarrage du seul programme, sans panne électrique.
2. **Preuve de poste réel** : version SQLCipher, OS, SSD, système de fichiers, politique WAL/NORMAL ou WAL/FULL, journalisation des barrières et de la chaîne d'alimentation.
3. **Preuve d'évènement externe** : capture indépendante avant l'évènement, observation horodatée de l'interruption par un opérateur autorisé, récupération à froid.
4. **Revue indépendante** : validation matérielle/driver/flush, sécurité, conformité et décision humaine. Un test qui revient avec les reçus intacts ne peut **jamais** s'auto-certifier.

Selon [SQLite PRAGMA synchronous](https://www.sqlite.org/pragma.html), WAL/NORMAL ne protège pas tous les COMMITs contre une coupure d'alimentation ; WAL/FULL synchronise le journal WAL par transaction, à condition que la pile OS/VFS/stockage respecte ses garanties. Tester un seul matériel ne certifie pas tous les supports.

## Préconditions humaines et de sécurité

- Un **poste de laboratoire sacrifiable et non clinique**, aucun patient, aucune application Digital Crown en production, aucun utilisateur actif.
- Autorisation de l'administrateur du matériel et opérateur compétent ; supervision de l'essai ; alimentation, périphériques et stockage documentés.
- Avant essai, sauvegarde du poste de test, plan de retour arrière, contrôle de risques électriques selon procédures du site, sans manipulation de circuits sous tension.
- Support de preuve **indépendant de la machine éprouvée** pour copier le manifeste *avant* l'interruption ; idéalement autre appareil / autre stockage physique, avec horodatage externe.
- Linux/POSIX est le **seul environnement pris en charge** par le collecteur actuel (fsync fichier + répertoire). Windows/NTFS reste BLOQUÉ ; ne pas interpréter un test Linux comme certification Windows.
- La clé du banc est dans `lab-secrets.private.json` : secret **synthétique** local, permissions 0600 ; **ne jamais joindre ce fichier** à un ticket, artifact, capture ou Notion. La copie de preuve externe ne contient aucune clé.

## Séquence à réaliser par l'opérateur (plus tard, sur poste physique)

Depuis la racine du dépôt sur le poste TEST, avec `sqlcipher3` et `cryptography` installés :

```bash
export ENVIRONMENT=test
export DIGITALCROWN_ISOLATED_RUNTIME=true
export DC06C05B03E_TEST_ONLY=1

# Choisir un nouveau répertoire VIDE dont le nom commence par lot06c05b03e-
# IMPORTANT : --hold laisse le processus/connexion SQLCipher actifs.
python -m tools.imaging_gateway.qa_physical_power_witness_lab prepare \
  --root /mnt/test-bench/lot06c05b03e-full-01 --mode FULL --hold
```

Dans un second terminal, **avant l'évènement**, copier `pre_event_manifest.json` sur le support indépendant, par un moyen autorisé et contrôlé. Vérifier cette copie sur la machine témoin ; noter dans le journal indépendant sa somme SHA-256, l'identifiant de l'essai, l'heure, le modèle du poste et le SSD. **Ne pas copier le fichier des secrets**. Si le collecteur a été arrêté normalement avant la coupure, ne pas considérer cet essai valide : la fermeture peut déclencher un checkpoint WAL.

L'interruption réelle n'est pas une commande de ce dépôt. Elle relève exclusivement du protocole de laboratoire approuvé, sous supervision humaine, sur machine dédiée. **Ne pas couper l'alimentation du cabinet ou d'un dispositif médical**. Noter l'instant du COMMIT, le délai avant interruption, si le processus était encore actif, la preuve d'interruption et les conditions du stockage.

Après redémarrage complet, recopier le manifeste depuis le support témoin vers un chemin **hors du répertoire testé**, puis exécuter :

```bash
python -m tools.imaging_gateway.qa_physical_power_witness_lab recover \
  --root /mnt/test-bench/lot06c05b03e-full-01 \
  --witness /mnt/independent-witness/full-01-pre-event.json
```

Une sortie `RECOVERY_OBSERVED_EVENT_UNVERIFIED` signifie seulement que SQLCipher, reçu/audit/outbox et média AES-GCM correspondent à la copie externe. **Elle ne valide ni la coupure, ni la durabilité clinique.** En cas de contradiction, `NO_GO` / code de sortie 2 : ne pas générer ni valider de nouveau reçu patient.

Effectuer une **nouvelle** expérience avec un répertoire vierge pour `--mode NORMAL`. Les deux modes sont des comparateurs, pas deux configurations appliquées au cabinet. La politique runtime Digital Crown demeure WAL/NORMAL tant qu'une décision d'architecture distincte n'est pas approuvée.

## Matrice FUE de matériel requise (en dehors de cette CI)

| Scénario | Matériel / preuve exigée | Décision |
|---|---|---|
| FULL : COMMIT, processus actif, interruption physique externe | Horodatage externe, WAL, identité du SSD/VFS, récupération froide, cohérence média/reçu | En attente opérateur |
| NORMAL : même scénario, banc vierge | Même instrument, même méthode ; évaluer pertes de COMMIT sans affirmer qu'une absence de pertes prouve durable | En attente opérateur |
| Interruption pendant la fenêtre autour du COMMIT | Instrument de contrôle / témoin réellement indépendant, incident reproductible | Non exécuté |
| COMMIT ambigu, reçu absent après redémarrage | Fail-closed, aucun ACK anticipé, reprise avec même identité vérifiée | Non exécuté |
| Reçu présent et média manquant / AES altéré | Bloquer accès, consigner incident, préserver preuve ; pas de succès clinique | CI synthétique seulement |
| WAL/sqlcipher illisible / corruption / clé perdue | Aucune attestation ; restauration et audit séparé, sans contourner sécurité | Non exécuté |
| Windows / NTFS / SSD à cache volatile | Barrières fsync/FlushFileBuffers et VFS réellement vérifiés par OS/hardware, pas extrapolés de POSIX | BLOQUÉ |
| Pile de certification clinique (staff/device, migration et permission) | Tests d'identité réels, revue de sécurité, FUE humaine d'autorisation | BLOQUÉ |

## Dossier de preuve à réunir hors GitHub CI

Identifiant d'expérience, date en UTC, opérateur et revueur distincts, approbation d'essai ; matériel (fabricant/model/firmware SSD, cache, alimentation, contrôleur), OS, filesystem, SQLCipher et VFS ; dépôt SHA exact ; paramètre `PRAGMA synchronous` réellement observé sur la connexion qui COMMIT ; journal témoin avant coupure, copie indépendante et empreinte de manifeste ; photographie/capture ou mesure indépendante de l'évènement ; durée entre COMMIT et coupure ; résultat à froid ; exceptions, pertes ou corruptions ; conclusion signée **distincte** du statut du collecteur.

Ne jamais publier clé de banc, chemins privés, identifiants personnels ni média du cabinet. Le fichier JSON des tests CI doit conserver tous les indicateurs de certification `false`.

## Gates de clôture

**C05B-03E LAB GREEN** : tests négatifs CI sur SHA exact + artefact JSON démontrant que le collecteur n'émet pas de faux GO ; script et protocole relus.

**C05B-03E PHYSICAL GREEN** : essais réels sur configurations approuvées, preuve indépendante, revue humaine et décision signée distincte. Aucun mécanisme de cette PR n'autorise à déclarer automatiquement cette seconde gate.

**LOT06 PRODUIT NO-GO** tant que coupure physique, Windows si cible, véritable autorité clinique et migration, fsync/média et revue humaine ne sont pas validés. Pas de merge/déploiement implicite.
