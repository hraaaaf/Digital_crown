# V1.5-01.1 — Réconciliation FUE-0 : topologie cabinet, réseau et origines mobiles

Date : 2026-10-08
Périmètre : **01.1 FUE-0 (contrat/tests)**, pas un parcours utilisateur. **Gate FUE-0 ciblé : PASS.** Closeout global V1.5-01 et gate FUE-G avec vrais postes : **NON revendiqués**.

## Autorités et baseline

- `STATE.md` et les PR fusionnées #728, #734, #738, #739 montrent que V1.5-01 avait historiquement été implémenté/clôturé sur `master`. La PR #786 a ensuite corrigé la première expérience installateur/Control Center ; #792 a ajusté l'audit du vocabulaire technique.
- Baseline réexaminée : `master@c3b094d8e5e8ba52ca40e7521927c0c5d60326a9`. Contrat pur `backend/core/cabinet_topology.py` SHA blob `9b17963f72baea1e85c7362aae175b57470fe9c0` ; fichier existant `tests/test_cabinet_topology.py`, garde backend `backend/tests/test_v1_5_01_topology_contract.py`.
- Selon le plan FUE canonique Notion, **01.1=FUE-0**, **01.2=FUE-I installateur**, **01.3=FUE-I erreur**, **01.4=FUE-G avec serveur + deux postes + redémarrage/coupure**. Ne pas confondre ces preuves.

## Finding de sécurité lors de la revue A

Sur `master`, `backend/routers/mobile_legacy.py::get_lan_base_url()` délègue bien au résolveur canonique. **Mais** `backend/routers/__init__.py` appelle `mobile_push.install_secure_lan_url_overrides()`, qui remplaçait dynamiquement ce résolveur par une URL construite à partir de `_detect_lan_ip()`, `os.getenv('PORT', '8005')` et du drapeau HTTPS. En l'absence d'HTTPS, l'override WebAuthn ultérieur n'est pas appliqué : le chemin ancien pouvait publier `http://<LAN>:<PORT>` malgré le lancement cabinet loopback-only. Le frontend LAN historique construisait parallèlement `http://<LAN>:5173`.

**Correctif minimal sur PR #803 :**
- `backend/routers/mobile_push.py` : l'init M6-D2 préserve désormais la fonction canonique au lieu de la monkey-patcher ; elle continue à désactiver l'ancien endpoint FCM.
- `backend/routers/mobile_legacy.py::get_lan_frontend_url()` : en cabinet/production ou HTTPS, l'origine frontend suit `resolve_cabinet_network().base_url`, sans générer un faux LAN HTTP ; le helper Vite :5173 reste réservé au développement non-HTTPS.
- `backend/tests/test_mobile_m6d2_push.py` : test anti-régression du hook M6-D2 en HTTPS activé/désactivé ; la fonction d'origine doit rester identique.
- `.github/workflows/v15-01-fue.yml` : ajoute le test M6-D2 réel aux régressions topology/back-end du laboratoire complet.
- Aucun secret, donnée patient, modèle DB, migration, packaging, cabinet réel ou Vercel modifié.

## Preuves exécutées

- **Code / workflow HEAD : `6217daa801ad71efbd440c857d96c2bc51c342a0`.**
- [Run **V1.5-01.1 FUE-0 #37812050447**](https://github.com/hraaaaf/Digital_crown/actions/runs/37812050447) : **SUCCESS**, compilation syntaxe et **23/23 checks** exécutés. Artifact [#11565915871](https://github.com/hraaaaf/Digital_crown/actions/runs/37812050447/artifacts/11565915871), ZIP digest `sha256:983a408d3bd92621419edfcf5899bffc4df995b65baf888fa25a69feea803591`, JSON inspecté : 23 résultats PASS.
- [CI Scope Gate #37812050372](https://github.com/hraaaaf/Digital_crown/actions/runs/37812050372) : **SUCCESS**.
- [FUE V1.5-01 isolé #37801976869](https://github.com/hraaaaf/Digital_crown/actions/runs/37801976869) : **SUCCESS** sur le HEAD de code antérieur `d0de97fc97d3c8810c54abc5791f284a55e37ec5`, avec même correctif produit. La répétition exacte au HEAD `6217daa8...`, [run #37812050341](https://github.com/hraaaaf/Digital_crown/actions/runs/37812050341), est à **revérifier** avant closeout exact.
- Échecs antérieurs du workflow isolé `#37801976754`, `#37811695856`, `#37811803603` : **harness bootstrap seulement**. Le premier exécutait `pytest` sans SQLAlchemy (chargement du `conftest.py`) ; le second importait `backend` sans `PYTHONPATH`, le troisième initialisait indirectement l'ORM via `backend/__init__.py`. Fix final : chargement direct du vrai module pure-Python via `importlib.util` (module enregistré dans `sys.modules`), sans stubber son comportement ; le hook réel Mobile Push et la fonction frontend réelle sont exécutés via AST contre des dépendances isolées. Le workflow complet conserve l'authentique environnement backend.

**Oracle FUE-0 :** 4 rôles descriptifs séparés des permissions ; port HTTPS 8005 ; loopback de premier boot ; LAN cabinet sans TLS refusé ; cert/key obligatoires ; URL wildcard sans adresse inventée ; diagnostics non secrets ; origine backend et frontend Mobile canoniques ; Vite dev préservé ; hook Mobile Push sans mutation ; ancien FCM désactivé ; découverte sans résolution DNS publique.

## Deux revues adversariales **internes** (même HEAD `6217daa8...`)

### Prompt A — Sécurité / architecture

> Cherche tout fail-open entre le résolveur cabinet `resolve_cabinet_network` et les export/rebindings runtime des modules Mobile, Push et WebAuthn ; cible les origines HTTP LAN, le port `PORT` vs `CABINET_PORT`, les contrôles TLS/cert/key, les secrets de diagnostic et la séparation rôle descriptif/permission. Ne crédite aucune assertion qui ne prouve pas le chemin actif.

**Résultat :** fail-open de construction d'URL dans l'init M6-D2 **découvert, corrigé et protégé**. La source Mobile canonique et l'ordre d'initialisation sont recontrôlés, tests dynamiques du hook et des branches cabinet/development PASS. Le changement ne revendique pas un vrai handshake TLS, un QR client en réseau physique, ni la sécurité WebAuthn indépendante.

### Prompt B — Preuve / reproductibilité / régression

> Tente de réfuter le PASS : vérifier la collecte effective, un rapport non vide avec HEAD exact, SHA produit distinct du merge-ref PR, artefacts, imports exécutés, dépendances masquées, gates requis, diff hors-scope et compatibilité du login/Push. Cherche tests skippés ou vert obtenu en désactivant la protection.

**Résultat :** 3 échecs de laboratoire **réels et diagnostiqués**, corrigés sans modifier l'exigence de sécurité ; preuve du module source réellement exécuté (pas un simulacre de `resolve_cabinet_network`) et hook Mobile Push soumis aux assertions. 23/23 certifiés et ZIP vérifié. Le runner complet exécute séparément les vrais tests ORM quand toutes les dépendances sont installées.

**Perfection Pass interne :** revue du diff, règles réseau, compatibilité frontend historique, données privées et distinction FUE-0 / FUE-G. Aucune autre régression significative démontrée sur le contrat 01.1 ; le futur parcours sur **deux vrais postes** reste explicitement réservé à **01.4**.

## Scoring et décision

- `EXECUTION_SCORE` : **9,2/10** (correctif minimal et 23/23 preuves réelles, pas d'environnement réseau matériel).
- `ADVERSARIAL_SCORE` : **9,1/10** (deux perspectives internes ; dette de preuve terrain hors scope ; pas de revue indépendante revendiquée).
- `RETAINED_SCORE = min(...)` : **9,1/10 scoped** ; plafond d'auto-revue 9,4 appliqué ; aucun BLOCKER/MAJOR ouvert **sur le périmètre 01.1 testé**.
- **Ne pas dire FUE-G V1.5-01 validé** et ne pas substituer les mocks du labo aux validations réelles serveur + 2 PC, restauration réseau, auth/PIN cookie/tenant/reboot.

Next exact : confirmation du FUE backend isolé exact HEAD, final gate documentaire, puis **01.2 FUE-I** assistant de connexion d'un poste annexe (installation/technicien), **01.3** récupération diagnostic erreur, **01.4 FUE-G terrain**. **Aucun merge/déploiement**.
