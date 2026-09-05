# Digital Crown — Mobile Product — Canonical Roadmap

Status: ACTIVE
Canonical file: `docs/ux/DIGITAL_CROWN_MOBILE_PRODUCT_CANONICAL.md`
Repo: `hraaaaf/Digital_crown`
Current branch: `audit/mobile-secondary-value-mob5`
Current MOB-5 baseline: `1e5c8d2b5ed1fd68591abdb185645ab2c7758fce`
Current master baseline after MOB-4 closeout: `df48ef3cf1af8e9075828b3bf0b9b1f2c874fcda`
MOB-2 PR: `#354` — MERGED
MOB-3 PR: `#355` — MERGED
MOB-4 PR: `#356` — MERGED
MOB-5 PR: `#357` — ACTIVE
Deployment: none. No Vercel deployment is authorized by this chantier.

## Goal final

Faire de Digital Crown mobile un **cockpit opérationnel clinique**, et non une copie réduite du desktop.

Le mobile doit permettre les actions utiles au fauteuil, debout, entre deux patients ou hors du poste principal, idéalement en moins de 30 secondes.

Le desktop reste le système complet pour les workflows lourds, la production clinique détaillée, l'administration et le paramétrage.

## Doctrine verrouillée

### Mobile = cockpit opérationnel
Prioriser : agenda rapide, patient rapide, alertes médicales, appel / WhatsApp, prochain RDV, encaissement rapide, photo clinique, scan, signature, partage, notifications, assistant, sécurité / biométrie.

### Desktop = système complet
Conserver principalement sur desktop : Analytics complet, comptabilité/Treasury, ClinicalHub/odontogramme/Master Plan, RVG Studio, Panoramic Studio complet, Céphalométrie, Document Studio complet, paramètres cabinet, catalogue actes, Setup cabinet et workflows lourds d'administration.

### Invariants UI/UX
- Réglages cabinet = source de vérité unique du thème et de la typographie ;
- aucune couleur de marque ou police locale figée dans les features mobiles ;
- tout changement UI suit BEFORE → Goal UI → mockup/référence → implémentation → AFTER mêmes viewports → comparaison + tests + score visuel ;
- mockup d'un écran existant = composition sur capture réelle, pas reconstruction schématique ;
- ne jamais transformer le mobile en clone du desktop ;
- aucun Vercel sans autorisation explicite.

---

# Roadmap canonique

## MOB-0 — Canonique produit & frontière Desktop/Mobile — DONE
Goal : figer doctrine, périmètre et ordre d'exécution avant changement UI.
Preuve : bootstrap `af8c44af145a30deeb4d04337cc70bb679c21a81`, puis closeout MOB-0.

## MOB-1 — Goal UI + mockup du Patient Cockpit — DONE
Goal : concevoir le Patient Cockpit fidèle au langage Digital Crown et piloté par le thème/typographie du cabinet.
Références :
- `docs/ux/DIGITAL_CROWN_MOBILE_PATIENT_COCKPIT_GOAL_UI.md`
- `docs/ux/assets/MOBILE_PATIENT_COCKPIT_GOAL_V1.svg`
Preuves : mockup cible `b6924f0f57931e0361dc0db45653b63c4de9fb0c`, invariant thème + `font_fr`, validation visuelle humaine reçue le 2026-09-04.

## MOB-2 — Patient Cockpit — DONE / MERGED
Goal : implémenter le parcours patient mobile cible en moins de 30 secondes.
Fonctions certifiées : recherche patient, identité/synthèse, alerte médicale, appel/WhatsApp, prochain RDV, finance selon permissions, photo, scan, dernier document, dernière pano, contextes opaques, offline explicite, thème et `font_fr`, purge fail-closed inter-patient.

### BEFORE
Run `33880152997` ✅ — HEAD `3ecfa47c449d9724d9517003499ec3e3ec4f730d` — artifact `9939517547` — digest `sha256:7a3b97a4e7b1b7fe652d40f9496fca88dcf2a441149437ed00f403334e7c226f` — 390/430/768.

### AFTER
Run `33889545163` ✅ — candidat `2a01e58d4bf3e3deff833723a52e3449bb26e4ac` — artifact `9943369750` — digest `sha256:b4d274590a3349cbcab8a71faeb25e880acc3aee4ab818420fab8918813777fd` — 390/430/768.

Preuve : `docs/ux/DIGITAL_CROWN_MOBILE_PATIENT_COCKPIT_MOB2_PROOF.md`.
Score visuel : **9.2 / 10**.
Git : PR `#354` merged ; merge commit `5fd2a06663e941581ad422267d31a5bb69a13d11` ; closeout master `508a2e1e174887fe44f271cc6a8283eb89e443c7` ; aucun déploiement.

## MOB-3 — Quick Action Hub — DONE / MERGED
Goal : permettre les actions fréquentes sans chercher une page, en 2 gestes maximum.

### BEFORE
Run `33906860335` ✅ — artifact `9949854305` — digest `sha256:b24cf6ecf919a97be154cfeb45275b54cc3bd2f2f4273fb1ee0f3fa2dee10748` — 390/430/768.

### AFTER
Run `33927174832` ✅ — candidat `37a9413fd8675717da31b77f43c5f9f2ab76de0c` — artifact `9957298023` — digest `sha256:eb96f1193345a3d1770b013eb7451e9d87ca7e95afa062612d08b3078640e8a8` — 390/430/768.

Preuve : `docs/ux/DIGITAL_CROWN_MOBILE_QUICK_ACTION_HUB_MOB3_PROOF.md`.
Score visuel runtime : **9.5 / 10**.
Git : PR `#355` merged ; merge commit `23e4828729e085a4566cbfdf430025d1019e53fa` ; aucun déploiement.

## MOB-4 — Navigation mobile canonique — DONE / MERGED
Goal : simplifier la navigation globale autour des usages réels avec maximum cinq entrées permanentes.
Cible certifiée : `Aujourd’hui / Patients / + / Assistant / Plus`.

### BEFORE
Run `33945615036` ✅
- HEAD `6e1c5ffe3314b7621ae22202091e978025f18a23`
- artifact `9963244367`
- digest `sha256:6c2416c3454270a0dcfe863c1b834fbea75d658437cc060c46741d8013cfb35d`
- viewports `390×844`, `430×932`, `768×1024`
- nav observée : `Agenda / Finance / Envois Labo / Assistant / Sécurité`.

### AFTER
Run `33953721202` ✅
- candidat runtime exact : `4c04d09bf8102b80fcab25e88d58db5d30e0358f`
- artifact : `9965680255`
- digest : `sha256:99ae384612cdffffbb7226ee088f516d564e854900db1b91ceef47bd06afd9b2`
- viewports : `390×844`, `430×932`, `768×1024`
- tests/build/Chromium ✅
- 5 boutons permanents ✅
- aucun overflow horizontal ✅
- aucune erreur runtime ✅
- ancien FAB Agenda neutralisé ✅
- deep links historiques préservés ✅
- score visuel : **9.6 / 10**.

Preuve : `docs/ux/DIGITAL_CROWN_MOBILE_CANONICAL_NAVIGATION_MOB4_PROOF.md`.
Git : PR `#356` merged ; merge commit `28cf8278a31507d96b33c10f03e1635f86223454` ; closeout master `df48ef3cf1af8e9075828b3bf0b9b1f2c874fcda` ; aucun déploiement.

---

## MOB-5 — Mobile secondaire à forte valeur — ACTIVE / SCOPE LOCKED

### Goal
Porter uniquement les scénarios secondaires à forte valeur sur mobile, avec UX dédiée, DB/permissions partagées et sans dupliquer les workflows lourds du desktop.

### Success
Chaque sous-lot retenu possède : scénario mobile explicite, Goal UI, preuve BEFORE/AFTER 390/430/768 si visuel, tests ciblés, build, runtime sans erreur, permissions/RBAC vérifiés et cohérence desktop/mobile sur la même donnée métier.

### Scope produit verrouillé le 2026-09-05

| # | Fonction | Décision | Cible mobile |
|---|---|---|---|
| 1 | Salle d’attente | Desktop + Mobile | **Coming Soon** sur les deux surfaces pour le moment ; ne pas implémenter le métier avant audit dédié |
| 2 | Équipe / praticiens | Desktop + Mobile | vue praticiens, disponibilité/charge et RDV du jour ; accès via `Plus` |
| 3 | Bibliothèque clinique | Desktop + Mobile | recherche/consultation rapide ; lecture simplifiée, pas le gros écran desktop compressé |
| 4 | Science Hub | **Desktop only** | aucun portage mobile prévu |
| 5 | Frontdesk / demandes RDV | Desktop + Mobile | voir, accepter/refuser, appeler/WhatsApp, suivi rapide ; administration lourde desktop |
| 6 | Marketplace / Approvisionnement | Desktop + Mobile | **refonte dédiée** après benchmark de 3–4 références mobiles dentaires/médicales/B2B ; UX mobile distincte |
| 7 | Stock | Desktop + Mobile | niveau de stock, alertes, produits critiques, réassort/mouvements simples ; paramétrage lourd desktop |
| 8 | Notifications | Desktop + Mobile | alertes actionnables, priorité/filtrage strict, deep link vers contexte |
| 9 | SuperAdmin | Desktop + Mobile | supervision/urgence seulement ; opérations lourdes et configuration complète desktop |
| 10 | Patients / génération de documents | Desktop + Mobile | **Quick Document Studio** mobile : ordonnance, certificat, devis, consentement, consignes postop, courrier/orientation, modèle libre simplifié |

### Invariant données desktop/mobile
Une seule source de vérité serveur/DB. Mobile et desktop consomment le même objet métier et le même historique. Aucun modèle parallèle de données.

Pour les documents : `patient_id + practitioner_id + template_id + payload structuré + version + status + created_at + updated_at` comme contrat cible à auditer avant migration. Brouillon local éventuel autorisé uniquement avec queue de sync, versioning et conflit explicite ; aucun écrasement silencieux.

Le pont documentaire existant doit être conservé comme mécanisme de continuité sécurisé tant que le Quick Document Studio n’est pas certifié.

### Ordre d’exécution MOB-5

#### MOB-5A — Équipe / praticiens — CERTIFIED / MERGE PENDING
Goal : rendre l’aperçu praticiens réellement accessible depuis la navigation mobile canonique et conforme aux tokens/thème.
Success observé : `Plus → Équipe`, permission métier `agenda` conservée, nav canonique intacte, 390/430/768 sans overflow, runtime/build/tests verts.

Certification :
- branch HEAD : `51f694f5066e1f6c8208e07286205e421cc226f9`
- visual run `33963384867` ✅
- artifact `9968666702`
- digest `sha256:6a463707a1c7dbe2bb9623db1e3b19b631d267294ad08dc6bb32dcb729929385`
- CI `33963384865` ✅
- T2 runtime `33963384839` ✅
- Settings Security `33963384838` ✅
- viewports `390×844`, `430×932`, `768×1024`
- 5 boutons nav, 76 px, aucun overflow, aucune erreur runtime ✅
- score visuel : **9.2 / 10**.

Preuve : `docs/ux/DIGITAL_CROWN_MOBILE_TEAM_MOB5A_PROOF.md`.

#### MOB-5B — Frontdesk / demandes RDV — NEXT
Goal : traiter une demande RDV en quelques gestes depuis mobile.
Success : voir → demander confirmation / confirmer / refuser → contact rapide → état partagé avec desktop, permissions `agenda` et tenant isolation vérifiés.
Audit : `docs/ux/DIGITAL_CROWN_MOBILE_FRONTDESK_MOB5B_AUDIT.md`.
État vérifié : backend existant réutilisable (`/frontdesk/appointment-request`, `/appointments/pending`, confirm/request-confirmation/reject) avec `employer_id`, permission `agenda` et audit log. L’UX mobile reste à concevoir puis implémenter.

#### MOB-5C — Notifications
Goal : centraliser les alertes actionnables mobile sans bruit.
Success : catégories/priorités/RBAC/deep links testés ; aucune notification non autorisée.

#### MOB-5D — Stock
Goal : consulter criticité stock et lancer une action courte de réassort/mouvement.
Success : données cohérentes desktop/mobile, permissions et actions simples certifiées.

#### MOB-5E — Bibliothèque clinique
Goal : recherche et consultation clinique rapide sur mobile.
Success : recherche, favoris/récents si disponibles, lecture mobile dédiée, aucun portage brut de `EliteLibrary`.

#### MOB-5F — Patients / Quick Document Studio
Goal : produire un document courant en idéalement <30 s depuis le dossier patient.
Success : modèles préremplis, ordonnance simplifiée, aperçu, finalisation, historique commun desktop/mobile, PDF partagé, versioning/audit/RBAC vérifiés.
Références produit à approfondir : CareStack, Dentrix et autres systèmes dentaires de référence avant Goal UI final.

#### MOB-5G — Marketplace / Approvisionnement — REFONTE
Goal : refondre l’expérience Marketplace desktop/mobile à partir d’un benchmark externe sérieux.
Gate obligatoire : audit de 3–4 marketplaces mobiles dentaires/médicales/B2B avant mockup et code.
Success : architecture IA, recherche, catégories, produit, panier/commande, suivi et réassort adaptés à chaque surface ; même métier, UX distinctes.

#### MOB-5H — SuperAdmin mobile
Goal : supervision et urgence, pas administration complète.
Success : états/incidents/utilisateurs visibles selon permissions ; actions critiques explicitement sécurisées.

#### MOB-5I — Salle d’attente — COMING SOON
Goal : conserver une place produit sur desktop et mobile sans fausse fonctionnalité.
Success actuel : surfaces cohérentes marquées Coming Soon ; aucun backend/UI métier partiel présenté comme prêt.

### Explicitement hors MOB-5 mobile
- Science Hub : desktop only.
- Éditeur WYSIWYG complet de documents.
- Création/paramétrage lourd des templates.
- Administration Marketplace exhaustive.
- Paramétrage stock avancé.
- Configuration SuperAdmin complète.

---

## MOB-6 — Canonisation du routage mobile — PLANNED
Goal : supprimer l'ambiguïté entre PWA mobile dédiée et shell desktop responsive après couverture des parcours essentiels.
À auditer : routes desktop directes, redirects, deep links, contextual bridge, onboarding/appairage, rôles, tablette 768 px, fallback support/recovery.

## MOB-7 — Certification globale Mobile Product — PLANNED
Preuves minimales : frontend/backend ciblés, build, runtime, RBAC, offline/sync/revocation, context bridges, BEFORE/AFTER 390/430/768, zéro overflow, zéro erreur console/page, comparaison Goal UI, score visuel et gates physiques séparés.
Aucun Vercel sans autorisation explicite.

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

Fermer MOB-5A par merge de PR `#357` après vérification du HEAD courant, puis démarrer MOB-5B Frontdesk : BEFORE 390/430/768 → Goal UI/mockup → implémentation mobile dédiée → tests/build/runtime/RBAC → AFTER mêmes viewports → closeout.
