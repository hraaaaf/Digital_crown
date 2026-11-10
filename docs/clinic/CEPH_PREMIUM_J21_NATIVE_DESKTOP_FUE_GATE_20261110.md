# DIGITAL CROWN — CEPH-PREMIUM J2.1 — FUE-G natif : preuve du blocage de version (2026-11-10)

## Décision, Goal, périmètre
**Décision unique :** vérifier si un exécutable Windows réellement certifié permet aujourd'hui le parcours Céphalo Premium J2.1 dans un cabinet totalement fictif et jetable, sans injecter de code non certifié ni accéder aux données cliniques. **Conclusion : NON**, blocage produit/release vérifié. FUE-1 React↔FastAPI sur navigateur local reste PASS indépendamment.

## Identités contrôlées
- Branche candidate : PR Draft #1253 `test/ceph-premium-j21-m2m6-isolated-20261109`, HEAD au contrôle `1ccfc012d2aab3894381221520b43dc750c7e184` (OPEN, DRAFT, pas de merge).
- Exécutable natif réellement disponible : `DigitalCrown.exe` certifié `INSTALLABLE_CERTIFIED`, source exacte **`e1a6af02dc7a32de74503451ad3265e5aa2a68d7`** datée du 28 octobre 2026, certification GitHub installable #40540917952.
- SHA-256 de l'exécutable : `FFA8E8B2BEA98DB279A9F6A2CA0FDB463FE501B7C9A44ACEB56DD9420E5D4BCD`.
- Ce package est **antérieur et différent** du HEAD J2.1. Il ne contient ni `backend/services/ceph_premium_scene_app_fue.py` ni `backend/routers/ceph_premium_scene_app_fue.py`. Même le code actuel de PR maintient la route et le viewer hors de l'interface clinique / des routes de production par conception de sécurité : une certification future du même SHA ne suffirait pas à elle seule à les monter.

## Vrai essai sur Windows / profil séparé (aucune donnée patient réelle)
- Avant essai : aucun `DigitalCrown.exe` actif et port cabinet 8005 libre.
- Nouveau profil sous **`%TEMP%\ceph-j21-native-fue-20261110-1ccfc012`**, quatre sous-répertoires `data`, `config`, `runtime`, `logs` distincts, cinq chemins explicites ; l'application reçoit uniquement ces chemins et un `--cabinet-env-file` absolu. `DIGITALCROWN_RESTORE_RESTART=1` désactive l'ouverture automatique de navigateur. Aucune configuration du vrai cabinet n'est utilisée.
- Premier lancement de **l'exécutable réel** avec `--initialize-new-cabinet` : environnement vierge créé avec secrets distincts ; arrêt fail-closed attendu car `clinical_vault.db` absente. Aucun schéma créé implicitement.
- Initialisation **uniquement** de la DB fictive isolée à partir du code certifié avec Alembic exact `upgrade head` : **112 tables**, head `neo000000032`, base SQLCipher sans en-tête SQLite en clair. Il ne s'agit pas d'une migration d'un cabinet clinique, ni d'une migration des données du cabinet.
- Nouveau lancement du même `DigitalCrown.exe` sur ce seul profil : processus natif vivant, **`GET http://127.0.0.1:8005/health = 200`**, `status=ok`, `db=ok`, `instance_id` correspond au profil fictif ; `GET /` interface = **200**.
- Tentative de route scène `GET /api/ia/analyses/1/premium-scene-fue?patient_id=1` = **404**. Les modules correspondants sont absents de cette distribution certifiée ; aucun endpoint exploitable pour le cycle ouvrir → modifier → sauvegarder → relancer → rouvrir. OpenAPI n'a pas été retenu comme preuve (lecture expirée) ; la conclusion est fondée sur l'identité/source certifiée et le 404 direct.
- Les preuves synthétiques sans secrets ni base sont dans `docs/clinic/evidence/j21_native_gate_20261110/certified_release_route_gate.json`. Aucune capture Desktop Céphalo n'est prétendue.

## Verdict
- Démarrage installable sur profil fictif + chiffrement + readiness : **PASS**.
- Existence du parcours Céphalo Premium au SHA certifié : **FAIL / route absente (404)**, bloquant vérifié.
- **FUE-G Desktop natif sur la scène J2.1 : NON EXECUTABLE dans ce package, reste OPEN/RED.** Ne pas cocher M6, ni M2–M5 faute de leurs validations produit ; pas d'affirmation d'intégration clinique.
- Priorités conservées : sécurité patient, intégrité, preuve. Pas d'injection dans les fichiers certifiés, pas de base clinique, pas de production, pas de merge, pas de déploiement.

## Next exact (sans contourner la certification)
1. Préparer et tester un **raccordement FUE explicitement isolé** dans l'architecture de packaging native, avec source vérifiée, JWT, schéma app local et viewer, aucun accès aux bases de cabinets et port local strict, sans enregistrer la route dans l'application clinique normale.
2. Obtenir le contrôle de provenance et une **certification appropriée du binaire exact** portant ce raccordement test. La certification installable actuelle requiert `refs/heads/master` et ne peut être fabriquée depuis cette PR Draft ; ne pas forcer la signature ou l'identité d'une autre version.
3. Toute fusion sur master / activation clinique / mise en production **requiert l'autorisation explicite de l'utilisateur**. Réexécuter FUE-G avec binaire exact, arrêt complet, réouverture, SHA image/scène, captures identiques aux viewports concernés et refus A/B/X.
4. Revue indépendante médicale obligatoire pour cartographie réelle des 38 points et calibration avant de faire toute déclaration diagnostique.

**Canonique précédent :** `docs/clinic/CEPH_PREMIUM_J21_BROWSER_FUE1_20261110.md` (FUE-1 navigateur PASS au HEAD `1ccfc012`).

## Closeout / nettoyage vérifié
Après le contrôle : processus natif de test PID 23540 terminé ; port local 8005 sans listener ; profil `%TEMP%\\ceph-j21-native-fue-20261110-1ccfc012` intégralement supprimé (SQLite SQLCipher fictive, fichiers chiffrés, configuration et clés, logs, verrous) ; deux helpers Python de test retirés. Seules la documentation et la preuve JSON sans secret sont conservées dans la PR Draft.
