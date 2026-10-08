# V1.5-00.2 — FUE-I Hub première ouverture (PR #783 Lab)

Date: 2026-10-08
Status: OPEN / INVENTAIRE

## Contexte et classification
- Campagne: réconciliation rétrospective V1.5 des sous-lots CLOSED, avant V1.5-04.
- Sous-lot: 00.2 — Shell Hub + routing; exigence du plan V1.5: **FUE-I**.
- Laboratoire de référence: PR #783, `docs/audits/FIRST_USER_EXPERIENCE_PROMPT.md`; personnaliser le protocole pour ce sous-lot sans réutiliser son score FUE-A.
- Persona: utilisateur autorisé devant un PC cabinet à première ouverture; contextes poste non configuré et poste mémorisé si pertinents, sans substitution du scénario 00.3.
- First Value: choix explicite Cabinet / Station / Centre de contrôle puis arrivée dans la surface sélectionnée, avec une possibilité de récupération appropriée.

## Parcours et preuves attendues
1. Environnement synthétique isolé, session/poste vierge, état auth explicite.
2. Ouverture racine/Hub; observer l'identité de l'établissement et les 3 espaces.
3. Cliquer chaque carte, vérifier destination et garde d'accès : `/cabinet`, `/station`, `/control-center`.
4. Vérifier retour contrôlé Hub et résistance à la navigation URL directe Station; ne jamais contourner owner PIN.
5. Panne backend simulée sur fixture isolée : Hub et diagnostic restent visibles, espace clinique non ouvert sans autorité.
6. Captures BEFORE/AFTER comparables desktop 1280×900 et tablette 768×1024 ; mobile 390×844 seulement si le scénario Hub est applicable à ce viewport, sinon expliciter N/A (le routeur mobile est distinct).
7. Consigner latences, interactions, exceptions HTTP, console, erreurs navigateur, overflow, P0/P1/P2 et score sévère; deux revues adversariales et confirmation sur même HEAD.

## Inventaire initial
- PR historique #720 : preuve visuelle Hub 390/768/1280 et validation humaine documentées dans roadmap Notion.
- PR #724 : Hub 00.4 closeout/visuel, et #727 closeout documentaire; preuves à réconcilier sans les substituer au FUE-I de 00.2.
- `App.tsx` et `HubPage.tsx` actuels : routes et 3 cartes présents (revue source seulement).
- Les artefacts existants ne sont pas encore téléchargés ni inspectés pour les étapes « première ouverture → choix → destination »; **aucun score FUE-I attribuable aujourd'hui**.

## Verdict initial
**PARTIEL** — contrat scénario défini, preuves historiques identifiées; observabilité du parcours réel et preuves exact-HEAD du FUE-I encore à réunir. Pas de produit modifié. Pas de merge ni déploiement.

## Preuves visuelles historiques récupérées — 2026-10-08
- Run PR #720: `36651154266`, artifact `11069959474`, digest `sha256:4aa6548376596c4981559e128c408a199cb4c07cd0c3438a47f00f32faff46f1`; ZIP ouvert, contient `hub-390x844.png`, `hub-768x1024.png`, `hub-1280x900.png`, `report.json`. Report commit `78850bf4…` (merge-ref, à distinguer du PR head).
- Run PR #724: `36786234689`, artifact `11129697038`, digest `sha256:fa5e6df65b59fbe562162b83b17cad95ae2c63fb183aba9e6a9f05884c073dae`; mêmes trois viewports et rapport. Report commit `f0aacb5d…` (merge-ref).
- Deux rapports: `cards=3`, `scrollWidth=width`, `errors=[]` pour 390×844, 768×1024, 1280×900. Capture desktop 1280×900 effectivement inspectée: identité établissement et trois destinations cohérentes, sans données patient visibles; cette inspection n'est **pas** la preuve d'un clic ni de l'arrivée destination.
- **GAP FUE-I MAJEUR DE PREUVE** : ni artifact ne contient une séquence navigationnelle avec click-through, destination, retour et refus sécurité. Ne pas classer FUE-I validé et ne pas recycler le score ou l'état du FUE-A indépendant.
- **Next exact** : exécuter sur runtime de test isolé un harness #783 adapté à 00.2 (first launch → sélection des trois destinations → retour/guard/offline), capturer AFTER et métriques, puis deux revues adversariales et confirmation même HEAD. Ne pas produire de faux score sans observation.

## Résultat GitHub Actions observé — 2026-10-08
Run `37760198738` (V1.5-00.2 FUE-I Hub Lab) = SUCCESS, job `fue-hub` SUCCESS, step `Run FUE-I Hub` SUCCESS, upload SUCCESS. HEAD branche `529caa586646c210c5f3c9e9c341e452d3675cef`; artifact `11542185939`, digest `sha256:677aad7e6f13b278f6f54267748c0fd8ada42b54a4e9d2c53c2fbb73b7fbec1a`. ZIP inspecté : 10 PNG (5 tablette + 5 desktop) et `report.json`. Runner report: `productHead=c58ed0aac9a872ca14ea9b56a800d2c99e9975ea` (merge-ref Actions; ne pas confondre avec HEAD PR), tablette 768x1024 `hubMs=4282`, `firstValueMs=4588`; desktop 1280x900 `hubMs=1228`, `firstValueMs=1471`; cartes=3, refus Station non appairée=true, offlineMessage=true, overflow=false, pageErrors=[].

**Revue de vérité adversariale** : assertion Cabinet insuffisante : `cabinetUrl='/cabinet'` sur les deux profils, car le script rejette seulement le path `/dashboard`, sans exiger un refus réseau/une UI de verrouillage observé. Également, les parcours Cabinet authentifié, Station appairée, sortie PIN et offline clinique exact ne sont pas couverts. Une étape CI green ne prouve pas ces invariants. Les durées sont mesures browser synthétiques, pas UX terrain. **Statut 00.2 = PARTIEL; pas de score final ni CONVERGED.** Prochaine action : durcir oracle Cabinet et étendre runtime isolé, retester sur nouveau HEAD et refaire revues/confirmation. Aucun merge ni déploiement.

## Décision de gate par sous-lot — 2026-10-08
**Gate 00.2 du périmètre réalisable = VALIDÉ techniquement**, sous réserve de revue UX des captures avant validation UX définitive. Run #37762482791 SUCCESS sur PR head `5091e6c118c3d6c15db17b30b9b4fa9bf9197ffe`; 2 scénarios initiaux + 8 scénarios étendus PASS, 26 captures, 2 rapports, 0 FAIL. La preuve concerne des environnements synthétiques isolés. **Gate transversal différé à fin V1.5-01** : Cabinet authentifié, Station réellement appairée, validation PIN serveur, reboot/recovery de bout en bout. L'absence de ces tests n'est plus bloquante pour valider le périmètre propre de 00.2, mais leur réussite ne peut pas être revendiquée. **Ne pas confondre VALIDÉ technique et FUE-G intégré.**
