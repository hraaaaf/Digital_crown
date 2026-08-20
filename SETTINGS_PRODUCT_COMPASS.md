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
| R4 Modèles documentaires | PDF réel = vérité | CLOSED — MERGED (#174) — recovery #193 certifiée | 9,2/10 |
| R5 QR documentaire | GARDER / RENDRE EXPLICITE ET TESTABLE | CLOSED — MERGED (#192) | 9,4/10 |
| R6 Catalogue Actes | GARDER architecture / REFONDRE CRUD | CLOSED — MERGED (#177) — recovery #193 certifiée | 9,6/10 |
| R7 Horaires & Agenda | GARDER / RENDRE RÉEL | CLOSED — MERGED (#178) | 9,3/10 |
| R8 Performance & Assistance | GARDER / CLARIFIER / DÉPLACER | CLOSED — MERGED (#183) | 9,5/10 |
| R9-A Journal d’Audit | GARDER / HUMANISER | CLOSED — MERGED (#185) | 9,6/10 |
| R10-A Mon Équipe / mot de passe | GARDER / ALIGNER VÉRITÉ BACKEND | CLOSED — MERGED (#188) | 9,4/10 |
| R11 TemplateBuilder legacy | SUPPRIMER FRONTEND ORPHELIN / CONSERVER BACKEND | CLOSED — MERGED (#191) | n/a — aucun écran actif modifié |

**Avancement vérifié : 10/15 = 66,7 %.**

## 5. Décisions restantes

### R1 — Shell / doctrine de sauvegarde

Shell/RBAC/Truth Gates : **GARDER**. Doctrine de sauvegarde inter-onglets : **À UNIFIER**. Cible : sauvegarde explicite par onglet + état de modifications non enregistrées, hors CRUD atomiques.

### R5 — QR documentaire

**CLOSED — CERTIFIÉ — MERGED**.

Décision finale : **GARDER / RENDRE EXPLICITE ET TESTABLE**.

Résultat :
- 7 types QR conservés ;
- `Signature` renommé `Vérification du document` ;
- `Paiement` renommé `Suivi du paiement` avec avertissement explicite qu’aucun paiement n’est encaissé ici ;
- VALIDATION corrigé vers `/api/documents/verify/<document>` ;
- PAYMENT corrigé vers `/api/documents/track/<document>` ;
- Website / Instagram / WhatsApp contextualisés ; Maps reste basé sur l’adresse du cabinet ;
- `BaseTemplateCore` et `StudioControlsCore` préservés ;
- compatibilité historique `ImageReader` restaurée dans la façade `BaseTemplate` après détection par la CI complète.

Preuves :
- BEFORE canonique `32370918895` — SUCCESS — artifact `9407139877` ;
- HEAD produit corrigé `a40722fc3db8f1c89d25ee66e37143034029654c` ;
- AFTER final `32374163733` — SUCCESS — artifact `9408382545` — digest `sha256:7272aa7d2f74c74516f6daf5b8a3f5f9b8d2b9232ee95781e9a101651700607c` ;
- CI #1476 `32374163732` — SUCCESS ;
- T2 #712 `32374163943` — SUCCESS ;
- RBAC #132 `32374163649` — SUCCESS ;
- Patient P7 Final #11 `32374163768` — SUCCESS ;
- 5 viewports sans overflow horizontal ni erreur runtime ;
- score visuel **9,4/10** ;
- closeout `docs/settings/R5_QR_TRUTH_CLOSEOUT.md` ;
- PR #192 mergée ; merge `2b342efdd8dd59fbffec6833549173b1dd74c577`.

Dette non bloquante : la microcopie Maps peut afficher `Destination : Source : adresse du cabinet`.

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

**CLOSED — CERTIFIÉ SCOPE FRONTEND — MERGED**.

Décision : **SUPPRIMER le frontend orphelin, CONSERVER le domaine backend**.

Preuves :
- reachability BEFORE #3 `32365989327` — SUCCESS, artifact `9405292952`, digest `sha256:7d25355bc2aa2fd5350beef48aed9985bc1f46fc3817fd118e05a4b433a8d66d` ;
- `TemplateBuilder.tsx` non routé et sans consommation produit externe ;
- `templateApi` template consommé uniquement par ce builder ;
- `DocumentTemplate` largement référencé backend et conservé ;
- `TemplateEngine` + tests + instanciation `DocumentFactory` conservés hors scope ;
- commit produit `fb51b02125baee2996694db2e1ab2173ece30897` ;
- R11 AFTER/reachability #4 `32366397114` — SUCCESS, artifact `9405470141`, digest `sha256:67a7e753e8bc51f8293c9c9f91d39adffc7d73a78cbe690a068654b28b1f8543` ;
- T2 #707 — SUCCESS ; frontend CI tests/build — SUCCESS ;
- aucun fichier backend dans le diff produit R11.

Merge squash : `a4af5ce0ad535e8c154fb7cecee931cba7f76204`.
Closeout : `docs/settings/R11_TEMPLATEBUILDER_REACHABILITY_CLOSEOUT.md`.
Aucun score visuel : aucun écran actif n’a été modifié.

## 6. Roadmap active

P1 : **doctrine sauvegarde — prochain lot recommandé** ; modèles documentaires ✅ ; Catalogue CRUD ✅ ; Profil ✅ ; mot de passe Team ✅ ; Branding ✅.

P2 : Agenda réel ✅ ; Catalogue avancé ; Performance & Assistance ✅ ; Audit Log humanisé ✅ ; indicateurs patient explicables ; QR documentaire ✅ ; restauration guidée.

P3 : TemplateBuilder legacy ✅ frontend orphelin supprimé ; dette backend TemplateEngine conservée pour lot séparé si utile ; suppression de toggles/features uniquement après preuve downstream.

## 7. HANDOVER COURANT

- Chantier : **Réglages — Product Review & Simplification**
- Lot actif : **Recovery R4 + R6 post-R7 — PR #193**
- Statut : **CERTIFIÉ — READY TO MERGE**
- Repo : `hraaaaf/Digital_crown`
- Base : `master`
- Branche : `settings-recovery-r4-r6-post-r7`
- HEAD produit certifié : `5ac5104dae3e51cc72c22362bba5fd9b259df650`
- HEAD docs : `6bccb2b78eb792c46417d54647a188dbd5ceb829` ; delta = closeout Markdown-only
- CI #1481 `32380900040` — SUCCESS
- R4 Document Models #21, Branding #68, R5 QR #6, R6 #11, RBAC #135, Read Truth #39, T2 #715, R11 #7 et P7 #14 — SUCCESS
- Closeout : `docs/settings/R4_R6_POST_R7_RECOVERY_CLOSEOUT.md`
- Scores : R4 **9,2/10** ; R5 **9,4/10** ; R6 **9,6/10**
- Prochain lot après merge : **R1 — Shell / doctrine de sauvegarde**
- Next exact : **merge #193 → vérifier master → reprendre R1 en audit uniquement**
- Avancement vérifié après merge : **10/15 = 66,7 %**
- Vercel : **aucun déploiement**

## 8. Journal

### 2026-08-20 — RECOVERY R4 + R6 POST-R7 CERTIFIÉE

- R7 avait régressé hors scope des surfaces R4/R6 certifiées ;
- récupération ciblée sans revert global de R7 ;
- R4 replacé dans les `*Core` compatibles R5 ;
- R6 CRUD complet restauré ;
- contrats `settings_preview`, Heritage centré et Playfair/serif restaurés ;
- CI #1481 et tous les gates exact-head verts ;
- R4/R5/R6 inspectés sur 5 viewports ; scores maintenus 9,2 / 9,4 / 9,6 ;
- closeout `docs/settings/R4_R6_POST_R7_RECOVERY_CLOSEOUT.md` ;
- aucun Vercel.

### 2026-08-20 — R5 CLOSED

- PR #192 mergée ; merge `2b342efdd8dd59fbffec6833549173b1dd74c577` ;
- destinations QR VALIDATION/PAYMENT corrigées vers `/api/documents/verify|track/...` ;
- libellés `Vérification du document` / `Suivi du paiement` rendus factuels ;
- compatibilité historique `ImageReader` restaurée après détection CI ;
- AFTER final, CI #1476, T2 #712, RBAC #132 et P7 Final #11 verts ;
- 5 viewports propres ; score **9,4/10** ;
- aucun Vercel.

### 2026-08-20 — R11 CLOSED

- PR #191 squash-mergée ; merge `a4af5ce0...` ;
- reachability repo-wide prouvée avant suppression ;
- `TemplateBuilder.tsx` et API frontend template orpheline retirés ;
- `cabinetApi`, `DocumentTemplate`, seed, router `/api/templates` et `TemplateEngine` conservés ;
- R11 #4 et T2 #707 verts ; frontend CI tests/build vert ; aucun backend produit modifié ;
- aucun écran actif modifié ; aucun Vercel.

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
