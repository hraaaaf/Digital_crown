# SETTINGS PRODUCT COMPASS — Réglages / Paramètres

Date d'initialisation : 2026-08-19
Repo : `hraaaaf/Digital_crown`
Statut : **BOUSSOLE CANONIQUE ACTIVE**

> Source de reprise prioritaire du chantier Réglages / Paramètres.
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

Le preset personnel (`Dr. Benmoussa Achraf`, équivalent arabe et expertises associées) reste réservé au superadmin propriétaire ; jamais défaut d'un cabinet standard ; non-superadmin = reset depuis données réelles ; vérité propriétaire = backend `SUPERADMIN_EMAIL`.

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

RBAC / Truth Gates : garder. Navigation correcte. Doctrine de sauvegarde encore incohérente.
Décision : **GARDER le shell, REFONDRE la doctrine de sauvegarde**.
Statut : `AUDITÉ — À EXÉCUTER`.

### R2 — Profil Cabinet

Décision : **GARDER / SIMPLIFIER — CLOSED**.
Preuves : PR #171 MERGED ; HEAD produit `99de2c4aee19f389bdbd0eee46cae072747babdb` ; merge `397f40b50a52457ad53f4b1cb8a9def85b74f5a8` ; R2 Visual #17 / CI #1117 / T2 #377 SUCCESS.
Score visuel : **9.6/10**.
Statut : `CLOSED — CERTIFIÉ — MERGED`.

### R3 — Design & Ambiance

Décision : **GARDER / CLARIFIER LE MODÈLE MENTAL — CLOSED**.
Preuves : PR #173 MERGED ; HEAD produit `9db4b560af7925233d5584dfb7af870b76e086d2` ; merge `985873dc644453b078a2a0efc6a1e006121ee6b0` ; Branding #26 / RBAC #53 / T2 #381 / CI #1124 SUCCESS ; 10 AFTER inspectées.
Score visuel : **9.7/10**.
Statut : `CLOSED — CERTIFIÉ — MERGED`.

### R4 — Réglages / Modèles & rendu des documents

Décision finale : **GARDER / RENDRE LE PDF RÉEL AUTORITAIRE — CLOSED**.

Implémenté : faux renderer React supprimé ; PDF réel = aperçu principal ; génération explicite ; 5 IDs alignés `swiss / royal / clinical / modern / heritage` ; moteur `premium_document_headers.py` ; cinq signatures réellement distinctes ; arabe via fonte Unicode locale ; previews isolés et bornés ; Document Studio clinique hors scope.

Preuves : PR #174 MERGED ; HEAD produit `0dd384c7b242945270ddb009350961da3590f44f` ; merge `5efca67d5416c1d7752a792c304b8d90c7a80aea` ; Document Models #19 `32207520254` / Branding #56 `32207520252` / RBAC #91 `32207520212` / T2 #459 `32207520238` / CI #1205 `32207520301` SUCCESS ; closeout `docs/settings/R4B_PREMIUM_DOCUMENT_MODELS_CLOSEOUT.md`.

Score visuel global modèles : **9.2/10**.
Statut : `CLOSED — CERTIFIÉ — MERGED`.

### R5 — QR documentaire

Garder. À améliorer : destination, donnée utilisée, aperçu, action tester/scanner.
Statut : `AUDITÉ — P2`.

### R6 — Catalogue Actes

Décision finale : **GARDER L'ARCHITECTURE / REFONDRE LE CRUD — CLOSED**.

Implémenté :
- architecture Spécialité → Actes → Pathologies conservée ;
- `window.prompt()` supprimé ;
- vrais formulaires/modales avec validation ;
- édition complète des actes/pathologies ;
- désactivation contrôlée pour entités supportant `is_active` ;
- aucune suppression physique inventée pour les spécialités ;
- mutations ne ferment la modale qu'après succès backend ;
- mobile rééquilibré ; états inactifs rendus explicites.

Preuves :
- PR #177 MERGED ;
- HEAD produit certifié `f0e05923e85c34e90493a1086bec6b5eeabc86ed` ;
- merge `f88da1bed2f0cc66be8ecf6fef140d7f270903db` ;
- Catalog #9 run `32207096740` SUCCESS ;
- RBAC #89 run `32207096768` SUCCESS ;
- Read Truth #12 run `32207096741` SUCCESS ;
- T2 #450 run `32207096762` SUCCESS ;
- CI #1196 run `32207096743` SUCCESS ;
- 10 AFTER inspectées : page + modale Acte × 1440/1024/768/430/390.

Score visuel : **9.6/10**.
Statut : `CLOSED — CERTIFIÉ — MERGED`.

### R7 — Horaires & Agenda

Décision en cours : **GARDER les horaires, rendre la configuration réellement appliquée**.

Audit vérifié :
- modèle historique = horaires globaux + `agenda_mode` + `use_tickets` ;
- DailyView / WeeklyView historiquement codés 08:00–19:00 ;
- `agenda_mode` n'est pas consommé par Agenda ; la flexibilité réelle vit déjà dans `Appointment.scheduling_type` ;
- `use_tickets` ne produit qu'un bouton `Nouveau Ticket` sans action ;
- backend possède déjà les exceptions/congés `/agenda/exceptions` ;
- Goal + wireframe écrits dans `docs/settings/R7_AGENDA_REAL_SCHEDULE_VISUAL_GOAL.md` ;
- Settings R7 a déjà avancé vers semaine persistée + exceptions.

Preuves courantes au HEAD `4d44a820f680ebdf75150e3d8d43e41f84333f82` :
- Settings Agenda Visual #9 SUCCESS ;
- Read Truth #17 SUCCESS ;
- T2 #463 SUCCESS ;
- CI #1209 SUCCESS ;
- **Agenda Downstream BEFORE #1 FAILURE : root overflow weekly à 1440 px** ;
- **RBAC #95 FAILURE**.

Statut : `ACTIF — NON CERTIFIÉ`.

### R8 — IA & Système

Cible : **Performance & Assistance**.
- Performance : downstream réel, GARDER.
- Fond animé : downstream réel, DÉPLACER vers Design & Ambiance.
- Conseils cliniques : persistés mais aucun consommateur retrouvé, candidat retrait UI.
- Indicateurs patient : persistés mais aucun consommateur retrouvé, candidat retrait UI / cleanup après preuve finale.
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
- **P1.2** Modèles/rendu documentaire. ✅ CLOSED R4.
- **P1.3** Catalogue CRUD réel. ✅ CLOSED R6.
- **P1.4** Profil / preset propriétaire. ✅ CLOSED R2.
- **P1.5** Team password copy 8..128.
- **P1.6** Scope Branding. ✅ CLOSED R3.

### P2 — valeur métier / simplification

- **P2.1** Agenda hebdomadaire réel. **ACTIF R7**.
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
3. ✅ R4 Modèles & rendu documents ;
4. ✅ R6 Catalogue Actes ;
5. **R7 Agenda** ;
6. R8 Performance & Assistance ;
7. R9 Sécurité & Backup ;
8. R10 Mon Équipe ;
9. R11 cleanup legacy.

## 8. HANDOVER COURANT

- Chantier : **Réglages / Paramètres — Product Review & Simplification**
- Lot actif : **R7 — Horaires & Agenda**
- Goal : semaine réelle persistée + fermetures/congés + Agenda downstream réellement borné par les horaires
- Repo : `hraaaaf/Digital_crown`
- Branche : `settings-r7-agenda-real-schedule`
- PR : `#178 OPEN / mergeable`
- HEAD : `4d44a820f680ebdf75150e3d8d43e41f84333f82`
- Dernière preuve : Settings Agenda Visual #9 / Read Truth #17 / T2 #463 / CI #1209 SUCCESS ; downstream baseline et RBAC rouges
- Blocage réel : overflow weekly détecté à 1440 px dans le downstream + RBAC #95 à diagnostiquer/corriger
- Next exact : **corriger baseline/harness ou overflow réel → diagnostiquer RBAC #95 → wiring Daily/Weekly → AFTER Settings + downstream mêmes viewports → score → merge**
- Avancement roadmap validé : **4/15 = 26.7 %**
- Vercel : **interdit sans autorisation explicite**

## 9. Journal

### 2026-08-19 — R6 CLOSED
- CRUD prompt remplacé par formulaires sûrs ; aucune suppression physique inventée ; 10 AFTER inspectées ; score 9.6/10 ; Catalog/RBAC/Read Truth/T2/CI verts ; PR #177 mergée en `f88da1bed2f0cc66be8ecf6fef140d7f270903db` ; aucun Vercel.

### 2026-08-19 — R4 CLOSED
- PDF réel promu vérité du preview ; 5 modèles premium réalignés ; arabe corrigé ; score global 9.2/10 ; tous gates verts ; PR #174 mergée en `5efca67d5416c1d7752a792c304b8d90c7a80aea` ; aucun Vercel.

### 2026-08-19 — R3 CLOSED
- PR #173 mergée ; 10 AFTER certifiées ; score 9.7/10 ; aucun Vercel.

### 2026-08-19 — R2 CLOSED
- PR #171 mergée ; preset Benmoussa limité au superadmin propriétaire ; score 9.6/10 ; aucun Vercel.
