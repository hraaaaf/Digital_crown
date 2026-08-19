# SETTINGS PRODUCT COMPASS — Réglages / Paramètres

Date d'initialisation : 2026-08-19
Repo : `hraaaaf/Digital_crown`
Statut : **BOUSSOLE CANONIQUE ACTIVE**

> Source de reprise prioritaire du chantier Réglages / Paramètres.
> `SETTINGS_HARDENING_CLOSEOUT.md` reste la preuve du Hardening précédent.
> Aucun déploiement Vercel sans autorisation explicite.

## 1. Goal

Juger et améliorer chaque feature de Réglages comme un produit réel de cabinet dentaire : valeur métier, UX, robustesse, vérité backend, dette, doublons, promesses trompeuses et complexité inutile.

Décisions : **GARDER / AMÉLIORER / REFONDRE / DÉPLACER / SUPPRIMER / À PROUVER**.

## 2. Doctrine

Pour chaque lot significatif : audit downstream → BEFORE si UI → Goal + critères → wireframe/référence → implémentation → tests → AFTER mêmes viewports + score → docs canoniques → merge/post-merge.

Ne jamais créditer un lot sans preuve. Une CI queued/in-progress n’arrête pas le travail indépendant. Une preuve CI sur un parent peut être réutilisée uniquement si l’équivalence produit du delta est explicitement démontrée. Vercel reste interdit sans autorisation explicite.

## 3. Règle propriétaire Benmoussa

Le preset personnel `Dr. Benmoussa Achraf` reste réservé au superadmin propriétaire. Pour un non-superadmin, la réinitialisation repart des données réelles de son cabinet. L’identité propriétaire repose sur `SUPERADMIN_EMAIL`, pas seulement sur le rôle ADMIN.

Statut : **CERTIFIÉ R2**.

## 4. Lots certifiés

| Lot | Décision | Statut | Score visuel |
|---|---|---|---:|
| R2 Profil Cabinet | GARDER / SIMPLIFIER | CLOSED — MERGED (#171) | 9,6/10 |
| R3 Design & Ambiance | GARDER / CLARIFIER | CLOSED — MERGED (#173) | 9,7/10 |
| R4 Modèles documentaires | PDF réel = vérité | CLOSED — MERGED (#174) | 9,2/10 |
| R6 Catalogue Actes | GARDER architecture / REFONDRE CRUD | CLOSED — MERGED (#177) | 9,6/10 |
| R7 Horaires & Agenda | GARDER / RENDRE RÉEL | CLOSED — MERGED (#178) | 9,3/10 |
| R8 Performance & Assistance | GARDER / CLARIFIER / DÉPLACER | CLOSED — MERGED (#183) | 9,5/10 |

**Avancement vérifié : 6/15 = 40,0 %.**

## 5. Décisions restantes

### R1 — Shell / doctrine de sauvegarde

Shell/RBAC/Truth Gates : **GARDER**. Doctrine de sauvegarde inter-onglets : **À UNIFIER**. Cible : sauvegarde explicite par onglet + état de modifications non enregistrées, hors CRUD atomiques.

### R5 — QR documentaire

**GARDER / RENDRE EXPLICITE ET TESTABLE**. PR d’audit #187 ouverte ; aucune refonte avant preuve des destinations réelles.

### R7 — Horaires & Agenda

**CLOSED — CERTIFIÉ — MERGED**.

Preuves : `docs/settings/R7_AGENDA_REAL_SCHEDULE_VISUAL_GOAL.md` + `docs/settings/R7_AGENDA_REAL_SCHEDULE_CLOSEOUT.md`. Merge `4f20832ee70fecf5878242cc1a98ef633d8be129`.

### R8 — Performance & Assistance

**CLOSED — CERTIFIÉ — MERGED**.

Décision finale :
- Mode Performance : **GARDER** ; downstream réel ;
- Arrière-plan animé : **DÉPLACER vers Design & Ambiance** ;
- Conseils cliniques contextuels : **GARDER** ; consommateurs `Sidebar` + `Step1Cephalo` ;
- Indicateurs patient : **GARDER / RENOMMER / EXPLIQUER** ; backend = 60 % assiduité RDV + 40 % encaissé/facturé, neutre 50 sans données, override praticien possible ;
- aucune nouvelle IA/LLM ; aucun champ persistant supprimé.

HEAD produit certifié : `bfabc0cb4809b7cca2a0a9b4bee4cc93b669d482`.
Merge : `1ac1dd54a9f29c29c06107cd2a1395e8bf6639ce`.
Score : **9,5/10**.
Closeout : `docs/settings/R8_PERFORMANCE_ASSISTANCE_CLOSEOUT.md`.

### R9 — Sécurité & Backup

**LOT ACTIF SUIVANT — R9-A Journal d’Audit humanisé — PR #185**.

Zone forte : **GARDER** backup chiffré, appairage local, révocation, audit log. La collecte backend reste hors scope R9-A. Cible immédiate : rendre actions, ressources, sévérités, utilisateur et détails immédiatement compréhensibles sans inventer de données.

Vérité déjà auditée : endpoint tenant-isolé ; filtres action/resource_type/severity ; API retourne `user_id` mais aucun nom utilisateur, donc UI honnête = `Utilisateur #id`.

PR #185 est préparatoire seulement et doit être reconstruite sur master post-R8 avant implémentation. Sa baseline BEFORE historique a été annulée pendant `playwright install --with-deps chromium`; stratégie retenue : installation Chromium simple, puis une baseline unique.

### R10 — Mon Équipe

**GARDER** comptes/activation/approbation/permissions fines/Truth Gate. Corriger la vérité mot de passe UI vers 8..128 ; PR #184 ouverte. Quotas/upsell uniquement si règle licence réelle.

### R11 — TemplateBuilder legacy

Ne pas refondre isolément. Prouver les dépendances, extraire les idées utiles, puis supprimer/quarantainer lorsque Document Studio couvre le besoin. Audit PR #186 ouverte.

## 6. Roadmap active

P1 : doctrine sauvegarde ; modèles documentaires ✅ ; Catalogue CRUD ✅ ; Profil ✅ ; mot de passe Team ; Branding ✅.

P2 : Agenda réel ✅ ; Catalogue avancé ; Performance & Assistance ✅ ; **Audit Log humanisé ACTIF** ; indicateurs patient explicables ; QR documentaire ; restauration guidée.

P3 : TemplateBuilder legacy ; suppression de toggles/features uniquement après preuve downstream.

## 7. HANDOVER COURANT

- Chantier : **Réglages — Product Review & Simplification**
- Lot actif : **R9-A — Journal d’Audit humanisé**
- Repo : `hraaaaf/Digital_crown`
- Base : `master`
- Dernier merge R8 : `1ac1dd54a9f29c29c06107cd2a1395e8bf6639ce`
- R8 : CLOSED — score **9,5/10**
- PR suivante : `#185`
- Branche R9-A : `settings-r9-audit-log-humanized`
- HEAD R9-A préparatoire : `6397ccc680070ee73a9b29f234c206881328cdb0`
- Scope R9-A actuel : Goal + workflow BEFORE uniquement, zéro code produit
- Next exact : **reconstruire R9-A sur master post-R8 → corriger baseline Chromium → BEFORE 5 viewports → implémentation unique → AFTER/tests/score**
- Avancement vérifié : **6/15 = 40,0 %**
- Vercel : **aucun déploiement**

## 8. Journal

### 2026-08-19 — R8 CLOSED

- PR #183 squash-mergée ; merge `1ac1dd54...` ;
- `IA & Système` remplacé par `Performance & Assistance` ;
- arrière-plan animé déplacé vers Design & Ambiance ;
- conseils cliniques et indicateurs patients conservés sur preuve downstream ;
- score patient expliqué factuellement 60/40 ;
- AFTER exact-head inspecté sur 1440/1024/768/430/390 ; score **9,5/10** ;
- IA Visual #18, Branding #65, RBAC #124, Profile R2 #24, Read Truth #12 et T2 #644 verts sur le HEAD produit ; CI #1396 verte sur parent produit-identique ;
- aucun Vercel.

### 2026-08-19 — R7 CLOSED

- PR #178 mergée ; merge `4f20832...` ;
- six gates produit vertes ; backend 2748 passed ; frontend 367 passed ;
- score **9,3/10** ; aucun Vercel.

### 2026-08-19 — R6 CLOSED

- PR #177 mergée ; CRUD prompt remplacé par formulaires sûrs ; score **9,6/10**.

### 2026-08-19 — R4 CLOSED

- PR #174 mergée ; PDF réel source de vérité ; cinq modèles premium ; score global **9,2/10**.

### 2026-08-19 — R3 CLOSED

- PR #173 mergée ; scope Branding clarifié ; score **9,7/10**.

### 2026-08-19 — R2 CLOSED

- PR #171 mergée ; Profil simplifié et preset propriétaire verrouillé ; score **9,6/10**.
