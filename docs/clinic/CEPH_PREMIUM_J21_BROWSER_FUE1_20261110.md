# CEPH-PREMIUM J2.1 — FUE-1 FRONTEND ↔ vraie API isolée — 10/11/2026

## Décision et périmètre
**Goal :** vérifier dans un vrai navigateur Chromium le cycle de la scène céphalométrique `CEPH_PREMIUM_SCENE_V1_DRAFT` avec FastAPI/JWT/DC-DOS-05, image originale AES-GCM et base SQLite **applicative de test jetable**. **Pas** d'activation de l'UI clinique ni de validation de la native Digital Crown Desktop.

## Exécution sur Windows, branche de PR Draft #1253
- Point de départ : `c29b07fcca043bfd535c08f5e049d4ffa7ea241c`, PR Draft #1253, aucune fusion, migration ou mise en production.
- Fixture test : patient et étude synthétiques, PNG uni 800×600 généré en mémoire, 38 points fictifs selon `SOTA_LANDMARKS_MAPPING`. Ce PNG ne représente pas une vraie téléradiographie et n'a été traité par **aucun ONNX** pendant le FUE. Les points ne sont donc **pas anatomiquement certifiés**.
- Serveurs bind sur la boucle locale uniquement : Vite `127.0.0.1:5187` (page HTML indépendante, gate `DEV + VITE_CEPH_J21_SCENE_FUE=true`) avec proxy `/api`, backend réel FastAPI `127.0.0.1:8879` avec quatre guards `test` / `DIGITALCROWN_ISOLATED_RUNTIME` / `CEPH_J21_SCENE_APP_FUE_ONLY` / `DC_DOS05_FUE_ONLY`. DB source sous `%TEMP%\ceph-j21-browser-fue-*\ceph-j21-scene-app-fue.sqlite3` ; médias synthétiques chiffrés sous ce même répertoire. Aucun fichier patient du cabinet.
- Authentification : formulaire de connexion au vrai `POST /api/auth/login` → 200, jeton JWT puis `GET /api/ia/analyses/1/premium-scene-fue` → 200 et `GET /api/patients/1/assets/1/content` → 200, SHA-256 original vérifié via SubtleCrypto.
- Première tentative FUE : FAIL légitime sur sélection au centre du cercle SVG (ancien `fill="none"` → zone centrale ne reçoit pas `pointerdown`). Correction **dans le seul viewer candidat** : `fill="transparent" pointerEvents="all"`. Relance Chromium : **PASS**.
- BEFORE : `scene_revision=1`, point `A` à `x=45`. ACTION : clic réel puis touche flèche droite ; `x=46`, provenance `PRACTITIONER_EDIT`, invalidation de SNA fictive. `POST /api/ia/analyses/1/premium-scene-fue` → 201. AFTER : GET indépendante et bouton recharger → `scene_revision=2`, `x=46`. Nouveau chargement complet du navigateur puis connexion JWT : `revision=2`, `x=46` retrouvés.
- Identité SHA preuve : original `d18e1f863c91a2876cbb2c979951ec0117ddcd039bc6f3d91011213292429787` = hash navigateur du contenu HTTP ; scène avant `9da9a0c351fb74ac57950eea9f67b641a0fa7f7a5462ecc3f600af2f9878d89b` ; scène après `90ab75fcf639d18dfd01b423500c975adc3d01e14b21fa19e73cf92af8d68f85` avec parent correspondant. Audit négatif navigateur (sans cookie) : anonyme HTTP 401 ; patient différent HTTP 404 ; 38 landmarks, SNA `UNAVAILABLE`/`null`, pas d’autorité clinique.
- Responsive : captures réelles à **390, 430, 768 et 1280 px** ; aucun dépassement horizontal DOM. La fixture uniforme et les noms de points volontairement concentrés ne valent **pas** validation UX de la téléradiographie ou des étiquettes. FUE visuel du produit réel et mapping 38 repères restent HOLD. Une ressource HTTP 404 non identifiée apparaît dans la console Chromium (sans effet sur les requêtes métier prouvées) ; à classifier si nécessaire.

## Preuve vérifiable versionnée
Artefacts uniquement synthétiques sous `docs/clinic/evidence/j21_browser_fue1_20261110/` :
- `BEFORE-1280.png`, `AFTER-1280.png`, `AFTER-390.png`, `AFTER-430.png`, `AFTER-768.png`, `REOPENED-1280.png` ;
- `report.json` : requêtes HTTP observées, scénarios, résultat PASS, viewports, hashes SHA-256 de chaque capture ;
- `live-api-integrity-audit.json` : révision 2, SHA réels, 401/404, contenu 38 points et invalidation de mesure.
Les copies des 8 fichiers ont été vérifiées par SHA256 avant inclusion dans la PR. **Aucun JWT, mot de passe, base de données ou contenu clinique réel dans ces preuves.**

## Verdict rigoureux
**FUE-1 FRONTEND ↔ API navigateur isolé : PASS** ; autorise seulement le passage au FUE natif. M1 🟢, M2–M5 🟡, M6 🔴 restent **inchangés** dans la checklist de clôture. Ce succès n'est ni un test dans le package Desktop ni une certification médicale. Reste à prouver le lancement de Digital Crown installable, ses véritables routes et persistance locales, l’arrêt/relance de l'application, captures mêmes viewports et négatifs M5, puis validation des repères par un praticien.

## Next exact
1. Après ce run, arrêter Vite et FastAPI, contrôler suppression du répertoire temporaire et des paquets de test externes et le worktree propre.
2. Revalider les tests du viewer incluant l'assertion de zone SVG cliquable ; pousser seulement sur PR Draft #1253, sans merge, migration clinique ni déploiement.
3. Préparer FUE Desktop natif avec fixture synthétique et JWT, sans brancher le code clinique non autorisé.
