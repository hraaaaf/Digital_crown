# Digital Crown · LOT07 R7 / 07.1.E + 07-E — protocole FUE Desktop

**Statut :** dossier de validation, PAS une approbation clinique. Les tests synthétiques Linux/Chromium ne certifient pas la plateforme Windows physique ni deux vrais moniteurs.

**Base technique :** R6/07.1.D PR #1145, SHA `abcd74eaa0e6615a16d7d1895a03297dee9ef025`, 6/6 workflows applicables SUCCESS, FUE 54/54 et 8 captures. R7 est une PR STACKED distincte. Ne jamais fusionner ni déployer sur simple GO pour un test.

## FUE-A — automatiquement exécutables sur T2 jetable

| Contrôle | Preuve attendue | Statut initial |
| --- | --- | --- |
| A01. React réel à 1280 × 900 | Triptyque réel visible, sources T0/T1/T2, capture, aucun débordement du panneau | À exécuter |
| A02. React réel à 1440 × 900 | Même identité source + capture | À exécuter |
| A03. React réel à 1920 × 900 | Même identité source + capture | À exécuter |
| A04. React réel à 2560 × 900 | Même identité source + capture | À exécuter |
| A05. Ouverture clavier via Enter | Focus du bouton et nouvelle fenêtre effective (pas seulement un état React) | À exécuter |
| A06. Popout en lecture seule | Trois repères, aucune commande d'écriture ni script embarqué | À exécuter |
| A07. Changement patient A → B | Fermeture prouvée de la fenêtre A et aucune source A dans B | À exécuter |
| A08. Réseau retardé A → B → A | Ne jamais afficher des sources de A dans la vue B | Hérité et réexécuté via FUE R6D |
| A09. RBAC et tenant | Refus authentiques 403 et 403/404, aucun faux 423 | Hérité et réexécuté via FUE R6D |
| A10. Confidentialité | Aucun commentaire clinique, identité patient ni clé d'accès dans le rendu du popout | Hérité et réexécuté via FUE R6D |
| A11. Observabilité | Captures BEFORE / TARGET / AFTER, mesures temporelles et heap dans rapport au SHA exact | À exécuter |
| A12. Production désactivée | Les flags R6C et R6D demeurent DEV-only et production OFF | À vérifier avec CI R6D + R7 |

**Règle :** un FUE RED reste RED ; interdiction de masquer un 403, ignorer un timeout, utiliser des routes interceptées ou revendiquer un PASS à partir d'un ancien SHA. Les images et comptes sont uniquement synthétiques.

## FUE-B — test physique obligatoire avant R8

À réaliser sur un poste Cabinet **Windows** autorisé, deux moniteurs réellement branchés en **mode Étendre**. Ne pas utiliser de véritable dossier patient dans une capture partagée.

- [ ] B01. Windows Paramètres → Affichage → Mise à l'échelle à **200 % natifs** ; relevé de l'affichage Windows et de la résolution effective. Une émulation Chromium/deviceScaleFactor n'est PAS une preuve.
- [ ] B02. Vérifier 1280 / 1440 / 1920 / 2560 selon l'équipement, ou signaler **impossible** si l'écran ne les supporte pas ; prendre BEFORE, TARGET, AFTER pour chaque largeur réalisée.
- [ ] B03. Ouvrir le Cabinet réel et parcourir les **neuf** dispositions MultiView avec de vrais modules ; déplacement, redimensionnement, swap, max/reset, sans panneau hors droits.
- [ ] B04. Ouvrir la fenêtre patient au clavier et la **déplacer réellement** sur le second moniteur ; aucun champ modifiable, aucun accès dossier complet, lecture seule.
- [ ] B05. Fermer le dossier A, ouvrir B et vérifier **en temps réel** extinction de la fenêtre A sur l'autre moniteur. Refaire à la déconnexion, expiration, arrêt brutal du poste parent et changement de compte.
- [ ] B06. Tester NVDA : annonces de titre/repères T0/T1/T2 et navigation clavier sans piège ; relever chaque anomalie.
- [ ] B07. Vérifier la révocation **effective côté serveur** des jetons/sessions, y compris une fenêtre ouverte et un réseau retardé. Un changement local Zustand ne compte pas.
- [ ] B08. Exécuter le dossier scientifique avec vraies sources autorisées, zoom/pan et mesure : comparabilité contrôlée par le praticien, aucun diagnostic automatique.
- [ ] B09. Surveiller consommation mémoire / CPU en charge sur le poste ; noter valeurs, durée, logiciel et résolution sans seuil inventé.
- [ ] B10. Revue de sécurité : la fenêtre `about:blank` hérite de l'origine du Cabinet même avec CSP et sans script. **Gate OPEN** tant qu'une revue de l'isolation n'atteste pas l'absence de risque d'accès au stockage authentifié.
- [ ] B11. Approbation visuelle et clinique explicite du propriétaire, **liée au SHA exact et aux captures**, après corrections. Une ancienne validation R3 ne vaut pas R7.
- [ ] B12. Autorisation de fusion, puis autorisation de release/activation, **distinctes**. Vérifier les CI `master` après fusion, pas avant.

## Revue B10 — source du risque et preuve automatisée

**Statut : BLOCKED — pas une certification clinique.**

Le popup Digital Crown R6D utilise `window.open('about:blank')` puis construit un DOM statique et applique une CSP par balise `meta`. Le fait d'effacer `window.opener` ne change pas l'origine du document : un `about:blank` ouvert par un parent hérite normalement de son origine. Par conséquent, **la fenêtre n'est pas un contexte de stockage isolé** et le contrôle de l'absence de boutons/scripts ne démontre pas l'inaccessibilité des jetons applicatifs. Ce constat architectural est indépendant de la présence effective d'un script malveillant.

À partir de la passe R7B, le FUE Chromium teste uniquement si la surface `localStorage` du popup donne accès au jeton **entièrement synthétique** injecté dans le test. Le résultat `inheritedCredentialSurfaceReadable` est un booléen : ne jamais écrire le jeton dans un log, un fichier, une capture ou une télémétrie. Le rapport doit obligatoirement conserver `detachedOriginIsolationCertified=false`, `clinicalActivationApproved=false`, `review=BLOCKED_PENDING_ISOLATED_ORIGIN`. Un FUE automatisé GREEN peut prouver la mesure de ce risque ; il **ne ferme pas B10**.

**Gate de correction avant usage clinique :** présenter sur un contexte réellement isolé du stockage d'authentification du Cabinet (origine distincte ou politique de sandbox à origine opaque appropriée) et prouver l'impossibilité d'accéder aux jetons/cookies/données cabinet depuis ce contexte. Le canal de transmission doit être limité à une projection minimale et authentifiée du patient choisi, avec fermeture sur expiration, déconnexion, changement de dossier et révocation serveur. Répéter un FUE négatif sans mocks puis demander la revue indépendante. Ne pas supprimer les vérifications simplement pour rendre la CI verte.

Références techniques : MDN Same-origin policy (about:blank inherited origins) ; documentation Chromium « Special Case URLs » ; MDN CSP sandbox (opaque origin).

## Verdict de livraison

- **R7A AUTOMATED** = GREEN uniquement avec workflows et preuves FUE au même HEAD.
- **R7B PHYSICAL** = **NOT RUN** en l'absence de preuve du vrai poste et de l'accord humain.
- **R7 GLOBAL** = **BLOCKED** jusqu'à clôture de B01–B12, revue sécurité popout comprise.
- **R8** = **NOT AUTHORIZED** par le GO R7.

Dernier enregistrement des preuves : dans le canonique Notion LOT07, URL PR et GitHub Actions exacts, SHA et date, sans aucune donnée patient réelle.
