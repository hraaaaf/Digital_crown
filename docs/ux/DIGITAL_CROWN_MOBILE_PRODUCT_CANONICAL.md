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
- tout changement UI suit obligatoirement BEFORE → Goal UI → mockup/référence → implémentation → AFTER mêmes viewports → comparaison + tests + score visuel ;
- aucune certification n'est déclarée sans preuve ;
- aucun déploiement Vercel n'est effectué sans autorisation explicite.

## Baseline vérifiée au lancement

Audit statique effectué sur `master` HEAD `7e0289fa030720c8729d77336305facf466266ea`.

### Architecture actuelle

L'entrée `/` détecte le mobile et redirige vers `/mobile/dashboard`.

La PWA mobile dédiée expose principalement :

1. Agenda ;
2. Finance ;
3. Envois Labo ;
4. Assistant ;
5. Sécurité.

Routes mobiles dédiées identifiées :

- `/mobile/onboarding` ;
- `/mobile/dashboard` ;
- `/mobile/context` ;
- `/mobile/dentists` ;
- `/mobile/superadmin`.

Les routes desktop ne sont actuellement pas bloquées par type d'appareil : un téléphone peut encore ouvrir directement des routes telles que `/analytics`, `/patients`, `/settings` ou `/bibliotheque` et recevoir le shell desktop responsive.

Cette coexistence est tolérée comme baseline mais ne constitue pas la cible produit finale.

### Thème / typographie mobile — dette vérifiée

Les réglages cabinet possèdent déjà une source de vérité pour :

- `selected_theme` ;
- `primary_color` ;
- `secondary_color` ;
- `accent_color` ;
- `font_fr`.

Le système de surfaces mobile consomme déjà largement les tokens CSS du thème (`--primary`, `--secondary`, `--accent`, `--glass-bg`, `--glass-border`, etc.).

L'audit MOB-1 avait confirmé quatre incohérences à corriger avant le nouveau Patient Cockpit :

1. `useSettingsStore.applyTheme()` n'appliquait pas `font_fr` au runtime mobile ;
2. `useMobileDashboard()` réinitialisait `documentElement.dataset.theme` et `body.dataset.theme` à une chaîne vide au montage ;
3. `MobileDashboard.tsx` et certains titres de `MobileHeader.tsx` forçaient `font-outfit` ;
4. le canal mobile ne transportait pas les paramètres de présentation du cabinet.

Décision verrouillée : **Réglages cabinet reste la source de vérité unique. Aucun moteur de thème mobile parallèle.**

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
- Panoramic Studio complet : upload, validation, annotations, rapports, comparaison T0/T1, évolution ;
- Céphalométrie ;
- Document Studio complet ;
- paramètres cabinet ;
- catalogue actes ;
- administration fournisseurs / Marketplace ;
- Setup cabinet ;
- workflows lourds d'administration.

### Mobile secondaire potentiel

À évaluer seulement après le coeur mobile :

- Bibliothèque clinique ;
- demandes RDV / Frontdesk ;
- aperçu multi-praticien ;
- Marketplace utilisateur ;
- fonctions métier réellement utiles en mobilité démontrée.

## Écarts desktop/mobile déjà identifiés

### Agenda

Mobile actuel : jour / semaine / mois, création, déplacement et gestion rapide des RDV.

Desktop ajoute notamment : multi-praticien, import Google Agenda, Frontdesk, demandes RDV en attente, jours fériés / exceptions.

Décision : ne pas copier l'ensemble. Évaluer seulement Frontdesk / demandes et aperçu multi-praticien après le coeur mobile.

### Finance

Mobile actuel : recettes jour/mois, créances, activité 7 jours, débiteurs, WhatsApp, bilan PDF.

Desktop ajoute notamment historique détaillé, Treasury Hub, Visual Insights, impayés avancés, filtres, édition et exports détaillés.

Décision : conserver la synthèse mobile. Ne pas porter la comptabilité complète.

### Patient

Desktop contient liste complète, ClinicalHub, RVG, Panoramique, Céphalométrie, Document Studio, archives et finances détaillées.

Mobile possède déjà des contextes ciblés patient / panoramique / document / rendez-vous, ainsi que photo clinique, scan et partage.

Décision : construire un **Patient Cockpit mobile**, pas reproduire le dossier patient desktop.

### Faux desktop-only à ne pas intégrer au scope

- `Stock` : desktop encore `ComingSoon` ;
- `Salle d'attente` : desktop encore `ComingSoon` ;
- `Labo` : cas inverse, mobile possède déjà une vraie surface alors que la route desktop est encore `ComingSoon`.

---

# Roadmap canonique

## MOB-0 — Canonique produit & frontière Desktop/Mobile — DONE

Goal : figer la doctrine, le périmètre et l'ordre d'exécution avant tout nouveau changement UI.

Preuve : fichier créé par `af8c44af145a30deeb4d04337cc70bb679c21a81`, puis relu et closeout MOB-0 sur la branche.

---

## MOB-1 — Goal UI + mockup du Patient Cockpit — DONE

Goal : concevoir l'écran mobile principal de recherche et contexte patient en restant fidèle au langage visuel Digital Crown existant et **100 % dépendant du thème/typographie du cabinet**.

Fichier Goal UI : `docs/ux/DIGITAL_CROWN_MOBILE_PATIENT_COCKPIT_GOAL_UI.md`.

Mockup 390 px : `docs/ux/assets/MOBILE_PATIENT_COCKPIT_GOAL_V1.svg`.

Preuves :

- premier mockup conceptuel rejeté car trop générique et hors scope ;
- baseline réelle réauditée à partir de `MobileHeader`, `MobileBottomNav`, `FinanceView`, `SecuriteView` et des références M6 ;
- contrat thème / `font_fr` verrouillé ;
- mockup cible versionné par `b6924f0f57931e0361dc0db45653b63c4de9fb0c` ;
- Goal UI thémable mis à jour par `7e17f23bd56bfbc3178eee45fd5113b1ea812b79` ;
- validation visuelle humaine explicite reçue le 2026-09-04 avant ouverture de MOB-2.

---

## MOB-2 — Patient Cockpit — IN PROGRESS

Goal : implémenter le parcours patient mobile cible en moins de 30 secondes.

Ordre interne obligatoire :

1. réparer le contrat thème / typographie mobile sans moteur parallèle ;
2. capturer le BEFORE runtime 390 / 430 / 768 ;
3. implémenter recherche patient + fiche synthèse ;
4. alertes critiques ;
5. contact téléphone / WhatsApp ;
6. prochain RDV ;
7. contexte financier synthétique selon permissions ;
8. pont vers photo / scan / document / panoramique existants ;
9. comportement online/offline explicite ;
10. tests source + runtime + AFTER visuel.

État vérifié au 2026-09-04 :

- BEFORE immutable : run `33880152997` ✅ sur `3ecfa47c449d9724d9517003499ec3e3ec4f730d` ; artifact `9939517547` ; digest `sha256:7a3b97a4e7b1b7fe652d40f9496fca88dcf2a441149437ed00f403334e7c226f` ; viewports 390×844 / 430×932 / 768×1024 ;
- runtime thème cabinet : `3392fd91b3f479241373db81da1172a7a462b40b` ;
- police cabinet appliquée au shell : `223a0174a1a459a4aabd4a0b726d4488436746f9` ;
- header débarrassé du `font-outfit` forcé : `206d333d9c97504661df3563c6531b084498ce72` ;
- paramètres visuels exposés via canal mobile chiffré : `68899556d7f438a7ee981bcf86aca5fbfaf65e92` ;
- contrat de test thème/police : `11de1b01e258531181e49bd11f394a796f8f2964` ;
- reset legacy du thème supprimé : `1d9e4389bbfe7009bd8c8c11d3bb72328e0daaba` ;
- read model Patient Cockpit tenant-scopé / permission-gated / chiffré : `6ba20f1af36b6a8cebb355efac5f8fdff4f01e06` ;
- router Patient Cockpit monté : `92893c7576624877dd1500a2e5c005d56aed380c` ;
- vue recherche + synthèse patient : `37cc3ee958be6746fce6889fc27b851fd4b0b238` ;
- tab `patients` : `22336d3018cfa052378559e59e8a9565a8922540` ;
- accès rapide depuis le header : `bce1bb7d75e62562055ec637371b5c0255452c79` ;
- Patient Cockpit monté dans `MobileDashboard` : `eba175ab222e5d847b1ec87e63c01a4a587bc2af` ;
- workflow de certification thème + build + AFTER ajouté : `121a5df360c350026169d10254226f30db42572a` ; run `33884838745` actuellement queued au dernier contrôle.

Fonctions déjà présentes : recherche patient, identité, alerte médicale, appel, WhatsApp, prochain RDV, synthèse financière filtrée par permission, navigation Agenda/Patients.

Reste connu avant DONE :

- ponts explicites vers photo clinique / scan / document / panoramique existants ;
- comportement online/offline explicite du Patient Cockpit ;
- tests ciblés backend Patient Cockpit + non-régression M4/M6 proportionnée ;
- AFTER 390 / 430 / 768 disponible et comparé au BEFORE + Goal UI ;
- score visuel documenté ;
- aucune erreur source/build/runtime restante.

Succès :

- thème et police des Réglages réellement propagés au mobile ;
- aucune valeur de marque codée en dur dans le Patient Cockpit ;
- parcours principal complet sur rôles autorisés ;
- aucune fuite de données inter-patient ;
- permissions fail-closed ;
- aucune régression M4/M6 existante ;
- AFTER comparé au Goal UI sur mêmes viewports.

---

## MOB-3 — Quick Action Hub — PLANNED

Goal : permettre les actions fréquentes sans chercher une page.

Cible produit : Nouveau RDV, Nouveau patient, Photo clinique, Scanner document, Encaisser rapidement si permission.

La forme finale n'est pas verrouillée avant son propre mockup/validation.

---

## MOB-4 — Navigation mobile canonique — PLANNED

Goal : simplifier la navigation globale autour des usages réels.

Direction à tester : `Aujourd'hui / Patients / action centrale / Assistant / Plus`.

`Plus` peut regrouper selon rôle : Finance, Labo, Bibliothèque, Sécurité, Marketplace éventuelle, SuperAdmin.

Succès : maximum cinq points d'entrée permanents, aucun doublon, rôles filtrés, deep links et contextes existants préservés.

---

## MOB-5 — Mobile secondaire à forte valeur — PLANNED / CONDITIONAL

Candidats : Bibliothèque clinique, demandes RDV / Frontdesk, aperçu multi-praticien, Marketplace utilisateur.

Gate : existe-t-il un scénario mobile réel, fréquent et plus efficace sur téléphone que sur desktop ? Si non, rester desktop-only.

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

Ordre obligatoire : validation → canonique → cohérence docs → roadmap/% réel → Git/PR/merge → vérification post-merge → lot suivant ou CLOSED.

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

Compléter les ponts Patient Cockpit vers photo / scan / document / panoramique et rendre l'état online/offline explicite pendant que la certification `33884838745` s'exécute ; ensuite exploiter l'AFTER 390 / 430 / 768 et comparer au BEFORE + Goal UI.
