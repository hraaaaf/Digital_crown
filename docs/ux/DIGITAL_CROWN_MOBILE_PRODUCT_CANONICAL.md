# Digital Crown — Mobile Product — Canonical Roadmap

Status: ACTIVE
Canonical file: `docs/ux/DIGITAL_CROWN_MOBILE_PRODUCT_CANONICAL.md`
Repo: `hraaaaf/Digital_crown`
Branch: `ux/mobile-product-canonical`
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

Desktop ajoute notamment :

- multi-praticien ;
- import Google Agenda ;
- Frontdesk ;
- demandes RDV en attente ;
- jours fériés / exceptions.

Décision : ne pas copier l'ensemble. Évaluer seulement Frontdesk / demandes et aperçu multi-praticien après le coeur mobile.

### Finance

Mobile actuel : recettes jour/mois, créances, activité 7 jours, débiteurs, WhatsApp, bilan PDF.

Desktop ajoute :

- historique détaillé ;
- Treasury Hub ;
- Visual Insights ;
- impayés avancés ;
- filtres, édition, exports et opérations détaillées.

Décision : conserver la synthèse mobile. Ne pas porter la comptabilité complète.

### Patient

Desktop contient :

- liste complète ;
- recherche / tri / import CSV ;
- ClinicalHub ;
- RVG ;
- Panoramique ;
- Céphalométrie ;
- Document Studio ;
- archives ;
- finances patient.

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

Succès :

- fichier canonique versionné ;
- frontière Mobile / Desktop documentée ;
- lots ordonnés ;
- critères de succès et preuves explicités ;
- aucune implémentation UI engagée avant le mockup du lot suivant.

Preuve : fichier créé sur la branche du chantier par le commit `af8c44af145a30deeb4d04337cc70bb679c21a81`, puis relu depuis GitHub avant closeout MOB-0.

---

## MOB-1 — Goal UI + mockup du Patient Cockpit — PLANNED

Goal : concevoir l'écran mobile principal de recherche et contexte patient, inspiré du langage visuel Digital Crown déjà certifié.

Le mockup doit couvrir au minimum :

- recherche patient immédiate ;
- identité patient ;
- alerte médicale critique visible sans ambiguïté ;
- téléphone / WhatsApp ;
- prochain RDV / prochaine séance ;
- solde ou statut financier synthétique si permission ;
- accès photo clinique ;
- accès scan document ;
- accès encaissement rapide si permission ;
- accès au contexte clinique mobile disponible ;
- navigation retour cohérente avec le shell mobile.

Contraintes UI :

- cohérence avec la PWA existante : surfaces premium, cartes arrondies, hiérarchie forte, tokens Digital Crown ;
- aucune densité de dossier desktop ;
- touch targets adaptés ;
- priorité aux actions à une main ;
- 390 / 430 / 768 px comme viewports de référence minimum ;
- états loading / empty / error / offline prévus dès le mockup.

Process obligatoire :

BEFORE certifié → Goal UI écrit → mockup/référence → validation visuelle → seulement ensuite implémentation.

---

## MOB-2 — Patient Cockpit — PLANNED

Goal : implémenter le parcours patient mobile cible en moins de 30 secondes.

Fonctions cibles :

- recherche patient ;
- fiche synthèse ;
- alertes critiques ;
- contact téléphone / WhatsApp ;
- prochain RDV ;
- contexte financier synthétique selon permissions ;
- pont vers photo / scan / document / panoramique existants ;
- navigation cohérente et retour fiable ;
- comportement online/offline explicite.

Succès :

- parcours principal complet sur rôles autorisés ;
- aucune fuite de données inter-patient ;
- permissions fail-closed ;
- aucune régression M4/M6 existante ;
- tests source + runtime + AFTER visuel.

---

## MOB-3 — Quick Action Hub — PLANNED

Goal : permettre les actions fréquentes sans chercher une page.

Cible produit : bouton d'action central ou mécanisme équivalent donnant accès à :

- Nouveau RDV ;
- Nouveau patient ;
- Photo clinique ;
- Scanner document ;
- Encaisser rapidement, si permission.

La forme finale n'est pas verrouillée avant le mockup.

Succès : chaque action critique est accessible en quelques gestes, sans introduire une deuxième navigation concurrente.

---

## MOB-4 — Navigation mobile canonique — PLANNED

Goal : simplifier la navigation globale autour des usages réels.

Direction actuelle à tester dans le mockup :

- Aujourd'hui ;
- Patients ;
- action centrale ;
- Assistant ;
- Plus.

`Plus` peut regrouper selon rôle : Finance, Labo, Bibliothèque, Sécurité, Marketplace éventuelle, SuperAdmin.

Cette architecture reste une **hypothèse de design** jusqu'à validation par mockup et comparaison avec la navigation actuelle.

Succès :

- maximum cinq points d'entrée permanents ;
- aucun doublon de destination ;
- navigation compréhensible sans apprentissage ;
- rôles filtrés correctement ;
- deep links et contextes existants préservés.

---

## MOB-5 — Mobile secondaire à forte valeur — PLANNED / CONDITIONAL

Ce lot n'est ouvert que si MOB-1 à MOB-4 sont validés.

Candidats :

1. Bibliothèque clinique ;
2. demandes RDV / Frontdesk ;
3. aperçu multi-praticien ;
4. Marketplace utilisateur.

Chaque candidat doit franchir un gate produit :

> Existe-t-il un scénario mobile réel, fréquent et plus efficace sur téléphone que sur desktop ?

Si non : rester desktop-only.

---

## MOB-6 — Canonisation du routage mobile — PLANNED

Goal : supprimer l'ambiguïté entre PWA mobile dédiée et shell desktop responsive.

À traiter seulement après couverture des parcours mobiles essentiels afin de ne pas bloquer prématurément une fonctionnalité utile.

À auditer :

- accès direct aux routes desktop depuis mobile ;
- redirects ;
- deep links ;
- contextual bridge ;
- onboarding / appairage ;
- rôles ;
- fallback desktop/tablette ;
- comportement 768 px ;
- accès support / recovery.

La cible probable est une expérience mobile canonique unique, avec exceptions explicites plutôt qu'un accès accidentel au desktop responsive.

---

## MOB-7 — Certification globale Mobile Product — PLANNED

Goal : certifier le produit mobile final sur une candidate immutable.

Preuves minimales :

- tests frontend ciblés ;
- tests backend ciblés ;
- build gardé ;
- tests runtime ;
- RBAC ;
- offline / sync / revocation ;
- context bridges ;
- BEFORE / AFTER sur 390 / 430 / 768 ;
- absence d'overflow horizontal ;
- absence d'erreur console/page ;
- comparaison Goal UI ;
- score visuel ;
- réutilisation des certifications M6 existantes lorsqu'elles restent valides ;
- gates physiques explicitement séparés des preuves navigateur/CI.

Aucun déploiement Vercel ne fait partie de cette certification sans autorisation explicite.

---

## MOB-8 — Closeout — PLANNED

Ordre obligatoire :

validation → mise à jour du canonique → cohérence docs → roadmap/% réel → Git/PR/merge → vérification post-merge → lot suivant ou CLOSED.

Le chantier ne peut être déclaré CLOSED que si :

- tous les lots retenus sont DONE ou explicitement DROPPED avec justification ;
- preuves finales présentes ;
- canonique mis à jour ;
- branche/PR/merge vérifiés ;
- post-merge vérifié ;
- aucun déploiement non autorisé n'a été effectué.

## Garde-fous permanents

- ne jamais transformer le mobile en clone du desktop ;
- ne jamais porter une page sans scénario mobile démontré ;
- ne pas casser les context bridges existants ;
- ne pas casser l'offline ;
- ne pas affaiblir la sécurité mobile / biométrie ;
- ne pas exposer de données sans permission ;
- ne pas mélanger un mockup et une preuve AFTER ;
- ne jamais annoncer une certification physique depuis une CI navigateur ;
- ne pas déployer sur Vercel sans autorisation explicite.

## Next exact

Créer le **Goal UI + mockup du Patient Cockpit mobile** à partir de la baseline actuelle et des invariants de MOB-1, avant toute implémentation.
