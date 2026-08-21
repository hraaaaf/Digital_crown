# SETTINGS PRODUCT COMPASS — Réglages / Paramètres

Dernière mise à jour : 2026-08-21
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
| R1 Shell / doctrine de sauvegarde | GARDER / UNIFIER | CLOSED — MERGED (#194) | 9,5/10 |
| R2 Profil Cabinet | GARDER / SIMPLIFIER | CLOSED — MERGED (#171) | 9,6/10 |
| R3 Design & Ambiance | GARDER / CLARIFIER | CLOSED — MERGED (#173) | 9,7/10 |
| R4 Modèles documentaires | PDF réel = vérité | CLOSED — MERGED (#174) — recovery #193 MERGED | 9,2/10 |
| R5 QR documentaire | GARDER / RENDRE EXPLICITE ET TESTABLE | CLOSED — MERGED (#192) | 9,4/10 |
| R6 Catalogue Actes | GARDER architecture / REFONDRE CRUD | CLOSED — MERGED (#177) — recovery #193 MERGED | 9,6/10 |
| R7 Horaires & Agenda | GARDER / RENDRE RÉEL | CLOSED — MERGED (#178) | 9,3/10 |
| R8 Performance & Assistance | GARDER / CLARIFIER / DÉPLACER | CLOSED — MERGED (#183) | 9,5/10 |
| R9-A Journal d’Audit | GARDER / HUMANISER | CLOSED — MERGED (#185) | 9,6/10 |
| R10-A Mon Équipe / mot de passe | GARDER / ALIGNER VÉRITÉ BACKEND | CLOSED — MERGED (#188) | 9,4/10 |
| R11 TemplateBuilder legacy | SUPPRIMER FRONTEND ORPHELIN / CONSERVER BACKEND | CLOSED — MERGED (#191) | n/a |
| Catalogue avancé / Catalogue connecté | GARDER / CONNECTER / FIGER HISTORIQUE | CLOSED — MERGED (#195) | 9,5/10 |
| Indicateurs patient explicables | SUPPRIMER JUGEMENTS / GARDER REPÈRES FACTUELS | CLOSED — MERGED (#199) | 9,3/10 |

**Avancement vérifié : 13/15 = 86,7 %.**

## 5. R1 — décision finale

**CLOSED — CERTIFIÉ — MERGED.**

Résultat :
- Profil / Design / Performance partagent une sauvegarde staged explicite ;
- Catalogue / Agenda / Sécurité / Équipe gardent leurs mutations atomiques propres ;
- aucun faux bouton global sur les domaines atomiques ;
- dirty-state protégé par `beforeunload` ;
- préférences runtime committées uniquement après succès backend ;
- Read Truth conservée ;
- 35 BEFORE + 35 AFTER, 5 viewports, 0 overflow, 0 erreur runtime ;
- score **9,5/10**.

Preuves :
- produit certifié `e472ec47f411850f3270335fd92278c1c08b4fc5` ;
- harness final `10ca5475279f579a841bbcce041ffcb7fb6b3f5e` ;
- R1 #2 `32393398276` — SUCCESS — artifact `9415784766` — digest `sha256:329431c1aded9c5c5fd7f90f3c2c4a45ac0da13b837bd61be2075c175fc354ae` ;
- R2 #31, CI #1491, T2 #722, RBAC #142, Branding #75, IA #25, Read Truth #19, R10 #7 et P7 #21 — SUCCESS ;
- merge #194 : `4833a9e54c4fa7383e5ca5096afa18f0a5b500f1` ;
- closeout : `docs/settings/R1_SAVE_DOCTRINE_CLOSEOUT.md`.

Dette non bloquante : le bouton local historique de `ProfileTab.tsx` reste dans le markup mais est masqué par le shell R1 ; aucun effet produit.

## 6. Autres décisions fermées

- **R4 + R6 recovery** : #193, merge `639c40ef4f0f86229cacbc54a16939307dd968e5`.
- **R5 QR** : #192, merge `2b342efdd8dd59fbffec6833549173b1dd74c577`, closeout `docs/settings/R5_QR_TRUTH_CLOSEOUT.md`.
- **R7 Agenda** : #178, merge `4f20832ee70fecf5878242cc1a98ef633d8be129`.
- **R8 Performance & Assistance** : #183, merge `1ac1dd54a9f29c29c06107cd2a1395e8bf6639ce`, closeout `docs/settings/R8_PERFORMANCE_ASSISTANCE_CLOSEOUT.md`.
- **R9-A Audit Log** : #185, merge `bda7f99aa95e9341f5154293618c35949bcae331`, closeout `docs/settings/R9A_AUDIT_LOG_HUMANIZED_CLOSEOUT.md`.
- **R10-A Team mot de passe** : #188, merge `5e8307d4d20ee6ed0df18ee7d06fe2cdb24bc24a`, closeout `docs/settings/R10A_TEAM_PASSWORD_TRUTH_CLOSEOUT.md`.
- **R11 TemplateBuilder frontend** : #191, merge `a4af5ce0ad535e8c154fb7cecee931cba7f76204`, closeout `docs/settings/R11_TEMPLATEBUILDER_REACHABILITY_CLOSEOUT.md`.
- **Catalogue avancé / Catalogue connecté** : #195, merge `5f6187b30906e5f51b6176fa3143702d4b6d62ed`, closeout `docs/settings/CATALOG_CONNECTED_CLOSEOUT.md`, score **9,5/10**.
- **Indicateurs patient explicables** : #199, merge `b22e7bc9e7981eef54916c4e1412fa69ad612bf5`, closeout `docs/settings/INDICATEURS_PATIENT_EXPLICABLES_CLOSEOUT.md`, post-merge `docs/settings/INDICATEURS_PATIENT_EXPLICABLES_POSTMERGE.md`, score **9,3/10**.

## 7. Roadmap restante

Axes encore explicitement nommés dans la roadmap et non crédités :

1. **Restauration guidée** — audit Sécurité & Backup ;
2. **Dette backend TemplateEngine / reachability restante** — uniquement après preuve downstream, sans suppression spéculative.

L’ordre recommandé suit le chemin critique existant : **Restauration guidée d’abord**.

## 8. HANDOVER COURANT

- Chantier : **Réglages — Product Review & Simplification**
- Dernier lot fermé : **Indicateurs patient explicables**
- PR : #199 — MERGED
- Merge : `b22e7bc9e7981eef54916c4e1412fa69ad612bf5`
- HEAD produit principal : `f39944aeaaf3688f496a81f1df0d7dde8aa74692`
- HEAD de certification : `ffe2cf7546a79ea476c393a6251fc0aba2036ff1`
- Truth #7 `32498981650`, CI #1533 `32498981685`, T2 #753 `32498981646`, P7 #52 `32498981617`, P1 #15 `32498981643`, Catalogue #26 `32498981615`, BEFORE #13 `32498981616` — SUCCESS
- Artifact AFTER final : `9452294425` — digest `sha256:7e568a5327f76bfab834bc23ea6eb4ec664eae97e3107a588d13bc879c022a14`
- Score : **9,3/10**
- Closeout : `docs/settings/INDICATEURS_PATIENT_EXPLICABLES_CLOSEOUT.md`
- Post-merge : `docs/settings/INDICATEURS_PATIENT_EXPLICABLES_POSTMERGE.md`
- Next exact : **Restauration guidée → audit Sécurité & Backup, code/routes/tests/UI existants, aucune modification produit**
- Avancement vérifié : **13/15 = 86,7 %**
- Vercel : **aucun déploiement**

## 9. Journal récent

### 2026-08-21 — Indicateurs patient explicables CLOSED

- scores/grades automatiques retirés ;
- repères RDV/finance factuels conservés ;
- tag cabinet manuel conservé ;
- intelligence score `/100` retiré ;
- `Fantôme` remplacé par `Sans RDV futur` ;
- NBA déterministe rendu explicable ;
- IMPA exposé en delta brut sans jugement automatique ;
- FlashSummary mort retiré ;
- AFTER 15/15, 0 overflow, 0 page error, 0 HTTP 5xx ;
- score **9,3/10** ;
- Truth #7, CI #1533, T2 #753, P7 #52, P1 #15, Catalogue #26 et BEFORE #13 — SUCCESS ;
- PR #199 squash-mergée : `b22e7bc9e7981eef54916c4e1412fa69ad612bf5` ;
- aucun Vercel.

### 2026-08-21 — Catalogue avancé / Catalogue connecté CLOSED

- catalogue R6 connecté au flux clinique et au Master Plan ;
- snapshot historique nom/code/tarif figé par valeur ;
- preuve 500 DH → catalogue 650 DH → historique 500 DH ;
- statut historique modifiable pendant désactivation ;
- tenant isolation et quick-add contract verrouillés ;
- AFTER 5/5, 0 overflow, 0 page error, 0 HTTP 5xx ;
- score **9,5/10** ;
- Catalogue #8, CI #1509, T2 #734, P7 #33 — SUCCESS ;
- PR #195 squash-mergée : `5f6187b30906e5f51b6176fa3143702d4b6d62ed` ;
- aucun Vercel.

### 2026-08-20 — R1 CLOSED

- doctrine staged/atomique unifiée ;
- faux bouton global supprimé des domaines atomiques ;
- anti-perte `beforeunload` ;
- runtime commit après vérité backend ;
- deux contrats historiques obsolètes corrigés sans modifier le produit ;
- tous les gates finaux verts ;
- PR #194 squash-mergée ;
- aucun Vercel.

### 2026-08-20 — RECOVERY R4 + R6 CLOSED

- PR #193 mergée après récupération ciblée des surfaces régressées par R7 ;
- R4/R5/R6 recertifiés ;
- aucun Vercel.
