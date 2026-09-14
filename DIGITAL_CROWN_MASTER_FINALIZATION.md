# DIGITAL CROWN — FINALISATION PRODUIT

**FICHIER CANONIQUE DE PILOTAGE GLOBAL — HORS CÉPHALOMÉTRIE**

Baseline de création : `master@dca24d01ca5591d4255f3ac85f79a32ab6d673c1`.

## Périmètre

Ce fichier fusionne le pilotage des chantiers Digital Crown restants en un seul programme maître.

**Exclusion explicite : la Céphalométrie reste un chantier séparé et n'entre ni dans le score global, ni dans le Next exact, ni dans les priorités de ce fichier.**

## Goal global

Obtenir un Digital Crown non-Céphalo cohérent, certifié et exploitable en cabinet réel.

## Méthode de score

Axes inclus : Document Studio 100 %, Dossier Patient UX 100 %, Clinique multi-praticiens 100 %, Portabilité 89,2 %, Mobile Terrain 70 %, Sécurité / Anti-piratage 60 %.

Calcul : `(100 + 100 + 100 + 89,2 + 70 + 60) / 6 = 86,53 %`.

**Indice global courant : 86,5 %.**

Le benchmark Competitive / Media reste un KPI séparé et n'entre pas dans ce calcul.

## État consolidé

### L1 — Document Studio — FERMÉ
P1→P6 actifs certifiés ; T1 transversal mergé via PR #465.

### L2 — Dossier Patient UX — FERMÉ
UX1-A/B PR #467 et UX1-C PR #468 mergées ; 390 / 768 / 1280 certifiés.

### L3 — Clinique multi-praticiens — FERMÉ
P3 final PR #463 mergée ; HEAD certifié `30e5c235cebdb9f4e460b03a0687856336149c08` ; merge `f16fc658dad0ee4ff67a919568359f1e90d4e2da` ; CI #3763, PostgreSQL #216 et T2 #2701 SUCCESS. Axe : 100 %.

### L4 — Portabilité — HUMAN GATE
`149/167 EP = 89,2 %`. P13 physique `0/13 EP`. Fermeture requiert Windows 11 cabinet réel + stockage hors machine + Apple Silicon + closure guard.

### L5 — Mobile Terrain — HUMAN GATE
Baseline 70 %. Gates physiques iPhone/Android/biométrie/Push restent non substituables.

### L6 — Sécurité / Anti-piratage — BLOQUÉ EXTERNE
Baseline 60 %. Accès control-plane production requis pour les mutations réelles et la chaîne OWNER/licences.

### L7 — Release / CI — ACTIF TRANSVERSE
Packaging #450/#451 mergés ; Document History #469 fermé ; P3 #463 fermé. Rechercher uniquement les dettes release/CI encore réellement ouvertes lors des closeouts suivants.

### L8 — Competitive / Media — C7 FERMÉ
- C4/C5/C6 restent fermés ; C7 n'a pas repris leurs scopes hors régression nécessaire et n'a pas touché la Céphalométrie.
- PR #483 `feat(media): certify Competitive / Media C7` : **MERGED**.
- HEAD candidat certifié : `cf56bb69e65d0eca5b8c5a73e593a02c788cb2d7`.
- Merge squash C7 : `fdaa969f4369c7335e9badcd9480df223f8ee30c`.
- Fonctionnalité fermée : recherche et filtres Media Core côté serveur sous scope tenant + patient, pagination bornée avec `has_more`, taille publique maximale 200, chargement explicite de la page suivante dans le Media Hub, protections de réponse obsolète et déduplication frontend.
- Certification volumétrique : **5 000 assets** tenant A + **500 assets de bruit cross-tenant** ; première page `0,0171 s`, seconde `0,0152 s`, offset profond 4 800 `0,0166 s`, recherche profonde `0,0093 s`, filtre combiné `0,0037 s` ; compteur SQL constant à **2 SELECT** pour les listes certifiées.
- Invariants volumétriques validés : ordre déterministe, pages adjacentes sans duplication/gap, offset profond correct, marqueur situé au-delà des 200 premiers retrouvé par recherche serveur, filtres `asset_type` / `source_kind` / `timepoint` fonctionnels.
- Isolation cross-tenant validée : aucun asset du tenant étranger exposé dans la timeline tenant A ; accès direct au contenu étranger retourne **404** ; le scope tenant + patient reste appliqué au service et aux routes de contenu.
- Exact-head candidat : CI #3941 / run `34856390298` **SUCCESS** ; backend **3467 passed / 10 skipped** ; frontend complet SUCCESS ; tests C7 dédiés pagination + recherche serveur SUCCESS ; PostgreSQL #374, T2 #2859, P7 #1474, C4 Visual #58 et autres checks pertinents SUCCESS ; M6-I #1659 SKIPPED attendu.
- Responsive / UI : Media C5 Visual Certification #28 / run `34856390242` **SUCCESS** aux viewports **390×844, 768×1024, 1280×900** ; 3/3 captures, zéro overflow horizontal, zéro overlap sticky/workspace, zéro page error, zéro HTTP 5xx.
- Comparaison stricte BEFORE → AFTER avec la baseline C5 Visual Certification #20 : 390×844 pixel-identique ; 768×1024 delta `0,002416 %` des pixels ; 1280×900 delta `0,005208 %` ; aucun changement UX visible. Score visuel C7 conservé à **9,6/10** sur preuve comparative.
- Audit PR avant merge : **0 review / 0 thread / 0 comment** ; PR mergeable et HEAD exact confirmé avant merge.
- Post-merge `master@fdaa969f4369c7335e9badcd9480df223f8ee30c` : CI #3942 / run `34857880262` **SUCCESS**.
- Aucun déploiement Vercel.
- Le KPI Competitive / Media reste séparé du calcul global ; aucune nouvelle valeur globale n'est inventée sans règle canonique de recalcul.

## Chemin critique unique

1. **Exécuter les gates physiques** : Portabilité P13 puis Mobile Terrain, selon disponibilité du matériel réel.
2. **Fermer Sécurité** dès que l'accès control-plane production permet l'exécution réelle des mutations autorisées.
3. **Certification globale non-Céphalo** : master propre, CI transverse verte, docs canoniques cohérents, inventaire explicite des human/external gates résiduels.

## Next exact

**HUMAN GATE — Portabilité P13 : exécuter la certification physique uniquement quand Windows 11 cabinet réel + stockage hors machine + Apple Silicon sont disponibles. En attendant, ne pas simuler ni remplacer ce gate.**

## Règles de continuité

- Une fenêtre = un lot principal jusqu'à son closeout, puis HANDOVER + STOP.
- Une CI en cours n'arrête pas le programme ; faire le travail indépendant restant.
- Aucun lot déclaré fermé sans preuve exacte.
- Aucun déploiement Vercel sans autorisation explicite.
- Les chantiers Céphalo ne sont ni modifiés, ni scorés, ni priorisés depuis ce fichier.

## Repères courant

- Competitive / Media C7 : **FERMÉ**
- C7 PR #483 : **MERGED**
- C7 HEAD certifié : `cf56bb69e65d0eca5b8c5a73e593a02c788cb2d7`
- C7 merge squash : `fdaa969f4369c7335e9badcd9480df223f8ee30c`
- CI candidat #3941 : **SUCCESS**
- CI post-merge #3942 : **SUCCESS**
- Media C5 Visual #28 : **SUCCESS**
- volumétrie C7 : **5 000 + 500**, deep offset 4 800, 2 SELECT constants, toutes latences mesurées < 0,018 s
- cross-tenant C7 : **0 fuite observée**, contenu étranger 404
- UI C7 : **390 / 768 / 1280 certifiés**, score visuel **9,6/10** conservé après comparaison stricte BEFORE/AFTER
- audit PR : **0 review / 0 thread / 0 comment**
- indice global : **86,5 %**
- Céphalométrie : **hors périmètre**
- prochain gate : **Portabilité P13 — HUMAN GATE physique**
- human gates : **Portabilité P13 + Mobile Terrain**
- external gate : **Security control-plane production**
