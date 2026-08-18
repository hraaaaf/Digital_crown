# SETTINGS PRODUCT COMPASS — Réglages / Paramètres

Date d'initialisation : 2026-08-19
Repo : `hraaaaf/Digital_crown`
Baseline de départ : `master@4f4a4e34e94e82bebe44b2e1fc81d79b1ad195a1`
Statut : **BOUSSOLE CANONIQUE ACTIVE**

> Ce fichier est la source de reprise prioritaire du chantier Réglages / Paramètres.
> Toute nouvelle fenêtre travaillant sur ce chantier doit le lire avant de poursuivre.
> Il doit être mis à jour après chaque page / gros lot réellement traité.
> `SETTINGS_HARDENING_CLOSEOUT.md` reste la preuve du chantier Hardening précédent ; le présent fichier pilote la revue produit, UX et simplification fonctionnelle.

## 1. Goal du chantier

Passer chaque feature de Réglages au tamis comme un produit réel de cabinet dentaire : utilité métier, UX, robustesse, cohérence, dette, doublons, promesses trompeuses et complexité inutile.

Chaque feature reçoit une décision :
- **GARDER** : bonne idée bien exécutée ;
- **AMÉLIORER** : utile, défauts ciblés ;
- **REFONDRE** : bonne idée mais mauvaise exécution / mauvais modèle mental ;
- **DÉPLACER** : feature utile, mauvais emplacement ;
- **SUPPRIMER** : inutile, legacy ou dette sans valeur produit ;
- **À PROUVER** : impact downstream non encore démontré.

## 2. Doctrine d'exécution

Pour chaque page / lot :
1. lire le code et les dépendances downstream ;
2. si UI touchée : capture BEFORE des viewports concernés ;
3. écrire Goal + critères de succès ;
4. produire mockup/wireframe/référence visuelle avant implémentation ;
5. implémenter le chemin le plus simple ;
6. tester le comportement métier + régression proportionnée ;
7. si UI touchée : captures AFTER sur les mêmes viewports + score ;
8. mettre à jour **ce fichier** avec état, décisions, preuves, commit/PR/CI et Next exact ;
9. ne jamais déclarer une page terminée sans preuve.

Aucun déploiement Vercel sans autorisation explicite de l'utilisateur.

## 3. Règle spéciale — preset Benmoussa

Le preset personnel contenant notamment :
- `Dr. Benmoussa Achraf` ;
- `د. أشرف بنموسى` ;
- les lignes d'expertises personnelles associées ;

**NE DOIT PAS être supprimé pour le compte propriétaire de Digital Crown.**

Décision canonique :
- il peut rester disponible / être proposé par défaut **uniquement lorsque l'utilisateur authentifié est le superadmin propriétaire** ;
- il ne doit jamais apparaître comme valeur ou modèle par défaut pour un cabinet standard ;
- pour tout utilisateur non-superadmin, le bouton équivalent doit générer/réinitialiser l'en-tête depuis les informations réelles de son cabinet ;
- si plusieurs superadmins peuvent exister à l'avenir, ne pas se contenter du rôle : cibler explicitement le compte propriétaire afin d'éviter de distribuer le preset personnel à d'autres comptes.

Statut : **DÉCISION PRODUIT VERROUILLÉE — à implémenter lors du lot Profil.**

## 4. Audit produit initial — verdicts

| Zone | Idée | Exécution | Verdict |
|---|---:|---:|---|
| Sécurité & Backup | 10/10 | 9/10 | GARDER / renforcer |
| Équipe / RBAC | 9.5/10 | 8.5/10 | GARDER |
| Profil Cabinet | 9/10 | 7.5/10 | GARDER / simplifier |
| Design & Ambiance | 9.5/10 | 6.5/10 | REFONDRE ciblé |
| Catalogue Actes | 9.5/10 | 5/10 | REFONDRE UX |
| Horaires & Agenda | 8.5/10 | 6/10 | AMÉLIORER |
| IA & Système | 6/10 | 5/10 | RESTRUCTURER / RENOMMER |
| TemplateBuilder legacy | 8/10 | 2/10 | MIGRER idées utiles puis SUPPRIMER |

Le Hardening a surtout fiabilisé la vérité backend, les permissions et les états d'erreur. Le chantier actuel juge si les réglages méritent d'exister sous cette forme.

## 5. Décisions par page

### R1 — Shell / architecture générale Settings

Constats :
- RBAC et filtrage des onglets : très bons ;
- Truth Gates / états d'erreur : à conserver ;
- navigation latérale : correcte ;
- logique de sauvegarde incohérente entre Profil, Branding, IA, Agenda et Catalogue.

Décision : **GARDER le shell, REFONDRE la doctrine de sauvegarde.**

Cible recommandée : sauvegarde explicite par onglet avec état visible `Modifications non enregistrées`, sauf mutations CRUD naturellement atomiques.

Statut : `AUDITÉ — À EXÉCUTER`.

### R2 — Profil Cabinet

À garder :
- identité structure/cabinet/clinique ;
- praticien FR/AR ;
- adresse, INPE, ICE, IF ;
- clavier arabe ;
- spécialités bilingues ;
- génération automatique de l'en-tête ;
- logo ;
- contacts pied de page.

À améliorer :
- éditeur manuel d'en-tête à garder en mode avancé ;
- vérifier toute promesse de détourage / normalisation / SVG avant affichage marketing ;
- remplacer pour les utilisateurs standards le preset personnel par `Réinitialiser depuis les informations du cabinet`.

Règle Benmoussa : voir section 3.

Statut : `AUDITÉ — À EXÉCUTER`.

### R3 — Design & Ambiance

Forces : presets, studio centralisé, preview, réglages de densité.

Problème majeur : le switch `Apparence app / Documents` ressemble à un scope d'édition, alors qu'il sert surtout de scope d'aperçu sur un même profil partagé.

Décision recommandée : **renommer en `Aperçu : Application | Document`** plutôt que créer deux systèmes de thème séparés, sauf besoin produit démontré.

Statut : `AUDITÉ — À EXÉCUTER`.

### R4 — Modèles documentaires / Document Studio

Constat majeur : les taxonomies des templates proposées par les contrôles et celles utilisées dans l'aperçu React ne sont pas alignées. Le preview visuel simulé peut donc raconter une histoire différente du moteur PDF réel.

À garder :
- sélection de modèles ;
- marges/densité ;
- réglages avancés ;
- D-pad logo/QR ;
- import de papier-en-tête ;
- nettoyage du corps d'un document déjà rempli ;
- **rendu PDF réel**.

Décision structurante : **le moteur PDF réel devient la source de vérité du preview documentaire**. Le faux renderer React doit être simplifié, réduit à une prévisualisation indicative ou supprimé lorsqu'il duplique mal le moteur réel.

Statut : `AUDITÉ — P1`.

### R5 — QR Code documentaire

Garder la feature.

À améliorer : pour chaque type de QR afficher clairement :
- destination ;
- donnée utilisée ;
- aperçu ;
- action de test/scanner.

Statut : `AUDITÉ — P2`.

### R6 — Catalogue Actes

Concept métier : **très fort**. Spécialité → Actes → Pathologies doit rester une nomenclature centrale réutilisable par les autres modules.

Problème UX majeur : création / édition via `window.prompt()`.

Décision : **GARDER l'architecture, REFONDRE le CRUD** avec formulaires/modales dédiés, validation, édition des noms/codes/prix/pathologies, archivage/suppression contrôlée et feedback cohérent.

Statut : `AUDITÉ — P1`.

### R7 — Horaires & Agenda

À garder :
- horaires d'ouverture ;
- journée continue ;
- concept de mode d'agenda si son impact downstream est réel.

À améliorer :
- gestion par jour de semaine ;
- jours fermés ;
- exceptions / congés / horaires ponctuels.

À prouver avant décision :
- impact réel de `agenda_mode` ;
- impact réel de `use_tickets` / file d'attente.

Statut : `AUDITÉ — P2 / DOWNSTREAM À PROUVER`.

### R8 — IA & Système

Constat : le nom ne correspond plus à la page, particulièrement avec la doctrine ZERO-LLM.

Contenu actuel : performance, arrière-plan animé, conseils cliniques, badges patient.

Décisions :
- renommer vers **Performance & Assistance** ou équivalent ;
- garder Mode Performance ;
- déplacer Arrière-plan animé vers Design & Ambiance ou le supprimer s'il n'apporte pas de valeur ;
- auditer les Conseils cliniques downstream et leur fondement scientifique ;
- renommer `Badges de Fiabilité Patient` vers une formulation non-jugementale, par ex. `Indicateurs de suivi administratif`, et rendre le calcul explicable.

Statut : `AUDITÉ — P2`.

### R9 — Sécurité & Backup

Meilleure zone actuelle.

À garder :
- sauvegarde chiffrée vérifiée ;
- appairage mobile local ;
- QR/code temporaire ;
- révocation des sessions ;
- journal d'audit.

À améliorer :
- restauration guidée de backup ;
- humaniser le journal d'audit (`Utilisateur #13 / UPDATE / resource#27` → phrase métier compréhensible).

Statut : `AUDITÉ — GARDER / P2 amélioration`.

### R10 — Mon Équipe

À garder :
- comptes collaborateurs ;
- activation / désactivation ;
- approbation / refus ;
- permissions fines ;
- Truth Gate équipe/quotas.

Points à corriger / prouver :
- le frontend contient encore un message d'erreur `mot de passe au moins 4 caractères` alors que le Hardening a fixé 8..128 ;
- conserver les quotas et upsell uniquement si la licence par nombre de collaborateurs reste une règle produit réelle.

Statut : `AUDITÉ — P1 correction message / P2 produit`.

### R11 — TemplateBuilder legacy

Constat : composant historique non monté par le routeur actuel, avec logique de preview et UX anciennes.

Décision : **ne pas investir dans une refonte autonome**. Extraire les idées réellement utiles, vérifier les dépendances, puis supprimer/quarantainer le legacy lorsque le Document Studio couvre les besoins.

Statut : `AUDITÉ — P3`.

## 6. Roadmap d'exécution canonique

### P1 — incohérences fortes / dette visible

- **P1.1 — Doctrine de sauvegarde Settings** : unifier comportement et feedback.
- **P1.2 — Modèles documentaires** : PDF réel comme source de vérité, taxonomies alignées, preview trompeur éliminé.
- **P1.3 — Catalogue CRUD** : supprimer tous les `prompt()` et exposer un vrai CRUD.
- **P1.4 — Profil / preset propriétaire** : Benmoussa uniquement superadmin propriétaire ; reset dynamique pour les autres.
- **P1.5 — Team password copy** : aligner le message frontend sur la politique 8..128 réelle.
- **P1.6 — Scope Branding** : renommer en scope d'aperçu ou prouver le besoin d'un vrai scope d'édition.

### P2 — valeur métier et simplification

- **P2.1 — Agenda hebdomadaire réel**.
- **P2.2 — Catalogue avancé** : archivage, renommage, codes, réorganisation si utile.
- **P2.3 — IA & Système → Performance & Assistance**.
- **P2.4 — Audit Log humanisé**.
- **P2.5 — Indicateurs patient explicables et non-jugementaux**.
- **P2.6 — QR documentaire explicite/testable**.
- **P2.7 — Restauration guidée backup**.

### P3 — cleanup / consolidation

- **P3.1 — TemplateBuilder legacy** : extraction utile puis suppression/quarantaine.
- **P3.2 — suppressions de toggles/features uniquement après preuve d'absence de valeur downstream**.

## 7. Ordre recommandé

Ordre actuel recommandé :
1. Profil Cabinet ;
2. Design & Ambiance + Documents ;
3. Catalogue Actes ;
4. Agenda ;
5. Performance & Assistance ;
6. Sécurité & Backup ;
7. Mon Équipe ;
8. cleanup legacy.

Raison : Profil + Documents portent la plus forte dette de cohérence visible et structurent les choix des pages suivantes.

## 8. Protocole de handover obligatoire

À la fin de **chaque page / gros lot**, mettre à jour ce bloc :

### HANDOVER COURANT

- Chantier : Réglages / Paramètres — Product Review & Simplification
- Lot actif : **aucune implémentation démarrée dans ce fichier initial**
- Goal courant : transformer l'audit produit en exécution page par page avec preuves
- Repo : `hraaaaf/Digital_crown`
- Branche : `docs/settings-product-compass-v2` lors de la création initiale de cette boussole
- Baseline de départ : `4f4a4e34e94e82bebe44b2e1fc81d79b1ad195a1`
- Dernière décision verrouillée : preset Benmoussa uniquement superadmin propriétaire
- Dernière preuve : audit code Settings + `SETTINGS_HARDENING_CLOSEOUT.md`
- Blocage réel : aucun pour la documentation ; impacts downstream Agenda/Tickets/Tips/Badges à prouver avant suppression
- Next exact : commencer **R2 / Profil Cabinet** avec baseline visuelle, goal écrit et mockup avant toute modification UI
- Vercel : **interdit sans autorisation explicite**

## 9. Journal de progression

### 2026-08-19 — Initialisation

- audit produit initial consolidé ;
- roadmap P1/P2/P3 créée ;
- règle Benmoussa corrigée : **ne pas supprimer pour le propriétaire, restreindre au superadmin propriétaire** ;
- protocole de mise à jour après chaque page ajouté ;
- aucune modification fonctionnelle ni UI effectuée ;
- aucun déploiement effectué.
