# Digital Crown — Mobile Product — Canonical Roadmap

Status: ACTIVE
Canonical file: `docs/ux/DIGITAL_CROWN_MOBILE_PRODUCT_CANONICAL.md`
Repo: `hraaaaf/Digital_crown`
Current master baseline: `21a41852182c7e74cc66c335c8d67c93a94d5871` (MOB-5B merge)
Deployment: none. No Vercel deployment is authorized by this chantier.

## Goal final

Faire de Digital Crown mobile un **cockpit opérationnel clinique**, et non une copie réduite du desktop. Les actions mobiles doivent viser les usages au fauteuil, entre deux patients ou hors du poste principal, idéalement en moins de 30 secondes. Le desktop reste le système complet pour les workflows lourds, la production clinique détaillée, l'administration et le paramétrage.

## Doctrine verrouillée

### Mobile = cockpit opérationnel
Prioriser : agenda rapide, patient rapide, alertes, appel / WhatsApp, prochain RDV, encaissement rapide, photo clinique, scan, signature, partage, notifications, assistant, sécurité / biométrie.

### Desktop = système complet
Conserver principalement sur desktop : Analytics complet, comptabilité/Treasury, ClinicalHub/odontogramme/Master Plan, RVG Studio, Panoramic Studio complet, Céphalométrie, Document Studio complet, paramètres cabinet, catalogue actes, Setup cabinet et workflows lourds d'administration.

### Invariants UI/UX
- Réglages cabinet = source de vérité du thème et de la typographie.
- Aucune couleur de marque ou police locale figée dans les features mobiles.
- Tout changement UI suit BEFORE → Goal UI → mockup/référence → implémentation → AFTER mêmes viewports → comparaison + tests + score visuel.
- Mockup d'un écran existant = composition sur capture réelle, pas reconstruction schématique.
- Ne jamais transformer le mobile en clone du desktop.
- Aucun Vercel sans autorisation explicite.

---

# Lots certifiés

## MOB-0 — Canonique produit & frontière Desktop/Mobile — DONE
Preuve bootstrap : `af8c44af145a30deeb4d04337cc70bb679c21a81`.

## MOB-1 — Goal UI Patient Cockpit — DONE
Références :
- `docs/ux/DIGITAL_CROWN_MOBILE_PATIENT_COCKPIT_GOAL_UI.md`
- `docs/ux/assets/MOBILE_PATIENT_COCKPIT_GOAL_V1.svg`

## MOB-2 — Patient Cockpit — DONE / MERGED
- PR `#354`
- merge `5fd2a06663e941581ad422267d31a5bb69a13d11`
- closeout master `508a2e1e174887fe44f271cc6a8283eb89e443c7`
- AFTER run `33889545163` ✅
- artifact `9943369750`
- digest `sha256:b4d274590a3349cbcab8a71faeb25e880acc3aee4ab818420fab8918813777fd`
- viewports 390/430/768
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
Cible certifiée : `Aujourd’hui / Patients / + / Assistant / Plus`.
- PR `#356`
- merge `28cf8278a31507d96b33c10f03e1635f86223454`
- closeout master `df48ef3cf1af8e9075828b3bf0b9b1f2c874fcda`
- AFTER run `33953721202` ✅
- artifact `9965680255`
- digest `sha256:99ae384612cdffffbb7226ee088f516d564e854900db1b91ceef47bd06afd9b2`
- 5 boutons permanents, aucun overflow, aucune erreur runtime ✅
- score visuel **9.6/10**
- preuve `docs/ux/DIGITAL_CROWN_MOBILE_CANONICAL_NAVIGATION_MOB4_PROOF.md`

---

# MOB-5 — Mobile secondaire à forte valeur — ACTIVE / SCOPE LOCKED

## Goal
Porter uniquement les scénarios secondaires à forte valeur sur mobile, avec UX dédiée, DB/permissions partagées et sans dupliquer les workflows lourds du desktop.

## Success
Chaque sous-lot retenu possède : scénario mobile explicite, Goal UI, preuve BEFORE/AFTER 390/430/768 si visuel, tests ciblés, build, runtime sans erreur, permissions/RBAC vérifiés et cohérence desktop/mobile sur la même donnée métier.

## Scope produit verrouillé le 2026-09-05

| # | Fonction | Décision | Cible mobile |
|---|---|---|---|
| 1 | Salle d’attente | Desktop + Mobile | **Coming Soon** sur les deux surfaces ; ne pas implémenter le métier avant audit dédié |
| 2 | Équipe / praticiens | Desktop + Mobile | vue praticiens, disponibilité/charge, RDV du jour ; `Plus → Équipe` |
| 3 | Bibliothèque clinique | Desktop + Mobile | recherche/consultation rapide ; lecture simplifiée |
| 4 | Science Hub | **Desktop only** | aucun portage mobile prévu |
| 5 | Frontdesk / demandes RDV | Desktop + Mobile | voir, accepter/refuser, appeler/WhatsApp, suivi rapide |
| 6 | Marketplace / Approvisionnement | Desktop + Mobile | **refonte dédiée** après benchmark de 3–4 références mobiles dentaires/médicales/B2B |
| 7 | Stock | Desktop + Mobile | niveaux, alertes, criticité, réassort/mouvements simples |
| 8 | Notifications | Desktop + Mobile | alertes actionnables, priorité/filtrage strict, deep links |
| 9 | SuperAdmin | Desktop + Mobile | supervision/urgence seulement ; configuration complète desktop |
| 10 | Patients / génération de documents | Desktop + Mobile | **Quick Document Studio** : ordonnance, certificat, devis, consentement, consignes postop, courrier/orientation, modèle libre simplifié |

## Invariant données desktop/mobile
Une seule source de vérité serveur/DB. Mobile et desktop consomment le même objet métier et le même historique. Aucun modèle parallèle de données.

Pour les documents, contrat cible à auditer avant migration : `patient_id + practitioner_id + template_id + payload structuré + version + status + created_at + updated_at`. Brouillon local éventuel uniquement avec queue de sync, versioning et conflit explicite ; aucun écrasement silencieux.

---

## MOB-5A — Équipe / praticiens — DONE / MERGED
Goal : rendre l’aperçu praticiens accessible depuis la navigation mobile canonique et conforme au thème.

Preuves :
- PR `#357` merged
- merge `89098066ef0c943c0e084af4b9cd388d3ab0aa5b`
- artifact `9968666702`
- digest `sha256:6a463707a1c7dbe2bb9623db1e3b19b631d267294ad08dc6bb32dcb729929385`
- 390×844 / 430×932 / 768×1024
- 0 overflow, 0 erreur runtime
- score visuel **9.2/10**
- preuve `docs/ux/DIGITAL_CROWN_MOBILE_TEAM_MOB5A_PROOF.md`

## MOB-5B — Frontdesk / demandes RDV — DONE / MERGED
Goal : traiter une demande RDV depuis mobile en quelques gestes avec la même donnée serveur que desktop.

Fonctions certifiées :
- `Plus → Frontdesk`
- deep-link `?tab=frontdesk`
- liste `/appointments/pending`
- demander confirmation / confirmer / refuser
- appel / WhatsApp depuis le téléphone métier
- refus via dialog mobile
- erreurs inline
- aucune fausse affirmation d’envoi WhatsApp serveur
- permission `agenda` et backend tenant-scoped conservés

Preuves :
- PR `#358` merged
- merge `21a41852182c7e74cc66c335c8d67c93a94d5871`
- final head `8cdf653d173966e77ea598dfcac4998c3c779903`
- CI `33968295039` ✅
- T2 `33968295021` ✅
- Settings `33968295003` ✅
- MOB-5B cert `33968295005` ✅
- artifact `9970008232`
- digest `sha256:b831122003e2cd71d949c45926fe0f3da6adfa82453a1b09c0111be2f752fe46`
- 390×844 / 430×932 / 768×1024
- 5 boutons canoniques, nav 76 px, 0 overflow, 0 erreur runtime ✅
- score visuel **9.3/10**
- preuve `docs/ux/DIGITAL_CROWN_MOBILE_FRONTDESK_MOB5B_PROOF.md`

## MOB-5C — Notifications — NEXT / AUDIT STARTED
Goal : centraliser les alertes actionnables desktop/mobile sans bruit et sans fuite de données patient dans les notifications OS.

État déjà vérifié :
- `backend/routers/mobile_push.py` expose configuration, statut, enregistrement et suppression Web Push liés à l’appareil appairé, l’utilisateur et le tenant ;
- permission minimale actuelle : `patients` ;
- abonnement Web Push validé HTTPS et device-bound ;
- `backend/services/mobile_push_service.py` envoie un payload OS générique `{ "kind": "alerts" }`, sans donnée patient, TTL 300 s ;
- filtrage des destinataires sur appareil non révoqué, utilisateur actif/non suspendu/non archivé et tenant correct ;
- `backend/services/mobile_notification_policy.py` exige `accounting`/`payments` pour les alertes financières ;
- les subscriptions obsolètes 404/410 sont purgées.

À auditer avant UI : source persistante des alertes, endpoints list/read/dismiss/snooze, catégories/priorités, frontend/PWA/service worker, click/deep-link, déduplication et fréquence.

Success : catégories/priorités/RBAC/deep links testés ; aucune notification non autorisée ; push OS sans PHI ; même état lu/non-lu desktop/mobile ; bruit maîtrisé.

## MOB-5D — Stock — PLANNED
Goal : consulter criticité stock et lancer une action courte de réassort/mouvement.

## MOB-5E — Bibliothèque clinique — PLANNED
Goal : recherche et consultation clinique rapide sur mobile sans portage brut de `EliteLibrary`.

## MOB-5F — Patients / Quick Document Studio — PLANNED
Goal : produire un document courant en idéalement <30 s depuis le dossier patient.
Gate : audit interne + benchmark externe avant Goal UI final.

## MOB-5G — Marketplace / Approvisionnement — REFONTE PLANNED
Goal : refondre l’expérience Marketplace desktop/mobile à partir d’un benchmark externe sérieux.
Gate obligatoire : audit de 3–4 marketplaces mobiles dentaires/médicales/B2B avant mockup et code.

## MOB-5H — SuperAdmin mobile — PLANNED
Goal : supervision et urgence, pas administration complète.

## MOB-5I — Salle d’attente — COMING SOON
Goal actuel : conserver une place produit cohérente desktop/mobile sans fausse fonctionnalité.

### Explicitement hors MOB-5 mobile
- Science Hub.
- Éditeur WYSIWYG complet de documents.
- Création/paramétrage lourd des templates.
- Administration Marketplace exhaustive.
- Paramétrage stock avancé.
- Configuration SuperAdmin complète.

---

## MOB-6 — Canonisation du routage mobile — PLANNED
Goal : supprimer l'ambiguïté entre PWA mobile dédiée et shell desktop responsive après couverture des parcours essentiels.

## MOB-7 — Certification globale Mobile Product — PLANNED
Preuves minimales : frontend/backend ciblés, build, runtime, RBAC, offline/sync/revocation, context bridges, BEFORE/AFTER 390/430/768, zéro overflow, zéro erreur console/page, comparaison Goal UI, score visuel et gates physiques séparés.

## MOB-8 — Closeout — PLANNED
Ordre : validation → canonique → cohérence docs → roadmap/% réel → Git/PR/merge → post-merge → lot suivant ou CLOSED.

## Garde-fous permanents
- ne jamais porter une page sans scénario mobile démontré ;
- ne pas casser les context bridges existants ;
- ne pas casser l'offline ;
- ne pas affaiblir sécurité / biométrie ;
- ne pas exposer de données sans permission ;
- ne pas mélanger mockup et preuve AFTER ;
- ne jamais annoncer une certification physique depuis une CI navigateur ;
- ne pas déployer sur Vercel sans autorisation explicite.

## Next exact

MOB-5C Notifications : terminer l’audit backend + frontend/PWA → verrouiller architecture et catégories → BEFORE 390/430/768 → Goal UI/mockup → implémentation dédiée desktop/mobile → tests/RBAC/build/runtime → AFTER mêmes viewports → closeout.
