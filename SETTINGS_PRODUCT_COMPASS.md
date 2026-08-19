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

Implémenté : identité/praticien FR-AR, spécialités bilingues, génération automatique d'en-tête ; édition manuelle avancée/repliable ; preset Benmoussa réservé au superadmin ; faux discours détourage IA/SVG supprimé ; double sauvegarde et sticky mobile corrigés.

Preuves : PR #171 MERGED ; HEAD produit `99de2c4aee19f389bdbd0eee46cae072747babdb` ; merge `397f40b50a52457ad53f4b1cb8a9def85b74f5a8` ; R2 Visual #17 / CI #1117 / T2 #377 SUCCESS.

Score visuel : **9.6/10**.
Statut : `CLOSED — CERTIFIÉ — MERGED`.

### R3 — Design & Ambiance

Décision : **GARDER / CLARIFIER LE MODÈLE MENTAL — CLOSED**.

Implémenté : `Apparence app | Documents` → `APERÇU — Application | Document` ; microcopie explicite ; `previewScope` + migration locale ; aucune duplication de thème/profil.

Preuves : BEFORE 5 viewports ; Goal/wireframe avant code ; PR #173 MERGED ; HEAD produit `9db4b560af7925233d5584dfb7af870b76e086d2` ; merge `985873dc644453b078a2a0efc6a1e006121ee6b0` ; Branding #26 / RBAC #53 / T2 #381 / CI #1124 SUCCESS ; 10 AFTER inspectées.

Score visuel : **9.7/10**.
Statut : `CLOSED — CERTIFIÉ — MERGED`.

### R4 — Réglages / Modèles & rendu des documents

Décision finale : **GARDER / RENDRE LE PDF RÉEL AUTORITAIRE — CLOSED**.

Implémenté :
- faux renderer documentaire React supprimé de Réglages ;
- PDF réel = aperçu documentaire principal ;
- état `À actualiser / Rendu à jour` ; génération explicite, plus de régénération automatique 600 ms ;
- 5 IDs conservés et alignés : `swiss / royal / clinical / modern / heritage` ;
- moteur dédié `premium_document_headers.py` ;
- cinq signatures visuelles réellement distinctes ;
- arabe corrigé via fonte Unicode locale, sans réseau ;
- choix typographiques Settings rendus déterministes ;
- previews isolés sous `.previews/settings_branding/<user>` et stockage borné ;
- Document Studio clinique hors scope et non modifié.

Preuves :
- PR #174 MERGED ;
- HEAD produit certifié `0dd384c7b242945270ddb009350961da3590f44f` ;
- merge `5efca67d5416c1d7752a792c304b8d90c7a80aea` ;
- Settings Document Models Visual Audit #19 run `32207520254` SUCCESS ;
- Branding #56 run `32207520252` SUCCESS ;
- RBAC #91 run `32207520212` SUCCESS ;
- T2 #459 run `32207520238` SUCCESS ;
- CI #1205 run `32207520301` SUCCESS ;
- closeout : `docs/settings/R4B_PREMIUM_DOCUMENT_MODELS_CLOSEOUT.md` ;
- scores modèles AFTER : Swiss 9.2, Royal 9.1, Clinical 9.3, Modern 9.2, Heritage 9.1.

Score visuel global modèles : **9.2/10**.
Statut : `CLOSED — CERTIFIÉ — MERGED`.

### R5 — QR documentaire

Garder. À améliorer : destination, donnée utilisée, aperçu, action tester/scanner.
Statut : `AUDITÉ — P2`.

### R6 — Catalogue Actes

Architecture Spécialité → Actes → Pathologies : **GARDER**.
CRUD `window.prompt()` : **REFONDRE** avec vrais formulaires/modales, validation et désactivation contrôlée.

État courant vérifié : PR #177 entièrement verte au HEAD `f0e05923e85c34e90493a1086bec6b5eeabc86ed` ; score visuel AFTER 9.6/10 ; closeout/merge restant.
Statut : `EN CLOSEOUT — P1`.

### R7 — Horaires & Agenda

Garder horaires. Cible : semaine réelle persistée + fermetures/congés. Audit downstream : `agenda_mode` non consommé ; `use_tickets` ne mène qu'à un bouton mort ; exceptions backend déjà présentes.

État courant : Settings visual et CI verts sur le HEAD audité, mais downstream baseline détecte un overflow 1440 px et RBAC est rouge. Ne pas déclarer certifié.
Statut : `ACTIF APRÈS R6 — P2`.

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
- **P1.2** Modèles/rendu documentaire dans Réglages. ✅ CLOSED R4.
- **P1.3** Catalogue CRUD réel. **EN CLOSEOUT R6 / PR #177**.
- **P1.4** Profil / preset propriétaire. ✅ CLOSED R2.
- **P1.5** Team password copy 8..128.
- **P1.6** Scope Branding. ✅ CLOSED R3.

### P2 — valeur métier / simplification

- **P2.1** Agenda hebdomadaire réel. R7 actif après R6.
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
4. **R6 Catalogue Actes** ;
5. R7 Agenda ;
6. R8 Performance & Assistance ;
7. R9 Sécurité & Backup ;
8. R10 Mon Équipe ;
9. R11 cleanup legacy.

## 8. HANDOVER COURANT

- Chantier : **Réglages / Paramètres — Product Review & Simplification**
- Lot actif : **R6 — Catalogue Actes**
- Goal : remplacer le CRUD `prompt()` par des formulaires sûrs sans suppression physique non supportée
- Repo : `hraaaaf/Digital_crown`
- Branche : `settings-r6-catalog-crud`
- PR : `#177 OPEN / mergeable`
- HEAD produit certifié R6 : `f0e05923e85c34e90493a1086bec6b5eeabc86ed`
- Preuves R6 : Catalog #9 / RBAC #89 / Read Truth #12 / T2 #450 / CI #1196 SUCCESS
- Dernière preuve visuelle : 10 AFTER Catalogue inspectées, score 9.6/10
- Blocage réel : aucun produit ; closeout + merge R6 restent à faire après intégration R4 dans master
- Next exact : **closeout R6 contre master post-R4 → merge #177 → corriger R7 downstream overflow/RBAC**
- Avancement roadmap validé : **3/15 = 20.0 %**
- Vercel : **interdit sans autorisation explicite**

## 9. Journal

### 2026-08-19 — R4 CLOSED

- PDF réel promu vérité du preview documentaire ;
- renderer simulé supprimé ;
- 5 modèles premium réalignés et différenciés ;
- arabe corrigé ;
- Document Models / Branding / RBAC / T2 / CI verts sur HEAD exact ;
- score visuel global 9.2/10 ;
- PR #174 mergée en `5efca67d5416c1d7752a792c304b8d90c7a80aea` ;
- aucun déploiement Vercel.

### 2026-08-19 — R3 CLOSED

- PR #173 mergée ; 10 AFTER certifiées ; score 9.7/10 ; aucun déploiement Vercel.

### 2026-08-19 — R2 CLOSED

- PR #171 mergée ; preset Benmoussa limité au superadmin propriétaire ; score 9.6/10 ; aucun déploiement Vercel.
