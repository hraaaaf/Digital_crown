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
| R8 Performance & Assistance | GARDER / CLARIFIER / DÉPLACER | CERTIFIÉ — READY TO MERGE (#183) | 9,5/10 |

**Avancement comptabilisé : 5/15 = 33,3 %.** R8 ne sera crédité qu’après preuve du merge.

## 5. Décisions restantes

### R1 — Shell / doctrine de sauvegarde

Shell/RBAC/Truth Gates : **GARDER**. Doctrine de sauvegarde inter-onglets : **À UNIFIER**. Cible : sauvegarde explicite par onglet + état de modifications non enregistrées, hors CRUD atomiques.

### R5 — QR documentaire

**GARDER / RENDRE EXPLICITE ET TESTABLE**. PR d’audit #187 ouverte ; aucune refonte avant preuve des destinations réelles.

### R7 — Horaires & Agenda

**CLOSED — CERTIFIÉ — MERGED**.

Semaine 7 jours réelle, jours fermés, exceptions, journée continue, bornes Daily/Weekly, garde pause/hors-plage, backend autoritaire create/update/bulk, compatibilité legacy fail-safe et feedback backend explicite.

Preuves : `docs/settings/R7_AGENDA_REAL_SCHEDULE_VISUAL_GOAL.md` + `docs/settings/R7_AGENDA_REAL_SCHEDULE_CLOSEOUT.md`. Merge `4f20832ee70fecf5878242cc1a98ef633d8be129`.

### R8 — Performance & Assistance

**CERTIFIÉ — READY TO MERGE — PR #183**.

Décision finale :
- Mode Performance : **GARDER** ; downstream réel ;
- Arrière-plan animé : **DÉPLACER vers Design & Ambiance** ;
- Conseils cliniques contextuels : **GARDER** ; consommateurs `Sidebar` + `Step1Cephalo` ;
- Indicateurs patient : **GARDER / RENOMMER / EXPLIQUER** ; backend = 60 % assiduité RDV + 40 % encaissé/facturé, neutre 50 sans données, override praticien possible ;
- aucune nouvelle IA/LLM ; aucun champ persistant supprimé.

HEAD certifié : `bfabc0cb4809b7cca2a0a9b4bee4cc93b669d482`.

Preuves exact-head : IA Visual #18 ✅ ; Branding #65 ✅ ; RBAC #124 ✅ ; Profile R2 #24 ✅ ; Read Truth #12 ✅ ; T2 #644 ✅. CI #1396 ✅ sur le parent produit-identique `7ee155...`; delta vers `bfabc0...` = une seule ligne dans le harness IA (`--with-deps chromium` → `chromium`), zéro fichier produit.

Score : **9,5/10**.

Closeout : `docs/settings/R8_PERFORMANCE_ASSISTANCE_CLOSEOUT.md`.

### R9 — Sécurité & Backup

Zone forte : **GARDER** backup chiffré, appairage local, révocation, audit log. Audit log humanisé préparé dans PR #185. Restauration guidée reste à traiter.

### R10 — Mon Équipe

**GARDER** comptes/activation/approbation/permissions fines/Truth Gate. Corriger la vérité mot de passe UI vers 8..128 ; PR #184 ouverte. Quotas/upsell uniquement si règle licence réelle.

### R11 — TemplateBuilder legacy

Ne pas refondre isolément. Prouver les dépendances, extraire les idées utiles, puis supprimer/quarantainer lorsque Document Studio couvre le besoin. Audit PR #186 ouverte.

## 6. Roadmap active

P1 : doctrine sauvegarde ; modèles documentaires ✅ ; Catalogue CRUD ✅ ; Profil ✅ ; mot de passe Team ; Branding ✅.

P2 : Agenda réel ✅ ; Catalogue avancé ; **Performance & Assistance CERTIFIÉ / READY TO MERGE** ; **Audit Log humanisé = prochain lot** ; indicateurs patient explicables ; QR documentaire ; restauration guidée.

P3 : TemplateBuilder legacy ; suppression de toggles/features uniquement après preuve downstream.

## 7. HANDOVER COURANT

- Chantier : **Réglages — Product Review & Simplification**
- Lot actif : **R8 — Performance & Assistance — closeout/merge**
- Repo : `hraaaaf/Digital_crown`
- Base : `master`
- Master actuel : `5c2593d4a3d063c439faa8746403c793fb2241f4`
- PR active : `#183`
- Branche R8 : `settings-r8-performance-assistance`
- HEAD produit certifié : `bfabc0cb4809b7cca2a0a9b4bee4cc93b669d482`
- Score R8 : **9,5/10**
- Gates exact-head : IA #18 ✅ ; Branding #65 ✅ ; RBAC #124 ✅ ; Profile R2 #24 ✅ ; Read Truth #12 ✅ ; T2 #644 ✅
- CI de référence produit : #1396 ✅ sur `7ee155...` ; équivalence produit jusqu’à `bfabc0...` vérifiée
- Next exact : **merge #183 → post-merge docs → créditer 6/15 → reconstruire R9-A sur master**
- Avancement comptabilisé : **5/15 = 33,3 %**
- Vercel : **aucun déploiement**

## 8. Journal

### 2026-08-19 — R8 CERTIFIÉ / READY TO MERGE

- PR #183 ; HEAD certifié `bfabc0...` ;
- ancienne surface `IA & Système` remplacée par `Performance & Assistance` ;
- arrière-plan animé déplacé vers Design & Ambiance ;
- conseils cliniques et indicateurs patients conservés sur preuve downstream ;
- score patient expliqué factuellement 60/40 ;
- AFTER exact-head inspecté sur 1440/1024/768/430/390 ; score **9,5/10** ;
- six gates exact-head vertes + CI verte sur parent produit-identique ;
- aucun Vercel.

### 2026-08-19 — R7 CLOSED

- PR #178 mergée ; merge `4f20832...` ;
- six gates produit vertes ; backend 2748 passed ; frontend 367 passed ;
- 10 AFTER Settings + 10 downstream inspectées sur 5 viewports ;
- aucun overflow horizontal downstream ; score **9,3/10** ;
- aucun Vercel.

### 2026-08-19 — R6 CLOSED

- PR #177 mergée ; CRUD prompt remplacé par formulaires sûrs ; score **9,6/10**.

### 2026-08-19 — R4 CLOSED

- PR #174 mergée ; PDF réel source de vérité ; cinq modèles premium ; score global **9,2/10**.

### 2026-08-19 — R3 CLOSED

- PR #173 mergée ; scope Branding clarifié ; score **9,7/10**.

### 2026-08-19 — R2 CLOSED

- PR #171 mergée ; Profil simplifié et preset propriétaire verrouillé ; score **9,6/10**.
