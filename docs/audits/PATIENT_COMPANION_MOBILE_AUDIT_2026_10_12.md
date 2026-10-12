# Patient Companion mobile — audit initial du 12 octobre 2026

Statut : AUDIT TECHNIQUE INITIAL TERMINÉ / AUDIT VISUEL ET FUE-G NON TESTÉS.
Base examinée : `c0d47f4832e6da2211c6f94eb88f0db56fcaebb6` (origin/master).
Branche : `codex/patient-companion-audit-20261012`.
Cette PR ouvre le chantier demandé et documente le diagnostic ; elle ne modifie aucun comportement produit et ne constitue pas une autorisation de merge, de certification ou de déploiement.

## Goal / succès / preuve

Goal : établir la surface patient existante, ses risques et le premier lot correctif avant implementation.
Succès observable : constats liés au code courant, priorités concrètes, validation ciblée et limites explicites.
Preuve : inspection de la base ci-dessus et exécution de quatre suites frontend, 13 tests PASS.
EXECUTION_SCORE : 7.5/10. ADVERSARIAL_SCORE : 7.5/10. RETAINED_SCORE : 7.5/10.
Plafond : captures et preuve réelle du parcours mobile manquantes ; aucune fidélité visuelle ni certification exhaustive revendiquée.
Divergence > 0.5 : non.
Next exact : rendre le parcours capturable sur environnement isolé, puis traiter la vérité des statuts et de la fraîcheur.

## Architecture réellement utilisée

- Entrée canonique : `frontend/src/App.tsx`, route publique `/companion`, montant `features/patient-companion/PatientCompanionApp.tsx`.
- Appairage QR/code à usage unique et identité appareil : `backend/routers/patient_companion_pairing.py`.
- Coffre IndexedDB dédié : `PatientCompanionStorage.ts`, enveloppe AES-GCM et clés WebCrypto. Données partagées par le cabinet, pas copie cloud du dossier.
- Accès local via API cabinet ; transport distant chiffré et relay opaque lorsque l'appairage possède remoteTransport.
- Agenda, questionnaires, consentements, notifications, messages, photo d'urgence, finance et téléconsultation existent déjà.
- `/patient-companion` est une entrée distincte dans `main.tsx`, montant `PatientCompanionEntry` et `PatientCompanionPage` avec identité Firebase. Ne pas confondre cette compatibilité historique avec le shell local-first.
- Les documents PC-00…PC-09 et leurs anciens runs servent de contexte historique, pas de preuve de cette nouvelle campagne.

## Parcours et état de couverture

| Étape | Parcours | Santé et preuve actuelle |
| --- | --- | --- |
| 1 | Ouvrir /companion sur un téléphone vierge | Contrat frontend testé ; rendu navigateur NON TESTÉ |
| 2 | Scanner le QR ou saisir le code | Code manuel et retrait du token de l'URL testés ; caméra, QR réel, HTTPS et invitation backend NON TESTÉS |
| 3 | Ouvrir le coffre et choisir le dossier | Lecture locale et choix explicite multi-dossiers testés ; cycle de changement complet NON TESTÉ |
| 4 | Vérifier la connexion et synchroniser | Snapshot atomique et maintien du cache après erreur testés ; vérité de la fraîcheur et erreurs à corriger |
| 5 | Lire et gérer les rendez-vous | Transport chiffré testé ; badge de statut incorrect par construction ; réservation serveur réelle NON TESTÉE |
| 6 | Utiliser documents, messages et autres services | Surfaces cartographiées ; parcours complet et permissions NON TESTÉS dans cette campagne |
| 7 | Reprendre hors connexion ou après expiration | Cache affiché sans contact cabinet testé ; expiration à chaud et reprise réseau NON TESTÉES |
| 8 | Installer la PWA ou effacer l'appareil | Manifest et suppression inspectés ; installation et effacement réel NON TESTÉS |

## Constats prioritaires

### F01 — P1 : le statut des rendez-vous est remplacé par « Confirmé »

Preuve : `PatientCompanionApp.tsx:728` rend un badge constant. `backend/routers/patient_companion_agenda.py:101-124` exclut ANNULE mais retourne les autres statuts avec leur valeur réelle.
Impact : un rendez-vous non confirmé ou terminé peut être présenté comme confirmé. Il ne s'agit pas d'un défaut serveur d'autorisation.
Correction attendue : rendre le statut canonique avec un fallback explicite pour une valeur inconnue ; vérifier les actions permises selon ce statut.
Validation : couvrir les statuts réellement définis dans les modèles et les valeurs inconnues, puis capturer chaque état pertinent.

### F02 — P1 : une actualisation partielle rafraîchit la date du coffre entier

Preuve : branche relay de `PatientCompanionApp.tsx:415` : refreshAgenda puis syncState=synced ; `PatientCompanionStorage.ts:381-405` : saveAppointments remplace syncedAt sans actualiser shares. La date globale est rendue à `PatientCompanionApp.tsx:699`. checkCabinet utilise aussi saveAppointments.
Impact : des documents anciens peuvent paraître aussi récents que l'agenda ; « Synchroniser mon espace » couvre en réalité un sous-ensemble dans ce chemin.
Correction attendue : fraîcheur par domaine, libellé exact de la portée de chaque actualisation et état partiel explicite.
Validation : documents T0, agenda T1 ; prouver que la date des documents reste T0, y compris après « Vérifier la connexion ».

### F03 — P1 : effacement complet sans étape de confirmation

Preuve : `PatientCompanionApp.tsx:620-625,820` appelle directement clear ; `PatientCompanionStorage.ts:571-578` supprime la base IndexedDB entière.
Impact : un tap peut supprimer appairages, clés et données locales, notamment les demandes/messages/photos encore en attente. Il ne supprime pas le dossier cabinet.
Correction attendue : confirmation explicite indiquant le périmètre et les éléments non transmis, possibilité de revenir en arrière, feedback en cas d'effacement bloqué.
Validation : test sur coffre jetable uniquement ; annulation conserve les données, confirmation efface effectivement, onblocked produit une erreur visible.

### F04 — P1 : l'installation utilise le manifest professionnel Pocket

Preuve : `frontend/index.html:11` référence l'unique manifest ; `frontend/public/manifest.json` définit Digital Crown Pocket, id=/ et start_url=/?source=pwa. Le patient entre sur /companion.
Impact attendu : une installation depuis le parcours patient peut rouvrir le point d'entrée général du cabinet et perdre le contexte patient. L'effet exact sur iOS/Android reste à vérifier sur appareils.
Correction attendue : définir l'identité, le start_url et le scope installable du Companion ; respecter la coexistence avec Pocket.
Validation : première installation et relance sur iOS et Android, patient appairé et hors connexion.

### F05 — P2 : erreurs d'accès et panne réseau confondues

Preuve : `PatientCompanionApp.tsx:317-343` : checkCabinet transforme toute réponse non OK en offline. syncWallet distingue 401/403 mais remet aussi cabinetReachability à offline.
Impact : accès expiré/révoqué et serveur non joignable donnent des indications contradictoires ou une mauvaise action de reprise.
Correction attendue : distinguer réseau, expiration, accès refusé et erreur serveur, conserver le cache avec son statut connu.
Validation : 401, 403, 500 et absence réseau avec les libellés/actions correspondants ; ne pas assimiler un refus à un cabinet hors ligne.

### F06 — P2 : expiration locale figée et états non réinitialisés au changement de dossier

Preuve : `PatientCompanionApp.tsx:75-78` calcule sessionExpired dans useMemo dépendant de activePairing, sans horloge réactive. `selectContext:460-473` change le coffre/contexte sans réinitialiser syncState, cabinetReachability ni les états agenda.
Impact : si le même appairage reste actif, le message d'expiration peut ne pas changer au passage de l'échéance ; un nouveau dossier peut hériter de feedback et sélections du précédent.
Limite : aucune fuite inter-patient démontrée ; les guards backend doivent rester l'autorité.
Correction attendue : expiration réévaluée aux actions/retour au premier plan et cycle d'état explicitement attaché à access_id.
Validation : horloge simulée, dossier A → B, créneau sélectionné et opération réseau en cours.

### F07 — P2 : demandes réseau sans délai de fin explicite

Preuve : fetch d'appairage dans `PatientCompanionApp.tsx`, de lecture dans `PatientCompanionSync.ts` et `PatientCompanionAgendaApi.ts` sans AbortSignal. La boucle relay borne le nombre d'essais, mais chaque fetch de `PatientCompanionRemoteCommandTransport.ts:120-161` reste sans délai explicite.
Impact possible : serveur qui ne termine pas sa réponse → attente prolongée avec action indisponible et reprise peu claire.
Correction attendue : budget de temps par opération, annulation lors du changement de contexte et feedback récupérable ; préserver idempotence et distinction envoi/ACK.
Validation : réponse qui ne se termine jamais, sortie de l'écran et retour réseau.

### F08 — P2 : la couverture actuelle ne vaut pas validation du premier usage

Preuve : les tests exécutés utilisent mocks de fetch/stockage ; ils ne valident pas invitation staff réelle, backend isolé, permissions caméra, relay réel, installation ni téléconsultation.
Correction attendue : matrice FUE adaptée au patient découvrant le produit, avec PASS/FAIL/NON TESTÉ, preuve et SHA pour chaque scénario.
Validation : viewports 390×844, 768×1024, 1280×900 puis appareils iOS/Android pour les fonctions natives ; persona fictive, données jetables.

## Forces et risques d'accessibilité

Forces vérifiées dans le code et les tests : entrée sans connexion staff, QR/code retiré de l'URL avant requête, cache local ouvrable sans réseau, échec de sync ne remplaçant pas le snapshot, préservation des messages/files lors de saveWallet, demandes en attente distinctes des confirmations.
Les boutons principaux déclarent des hauteurs de 48–56 px et le champ code possède un nom accessible ; l'erreur d'appairage utilise role=alert.
Risques à tester : erreurs non annoncées dans les autres panneaux, focus après changement de phase, ordre de navigation, zoom texte, contrastes en clair/sombre, clavier logiciel, safe areas et lecteur d'écran. Aucun verdict WCAG ou score esthétique depuis le code.

## Validation exécutée

Commande depuis frontend :
```text
npx vitest run src/features/patient-companion/PatientCompanionApp.test.tsx src/features/patient-companion/PatientCompanionSync.test.ts src/features/patient-companion/PatientCompanionAgendaTransport.test.ts src/features/patient-companion/PatientCompanionStorage.messaging.contract.test.ts
```
Résultat : 4 fichiers PASS, 13 tests PASS ; durée 93.67 s.
Installation locale reproductible : npm ci --ignore-scripts --no-audit --no-fund, 818 packages. Aucun lockfile modifié.
Aucun test backend, build release, migration, seed ou accès aux données cabinet exécuté.

## Limite de capture et suite

Le serveur Vite isolé a démarré sur 127.0.0.1:5197. Deux tentatives d'ouverture dans le navigateur intégré ont échoué avant attachement de la vue ; l'alternative Chrome est indisponible. Aucune capture actuelle acceptée n'a donc été obtenue. L'audit Product Design visuel est bloqué par l'environnement, conformément à sa règle de preuve ; ce document est une revue technique, pas un audit UX visuel complet.

Prochain lot recommandé : vérité patient (F01/F02/F05/F06), puis protection de l'effacement (F03) et installation (F04). Avant toute modification visuelle, obtenir BEFORE, Goal/Target, AFTER aux mêmes viewports et validation humaine suivant les règles du dépôt. Ne pas transformer cette liste en nouvelle roadmap concurrente : le propriétaire doit la réconcilier au lot courant dans l'autorité canonique.
