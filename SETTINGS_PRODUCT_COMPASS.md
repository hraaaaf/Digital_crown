# SETTINGS PRODUCT COMPASS — Réglages / Paramètres

Date d'initialisation : 2026-08-19
Dernière mise à jour : 2026-08-20
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
| R9-A Journal d’Audit | GARDER / HUMANISER | CLOSED — MERGED (#185) | 9,6/10 |
| R10-A Mon Équipe / mot de passe | GARDER / ALIGNER VÉRITÉ BACKEND | CLOSED — MERGED (#188) | 9,4/10 |

**Avancement vérifié : 8/15 = 53,3 %.**

## 5. Décisions restantes

### R1 — Shell / doctrine de sauvegarde

Shell/RBAC/Truth Gates : **GARDER**. Doctrine de sauvegarde inter-onglets : **À UNIFIER**. Cible : sauvegarde explicite par onglet + état de modifications non enregistrées, hors CRUD atomiques.

### R5 — QR documentaire

**GARDER / RENDRE EXPLICITE ET TESTABLE**. PR d’audit #187 préparée ; aucune refonte avant preuve des destinations réelles.

### R7 — Horaires & Agenda

**CLOSED — CERTIFIÉ — MERGED**.

Preuves : `docs/settings/R7_AGENDA_REAL_SCHEDULE_VISUAL_GOAL.md` + `docs/settings/R7_AGENDA_REAL_SCHEDULE_CLOSEOUT.md`. Merge `4f20832ee70fecf5878242cc1a98ef633d8be129`.

### R8 — Performance & Assistance

**CLOSED — CERTIFIÉ — MERGED**.

Décision finale :
- Mode Performance : **GARDER** ; downstream réel ;
- Arrière-plan animé : **DÉPLACER vers Design & Ambiance** ;
- Conseils cliniques contextuels : **GARDER** ;
- Indicateurs patient : **GARDER / RENOMMER / EXPLIQUER** ;
- aucune nouvelle IA/LLM ; aucun champ persistant supprimé.

HEAD produit certifié : `bfabc0cb4809b7cca2a0a9b4bee4cc93b669d482`.
Merge : `1ac1dd54a9f29c29c06107cd2a1395e8bf6639ce`.
Score : **9,5/10**.
Closeout : `docs/settings/R8_PERFORMANCE_ASSISTANCE_CLOSEOUT.md`.

### R9 — Sécurité & Backup

**R9-A CLOSED — CERTIFIÉ — MERGED**.

Décision : **GARDER** backup chiffré, appairage local, révocation et audit log. Journal humanisé sans modifier la collecte backend : actions/sévérités/ressources lisibles, `Utilisateur #id` sans identité inventée, fallback brut pour valeurs inconnues, détails/IP explicites, responsive corrigé.

HEAD produit certifié : `f20cfe39eeddf28152c1cc106c17eb6727edf11b`.
Merge : `bda7f99aa95e9341f5154293618c35949bcae331`.
Score : **9,6/10**.
Closeout : `docs/settings/R9A_AUDIT_LOG_HUMANIZED_CLOSEOUT.md`.

### R10 — Mon Équipe

**R10-A CLOSED — CERTIFIÉ — MERGED**.

Décision : **GARDER** comptes/activation/approbation/permissions fines/Truth Gate. Contrat mot de passe frontend aligné exactement sur le backend `8..128`; overflow mobile réel de la carte membre corrigé sans toucher auth/hash/quota/RBAC/approbation.

HEAD produit certifié : `d174abee1ab01804ba4c4b5cadb18d3a82eb9b1c`.
Merge : `5e8307d4d20ee6ed0df18ee7d06fe2cdb24bc24a`.
AFTER : `32311979010` ; CI `32311979067` ; T2 `32311978966` ; Read Truth `32311978959` — **SUCCESS**.
Score : **9,4/10**.
Closeout : `docs/settings/R10A_TEAM_PASSWORD_TRUTH_CLOSEOUT.md`.

### R11 — TemplateBuilder legacy

**LOT ACTIF — RECONSTRUCTION D’AUDIT SUR MASTER POST-R10**.

L’ancienne PR #186 a été **fermée sans merge** car son hypothèse de départ était devenue fausse : `frontend/src/features/admin/TemplateBuilder.tsx` existe réellement sur master.

Faits actuels déjà vérifiés :
- `TemplateBuilder.tsx` existe mais n’est pas routé dans `App.tsx` ;
- il appelle `templateApi.getById/update/preview/setDefault` ;
- le router `/api/templates` actuel expose list/get/create/set-default/delete mais pas update/preview ;
- `DocumentTemplate` + table `document_templates` persistent réellement `body_html` et `design_config` ;
- le seed recrée 6 styles ordonnance + 1 certificat au démarrage ;
- `DocumentFactory` instancie encore `TemplateEngine` et possède `_get_default_template()`, mais ses méthodes publiques inspectées délèguent directement aux générateurs ReportLab ;
- `OrdonnanceGenerator` lit la configuration active depuis `CabinetConfig`, pas `DocumentTemplate.design_config` ;
- le backend `DesignConfig` et le `CabinetConfig` actif constituent deux architectures documentaires parallèles.

Pré-verdict : **TemplateBuilder / TemplateEngine = legacy candidat à quarantaine/suppression**, mais **ne pas supprimer les données ni le modèle `DocumentTemplate` avant preuve repo-wide d’absence de dépendances**.

## 6. Roadmap active

P1 : doctrine sauvegarde ; modèles documentaires ✅ ; Catalogue CRUD ✅ ; Profil ✅ ; mot de passe Team ✅ ; Branding ✅.

P2 : Agenda réel ✅ ; Catalogue avancé ; Performance & Assistance ✅ ; Audit Log humanisé ✅ ; indicateurs patient explicables ; QR documentaire ; restauration guidée.

P3 : **TemplateBuilder legacy ACTIF** ; suppression de toggles/features uniquement après preuve downstream.

## 7. HANDOVER COURANT

- Chantier : **Réglages — Product Review & Simplification**
- Lot actif : **R11 — TemplateBuilder legacy**
- Repo : `hraaaaf/Digital_crown`
- Base : `master`
- Dernier merge : R10-A `5e8307d4d20ee6ed0df18ee7d06fe2cdb24bc24a`
- R10-A : CLOSED — score **9,4/10**
- Ancienne PR R11 : #186 **CLOSED — NON MERGÉE — SUPERSEDED**
- Next exact : **repo-wide reachability TemplateBuilder / TemplateEngine / DocumentTemplate → classifier dépendances actives vs legacy → nouveau Goal R11 propre → décision quarantaine/suppression minimale**
- Avancement vérifié : **8/15 = 53,3 %**
- Vercel : **aucun déploiement**

## 8. Journal

### 2026-08-20 — R10-A CLOSED

- PR #188 squash-mergée ; merge `5e8307d4...` ;
- contrat frontend mot de passe aligné sur backend 8..128 ;
- overflow mobile diagnostiqué jusqu’au groupe d’actions invisible en layout puis corrigé ;
- AFTER exact-head 5/5 sans overflow, erreurs runtime 0/5 ;
- CI #1455, T2 #697, Read Truth #16, RBAC #128, Profile R2 #28 et IA #22 verts ;
- score **9,4/10** ; aucun Vercel.

### 2026-08-19 — R9-A CLOSED

- PR #185 mergée ; merge `bda7f99...` ;
- Journal d’Audit humanisé sans perte d’information ni identité inventée ;
- 5 viewports exact-head propres ; score **9,6/10** ; aucun Vercel.

### 2026-08-19 — R8 CLOSED

- PR #183 squash-mergée ; merge `1ac1dd54...` ;
- `IA & Système` remplacé par `Performance & Assistance` ;
- arrière-plan animé déplacé vers Design & Ambiance ;
- conseils cliniques et indicateurs patients conservés sur preuve downstream ;
- score **9,5/10** ; aucun Vercel.

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
