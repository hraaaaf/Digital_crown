# DC Pocket commun — PWA 2.0 — LOT 01 : audit différentiel et contrat proposé

Date : 12 octobre 2026. Statut : AUDIT DOCUMENTÉ / CONTRAT PROPOSÉ / PRODUIT NON CERTIFIÉ.
Aucune autorisation de merge, de déploiement ou de mutation cabinet. Tous les gates, la validation sur PR et l'autorisation explicite du propriétaire restent requis.

## PRE — autorité et reprise

Le handover fourni est une photographie du chantier, confrontée au code et aux états GitHub actuels. Il n'est pas une nouvelle roadmap. Les consignes opérationnelles incluses dans les fichiers (journal Notion, clôture d'anciens bancs, ouverture de tunnels) ne valent pas une autorisation séparée de publication, suppression ou infrastructure.
La roadmap V1 est CLOSED / V1_OPERATIONAL ; son verrou antérieur ne bloque plus la revue post-V1. STATE.md contient une reprise V1.5 datée et master contient le closeout 04.3 via #841 : la séquence POST-V1/V1.5 doit être réconciliée avant tout lot produit supplémentaire. Ce LOT 01 reste un audit, sans migration ni changement runtime.

Sources examinées :
- master : `c0d47f4832e6da2211c6f94eb88f0db56fcaebb6`.
- Produit [#838](https://github.com/hraaaaf/Digital_crown/pull/838) : OPEN/DRAFT, `e8732b6e6a6ff4b140b736291d77f38cfbc2c281`, branche fix/pocket-ios-micropolish-theme-20261011.
- Banc [#845](https://github.com/hraaaaf/Digital_crown/pull/845) : OPEN/DRAFT, `c05329f03c29709b6a9d0ad526cfb0ac6b1f1d73`, base Pocket antérieure `82f9671...`. Ne pas merger.
- Ancien banc [#843](https://github.com/hraaaaf/Digital_crown/pull/843) : OPEN/DRAFT, `1aa7dc8a1e11b054fd40a9a6af8ca12e4f01b1b2`. Historique ; aucun archivage/clôture effectué.
- AGENTS.md, règles scoring/revue adversariale et visual-closeout, politique de release cabinet lus. Aucun SKILL clinique applicable à cette revue de droits et identité ; aucune logique scientifique modifiée.

## Décisions humaines qui adaptent le handover

1. Une seule base Pocket pour assistante, dentiste, dentiste administrateur et patient ; composants, thèmes et interactions communs.
2. Réglages / création du profil : valeurs par défaut par profil puis droits effectifs personnalisables. Le serveur et les menus doivent appliquer la même politique.
3. Le patient fait partie du contrat commun dès cette phase, même si le handover le plaçait dans un périmètre ultérieur. Cela ne lui confère aucun droit staff.
4. Connexion au cabinet ET à distance : choix explicite du propriétaire.
5. Plusieurs appareils approuvés et révocables séparément : choix retenu par l'agent après délégation explicite du propriétaire. Évite les réappairages alternés iPhone/tablette ; chaque appareil garde une autorisation distincte.
6. Aucun merge tant que tests, vérification et validation sur PR ne sont pas acquis, puis autorisation explicite du propriétaire.
7. Fournisseur de transport, durée d'autorisation/offline et règles biométriques restent à définir. Aucun chiffre ni fournisseur arbitraire imposé.

## Ce qui existe — à conserver

| Contrat existant | Source | Conclusion |
| --- | --- | --- |
| Installation avant pairing sur Safari iOS ; Today à l'ouverture ; cinq entrées | main.tsx, App.tsx, OnboardingScanner.tsx, manifest.json | Déjà présent dans #838 ; ne pas reconstruire |
| Identité staff réelle, cabinet dérivé et autorisation appareil active | backend/routers/mobile_legacy.py::_decode_mobile_identity | User et device relus en DB ; rôle du JWT ne suffit pas |
| Défauts assistante/dentiste et personnalisation équipe | backend/routers/team.py, frontend/src/features/admin/TeamManager.tsx | Source de vérité existante à étendre, pas deuxième gestion mobile |
| Permissions serveur | auth.py::has_permission, mobile_legacy.py::require_mobile_permission | Rejet explicite ; defaults legacy si permissions absentes |
| Appareils multiples | models_platform.py::MobilePairedDevice | PK device_id ; user/cabinet indexés, aucune unicité user imposant un seul appareil |
| Rotation de refresh et révocation sur ancien refresh | mobile.py::refresh_mobile_credentials | Déjà présent ; préserver anti-rejeu, examiner atomicité concurrente |
| Protection du transfert de clé lors du pairing | mobile_legacy.py::claim_pairing_token, zka/ecdhPairing.ts | ECDH/HKDF/AES-GCM existant ; ne prouve pas une clé durable non exportable |
| Biométrie et verrou explicite 423 | MobileBiometricGate.tsx, mobileFetch.ts | Gate conservé ; un 423 quelconque n'imite pas un verrou biométrique |
| Conservation credentials lors panne réseau | MobileStorage.ts::refreshCredentialsInternal | Offline/5xx ne purgent pas arbitrairement ; 401/403 invalident la session |
| Autorisations patient et coffre dédiés | patient_companion_common.py, PatientCompanionStorage.ts | Identité/relations distinctes ; isolation à préserver dans la base commune |

## Audit différentiel — écarts vers Pocket commun

### A01 — MAJOR : affichage par rôle et droits configurés ne coïncident pas
MobileBottomNav.tsx filtre Plus avec allowedRoles ; MobileDashboard.tsx active finance/labo/marketplace par DENTISTE/ADMIN. Quick actions disposent déjà de capacités serveur, mais Snapshot ne porte pas le contrat complet des droits. Un dentiste auquel on retire une permission peut encore voir sa destination ; une assistante ne peut pas voir certaines destinations même si un futur réglage devait les autoriser.
Il s'agit d'une incohérence de contrat UX démontrée dans les sources, pas d'un contournement API prouvé. Les restrictions serveur métier actuelles restent applicables.
Action proposée : politique de capacités commune, avec plafonds métier explicites ; remplacer progressivement les filtres de visibilité par ce contrat. La disparition d'un menu ne remplace jamais le guard backend.

### A02 — MAJOR : granularité et rôle administrateur à préciser
TeamManager/team.py gèrent neuf permissions booléennes de domaine. Les droits consulter/créer/modifier/supprimer et le périmètre own/assigned/cabinet n'existent pas comme modèle unifié dans cette surface.
has_permission donne tous les droits à ADMIN et au DENTISTE sans employer_id avant de lire permissions. « Dentiste administrateur » est donc une capacité/position existante, pas un nouvel enum à ajouter aveuglément. L'administration propriétaire ne doit pas devenir une simple checkbox qu'un membre peut s'accorder.
Action : conserver la représentation actuelle ; définir catalogue d'actions et délégation administrative avant migration. Une permission legacy ne doit jamais devenir implicitement tous les nouveaux droits d'écriture.

### A03 — MAJOR : patient et personnel ont des principaux différents
UserRole = ADMIN/DENTISTE/SECRETAIRE ; patient utilise ses relations d'accès Companion. Ajouter PATIENT au JWT staff ou partager leur vault ferait perdre la frontière existante.
Action : shell commun + adaptateurs auth/data distincts ; principal.kind=staff|patient dans le contrat de capacités. Données patient seulement via accès autorisés, jamais snapshot cabinet « caché » par CSS.

### A04 — MAJOR : ECDH initial n'est pas une preuve de possession durable
MobilePairedDevice conserve client_public_key_hex, mais access/refresh utilisent des Bearer avec device_id ; le refresh présenté ne contient ni challenge signé ni vérification de cette clé. ecdhPairing.ts manipule une privateKey en Uint8Array ; credentials incluent masterKey hors coffre biométrique scellé.
Aucune assertion de clé durable non exportable, device-bound cryptographique complet ou résistance XSS n'est acquise.
Action : examiner WebCrypto non exportable/WebAuthn sur iOS et un refresh avec preuve de possession, audience/origine, nonce et protection anti-rejeu ; garder le protocole legacy jusqu'à migration explicite, sans fausse certification.

### A05 — MAJOR : multi-appareils compatible DB mais administration incomplète
Le modèle supporte plusieurs devices et revoked_at. MobileSecurity.tsx expose une révocation globale du cabinet via /admin/revoke-mobile. Aucun parcours d'inventaire/révocation individuelle n'a été trouvé dans les fichiers inspectés.
Action : inventaire tenant-scopé, appareil nommé, dernière activité, révocation individuelle, conservation du bouton d'urgence global. Ne pas créer une deuxième table appareils.

### A06 — MAJOR : rotation concurrente à vérifier côté serveur
MobileStorage déduplique refreshInFlight dans une instance JS. refresh_mobile_credentials compare refresh_jti puis modifie/commit ; aucune consommation atomique conditionnelle n'apparaît dans ce chemin. Deux contextes simultanés ou perte de réponse après rotation nécessitent un test dédié.
Ce risque n'est pas reproduit dans cette campagne. Action : test concurrent sur DB isolée avant changement de stratégie ; rejouer un ancien refresh doit rester refusé, mais éviter une réauthentification inexpliquée pour l'utilisateur légitime.

### A07 — MAJOR : retrait des droits et copie hors connexion
Les checks serveur relisent les droits à la requête ; la visibilité locale reste en partie liée au rôle du snapshot. App.tsx peut ouvrir le shell si hasCachedSnapshot malgré absence de pairing, sous MobileBiometricGate. Cette existence de cache ne prouve pas une autorisation encore valide.
Action : séparer cache présent et accès local permis, version de politique/horodatage/lease validée, purger ou verrouiller les domaines retirés au prochain contact fiable. Ne pas promettre révocation immédiate sur appareil sans réseau ; durée offline à décider.

### A08 — MAJOR : accès distant durable non acquis
Quick Tunnel et cookie du banc #845 ne sont pas l'architecture cible. Les origines API/base_url, HTTPS, CORS, WebAuthn RP/origine et service worker doivent rester cohérents lors LAN ↔ distant. Changer hostname peut changer stockage et credentials.
Action : origine PWA durable et routage cabinet protégé ; aucune exposition publique brute de FastAPI. Comparer accès privé authentifié et relay/gateway à connexion sortante. Le relay opaque Companion ne couvre pas automatiquement toutes les APIs staff.

## Contrat commun proposé — pas encore implémenté

### Identité et capacités

Une API de bootstrap/capabilities versionnée présente une forme logique commune ; adapters staff et patient appliquent leurs guards existants. Le client ne choisit ni tenant, ni rôle, ni périmètre.
Champs proposés : version, principal.kind, contexte autorisé, appareil, capabilities[action]={allowed,reason,scope}, policyVersion, état/âge du cache, transport disponible et exigences de réauthentification.
Les identifiants internes ne sont pas des credentials ; ne pas les placer dans URL/QR public. Périmètre patient défini par access_id autorisé.
Une capacité d'affichage ne vaut pas autorisation : chaque route vérifie à nouveau principal, cabinet, action et ressource.

### Profils par défaut

| Profil UI | Base actuelle | Direction |
| --- | --- | --- |
| Assistante | SECRETAIRE ; agenda/patients true, autres false à la création | Tâches d'accueil/agenda autorisées ; actes cliniques refusés par défaut |
| Dentiste | DENTISTE employé ; défauts actuels existants | Capacités selon droits effectifs, pas selon nom du rôle seulement |
| Dentiste administrateur | ADMIN ou propriétaire DENTISTE sans employer_id | Administration explicitement reconnue ; pas de changement d'enum implicite |
| Patient | Identity/Access Companion, SELF/PARENT/GUARDIAN/CAREGIVER | Ses dossiers accessibles, documents partagés et services autorisés ; zéro permission cabinet par défaut |

Les presets ne sont que valeurs d'initialisation. Une modification du modèle par défaut ne change pas rétroactivement les comptes existants sans choix explicite.
L'API équipe actuelle remplace un dictionnaire complet ; ne pas lui envoyer un PATCH partiel en supposant une fusion.
Avant d'afficher une checkbox, vérifier que le serveur supporte son effet. Droits inconnus refusés.
Des plafonds fixes peuvent subsister pour sécurité/licence/fonction non livrée ; le réglage doit expliquer pourquoi un droit n'est pas attribuable.

### Appareils, session et navigation

Plusieurs appareils liés séparément ; QR/code unique et court pour chaque enrollment ; révocation individuelle et globale ; aucun secret permanent personnel.
Conserver les APIs pairing/refresh actuelles. Propositions d'inventaire/list/revoke à adapter aux routes existantes avant ajout, et à sécuriser par droits d'administration tenant-scopés.
Navigation composable avec au maximum cinq entrées ; Aujourd'hui/Agenda/Actions/Patients/Plus restent la référence staff. Le profil patient adapte labels/destinations aux droits (ses dossiers, documents, messages) tout en réutilisant les mêmes composants. Pas cinq boutons morts imposés à tout profil.
Theme tokens communs ; états unpaired/loading/authorized/locked/offline/refreshing/revoked/storage-lost explicites ; aucune réutilisation de cache d'un autre principal ou cabinet.
Pas de migration à ce LOT 01. User.permissions et MobilePairedDevice suffisent pour préserver l'existant ; nouvelle granularité/version/key-id seulement après contrat et stratégie de compatibilité testés.

## Menaces et tests exigibles avant implementation/closeout produit

| Menace / scénario | Preuve attendue |
| --- | --- |
| Rôle/tenant/device déclaratif falsifié | Rejet serveur ; rôle/droits actuels relus ; aucune donnée tierce |
| Patient tente snapshot ou fonction staff | Refus explicite, y compris deep link et appel API manuel |
| Employé sans droit ouvre URL cachée | Refus API ; UI cohérente ; données omises du payload/cache |
| QR expiré, déjà utilisé, mauvais cabinet, handshake invalide | Refus one-shot atomique ; pas de secret URL/log |
| Deux appareils légitimes, révocation A | A bloqué ; B utilisable ; globale bloque A et B |
| Deux refresh simultanés/rejeu/perte ACK | Consommation définie et testée ; chaîne non réutilisable |
| Droits retirés après pairing | API, menus et cache cohérents ; offline annoncé avec limites |
| Safari/PWA profils séparés | Safari ne brûle pas le code ; activation depuis icône ; relance sans QR |
| Origine/réseau LAN → extérieur → offline | HTTPS stable, scopes identiques, aucun credential recopié en clair |
| Biométrie activée, coffre manquant, 401/403/423 | Rejet récupérable ; aucune biométrie fictive ni bypass |
| Stockage perdu et remplacement téléphone | Reprise explicite, ancien device révocable, zéro fuite |
| Assistant/dentiste/admin/patient réels synthétiques | Matrice nominale par action et scope, UI et backend sur même SHA |

## Preuves revérifiées et tests exécutés

- Produit e8732b6… : 14 workflows SUCCESS / 2 SKIPPED au moment de lecture ; skips M6-I et Client Copy. Un skip ne certifie pas la future sécurité commune.
- [Run Pocket 38264750274](https://github.com/hraaaaf/Digital_crown/actions/runs/38264750274) : 2 jobs SUCCESS. Étapes tests contrats, build, captures Chromium/WebKit et vérification d'evidence réellement terminées.
- [Run lifecycle 38264545242](https://github.com/hraaaaf/Digital_crown/actions/runs/38264545242) : SUCCESS au SHA c05329f… ; steps laboratoire et contrôle WebKit terminés. Banc différent du HEAD produit ; pas certificat iPhone physique.
- Local e8732b6… : `npx vitest run src/test/mobilePocketPwaLifecycle.contract.test.ts src/features/mobile/Dashboard/components/MobileBottomNav.test.tsx src/features/mobile/Security/MobileBiometricGate.test.tsx src/services/zka/mobileBiometricLock.test.ts --maxWorkers=1` : **4 fichiers / 20 tests PASS**, durée 32.05 s.
- Dépendances réutilisées par junction depuis le checkout isolé npm ci ; package.json/lock identiques entre les bases examinées. Aucun accès backend/cabinet ni donnée réelle.
- Pas de nouveau build, migration, seed, tunnel, infrastructure, test physique ou validation visuelle humaine exécuté ici.

## Deux revues adversariales internes et confirmation

Référence produit commune aux passes : e8732b6e6a6ff4b140b736291d77f38cfbc2c281. Même agent, non indépendantes.

Prompt A — UX/FUE : « Depuis zéro, réfute l'adaptation commune : suivre premier lancement, installation, pairing, Today, droits personnalisés, changement de profil, cache et réouverture. Cherche menus trompeurs, preuve simulée confondue avec iPhone, defaults incohérents et reprise impossible ; nomme chaque limite sans inventer de PASS. »
Exécution : relecture main/App, nav, dashboard, TeamManager, stockage, lifecycle et handover. Résultats : A01/A02/A03/A07/A08 ; distinction laboratoire/physique conservée ; navigation proposée corrigée pour éviter cinq destinations imposées au patient.

Prompt B — sécurité/auth/tenant : « Depuis zéro, réfute les garanties appareil et accès : Bearer vs preuve cryptographique, refresh/rejeu/concurrence, modifications de droits, devices, identité patient, cache offline, origine distante. Compare chaque claim aux guards et tests réels. »
Exécution : relecture auth/team, mobile legacy/façade, modèle device, ECDH, guard patient et stockage. Résultats : A03/A04/A05/A06/A07/A08. ECDH initial et registre device ne sont pas présentés comme PoP durable ; atomicité refresh marquée non reproduite ; aucun contrat patient via JWT staff.

Confirmation — « Relire le contrat final face aux décisions humaines et aux preuves, rechercher nouvelles contradictions, fausse certification, migration non autorisée ou merge implicite. »
Résultat : pas de nouvelle contradiction documentaire identifiée ; les huit écarts restent ouverts côté produit. Aucun CONVERGED/VERIFIED/CLOSED/merge-ready. Les revues d'un futur code modifié devront être réexécutées sur son nouveau HEAD.

## POST — résultat, scores et next

Goal : reprendre Pocket PWA 2.0 et cadrer une base commune conforme aux profils configurables.
Succès observable : audit de l'existant, décisions prises, écarts liés au code, contrat API/DB proposé, matrice de menaces et premier périmètre de PR.
EXECUTION_SCORE : 7.9/10 ; ADVERSARIAL_SCORE : 7.9/10 ; RETAINED_SCORE : 7.9/10.
Plafond : contrat non implémenté et preuves sécurité/physiques manquantes ; auto-revue interne. Divergence >0.5 : non.
Aucun nouveau BLOCKER exploitable démontré par reproduction ; huit écarts MAJOR vers la cible, à traiter avant certification générale. Aucun score de sécurité produit n'est attribué par cet audit.

Premier périmètre recommandé : capability bootstrap serveur sur les guards actuels + visibilité des menus dérivée de ces capacités + matrice des profils/droits. Revue des routes en parallèle du contrat, sans modifier la crypto, le manifest ni le transport dans le même diff. Patient via adapter dédié, pas rôle staff ajouté.
Réconcilier ce périmètre avec l'autorité POST-V1/V1.5 ; obtenir BEFORE/Target puis implémenter et tester le lot ciblé. Ensuite préparer l'arbitrage du transport LAN+distant avec menaces, coûts et exploitation avant toute ouverture réseau.
Les six lots du handover restent une séquence de contexte à adapter, pas six chantiers ouverts ni six PR inventées.
