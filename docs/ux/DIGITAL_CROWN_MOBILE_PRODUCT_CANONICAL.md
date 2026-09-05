# Digital Crown — Mobile Product — Canonical Roadmap

Status: ACTIVE
Canonical file: `docs/ux/DIGITAL_CROWN_MOBILE_PRODUCT_CANONICAL.md`
Repo: `hraaaaf/Digital_crown`
Current branch: `master`
Current master: `23e4828729e085a4566cbfdf430025d1019e53fa` after MOB-3 merge
MOB-2 PR: `#354` — MERGED
MOB-3 PR: `#355` — MERGED
Deployment: none. No Vercel deployment is authorized by this chantier.

## Goal final

Faire de Digital Crown mobile un **cockpit opérationnel clinique**, et non une copie réduite du desktop.

Le mobile doit permettre les actions utiles au fauteuil, debout, entre deux patients ou hors du poste principal, idéalement en moins de 30 secondes.

Le desktop reste le système complet pour les workflows lourds, la production clinique détaillée, l'administration et le paramétrage.

## Doctrine verrouillée

### Mobile = cockpit opérationnel

Prioriser : agenda rapide, patient rapide, alertes médicales, appel / WhatsApp, prochain RDV, encaissement rapide, photo clinique, scan, signature, partage, notifications, assistant, sécurité / biométrie.

### Desktop = système complet

Conserver principalement sur desktop : Analytics complet, comptabilité/Treasury, ClinicalHub/odontogramme/Master Plan, RVG Studio, Panoramic Studio complet, Céphalométrie, Document Studio complet, paramètres cabinet, catalogue actes, administration fournisseurs/Marketplace, Setup cabinet et workflows lourds d'administration.

### Invariants UI/UX

- Réglages cabinet = source de vérité unique du thème et de la typographie ;
- aucune couleur de marque ou police locale figée dans les features mobiles ;
- tout changement UI suit BEFORE → Goal UI → mockup/référence → implémentation → AFTER mêmes viewports → comparaison + tests + score visuel ;
- mockup d'un écran existant = composition sur **capture réelle**, pas reconstruction schématique ;
- ne jamais transformer le mobile en clone du desktop ;
- aucun Vercel sans autorisation explicite.

---

# Roadmap canonique

## MOB-0 — Canonique produit & frontière Desktop/Mobile — DONE

Goal : figer doctrine, périmètre et ordre d'exécution avant changement UI.

Preuve : bootstrap `af8c44af145a30deeb4d04337cc70bb679c21a81`, puis closeout MOB-0.

---

## MOB-1 — Goal UI + mockup du Patient Cockpit — DONE

Goal : concevoir le Patient Cockpit fidèle au langage Digital Crown et piloté par le thème/typographie du cabinet.

Références :
- `docs/ux/DIGITAL_CROWN_MOBILE_PATIENT_COCKPIT_GOAL_UI.md`
- `docs/ux/assets/MOBILE_PATIENT_COCKPIT_GOAL_V1.svg`

Preuves : mockup cible `b6924f0f57931e0361dc0db45653b63c4de9fb0c`, invariant thème + `font_fr`, validation visuelle humaine reçue le 2026-09-04.

---

## MOB-2 — Patient Cockpit — DONE / MERGED

Goal : implémenter le parcours patient mobile cible en moins de 30 secondes.

Fonctions certifiées : recherche patient, identité/synthèse, alerte médicale, appel/WhatsApp, prochain RDV, finance selon permissions, photo, scan, dernier document, dernière pano, contextes opaques, offline explicite, thème et `font_fr`, purge fail-closed inter-patient.

### BEFORE
Run `33880152997` ✅ — HEAD `3ecfa47c449d9724d9517003499ec3e3ec4f730d` — artifact `9939517547` — digest `sha256:7a3b97a4e7b1b7fe652d40f9496fca88dcf2a441149437ed00f403334e7c226f` — 390/430/768.

### AFTER
Run `33889545163` ✅ — candidat `2a01e58d4bf3e3deff833723a52e3449bb26e4ac` — artifact `9943369750` — digest `sha256:b4d274590a3349cbcab8a71faeb25e880acc3aee4ab818420fab8918813777fd` — 390/430/768.

Preuve détaillée : `docs/ux/DIGITAL_CROWN_MOBILE_PATIENT_COCKPIT_MOB2_PROOF.md`.

Score visuel : **9.2 / 10**.

Git : PR `#354` merged ; merge commit `5fd2a06663e941581ad422267d31a5bb69a13d11` ; closeout master `508a2e1e174887fe44f271cc6a8283eb89e443c7` ; aucun déploiement.

---

## MOB-3 — Quick Action Hub — DONE / MERGED

Goal : permettre les actions fréquentes sans chercher une page, en **2 gestes maximum**, sans préempter MOB-4.

Cible :
- Nouveau RDV ;
- Nouveau patient ;
- Photo clinique ;
- Scanner document ;
- Encaisser rapidement si permission.

### BEFORE — VERIFIED
Run `33906860335` ✅
- HEAD `040beb21872e63167d149735b24cc6f48554bb8f`
- artifact `9949854305`
- digest `sha256:b24cf6ecf919a97be154cfeb45275b54cc3bd2f2f4273fb1ee0f3fa2dee10748`
- viewports `390×844`, `430×932`, `768×1024`.

### Goal UI + validation

- Goal UI : `docs/ux/DIGITAL_CROWN_MOBILE_QUICK_ACTION_HUB_GOAL_UI.md`
- V3 : **VALIDATED — REAL APP COMPOSITE**
- référence : `docs/ux/assets/MOBILE_QUICK_ACTION_HUB_GOAL_V3_OVERLAY.svg`
- validation humaine : 2026-09-04
- score pré-code : **9.4 / 10**.

### AFTER — VERIFIED

Run `33927174832` ✅ SUCCESS

- candidat runtime exact : `37a9413fd8675717da31b77f43c5f9f2ab76de0c`
- artifact : `9957298023`
- digest : `sha256:eb96f1193345a3d1770b013eb7451e9d87ca7e95afa062612d08b3078640e8a8`
- viewports : `390×844`, `430×932`, `768×1024`
- frontend ciblé : **17/17** ✅
- backend ciblé : **8/8** ✅
- build production ✅
- Chromium evidence ✅
- aucun overflow horizontal ✅
- un seul FAB visible ✅
- bottom nav inchangée ✅
- score visuel runtime : **9.5 / 10**.

Preuve détaillée : `docs/ux/DIGITAL_CROWN_MOBILE_QUICK_ACTION_HUB_MOB3_PROOF.md`.

Git : PR `#355` merged ; merge commit `23e4828729e085a4566cbfdf430025d1019e53fa` ; aucun déploiement.

---

## MOB-4 — Navigation mobile canonique — PLANNED

Goal : simplifier la navigation globale autour des usages réels.

Direction à tester : `Aujourd'hui / Patients / action centrale / Assistant / Plus`.

`Plus` peut regrouper selon rôle : Finance, Labo, Bibliothèque, Sécurité, Marketplace éventuelle, SuperAdmin.

Succès : maximum cinq points d'entrée permanents, aucun doublon, rôles filtrés, deep links et contextes existants préservés.

---

## MOB-5 — Mobile secondaire à forte valeur — PLANNED / CONDITIONAL

Candidats : Bibliothèque clinique, demandes RDV / Frontdesk, aperçu multi-praticien, Marketplace utilisateur.
Gate : scénario mobile réel, fréquent et plus efficace que desktop.

---

## MOB-6 — Canonisation du routage mobile — PLANNED

Goal : supprimer l'ambiguïté entre PWA mobile dédiée et shell desktop responsive après couverture des parcours essentiels.

À auditer : routes desktop directes, redirects, deep links, contextual bridge, onboarding/appairage, rôles, tablette 768 px, fallback support/recovery.

---

## MOB-7 — Certification globale Mobile Product — PLANNED

Preuves minimales : frontend/backend ciblés, build, runtime, RBAC, offline/sync/revocation, context bridges, BEFORE/AFTER 390/430/768, zéro overflow, zéro erreur console/page, comparaison Goal UI, score visuel et gates physiques séparés.

Aucun Vercel sans autorisation explicite.

---

## MOB-8 — Closeout — PLANNED

Ordre : validation → canonique → cohérence docs → roadmap/% réel → Git/PR/merge → post-merge → lot suivant ou CLOSED.

Le chantier est CLOSED uniquement si tous les lots retenus sont DONE ou explicitement DROPPED avec justification et preuves.

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

Créer la branche MOB-4 depuis le master post-closeout → capturer le BEFORE navigation réelle 390/430/768 → écrire le Goal UI → produire le mockup sur capture réelle → validation visuelle humaine avant code produit.
