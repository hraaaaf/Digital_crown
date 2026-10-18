# CB-01 FIRST_VALUE_UI — Protocole de certification d'accessibilité NATIVE

**Statut : PROTOCOLE PRÊT ; essais natifs `NOT_RUN` ; certification WCAG complète `NON`.**

Mission strictement limitée à CB-01 sur [PR #904](https://github.com/hraaaaf/Digital_crown/pull/904). Ne pas confondre :

- **Automatisé et prouvé** : [CB-01 #39145841795](https://github.com/hraaaaf/Digital_crown/actions/runs/39145841795), Chromium web synthétique à **390, 430, 1280, 1440, 1600 et 1920 CSS px**, navigation clavier/ARIA, contraste d'un texte prioritaire, reflow CSS, 69/69 tests Windows et aucun write clinique dans les scénarios enregistrés.
- **Natif, encore NON prouvé** : zoom du navigateur **200 %**, NVDA ou VoiceOver réel, contrôle exhaustif contrastes/haute visibilité et annonces dynamiques. Un viewport divisé par deux, un `font-size:200%`, `deviceScaleFactor:2` ou `Emulation.setPageScaleFactor(2)` **ne constituent PAS** un zoom navigateur natif.
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
