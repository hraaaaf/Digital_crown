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
1. code + dépendances downstream ;
2. BEFORE réelle si UI ;
3. Goal + critères ;
4. mockup/wireframe avant code ;
5. implémentation minimale et fiable ;
6. tests proportionnés ;
7. AFTER mêmes viewports + score ;
8. mise à jour de cette boussole ;
9. CI/merge/post-merge ;
10. jamais CLOSED sans preuve.

## 3. Règle spéciale — preset Benmoussa

Le preset personnel (`Dr. Benmoussa Achraf`, équivalent arabe et expertises associées) :
- disponible uniquement pour le superadmin propriétaire ;
- jamais défaut d'un cabinet standard ;
- non-superadmin : `Réinitialiser depuis le cabinet` utilise ses données réelles ;
- vérité propriétaire = backend `SUPERADMIN_EMAIL`, pas seulement rôle `ADMIN`.

Statut : **IMPLÉMENTÉ ET CERTIFIÉ R2**.

## 4. Audit produit initial

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

## 5. Décisions par lot

### R1 — Shell / architecture Settings

- RBAC / Truth Gates : garder.
- Navigation : correcte.
- Doctrine de sauvegarde encore incohérente entre pages.

Décision : **GARDER le shell, REFONDRE la doctrine de sauvegarde**.
Statut : `AUDITÉ — À EXÉCUTER`.

### R2 — Profil Cabinet

Décision : **GARDER / SIMPLIFIER — CLOSED**.

Implémenté :
- identité/praticien FR-AR/adresse/identifiants conservés ;
- clavier arabe + spécialités bilingues conservés ;
- génération automatique d'en-tête conservée ;
- édition manuelle avancée/repliable ;
- Automatique/Personnalisé explicite ;
- preset Benmoussa réservé au superadmin propriétaire ;
- faux discours détourage IA/SVG supprimé ;
- double sauvegarde et sticky mobile corrigés.

Preuves : PR #171 MERGED ; HEAD produit `99de2c4aee19f389bdbd0eee46cae072747babdb` ; merge `397f40b50a52457ad53f4b1cb8a9def85b74f5a8` ; R2 Visual #17 SUCCESS ; CI #1117 SUCCESS ; T2 #377 SUCCESS ; AFTER 1440/768/390 inspectées.

Score visuel : **9.6/10**.
Statut : `CLOSED — CERTIFIÉ — MERGED`.

### R3 — Design & Ambiance

Décision : **GARDER / CLARIFIER LE MODÈLE MENTAL — CLOSED**.

Implémenté :
- `Apparence app | Documents` → `APERÇU — Application | Document` ;
- microcopie explicite : le sélecteur change uniquement l'aperçu ;
- `previewScope` + migration locale ;
- aucune duplication de thème/profil.

Preuves : BEFORE 5 viewports ; Goal/wireframe avant code ; PR #173 MERGED ; HEAD produit `9db4b560af7925233d5584dfb7af870b76e086d2` ; merge `985873dc644453b078a2a0efc6a1e006121ee6b0` ; Branding #26 / RBAC #53 / T2 #381 / CI #1124 SUCCESS ; 10 AFTER inspectées.

Score visuel : **9.7/10**.
Statut : `CLOSED — CERTIFIÉ — MERGED`.

### R4 — Réglages / Modèles & rendu des documents

**Périmètre verrouillé : Réglages uniquement. Le Document Studio clinique est hors scope.**

Constat vérifié :
- Réglages expose `swiss / royal / clinical / modern / heritage` ;
- vrai moteur PDF implémente ces mêmes 5 modèles ;
- ancien preview React de Réglages utilisait encore `classic / asymetric / future / frame / double-column` ;
- ancien preview réel se régénérait automatiquement après chaque changement avec debounce 600 ms.

Décision structurante : **PDF réel = source de vérité de l'aperçu documentaire dans Réglages**.

Implémentation en PR #174 :
- faux renderer documentaire React supprimé de la vue Réglages ;
- PDF réel devient l'aperçu principal ;
- état `À actualiser / Rendu à jour` ;
- génération uniquement par action explicite ;
- vue Application conservée ;
- preview non-sticky avant `xl` sur mobile/tablette ;
- requêtes marquées `settings_preview` ;
- fichiers isolés sous `.previews/settings_branding/<user>` ;
- ancien preview PDF du même utilisateur supprimé avant le suivant ;
- test backend : un seul preview courant par utilisateur + drapeau interne retiré avant moteur ;
- test de taxonomie : les 5 IDs Settings dispatchent vers les 5 headers PDF réels ;
- certification Branding contrôle aussi l'absence de régénération automatique après changement de modèle.

Fichier Goal canonique : `docs/settings/R4_SETTINGS_DOCUMENT_RENDERING_VISUAL_GOAL.md`.

Statut : `EN VALIDATION — PR #174`.

### R5 — QR documentaire

Garder. À améliorer : destination, donnée utilisée, aperçu, action tester/scanner.
Statut : `AUDITÉ — P2`.

### R6 — Catalogue Actes

Architecture Spécialité → Actes → Pathologies : **GARDER**.
CRUD `window.prompt()` : **REFONDRE** avec vrais formulaires/modales, validation et archivage/suppression contrôlée.
Statut : `AUDITÉ — P1`.

### R7 — Horaires & Agenda

Garder horaires/journée continue. Améliorer vers semaine réelle, jours fermés, exceptions/congés.
À prouver : impact `agenda_mode` et `use_tickets`.
Statut : `AUDITÉ — P2 / DOWNSTREAM À PROUVER`.

### R8 — IA & Système

Renommer vers **Performance & Assistance** ou équivalent. Garder Performance. Déplacer/supprimer arrière-plan animé selon valeur. Auditer Conseils cliniques. Renommer badges patient vers formulation explicable et non-jugementale.
Statut : `AUDITÉ — P2`.

### R9 — Sécurité & Backup

Garder backup chiffré, appairage local, révocation, audit log. Améliorer restauration guidée + audit log humanisé.
Statut : `AUDITÉ — GARDER / P2`.

### R10 — Mon Équipe

Garder comptes/activation/approbation/permissions fines/Truth Gate. Corriger message `4 caractères` vs politique 8..128. Quotas/upsell seulement si règle licence réelle.
Statut : `AUDITÉ — P1/P2`.

### R11 — TemplateBuilder legacy

Ne pas refondre isolément. Extraire idées utiles, vérifier dépendances, puis supprimer/quarantainer lorsque les réglages actuels couvrent le besoin.
Statut : `AUDITÉ — P3`.

## 6. Roadmap canonique

### P1 — incohérences fortes / dette visible

- **P1.1** Doctrine de sauvegarde Settings.
- **P1.2** Modèles/rendu documentaire dans Réglages. **ACTIF R4 / PR #174**.
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

### P3 — cleanup

- **P3.1** TemplateBuilder legacy : extraction utile puis suppression/quarantaine.
- **P3.2** Suppression de toggles/features uniquement après preuve d'absence de valeur downstream.

## 7. Ordre d'exécution

1. ✅ R2 Profil Cabinet ;
2. ✅ R3 Design & Ambiance ;
3. **R4 Réglages / Modèles & rendu des documents** ;
4. R6 Catalogue Actes ;
5. R7 Agenda ;
6. R8 Performance & Assistance ;
7. R9 Sécurité & Backup ;
8. R10 Mon Équipe ;
9. R11 cleanup legacy.

## 8. HANDOVER COURANT

- Chantier : **Réglages / Paramètres — Product Review & Simplification**
- Lot actif : **R4 — Réglages / Modèles & rendu des documents**
- Goal : PDF réel source de vérité de l'aperçu documentaire dans Réglages, sans toucher au Document Studio clinique
- Repo : `hraaaaf/Digital_crown`
- Branche : `settings-r4-document-studio` *(nom historique de branche ; scope produit corrigé)*
- PR : `#174 OPEN / mergeable`
- HEAD : `005f7806e0b0e13a5631bdc76c21deae0392ac09`
- Goal visuel : `docs/settings/R4_SETTINGS_DOCUMENT_RENDERING_VISUAL_GOAL.md`
- Dernière preuve : diff limité à Settings preview + schéma/DocumentFactory de preview + tests ; aucun fichier `DocumentStudio` clinique modifié
- CI/run : Branding #35 in_progress ; RBAC #62 in_progress ; T2 #392 in_progress ; CI #1137 queued au dernier check
- Blocage réel : validation CI + AFTER R4 à inspecter
- Next exact : **Branding SUCCESS → télécharger/inspecter AFTER 1440/1024/768/430/390 → score → CI/T2 verts → boussole finale → merge #174 → R6 Catalogue**
- Avancement roadmap validé : **2/15 = 13.3 %**
- Vercel : **interdit sans autorisation explicite**

## 9. Journal

### 2026-08-19 — R4 EN VALIDATION

- scope corrigé : Réglages uniquement ;
- fichier Goal renommé pour supprimer l'ambiguïté `Document Studio` ;
- ancien renderer documentaire simulé retiré ;
- PDF réel promu comme vérité visuelle ;
- régénération automatique supprimée ;
- cycle de fichiers preview isolé et borné par utilisateur ;
- tests backend de cycle de vie + taxonomie ajoutés ;
- PR #174 ouverte ;
- aucun déploiement Vercel.

### 2026-08-19 — R3 CLOSED

- PR #173 mergée ;
- 10 AFTER certifiées ;
- score visuel 9.7/10 ;
- aucun déploiement Vercel.

### 2026-08-19 — R2 CLOSED

- PR #171 mergée ;
- preset Benmoussa limité au superadmin propriétaire ;
- score visuel 9.6/10 ;
- aucun déploiement Vercel.
