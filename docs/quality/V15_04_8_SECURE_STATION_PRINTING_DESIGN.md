# Digital Crown — V1.5 / LOT 04.8 — Impression sécurisée depuis la Station

**STATUT : CONCEPTION / BACKLOG, NON IMPLÉMENTÉ, NO-GO PRODUCTION.**  
**Décision utilisateur du 2026-10-12 : C — les deux selon la configuration du cabinet.**  
**Dépendance : [PR #840 / LOT 04.7](https://github.com/hraaaaf/Digital_crown/pull/840).**  
**Canonique : [Roadmap unique Notion V1.5](https://app.notion.com/p/3e677c66336281d88c82d2fbe43835fb).**

Le LOT 04.8 est **distinct de 04.7** et n'ajoute aucun droit à l'ancien flux d'identification, ne modifie aucun gate de 04.7, n'autorise aucun merge/deploy. Il introduira seulement après certification une **commande d'impression depuis la Station**, sans jamais servir de PDF au navigateur public.

## 1. Goal et preuve observable

Un patient identifié peut, si la politique du cabinet et le matériel le permettent, demander un exemplaire de son document éligible :
- **près de la Station**, via une imprimante physiquement accessible au patient avec libération confidentielle réellement supportée et éprouvée ;
- **derrière l'accueil**, par une imprimante sous surveillance du personnel et remise par un membre habilité ;
- **les deux**, le patient choisit explicitement la destination si deux imprimantes approuvées sont disponibles.

**Succès vérifiable** : bonne feuille de soins finalisée et autorisée, empreinte vérifiée, imprimée **une fois** à l'emplacement demandé, remise au bon patient, journal d'audit minimal, zéro PDF dans navigateur/Downloads/Cache de la Station, spool/temporaire maîtrisé et nettoyé avec preuve réelle ; les refus, offline et expirations ne libèrent pas d'autre document.

## 2. Politique de configuration (noms provisoires de contrat)

`stationDocumentPrint.mode` :
- `disabled` — **défaut**, bouton masqué et API de job refuse.
- `near_station` — seule la destination locale à proximité est sélectionnable, si confidentielle et certifiée.
- `reception` — seule la destination accueil approuvée, et remise supervisée.
- `both` — patient choisit *près de la Station* ou *à l'accueil*, sans présélection ni fallback implicite.

Administrateur/gestionnaire habilité du Cabinet définit une **allowlist** d'imprimantes physiques identifiées, leur emplacement (Station / accueil), les Stations liées, la prise en charge du secure release, les créneaux/conditions d'exploitation, les droits de l'agent d'impression et l'activation après certification. Le simple choix C ne configure aucune imprimante, n'active aucune impression.

En mode `both` si une destination est hors ligne/non validée, ne jamais rerouter silencieusement : la destination indisponible est clairement signalée, la destination saine reste utilisable si le cabinet l'autorise. Il ne faut pas proclamer `both` certifié quand seule une imprimante a été physiquement testée.

## 3. Invariants de sécurité conservés depuis LOT 04.7

1. **L'interdiction PDF Station reste stricte** : les GET `/api/workstation/patient-session/{session_id}/documents/care-sheet/{document_id}` et `.../presence-receipt/{appointment_id}` continuent de retourner **HTTP 423**. Ne jamais créer côté kiosk un `Blob`, `ObjectURL`, téléchargement, aperçu PDF, lien bearer ou `window.print()` contenant le PDF. Les octets ne traversent pas le navigateur Station.
2. La Station émet seulement une **intention d'impression** (`sessionId`, `documentId`, identifiant de destination autorisée, clé d'idempotence) vers une **API Cabinet dédiée**, authentifiée et bornée ; elle reçoit seulement un statut non clinique. Le service du Cabinet produit/transmet le PDF vérifié uniquement à un **agent d'impression de confiance** sur l'hôte Cabinet ou une passerelle locale dédiée, pas à la Station.
3. Avant **acceptation ET libération physique**, revalider : Station authentifiée/enrôlée et non révoquée, cabinet/tenant exact, session patient active et identifiée, identité clinique exacte, document de la bonne personne, dernière version active, finalisation de confiance, autorisation explicite du praticien, empreinte SHA256 et politique d'impression dédiée. Aucun QR/NFC seul, cookie Station seul, nom, téléphone ou date de naissance ne doit autoriser un job.
4. **Identification de secours sans Companion appairé** : jamais d'auto-impression sur l'imprimante publique sur de seules informations déclaratives ; parcours d'accueil possible uniquement après **vérification d'identité par le personnel habilité** et preuve d'action, à détailler et tester avant code.
5. **Confidentialité du papier** : `near_station` interdit tant qu'il n'existe pas de mécanisme de libération protégée, contrôlé et testé (PIN de retrait unique, impression retenue ou dispositif physiquement protégé). Toute preuve de libération doit parvenir au patient **par un canal personnel indépendant de l'écran de la Station**, ou être remise par le personnel après contrôle d'identité ; **aucun code, QR de déblocage ni secret de retrait affiché sur écran partagé, imprimé en avance ou dérivé du jeton Station**. Si le patient n'a ni canal personnel sûr ni intervention du personnel ni matériel de sortie protégée, désactiver ce mode et orienter vers accueil. `reception` : sortie hors accès public, personnel remet au patient contrôlé.
6. **Spool et temporaires** : aucun dossier patient sauvegardé dans DB/log/fichiers de la Station. Inventorier les traces de job dans OS Windows, driver, imprimante, fichiers temporaires, crash/reboot ; ne pas promettre de purge absolue là où elle n'est pas observable. Restreindre permissions, chiffrer stockage temporaire si techniquement disponible, borner TTL et éliminer les artefacts selon un contrat testé sur le matériel exact.
7. **Fail closed** : imprimante inconnue, permission insuffisante, configuration absente, certificat/agent non fiable, service offline, QR replay, changement de station/cabinet, document révoqué, erreur de spool ou statut ambigu ⇒ pas d'impression, pas de fuite, information neutre, alternative à l'accueil / Companion.
8. **Anti-répétition et courses (y compris entre destinations)** : une seule intention de remise papier autorisée **par couple Cabinet/session/document/version**, quel que soit le choix `near_station` ou `reception`. Une clé d'idempotence cliente seule, ou un verrou qui inclut la destination, **ne suffit pas** : créer un verrou/identifiant de délivrance serveur atomique, indépendant de l'imprimante, contre double-clic, QR replay, requêtes concurrentes et bascule Station↔accueil ; éviter deux feuilles en mode `both`. Pour chaque tentative, conserver la destination initiale et interdire la migration silencieuse. Si l'état de la file/du matériel est inconnu, marquer `uncertain/held_for_manual_review`, **bloquer toute relance ou seconde destination jusqu'à réconciliation par un agent habilité** ; une impression physique exactement-une-fois ne peut pas être garantie après crash sans preuve matérielle. Réémission exceptionnelle : nouvelle décision justifiée et auditée par le personnel, jamais sur seul clic/retry. Purge/expiration/révocation empêche *toute future libération* tant que le papier n'est pas physiquement sorti ; indiquer les limites d'annulation dès que le moteur a commencé l'impression.
9. **Audit minimisé et exact** : acteur, locataire, session, document ID + SHA, destination approuvée, identifiant de délivrance + job ID, timestamp, état `requested/accepted/held/released/completed/failed/cancelled/uncertain` ; ne jamais journaliser PDF, nom patient, token QR, PIN ou donnée clinique. Les réponses Station divulguent **uniquement un état sans détail médical**. `COMPLETED` signifie impression effectivement confirmée par la chaîne certifiée, pas simplement « placé en file » ; un acquittement de spool ne prouve ni sortie papier ni remise au bon patient.

## 4. UX et états

Station, uniquement pour une session autorisée : conserver **« Recevoir sur mon téléphone »** (04.7) ; ajouter option **« Imprimer mon document »** seulement quand mode/destination disponibles et certifiés. Confirmation explicite 1 exemplaire, destination et avertissement confidentialité. En mode `both`, sélection volontaire sans choix par défaut ; en `near_station`, instructions de retrait protégé ; en `reception`, instruction de remise à l'accueil sans divulgation de données cliniques sur écran partagé.

États sans fausse promesse : `indisponible` → `confirmation` → `demande reçue` → `en attente de libération` → `impression confirmée` ou `échec/annulé`. **Aucun texte « imprimé » sur seul HTTP 202/queue.** Déconnexion, annulation, sortie de Station ou TTL doivent effacer l'affichage patient et bloquer les demandes tardives. Échec = explication simple et fallback explicite, sans fallback implicite.

FR/EN/AR et RTL, navigation clavier, lecteurs d'écran, 360×800 / 390×844 / 430×932 sur mobile si UI disponible, 768/1280 Station, tailles normales et texte 200 %, pas d'overflow ni bouton inactif. Ne pas modifier les flux Patient Companion, QR/NFC et l'arrivée en rendez-vous.

## 5. Découpage d'exécution proposé

- **04.8-A — Architecture / matériel** : inventorier imprimantes réseau/USB, Windows spool/driver, politique de libération sécurisée, agent/passerelle, certificats, accès admin. Fixer matrice matériel supporté ; pas de revendication sans test.
- **04.8-B — Configuration** : modèles de politique/migrations en défaut `disabled`, allowlist, droits et mapping destination Station/accueil, invariants multi-tenant.
- **04.8-C — Service d'impression** : API command/status sans PDF, revalidation, idempotence, job state machine, agent de confiance, journal minimal, TTL/révocation et nettoyage.
- **04.8-D — UI** : choix conditionnel Patient / destination, dialogues sûrs, FR/EN/AR/RTL, retours erreur sans divulgation, boutons accessibles.
- **04.8-E — CI et certification physique** : tests adversariaux, captures BEFORE/AFTER, pilote Windows réel, revue A sécurité vs B UX/QA sur le même SHA, approbation humaine, GO d'activation explicite.

## 6. Gates de sortie obligatoires

**REQUIRED / CI** : test `GET Station PDF === 423` immuable et **zéro PDF bytes dans navigateur Station** ; tests tenant différent, patient différent, mauvais accès, QR rejoué, document non finalisé/non autorisé/tamper, imprimante non allowlist, Station révoquée, changement de politique, double clic, copie multiple, déconnexion, imprimer après purge/TTL, reboot/crash/queue bloquée, faux retour « imprimé », logs propres, absence de cache PDF public. En mode `both`, **deux clics concurrents pour deux destinations ne doivent produire qu'une seule délivrance**, même avec clés d'idempotence différentes ; changement de destination après soumission refusé ; statut de job incertain interdit toute relance automatique ; réémission nécessite agent habilité et trace ; libération publique sans canal privé refusée. Test redémarrage entre acceptation/spool/feuille sortie, avec état conservateur. Tests sur Windows pour print agent natif ; contrôles avant/après mêmes viewports et traductions.

**REQUIRED / terrain avant activation** : deux machines Cabinet + Station réellement distinctes, réseau/TLS contrôlé, deux destinations **physiques** si mode `both`, document **synthétique** dont les octets en entrée de l'agent sont vérifiés par SHA-256 contre la version Cabinet ; papier sorti contrôlé visuellement (contenu/pages/destination) avec preuve humaine, **sans prétendre pouvoir mesurer le SHA-256 d'une feuille papier**, personnel témoin du bon emplacement, mécanisme de sortie confidentielle Station, spool inspecté avant/après annulation, échec/reboot, déchets papier, job de réémission, et absence de PDF dans l'historique/Downloads de la Station. Cas de panne validés fail-closed. Si un sous-test ne peut être observé, état OPEN et mode correspondant désactivé.

**EXPERIMENTAL** : tests hors périmètre hardware supporté, à isoler comme tels, sauf risque sécurité avéré. **HORS SCOPE** : imprimante directe `window.print()`, déploiement Vercel, impression auto sans demande patient, routage silencieux, usage de véritables dossiers patients dans les essais.

**CLOSEOUT** : même HEAD, tests exécutés, deux revues adversariales internes propres et confirmation indépendante si disponible, zéro BLOCKER/MAJOR, preuves physiques, décision utilisateur et mise à jour roadmap, avant toute PR de merge/deploy. Sans ces preuves : **04.8 OUVERT**.

## 7. Interaction avec le statut actuel de 04.7

Au moment de cette conception, [PR #840](https://github.com/hraaaaf/Digital_crown/pull/840) est OPEN/DRAFT au HEAD `445d63b9b1a677a4b0059744cc6c9d08a15a3131` avec **50 succès, 2 ignorés et 1 gate humain rouge** (`Human Visual Approval`) ; aucune approbation visuelle implicite issue de la présente décision **C**. **Cette spécification ne change aucun fichier de 04.7**, et ne déclenche ni fusion sur `master` ni déploiement.

**Source de la décision :** instruction explicite de l'utilisateur « Pour l'impression sécurisée depuis la Station, je choisis C : les deux selon la configuration du cabinet. Intègre ce choix dans la conception du LOT 04.8, sans compromettre les protections de 04.7. ».
