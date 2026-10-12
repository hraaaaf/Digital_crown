# DC Pocket commun — premier contrat de lecture

Date : 12 octobre 2026. Statut : IMPLEMENTED / VALIDATION PR EN ATTENTE.
Base produit : #838, e8732b6e6a6ff4b140b736291d77f38cfbc2c281.
Continuation du LOT 01 documentaire #846 ; aucun merge autorisé.

## Résultat

Deux adaptateurs exposent un contrat versionné commun :
- GET /api/mobile/capabilities : identité mobile staff actuelle, réponse AES-GCM existante.
- GET /api/patient-companion/contexts/{access_id}/capabilities : identité patient et relation active contrôlées avant réponse.

La forme commune contient version=1, principal_kind et capabilities. Chaque capacité porte allowed, scope et reason. Les réponses sont no-store et ne contiennent ni credentials ni identifiants internes de patient/cabinet.

Capacités couvertes :
- agenda.read : cabinet pour staff autorisé, contexte patient pour patient autorisé ;
- cabinet.patients.read : permission patients actuelle ;
- cabinet.clinical.read : patients ET clinical ;
- cabinet.finance.read : politique accounting OU payments actuelle ;
- shares.read : ressources explicitement partagées dans un contexte patient.

Les capacités cabinet sont refusées pour le patient. Les domaines cabinet sont nommés explicitement pour ne pas confondre les finances du cabinet avec le parcours financier personnel du patient.
Ce premier contrat couvre ces lectures uniquement. Il ne remplace pas les capacités Quick Action Hub ni les guards de chaque ressource ; il ne révoque pas les services patient existants qui ne sont pas encore décrits dans ce contrat.
Pas de nouveaux droits d'écriture, de preset, de rôle ou de table. ADMIN/propriétaire conserve la politique existante. Les permissions viennent de has_permission, donc des réglages et defaults serveur existants.
Aucun écran ne consomme encore les nouveaux endpoints : le branchement de la navigation et la gestion complète des profils restent à implémenter.

## Tests et isolation

Nouveaux tests : backend/tests/test_pocket_common_capabilities.py.
- profils assistante/dentiste/admin/propriétaire et permission absente ;
- droits retirés, clinical sans patients ;
- contrat patient sans autorisations cabinet ;
- endpoint staff chiffré et no-store ;
- JWT staff/patient non interchangeables ;
- droits relus en DB malgré rôle JWT différent ;
- accès patient d'une autre identité et accès révoqué refusés ;
- appareil staff révoqué refusé.

Résultat après le dernier changement de noms de capacités : **12 PASS en 6.01 s**.
Régression ciblée : test_mobile_patient_cockpit.py + test_patient_companion_local_first_contract.py + test_mobile_auth_security_contract.py : **18 PASS en 5.84 s**. Ce dernier changement de noms ne touche pas leurs fonctions existantes.
git diff --check : PASS.

Python 3.12.14 bundled, dépendances de test installées dans un répertoire jetable distinct. L'ancienne venv locale ne pouvait pas démarrer. Aucun changement des requirements.
Avant import/pytest : DIGITALCROWN_ENV_FILE vers un fichier dédié ; Settings.ENVIRONMENT=test ; Settings.DATABASE_URL=database.SQLALCHEMY_DATABASE_URL=sqlite:///:memory: assertés. Config/data/logs/runtime/media sont dirigés dans le répertoire de test isolé.
Le test utilise de vraies routes FastAPI dans une app minimale, de vrais JWT et une DB SQLite en mémoire ; pas de backend cabinet, pas de modèle clinique exécuté, pas de tunnel.
Les dependencies locales supplémentaires ne remplacent pas la validation CI du lock canonique.

## Revue adversariale interne A — contrat et compatibilité

Prompt : « Chercher les divergences entre droits Settings et capacités, confusion rôle/droit, domaines patient/cabinet, régression des endpoints existants, évolution implicite des presets et capacités inconnues. »
Exécution : inspection service, diff des deux routes et tests, confrontation aux guards existants.
Correction issue de la passe : nommer cabinet.patients/clinical/finance explicitement, afin qu'un refus finance cabinet ne masque pas les finances personnelles patient. Suite dédiée rerun verte.
Après correction : politiques existantes conservées, Quick Action Hub inchangé ; aucune migration, aucun rôle ajouté. Limite ouverte : la navigation ne consomme pas encore le contrat.

## Revue adversariale interne B — auth et isolation

Prompt : « Chercher un principal non authentifié, JWT de l'autre population, permission tirée du client, tenant imposé, cache public, ressource d'autrui ou révoquée, nouvel accès patient staff. Exiger une preuve pour chaque frontière. »
Exécution sur le même code final : contrôles auth existants conservés, résolution principal_for_access avant capacités patient ; réponse staff chiffrée, no-store ; tests avec vrais JWT, mauvaise identité et révocations.
Pas de nouveau contournement démontré. Les permissions d'une ressource restent contrôlées par sa route ; une capacité ne constitue pas un jeton d'accès.
Confirmation interne : relecture du diff final et des résultats ; aucune revendication de session device-bound ou d'iPhone physique. Auto-revue, pas revue indépendante.

## Preuve visuelle et merge

Aucun rendu, navigation, manifest, installation ou fonctionnement UI n'a changé. Ces endpoints sont nouveaux et non consommés par un parcours utilisateur ; la preuve runtime la plus proche est le statut HTTP, le contenu déchiffré et le refus d'accès vérifiés par les tests. Aucune capture AFTER produit fabriquée.
Avant merge : CI pertinente au HEAD final et inspection de cette preuve runtime sur PR ; les futures modifications UI exigeront BEFORE/Target/AFTER et validation humaine.
EXECUTION_SCORE=7.9/10 ; ADVERSARIAL_SCORE=7.9/10 ; RETAINED_SCORE=7.9/10 ; divergence >0.5 : non.
Plafond : validation CI/PR et validation humaine non acquises. Ni VERIFIED, ni merge-ready.
Next : brancher progressivement la visibilité des destinations couvertes sur ce contrat ; étendre la matrice des routes avant d'ajouter d'autres capacités. Garder le projet commun ouvert jusqu'aux essais PWA réels et à l'autorisation du propriétaire.

## Préparation du chargement frontend — 12 octobre 2026

Le hook usePocketReadCapabilities et le parseur typé sont ajoutés, sans être encore branchés à un écran.
Réponses staff chiffrées obligatoires ; version, population, booléens et scope cabinet contrôlés. Aucun droit déduit du rôle du snapshot ni conservé dans localStorage/IndexedDB.
Refresh au retour au premier plan, au retour réseau et sur nouveau snapshot ; droits réinitialisés pendant la vérification. Une génération de requête et AbortController empêchent une réponse ancienne ou annulée de rétablir des permissions retirées. Timeout réseau 5 s, sans effacer les credentials.
Une future UI devra expliquer les états loading/unavailable et définir l'accès offline autorisé avant de présenter un cache comme accessible.

Tests ciblés : usePocketReadCapabilities.test.tsx, **16 PASS en 2.80 s**. Contrat inconnu/patient/incomplet, type ou scope invalide, échec de déchiffrement, réponse staff en clair, absence de pairing, HTTP 401/403/500, panne réseau, retour au premier plan et réponse ancienne couverts.
Aucun changement backend depuis la preuve 30 tests ; ces preuves restent acquises pour les sources backend byte-identiques.
TypeScript : vérification lancée ; résultat consigné dans la PR après achèvement.
Revue interne A frontend : contrôle du contrat, refus de tout fallback par rôle et absence de consumer UI prématuré. Revue interne B frontend : contrôle des timers, cleanup, concurrence et réponse non chiffrée ; cette dernière a été rendue explicitement refusée, suite rerun verte. Confirmation : aucune capture AFTER ni intégration navigation revendiquée.
Les deux revues sont internes, pas indépendantes ; preuve CI et integration UI manquantes maintiennent les trois scores à 7.9/10.

BEFORE : navigateur intégré indisponible (échec d'attachement de vue). L'autorisation d'utiliser le runner de capture isolé Playwright a été demandée au propriétaire, conformément à la règle Product Design. Aucun runner de navigateur alternatif lancé sans sa réponse.
Next : obtenir les captures BEFORE, verrouiller le Target sur la disposition Pocket existante puis brancher les destinations couvertes. Aucun merge.
