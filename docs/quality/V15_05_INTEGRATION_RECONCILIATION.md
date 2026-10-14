# LOT05 — intégration provisoire Mapping Studio FR + essai SQLite fictif

**État : DRAFT / NO-GO intégration finale, aucune donnée réelle, aucun merge ou déploiement.**

## Sources observées (14 octobre 2026)

- Base commune : PR #854 `b7a918d3ae59bb0e3eae3827618e87a91b7de7ad`.
- Voie UI/auth : #879 → #880 → #883, HEAD `cc4db5cb1ff473bfa6a2859081ea98f9beed0ded`.
- Voie labo/HTTP/synthétique : #856 → #857 → #861 → #863 → #867 → #869 → #872 → #875, HEAD `5b56a3ea74955a181de11941ce6b6d3286bbc2fb`.
- Un **conflit sémantique** réel entre les deux voies : `frontend/src/features/admin/migration/MigrationMappingStudio.tsx`; l'ancien composant UI de #883 n'inclut pas les fonctions prévol et fichier SQLite ajoutées depuis #872/#875. **Ne jamais copier le composant #883 par-dessus #875.**
- Six autres fichiers UI/auth de #883 peuvent être portés sans recouvrement direct depuis #854 : politique owner et tests, tests Mapping Studio, harnais capture, harnais Chromium T2 et workflow T2.

## Arbitrage effectué dans ce candidat

1. Partir de #875, conserver **intégralement** `migrationGateway.ts`, les routeurs backend, la vérification SHA du seul fichier SQLite officiel fictif, les gardes propriétaire, la validation du sous-ensemble physique, l'absence d'import patient et le rollback dans le laboratoire.
2. Conserver dans le composant fusionné les fonctions `fetchMigrationPreflight`, `runSyntheticStaffRehearsal`, `downloadOfficialSyntheticFile`, `dryrunOfficialSyntheticFile`, `checkPreflight`, `checkFile`, `useObservedTarget`, et le bouton Import toujours **disabled**.
3. Reporter uniquement la présentation FR : `Correspondances de données`, `Choisir un fichier JSON`, `Choisir le fichier SQLite fictif`, `Contrôler le serveur sécurisé`, erreurs de métadonnées lisibles, statistiques « sans correspondance », titre et étapes responsive. Les identifiants des tables/colonnes restent les valeurs du schéma et **ne sont jamais traduits automatiquement**.
4. Conserver `Import réel interdit`, le statut en cours de construction, le message de simulation purement fictive, ainsi que l'interdiction de tout import clinique. Les `input[type=file]` sont seulement **visuellement masqués** (`sr-only`), gardent le focus clavier, les événements `change`, les gardes d'activation et des `label[for]` français. L'entrée SQLite reste désactivée tant que le téléchargement officiel n'est pas validé.
5. Aligner les tests et harnais **05.5, 05.6, B1, T2** sur les nouveaux libellés sans affaiblir les assertions sur données synthétiques et droits d'accès.

## Contrats et preuves à obtenir sur le HEAD final de cette branche

- **REQUIRED — Mapping B1** : Node 20 et Node 22, contrat 25/25 (2 suites), TypeScript, 4 captures AVANT/APRÈS en 390×844 et 1280×900 ; zéro import possible et aucune API patient déclenchée par l'import JSON.
- **REQUIRED — T2 App shell** : vraie page de login React, vrai backend `backend.main` isolé, propriétaire autorisé / ADMIN employé refusé en navigation et route, 390/1280, vraie visibilité du tableau de bord employé après redirection, sélecteur FR ouvrable.
- **REQUIRED — Gateway 05.5** : prévol serveur lecture seule, authentification propriétaire, mauvaise révision/permission refusées, aucune donnée clinique importée ; capture responsive et CI ciblée.
- **REQUIRED — Fichier 05.6** : 100 patients + 200 RDV **fictifs** exclusivement, SHA local et canonique serveur, MIME/limite et données invalides rejetés, PostgreSQL Alembic synthétique et tests HTTP auth, rollback zéro patient/RDV, visuel 390/430/768/1280 et 100/200% selon le workflow.
- **REQUIRED — CI Scope** : pas d'extension de gate sans preuve. Un changement de SHA invalide les anciennes approbations visuelles, à refaire sur ce candidat.
- **EXPERIMENTAL** : M6-I biométrie, hors du périmètre de LOT05. Un `skipped` n'est ni un PASS, ni un bloqueur LOT05 par défaut.
- **HORS SCOPE / non certifié** : import de données réelles, activation clinique, sauvegarde vraie base, SQLCipher réel du cabinet, Zoom natif, Pocket mobile, FUE/LOT04 et déploiement Vercel.

## Décision de clôture

Ne jamais déduire `GO` des CI vertes des deux branches parentes : elles certifient des arbres Git différents. La PR d'intégration doit réussir ses tests exact HEAD, fournir ses propres captures, faire l'objet de deux lectures adversariales A (protection/tenants) et B (UX/preuves) puis être **explicitement approuvée visuellement**. Les branches parentes restent ouvertes. L'ordre de fusion interne et la base stable seront réconciliés **après** validation, pas supposés. Aucun merge depuis ce document.

## Intégration master après LOT04 — candidat de vérification, 14 octobre 2026

- Origine exacte de ce candidat : `master@55b1985fefbd6d3522813d123985ea3f094d9012` (LOT04 #882 déjà MERGED) ; la présente intégration ne modifie aucun code LOT04.
- Source LOT05 consolidée : `#885@2f2504667fdc5368c576b41a1933c1b0cff6f36e`, dont les 7 REQUIRED techniques sont SUCCESS sur le SHA de source. Cette réussite **ne certifie pas** le candidat master ; le gate humain de #885 est FAIL et ne doit pas être hérité.
- Reconciliation observée depuis l'ancien ancêtre `master@c0d47f4832e6da2211c6f94eb88f0db56fcaebb6` : 68 fichiers LOT05, 214 chemins ajoutés/modifiés sur master, intersection unique `backend/main.py`. Les 67 autres chemins sont reportés uniquement depuis le LOT05 certifié ; il ne faut jamais écraser le fichier main.py de master par le main.py de la branche antérieure.
- `backend/main.py` du candidat conserve l'enregistrement existant `station_print_config_admin.router` avec son préfixe `/api/admin` et ajoute exclusivement `legacy_migration_router.router` sous `/api/migration`. Toute activation d'import réel demeure interdite.
- Retouche UX candidate uniquement : sur petit écran, présenter l'icône au-dessus du titre et réduire le H1 à `text-lg` (responsive `sm:text-3xl`) afin d'éviter les coupures de syllabes constatées en 390px et CSS root text 200% sur les captures AFTER de #885. Vérifier AVANT/APRÈS, 390/430/768/1280 et root text 100/200 ; **aucune garantie de certification sans nouveau test**.
- Nouvelle PR **Draft vers master**, CI complète sur SHA exact de cette combinaison, deux revues adversariales indépendantes seulement si deux réviseurs indépendants réels, sinon deux perspectives de revue interne clairement étiquetées et aucune prétention d'indépendance. Approbation humaine des nouvelles captures AFTER sur ce même SHA avant tout GO. Ne pas fusionner ni déployer sans décision explicite distincte.
