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
État initial de ce document : aucun écran ne consommait les nouveaux endpoints. Le branchement staff est maintenant décrit dans l'addendum ci-dessous ; la gestion complète des profils reste à implémenter.

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

Pour le premier commit backend décrit ci-dessus : aucun rendu, navigation, manifest, installation ou fonctionnement UI n'avait changé. Les étapes suivantes ont ajouté le consumer staff ; voir l'addendum et les captures réelles ci-dessous.
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

## Branchement UI staff — addendum du 12 octobre 2026

Le propriétaire a autorisé le runner Playwright isolé. Before accepté : 16 cas Chromium et 16 cas WebKit, quatre profils fictifs × quatre formats, trois écrans par cas. La tentative dev initiale comportant une navigation HMR a été rejetée ; les références conservées viennent du build de test isolé. Cible écrite avant modification dans DC_POCKET_READ_UI_TARGET_2026_10_12.md.

MobileDashboard consomme maintenant les capacités chiffrées. Les destinations couvertes ne montent pas leur composant sans permission, y compris via querystring. La finance n'est plus déduite du seul rôle : une assistante autorisée peut voir le résumé en lecture seule. Patients/Agenda restent aux mêmes positions et deviennent désactivés si refusés ; Plus filtre les destinations refusées. Recherche, notifications, liens de dossier Today/Agenda et actions rapides sont bornés par les droits correspondants. Les limites de rôle existantes pour labo/catalogue restent en place.

Les droits sont réinitialisés pendant chaque vérification et retirés au passage hors ligne ; loading et unavailable sont explicites avec réessai, credentials conservés. Ce lot choisit de fermer les lectures couvertes lorsque les droits ne peuvent pas être vérifiés : il ne fournit pas de bail offline. Le hook historique continue son chargement de snapshot/liste patients en arrière-plan avec les guards backend existants ; ce lot contrôle les composants visibles, sans prétendre remplacer cette couche de fetch ni un guard ressource.

Validation locale :
- 64 tests sur sept fichiers capacités/navigation/Today/Agenda/contracts de thème/runtime ;
- 5 tests du vrai MobileDashboard avec composants de données espionnés : aucun montage finance/patients refusé, assistante finance autorisée, révocation et état inconnu/indisponible ;
- 16 tests de régression header/finance/compact/actions/hook existant ; **85 PASS frontend ciblés**, aucun skip ;
- build:test : tsc -b et Vite PASS, sortie dist-test isolée, aucun frontend cabinet écrasé ;
- backend inchangé : preuves 12 + 18 PASS précédentes conservées ;
- After : **16 PASS Chromium + 16 PASS WebKit**, chacun vérifie Today/Plus/finance, révocation d'un écran ouvert, lien patient refusé, HTTP 503 puis réessai. 80 captures par moteur. Aucun débordement horizontal, pageerror ou appel API non modélisé ; API fictive interceptée, pas une preuve E2E d'auth réelle.

Comparaison dentiste autorisé Today/Finance : les huit PNG Chromium sont byte-identiques aux Before ; six des huit WebKit le sont. Today WebKit 430 et 1280 présentent un écart de rendu/gouttière, inspecté dans les paires, sans changement de disposition volontaire. Ne pas affirmer une fidélité pixel parfaite générale ou une certification Safari iPhone. La galerie locale permet la validation des trois écrans aux quatre formats et des états révocation/indisponibilité.

Le build et les captures ont été produits depuis les fichiers de travail testés ; le manifest de build porte encore le parent 4c13a9f. L'identité des sources publiées doit être contrôlée avant de rattacher ces preuves au nouveau HEAD. Cela ne remplace pas la CI au SHA final.

Prompts pour les deux nouvelles revues adversariales internes, à exécuter séparément depuis zéro sur le HEAD publié, puis confirmation sur ce même HEAD :
1. « Réfuter la frontière d'autorisation : lien direct, droits inconnus/refusés, patient vs staff, droits custom vs rôle, données en cache, Quick Actions, révocation pendant une requête et hors ligne. Chercher BLOCKER/MAJOR et contradiction entre contrat et guards. »
2. « Réfuter la preuve produit et sa reproductibilité : vrais composants vs preview, captures avant/après aux mêmes tailles, faux vert/absence de collecte/skip, différences de rendu, CI au SHA exact, isolation des données et assertion d'accès distant/iPhone non démontrée. Chercher BLOCKER/MAJOR et dette significative. »
Trace des exécutions et confirmation : description de PR au SHA publié. Ces passes restent internes, pas indépendantes.

EXECUTION_SCORE=7.9 ; ADVERSARIAL_SCORE=7.9 ; RETAINED_SCORE=7.9. Divergence >0.5 : non. Validation humaine des captures, CI ciblée finale et iPhone réel non acquis. Pas de VERIFIED ni de merge. Le transport distant, la coque patient commune et la gestion des appareils approuvés restent des étapes ultérieures du chantier autorisé.
