# Digital Crown — Mobile Product — Canonical Roadmap

Status: ACTIVE
Canonical file: `docs/ux/DIGITAL_CROWN_MOBILE_PRODUCT_CANONICAL.md`
Repo: `hraaaaf/Digital_crown`
Working branch: `ux/mobile-patient-cockpit-mob2`
Canonical origin branch: `ux/mobile-product-canonical`
Base master at chantier creation: `7e0289fa030720c8729d77336305facf466266ea`
Canonical bootstrap commit: `af8c44af145a30deeb4d04337cc70bb679c21a81`
Deployment: none. No Vercel deployment is authorized by this chantier.

## Goal final

Faire de Digital Crown mobile un **cockpit opérationnel clinique**, et non une copie réduite du desktop.

Le mobile doit permettre les actions utiles au fauteuil, debout, entre deux patients ou hors du poste principal, idéalement en moins de 30 secondes.

Le desktop reste le système complet pour les workflows lourds, la production clinique détaillée, l'administration et le paramétrage.

## Succès observable

Le chantier est réussi seulement si :

- l'expérience mobile canonique est clairement distincte du shell desktop responsive ;
- les fonctions essentielles mobile sont accessibles rapidement sans navigation inutile ;
- un praticien peut rechercher un patient et accéder à son contexte critique en moins de 30 secondes ;
- les actions natives du téléphone sont prioritaires : appel, WhatsApp, photo clinique, scan, signature, partage ;
- l'agenda mobile reste pleinement opérationnel pour les usages rapides ;
- les workflows lourds restent volontairement desktop-only ;
- aucun écran n'est porté sur mobile uniquement parce qu'il existe déjà sur desktop ;
- les rôles et permissions restent fail-closed ;
- l'offline, l'appairage, la biométrie et les contextes mobiles existants ne régressent pas ;
- les couleurs et polices du mobile suivent les réglages du cabinet, sans thème mobile parallèle ni valeurs de marque codées en dur ;
- tout changement UI suit obligatoirement BEFORE → Goal UI → mockup/référence → implémentation → AFTER mêmes viewports → comparaison + tests → score visuel ;
- aucune certification n'est déclarée sans preuve ;
- aucun déploiement Vercel n'est effectué sans autorisation explicite.

## Baseline produit

Audit initial sur `master` HEAD `7e0289fa030720c8729d77336305facf466266ea`.

PWA mobile dédiée initiale : Agenda / Finance / Envois Labo / Assistant / Sécurité.

Routes mobiles identifiées :

- `/mobile/onboarding`
- `/mobile/dashboard`
- `/mobile/context`
- `/mobile/dentists`
- `/mobile/superadmin`

Les routes desktop restent encore directement accessibles sur téléphone. Cette coexistence est tolérée jusqu'à MOB-6, mais n'est pas la cible finale.

## Doctrine produit verrouillée

### Mobile = cockpit opérationnel

Prioriser :

- agenda rapide ;
- patient rapide ;
- alertes médicales critiques ;
- appel / WhatsApp ;
- prochaine séance / prochain RDV ;
- encaissement rapide ;
- photo clinique ;
- scan document ;
- signature ;
- partage ;
- notifications ;
- assistant ;
- sécurité / biométrie.

### Desktop = système complet

Conserver principalement sur desktop :

- Analytics complet ;
- comptabilité complète / Treasury Hub / Visual Insights ;
- ClinicalHub / odontogramme / Master Plan ;
- RVG Studio ;
- Panoramic Studio complet ;
- Céphalométrie ;
- Document Studio complet ;
- paramètres cabinet ;
- catalogue actes ;
- administration fournisseurs / Marketplace ;
- Setup cabinet ;
- workflows lourds d'administration.

### Mobile secondaire potentiel

Évaluer seulement après le coeur mobile :

- Bibliothèque clinique ;
- demandes RDV / Frontdesk ;
- aperçu multi-praticien ;
- Marketplace utilisateur.

Gate : il doit exister un scénario mobile réel, fréquent et plus efficace sur téléphone que sur desktop.

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

## MOB-2 — Patient Cockpit — DONE

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

Gates verts sur ce candidat :

- thème / offline / isolation inter-patient ;
- non-régression frontend M4/M6 proportionnée ;
- tenant / finance / device backend ;
- non-régression backend M6 photo/scan ;
- build production frontend ;
- syntaxe backend ;
- runtime Chromium ;
- captures AFTER et dimensions exactes.

Preuve détaillée : `docs/ux/DIGITAL_CROWN_MOBILE_PATIENT_COCKPIT_MOB2_PROOF.md`.

### Sécurité

- read model tenant-scopé / permission-gated / chiffré ;
- finance alignée sur le contrat canonique `accounting` / `payments` ;
- changement de patient purge l'identité et les ressources précédentes avant nouveau fetch ;
- contextes liés au tenant, utilisateur et appareil ;
- réponse publique de contexte opaque, sans identifiant patient/ressource ;
- suppression de la promesse `expires_in=1800` car non directement enforcée par le contrat de contexte résolu.

### Comparaison visuelle

Constats 390 / 430 / 768 :

- langage visuel cohérent avec le shell Digital Crown ;
- hiérarchie identité forte ;
- alerte médicale immédiate ;
- Appeler / WhatsApp prioritaires ;
- actions cliniques lisibles et tactiles ;
- 768 reste un cockpit mobile/tablette, pas un desktop réduit ;
- aucun overflow horizontal ou erreur runtime accepté par la certification.

Écarts connus du mockup MOB-1 :

1. actions cliniques avant le prochain RDV ;
2. recherche remplacée par `Tous les patients` après sélection ;
3. navigation cible reportée à MOB-4 ;
4. `Encaisser` reporté à MOB-3.

**Score visuel MOB-2 : 9.2 / 10.**

Conclusion : Goal MOB-2 atteint et prouvé sur candidat immutable `2a01e58d4bf3e3deff833723a52e3449bb26e4ac`.

---

## MOB-3 — Quick Action Hub — NEXT

Goal : permettre les actions fréquentes sans chercher une page.

Cible produit :

- Nouveau RDV ;
- Nouveau patient ;
- Photo clinique ;
- Scanner document ;
- Encaisser rapidement si permission.

Process obligatoire avant code :

1. BEFORE réel sur 390 / 430 / 768 ;
2. Goal UI écrit ;
3. mockup/référence ;
4. validation visuelle ;
5. implémentation seulement après ce gate.

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

- ne jamais transformer le mobile en clone du desktop ;
- ne jamais porter une page sans scénario mobile démontré ;
- ne jamais figer couleur de marque ou police dans une feature mobile ;
- Réglages cabinet = source de vérité unique du thème et de la typographie ;
- couleurs danger / warning / succès restent sémantiques et doivent conserver le contraste ;
- ne pas casser les context bridges existants ;
- ne pas casser l'offline ;
- ne pas affaiblir sécurité / biométrie ;
- ne pas exposer de données sans permission ;
- ne pas mélanger mockup et preuve AFTER ;
- ne jamais annoncer une certification physique depuis une CI navigateur ;
- ne pas déployer sur Vercel sans autorisation explicite.

## Next exact

Ouvrir la PR MOB-2 vers `master`, vérifier ses checks, merger si verts, vérifier le HEAD post-merge, puis ouvrir MOB-3 par son BEFORE réel + Goal UI + mockup avant toute implémentation.
