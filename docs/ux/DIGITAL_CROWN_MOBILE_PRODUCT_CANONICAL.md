# Digital Crown — Mobile Product — Canonical Roadmap

Status: ACTIVE
Canonical file: `docs/ux/DIGITAL_CROWN_MOBILE_PRODUCT_CANONICAL.md`
Repo: `hraaaaf/Digital_crown`
Current merged product baseline: `e30b858f58686f5f7bef19ca93f1c5dae42929c9`
Deployment: none. No Vercel deployment is authorized by this chantier.

## Goal final
Faire de Digital Crown mobile un **cockpit opérationnel clinique**, pas une copie réduite du desktop. Les actions mobiles doivent viser les usages au fauteuil, entre deux patients ou hors du poste principal, idéalement en moins de 30 secondes. Le desktop reste le système complet pour les workflows lourds, la production clinique détaillée et le paramétrage.

Exception fonctionnelle verrouillée — SuperAdmin : le mobile ne réduit **aucune** prérogative SuperAdmin active. L'adaptation porte uniquement sur l'UX mobile, les confirmations et les step-up de sécurité requis par le backend.

## Doctrine verrouillée
- Mobile = cockpit opérationnel.
- Desktop = workflows lourds/complets.
- SuperAdmin mobile = parité fonctionnelle des prérogatives SuperAdmin actives, sans SuperAdmin lite.
- Source de vérité unique serveur/DB pour desktop + mobile.
- Thème/typographie pilotés par les réglages cabinet, sans couleurs/polices de marque hardcodées dans les features mobiles.
- Tout changement UI suit : BEFORE → Goal UI → référence/mockup → implémentation → AFTER mêmes viewports → comparaison + tests + score visuel.
- Aucun Vercel sans autorisation explicite.

## Navigation mobile canonique
`Aujourd’hui / Patients / + / Assistant / Plus`

---

# Lots certifiés

## MOB-2 — Patient Cockpit — DONE / MERGED
- PR `#354`
- merge `5fd2a06663e941581ad422267d31a5bb69a13d11`
- closeout master `508a2e1e174887fe44f271cc6a8283eb89e443c7`
- AFTER run `33889545163` ✅
- artifact `9943369750`
- digest `sha256:b4d274590a3349cbcab8a71faeb25e880acc3aee4ab818420fab8918813777fd`
- score visuel **9.2/10**
- preuve `docs/ux/DIGITAL_CROWN_MOBILE_PATIENT_COCKPIT_MOB2_PROOF.md`

## MOB-3 — Quick Action Hub — DONE / MERGED
- PR `#355`
- merge `23e4828729e085a4566cbfdf430025d1019e53fa`
- closeout `e49907c20c1062e9691fb34c030bcc182289b760`
- AFTER run `33927174832` ✅
- artifact `9957298023`
- digest `sha256:eb96f1193345a3d1770b013eb7451e9d87ca7e95afa062612d08b3078640e8a8`
- score visuel **9.5/10**
- preuve `docs/ux/DIGITAL_CROWN_MOBILE_QUICK_ACTION_HUB_MOB3_PROOF.md`

## MOB-4 — Navigation mobile canonique — DONE / MERGED
- PR `#356`
- merge `28cf8278a31507d96b33c10f03e1635f86223454`
- closeout master `df48ef3cf1af8e9075828b3bf0b9b1f2c874fcda`
- AFTER run `33953721202` ✅
- artifact `9965680255`
- digest `sha256:99ae384612cdffffbb7226ee088f516d564e854900db1b91ceef47bd06afd9b2`
- score visuel **9.6/10**
- preuve `docs/ux/DIGITAL_CROWN_MOBILE_CANONICAL_NAVIGATION_MOB4_PROOF.md`

---

# MOB-5 — Mobile secondaire à forte valeur — ACTIVE / SCOPE LOCKED

## Scope produit verrouillé le 2026-09-05

| # | Fonction | Décision | Cible mobile |
|---|---|---|---|
| 1 | Salle d’attente | Desktop + Mobile | **Coming Soon** sur les deux surfaces ; ne pas implémenter le métier avant audit dédié |
| 2 | Équipe / praticiens | Desktop + Mobile | praticiens, charge/RDV du jour ; `Plus → Équipe` |
| 3 | Bibliothèque clinique | Desktop + Mobile | recherche/consultation rapide ; lecture simplifiée |
| 4 | Science Hub | **Desktop only** | aucun portage mobile |
| 5 | Frontdesk / demandes RDV | Desktop + Mobile | voir, accepter/refuser, appeler/WhatsApp, suivi rapide |
| 6 | Marketplace / Approvisionnement | Desktop + Mobile | refonte dédiée desktop/mobile, moteur catalogue/commande partagé |
| 7 | Stock | Desktop + Mobile | niveaux, alertes, criticité, réassort/mouvements simples |
| 8 | Notifications | Desktop + Mobile | alertes actionnables, priorité/filtrage strict, deep links |
| 9 | SuperAdmin | Desktop + Mobile | **parité fonctionnelle complète des prérogatives SuperAdmin actives** ; UX/confirmations/step-up adaptés au mobile |
| 10 | Patients / génération de documents | Desktop + Mobile | **Quick Document Studio** : flux mobile ciblé réutilisant le moteur Document Studio canonique |

## Invariant données desktop/mobile
Une seule source de vérité serveur/DB. Mobile et desktop consomment le même objet métier et le même historique. Aucun modèle parallèle de données.

Pour les documents, le moteur canonique `/documents/generate`, les permissions par type et `assert_patient_access` restent autoritaires. Aucun moteur de génération documentaire parallèle ne doit être créé pour le mobile.

## MOB-5A — Équipe / praticiens — DONE / MERGED
- PR `#357`
- merge `89098066ef0c943c0e084af4b9cd388d3ab0aa5b`
- artifact `9968666702`
- digest `sha256:6a463707a1c7dbe2bb9623db1e3b19b631d267294ad08dc6bb32dcb729929385`
- 390×844 / 430×932 / 768×1024
- 0 overflow, 0 erreur runtime
- score visuel **9.2/10**
- preuve `docs/ux/DIGITAL_CROWN_MOBILE_TEAM_MOB5A_PROOF.md`

## MOB-5B — Frontdesk — DONE / MERGED
- PR `#358`
- merge `21a41852182c7e74cc66c335c8d67c93a94d5871`
- post-merge master `8891c771f1d77f0ab9347682609b0460881ae2a8`
- cert `33968295005` ✅
- artifact `9970008232`
- digest `sha256:b831122003e2cd71d949c45926fe0f3da6adfa82453a1b09c0111be2f752fe46`
- score visuel **9.3/10**
- preuve `docs/ux/DIGITAL_CROWN_MOBILE_FRONTDESK_MOB5B_PROOF.md`

## MOB-5C — Notifications — DONE / MERGED
Goal : cockpit d’alertes actionnables mobile sans bruit, avec RBAC/tenant isolation et push OS sans PHI.

Fonctions certifiées :
- `Plus → Notifications`
- deep-link `?tab=notifications`
- `NotificationsView`
- source in-app unique `/api/mobile/notifications`
- filtres `Toutes / Prioritaires`
- actions contextuelles allowlistées
- marquer lu
- snooze 24 h
- états empty/error explicites
- alertes Labo exclues tant que leur isolation tenant n’est pas prouvée
- push OS générique sans donnée patient

Preuves :
- PR `#359` merged
- produit certifié `fc40af1a28cb1a8cdc65bce2a5b0357075d3a0a1`
- tête documentaire finale `9fe0b82571d9c2507e0d4af79358c664084ab4dc`
- merge `aaa28ef97b22df2c5654c4e0da7efc15692787a8`
- CI / T2 / Settings / MOB-5C cert ✅
- artifact `9975417271`
- digest `sha256:4e40891c94abc35a49548220b76e075c3d8884157dd8160255f4956a6325fe3c`
- 390×844 / 430×932 / 768×1024
- 5 boutons canoniques, nav 76 px, 0 overflow, 0 erreur runtime ✅
- score visuel **9.4/10**
- preuve `docs/ux/DIGITAL_CROWN_MOBILE_NOTIFICATIONS_MOB5C_PROOF.md`

## MOB-5D — Stock — DONE / MERGED
Goal : consulter criticité stock et lancer une action courte sans dupliquer la logique desktop.

Fonctions certifiées :
- Desktop `/stock` → `StockPage` existante
- `Plus → Stock`
- deep-link `?tab=stock`
- criticité rupture / alerte / OK
- recherche + filtre
- ajustement rapide `-1/+1`
- ajout rapide
- même backend `/stock/*`, même DB, même scoping `employer_id`
- aucun paramétrage lourd ni suppression porté sur mobile

Preuves :
- PR `#360` merged
- HEAD produit certifié `9ce48a6c38aaa20ff2e029646a919a5c2ed5c163`
- tête documentaire pré-merge `08651a595389c17fac6e2fb69baeed7bd96014af`
- merge `9cb740bc52efc9bf734c19fefc3c4f07470eba80`
- CI pré-merge `34040466943` ✅
- MOB-5D cert final `34040466967` ✅
- CI post-merge `34041170446` ✅
- backend complet : **2994 passed, 8 skipped, 4 warnings**
- targeted Vitest : **11/11** ✅
- artifact `9991265607`
- digest `sha256:539b9a1aa6ca55b72b91a4fe1398d5d7c1162a1edd8a26633a9f421a43e8c51f`
- 390×844 / 430×932 / 768×1024
- 5 boutons canoniques, nav 76 px, 0 overflow, 0 erreur runtime ✅
- score visuel **9.3/10**
- preuve `docs/ux/DIGITAL_CROWN_MOBILE_STOCK_MOB5D_PROOF.md`

## MOB-5E — Bibliothèque clinique — DONE / MERGED
Goal : recherche et consultation clinique rapide sur mobile sans portage brut de `EliteLibrary`.

Fonctions certifiées :
- `Plus → Bibliothèque`
- deep-link `?tab=library`
- DENTISTE / ADMIN uniquement
- RBAC fail-closed pendant le chargement du rôle, menu Plus inclus
- source unique : **50 protocoles** `CLINICAL_PROTOCOLS`
- recherche acte / code / discipline
- cartes nom / catégorie / durée / difficulté
- détail mobile réutilisant `ClinicalRefContent`
- favoris `dc_favs` et récents `dc_recents` réutilisés
- aucune API/DB clinique parallèle
- Science Hub reste desktop only

Preuves :
- PR `#361` merged
- HEAD produit certifié `b345d7153196a8ee5e5e05c128eef8a5a8b2ec41`
- merge ref produit certifiée `2bd084d39b47dd6c79b25df69c83723c642887d8`
- HEAD final pré-merge `05cf642937210e70d70172503a142a45016d20f3`
- merge `b850cff2bd03dda667d6e1b6e449230658035d62`
- CI produit `34042238326` ✅
- MOB-5E cert produit `34042238302` ✅
- CI HEAD final `34043911174` ✅
- MOB-5E cert HEAD final `34043911199` ✅
- T2 HEAD final `34043911191` ✅
- backend complet : **2994 passed, 8 skipped, 4 warnings**
- targeted Vitest : **12/12** ✅
- build production ✅
- artifact `9992080508`
- digest `sha256:db3b5956c934701dbe6060781cedd87ad0171e52b85fe877095a58190abe671e`
- 390×844 / 430×932 / 768×1024
- liste + détail : 5 boutons canoniques, nav 76 px, 0 overflow, 0 erreur runtime ✅
- score visuel **9.4/10**
- preuve `docs/ux/DIGITAL_CROWN_MOBILE_LIBRARY_MOB5E_PROOF.md`

## MOB-5F — Patients / Quick Document Studio — ACTIVE / AUDIT + GOAL UI LOCKED
Goal : produire un document courant en idéalement <30 s depuis le dossier patient, en réutilisant le moteur documentaire canonique.

État vérifié au démarrage:
- cockpit patient mobile déjà capable de rechercher/sélectionner un patient et ouvrir ses ressources existantes via contexte opaque;
- aucune entrée de création documentaire sur le baseline `e30b858f...`;
- `/documents/generate` est le moteur canonique existant;
- token mobile appairé accepté par `get_current_user`, puis permissions documentaires et `assert_patient_access` restent autoritaires;
- aucun nouveau moteur backend de génération n'est requis.

Périmètre Quick Document V1 verrouillé par l'audit:
- Ordonnance;
- Certificat;
- Document libre;
- Devis.

Preuves de cadrage:
- `docs/ux/DIGITAL_CROWN_MOBILE_DOCUMENTS_MOB5F_AUDIT.md`
- `docs/ux/DIGITAL_CROWN_MOBILE_DOCUMENTS_MOB5F_GOAL_UI.md`
- branche `ux/mobile-documents-mob5f`
- BEFORE 390/430/768 lancé sur baseline produit `e30b858f...`; artifact/CI à certifier avant implémentation UI.

## MOB-5G — Marketplace / Approvisionnement — DONE / MERGED
Goal : achat cabinet rapide desktop + mobile, sans dupliquer le moteur catalogue/commande existant.

Fonctions certifiées :
- benchmark externe Henry Schein / Patterson / Medline / McKesson effectué avant implémentation ;
- controller Marketplace frontend partagé desktop/mobile ;
- desktop refondu Quick Order / SKU-first ;
- `Plus → Marketplace` ;
- deep-link `?tab=marketplace` ;
- DENTISTE / ADMIN uniquement ; SECRETAIRE exclu ; menu fail-closed ;
- recherche nom / SKU, filtres, quantité, panier, checkout DRAFT ;
- préremplissage nom / cabinet / email ;
- preview locale déterministe sans GET/POST Marketplace ;
- autorité backend conservée pour prix, fournisseurs, split et création DRAFT ;
- aucun backend métier Marketplace modifié.

Preuves :
- PR `#362` merged
- merge exact `6eb93c75f91402031ecc2c8fc1f8858372a97b9b`
- BEFORE run `34045330209` ✅
- BEFORE artifact `9992935589`
- MOB-5G certification / tests ciblés ✅
- targeted Vitest : **18/18** ✅
- backend Marketplace P1-P10 : **105/105 passed** ✅
- build production ✅
- AFTER artifact `9994164037`
- AFTER digest `sha256:1f6b5426be0514ce398edc37e4671c44d86e168593cc5b2ab2d6899ec269481f`
- CI post-merge `34054519282` ✅ SUCCESS
- 390×844 / 430×932 / 768×1024 / 1280×800
- 5 boutons canoniques, nav 76 px, 0 overflow, 0 erreur runtime ✅
- desktop : exactement 1 POST DRAFT, URL inchangée ✅
- score visuel **9.4/10**
- preuve `docs/ux/DIGITAL_CROWN_MOBILE_MARKETPLACE_MOB5G_PROOF.md`

Limite connue non résolue : le job Marketplace signale le conflit de dépendances `httpx==0.27.2` avec `firebase-admin 7.5.0` / `ultralytics-platform`; les tests restent verts. Ne pas déclarer ce conflit corrigé.

## MOB-5H — SuperAdmin mobile — DONE / MERGED
Goal : parité fonctionnelle complète des prérogatives SuperAdmin actives sur mobile, sans affaiblir la sécurité backend.

Fonctions certifiées:
- cinq domaines: Vue globale / Clients / Essais / Marketplace / Opérations;
- clients: validate, plan, extension/revoke licence, archive, suspend, notes, historique, relance;
- trial codes: liste, création, revoke;
- Marketplace global: overview, commandes, incidents, gouvernance, audit, fournisseurs, produits, sync;
- opérations: commandes, dispatch, procurement, facture, réconciliation, synthèse, réceptions;
- P10 mobile ordinaire refusé; WebAuthn UV court pour le control-plane qui l'exige;
- actions tenant-scoped conservent leur contrat backend sans WebAuthn artificiel.

Preuves:
- PR `#363` merged
- baseline BEFORE `6eb93c75f91402031ecc2c8fc1f8858372a97b9b`
- BEFORE artifact `9997848118`
- HEAD final pré-merge `904c6cd001ff87ab54ec6ad31f7a90e52b3ac23d`
- Mobile SuperAdmin MOB-5H Cert `34139811533` ✅
- CI PR `34139811583` ✅
- Marketplace Final Certification `34139811585` ✅
- T2 `34139811647` ✅
- AFTER artifact `10025509035`
- AFTER digest `sha256:465cf28d3f96138ce9ce3b5281d8718c460c5f1b16e595cf1d366ee0cff9e95b`
- 390×844 / 430×932 / 768×1024
- 0 overflow, 0 page error, 0 console error, 0 requête API inattendue, 0 egress externe réel ✅
- score visuel **9.3/10**
- merge exact `e30b858f58686f5f7bef19ca93f1c5dae42929c9`
- CI post-merge master `34142208046` ✅ SUCCESS
- audit `docs/ux/DIGITAL_CROWN_MOBILE_SUPERADMIN_MOB5H_AUDIT.md`
- preuve `docs/ux/DIGITAL_CROWN_MOBILE_SUPERADMIN_MOB5H_PROOF.md`

## MOB-5I — Salle d’attente — COMING SOON
Goal actuel : conserver une place produit cohérente desktop/mobile sans fausse fonctionnalité.

### Séquence restante verrouillée
Quick Document Studio → Salle d’attente.

### Explicitement hors MOB-5 mobile
- Science Hub.
- Éditeur WYSIWYG complet de documents.
- Création/paramétrage lourd des templates.
- Paramétrage stock avancé.

Clarification SuperAdmin: aucune prérogative SuperAdmin active n'est hors scope mobile. Les surfaces Marketplace globales nécessaires à cette parité font partie de MOB-5H.

---

## MOB-6 — Canonisation du routage mobile — PLANNED
Goal : supprimer l’ambiguïté entre PWA mobile dédiée et shell desktop responsive après couverture des parcours essentiels.

## MOB-7 — Certification globale Mobile Product — PLANNED
Preuves minimales : frontend/backend ciblés, build, runtime, RBAC, offline/sync/revocation, context bridges, BEFORE/AFTER 390/430/768, zéro overflow, zéro erreur console/page, comparaison Goal UI, score visuel et gates physiques séparés.

## MOB-8 — Closeout — PLANNED
Ordre : validation → canonique → cohérence docs → roadmap/% réel → Git/PR/merge → post-merge → lot suivant ou CLOSED.

## Garde-fous permanents
- ne jamais porter une page sans scénario mobile démontré ;
- ne pas casser les context bridges existants ;
- ne pas casser l’offline ;
- ne pas affaiblir sécurité / biométrie ;
- ne pas exposer de données sans permission ;
- ne pas mélanger mockup et preuve AFTER ;
- ne jamais annoncer une certification physique depuis une CI navigateur ;
- ne pas déployer sur Vercel sans autorisation explicite.

## Next exact
Certifier le BEFORE MOB-5F sur 390/430/768, puis implémenter le Quick Document Studio mobile sur le moteur `/documents/generate`, avec permissions documentaires backend inchangées, BEFORE/AFTER et tests ciblés avant PR/merge.
