# SETTINGS PRODUCT COMPASS — Réglages / Paramètres

Date d'initialisation : 2026-08-19
Repo : `hraaaaf/Digital_crown`
Statut : **BOUSSOLE CANONIQUE ACTIVE**

> Source de reprise prioritaire du chantier Réglages / Paramètres.
> Toute nouvelle fenêtre doit lire ce fichier avant de poursuivre.
> Mise à jour obligatoire après chaque page / gros lot réellement traité.
> `SETTINGS_HARDENING_CLOSEOUT.md` reste la preuve du Hardening précédent.
> Aucun déploiement Vercel sans autorisation explicite.

## 1. Goal du chantier

Juger et améliorer chaque feature de Réglages comme un produit réel de cabinet dentaire : utilité métier, UX, robustesse, cohérence, dette, doublons, promesses trompeuses et complexité inutile.

Décisions possibles : **GARDER / AMÉLIORER / REFONDRE / DÉPLACER / SUPPRIMER / À PROUVER**.

## 2. Doctrine d'exécution

Pour chaque page / lot :
1. lire code + dépendances downstream ;
2. si UI touchée : BEFORE réelle ;
3. écrire Goal + critères de succès ;
4. produire mockup/wireframe/référence visuelle avant implémentation ;
5. implémenter le chemin le plus simple et fiable ;
6. tests proportionnés au risque ;
7. AFTER mêmes viewports + score ;
8. mettre à jour ce fichier avec preuves, PR/commit/CI et Next exact ;
9. ne jamais déclarer CLOSED sans preuve.

## 3. Règle spéciale — preset Benmoussa

Le preset personnel (`Dr. Benmoussa Achraf`, équivalent arabe et expertises associées) :
- reste disponible **uniquement pour le superadmin propriétaire** ;
- ne doit jamais devenir le défaut d'un cabinet standard ;
- pour un non-superadmin : `Réinitialiser depuis le cabinet` utilise ses données réelles ;
- l'identité propriétaire repose sur la vérité backend `SUPERADMIN_EMAIL`, pas seulement sur le rôle `ADMIN`.

Statut : **IMPLÉMENTÉ ET CERTIFIÉ R2**.

## 4. Audit produit initial — verdicts

| Zone | Idée | Exécution initiale | Verdict |
|---|---:|---:|---|
| Sécurité & Backup | 10/10 | 9/10 | GARDER / renforcer |
| Équipe / RBAC | 9.5/10 | 8.5/10 | GARDER |
| Profil Cabinet | 9/10 | 7.5/10 | GARDER / simplifier |
| Design & Ambiance | 9.5/10 | 6.5/10 | REFONDRE ciblé |
| Catalogue Actes | 9.5/10 | 5/10 | REFONDRE UX |
| Horaires & Agenda | 8.5/10 | 6/10 | AMÉLIORER |
| IA & Système | 6/10 | 5/10 | RESTRUCTURER / RENOMMER |
| TemplateBuilder legacy | 8/10 | 2/10 | MIGRER idées utiles puis SUPPRIMER |

Le Hardening précédent a surtout fiabilisé la vérité backend, les permissions et les états d'erreur. Le chantier actuel juge la valeur et la forme produit.

## 5. Décisions par page

### R1 — Shell / architecture générale Settings

- RBAC / filtrage onglets : très bon.
- Truth Gates / erreurs : garder.
- Navigation latérale : correcte.
- Doctrine de sauvegarde encore incohérente entre pages.

Décision : **GARDER le shell, REFONDRE la doctrine de sauvegarde**.
Cible : sauvegarde explicite par onglet + état `Modifications non enregistrées`, hors mutations CRUD atomiques.

Statut : `AUDITÉ — À EXÉCUTER`.

### R2 — Profil Cabinet

Décision finale : **GARDER / SIMPLIFIER — CLOSED**.

Implémenté :
- identité/praticien FR-AR/adresse/INPE/ICE/IF conservés ;
- clavier arabe + spécialités bilingues conservés ;
- génération automatique de l'en-tête conservée ;
- édition manuelle déplacée en avancé repliable ;
- état Automatique/Personnalisé explicite ;
- preset Benmoussa réservé au superadmin propriétaire ;
- non-superadmin : reset depuis son cabinet ;
- faux discours `détourage IA / SVG` supprimé ;
- double sauvegarde Profil supprimée ;
- défaut sticky mobile corrigé.

Preuves :
- PR `#171` MERGED ;
- HEAD produit certifié `99de2c4aee19f389bdbd0eee46cae072747babdb` ;
- merge `397f40b50a52457ad53f4b1cb8a9def85b74f5a8` ;
- R2 Visual #17 SUCCESS ; CI #1117 SUCCESS ; T2 #377 SUCCESS ;
- RBAC #51 / Branding #24 / IA #7 / Team Truth #5 SUCCESS ;
- AFTER 1440/768/390 inspectées.

Score visuel : **9.6/10**.
Statut : `CLOSED — CERTIFIÉ — MERGED`.

### R3 — Design & Ambiance

Décision finale : **GARDER / CLARIFIER LE MODÈLE MENTAL — CLOSED**.

Constat vérifié : `Apparence app | Documents` ne séparait pas deux configurations. Le scope pilotait uniquement `StudioPreview`, tandis que `StudioControls` modifiait le même profil.

Implémenté :
- `Apparence app | Documents` → **`APERÇU — Application | Document`** ;
- microcopie : `Ce sélecteur change uniquement l’aperçu affiché.` ;
- état interne renommé `previewScope` ;
- migration locale `branding_scope` → `branding_preview_scope` ;
- aucune duplication de thème/profil par scope ;
- R4 volontairement non touché.

Preuves :
- BEFORE Branding certifiée : workflow #24, 1440/1024/768/430/390 ;
- Goal + wireframe écrits avant code dans `docs/settings/R3_BRANDING_VISUAL_GOAL.md` ;
- PR `#173` MERGED ;
- HEAD produit certifié `9db4b560af7925233d5584dfb7af870b76e086d2` ;
- merge `985873dc644453b078a2a0efc6a1e006121ee6b0` ;
- Branding Visual #26 SUCCESS ;
- RBAC #53 SUCCESS ;
- T2 #381 SUCCESS ;
- CI #1124 SUCCESS ;
- 10 AFTER inspectées : Application + Document × 1440/1024/768/430/390 ;
- aucun overflow horizontal ni chevauchement observé.

Incident CI : #1124 a duré anormalement longtemps dans la suite backend (~47 min) mais a finalement terminé SUCCESS. Aucune modification backend dans R3.

Score visuel : **9.7/10**.
Statut : `CLOSED — CERTIFIÉ — MERGED`.

### R4 — Modèles documentaires / Document Studio

Constat majeur déjà vérifié côté frontend :
- contrôles : `swiss / royal / clinical / modern / heritage` ;
- aperçu React historique contient des branches `classic / asymetric / future / frame / double-column` ;
- risque de preview simulé différent du moteur PDF réel.

À garder :
- sélection de modèles ;
- marges/densité ;
- réglages avancés ;
- D-pad logo/QR ;
- import papier-en-tête ;
- nettoyage corps d'un document déjà rempli ;
- **rendu PDF réel**.

Décision structurante : **le moteur PDF réel devient la source de vérité du preview documentaire**. Le renderer React ne doit jamais prétendre être fidèle s'il ne partage pas la même taxonomie/logique.

Statut : `ACTIF — P1`.

### R5 — QR Code documentaire

Garder. À améliorer : destination, donnée utilisée, aperçu, action tester/scanner.
Statut : `AUDITÉ — P2`.

### R6 — Catalogue Actes

Architecture Spécialité → Actes → Pathologies : **GARDER**.
CRUD `window.prompt()` : **REFONDRE** avec formulaires/modales, validation, édition et archivage/suppression contrôlée.
Statut : `AUDITÉ — P1`.

### R7 — Horaires & Agenda

Garder horaires/journée continue. Améliorer vers semaine réelle, jours fermés, exceptions/congés.
À prouver avant décision : impact `agenda_mode` et `use_tickets`.
Statut : `AUDITÉ — P2 / DOWNSTREAM À PROUVER`.

### R8 — IA & Système

Renommer vers **Performance & Assistance** ou équivalent. Garder Performance. Déplacer/supprimer arrière-plan animé selon valeur. Auditer Conseils cliniques. Renommer les badges patient vers une formulation explicable et non-jugementale.
Statut : `AUDITÉ — P2`.

### R9 — Sécurité & Backup

Zone forte. Garder backup chiffré, appairage local, révocation, audit log. Améliorer restauration guidée + audit log humanisé.
Statut : `AUDITÉ — GARDER / P2`.

### R10 — Mon Équipe

Garder comptes/activation/approbation/permissions fines/Truth Gate. Corriger message `4 caractères` vs politique réelle 8..128. Quotas/upsell à garder seulement si règle licence réelle.
Statut : `AUDITÉ — P1/P2`.

### R11 — TemplateBuilder legacy

Ne pas refondre isolément. Extraire idées utiles, vérifier dépendances, puis supprimer/quarantainer lorsque Document Studio couvre les besoins.
Statut : `AUDITÉ — P3`.

## 6. Roadmap canonique

### P1 — incohérences fortes / dette visible

- **P1.1** Doctrine de sauvegarde Settings.
- **P1.2** Modèles documentaires : PDF réel source de vérité, taxonomies alignées, preview trompeur éliminé. **ACTIF R4**.
- **P1.3** Catalogue CRUD réel.
- **P1.4** Profil / preset propriétaire. ✅ CLOSED R2.
- **P1.5** Team password copy 8..128.
- **P1.6** Scope Branding. ✅ CLOSED R3.

### P2 — valeur métier / simplification

- **P2.1** Agenda hebdomadaire réel.
- **P2.2** Catalogue avancé.
- **P2.3** IA & Système → Performance & Assistance.
- **P2.4** Audit Log humanisé.
- **P2.5** Indicateurs patient explicables/non-jugementaux.
- **P2.6** QR documentaire explicite/testable.
- **P2.7** Restauration guidée backup.

### P3 — cleanup / consolidation

- **P3.1** TemplateBuilder legacy : extraction utile puis suppression/quarantaine.
- **P3.2** Suppression de toggles/features uniquement après preuve d'absence de valeur downstream.

## 7. Ordre d'exécution

1. ✅ R2 Profil Cabinet ;
2. ✅ R3 Design & Ambiance ;
3. **R4 Modèles documentaires / Document Studio** ;
4. Catalogue Actes ;
5. Agenda ;
6. Performance & Assistance ;
7. Sécurité & Backup ;
8. Mon Équipe ;
9. cleanup legacy.

## 8. HANDOVER COURANT

- Chantier : **Réglages / Paramètres — Product Review & Simplification**
- Lot actif : **R4 — Modèles documentaires / Document Studio**
- Goal courant : rendre le moteur PDF réel source de vérité du preview et éliminer les divergences de taxonomie/renderer sans perdre les réglages utiles
- Repo : `hraaaaf/Digital_crown`
- Branche courante canonique : `master`
- Dernière PR : `#173 MERGED`
- Dernier merge : `985873dc644453b078a2a0efc6a1e006121ee6b0`
- Dernier HEAD produit certifié : `9db4b560af7925233d5584dfb7af870b76e086d2`
- Dernière CI : `#1124 SUCCESS`
- Dernière preuve visuelle : 10 AFTER R3 inspectées, score 9.7/10
- Blocage réel : aucun pour commencer l'audit R4 ; moteur PDF backend exact à cartographier avant toute modification
- Next exact : **R4 cartographie frontend/backend → BEFORE document → Goal visuel → mockup → implémentation**
- Avancement roadmap validé : **2/15 lots = 13.3 %**
- Vercel : **interdit sans autorisation explicite**

## 9. Journal de progression

### 2026-08-19 — R3 Design & Ambiance CLOSED

- BEFORE 5 viewports inspectée ;
- Goal + wireframe écrits avant implémentation ;
- scope clarifié en simple sélecteur d'aperçu ;
- 10 AFTER Application/Document certifiées ;
- Branding/RBAC/T2/CI SUCCESS ;
- score visuel **9.7/10** ;
- PR #173 mergée ;
- aucun déploiement Vercel.

### 2026-08-19 — R2 Profil Cabinet CLOSED

- PR #171 mergée ;
- preset Benmoussa limité au superadmin propriétaire ;
- en-tête avancé/repliable ;
- texte logo réaligné sur le vrai traitement ;
- double sauvegarde et sticky mobile corrigés ;
- score visuel **9.6/10** ;
- aucun déploiement Vercel.

### 2026-08-19 — Initialisation

- audit produit consolidé ;
- roadmap P1/P2/P3 créée ;
- règle Benmoussa verrouillée ;
- protocole de handover canonique créé ;
- aucun déploiement.
