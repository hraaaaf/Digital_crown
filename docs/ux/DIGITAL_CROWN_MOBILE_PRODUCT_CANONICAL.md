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

Preuves :

- mockup cible : `b6924f0f57931e0361dc0db45653b63c4de9fb0c` ;
- invariant thème + `font_fr` verrouillé ;
- validation visuelle humaine explicite reçue le 2026-09-04 avant MOB-2.

---

## MOB-2 — Patient Cockpit — DONE / MERGED

Goal : implémenter le parcours patient mobile cible en moins de 30 secondes.

### Fonctions certifiées

- recherche patient ;
- identité et synthèse ;
- alerte médicale prioritaire ;
- appel / WhatsApp ;
- prochain RDV ;
- situation financière filtrée par permissions ;
- photo clinique ;
- scan document ;
- dernier document ;
- dernière panoramique ;
- ponts contextuels opaques ;
- état online/offline explicite ;
- thème et `font_fr` issus des Réglages cabinet ;
- purge fail-closed entre deux sélections patient.

### BEFORE

Run `33880152997` ✅

- HEAD : `3ecfa47c449d9724d9517003499ec3e3ec4f730d`
- artifact : `9939517547`
- digest : `sha256:7a3b97a4e7b1b7fe652d40f9496fca88dcf2a441149437ed00f403334e7c226f`
- viewports : `390×844`, `430×932`, `768×1024`

### AFTER certifié

Run `33889545163` ✅

- candidat exact : `2a01e58d4bf3e3deff833723a52e3449bb26e4ac`
- artifact : `9943369750`
- digest : `sha256:b4d274590a3349cbcab8a71faeb25e880acc3aee4ab818420fab8918813777fd`
- viewports : `390×844`, `430×932`, `768×1024`

Gates verts : thème/offline/isolation inter-patient, non-régression frontend M4/M6 proportionnée, tenant/finance/device backend, non-régression backend photo/scan, build production frontend, syntaxe backend, runtime Chromium, captures AFTER et dimensions exactes.

Preuve détaillée : `docs/ux/DIGITAL_CROWN_MOBILE_PATIENT_COCKPIT_MOB2_PROOF.md`.

### Sécurité

- read model tenant-scopé / permission-gated / chiffré ;
- finance alignée sur le contrat canonique `accounting` / `payments` ;
- changement de patient purge identité et ressources précédentes avant nouveau fetch ;
- contextes liés tenant + utilisateur + appareil ;
- réponse publique de contexte opaque, sans identifiant patient/ressource ;
- aucune promesse de TTL non enforcée.

### Comparaison visuelle

390 / 430 / 768 : langage visuel cohérent avec Digital Crown, identité forte, alerte médicale immédiate, Appeler / WhatsApp prioritaires, actions cliniques tactiles, tablette 768 maîtrisée, aucun overflow horizontal ni erreur runtime dans la certification.

Écarts connus du mockup MOB-1 :

1. actions cliniques avant le prochain RDV ;
2. recherche remplacée par `Tous les patients` après sélection ;
3. navigation cible reportée à MOB-4 ;
4. `Encaisser` reporté à MOB-3.

**Score visuel MOB-2 : 9.2 / 10.**

### Git / merge

- PR `#354` ;
- checks PR verts : CI, Patient P7, T2 Runtime, Onboarding Settings P2, Settings Security, Portability Runtime ; M6-I correctement `skipped` ;
- PR mergée le 2026-09-04 ;
- merge commit : `5fd2a06663e941581ad422267d31a5bb69a13d11` ;
- closeout master : `508a2e1e174887fe44f271cc6a8283eb89e443c7` ;
- aucun déploiement Vercel.

Conclusion : MOB-2 fermé et intégré à `master` avec preuves.

---

## MOB-3 — Quick Action Hub — IN PROGRESS / VISUAL GATE

Goal : permettre les actions fréquentes sans chercher une page, en 2 gestes maximum, sans préempter la refonte de navigation MOB-4.

Cible produit verrouillée :

- Nouveau RDV ;
- Nouveau patient ;
- Photo clinique ;
- Scanner document ;
- Encaisser rapidement si permission.

### Branche

`ux/mobile-quick-action-hub-mob3`

Créée depuis `master@508a2e1e174887fe44f271cc6a8283eb89e443c7`.

### BEFORE — VERIFIED

Run `33906860335` ✅

- HEAD exact : `040beb21872e63167d149735b24cc6f48554bb8f`
- artifact : `9949854305`
- digest : `sha256:b24cf6ecf919a97be154cfeb45275b54cc3bd2f2f4273fb1ee0f3fa2dee10748`
- viewports : `390×844`, `430×932`, `768×1024`
- surface : dashboard mobile + bottom nav actuelle
- harness déterministe, aucune donnée cabinet.

### Goal UI

`docs/ux/DIGITAL_CROWN_MOBILE_QUICK_ACTION_HUB_GOAL_UI.md`

Statut : `AWAITING VISUAL VALIDATION`.

### Mockup

Référence à valider :

`docs/ux/assets/MOBILE_QUICK_ACTION_HUB_GOAL_V2.svg`

Décisions verrouillées avant validation :

- bottom nav actuelle conservée structurellement dans MOB-3 ;
- déclencheur `+` flottant centré au-dessus de la nav ;
- bottom sheet compacte ;
- grille 2 colonnes pour RDV / patient / photo / scan ;
- Encaisser pleine largeur et uniquement si permission ;
- thème/police pilotés par les Réglages cabinet ;
- aucune fonction desktop lourde ;
- v1 rejetée en interne car la nav y était trop simplifiée ; v2 réalignée sur la géométrie réelle de `MobileBottomNav`.

### Réutilisation fonctionnelle auditée

- Nouveau RDV : flow mobile Agenda existant ;
- Nouveau patient : flow mobile de création patient existant ;
- Photo / Scan : contexte patient sécurisé existant ;
- Encaisser : contrat canonique existant `POST /api/accounting/payments`, avec permission `accounting/payments` et `assert_patient_access` ; aucun nouveau moteur financier.

### Gate

1. BEFORE réel ✅ ;
2. Goal UI ✅ ;
3. mockup 390 px ✅ ;
4. validation visuelle humaine explicite ⏳ ;
5. code produit interdit avant gate 4.

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

Preuves minimales : frontend ciblé, backend ciblé, build, runtime, RBAC, offline/sync/revocation, context bridges, BEFORE/AFTER 390/430/768, zéro overflow horizontal, zéro erreur console/page, comparaison Goal UI, score visuel et gates physiques séparés.

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

Human gate : validation visuelle explicite de `docs/ux/assets/MOBILE_QUICK_ACTION_HUB_GOAL_V2.svg`.

Si validé : implémenter MOB-3 en réutilisant exclusivement les flows existants, puis AFTER 390 / 430 / 768 → comparaison BEFORE/Goal → tests → score visuel → PR/merge/closeout → MOB-4.

Si rejeté : corriger le mockup/Goal UI avant tout code produit.
