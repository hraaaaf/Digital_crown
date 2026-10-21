# CB-01 FIRST_VALUE_UI — Protocole de certification d'accessibilité NATIVE

## Addendum de preuves intégrées — 20 octobre 2026 (CB-01 FUE-G, synthétique)

**Source de preuve, à ne pas confondre avec une certification terrain :**
[Windows FUE-G run #39407423984](https://github.com/hraaaaf/Digital_crown/actions/runs/39407423984), job `118576639411`, `SUCCESS` sur le HEAD exact
`6edc21ef91d26d0b399a57d01d36a8caa99594be`. Artefact GitHub `#12258118334`
SHA-256 `0bb951fa88ac57fc149c5a3334fe8c852909a120385a0f630bafc769a5c86a4e`,
téléchargé et comparé à GitHub, rapport JSON + cinq captures. Un re-check du banc Windows sur le HEAD documentaire suivant
`04181589329ba70081e5c90439d2647b0ffc56b6` est également [SUCCESS #39410225369](https://github.com/hraaaaf/Digital_crown/actions/runs/39410225369) ; ce re-check ne certifie pas une installation réelle.

**Ce qui est effectivement prouvé dans le même onglet Chromium hébergé Windows :**
vrai `MainLayout` et `CrownBotChat`, vraies réponses FastAPI sur DB SQLCipher T2 fictive,
`chrome.tabs.setZoom/getZoom` natif `1 → 2` même onglet, `innerWidth 1920 → 960`,
DPR `1 → 2`, absence de scroll horizontal, panneau de repli borné dans
le viewport CSS de 450 px, cinq contrôles visibles, **cinq annonces rôle + nom
dans le journal du vrai NVDA/Guidepup** (onglets Mémoire contextuelle/Chat et
trois boutons métier). S05 HTTP `200` avec proposition de RDV `proposal_only`
visible et non exécutable, S06 HTTP `403` sans identité patient ;
état final de **119 tables** fictives inchangé côté clinique
(exceptions techniques `audit_logs` et `workstation_modes`). Ceci prouve un
parcours synthétique automatisé combiné et **ne prouve pas** l'absence d'une
écriture transitoire compensée, un test physique ou un résultat en données réelles.

**Matrice de portée, sans promotion artificielle de preuves :**

| Point du protocole | État fondé sur les preuves du 20/10 | Encore à réaliser |
|---|---|---|
| N01 / N02 | `PASS_PARTIEL_AUTOMATISÉ` : zoom Chromium natif 200 % / reflow et cinq contrôles accessibles dans le cas FUE-G 1920 × 900 ; pas de capture du menu natif vérifiée humainement | Menus Chrome/Edge et 1280 × 900 / 1600 × 900 demandés par N01/N02, comparaisons BEFORE/AFTER humaines |
| N03 / N04 / N05 / N06 | `NOT_RUN_GLOBAL` : le banc couvre des actions clavier et S05/S06 mais pas ces parcours natifs complets, historique, états critiques et retour manuel à 100 % | Séquences réelles avec capture et traces de focus |
| Lecteur écran S01 / S02 / S06 | `PASS_PARTIEL_AUTOMATISÉ` : cinq annonces NVDA authentiques au zoom 200 % dans MainLayout ; pas d'écoute/validation opérateur | Ouverture/fermeture, ordre de focus complet, vidéo ou enregistrement assistif humain |
| Lecteur écran S03 / S04 / S05 | `NOT_RUN_GLOBAL` | Historique read-only, états dynamiques, homonymes et sélection annoncée |
| WCAG AA complète, 400 %, couleurs forcées, VoiceOver, contraste exhaustif | `NOT_RUN` | Tests dédiés selon disponibilités et scope matériel |
| S01–S12 opérateur | `0/12 E2E humains` ; matrice automatisée distincte = 7 tests HTTP + 1 navigateur synthétique PASS, 4 NOT_RUN | Poste T2 fictif autorisé et registre de scénarios |
| Latence de première valeur | 31 543 ms sur **une séquence** FUE-G contenant huit clics et six réponses saisies, **pas** un p50/p95 d'usage | Campagne répétée définie au runbook (30 mesures de valeur utile par scénario) |

Les sections historiques ci-dessous datées du 18/10 restent des descriptions **datées** de leurs anciens
HEAD ; leur mention `NOT_RUN` ne doit pas être lue comme le verdict du nouveau banc FUE-G, ni remplacée
par `WCAG AA conforme`. Les flags opt-in demeurent OFF par défaut et aucune activité sur Pocket
mobile native n'est incluse.

### Handoff exécutable — validation humaine et revues indépendantes (à planifier, non réalisées)

**Préconditions** : décision et accord explicites d'accès à une **station Windows T2
isolée et autorisée** ; version SHA/bundle admissible vérifiée suivant la politique
d'installation, comptes et patients entièrement fictifs, zéro mutation clinique ;
pas d'installation du HEAD de PR sur poste cabinet, pas de données réelles.

1. **Opérateur métier** : suivre les douze lignes S01–S12 du
   `CB01_S01_S12_T2_FIELD_REVIEW_RUNBOOK_20261017.md`. Pour chaque cas :
   `ID | HEAD/bundle | rôle synthétique | viewport réel | zoom natif |
   réussite/échec/NOT_RUN | capture vidéo/log | diff clinique | date | signataire`.
   Capturer BEFORE / TARGET / AFTER aux mêmes viewports du parcours concerné ;
   chronométrer au moins trente premières valeurs réellement utiles par scénario
   éligible (p50/p95), sans substituer la latence HTTP. Une impossibilité physique
   reste `BLOQUÉ HUMAIN`, pas `PASS`.
2. **Reviewer externe A — FUE-C produit/UX** : examiner le parcours neuf, la
   première valeur **effective**, les 8 gestes du parcours simulé vs utilisateur
   réel, les mesures répétées, les états accessibilité, les captures égales et
   la non-exécution du RDV. Rechercher d'abord BLOCKER/MAJOR/faux succès,
   donner pour chaque constat `gravité, preuve, exact SHA, reproduction`.
3. **Reviewer externe B — frontière transversale sécurité / vérité des preuves** :
   partir du même HEAD **sans adopter la conclusion A** ; examiner Session/Station
   423, permissions S05/S06, tenant/404, homonymes, 409/422/503, SQLCipher
   avant/après, limites d'écritures transitoires, WS ACK GhostBrain, versions
   Windows/tzdata et déclenchement CI. Exiger une démonstration ou consigner
   `NOT_RUN`, ne pas déduire un PASS humain du laboratoire.
4. **Décision** : les deux rapports, leurs auteurs réels, les preuves et une passe
   de confirmation doivent porter le **même HEAD final** ; correction ⇒ nouveau
   HEAD ⇒ nouvelles revues et nouveaux tests impactés. Si les personnes
   indépendantes ne sont pas disponibles, consigner `REVUE INDÉPENDANTE : NON
   RÉALISÉE` sans demander de merge. Aucune invitation ni approbation humaine
   n'est implicite dans le présent document.

---


**Statut au 2026-10-18 : zoom NATIF 200 % du composant Crown Bot CERTIFIÉ en laboratoire Windows Chromium ; annonces réelles NVDA des 2 onglets et des 3 CTA CERTIFIÉES en laboratoire Windows distinct. Évaluation WCAG complète avec backend clinique réel, NVDA à 200 % combiné et VoiceOver NON CERTIFIÉE.**

### Preuve NVDA Windows réellement exécutée — cinq contrôles explicites

- **HEAD de test** : `b5d59cb4ebafc1c770f1defa51e9f61e90ecca92` ; [GitHub Actions #39153178226](https://github.com/hraaaaf/Digital_crown/actions/runs/39153178226) **COMPLETED SUCCESS**, `windows-latest`, vrai processus NVDA démarré via **Guidepup** en Chromium graphique, `nvda.spokenPhraseLog()` lu après les actions de navigation `nvda.next()`.
- **15 annonces capturées (pas un mock ARIA)**, dont 5 phrases **avec rôle ET libellé** : `tab, Mémoire contextuelle`, `tab, selected, Chat`, `button, Mon programme`, `button, Trouver un patient`, `button, Préparer un RDV`. Le test **échoue désormais si l'une manque**. État du protocole : annonces initiales des onglets et trois CTA en laboratoire = **PASS réel NVDA automatisé**.
- **Contrôle adversarial de preuve** : le précédent [run #39151759415](https://github.com/hraaaaf/Digital_crown/actions/runs/39151759415) avait 10 annonces mais comptait « RDV » dans un **texte explicatif**, et non comme bouton. Cet ancien résultat n'était PAS une certification NVDA des trois CTA. Les nouvelles assertions exigent `^button, <libellé>` sur une annonce NVDA distincte. Le premier artefact échoue avec les nouveaux critères, le nouveau run passe 5/5.
- **Artefact** : [#12145917059](https://github.com/hraaaaf/Digital_crown/actions/runs/39153178226/artifacts/12145917059), ZIP SHA-256 `53ed3a9841309ebf69ee9158f22a738b623dba3ee05247c81c310b4699af9193` ; `report.json` vérifié après téléchargement avec `observedAccessibleControls` = les cinq clés `true`, 15 phrases, `nvdaStarted:true`, `clinicalWritesAttempted:[]` et screenshot UI.
- **Limite contractuelle** : vrai `CrownBotChat` importé dans Vite loopback avec **API et utilisateur synthétiques**, aucune donnée médicale réelle, aucune FastAPI réelle, aucune session/praticien réel ; `speechHardwareAudioRecording:NOT_RUN`, `nvdaHumanReview:NOT_RUN`. Ce log de synthèse ne vaut pas écoute humaine ni revue de tous les états, focus après actions, messages dynamiques, zoom + NVDA simultané ou certification WCAG AA globale. `S01–S06` de la matrice réelle complète demeurent **PARTIAL/NOT_RUN selon scénario**, et VoiceOver non exécuté.



### Preuve Windows native obtenue (laboratoire isolé, sans backend réel)

- **HEAD de preuve** : `995aa3cb907ed7a7c60c49362164a6e064b459fb` ; [GitHub Actions #39149216305](https://github.com/hraaaaf/Digital_crown/actions/runs/39149216305) **SUCCESS** (`windows-latest`, Chromium **140.0.7339.16**, job expérimental indépendant des gates REQUIRED).
- **Preuve navigateur** : extension Manifest V3 avec `chrome.tabs.setZoom(1|2)` ET vérification `chrome.tabs.getZoom() === 1|2`. Les captures sont prises à dimensions de fenêtre constantes : **1280×900** à 100% (innerWidth 1280 / DPR 1), 200% (**innerWidth 640 / DPR 2**) ; **1600×900** à 100% (innerWidth 1600 / DPR 1), 200% (**innerWidth 800 / DPR 2**). `visualViewport.scale = 1` est attendu pour le zoom navigateur et NE rend pas le test équivalent à un pinch. `rootScrollWidth === rootClientWidth` à ces quatre points.
- **Rendu réel** : `CrownBotChat` de production importé en laboratoire Vite localhost avec flags strictement locaux, session et endpoints **synthétiques interceptés** ; les 3 CTA visibles aux 4 points, `ArrowLeft/End` sur les onglets ARIA PASS et `Préparer un RDV` renvoie clarification simulée sans écriture. **Aucune donnée médicale réelle, aucun backend médical réel, aucun parcours staff humain.**
- **Preuves immuables** : [artefact #12144792182](https://github.com/hraaaaf/Digital_crown/actions/runs/39149216305/artifacts/12144792182), `report.json` + 4 captures 100/200 aux deux largeurs, digest ZIP `sha256:e81e5a23135ffb263cea3851988d8b5e41d6721f5b14afc4428842aecc256d8c`. Images examinées : CTA disponibles, pas de texte d'action tronqué ni scroll horizontal dans ce **lab**, main synthétique parfois occulté par l'overlay flottant à 1280/200% (comportement du laboratoire, **ne prouve pas maintien de tout l'espace clinique Agenda réel**).
- **Classification précise** : `CB01_NATIVE_WINDOWS_ZOOM_200 = PASS_BROWSER_EXTENSION_VERIFIED` (composant isolé) ; **N01–N06 de ce protocole pour application clinique complète** restent `NOT_RUN` tant que le serveur réel, les permissions, la vraie fenêtre UI et les captures à zoom natif ne sont pas examinés. `NVDA première navigation + cinq rôles/libellés = PASS_SYNTHETIC_LAB` ; `NVDA sur application intégrée / zoom combiné / VoiceOver = NOT_RUN`, 400%, forced-colors et contrastes exhaustifs `NOT_RUN`. Aucun `WCAG AA global PASS`, aucun `CONVERGED`.


Mission strictement limitée à CB-01 sur [PR #904](https://github.com/hraaaaf/Digital_crown/pull/904). Ne pas confondre :

- **Automatisé et prouvé** : [CB-01 #39145841795](https://github.com/hraaaaf/Digital_crown/actions/runs/39145841795), Chromium web synthétique à **390, 430, 1280, 1440, 1600 et 1920 CSS px**, navigation clavier/ARIA, contraste d'un texte prioritaire, reflow CSS, 69/69 tests Windows et aucun write clinique dans les scénarios enregistrés.
- **Natif, acquis partiellement** : zoom navigateur réel **200 %** prouvé sur le composant synthétique Windows, **NVDA réellement lancé et cinq contrôles annoncés** en laboratoire Windows distinct. **NON prouvé** : zoom NVDA combinés sur l'application clinique réelle, VoiceOver réel, contrastes exhaustifs/haute visibilité et annonces dynamiques sur le backend. Un viewport divisé par deux, un `font-size:200%`, `deviceScaleFactor:2` ou `Emulation.setPageScaleFactor(2)` **ne constituent PAS** un zoom navigateur natif.
- **Hors mission** : essais physiques de personnel en cabinet = Lot 10 ; Pocket mobile natif = CB-06 conditionnel ; timezone par tenant = Agenda A5 ; actions cliniques CB-03.

## 0. Préconditions obligatoires

1. Exécuter sur le **HEAD exact final** de PR #904 ; noter SHA, version de Chromium/Chrome/Edge, OS, fuseau navigateur et fuseau pilote cabinet. Utiliser seulement **l'installation locale isolée, des comptes synthétiques autorisés et les flags de preview prévues par le laboratoire** ; aucune donnée patient réelle.
2. Confirmer l'exécution des workflows applicables sur CE SHA (ne pas réutiliser le GREEN d'un SHA parent). Relever tous les jobs REQUIRED / EXPERIMENTAL / HORS SCOPE sans renforcer arbitrairement le gate.
3. Fixer la **même taille de fenêtre physique** avant les deux captures, largeur/hauteur relevées. Mesurer `innerWidth`, `document.documentElement.scrollWidth`, `devicePixelRatio`, `visualViewport.scale` et l'élément actuellement focalisé à chaque étape comme **indices secondaires**. Le zoom du navigateur doit être vérifié dans l'**interface native du navigateur** elle-même, avec capture ou enregistrement de son indicateur « 100 % » puis « 200 % ».
4. Fermer les extensions personnalisées susceptibles de modifier le zoom ou le DOM ; ne jamais coller dans DevTools une commande qui transforme le contenu puis proclamer « zoom natif ».

## 1. Tests navigateur : 100 % puis 200 % réels

**Périmètre web CB-01 :** tester au minimum une fenêtre de référence 1280×900 (floating overlay) et 1600×900 (sidecar). Complément recommandé : 430×932 web fallback, à distinguer de l'app Pocket native.

| Cas | Procédure et oracle | Preuve requise |
|---|---|---|
| N01 Zoom réel | Ouvrir Crown Bot, capture à 100 % ; activer **Zoom 200 % dans le menu natif Chrome/Edge** sans changer la fenêtre physique, nouvelle capture ; vérifier indicateur exact « 200 % » | Deux captures navigateur incluant indicateur de zoom, dimensions et SHA |
| N02 Reflow | À 200 %, trois CTA **Mon programme / Trouver un patient / Préparer un RDV** accessibles ; ni texte tronqué ni contrôle hors écran sans moyen de défilement ; pas de scroll horizontal de page, conserver le contexte Agenda | BEFORE / AFTER au même viewport physique + métriques de défilement |
| N03 Clavier | Sans souris : launcher→panneau, Tab/Shift+Tab, onglets ArrowLeft/Right + Home/End, CTA, historique, fermeture Escape puis restitution du focus ; aucun focus dans tiroir caché `inert` | Vidéo courte ou séquence de captures avec focus visible + éléments actifs |
| N04 Historique sûr | Ouvrir conversation synthétique avec ancien `pendingActionId` ; voix/DOM lisent **historique lecture seule** ; aucun bouton de confirmation, aucune mutation clinique, retour aux CTA | Capture historique, log réseau vérifiant GET uniquement |
| N05 États critiques | Données synthétiques : agenda vide, 403, praticien invalide, deux patients homonymes ; erreurs explicites, sélecteur reste utilisable à 200 %, identité du patient sélectionné lisible et effacée après refus | Captures de chaque état et traces réseau sans fuite |
| N06 Retour 100 % | Remettre zoom via menu natif à 100 % ; vérifier que session et focus restent cohérents, sans fuite inter-principal ni mutation | Capture avec indicateur « 100 % », nouvelle inspection DOM |

**Échec dès que :** fonctionnalité essentielle inaccessible au clavier, ordre de focus incohérent, identité erronée, bouton d'action clinique historique, débordement sans possibilité d'accès, ou zoom non réellement prouvé. Le simple échec à reproduire le zoom est `NOT_RUN`, **pas** `PASS`.

## 2. Lecteur d'écran : NVDA / VoiceOver

Effectuer sur une station disposant réellement d'un lecteur d'écran activé. Pour un cabinet Windows, **NVDA avec Chrome ou Edge** est prioritaire ; VoiceOver/Safari est une matrice distincte si macOS disponible. **Ne pas prétendre avoir essayé VoiceOver sur Windows ni NVDA dans Playwright seul.**

| Cas | Annonce audible attendue | Résultat à collecter |
|---|---|---|
| S01 Premier clic | Le panneau et son contrôle de fermeture sont annoncés ; les trois actions métier lisibles | Enregistrement audio/vidéo, lecteur écran + version |
| S02 Onglets | « Vues de Crown Bot », « Mémoire contextuelle » / « Chat », **onglet sélectionné**, changement de sélection par flèches | Séquence des annonces avec ordre de focus |
| S03 Historique | « Historique Crown Bot, dialogue », lecture seule, messages user/assistant, Escape restaure le bon contrôle | Enregistrement + aucune annonce d'ancien bouton exécutif |
| S04 Statuts dynamiques | Chargement, « aucun RDV », échec de permission et résultat sont annoncés au bon moment, sans doublons trompeurs | Transcription des annonces + capture d'état |
| S05 Homonymes | Nom + numéro dossier de chaque candidat et de l'option choisie restent compréhensibles ; disparition claire si refus | Annonces exactes sur données synthétiques |
| S06 200 % + lecteur écran | N02–N04 fonctionnent au **zoom natif** et au lecteur écran simultanément | Preuve du niveau de zoom + enregistrement |

**Résultat** : `PASS` uniquement si une interaction réelle est réalisée et tracée ; sinon `NOT_RUN`. Les tests ARIA Playwright et le DOM ne remplacent pas une évaluation assistive.

## 3. Contraste, focus et redimensionnement

Vérifier **tous les états essentiels** (actif, inactif, focus, erreur, désactivé), pas seulement une ligne d'instruction :

- Texte ordinaire **≥ 4,5:1** ; texte large (définition WCAG) **≥ 3:1** ; icônes de contrôle/focus indispensables **≥ 3:1** contre leurs couleurs adjacentes.
- Pour transparence, dégradé et overlay, mesurer les couleurs **composées réellement rendues**, pas seulement la déclaration CSS d'une classe Tailwind ; enregistrer l'outil de mesure et les paires FG/BG.
- Mode Windows Contraste élevé ou couleurs forcées, zoom navigateur 200 % et **400 %** : captures + contrôle clavier + pas de perte de contenu ni de fonctionnalité. `NOT_RUN` tant que non réalisé.
- Décrire chaque échec BLOCKER/MAJOR/MINOR avec élément, contraste mesuré, viewport, SHA, preuve et correction ciblée. Aucun « WCAG AA conforme » global sur une seule couleur conforme.

## 4. Registre d'exécution et décision

Remplir une ligne **par scénario** : `ID | date-heure | HEAD | environnement | rôle synthétique | zoom natif confirmé (%) | résultat PASS/FAIL/NOT_RUN | preuve URL/fichier | finding/sevérité | reviewer`.

**État au moment de la création du protocole** :

- N01–N06 : **NOT_RUN**, absence d'une session Chrome/Edge native autorisée sur Digital Crown.
- S01–S06 : **NOT_RUN**, aucun lecteur d'écran réellement exécuté sur l'app.
- Contraste exhaustif / 400 % / couleurs forcées : **NOT_RUN**.
- Tests UI automatisés CB-01 : **PASS** à [run #39145841795](https://github.com/hraaaaf/Digital_crown/actions/runs/39145841795) sur HEAD `4302371d755fb66c540e1245fa2a491bcfef1073`, sans confondre avec les points ci-dessus.
- PR #904 : **DRAFT / NON MERGED** ; vraies revues indépendantes **0/2** ; `CONVERGED=NO`.

**Chemin de certification** : exécuter les cas natifs → sauvegarder les preuves immuables liées au SHA → corriger tout défaut dans CB-01 et relancer CI si nouveau HEAD → deux revues externes réelles sur le même HEAD final → décision de merge **séparée avec approbation**. Ne jamais déplacer les essais physiques Lot 10 dans cette mission.
