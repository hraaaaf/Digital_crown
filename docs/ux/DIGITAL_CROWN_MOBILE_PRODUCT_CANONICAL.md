# Digital Crown — Mobile Product — Canonical Roadmap

Status: ACTIVE
Canonical file: `docs/ux/DIGITAL_CROWN_MOBILE_PRODUCT_CANONICAL.md`
Repo: `hraaaaf/Digital_crown`
Current branch: `ux/mobile-quick-action-hub-mob3`
Current master baseline for MOB-3: `508a2e1e174887fe44f271cc6a8283eb89e443c7`
MOB-2 PR: `#354` — MERGED
MOB-2 merge commit: `5fd2a06663e941581ad422267d31a5bb69a13d11`
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

## MOB-3 — Quick Action Hub — IN PROGRESS / VISUAL GATE

Goal : permettre les actions fréquentes sans chercher une page, en **2 gestes maximum**, sans préempter MOB-4.

Cible :
- Nouveau RDV ;
- Nouveau patient ;
- Photo clinique ;
- Scanner document ;
- Encaisser rapidement si permission.

### Branche
`ux/mobile-quick-action-hub-mob3`, créée depuis `master@508a2e1e174887fe44f271cc6a8283eb89e443c7`.

### BEFORE — VERIFIED
Run `33906860335` ✅
- HEAD `040beb21872e63167d149735b24cc6f48554bb8f`
- artifact `9949854305`
- digest `sha256:b24cf6ecf919a97be154cfeb45275b54cc3bd2f2f4273fb1ee0f3fa2dee10748`
- viewports `390×844`, `430×932`, `768×1024`
- dashboard réel du harness, aucune donnée cabinet.

### Correction UX issue du BEFORE réel

Le BEFORE montre qu'un **FAB `+` existe déjà dans `AgendaView`** : `bottom-32 right-6`, `56×56`, `bg-primary`, et ouvre actuellement `AddApptModal`.

Décision verrouillée :
- **ne pas créer un second `+`** ;
- conserver la position/taille/style exacts du FAB existant ;
- promouvoir ce FAB vers la shell mobile pour le rendre disponible sur les surfaces autorisées ;
- fermé : `+` ouvre le Quick Action Hub ;
- ouvert : le même FAB devient `×` ;
- `Nouveau RDV` réutilise `AddApptModal` ;
- bottom nav inchangée jusqu'à MOB-4.

### Goal UI
`docs/ux/DIGITAL_CROWN_MOBILE_QUICK_ACTION_HUB_GOAL_UI.md`

État : `AWAITING VISUAL VALIDATION`.

### Mockups
- v1 : REJECTED — trop reconstruit ;
- v2 : REJECTED après feedback humain — nav alignée mais dashboard schématique ;
- v3 : **REAL-APP COMPOSITE — AWAITING VISUAL VALIDATION**.

La v3 est construite directement sur `before-390x844.png` de l'artifact `9949854305`. Le vrai logo, header, date, `Bonsoir`, badges, Preview, tabs, progression, timeline, FAB et bottom nav sont conservés. Seuls backdrop + sheet + actions + transformation `+`→`×` sont ajoutés.

### Réutilisation fonctionnelle
- Nouveau RDV : `AddApptModal` existant ;
- Nouveau patient : flow mobile existant ;
- Photo / Scan : contexte patient sécurisé existant ;
- Encaisser : `POST /api/accounting/payments`, permissions `accounting/payments`, `assert_patient_access` ; aucun nouveau moteur financier.

### Gate
1. BEFORE réel ✅
2. Goal UI corrigé ✅
3. mockup v3 basé sur la vraie app ✅
4. validation visuelle humaine explicite ⏳
5. aucun code produit avant gate 4.

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

Human gate : validation visuelle du **mockup v3 construit sur le BEFORE réel 390×844**.

Si validé : implémentation MOB-3 → tests → AFTER 390/430/768 → comparaison BEFORE/Goal → score visuel → PR/merge/closeout → MOB-4.

Si rejeté : corriger uniquement la v3/Goal UI avant tout code produit.
